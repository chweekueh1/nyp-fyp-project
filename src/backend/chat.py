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

import json
import os
from typing import List, Dict, Any, Tuple, Optional  # noqa: F401
from pathlib import Path
import uuid
from datetime import datetime  # noqa: F401
import difflib  # Import difflib for fuzzy matching

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit, get_rate_limit_info
from .utils import (
    sanitize_input,
)
from .timezone_utils import now_singapore
from infra_utils import setup_logging
from .markdown_formatter import format_markdown

# (Delayed import of llm.chatModel to avoid circular import)


# Set up logging
logger = setup_logging()

# Ensure chat session directory exists (skip during benchmarks)
if not os.environ.get("BENCHMARK_MODE"):
    Path(CHAT_SESSIONS_PATH).mkdir(parents=True, exist_ok=True)

# In-memory store for chat names and metadata
_chat_metadata_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}


def _get_chat_metadata_cache_internal() -> Dict[str, Dict[str, Any]]:
    """
    Returns a reference to the in-memory chat metadata cache.
    This is for internal module use or specific backend interactions.
    """
    return _chat_metadata_cache


def _get_user_chat_dir(username: str) -> Path:
    """
    Get the directory for a user's chat sessions.

    Args:
        username (str): The username.

    Returns:
        Path: Path to the user's chat directory.
    """
    # Always use /home/appuser/.nypai-chatbot/data/chat_sessions as base, never /root/.nypai-chatbot
    base_dir = os.environ.get(
        "CHAT_SESSIONS_PATH", "/home/appuser/.nypai-chatbot/data/chat_sessions"
    )
    return Path(base_dir) / username


def _get_chat_file_path(username: str, chat_id: str) -> Path:
    """
    Get the file path for a specific chat session.

    :param username: The username.
    :type username: str
    :param chat_id: The chat session ID.
    :type chat_id: str
    :return: Path to the chat session file.
    :rtype: Path
    """
    return _get_user_chat_dir(username) / f"{chat_id}.json"


