# backend/chat.py
#!/usr/bin/env python3
"""
Chat module for the backend.
Contains chat-related functions for handling conversations and chat history,
including persistence, loading, searching, and renaming.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import uuid
from datetime import datetime

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit, get_rate_limit_info
from .utils import (
    sanitize_input,
)
from .timezone_utils import now_singapore
from infra_utils import setup_logging

# New imports from chatModel.py
from llm.chatModel import get_convo_hist_answer, initialize_llm_and_db, is_llm_ready


# Set up logging
logger = setup_logging()

# Ensure chat session directory exists
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

    :param username: The username.
    :type username: str
    :return: Path to the user's chat directory.
    :rtype: Path
    """
    return Path(CHAT_SESSIONS_PATH) / username


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
    user_chats = _chat_metadata_cache.get(username, {})
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


def search_chat_history(
    search_query: str, username: str, chat_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Searches through chat history for a given query for a specific user,
    optionally within a specific chat.

    :param search_query: The query string to search for.
    :type search_query: str
    :param username: The username whose chats are being searched.
    :type username: str
    :param chat_id: Optional. The specific chat ID to search within. If None,
                    all chats for the user are searched.
    :type chat_id: Optional[str]
    :return: A tuple containing:
                - A list of dictionaries, where each dictionary represents a found match:
                  {'chat_id': ..., 'chat_name': ..., 'message_index': ...,
                   'message_type': 'user' or 'bot', 'content': ...}
                - A status message.
    :rtype: Tuple[List[Dict[str, Any]], str]
    """
    if not search_query:
        return [], "Please enter a search query."

    sanitized_query = sanitize_input(search_query)
    search_results = []
    user_chats = _get_chat_metadata_cache(username)

    target_chats = {}
    if chat_id and chat_id != "all":
        if chat_id in user_chats:
            target_chats[chat_id] = user_chats[chat_id]
        else:
            return [], "Specified chat not found."
    else:
        target_chats = user_chats

    for current_chat_id, chat_data in target_chats.items():
        chat_name = chat_data.get("name", "Unnamed Chat")
        history = chat_data.get("history", [])

        for i, message_pair in enumerate(history):
            user_msg = message_pair[0]
            bot_resp = message_pair[1]

            if sanitized_query.lower() in user_msg.lower():
                search_results.append(
                    {
                        "chat_id": current_chat_id,
                        "chat_name": chat_name,
                        "message_index": i,
                        "message_type": "user",
                        "content": user_msg,
                    }
                )
            if sanitized_query.lower() in bot_resp.lower():
                search_results.append(
                    {
                        "chat_id": current_chat_id,
                        "chat_name": chat_name,
                        "message_index": i,
                        "message_type": "bot",
                        "content": bot_resp,
                    }
                )

    if search_results:
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
    _save_chat_metadata_cache(username)
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
    # Ensure LLM and DB are initialized for every call (safe due to internal lock)
    if not is_llm_ready():
        await initialize_llm_and_db()  # Await this call

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
