# backend/chat.py
#!/usr/bin/env python3
"""
Chat module for the backend.
Contains chat-related functions for handling conversations and chat history,
including persistence, loading, searching, and renaming.
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime

from .config import CHAT_SESSIONS_PATH
from .rate_limiting import check_rate_limit, get_rate_limit_info
from .utils import (
    sanitize_input,
    save_message_async,
)  # Assuming save_message_async handles persistence

# The import for get_llm_functions is now lazy-loaded within ask_question
from .timezone_utils import now_singapore

# Set up logging
logger = logging.getLogger(__name__)

# Ensure chat session directory exists
Path(CHAT_SESSIONS_PATH).mkdir(parents=True, exist_ok=True)

# In-memory store for chat names and metadata
_chat_metadata_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}


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

    :param chat_id: The ID of the chat.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: Path to the chat file.
    :rtype: Path
    """
    user_chat_dir = _get_user_chat_dir(username)
    return user_chat_dir / f"{chat_id}.json"


def _load_chat_metadata(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Load chat metadata for a user from disk.

    :param username: The username.
    :type username: str
    :return: Dictionary of chat metadata.
    :rtype: Dict[str, Dict[str, Any]]
    """
    user_chat_dir = _get_user_chat_dir(username)
    metadata_file = user_chat_dir / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding metadata for user {username}: {e}")
            return {}
    return {}


def _save_chat_metadata(username: str, metadata: Dict[str, Dict[str, Any]]) -> None:
    """
    Save chat metadata for a user to disk.

    :param username: The username.
    :type username: str
    :param metadata: Dictionary of chat metadata.
    :type metadata: Dict[str, Dict[str, Any]]
    """
    user_chat_dir = _get_user_chat_dir(username)
    user_chat_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    metadata_file = user_chat_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)


def list_user_chat_ids(username: str) -> List[str]:
    """
    List all chat IDs for a given user.

    :param username: The username.
    :type username: str
    :return: List of chat IDs.
    :rtype: List[str]
    """
    user_chat_dir = _get_user_chat_dir(username)
    if not user_chat_dir.exists():
        return []
    # Load from metadata, fallback to scanning files if metadata not found
    metadata = _load_chat_metadata(username)
    if metadata:
        return list(metadata.keys())
    else:
        # Fallback to scanning .json files, but prefer metadata.json
        return [
            f.stem
            for f in user_chat_dir.iterdir()
            if f.suffix == ".json" and f.stem != "metadata"
        ]


def get_chat_history(chat_id: str, username: str) -> List[List[str]]:
    """
    Retrieve the chat history for a given chat ID and username.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: A list of message pairs (user, bot).
    :rtype: List[List[str]]
    """
    file_path = _get_chat_file_path(chat_id, username)
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure data is a list of lists or equivalent for Gradio Chatbot
            # Assumes chat data is stored as a list of dictionaries with 'role' and 'content'
            history = []
            for msg in data.get("messages", []):
                if msg["role"] == "user":
                    history.append([msg["content"], None])
                elif msg["role"] == "assistant":
                    if history and history[-1][1] is None:
                        history[-1][1] = msg["content"]
                    else:
                        # This handles cases where assistant message might not directly follow user
                        # or if history is empty (e.g. first message is bot-generated)
                        history.append([None, msg["content"]])
            return history
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding chat file {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load chat history from {file_path}: {e}")
        return []


def create_and_persist_new_chat(username: str) -> str:
    """
    Create a new chat session for the user and persist it to disk.
    If the user has no existing chats, this will be their first.

    :param username: The username for whom to create the chat.
    :type username: str
    :return: The ID of the newly created chat session.
    :rtype: str
    """
    new_chat_id = str(uuid.uuid4())
    user_chat_dir = _get_user_chat_dir(username)
    user_chat_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    # Create an empty chat file
    file_path = _get_chat_file_path(new_chat_id, username)
    initial_chat_data = {
        "chat_id": new_chat_id,
        "name": f"New Chat {now_singapore().strftime('%H:%M')}",
        "created_at": now_singapore().isoformat(),
        "messages": [],
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(initial_chat_data, f, indent=4)

    # Update metadata
    metadata = _load_chat_metadata(username)
    metadata[new_chat_id] = {
        "name": initial_chat_data["name"],
        "created_at": initial_chat_data["created_at"],
    }
    _save_chat_metadata(username, metadata)

    logger.info(f"Created new chat {new_chat_id} for user {username}")
    return new_chat_id


def get_chat_name(chat_id: str, username: str) -> str:
    """
    Get the name of a chat session.

    :param chat_id: The ID of the chat session.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :return: The name of the chat, or a default name if not found.
    :rtype: str
    """
    metadata = _load_chat_metadata(username)
    return metadata.get(chat_id, {}).get("name", f"Chat {chat_id[:8]}")


def rename_chat(chat_id: str, username: str, new_name: str) -> bool:
    """
    Rename a chat session.

    :param chat_id: The ID of the chat session to rename.
    :type chat_id: str
    :param username: The username.
    :type username: str
    :param new_name: The new name for the chat.
    :type new_name: str
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    metadata = _load_chat_metadata(username)
    if chat_id in metadata:
        metadata[chat_id]["name"] = new_name
        _save_chat_metadata(username, metadata)
        logger.info(f"Renamed chat {chat_id} to '{new_name}' for user {username}")
        return True
    logger.warning(f"Chat {chat_id} not found for renaming by user {username}")
    return False


def search_chat_history(query: str, username: str) -> List[Dict[str, Any]]:
    """
    Search chat history for a given query across all user's chats.

    :param query: The search query string.
    :type query: str
    :param username: The username.
    :type username: str
    :return: A list of dictionaries, each representing a chat with matches.
    :rtype: List[Dict[str, Any]]
    """
    results = []
    chat_ids = list_user_chat_ids(username)
    for chat_id in chat_ids:
        history = get_chat_history(chat_id, username)
        chat_name = get_chat_name(chat_id, username)
        matches = []
        match_count = 0
        preview_messages = []

        for i, pair in enumerate(history):
            user_msg = pair[0]
            bot_msg = pair[1]

            user_match = user_msg and query.lower() in user_msg.lower()
            bot_match = bot_msg and query.lower() in bot_msg.lower()

            if user_match or bot_match:
                match_count += 1
                matches.append(
                    {
                        "index": i,
                        "user_message": user_msg,
                        "bot_message": bot_msg,
                        "user_match": user_match,
                        "bot_match": bot_match,
                    }
                )
                if (
                    len(preview_messages) < 2
                ):  # Capture a couple of messages for preview
                    preview_messages.append(user_msg if user_msg else "")
                    if bot_msg:
                        preview_messages.append(bot_msg)

        if matches:
            results.append(
                {
                    "chat_id": chat_id,
                    "chat_name": chat_name,
                    "match_count": match_count,
                    "matching_messages": matches,
                    "chat_preview": " ... ".join(preview_messages[:2]).strip(),
                }
            )
    return results


def ensure_chat_on_login(username: str) -> str:
    """
    Ensures that a chat session exists for the user upon login.
    If no chats exist, a new one is created. Otherwise, the most recent one is returned.

    :param username: The username.
    :type username: str
    :return: The ID of the chat session to be used.
    :rtype: str
    """
    chat_ids = list_user_chat_ids(username)
    if not chat_ids:
        logger.info(f"No chats found for user {username}. Creating a new one.")
        return create_and_persist_new_chat(username)

    # Load all chat metadata to find the most recent chat
    user_chats = _load_chat_metadata(username)
    if not user_chats:
        logger.warning(
            f"No chat metadata found for {username} despite chat IDs existing. Creating new chat."
        )
        return create_and_persist_new_chat(username)

    most_recent_chat = None
    latest_timestamp = None

    for chat_id, chat_data in user_chats.items():
        created_at_str = chat_data.get("created_at")
        if created_at_str:
            try:
                # Parse ISO format string to datetime object
                current_timestamp = datetime.fromisoformat(created_at_str)
                if most_recent_chat is None or current_timestamp > latest_timestamp:
                    latest_timestamp = current_timestamp
                    most_recent_chat = chat_id
            except ValueError:
                logger.warning(
                    f"Could not parse created_at for chat {chat_id}: {created_at_str}"
                )
                # If parsing fails, fallback to using the first available chat
                if most_recent_chat is None:
                    most_recent_chat = chat_id
        else:
            # If created_at is missing, fallback to using the first available chat
            if most_recent_chat is None:
                most_recent_chat = chat_id

    if most_recent_chat:
        logger.info(
            f"Returning most recent chat {most_recent_chat} for user {username}."
        )
        return most_recent_chat
    else:
        # Fallback if somehow no chat could be determined as "most recent"
        logger.warning(
            f"Could not determine most recent chat for {username}, creating a new one as fallback."
        )
        return create_and_persist_new_chat(username)


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
    logging.error(
        f"ask_question called with question={question!r}, chat_id={chat_id!r}, username={username!r}"
    )
    if not question or not chat_id or not username:
        return {"error": "Invalid question or chat_id or username", "code": "400"}
    if not await check_rate_limit(username, "chat"):
        rate_limit_info = get_rate_limit_info("chat")
        return {
            "error": f"Rate limit exceeded. Please wait {rate_limit_info['time_window']} seconds.",
            "code": "429",
        }
    sanitized_question = sanitize_input(question)
    try:
        # Lazily import get_llm_functions here to break the circular dependency
        from .database import get_llm_functions

        # Get LLM functions
        llm_funcs = get_llm_functions()
        if not llm_funcs or not llm_funcs["is_llm_ready"]():
            logging.error(
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
        logging.error(f"Error in ask_question: {e}")
        return {"error": str(e), "code": "500"}


async def get_chatbot_response(ui_state: dict) -> dict:
    """
    Chatbot interface: generates a response using the LLM and updates history.
    Now includes message persistence to chat session files.

    :param ui_state: A dictionary containing the current UI state, including 'username', 'message', 'history', and 'chat_id'.
    :type ui_state: dict
    :return: A dictionary containing the updated history, bot response, and debug information.
    :rtype: dict
    """
    print(f"[DEBUG] backend.get_chatbot_response called with ui_state: {ui_state}")
    username = ui_state.get("username")
    message = ui_state.get("message")
    history = ui_state.get("history", [])
    chat_id = ui_state.get("chat_id", "default")

    if not message:
        return {
            "history": history,
            "response": "[No message provided]",
            "debug": "No message.",
        }

    if not username:
        return {
            "history": history,
            "response": "[Error] Username required for message persistence",
            "debug": "No username provided.",
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

        if result.get("code") == "200":
            answer = result.get("response", "")
            if isinstance(answer, dict) and "answer" in answer:
                answer = answer["answer"]
            updated_history = history + [[message, answer]]
            return {
                "history": updated_history,
                "response": answer,
                "debug": "Message processed.",
            }
        else:
            error_msg = result.get("error", "An unknown error occurred.")
            updated_history = history + [[message, f"Error: {error_msg}"]]
            return {
                "history": updated_history,
                "response": f"Error: {error_msg}",
                "debug": f"Error during question: {error_msg}",
            }
    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}")
        return {
            "history": history,
            "response": f"[Error] An unexpected error occurred: {e}",
            "debug": f"Unexpected error: {e}",
        }
