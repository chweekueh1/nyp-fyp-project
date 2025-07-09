#!/usr/bin/env python3
"""
Utility functions module for the backend.
Contains helper functions and utilities.
"""

import os
import html
import re
import json
from typing import Dict, Any, Union  # noqa: F401
from infra_utils import setup_logging, ensure_chatbot_dir_exists
from .config import CHAT_DATA_PATH, CHAT_SESSIONS_PATH, USER_DB_PATH
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = setup_logging()


def sanitize_input(input_text: str) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.

    :param input_text: The input text to sanitize.
    :type input_text: str
    :return: Sanitized input text with HTML tags removed and entities escaped.
    :rtype: str
    """
    if not input_text:
        return ""

    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", "", input_text)

    # Escape HTML entities
    cleaned = html.escape(cleaned)

    # Remove potentially dangerous characters
    cleaned = re.sub(r'[<>"\']', "", cleaned)

    # Limit length
    if len(cleaned) > 400000:
        cleaned = cleaned[:400000]

    # Strip whitespace but preserve non-whitespace content
    cleaned = cleaned.strip()

    # If the result is empty after stripping, return the original input
    # This prevents short queries like "hi" from becoming empty
    if not cleaned and input_text.strip():
        return input_text.strip()

    return cleaned


async def _ensure_db_and_folders_async() -> None:
    """
    Ensure all necessary directories and files exist.

    Raises:
        Exception: If directory or file creation fails.
    """
    try:
        # Ensure chatbot directory exists
        ensure_chatbot_dir_exists()

        # Ensure chat data directory exists
        os.makedirs(CHAT_DATA_PATH, exist_ok=True)

        # Ensure chat sessions directory exists
        os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)

        # Ensure user database directory exists
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)

        # Create user database file if it doesn't exist
        if not os.path.exists(USER_DB_PATH):
            with open(USER_DB_PATH, "w") as f:
                json.dump({}, f)
            logger.info(f"Created user database at {USER_DB_PATH}")

        logger.info("Database and folders ensured successfully")

    except Exception as e:
        logger.error(f"Error ensuring database and folders: {e}")
        raise


async def ensure_user_folder_file_exists_async(username: str, chat_id: str) -> str:
    """
    Ensure user folder and chat file exist.

    :param username: Username for the folder.
    :type username: str
    :param chat_id: Chat ID for the file.
    :type chat_id: str
    :return: Path to the chat file.
    :rtype: str
    :raises Exception: If folder or file creation fails.
    """
    try:
        user_folder = os.path.join(CHAT_DATA_PATH, username)
        os.makedirs(user_folder, exist_ok=True)

        chat_file = os.path.join(user_folder, f"{chat_id}.json")
        if not os.path.exists(chat_file):
            with open(chat_file, "w") as f:
                json.dump({"messages": []}, f)

        return chat_file
    except Exception as e:
        logger.error(f"Error ensuring user folder/file exists: {e}")
        raise


async def save_message_async(
    username: str, chat_id: str, message: Dict[str, Any]
) -> None:
    """
    Save a message to the user's chat file.

    :param username: Username for the message.
    :type username: str
    :param chat_id: Chat ID for the message.
    :type chat_id: str
    :param message: Message data to save.
    :type message: Dict[str, Any]
    :raises Exception: If message saving fails.
    """
    try:
        chat_file = await ensure_user_folder_file_exists_async(username, chat_id)

        with open(chat_file, "r") as f:
            chat_data = json.load(f)

        # Add timestamp to message (store in UTC for consistency)
        message_with_timestamp = {
            **message,
            "timestamp": get_utc_timestamp(),
        }

        chat_data["messages"].append(message_with_timestamp)

        with open(chat_file, "w") as f:
            json.dump(chat_data, f, indent=2)

        logger.info(f"Message saved for user {username} in chat {chat_id}")

    except Exception as e:
        logger.error(f"Error saving message: {e}")
        raise


async def check_health() -> dict[str, str]:
    """
    Check the health of the backend system.

    :return: Dictionary containing health status and message.
    :rtype: dict[str, str]
    """
    try:
        # Check if essential directories exist
        dirs_to_check = [
            CHAT_DATA_PATH,
            CHAT_SESSIONS_PATH,
            os.path.dirname(USER_DB_PATH),
        ]

        for dir_path in dirs_to_check:
            if not os.path.exists(dir_path):
                return {
                    "status": "error",
                    "message": f"Directory {dir_path} does not exist",
                }

        # Check if user database is accessible
        if not os.path.exists(USER_DB_PATH):
            return {"status": "error", "message": "User database does not exist"}

        # Try to read user database
        try:
            with open(USER_DB_PATH, "r") as f:
                json.load(f)
        except Exception as e:
            return {"status": "error", "message": f"User database is corrupted: {e}"}

        return {"status": "healthy", "message": "All systems operational"}

    except Exception as e:
        return {"status": "error", "message": f"Health check failed: {e}"}


def get_completion(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 150,
    temperature: float = 0.8,
) -> Union[str, Dict[str, Any]]:
    """
    Get a completion from OpenAI.

    :param prompt: The prompt to send to the model
    :type prompt: str
    :param model: The model to use
    :type model: str
    :param max_tokens: Maximum tokens to generate
    :type max_tokens: int
    :param temperature: Temperature for generation
    :type temperature: float
    :return: The completion response
    :rtype: Union[str, Dict[str, Any]]
    """
    try:
        from .config import client

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            return {"error": "No response from model"}

    except Exception as e:
        logger.error(f"Error getting completion: {e}")
        return {"error": str(e)}
