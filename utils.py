#!/usr/bin/env python3
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def rel2abspath(relative_path: str) -> str:
    return os.path.abspath(relative_path)


def create_folders(path: str):
    """
    Checks if a directory (and all its parent directories) exist.
    If not, it creates them. This function is idempotent, meaning it
    won't raise an error if the directories already exist.

    Args:
        path (str): The full path of the directory to ensure exists.
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


def ensure_chatbot_dir_exists():
    """Ensure the chatbot directory exists in user's home directory."""
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


def get_chatbot_dir():
    """Return the chatbot directory path (~/.nypai-chatbot)."""
    # Check if we're running in Docker
    if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
        # In Docker, use the mounted volume path
        return "/root/.nypai-chatbot"
    else:
        # In local development, use user's home directory
        return os.path.expanduser("~/.nypai-chatbot")


def setup_logging():
    """Set up centralized logging configuration in ~/.nypai-chatbot/logs."""
    logs_dir = Path(get_chatbot_dir()) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create rotating file handler
    log_file = logs_dir / "app.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add handler to root logger
    logger.addHandler(file_handler)

    # Also log to console with INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Clear the log file
    with open(log_file, "w") as f:
        f.write("")

    return logger
