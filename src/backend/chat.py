# backend/chat.py
#!/usr/bin/env python3
"""
Chat module for the NYP FYP CNC Chatbot backend.

This module provides comprehensive chat functionality including:

- Chat session management and persistence
- Chat history loading and searching
- Real-time chatbot responses with LLM integration
- Chat metadata management (names, timestamps)
- Search functionality with fuzzy matching
- Markdown formatting and Mermaid diagram support
- Rate limiting integration for chat operations

The module uses an in-memory cache for performance and provides
both synchronous and asynchronous interfaces for chat operations.
"""

import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import chat_rate_limiter  # Ensure chat_rate_limiter is imported
from .utils import (
    sanitize_input,
)
from .timezone_utils import get_utc_timestamp
from infra_utils import setup_logging
from .markdown_formatter import format_markdown
from .consolidated_database import (
    get_consolidated_database,  # Now importing only the consolidated function
    InputSanitizer,  # Added for general sanitization
)
from performance_utils import perf_monitor

# (Delayed import of llm.chatModel to avoid circular import)


# Set up logging
logger = setup_logging()

# Ensure chat session directory exists (skip during benchmarks)
if not os.environ.get("BENCHMARK_MODE"):
    Path(CHAT_SESSIONS_PATH).mkdir(parents=True, exist_ok=True)

# In-memory store for chat names and metadata
# Structure: {username: {chat_id: {session_name: str, created_at: str, updated_at: str}}}
_chat_metadata_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

# In-memory store for chat history to reduce DB reads for active sessions
# Structure: {chat_id: [{role: str, content: str, timestamp: str}]}
_chat_history_cache: Dict[str, List[Dict[str, str]]] = {}

_MAX_CHAT_HISTORY_CACHE_SIZE = 100  # Max number of chat sessions to cache history for


def _get_chat_db_manager():
    """Returns the consolidated database instance."""
    return get_consolidated_database()


def _get_user_db_manager():
    """Returns the consolidated database instance (for user operations if needed)."""
    return get_consolidated_database()


# --- Cache Management Functions ---


