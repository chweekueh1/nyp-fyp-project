import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import difflib

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit
from .utils import (
    sanitize_input,
)
from .timezone_utils import get_utc_timestamp
from infra_utils import setup_logging
from .markdown_formatter import format_markdown
from .consolidated_database import (
    get_consolidated_database,
    InputSanitizer,
)

logger = setup_logging()

if not os.environ.get("BENCHMARK_MODE"):
    Path(CHAT_SESSIONS_PATH).mkdir(parents=True, exist_ok=True)

_chat_metadata_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
_chat_history_cache: Dict[str, List[Dict[str, str]]] = {}

_MAX_CHAT_HISTORY_CACHE_SIZE = 100


def _get_chat_db_manager():
    return get_consolidated_database()


def _get_user_db_manager():
    return get_consolidated_database()


def persist_user_and_assistant_message(
    username, chat_id, user_message, assistant_message
):
    db = get_consolidated_database()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    history = db.get_chat_messages(sanitized_chat_id)
    if history:
        next_index = (
            max((msg.get("message_index", -1) for msg in history), default=-1) + 1
        )
    else:
        next_index = 0
    if user_message:
        db.add_chat_message(
            sanitized_chat_id,
            sanitized_username,
            next_index,
            "user",
            user_message,
            None,
        )
        next_index += 1
    if assistant_message:
        db.add_chat_message(
            sanitized_chat_id,
            sanitized_username,
            next_index,
            "assistant",
            assistant_message,
            None,
        )


