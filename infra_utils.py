"""
Infrastructure Utilities for NYP FYP Chatbot

This module provides utility functions for path resolution, directory creation, logging setup, and environment management for both local and Docker deployments.
It is used throughout the project for consistent infrastructure operations and test environment cleanup.
"""

#!/usr/bin/env python3
import os
import logging
from typing import Optional


def rel2abspath(relative_path: str) -> str:
    """
    Convert a relative path to an absolute path.

    :param relative_path: The relative path to convert.
    :type relative_path: str
    :return: The absolute path.
    :rtype: str
    """
    return os.path.abspath(relative_path)


def create_folders(path: str) -> None:
    """
    Check if a directory (and all its parent directories) exists, and create them if not.

    :param path: The full path of the directory to ensure exists.
    :type path: str
    :raises OSError: If the directory cannot be created due to a file system error.
    """
    try:
        # os.makedirs creates all intermediate directories needed.
        # exist_ok=True prevents an error if the directory already exists.
        os.makedirs(path, exist_ok=True)
    except OSError:
        # Catching OSError for file system related errors (e.g., permissions)
        # Re-raise the exception because if the directory can't be created,
        # subsequent operations relying on it will fail.
        raise


def ensure_chatbot_dir_exists() -> None:
    """
    Ensure the chatbot directory exists in the user's home directory, including subdirectories for data organization.
    """
    chatbot_dir = get_chatbot_dir()
    create_folders(chatbot_dir)

    # Create subdirectories for data organization
    subdirs = [
        os.path.join(chatbot_dir, "data", "chat_sessions"),
        os.path.join(chatbot_dir, "data", "user_info"),
        os.path.join(chatbot_dir, "data", "vector_store", "chroma_db"),
        os.path.join(chatbot_dir, "logs"),
    ]

    for subdir in subdirs:
        create_folders(subdir)


def get_chatbot_dir() -> str:
    """
    Return the chatbot directory path (~/.nypai-chatbot).

    :return: The path to the chatbot directory.
    :rtype: str
    """
    # Check if we're running in Docker
    if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
        # In Docker, check if we're running as appuser (non-root)
        if os.getuid() == 1001:  # appuser UID
            return "/home/appuser/.nypai-chatbot"
        else:
            # In Docker as root, use the mounted volume path
            return "/root/.nypai-chatbot"
    else:
        # In local development, use user's home directory
        return os.path.expanduser("~/.nypai-chatbot")


def setup_logging() -> logging.Logger:
    """
    Set up centralized logging configuration. In test mode (TESTING=true), only log to console. In all modes, do not use file-based logging.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Only log to console in all modes
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def clear_chat_history(chat_id: str, username: str) -> tuple[bool, dict]:
    """
    Clear the history of a specific chat for a user.

    This function clears the message history of a specific chat while preserving
    the chat metadata (name, timestamps, etc.). It updates both the in-memory
    cache and the persistent storage.

    :param chat_id: The ID of the chat to clear.
    :type chat_id: str
    :param username: The username whose chat should be cleared.
    :type username: str
    :return: A tuple containing (success: bool, all_chats: dict) where success
             indicates if the operation was successful and all_chats contains
             the updated chat metadata for the user.
    :rtype: tuple[bool, dict]
    """
    try:
        # Import here to avoid circular imports
        from backend.chat import (
            _get_chat_metadata_cache_internal,
            _save_chat_metadata_cache,
        )
        from datetime import datetime  # noqa: F401

        # Get the user's chat metadata cache
        user_chats = _get_chat_metadata_cache_internal().get(username, {})

        if chat_id not in user_chats:
            return False, user_chats

        # Clear the history while preserving metadata
        user_chats[chat_id]["history"] = []
        user_chats[chat_id]["updated_at"] = datetime.now().isoformat()

        # Update the in-memory cache
        _get_chat_metadata_cache_internal()[username] = user_chats

        # Persist the changes to disk
        _save_chat_metadata_cache(username)

        return True, user_chats

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error clearing chat history for {chat_id}: {e}")
        return False, {}


def clear_all_chat_history() -> None:
    """Delete all files in the chat_sessions directory."""
    chat_history_dir = os.path.join(get_chatbot_dir(), "data", "chat_sessions")
    if os.path.exists(chat_history_dir):
        for fname in os.listdir(chat_history_dir):
            fpath = os.path.join(chat_history_dir, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    import shutil

                    shutil.rmtree(fpath)
            except Exception as e:
                print(f"Warning: Could not delete {fpath}: {e}")


def clear_uploaded_files() -> None:
    """Delete all files in the uploads directory (data/modelling/data by default)."""
    uploads_dir = os.path.join(get_chatbot_dir(), "data", "modelling", "data")
    if os.path.exists(uploads_dir):
        for fname in os.listdir(uploads_dir):
            fpath = os.path.join(uploads_dir, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    import shutil

                    shutil.rmtree(fpath)
            except Exception as e:
                print(f"Warning: Could not delete {fpath}: {e}")


def cleanup_test_environment(
    test_dir: Optional[str] = None, original_get_chatbot_dir: Optional[callable] = None
) -> None:
    """
    Clean up test environment by removing test directories and restoring original functions.

    This function is used in test suites to clean up after tests that modify the
    chatbot directory or mock functions.

    :param test_dir: Optional test directory to remove. If None, uses default test cleanup.
    :type test_dir: Optional[str]
    :param original_get_chatbot_dir: Optional original function to restore if it was mocked.
    :type original_get_chatbot_dir: Optional[callable]
    """
    try:
        import shutil

        # Restore original function if provided
        if original_get_chatbot_dir is not None:
            import infra_utils

            infra_utils.get_chatbot_dir = original_get_chatbot_dir

        # Remove test directory if provided
        if test_dir and os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)

        # Default cleanup: remove test data directories
        test_data_dirs = [
            os.path.join(get_chatbot_dir(), "data", "chat_sessions"),
            os.path.join(get_chatbot_dir(), "data", "user_info"),
            os.path.join(get_chatbot_dir(), "data", "modelling", "data"),
        ]

        for test_dir_path in test_data_dirs:
            if os.path.exists(test_dir_path):
                shutil.rmtree(test_dir_path, ignore_errors=True)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Error during test environment cleanup: {e}")


def get_docker_venv_path(mode="prod") -> str:
    """
    Return the Docker venv path for the given mode (prod, dev, test).
    - If running inside a container, use the VENV_PATH environment variable if set.
    - Otherwise, parse the default from the relevant Dockerfile.
    - Fallback to the known default for each mode.
    """
    import os

    # If running inside a container, use the environment variable
    if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
        return os.environ.get("VENV_PATH", "/home/appuser/.nypai-chatbot/venv")
    # Map mode to Dockerfile
    dockerfile_map = {
        "prod": "Dockerfile",
        "dev": "Dockerfile.dev",
        "test": "Dockerfile.test",
    }
    dockerfile = dockerfile_map.get(mode, "Dockerfile")
    try:
        with open(dockerfile, "r") as f:
            for line in f:
                if line.strip().startswith("ARG VENV_PATH="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    # Fallbacks
    if mode == "dev":
        return "/home/appuser/.nypai-chatbot/venv-dev"
    elif mode == "test":
        return "/home/appuser/.nypai-chatbot/venv-test"
    return "/home/appuser/.nypai-chatbot/venv"


def get_docker_venv_python(mode="prod") -> str:
    """
    Return the path to the Python executable in the Docker venv for the given mode.
    """
    return os.path.join(get_docker_venv_path(mode), "bin", "python")