def _load_chat_metadata_for_user(username: str) -> None:
    """
    Loads all chat session metadata for a given user into the in-memory cache.
    """
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
    """
    Retrieves chat metadata for a user from cache, loading if not present.
    """
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
    """Updates the in-memory chat history cache and metadata cache."""
    if chat_id not in _chat_history_cache:
        # If chat_id is new, ensure it doesn't exceed cache size
        if len(_chat_history_cache) >= _MAX_CHAT_HISTORY_CACHE_SIZE:
            # Simple LRU: remove the oldest entry (arbitrarily pick one)
            # A more robust LRU would track access times
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

    # Update metadata cache with the new message and updated_at timestamp
    current_metadata = _chat_metadata_cache.get(username, {}).get(chat_id)
    if current_metadata:
        current_metadata["updated_at"] = timestamp
        if new_session_name:
            current_metadata["session_name"] = new_session_name
    else:
        # This scenario happens if a new chat session is created
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
    """
    Appends the user message and LLM response to the chat history for a session.
    Also updates the in-memory cache.
    """
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_user_message = InputSanitizer.sanitize_text(user_message)
    sanitized_llm_response = InputSanitizer.sanitize_text(llm_response)
    timestamp = get_utc_timestamp()

    async with perf_monitor.track_performance_async("db_update_chat_history"):
        # Check if chat session exists, if not, create it
        session_exists_query = (
            "SELECT COUNT(*) FROM chat_sessions WHERE session_id = ? AND username = ?"
        )
        exists = db.fetch_one(
            session_exists_query, (sanitized_chat_id, sanitized_username)
        )[0]

        new_session_name = None
        if exists == 0:
            # New session: derive a name from the first message
            new_session_name = (
                user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
            sanitized_session_name = InputSanitizer.sanitize_text(new_session_name)
            create_session_query = """
                INSERT INTO chat_sessions (session_id, username, session_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_update(
                create_session_query,
                (
                    sanitized_chat_id,
                    sanitized_username,
                    sanitized_session_name,
                    timestamp,
                    timestamp,
                ),
            )
            logger.info(
                f"Created new chat session: {sanitized_session_name} for user {sanitized_username}"
            )
        else:
            # Update existing session's updated_at timestamp
            update_session_query = """
                UPDATE chat_sessions SET updated_at = ? WHERE session_id = ? AND username = ?
            """
            db.execute_update(
                update_session_query, (timestamp, sanitized_chat_id, sanitized_username)
            )

        # Insert user message
        user_message_query = """
            INSERT INTO chat_messages (session_id, username, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        db.execute_update(
            user_message_query,
            (
                sanitized_chat_id,
                sanitized_username,
                "user",
                sanitized_user_message,
                timestamp,
            ),
        )

        # Insert LLM response
        llm_response_query = """
            INSERT INTO chat_messages (session_id, username, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        db.execute_update(
            llm_response_query,
            (
                sanitized_chat_id,
                sanitized_username,
                "assistant",
                sanitized_llm_response,
                timestamp,
            ),
        )

    await _update_chat_history_cache(
        chat_id, username, user_message, llm_response, timestamp, new_session_name
    )

    # Return the updated history from cache
    return _chat_history_cache.get(chat_id, [])


async def get_chat_history(
    chat_id: str, username: str, limit: int = 50
) -> List[Dict[str, str]]:
    """
    Retrieves the chat history for a given chat ID and username.
    Prioritizes in-memory cache, then falls back to database.
    """
    if chat_id in _chat_history_cache:
        logger.debug(f"Returning chat history for {chat_id} from cache.")
        return _chat_history_cache[chat_id]

    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)

    async with perf_monitor.track_performance_async("db_get_chat_history"):
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
    _chat_history_cache[chat_id] = history  # Cache the retrieved history
    logger.info(
        f"Loaded {len(history)} messages for chat_id {chat_id} from database into cache."
    )
    return history


async def get_chat_metadata(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Retrieves all chat session metadata (session_id, session_name, created_at, updated_at)
    for a given username. Uses and updates in-memory cache.
    """
    return _get_chat_metadata_cache(username)


async def get_chatbot_response(
    message: str, chat_id: str, ui_state: Dict[str, Any]
) -> Tuple[str, List[Dict[str, str]], str, Dict[str, Any], str]:
    """
    Main function to get a chatbot response.
    Handles chat history, LLM interaction, and rate limiting.
    """
    username = ui_state.get("username")
    if not username:
        return (
            "",
            [],
            chat_id,
            {},
            "Error: User not logged in. Please log in to chat.",
        )

    # Use the chat_rate_limiter specifically for chat operations
    if not chat_rate_limiter.check_rate_limit(username):
        logger.warning(f"Chat rate limit hit for user: {username}")
        error_response = (
            "Rate limit exceeded. Please wait a moment before sending another message."
        )
        # Update history with rate limit message
        updated_history = await _update_chat_history(
            chat_id, username, message, error_response
        )
        user_chats_after_update = _get_chat_metadata_cache(username)
        return (
            "",
            updated_history,
            chat_id,
            user_chats_after_update,
            "Rate limit exceeded.",
        )

    # Delayed import to avoid circular dependency
    from llm import chatModel

    if not chatModel.is_llm_ready():
        error_response = "[Error] LLM is not ready. Please try again later."
        updated_history = await _update_chat_history(
            chat_id, username, message, error_response
        )
        user_chats_after_update = _get_chat_metadata_cache(username)  # Refresh cache
        return (
            "",
            updated_history,
            chat_id,
            user_chats_after_update,
            "LLM not ready.",
        )

    sanitized_message = sanitize_input(message)
    current_history = await get_chat_history(chat_id, username)

    try:
        async with perf_monitor.track_performance_async("llm_get_convo_hist_answer"):
            answer_text = await chatModel.get_convo_hist_answer(
                sanitized_message, chat_id, username, current_history
            )

        if answer_text and not answer_text.startswith("[Error]"):
            formatted_answer = format_markdown(answer_text)
            updated_history = await _update_chat_history(
                chat_id, username, message, formatted_answer
            )
            user_chats_after_update = _get_chat_metadata_cache(
                username
            )  # Refresh cache after update

            # If this is a new chat, generate a name based on the first user message
            if (
                len(updated_history) == 2
                and chat_id not in _chat_metadata_cache[username]
            ):  # First user message and LLM response
                new_session_name = (
                    message[:50] + "..." if len(message) > 50 else message
                )
                await rename_chat_session(chat_id, new_session_name, username)
                user_chats_after_update = _get_chat_metadata_cache(
                    username
                )  # Re-refresh to get new name

            # Determine the final chat_id to return. If it was a new chat, ensure it's propagated.
            # This logic needs to consider if a new chat_id was actually created/assigned.
            # In our current consolidated DB setup, chat_id is passed in and used.
            # The 'new session' logic is handled by _update_chat_history.
            final_chat_id = chat_id
            if not user_chats_after_update.get(
                chat_id
            ):  # This means it was a brand new chat, and the cache was updated.
                # Find the actual chat_id that was just created if it wasn't the one passed in
                # This logic assumes _update_chat_history creates an entry if not exists
                # and uses the provided chat_id. So final_chat_id remains the same.
                # The primary way to get a 'new' chat_id is from the UI generating a UUID.
                pass  # final_chat_id remains chat_id.

            # Ensure the current chat_id is the most recently updated one in the UI
            if user_chats_after_update.get(chat_id):
                # This ensures the active chat in the UI is always the one just updated.
                # It finds the chat with the latest updated_at timestamp.
                final_chat_id = max(
                    user_chats_after_update,
                    key=lambda k: user_chats_after_update[k].get(
                        "updated_at", datetime.min.isoformat()
                    ),
                    default=chat_id,
                )
            debug_info = "Message processed and LLM response obtained."
        else:
            error_response = answer_text
            updated_history = await _update_chat_history(
                chat_id, username, message, error_response
            )
            user_chats_after_update = _get_chat_metadata_cache(
                username
            )  # Refresh cache
            final_chat_id = chat_id
            debug_info = f"Error from LLM: {answer_text}"

        return (
            "",
            updated_history,
            final_chat_id,
            user_chats_after_update,
            debug_info,
        )
    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}")
        error_response = f"[Error] An unexpected error occurred in backend: {e}"
        updated_history = await _update_chat_history(
            chat_id, username, message, error_response
        )
        user_chats_after_update = _get_chat_metadata_cache(username)  # Refresh cache
        final_chat_id = chat_id
        return (
            "",
            updated_history,
            final_chat_id,
            user_chats_after_update,
            f"Unexpected error in get_chatbot_response: {e}",
        )


async def delete_chat_history_for_user(username: str) -> bool:
    """
    Deletes all chat history for a given user.
    """
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)

    async with perf_monitor.track_performance_async("db_delete_all_chat_history"):
        try:
            # Delete messages first
            db.execute_update(
                "DELETE FROM chat_messages WHERE username = ?", (sanitized_username,)
            )
            # Then delete sessions
            db.execute_update(
                "DELETE FROM chat_sessions WHERE username = ?", (sanitized_username,)
            )

            # Clear cache for the user
            _chat_metadata_cache.pop(username, None)
            # Clear relevant chat histories from cache
            for chat_id in list(_chat_history_cache.keys()):
                # This is a bit inefficient, assuming chat_id might not directly map to user.
                # A better cache structure might be {username: {chat_id: history}}
                # For now, we'll just clear all.
                # TODO: Implement a more granular history cache invalidation.
                _chat_history_cache.pop(chat_id, None)

            logger.info(f"Deleted all chat history for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat history for user {username}: {e}")
            return False


