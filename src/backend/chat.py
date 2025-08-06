# --- New Chat Session Creation ---
import uuid
from typing import Optional


def create_new_chat_session(username: str, session_name: Optional[str] = None) -> str:
    """
    Creates and persists a new chat session (with no messages) in both the database and in-memory cache.
    Returns the new chat_id.
    """
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)
    chat_id = f"chat_{uuid.uuid4().hex[:8]}"
    timestamp = get_utc_timestamp()
    session_name = session_name or f"Chat {chat_id[:8]}"
    # Persist in DB
    db.create_chat_session(sanitized_username, chat_id, session_name)
    # Update in-memory metadata cache
    _chat_metadata_cache.setdefault(username, {})[chat_id] = {
        "session_name": session_name,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    # No messages in history yet
    _chat_history_cache[chat_id] = []
    logger.info(
        f"Created new chat session: {session_name} for user {sanitized_username}"
    )
    return chat_id


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
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit  # Import check_rate_limit async function
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

    # Check if chat session exists, if not, create it using ConsolidatedDatabase
    session = db.get_chat_session(sanitized_chat_id)
    new_session_name = None
    if session is None:
        # New session: derive a name from the first message
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

    # Insert user message if not empty
    if user_message:
        db.add_chat_message(
            sanitized_chat_id,
            0,  # message_index is not used in schema, pass 0
            "user",
            sanitized_user_message,
            None,
        )
    # Insert LLM response if not empty
    if llm_response:
        db.add_chat_message(
            sanitized_chat_id,
            0,
            "assistant",
            sanitized_llm_response,
            None,
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
    # Always return a list of [user, bot] pairs (list of lists of length 2)
    if chat_id in _chat_history_cache:
        logger.debug(f"Returning chat history for {chat_id} from cache.")
        history = _chat_history_cache[chat_id]
        if not history:
            # New chat, no messages
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
    _chat_history_cache[chat_id] = history  # Cache the retrieved history
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
    # If there are no messages at all, return an empty list (valid for Gradio)
    return formatted_history


async def get_chat_metadata(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Retrieves all chat session metadata (session_id, session_name, created_at, updated_at)
    for a given username. Uses and updates in-memory cache.
    """
    return _get_chat_metadata_cache(username)


async def get_chatbot_response(username: str, chat_id: str, message: str):
    """
    Async generator for chatbot response streaming.
    Yields response chunks for Gradio async for streaming.
    """
    """
    Main function to get a chatbot response.
    Handles chat history, LLM interaction, and rate limiting.
    """
    # username is already passed as an argument
    if not username:
        yield "Error: User not logged in. Please log in to chat."
        return

    # Use the async check_rate_limit function for chat operations
    rate_limit_result = await check_rate_limit(username, "chat")
    if not rate_limit_result["allowed"]:
        logger.warning(f"Chat rate limit hit for user: {username}")
        yield "Rate limit exceeded. Please wait a moment before sending another message."
        return

    # Delayed import to avoid circular dependency
    from llm import chatModel

    if not chatModel.is_llm_ready():
        yield "[Error] LLM is not ready. Please try again later."
        return

    sanitized_message = sanitize_input(message)
    # current_history = await get_chat_history(chat_id, username)

    try:
        # chatModel.get_convo_hist_answer expects (question, thread_id)
        result = await chatModel.get_convo_hist_answer(sanitized_message, chat_id)
        answer = result.get("answer", "[No answer generated]")
        yield format_markdown(answer)
        return
    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}")
        yield f"[Error] An unexpected error occurred in backend: {e}"
        return


async def delete_chat_history_for_user(username: str) -> bool:
    """
    Deletes all chat history for a given user.
    """
    db = _get_chat_db_manager()
    sanitized_username = InputSanitizer.sanitize_username(username)

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
        logger.error(f"Error deleting chat session {chat_id} for user {username}: {e}")
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

    try:
        # Ensure session exists or create it (similar to _update_chat_history)
        session_exists_query = (
            "SELECT COUNT(*) FROM chat_sessions WHERE session_id = ? AND username = ?"
        )
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