def create_new_chat_session(username: str, session_name: Optional[str] = None) -> str:
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    chat_id = f"chat_{uuid.uuid4().hex[:8]}"
    timestamp = get_utc_timestamp()
    session_name = session_name or f"Chat {chat_id[:8]}"
    db.create_chat_session(sanitized_username, chat_id, session_name)
    _chat_metadata_cache.setdefault(username, {})[chat_id] = {
        "session_name": session_name,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    _chat_history_cache[chat_id] = []
    logger.info(
        f"Created new chat session: {session_name} for user {sanitized_username}"
    )
    return chat_id


def _load_chat_metadata_for_user(username: str) -> None:
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    query = """
        SELECT session_id, session_name, created_at, updated_at
        FROM chat_sessions
        WHERE username = ?
        ORDER BY updated_at DESC
    """
    rows = db.execute_query(query, (sanitized_username,))
    _chat_metadata_cache[username] = {
        row["session_id"]: {
            "session_name": row["session_name"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    }
    logger.info(
        f"Loaded {len(_chat_metadata_cache[username])} chat sessions for {username} into cache."
    )


def _get_chat_metadata_cache(username: str) -> Dict[str, Dict[str, Any]]:
    if username not in _chat_metadata_cache:
        _load_chat_metadata_for_user(username)
    return _chat_metadata_cache.get(username, {})


async def _update_chat_history_cache(
    chat_id: str,
    username: str,
    user_message: str,
    llm_response: str,
    timestamp: str,
    new_session_name: Optional[str] = None,
) -> None:
    if chat_id not in _chat_history_cache:
        if len(_chat_history_cache) >= _MAX_CHAT_HISTORY_CACHE_SIZE:
            oldest_chat_id = next(iter(_chat_history_cache))
            _chat_history_cache.pop(oldest_chat_id, None)
            logger.debug(f"Evicted chat history for {oldest_chat_id} from cache.")
        _chat_history_cache[chat_id] = []

    _chat_history_cache[chat_id].append(
        {"role": "user", "content": user_message, "timestamp": timestamp}
    )
    _chat_history_cache[chat_id].append(
        {"role": "assistant", "content": llm_response, "timestamp": timestamp}
    )

    current_metadata = _chat_metadata_cache.get(username, {}).get(chat_id)
    if current_metadata:
        current_metadata["updated_at"] = timestamp
        if new_session_name:
            current_metadata["session_name"] = new_session_name
    else:
        _chat_metadata_cache.setdefault(username, {})[chat_id] = {
            "session_name": new_session_name
            if new_session_name
            else f"Chat {chat_id[:8]}",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    logger.debug(f"Updated cache for chat_id {chat_id}.")


async def _update_chat_history(
    chat_id: str, username: str, user_message: str, llm_response: str
) -> List[Dict[str, str]]:
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_user_message = InputSanitizer.sanitize_text(user_message)
    sanitized_llm_response = InputSanitizer.sanitize_text(llm_response)
    timestamp = get_utc_timestamp()
    session = db.get_chat_session(sanitized_chat_id)
    new_session_name = None
    if session is None:
        new_session_name = (
            user_message[:50] + "..."
            if user_message and len(user_message) > 50
            else user_message or f"Chat {sanitized_chat_id[:8]}"
        )
        db.create_chat_session(sanitized_username, sanitized_chat_id, new_session_name)
        logger.info(
            f"Created new chat session: {new_session_name} for user {sanitized_username}"
        )
    else:
        db.update_chat_session_timestamp(sanitized_chat_id)
    history = db.get_chat_messages(sanitized_chat_id)
    if history:
        next_index = (
            max((msg.get("message_index", -1) for msg in history), default=-1) + 1
        )
    else:
        next_index = 0
    if user_message:
        db.add_chat_message(
            sanitized_chat_id,
            sanitized_username,
            next_index,
            "user",
            sanitized_user_message,
            None,
        )
        next_index += 1
    if llm_response:
        db.add_chat_message(
            sanitized_chat_id,
            sanitized_username,
            next_index,
            "assistant",
            sanitized_llm_response,
            None,
        )

    await _update_chat_history_cache(
        chat_id, username, user_message, llm_response, timestamp, new_session_name
    )

    return _chat_history_cache.get(chat_id, [])


async def get_chat_history(
    chat_id: str, username: str, limit: int = 50
) -> List[List[str]]:
    if chat_id in _chat_history_cache:
        logger.debug(f"Returning chat history for {chat_id} from cache.")
        history = _chat_history_cache[chat_id]
        if not history:
            return []
        formatted_history = []
        last_user = None
        for entry in history:
            if entry["role"] == "user":
                last_user = entry["content"]
            elif entry["role"] == "assistant" and last_user is not None:
                formatted_history.append([last_user, format_markdown(entry["content"])])
                last_user = None
        if last_user is not None:
            formatted_history.append([last_user, ""])
        return formatted_history

    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)

    query = """
        SELECT role, content, timestamp
        FROM chat_messages
        WHERE session_id = ? AND username = ?
        ORDER BY timestamp ASC
        LIMIT ?
    """
    rows = db.execute_query(query, (sanitized_chat_id, sanitized_username, limit))

    history = [
        {"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]}
        for row in rows
    ]
    _chat_history_cache[chat_id] = history
    logger.info(
        f"Loaded {len(history)} messages for chat_id {chat_id} from database into cache."
    )
    formatted_history = []
    last_user = None
    for entry in history:
        if entry["role"] == "user":
            last_user = entry["content"]
        elif entry["role"] == "assistant" and last_user is not None:
            formatted_history.append([last_user, format_markdown(entry["content"])])
            last_user = None
    if last_user is not None:
        formatted_history.append([last_user, ""])
    return formatted_history


async def get_chat_metadata(username: str) -> Dict[str, Dict[str, Any]]:
    return _get_chat_metadata_cache(username)


async def get_chatbot_response(username: str, chat_id: str, message: str):
    if not username:
        yield "Error: User not logged in. Please log in to chat."
        return
    rate_limit_result = await check_rate_limit(username, "chat")
    if not rate_limit_result["allowed"]:
        logger.warning(f"Chat rate limit hit for user: {username}")
        yield "Rate limit exceeded. Please wait a moment before sending another message."
        return
    from llm import chatModel

    if not chatModel.is_llm_ready():
        yield "[Error] LLM is not ready. Please try again later."
        return
    sanitized_message = sanitize_input(message)
    try:
        result = await chatModel.get_convo_hist_answer(sanitized_message, chat_id)
        answer = result.get("answer", "[No answer generated]")
        yield format_markdown(answer)
        return
    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}")
        yield f"[Error] An unexpected error occurred in backend: {e}"
        return


async def delete_chat_history_for_user(username: str) -> bool:
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    try:
        db.execute_update(
            "DELETE FROM chat_messages WHERE username = ?", (sanitized_username,)
        )
        db.execute_update(
            "DELETE FROM chat_sessions WHERE username = ?", (sanitized_username,)
        )
        _chat_metadata_cache.pop(username, None)
        for chat_id in list(_chat_history_cache.keys()):
            _chat_history_cache.pop(chat_id, None)
        logger.info(f"Deleted all chat history for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error deleting chat history for user {username}: {e}")
        return False


async def delete_single_chat_session(chat_id: str, username: str) -> bool:
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    try:
        db.execute_update(
            "DELETE FROM chat_messages WHERE session_id = ? AND username = ?",
            (sanitized_chat_id, sanitized_username),
        )
        db.execute_update(
            "DELETE FROM chat_sessions WHERE session_id = ? AND username = ?",
            (sanitized_chat_id, sanitized_username),
        )
        if username in _chat_metadata_cache:
            if chat_id in _chat_metadata_cache[username]:
                del _chat_metadata_cache[username][chat_id]
        _chat_history_cache.pop(chat_id, None)
        logger.info(f"Deleted chat session {chat_id} for user {username}.")
        return True
    except Exception as e:
        logger.error(f"Error deleting chat session {chat_id} for user {username}: {e}")
        return False


async def rename_chat_session(
    chat_id: str, new_name: str, username: str
) -> Optional[Dict[str, Any]]:
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_new_name = InputSanitizer.sanitize_text(new_name)
    sanitized_username = InputSanitizer.sanitize_username(username)
    timestamp = get_utc_timestamp()
    try:
        query = """
            UPDATE chat_sessions
            SET session_name = ?, updated_at = ?
            WHERE session_id = ? AND username = ?
        """
        rows_affected = db.execute_update(
            query,
            (sanitized_new_name, timestamp, sanitized_chat_id, sanitized_username),
        )
        if rows_affected > 0:
            if (
                username in _chat_metadata_cache
                and chat_id in _chat_metadata_cache[username]
            ):
                _chat_metadata_cache[username][chat_id]["session_name"] = (
                    sanitized_new_name
                )
                _chat_metadata_cache[username][chat_id]["updated_at"] = timestamp
            logger.info(
                f"Renamed chat session {chat_id} to '{sanitized_new_name}' for user {username}"
            )
            return {
                "session_id": chat_id,
                "session_name": sanitized_new_name,
                "updated_at": timestamp,
            }
        else:
            logger.warning(
                f"Could not find chat session {chat_id} for user {username} to rename."
            )
            return None
    except Exception as e:
        logger.error(f"Error renaming chat session {chat_id}: {e}")
        return None


async def save_message_async(
    chat_id: str, username: str, role: str, content: str
) -> bool:
    import asyncio

    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_role = InputSanitizer.sanitize_string(role)
    sanitized_content = InputSanitizer.sanitize_text(content)
    timestamp = get_utc_timestamp()
    loop = asyncio.get_event_loop()
    try:
        # Check if session exists using execute_query
        # session_exists_query = "SELECT COUNT(*) as count FROM chat_sessions WHERE session_id = ? AND username = ?"
        # result = await loop.run_in_executor(
        #     None,
        #     db.execute_query,
        #     session_exists_query,
        #     (sanitized_chat_id, sanitized_username),
        # )
        new_session_name = (
            (content[:50] + "..." if len(content) > 50 else content)
            if role == "user"
            else f"Chat {chat_id[:8]}"
        )
        sanitized_session_name = InputSanitizer.sanitize_text(new_session_name)
        create_session_query = """
            INSERT OR IGNORE INTO chat_sessions (session_id, username, session_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        await loop.run_in_executor(
            None,
            db.execute_update,
            create_session_query,
            (
                sanitized_chat_id,
                sanitized_username,
                sanitized_session_name,
                timestamp,
                timestamp,
            ),
        )
        # Always update timestamp after insert/ignore
        update_session_query = """
            UPDATE chat_sessions SET updated_at = ? WHERE session_id = ? AND username = ?
        """
        await loop.run_in_executor(
            None,
            db.execute_update,
            update_session_query,
            (timestamp, sanitized_chat_id, sanitized_username),
        )

        history = await loop.run_in_executor(
            None, db.get_chat_messages, sanitized_chat_id
        )
        if history:
            next_index = (
                max((msg.get("message_index", -1) for msg in history), default=-1) + 1
            )
        else:
            next_index = 0

        query = """
            INSERT INTO chat_messages (session_id, username, message_index, role, content, timestamp, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        await loop.run_in_executor(
            None,
            db.execute_update,
            query,
            (
                sanitized_chat_id,
                sanitized_username,
                next_index,
                sanitized_role,
                sanitized_content,
                timestamp,
                timestamp,
            ),
        )

        if chat_id in _chat_history_cache:
            _chat_history_cache[chat_id].append(
                {"role": role, "content": content, "timestamp": timestamp}
            )

        if (
            username in _chat_metadata_cache
            and chat_id in _chat_metadata_cache[username]
        ):
            _chat_metadata_cache[username][chat_id]["updated_at"] = timestamp

        logger.debug(f"Saved message to DB for chat_id {chat_id}, role {role}")
        return True
    except Exception as e:
        logger.error(f"Error saving message for chat_id {chat_id}: {e}")
        return False


async def search_chat_history(username: str, search_query: str) -> List[Dict[str, Any]]:
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_search_query = InputSanitizer.sanitize_text(search_query)
    try:
        db.increment_user_stat(sanitized_username, "search_queries", 1)
    except Exception:
        pass
    message_query = """
        SELECT cm.session_id, cs.session_name, cm.role, cm.content, cm.timestamp
        FROM chat_messages cm
        JOIN chat_sessions cs ON cm.session_id = cs.session_id AND cm.username = cs.username
        WHERE cm.username = ?
        ORDER BY cm.timestamp ASC
        LIMIT 1000
    """
    message_results = db.execute_query(message_query, (sanitized_username,))
    pairs = []
    current_user = None
    current_sid = None
    for row in message_results:
        if row["role"] == "user":
            current_user = row
            current_sid = row["session_id"]
        elif (
            row["role"] == "assistant"
            and current_user
            and row["session_id"] == current_sid
        ):
            pairs.append((current_user, row))
            current_user = None
            current_sid = None
    matches: List[Dict[str, Any]] = []
    needle = sanitized_search_query.lower()
    checked_lines_debug = []
    match_debug = []
    threshold = 0.2  # Lowered threshold for fuzzy matching
    for user_row, assist_row in pairs:
        for row in [user_row, assist_row]:
            content = row["content"]
            role = row["role"]
            lines = content.splitlines()
            for lineno, line in enumerate(lines):
                s = difflib.SequenceMatcher(None, line.lower(), needle)
                fuzzy_score = s.ratio()
                checked_lines_debug.append(
                    {"line": line, "role": role, "score": fuzzy_score}
                )
                # Case-insensitive substring match or fuzzy match above threshold
                if needle in line.lower() or fuzzy_score >= threshold:
                    highlighted = highlight_match(line, needle)
                    match_entry = {
                        "type": "message",
                        "session_name": row["session_name"],
                        "content": highlighted,
                        "role": row["role"],
                        "timestamp": row["timestamp"],
                        "session_id": row["session_id"],
                        "line": lineno + 1,
                        "fulltext": content,
                        "fuzzy_score": fuzzy_score,
                    }
                    matches.append(match_entry)
                    match_debug.append(
                        {
                            "match": line,
                            "score": fuzzy_score,
                            "role": role,
                            "session_id": row["session_id"],
                        }
                    )
    session_query = """
        SELECT session_name, session_id, created_at, updated_at
        FROM chat_sessions
        WHERE username = ?
        ORDER BY updated_at DESC
        LIMIT 50
    """
    session_rows = db.execute_query(session_query, (sanitized_username,))
    for row in session_rows:
        if needle in row["session_name"].lower():
            matches.append(
                {
                    "type": "session_name",
                    "session_name": row["session_name"],
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "fuzzy_score": 1.0,
                }
            )
    # Detailed debug
    logger.debug(
        f"[FUZZY SEARCH DEBUG] Checked lines: {[checked_line['line'] for checked_line in checked_lines_debug]}"
    )
    for entry in checked_lines_debug:
        logger.debug(
            f"[FUZZY SCORE] Role: {entry['role']} | Line: '{entry['line']}' | Score: {entry['score']:.3f}"
        )
    logger.info(
        f"[FUZZY MATCHES] User '{username}' Query '{search_query}': {len(matches)} matches: {match_debug}"
    )
    logger.info(
        f"Fuzzy chat search for '{username}' with query '{search_query}' returned {len(matches)} results."
    )
    return matches


def highlight_match(text, needle):
    import re

    if not needle:
        return text

    def _replace(m):
        return f'<mark style="background:yellow;font-weight:bold">{m.group(0)}</mark>'

    pattern = re.compile(re.escape(needle), re.IGNORECASE)
    return pattern.sub(_replace, text)


def format_search_results(results: List[Dict[str, Any]]) -> List[str]:
    formatted_output = []
    if not results:
        return ["No matching results found."]
    for item in results:
        if item["type"] == "message":
            chat_name = item.get("session_name", "Unknown Chat")
            chat_id_display = item.get("session_id", "N/A")
            if len(chat_id_display) > 8:
                chat_id_display = chat_id_display[:8] + "..."
            role = item.get("role", "N/A").capitalize()
            content = item.get("content", "No content").strip()
            timestamp = item.get("timestamp", "N/A")
            line_no = item.get("line", "?")
            formatted_output.append(
                f"--- Chat: '{chat_name}' (ID: {chat_id_display}) | Line {line_no} ---\n"
                f"  Role: {role}\n"
                f"  Time: {timestamp}\n"
                f"  Content: {content}\n"
                f"----------------------------------------"
            )
        elif item["type"] == "session_name":
            chat_id_display = item.get("session_id", "N/A")
            if len(chat_id_display) > 8:
                chat_id_display = chat_id_display[:8] + "..."
            chat_name = item.get("session_name", "?")
            updated_at = item.get("updated_at", "?")
            formatted_output.append(
                f"=== Session: '{chat_name}' (ID: {chat_id_display}) ===\n"
                f"  Last Updated: {updated_at}\n"
                f"=========================================="
            )
    return formatted_output