async def delete_single_chat_session(chat_id: str, username: str) -> bool:
    """Deletes a single chat session."""
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)

    async with perf_monitor.track_performance_async("db_delete_single_chat_session"):
        try:
            # Delete messages first
            db.execute_update(
                "DELETE FROM chat_messages WHERE session_id = ? AND username = ?",
                (sanitized_chat_id, sanitized_username),
            )
            # Then delete the session
            db.execute_update(
                "DELETE FROM chat_sessions WHERE session_id = ? AND username = ?",
                (sanitized_chat_id, sanitized_username),
            )

            if username in _chat_metadata_cache:
                if chat_id in _chat_metadata_cache[username]:
                    del _chat_metadata_cache[username][chat_id]
            _chat_history_cache.pop(chat_id, None)  # Remove from history cache

            logger.info(f"Deleted chat session {chat_id} for user {username}.")
            return True
        except Exception as e:
            logger.error(
                f"Error deleting chat session {chat_id} for user {username}: {e}"
            )
            return False


async def rename_chat_session(
    chat_id: str, new_name: str, username: str
) -> Optional[Dict[str, Any]]:
    """Renames a chat session."""
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_new_name = InputSanitizer.sanitize_text(new_name)
    sanitized_username = InputSanitizer.sanitize_username(username)
    timestamp = get_utc_timestamp()

    async with perf_monitor.track_performance_async("db_rename_chat_session_session"):
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
                # Update cache
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
    """
    Saves a single message to the database and updates the cache.
    This function is primarily for background/manual saving if needed,
    as _update_chat_history typically handles this during response generation.
    """
    db = _get_chat_db_manager()
    sanitized_chat_id = InputSanitizer.sanitize_string(chat_id)
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_role = InputSanitizer.sanitize_string(role)
    sanitized_content = InputSanitizer.sanitize_text(content)
    timestamp = get_utc_timestamp()

    async with perf_monitor.track_performance_async("db_save_message_async"):
        try:
            # Ensure session exists or create it (similar to _update_chat_history)
            session_exists_query = "SELECT COUNT(*) FROM chat_sessions WHERE session_id = ? AND username = ?"
            exists = db.fetch_one(
                session_exists_query, (sanitized_chat_id, sanitized_username)
            )[0]

            if exists == 0:
                new_session_name = (
                    (content[:50] + "..." if len(content) > 50 else content)
                    if role == "user"
                    else f"Chat {chat_id[:8]}"
                )
                sanitized_session_name = InputSanitizer.sanitize_text(new_session_name)
                create_session_query = """
                    INSERT INTO chat_sessions (session_id, username, session_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                db.execute_update(
                    create_session_query,
                    (
                        sanitized_chat_id,
                        sanitized_username,
                        sanitized_session_name,
                        timestamp,
                        timestamp,
                    ),
                )
            else:
                # Update existing session's updated_at timestamp
                update_session_query = """
                    UPDATE chat_sessions SET updated_at = ? WHERE session_id = ? AND username = ?
                """
                db.execute_update(
                    update_session_query,
                    (timestamp, sanitized_chat_id, sanitized_username),
                )

            query = """
                INSERT INTO chat_messages (session_id, username, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_update(
                query,
                (
                    sanitized_chat_id,
                    sanitized_username,
                    sanitized_role,
                    sanitized_content,
                    timestamp,
                ),
            )

            # Update cache: this function is less about direct UI update, more about backend consistency
            # If the chat history is not already in cache or is stale, it will be loaded on next get_chat_history call.
            # For simplicity, we just add the new message to the existing cache if the chat_id is present.
            if chat_id in _chat_history_cache:
                _chat_history_cache[chat_id].append(
                    {"role": role, "content": content, "timestamp": timestamp}
                )

            # Also update metadata cache for updated_at
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
    """
    Searches chat messages and session names for a given query.
    """
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    sanitized_search_query = InputSanitizer.sanitize_text(search_query)

    # Use a fuzzy search pattern
    search_pattern = f"%{sanitized_search_query}%"

    results: List[Dict[str, Any]] = []

    async with perf_monitor.track_performance_async("db_search_chat_history"):
        # Search in chat messages
        message_query = """
            SELECT cm.session_id, cs.session_name, cm.role, cm.content, cm.timestamp
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.session_id AND cm.username = cs.username
            WHERE cm.username = ? AND cm.content LIKE ?
            ORDER BY cm.timestamp DESC
            LIMIT 100
        """
        message_results = db.execute_query(
            message_query, (sanitized_username, search_pattern)
        )

    for row in message_results:
        results.append(
            {
                "type": "message",
                "session_name": row["session_name"],
                "content": row["content"],
                "role": row["role"],
                "timestamp": row["timestamp"],
                "session_id": row["session_id"],
            }
        )

    # Search in chat session names
    session_query = """
        SELECT session_name, session_id, created_at, updated_at
        FROM chat_sessions
        WHERE username = ? AND session_name LIKE ?
        ORDER BY updated_at DESC
        LIMIT 50
    """
    session_results = db.execute_query(
        session_query, (sanitized_username, search_pattern)
    )

    for row in session_results:
        # Avoid duplicating sessions already found via messages, but if a session name matches
        # and no message from that session matched, add it.
        if not any(r.get("session_id") == row["session_id"] for r in results):
            results.append(
                {
                    "type": "session_name",
                    "session_name": row["session_name"],
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
    logger.info(
        f"Chat search for '{username}' with query '{search_query}' returned {len(results)} results."
    )
    return results


def format_search_results(results: List[Dict[str, Any]]) -> List[str]:
    """
    Formats the raw search results into a human-readable list of strings.

    :param results: A list of dictionaries, where each dictionary represents a search result
                    (e.g., from search_chat_history).
    :type results: List[Dict[str, Any]]
    :return: A list of formatted strings, each representing a search result.
    :rtype: List[str]
    """
    formatted_output = []
    if not results:
        return ["No matching results found."]

    for item in results:
        chat_name = item.get("chat_name", "Unknown Chat")
        # Truncate chat_id for display purposes if it's too long
        chat_id_display = item.get("chat_id", "N/A")
        if len(chat_id_display) > 8:
            chat_id_display = chat_id_display[:8] + "..."

        role = item.get("role", "N/A").capitalize()
        content = item.get("content", "No content").strip()
        timestamp = item.get("timestamp", "N/A")

        # Basic formatting, could be more elaborate as per UI needs
        formatted_output.append(
            f"--- Chat: '{chat_name}' (ID: {chat_id_display}) ---\n\n"
            f"  Role: {role}\n\n"
            f"  Time: {timestamp}\n\n"
            f"  Content: {content}\n\n"
            f"----------------------------------------"
        )
    return formatted_output