def _load_chat_metadata_cache(username: str) -> None:
    """
    Loads all chat metadata for a user into the in-memory cache.
    This is called once per user login.
    """
    user_chat_dir = _get_user_chat_dir(username)
    if not user_chat_dir.exists():
        _chat_metadata_cache[username] = {}
        return

    user_chats_metadata = {}
    for chat_file in user_chat_dir.glob("*.json"):
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                chat_data = json.load(f)
                chat_id = chat_file.stem
                user_chats_metadata[chat_id] = {
                    "name": chat_data.get("name", "Unnamed Chat"),
                    "created_at": chat_data.get(
                        "created_at", now_singapore().isoformat()
                    ),
                    "updated_at": chat_data.get(
                        "updated_at", now_singapore().isoformat()
                    ),
                    "history": chat_data.get("history", []),
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {chat_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading chat metadata from {chat_file}: {e}")
    _chat_metadata_cache[username] = user_chats_metadata


def _save_chat_metadata_cache(username: str) -> None:
    """
    Saves the in-memory chat metadata cache for a user back to individual JSON files.
    This ensures that updates to names, timestamps, and history are persisted.
    """
    logger.info(
        f"🔍 [SAVE_CACHE] _save_chat_metadata_cache called for user: '{username}'"
    )
    user_chats = _chat_metadata_cache.get(username, {})
    logger.info(f"🔍 [SAVE_CACHE] Saving {len(user_chats)} chats for user '{username}'")
    user_chat_dir = _get_user_chat_dir(username)
    user_chat_dir.mkdir(parents=True, exist_ok=True)

    for chat_id, chat_data in user_chats.items():
        file_path = _get_chat_file_path(username, chat_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving chat data to {file_path}: {e}")


def _get_chat_metadata_cache(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Retrieves the in-memory chat metadata for a user.
    Loads it if not already cached.
    """
    if username not in _chat_metadata_cache:
        _load_chat_metadata_cache(username)
    return _chat_metadata_cache.get(username, {})


def list_user_chat_ids(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Lists all chat IDs and their names for a given user.
    This now returns the full metadata, including history, from the cache.

    :param username: The username.
    :type username: str
    :return: A dictionary where keys are chat IDs and values are dictionaries
             containing 'name', 'created_at', 'updated_at', and 'history' for each chat.
    :rtype: Dict[str, Dict[str, Any]]
    """
    return _get_chat_metadata_cache(username)


def get_chat_history(chat_id: str, username: str) -> List[List[str]]:
    """
    Retrieves the chat history for a specific chat session from the cache.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: A list of lists, where each inner list represents a [user_message, bot_response].
    :rtype: List[List[str]]
    """
    user_chats = _get_chat_metadata_cache(username)
    return user_chats.get(chat_id, {}).get("history", [])


def create_new_chat(username: str, chat_name: str = "New Chat") -> str:
    """
    Creates a new chat session for the user.

    :param username: The username.
    :type username: str
    :param chat_name: The initial name for the new chat.
    :type chat_name: str
    :return: The ID of the newly created chat session.
    :rtype: str
    """
    chat_id = str(uuid.uuid4())
    user_chats = _get_chat_metadata_cache(username)
    user_chats[chat_id] = {
        "name": chat_name,
        "created_at": now_singapore().isoformat(),
        "updated_at": now_singapore().isoformat(),
        "history": [],
    }
    _save_chat_metadata_cache(username)
    logger.info(f"New chat '{chat_name}' created for {username} with ID: {chat_id}")
    return chat_id


def rename_chat(
    chat_id: str, new_name: str, username: str, all_chats_data: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Renames a specific chat session.

    :param chat_id: The ID of the chat session to rename.
    :type chat_id: str
    :param new_name: The new name for the chat session.
    :type new_name: str
    :param username: The current username.
    :type username: str
    :param all_chats_data: The current state of all_chats_data.
    :type all_chats_data: Dict[str, Any]
    :return: A tuple containing a status message and the updated all_chats_data.
    :rtype: Tuple[str, Dict[str, Any]]
    """
    user_chats = _get_chat_metadata_cache(username)
    if chat_id in user_chats:
        user_chats[chat_id]["name"] = new_name
        user_chats[chat_id]["updated_at"] = now_singapore().isoformat()
        _save_chat_metadata_cache(username)
        return f"Chat renamed to '{new_name}'", user_chats
    logger.warning(f"Attempted to rename non-existent chat {chat_id} for {username}")
    return "Failed to rename chat. Chat not found.", all_chats_data


def delete_chat(chat_id: str, username: str) -> bool:
    """
    Deletes a specific chat session.

    :param chat_id: The ID of the chat session to delete.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: True if the chat was deleted, False otherwise.
    :rtype: bool
    """
    user_chats = _get_chat_metadata_cache(username)
    if chat_id in user_chats:
        file_path = _get_chat_file_path(username, chat_id)
        if file_path.exists():
            try:
                file_path.unlink()
                del user_chats[chat_id]
                _save_chat_metadata_cache(username)
                logger.info(f"Chat {chat_id} deleted for {username}")
                return True
            except Exception as e:
                logger.error(f"Error deleting chat file {file_path}: {e}")
                return False
        else:
            del user_chats[chat_id]
            _save_chat_metadata_cache(username)
            logger.warning(f"Chat file {file_path} not found but removed from cache.")
            return True
    return False


def ensure_chat_on_login(username: str) -> str:
    """
    Ensures that a user has at least one chat session upon login.
    If no chats exist, a new one is created.

    :param username: The username.
    :type username: str
    :return: The ID of the current or newly created chat session.
    :rtype: str
    """
    user_chats = _get_chat_metadata_cache(username)
    if not user_chats:
        logger.info(f"No chats found for {username}. Creating a new default chat.")
        return create_new_chat(username, "My First Chat")
    latest_chat_id = max(
        user_chats,
        key=lambda chat_id: user_chats[chat_id].get(
            "updated_at", datetime.min.isoformat()
        ),
        default=None,
    )
    if latest_chat_id:
        return latest_chat_id
    return create_new_chat(username, "My First Chat")


def escape_markdown(text: str) -> str:
    """
    Escapes markdown special characters in a string to prevent formatting issues.

    :param text: The text to escape markdown characters from.
    :type text: str
    :return: The text with markdown special characters escaped.
    :rtype: str
    """
    if not text:
        return text

    # First, handle arrow sequences to prevent them from being split
    # Use temporary placeholders to avoid double-escaping
    text = text.replace("-->", "ARROWLONGPLACEHOLDER")
    text = text.replace("->", "ARROWSHORTPLACEHOLDER")

    # Escape *, _, `, [, ], (, ), ~, >, #, +, -, =, |, {, }, ., !
    special_chars = r"\\`*_{}[]()#+-.!|>~="
    for char in special_chars:
        text = text.replace(char, f"\\{char}")

    # Restore arrow placeholders with proper escaping
    text = text.replace("ARROWLONGPLACEHOLDER", "\\-\\-\\>")
    text = text.replace("ARROWSHORTPLACEHOLDER", "\\-\\>")

    return text


def highlight_query_in_text(text: str, query: str) -> str:
    """
    Highlight all occurrences of the query (or its significant words) in the text,
    escaping markdown and providing context. Avoids overlapping highlights.

    Args:
        text (str): The text to search and highlight in.
        query (str): The search query to highlight.

    Returns:
        str: The text with highlighted query terms and context.
    """
    if not text or not query:
        return escape_markdown(text)

    # Escape markdown before processing
    text_escaped = escape_markdown(text)
    text_lower = text_escaped.lower()
    query_lower = query.lower()

    # Helper to find all non-overlapping matches
    def find_matches(haystack: str, needle: str) -> list:
        matches = []
        start = 0
        while True:
            pos = haystack.find(needle, start)
            if pos == -1:
                break
            matches.append((pos, pos + len(needle)))
            start = pos + len(needle)
        return matches

    matches = find_matches(text_lower, query_lower)

    # If no full query match, try to match significant words (length >= 3)
    if not matches:
        words = [w for w in query_lower.split() if len(w) >= 3]
        for word in words:
            matches.extend(find_matches(text_lower, word))

    if not matches:
        # No matches at all, return truncated text if too long
        return f"{text_escaped[:197]}..." if len(text_escaped) > 200 else text_escaped

    # Merge overlapping matches
    matches.sort()
    merged = []
    for start, end in matches:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    # Build highlighted text
    highlighted = []
    last = 0
    for start, end in merged:
        # Add context before match
        if start > last:
            context = text_escaped[last:start]
            if len(context) > 80:
                context = f"...{context[-77:]}"
            highlighted.append(context)
        # Add highlight
        highlighted.append(f"**`{text_escaped[start:end]}`**")
        last = end
    # Add context after last match
    if last < len(text_escaped):
        context = text_escaped[last:]
        if len(context) > 80:
            context = f"{context[:77]}..."
        highlighted.append(context)

    result = "".join(highlighted)
    # Truncate if too long, preserving highlights
    if len(result) > 500:
        first = result.find("**`")
        start_pos = max(0, first - 50) if first != -1 else 0
        result = f"...{result[start_pos : start_pos + 450]}..."
    return result


def format_search_results(
    search_results: List[Dict[str, Any]], query: str, include_similarity: bool = True
) -> str:
    """
    Format search results for display in UI components.

    This utility function provides consistent formatting for search results
    across different UI modules, reducing code duplication.

    :param search_results: List of search result dictionaries from search_chat_history.
    :type search_results: List[Dict[str, Any]]
    :param query: The original search query.
    :type query: str
    :param include_similarity: Whether to include similarity scores in the output.
    :type include_similarity: bool
    :return: Formatted markdown string with search results.
    :rtype: str
    """
    if not search_results:
        return f"**No results found for '{query}'**\n\nTry increasing the length of the query or using different keywords."

    if include_similarity:
        # Enhanced formatting with similarity scores and better visual hierarchy
        result_text = f"## 🔍 Search Results for '{query}'\n\n"
        result_text += f"**Found {len(search_results)} matching message{'s' if len(search_results) != 1 else ''}:**\n\n"
        result_text += "---\n\n"

        for i, result in enumerate(search_results, 1):
            chat_name = result.get("chat_name", result.get("chat_id", "Unknown Chat"))
            content = result.get("content", "N/A")
            message_type = result.get("message_type", "N/A").capitalize()
            similarity_score = result.get("similarity_score", 0)
            chat_id = result.get("chat_id")
            message_index = result.get("message_index", "N/A")

            # Highlight the query in the content with context
            highlighted_content = highlight_query_in_text(content, query)

            # Create a more visually appealing result format
            result_text += f"### 📝 Result {i}\n\n"

            # Message type and similarity score with visual indicators
            similarity_percentage = f"{similarity_score:.0%}"
            if similarity_score >= 0.8:
                score_indicator = "🟢"
            elif similarity_score >= 0.6:
                score_indicator = "🟡"
            elif similarity_score >= 0.4:
                score_indicator = "🟠"
            else:
                score_indicator = "🔴"

            result_text += f"**{score_indicator} {message_type} Message** (Match: {similarity_percentage})\n\n"

            # Chat information
            result_text += f"**💬 Chat:** {chat_name}\n"
            result_text += f"**🔢 Message Index:** {message_index}\n"
            result_text += f"**🆔 Chat ID:** `{chat_id}`\n\n"

            # Content with better formatting
            result_text += "**📄 Content:**\n\n"
            result_text += f"> {highlighted_content}\n\n"

            # Add separator between results
            if i < len(search_results):
                result_text += "---\n\n"
    else:
        # Simpler formatting without similarity scores (for chat history)
        result_text = f"### Found {len(search_results)} matching entries\n\n"

        for i, result in enumerate(search_results, 1):
            content = result.get("content", "N/A")
            highlighted_content = highlight_query_in_text(content, query)

            result_text += (
                f"**Match {i}:**\n\n"
                f"- **Chat Name:** {result.get('chat_name', 'Unnamed Chat')}\n\n"
                f"- **Chat ID:** `{result.get('chat_id', 'N/A')}`\n\n"
                f"- **Message Type:** {result.get('message_type', 'N/A').capitalize()}\n\n"
                f'- **Content:**\n\n"{highlighted_content}"\n\n'
            )

    return result_text


def search_chat_history(
    search_query: str, username: str, chat_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Search through chat history for a given query for a specific user,
    optionally within a specific chat, using both fuzzy matching with difflib
    and simple substring matching for better results.

    Args:
        search_query (str): The query string to search for.
        username (str): The username whose chats are being searched.
        chat_id (Optional[str], optional): The specific chat ID to search within. If None,
            all chats for the user are searched.

    Returns:
        Tuple[List[Dict[str, Any]], str]: A tuple containing:
            - A list of dictionaries, where each dictionary represents a found match:
              {'chat_id': ..., 'chat_name': ..., 'message_index': ...,
               'message_type': 'user' or 'bot', 'content': ..., 'similarity_score': ...}
            - A status message.
    """
    if not search_query:
        return [], "Please enter a search query."

    sanitized_query = sanitize_input(search_query).lower()
    search_results = []

    # Reload cache to ensure latest data
    _load_chat_metadata_cache(username)
    user_chats = _get_chat_metadata_cache(username)

    # Select chats to search
    if chat_id and chat_id != "all":
        if chat_id in user_chats:
            target_chats = {chat_id: user_chats[chat_id]}
        else:
            return [], "Specified chat not found."
    else:
        target_chats = user_chats

    FUZZY_THRESHOLD = 0.25
    MIN_QUERY_LENGTH = 3
    use_fuzzy = len(sanitized_query) >= MIN_QUERY_LENGTH
    threshold = FUZZY_THRESHOLD if use_fuzzy else 0.1

    def match_score(query: str, text: str) -> float:
        if use_fuzzy:
            return difflib.SequenceMatcher(None, query, text).ratio()
        if query in text:
            match_pos = text.find(query)
            return 1.0 - (match_pos / max(len(text), 1))
        return 0.0

    for current_chat_id, chat_data in target_chats.items():
        chat_name = chat_data.get("name", "Unnamed Chat")
        history = chat_data.get("history", [])
        for i, message_pair in enumerate(history):
            if not isinstance(message_pair, list) or len(message_pair) < 2:
                continue
            user_msg = message_pair[0] or ""
            bot_msg = message_pair[1] or ""
            if not user_msg and not bot_msg:
                continue
            user_score = match_score(sanitized_query, user_msg.lower())
            bot_score = match_score(sanitized_query, bot_msg.lower())
            if user_score >= threshold:
                search_results.append(
                    {
                        "chat_id": current_chat_id,
                        "chat_name": chat_name,
                        "message_index": i,
                        "message_type": "user",
                        "content": user_msg,
                        "similarity_score": round(user_score, 2),
                    }
                )
            if bot_score >= threshold:
                search_results.append(
                    {
                        "chat_id": current_chat_id,
                        "chat_name": chat_name,
                        "message_index": i,
                        "message_type": "bot",
                        "content": bot_msg,
                        "similarity_score": round(bot_score, 2),
                    }
                )

    if search_results:
        search_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        return search_results, f"Found {len(search_results)} matching entries."
    else:
        return [], "No matching entries found."


def _update_chat_history(
    chat_id: str, username: str, user_message: str, bot_response: str
) -> List[List[str]]:
    """
    Internal function to update chat history in memory and persist it.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :param user_message: The user's message.
    :type user_message: str
    :param bot_response: The bot's response.
    :type bot_response: str
    :return: The updated chat history.
    :rtype: List[List[str]]
    """
    logger.info(
        f"🔍 [UPDATE_HISTORY] _update_chat_history called for user: '{username}', chat_id: '{chat_id}'"
    )
    logger.info(
        f"🔍 [UPDATE_HISTORY] User message: '{user_message[:50]}...', Bot response: '{bot_response[:50]}...'"
    )

    user_chats = _get_chat_metadata_cache(username)
    current_chat_id = chat_id

    if current_chat_id == "new_chat_id":
        new_real_chat_id = create_new_chat(username, "New Chat")
        user_chats = _get_chat_metadata_cache(username)
        current_chat_id = new_real_chat_id
        logger.info(f"Created real chat {current_chat_id} from temp new_chat_id.")

    if current_chat_id not in user_chats:
        logger.error(
            f"Chat ID {current_chat_id} not found in user_chats for {username}. Cannot update history."
        )
        return user_chats.get(chat_id, {}).get("history", [])

    history = user_chats[current_chat_id].get("history", [])

    history.append([user_message, bot_response])
    user_chats[current_chat_id]["history"] = history
    user_chats[current_chat_id]["updated_at"] = now_singapore().isoformat()
    logger.info(
        f"🔍 [UPDATE_HISTORY] Updated chat history, now has {len(history)} messages"
    )
    logger.info("🔍 [UPDATE_HISTORY] Saving chat metadata cache...")
    _save_chat_metadata_cache(username)
    logger.info("🔍 [UPDATE_HISTORY] Chat metadata cache saved successfully")
    return history


# --- Main Chatbot Response Function ---
# This is where LLM interaction happens
async def get_chatbot_response(
    message: str, history: List[List[str]], username: str, chat_id: str
) -> Tuple[str, List[List[str]], str, Dict[str, Any], str]:
    """
    Generates a chatbot response to a user message, updates chat history,
    and handles chat ID creation for new chats.

    :param message: The user's input message.
    :type message: str
    :param history: The current chat history (list of [user, bot] pairs).
    :type history: List[List[str]]
    :param username: The current username.
    :type username: str
    :param chat_id: The current chat ID. Can be a temporary "new_chat_id".
    :type chat_id: str
    :return: A tuple of 5 values:
             (empty_message_input, updated_history, current_chat_id, all_user_chats_data, debug_info)
    :rtype: Tuple[str, List[List[str]], str, Dict[str, Any], str]
    """
    # Delayed import to avoid circular import
    from llm.chatModel import get_convo_hist_answer, initialize_llm_and_db, is_llm_ready

    # Ensure LLM and DB are initialized for every call (safe due to internal lock)
    if not is_llm_ready():
        await initialize_llm_and_db()

    if not is_llm_ready():
        logger.error("LLM and DB are not ready after initialization attempt.")
        error_response = (
            "I'm sorry, the AI system is not ready. Please try again later."
        )
        current_history = history if history is not None else []
        return (
            "",
            current_history,
            chat_id,
            _get_chat_metadata_cache(username),
            "AI system initialization failed.",
        )

    if not message:
        user_chats = _get_chat_metadata_cache(username)
        return "", history, chat_id, user_chats, "Empty message. No action taken."

    # Initial check for rate limits
    rate_limited = await check_rate_limit(username, "chat_message")
    if not rate_limited:
        limit_info = get_rate_limit_info("chat")
        error_response = f"Rate limit exceeded. Please wait {limit_info['time_to_wait']:.1f} seconds."
        updated_history = _update_chat_history(
            chat_id, username, message, error_response
        )
        user_chats = _get_chat_metadata_cache(username)
        return (
            "",
            updated_history,
            chat_id,
            user_chats,
            f"Rate limit hit: {limit_info['time_to_wait']:.1f}s wait.",
        )

    try:
        result = await get_convo_hist_answer(message, chat_id)

        answer_text = result.get("answer", "No answer generated by AI.")

        # Apply unified markdown formatting (includes Mermaid validation)
        answer_text = format_markdown(answer_text)

        is_error_from_chatModel = (
            "I'm sorry, the AI assistant is not fully set up." in answer_text
            or "I'm sorry, I cannot process your request right now" in answer_text
            or "I'm sorry, I encountered an error" in answer_text
        )

        if not is_error_from_chatModel:
            updated_history = _update_chat_history(
                chat_id, username, message, answer_text
            )
            user_chats_after_update = _get_chat_metadata_cache(username)
            final_chat_id = chat_id
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
            updated_history = _update_chat_history(
                chat_id, username, message, error_response
            )
            user_chats_after_update = _get_chat_metadata_cache(username)
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
        updated_history = _update_chat_history(
            chat_id, username, message, error_response
        )
        user_chats_after_update = _get_chat_metadata_cache(username)
        final_chat_id = chat_id
        return (
            "",
            updated_history,
            final_chat_id,
            user_chats_after_update,
            f"Unexpected error in get_chatbot_response: {e}",
        )
