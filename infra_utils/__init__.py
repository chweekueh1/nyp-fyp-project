"""
Infrastructure utilities for the NYP FYP Chatbot project.

This package contains utility modules for:
- NLTK configuration and data management
- Other infrastructure-related functionality
"""

# Import functions from the main infra_utils.py file to maintain compatibility
import sys
import os
import logging
from pathlib import Path
from typing import Callable

# Add the parent directory to the path to import from infra_utils.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    # Import the main infra_utils module directly
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "infra_utils_main", parent_dir / "infra_utils.py"
    )
    infra_utils_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(infra_utils_main)

    # Extract the functions we need
    rel2abspath = infra_utils_main.rel2abspath
    create_folders = infra_utils_main.create_folders
    ensure_chatbot_dir_exists = infra_utils_main.ensure_chatbot_dir_exists
    get_chatbot_dir = infra_utils_main.get_chatbot_dir
    setup_logging = infra_utils_main.setup_logging
    clear_chat_history = infra_utils_main.clear_chat_history
    clear_all_chat_history = infra_utils_main.clear_all_chat_history
    clear_uploaded_files = infra_utils_main.clear_uploaded_files
    cleanup_test_environment = infra_utils_main.cleanup_test_environment
    get_docker_venv_path = infra_utils_main.get_docker_venv_path
    get_docker_venv_python = infra_utils_main.get_docker_venv_python

    # Make these available at package level
    __all__ = [
        "rel2abspath",
        "create_folders",
        "ensure_chatbot_dir_exists",
        "get_chatbot_dir",
        "setup_logging",
        "clear_chat_history",
        "clear_all_chat_history",
        "clear_uploaded_files",
        "cleanup_test_environment",
        "get_docker_venv_path",
        "get_docker_venv_python",
    ]

except Exception:
    # If we can't import from the main file, define minimal stubs
    import os

    def rel2abspath(path: str) -> str:
        """
        Convert a relative path to an absolute path.

        :param path: The path to convert.
        :type path: str
        :return: The absolute path.
        :rtype: str
        """
        return os.path.abspath(path)

    def create_folders(path: str) -> None:
        """
        Create directories recursively if they do not exist.

        :param path: The directory path to create.
        :type path: str
        """
        os.makedirs(path, exist_ok=True)

    def ensure_chatbot_dir_exists() -> str:
        """
        Ensure the chatbot directory exists and create it if not.

        :return: The chatbot directory path.
        :rtype: str
        """
        chatbot_dir = get_chatbot_dir()
        create_folders(chatbot_dir)
        return chatbot_dir

    def get_chatbot_dir() -> str:
        """
        Get the chatbot directory path (~/.nypai-chatbot).

        :return: The chatbot directory path.
        :rtype: str
        """
        return os.path.expanduser("~/.nypai-chatbot")

    def setup_logging() -> logging.Logger:
        """
        Set up and return a logger instance.

        :return: Logger instance.
        :rtype: logging.Logger
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        return logger

    def clear_chat_history(chat_id: str, username: str) -> tuple[bool, dict]:
        """
        Stub function for clearing chat history.

        :param chat_id: The chat ID.
        :type chat_id: str
        :param username: The username.
        :type username: str
        :return: Tuple of (success, all_chats).
        :rtype: tuple[bool, dict]
        """
        return False, {}

    def clear_all_chat_history() -> None:
        """
        Stub function for clearing all chat history.
        """
        pass

    def clear_uploaded_files() -> None:
        """
        Stub function for clearing uploaded files.
        """
        pass

    def cleanup_test_environment(
        test_dir: str | None = None, original_get_chatbot_dir: Callable | None = None
    ) -> None:
        """
        Stub function for cleaning up test environment.

        :param test_dir: Optional test directory to remove.
        :type test_dir: str | None
        :param original_get_chatbot_dir: Optional original function to restore.
        :type original_get_chatbot_dir: Callable | None
        """
        pass

    def get_docker_venv_path(mode: str = "prod") -> str:
        """
        Get the Docker venv path for the given mode.

        :param mode: The mode (e.g., 'prod').
        :type mode: str
        :return: The venv path.
        :rtype: str
        """
        return f"/home/appuser/.nypai-chatbot/venv-{mode}"

    def get_docker_venv_python(mode: str = "prod") -> str:
        """
        Get the Docker venv python path for the given mode.

        :param mode: The mode (e.g., 'prod').
        :type mode: str
        :return: The python path.
        :rtype: str
        """
        return f"/home/appuser/.nypai-chatbot/venv-{mode}/bin/python"

    __all__ = [
        "rel2abspath",
        "create_folders",
        "ensure_chatbot_dir_exists",
        "get_chatbot_dir",
        "setup_logging",
        "clear_chat_history",
        "clear_all_chat_history",
        "clear_uploaded_files",
        "cleanup_test_environment",
        "get_docker_venv_path",
        "get_docker_venv_python",
    ]
