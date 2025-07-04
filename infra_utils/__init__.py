"""
Infrastructure utilities for the NYP FYP Chatbot project.

This package contains utility modules for:
- NLTK configuration and data management
- Other infrastructure-related functionality
"""

# Import functions from the main infra_utils.py file to maintain compatibility
import sys
import os
from pathlib import Path

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
        "cleanup_test_environment",
        "get_docker_venv_path",
        "get_docker_venv_python",
    ]

except Exception:
    # If we can't import from the main file, define minimal stubs
    import os

    def rel2abspath(path):
        return os.path.abspath(path)

    def create_folders(path):
        os.makedirs(path, exist_ok=True)

    def ensure_chatbot_dir_exists():
        chatbot_dir = get_chatbot_dir()
        create_folders(chatbot_dir)
        return chatbot_dir

    def get_chatbot_dir():
        return os.path.expanduser("~/.nypai-chatbot")

    def setup_logging():
        import logging

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        return logger

    def clear_chat_history():
        pass

    def cleanup_test_environment():
        pass

    def get_docker_venv_path(mode="prod"):
        return f"/home/appuser/.nypai-chatbot/venv-{mode}"

    def get_docker_venv_python(mode="prod"):
        return f"/home/appuser/.nypai-chatbot/venv-{mode}/bin/python"

    __all__ = [
        "rel2abspath",
        "create_folders",
        "ensure_chatbot_dir_exists",
        "get_chatbot_dir",
        "setup_logging",
        "clear_chat_history",
        "cleanup_test_environment",
        "get_docker_venv_path",
        "get_docker_venv_python",
    ]
