# backend/chat.py
#!/usr/bin/env python3
"""
Chat module for the backend.
Contains chat-related functions for handling conversations and chat history,
including persistence, loading, searching, and renaming.
"""

import json
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
import uuid
from datetime import datetime

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit, get_rate_limit_info
from .utils import (
    sanitize_input,
    save_message_async,
)
from .timezone_utils import now_singapore


# Set up logging
logger = logging.getLogger(__name__)

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


def _get_chat_file_path(chat_id: str, username: str) -> Path:
    """
    Get the file path for a specific chat session.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: Path to the chat session file.
    :rtype: Path
    """
    return _get_user_chat_dir(username) / f"{chat_id}.json"


def _get_user_chats_metadata_file(username: str) -> Path:
    """
    Get the file path for a user's chat metadata.

    :param username: The username.
    :type username: str
    :return: Path to the user's chat metadata file.
    :rtype: Path
    """
    return _get_user_chat_dir(username) / "user_chats.json"


def _load_chat_metadata_from_file(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Load chat metadata for a user from their user_chats.json file.

    :param username: The username.
    :type username: str
    :return: Dictionary of chat metadata, or an empty dictionary if file not found.
    :rtype: Dict[str, Dict[str, Any]]
    """
    metadata_file = _get_user_chats_metadata_file(username)
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding user_chats.json for {username}: {e}")
            # Consider backing up corrupted file and starting fresh or attempting recovery
            return {}
    return {}


def _save_chat_metadata_cache(username: str) -> None:
    """
    Save the in-memory chat metadata cache for a user to their user_chats.json file.

    :param username: The username.
    :type username: str
    :raises IOError: If there's an error writing to the file.
    """
    metadata_file = _get_user_chats_metadata_file(username)
    user_chat_dir = _get_user_chat_dir(username)
    user_chat_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(_chat_metadata_cache.get(username, {}), f, indent=4)
    except IOError as e:
        logger.error(f"Error saving user_chats.json for {username}: {e}")
        raise  # Re-raise to indicate a critical persistence error


def _get_chat_metadata_cache(
    username: str, force_reload: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Get the in-memory chat metadata cache for a user.
    Loads from file if not in cache or if force_reload is True.

    :param username: The username.
    :type username: str
    :param force_reload: If True, forces a reload from disk, bypassing the cache.
    :type force_reload: bool
    :return: Dictionary of chat metadata.
    :rtype: Dict[str, Dict[str, Any]]
    """
    if (
        username not in _chat_metadata_cache
        or not _chat_metadata_cache[username]
        or force_reload
    ):
        _chat_metadata_cache[username] = _load_chat_metadata_from_file(username)
        logger.debug(f"Refreshed chat metadata cache for {username}.")
    return _chat_metadata_cache[username]


def ensure_chat_on_login(username: str) -> str:
    """
    Ensures a chat exists for the user upon login. If no chats exist,
    a new default chat is created and persisted.

    :param username: The username.
    :type username: str
    :return: The ID of the ensured (or newly created) chat.
    :rtype: str
    """
    user_chats = _get_chat_metadata_cache(username)
    if not user_chats:
        logger.info(f"No chats found for {username}. Creating a new default chat.")
        chat_id = str(uuid.uuid4())
        default_chat_name = "New Chat"
        user_chats[chat_id] = {
            "name": default_chat_name,
            "created_at": now_singapore().isoformat(),
            "updated_at": now_singapore().isoformat(),
        }
        _chat_metadata_cache[username] = user_chats  # Update the cache directly
        _save_chat_metadata_cache(username)
        # Create an empty chat file
        chat_file = _get_chat_file_path(chat_id, username)
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump([], f)  # Empty history for a new chat
        logger.info(
            f"Created default chat '{default_chat_name}' ({chat_id}) for {username}."
        )
        return chat_id
    else:
        # Return the ID of the most recently updated chat or the first one found
        latest_chat_id = None
        latest_timestamp = None
        for cid, data in user_chats.items():
            updated_at_str = data.get("updated_at")
            if updated_at_str:
                updated_at = datetime.fromisoformat(updated_at_str)
                if latest_timestamp is None or updated_at > latest_timestamp:
                    latest_timestamp = updated_at
                    latest_chat_id = cid
        return latest_chat_id if latest_chat_id else next(iter(user_chats.keys()))


def list_user_chat_ids(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Lists all chat IDs and their metadata for a given user, forcing a reload of metadata.

    :param username: The username.
    :type username: str
    :return: A dictionary of chat IDs mapped to their metadata (name, created_at, updated_at).
    :rtype: Dict[str, Dict[str, Any]]
    """
    # Force reload metadata to ensure the dropdown always has the latest names/IDs
    user_chats = _get_chat_metadata_cache(username, force_reload=True)
    return user_chats


def get_chat_history(chat_id: str, username: str) -> List[List[str]]:
    """
    Retrieves the full chat history for a specific chat ID and user.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: A list of message pairs (user_message, bot_response).
    :rtype: List[List[str]]
    """
    chat_file = _get_chat_file_path(chat_id, username)
    if chat_file.exists():
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                history_raw = json.load(f)
                # Convert history to the [user_msg, bot_msg] format expected by Gradio
                # The stored format seems to be {"role": "user/assistant", "content": "..."}
                # We need to pair them up.
                parsed_history = []
                user_message = None
                for msg in history_raw:
                    if msg.get("role") == "user":
                        user_message = msg.get("content", "")
                    elif msg.get("role") == "assistant" and user_message is not None:
                        parsed_history.append([user_message, msg.get("content", "")])
                        user_message = None  # Reset for next pair
                return parsed_history
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding chat file {chat_file}: {e}")
            return []
    return []


def get_chat_name(chat_id: str, username: str) -> str:
    """
    Retrieves the name of a specific chat session.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: The name of the chat, or the chat ID if not found.
    :rtype: str
    """
    user_chats = _get_chat_metadata_cache(username)
    return user_chats.get(chat_id, {}).get("name", chat_id)


def create_new_chat(username: str) -> Dict[str, Any]:
    """
    Creates a new chat session, persists its metadata, and returns its details.

    :param username: The username for whom to create the chat.
    :type username: str
    :return: A dictionary containing the ID, name, and updated_at timestamp of the newly created chat.
    :rtype: Dict[str, Any]
    """
    chat_id = str(uuid.uuid4())
    user_chats = _get_chat_metadata_cache(username)
    default_chat_name = (
        f"Chat {len(user_chats) + 1}"  # Use len of current chats for numbering
    )

    new_chat_data = {
        "name": default_chat_name,
        "created_at": now_singapore().isoformat(),
        "updated_at": now_singapore().isoformat(),
    }
    user_chats[chat_id] = new_chat_data
    _chat_metadata_cache[username] = user_chats  # Update the cache directly
    _save_chat_metadata_cache(username)

    # Create an empty chat file for the new session
    chat_file = _get_chat_file_path(chat_id, username)
    with open(chat_file, "w", encoding="utf-8") as f:
        json.dump([], f)  # Empty history for a new chat
    logger.info(f"Created new chat '{default_chat_name}' ({chat_id}) for {username}.")

    return {"chat_id": chat_id, **new_chat_data}


def rename_chat(chat_id: str, username: str, new_name: str) -> bool:
    """
    Renames an existing chat session.

    :param chat_id: The ID of the chat to rename.
    :type chat_id: str
    :param username: The username who owns the chat.
    :type username: str
    :param new_name: The new name for the chat.
    :type new_name: str
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    user_chats = _get_chat_metadata_cache(
        username
    )  # Get the current metadata (might be cached)
    if chat_id not in user_chats:
        logger.warning(f"Chat {chat_id} not found for user {username} during rename.")
        return False

    user_chats[chat_id]["name"] = new_name
    user_chats[chat_id]["updated_at"] = (
        now_singapore().isoformat()
    )  # Update timestamp on rename
    _chat_metadata_cache[username] = user_chats  # Update the cache directly
    _save_chat_metadata_cache(username)  # Persist the updated metadata to disk
    logger.info(f"Chat {chat_id} renamed to '{new_name}' for user {username}.")
    return True


def all_history_text_snippet(history: List[List[str]], max_len: int) -> str:
    """
    Generates a snippet of the entire chat history for search results.

    :param history: The chat history (list of [user_msg, bot_msg] pairs).
    :type history: List[List[str]]
    :param max_len: Maximum length of the snippet.
    :type max_len: int
    :return: A truncated string of the chat history.
    :rtype: str
    """
    full_text = " ".join(
        [f"{msg[0]} {msg[1]}" for msg in history if msg and len(msg) == 2]
    )  # Ensure msg is valid
    return f"{full_text[:max_len]}..." if len(full_text) > max_len else full_text


def fuzzy_search_chats(search_query: str, username: str) -> List[Tuple[str, str, str]]:
    """
    Performs a fuzzy search through all chat sessions for a given user.
    Searches chat names and message content.

    :param search_query: The query string to search for.
    :type search_query: str
    :param username: The username performing the search.
    :type username: str
    :return: A list of tuples (chat_id, chat_name, matching_snippet) for found results.
    :rtype: List[Tuple[str, str, str]]
    """
    if not username:
        return []
    if not search_query:
        return []

    all_user_chats_metadata = _get_chat_metadata_cache(username, force_reload=True)
    if not all_user_chats_metadata:
        return []

    results = []
    search_query_lower = search_query.lower()

    for chat_id, chat_data in all_user_chats_metadata.items():
        chat_name = chat_data.get("name", chat_id)

        # Load the actual chat history for content search
        chat_history_list = get_chat_history(chat_id, username)

        # Combine name and all messages for search
        all_text = chat_name.lower()
        for msg_pair in chat_history_list:
            if msg_pair and len(msg_pair) == 2:
                all_text += " " + str(msg_pair[0]).lower()  # User message
                all_text += " " + str(msg_pair[1]).lower()  # Bot response

        if search_query_lower in all_text:
            # If a direct substring match, add it
            results.append(
                (chat_id, chat_name, all_history_text_snippet(chat_history_list, 100))
            )

    return results


def search_chat_history(username: str, query: str) -> List[Tuple[str, str, str]]:
    """
    Search chat history for the given user and query.

    This function performs a fuzzy search through chat names and message content.

    :param username: The username performing the search.
    :type username: str
    :param query: The search query string.
    :type query: str
    :return: A list of tuples (chat_id, chat_name, matching_snippet) for found results.
    :rtype: List[Tuple[str, str, str]]
    """
    return fuzzy_search_chats(query, username)


async def ask_question(
    question: str, chat_id: str, username: str
) -> dict[str, str | dict]:
    """
    Ask a question and get a response from the chatbot.

    This asynchronous function processes a user's question, applies rate limiting,
    sanitizes the input, calls the LLM, and persists both the user's message
    and the bot's response to the chat session file.

    :param question: The user's question.
    :type question: str
    :param chat_id: The ID of the current chat session.
    :type chat_id: str
    :param username: The username of the current user.
    :type username: str
    :return: A dictionary containing the response status, code, and the bot's answer.
             Includes error information if the operation fails or rate limit is exceeded.
    :rtype: dict[str, str | dict]
    """
    logger.info(
        f"ask_question called with question={question!r}, chat_id={chat_id!r}, username={username!r}"
    )
    if not question or not chat_id or not username:
        return {"error": "Invalid question or chat_id or username", "code": "400"}

    sanitized_question = sanitize_input(question)
    try:
        # Lazily import get_llm_functions here to break the circular dependency
        from .database import get_llm_functions

        # Get LLM functions
        llm_funcs = get_llm_functions()
        if not llm_funcs or not llm_funcs["is_llm_ready"]():
            logger.error(
                "LLM/DB not ready in ask_question. Backend may not be fully initialized."
            )
            return {
                "error": "AI assistant is not fully initialized. Please try again later.",
                "code": "500",
            }

        response = llm_funcs["get_convo_hist_answer"](sanitized_question, chat_id)

        # Save user message
        await save_message_async(
            username, chat_id, {"role": "user", "content": sanitized_question}
        )

        # Save bot response
        if isinstance(response, dict) and "answer" in response:
            answer = response["answer"]
        else:
            answer = str(response)

        await save_message_async(
            username, chat_id, {"role": "assistant", "content": answer}
        )

        return {"status": "OK", "code": "200", "response": response}
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return {"error": str(e), "code": "500"}


async def get_chatbot_response(
    message: str, history: List[List[str]], username: str, chat_id: str
) -> Dict[str, Any]:
    """
    Main function to get a chatbot response, handling persistence and rate limits.

    :param message: The current user message.
    :type message: str
    :param history: The current chat history (messages from both user and bot).
    :type history: List[List[str]]
    :param username: The username.
    :type username: str
    :param chat_id: The ID of the current chat.
    :type chat_id: str
    :return: A dictionary containing the updated history, bot response, and debug info.
    :rtype: Dict[str, Any]
    """
    if not username:
        return {
            "history": history,
            "response": "[Error] Please login to use the chatbot.",
            "debug": "User not logged in.",
        }
    if not chat_id:
        return {
            "history": history,
            "response": "[Error] No active chat session. Please create or select one.",
            "debug": "No chat_id provided.",
        }

    # Check rate limit for chat operations
    if not await check_rate_limit(username, "chat"):
        rate_limit_info = get_rate_limit_info("chat")
        return {
            "history": history,
            "response": f"[Error] Rate limit exceeded. Please wait {rate_limit_info['time_window']} seconds.",
            "debug": "Rate limit exceeded.",
        }
    try:
        result = await ask_question(message, chat_id, username)

        if result.get("code") == "200" or result.get("status") == "OK":
            answer = result.get("response", "")
            if isinstance(answer, dict) and "answer" in answer:
                answer_text = answer["answer"]
            else:
                answer_text = str(answer)

            updated_history = get_chat_history(chat_id, username)

            user_chats = _get_chat_metadata_cache(username)
            if chat_id in user_chats:
                user_chats[chat_id]["updated_at"] = now_singapore().isoformat()
                _chat_metadata_cache[username] = user_chats
                _save_chat_metadata_cache(username)
            return {
                "history": updated_history,
                "response": answer_text,
                "debug": "Message processed and LLM response obtained.",
            }
        else:
            error_msg = result.get("error", "An unknown error occurred from LLM.")
            if isinstance(result.get("response"), dict) and "answer" in result.get(
                "response"
            ):
                error_msg = result["response"]["answer"]

            updated_history = get_chat_history(chat_id, username)

            return {
                "history": updated_history,
                "response": f"[Error] {error_msg}",
                "debug": f"Error during question: {error_msg}",
            }
    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}")
        return {
            "history": history,
            "response": f"[Error] An unexpected error occurred in backend: {e}",
            "debug": f"Unexpected error in get_chatbot_response: {e}",
        }
