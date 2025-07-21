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
import uuid
from datetime import datetime

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit
from .utils import (
    sanitize_input,
)
from .timezone_utils import get_utc_timestamp
from infra_utils import setup_logging
from .markdown_formatter import format_markdown
from .consolidated_database import (
    get_chat_database,
    get_user_database,
)  # Import get_chat_database

# (Delayed import of llm.chatModel to avoid circular import)


# Set up logging
logger = setup_logging()

# Ensure chat session directory exists (skip during benchmarks)
if not os.environ.get("BENCHMARK_MODE"):
    Path(CHAT_SESSIONS_PATH).mkdir(parents=True, exist_ok=True)

# In-memory store for chat names and metadata
_chat_metadata_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

# Initialize chat database instance
chat_db = get_chat_database()
user_db = (
    get_user_database()
)  # Needed to convert user_id to username if necessary for chat_db


def _get_username_from_id(user_id: int) -> Optional[str]:
    """Helper to retrieve username from user ID."""
    try:
        result = user_db.fetch_one(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        )
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error fetching username for user ID {user_id}: {e}")
        return None


def _load_chat_metadata_from_db(username: str):
    """Loads chat metadata from the database into the cache."""
    try:
        sessions = chat_db.fetch_all(
            "SELECT chat_id, chat_name, created_at, updated_at FROM chat_sessions WHERE username = ?",
            (username,),
        )
        _chat_metadata_cache[username] = {
            session["chat_id"]: {
                "chat_name": session["chat_name"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
            }
            for session in sessions
        }
        logger.info(f"Loaded {len(sessions)} chat sessions for {username} from DB.")
    except Exception as e:
        logger.error(f"Error loading chat metadata from DB for {username}: {e}")
        _chat_metadata_cache[username] = {}  # Ensure it's initialized even on error


def _get_chat_metadata_cache(username: str) -> Dict[str, Any]:
    """
    Returns the chat metadata cache for a user.
    Loads from DB if not already in cache.
    """
    if username not in _chat_metadata_cache:
        _load_chat_metadata_from_db(username)
    return _chat_metadata_cache.get(username, {})


async def get_all_chats(user_id: int) -> Dict[str, Any]:
    """
    Retrieve all chat sessions for a given user from the database.
    """
    username = _get_username_from_id(user_id)
    if not username:
        return {"error": "User not found"}

    try:
        _load_chat_metadata_from_db(username)  # Ensure cache is fresh
        chats = _get_chat_metadata_cache(username)
        # Convert dictionary to list of dicts for frontend consumption if needed
        chat_list = [{"chat_id": chat_id, **data} for chat_id, data in chats.items()]
        # Sort by updated_at, most recent first
        chat_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return {"chats": chat_list}
    except Exception as e:
        logger.error(f"Error getting all chats for {username}: {e}")
        return {"error": f"Failed to retrieve chats: {e}"}


async def get_chat_history(chat_id: str) -> List[Dict[str, str]]:
    """
    Load chat history for a given chat ID from the database.
    """
    try:
        messages = chat_db.fetch_all(
            "SELECT role, content FROM chat_messages WHERE chat_id = ? ORDER BY message_index ASC",
            (chat_id,),
        )
        history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        logger.info(f"Loaded {len(history)} messages for chat_id {chat_id} from DB.")
        return history
    except Exception as e:
        logger.error(f"Error loading chat history for {chat_id}: {e}")
        return []


async def new_chat_session(username: str) -> Dict[str, Any]:
    """
    Create a new chat session and return its ID.
    """
    new_chat_id = str(uuid.uuid4())
    timestamp = get_utc_timestamp()
    chat_name = (
        f"New Chat {datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')}"
    )

    try:
        chat_db.execute_insert(
            "INSERT INTO chat_sessions (username, chat_id, chat_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (username, new_chat_id, chat_name, timestamp, timestamp),
        )
        _chat_metadata_cache.setdefault(username, {})[new_chat_id] = {
            "chat_name": chat_name,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        logger.info(f"New chat session created for {username}: {new_chat_id}")
        return {"chat_id": new_chat_id, "chat_name": chat_name}
    except Exception as e:
        logger.error(f"Error creating new chat session for {username}: {e}")
        return {"error": f"Failed to create new chat session: {e}"}


async def rename_chat(
    username: str, chat_id: str, new_chat_name: str
) -> Dict[str, Any]:
    """
    Rename a chat session.
    """
    # Sanitize new_chat_name using InputSanitizer (if applicable for display)
    # For DB updates, parameterized queries handle injection.
    sanitized_name = sanitize_input(
        new_chat_name
    )  # Assuming sanitize_input uses InputSanitizer
    timestamp = get_utc_timestamp()

    try:
        chat_db.execute_query(
            "UPDATE chat_sessions SET chat_name = ?, updated_at = ? WHERE username = ? AND chat_id = ?",
            (sanitized_name, timestamp, username, chat_id),
        )
        if (
            username in _chat_metadata_cache
            and chat_id in _chat_metadata_cache[username]
        ):
            _chat_metadata_cache[username][chat_id]["chat_name"] = sanitized_name
            _chat_metadata_cache[username][chat_id]["updated_at"] = timestamp
        logger.info(
            f"Chat session {chat_id} renamed to '{sanitized_name}' by {username}."
        )
        return {"success": True, "chat_id": chat_id, "new_chat_name": sanitized_name}
    except Exception as e:
        logger.error(f"Error renaming chat session {chat_id} for {username}: {e}")
        return {"success": False, "message": f"Failed to rename chat: {e}"}


async def delete_chat_session(username: str, chat_id: str) -> Dict[str, Any]:
    """
    Delete a chat session and its messages.
    """
    try:
        # Delete messages first due to foreign key constraint
        chat_db.execute_query("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
        chat_db.execute_query(
            "DELETE FROM chat_sessions WHERE username = ? AND chat_id = ?",
            (username, chat_id),
        )

        if (
            username in _chat_metadata_cache
            and chat_id in _chat_metadata_cache[username]
        ):
            del _chat_metadata_cache[username][chat_id]
        logger.info(f"Chat session {chat_id} deleted by {username}.")
        return {"success": True, "chat_id": chat_id}
    except Exception as e:
        logger.error(f"Error deleting chat session {chat_id} for {username}: {e}")
        return {"success": False, "message": f"Failed to delete chat: {e}"}


async def _update_chat_history(
    chat_id: str, username: str, user_message: str, llm_response: str
) -> List[Dict[str, str]]:
    """
    Updates the chat history in the database and returns the full history.
    """
    timestamp = get_utc_timestamp()

    # Get the next message index
    last_message_index_result = chat_db.fetch_one(
        "SELECT MAX(message_index) FROM chat_messages WHERE chat_id = ?", (chat_id,)
    )
    last_message_index = (
        last_message_index_result[0]
        if last_message_index_result and last_message_index_result[0] is not None
        else -1
    )
    next_message_index = last_message_index + 1

    # Insert user message
    chat_db.execute_insert(
        "INSERT INTO chat_messages (chat_id, message_index, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (chat_id, next_message_index, "user", user_message, timestamp),
    )

    # Insert LLM response
    chat_db.execute_insert(
        "INSERT INTO chat_messages (chat_id, message_index, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (chat_id, next_message_index + 1, "assistant", llm_response, timestamp),
    )

    # Update session timestamp
    chat_db.execute_query(
        "UPDATE chat_sessions SET updated_at = ? WHERE chat_id = ?",
        (timestamp, chat_id),
    )

    # Update in-memory cache
    if username in _chat_metadata_cache and chat_id in _chat_metadata_cache[username]:
        _chat_metadata_cache[username][chat_id]["updated_at"] = timestamp

    # Return the updated full history
    return await get_chat_history(chat_id)


async def search_chat_history(user_id: int, query: str) -> Dict[str, Any]:
    """
    Search chat messages for a given query for a user.
    """
    username = _get_username_from_id(user_id)
    if not username:
        return {"error": "User not found"}

    sanitized_query = sanitize_input(query)
    search_pattern = f"%{sanitized_query}%"  # Use LIKE for fuzzy matching in SQL

    try:
        # Get chat IDs for the user first
        user_chat_ids_result = chat_db.fetch_all(
            "SELECT chat_id FROM chat_sessions WHERE username = ?", (username,)
        )
        user_chat_ids = [row["chat_id"] for row in user_chat_ids_result]

        if not user_chat_ids:
            return {"results": []}

        # Search messages within those chat IDs
        # Using a parameterized query with IN clause
        placeholders = ",".join("?" for _ in user_chat_ids)
        query_messages = f"""
            SELECT cs.chat_name, cm.chat_id, cm.role, cm.content, cm.timestamp
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.chat_id = cs.chat_id
            WHERE cm.chat_id IN ({placeholders}) AND cm.content LIKE ?
            ORDER BY cm.timestamp DESC
        """
        params = tuple(user_chat_ids) + (search_pattern,)
        results = chat_db.fetch_all(query_messages, params)

        found_messages = [
            {
                "chat_name": row["chat_name"],
                "chat_id": row["chat_id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            for row in results
        ]
        logger.info(
            f"Found {len(found_messages)} messages for search query '{query}' by {username}."
        )
        return {"results": found_messages}
    except Exception as e:
        logger.error(
            f"Error searching chat history for {username} with query '{query}': {e}"
        )
        return {"error": f"Failed to search chats: {e}"}


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
            f"--- Chat: '{chat_name}' (ID: {chat_id_display}) ---\n"
            f"  Role: {role}\n"
            f"  Time: {timestamp}\n"
            f"  Content: {content}\n"
            f"----------------------------------------"
        )
    return formatted_output


async def get_chatbot_response(
    message: str, chat_id: str, user_id: int
) -> Tuple[str, List[Dict[str, str]], str, Dict[str, Any], str]:
    """
    Get a chatbot response based on the message and chat history.
    """
    from llm import chatModel  # Delayed import

    username = _get_username_from_id(user_id)
    if not username:
        return "", [], chat_id, {}, "Error: User not found."

    if not await check_rate_limit(username, "chat"):
        return (
            "",
            [],
            chat_id,
            _get_chat_metadata_cache(username),
            "Rate limit exceeded. Please try again later.",
        )

    history = await get_chat_history(chat_id)
    llm_functions = chatModel.get_llm_functions()
    get_convo_hist_answer = llm_functions["get_convo_hist_answer"]

    try:
        answer_text, is_success = await get_convo_hist_answer(message, history)

        if is_success:
            # Format the answer text (e.g., Markdown)
            formatted_answer = format_markdown(answer_text)
            updated_history = await _update_chat_history(
                chat_id, username, message, formatted_answer
            )
            user_chats_after_update = _get_chat_metadata_cache(
                username
            )  # Refresh cache after update
            final_chat_id = chat_id
            # If it's a new chat, update chat_id to the new one generated by database
            # (Note: consolidated_database now assigns chat_id directly, so "new_chat_id" logic might change)
            if chat_id == "new_chat_id" and user_chats_after_update:
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
