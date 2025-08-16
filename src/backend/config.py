#!/usr/bin/env python3
"""
Configuration module for the backend.
Contains all environment variables, paths, and configuration constants.
Updated for SQLite-based user management.
"""

import os
from dotenv import load_dotenv  # noqa: F401

load_dotenv()
from infra_utils import get_chatbot_dir

# Load environment variables


# OpenAI client (used for Whisper and other OpenAI API calls) will be initialized in backend.main:init_backend
client = None

# Rate limiting configuration
DEFAULT_RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
DEFAULT_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Different rate limits for different operations
CHAT_RATE_LIMIT_REQUESTS = int(
    os.getenv("CHAT_RATE_LIMIT_REQUESTS", str(DEFAULT_RATE_LIMIT_REQUESTS))
)
CHAT_RATE_LIMIT_WINDOW = int(
    os.getenv("CHAT_RATE_LIMIT_WINDOW", str(DEFAULT_RATE_LIMIT_WINDOW))
)

FILE_UPLOAD_RATE_LIMIT_REQUESTS = int(
    os.getenv("FILE_UPLOAD_RATE_LIMIT_REQUESTS", "10")
)
FILE_UPLOAD_RATE_LIMIT_WINDOW = int(os.getenv("FILE_UPLOAD_RATE_LIMIT_WINDOW", "60"))

AUDIO_RATE_LIMIT_REQUESTS = int(os.getenv("AUDIO_RATE_LIMIT_REQUESTS", "20"))
AUDIO_RATE_LIMIT_WINDOW = int(os.getenv("AUDIO_RATE_LIMIT_WINDOW", "60"))

AUTH_RATE_LIMIT_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "5"))
AUTH_RATE_LIMIT_WINDOW = int(os.getenv("AUTH_RATE_LIMIT_WINDOW", "300"))  # 5 minutes

# Path configurations
default_chat_path = os.path.join("data", "chats")
CHAT_DATA_PATH = os.path.join(
    get_chatbot_dir(), os.getenv("CHAT_DATA_PATH", default_chat_path)
)

default_db_path = os.path.join("data", "vector_store", "chroma_db")
DATABASE_PATH = os.path.join(
    get_chatbot_dir(), os.getenv("DATABASE_PATH", default_db_path)
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

default_session_path = os.path.join("data", "chat_sessions")
CHAT_SESSIONS_PATH = os.path.join(
    get_chatbot_dir(), os.getenv("CHAT_SESSIONS_PATH", default_session_path)
)

# SQLite database paths (managed by sqlite_database.py)
default_sqlite_path = os.path.join("data", "sqlite")
SQLITE_DB_PATH = os.path.join(
    get_chatbot_dir(), os.getenv("SQLITE_DB_PATH", default_sqlite_path)
)

# Allowed email domains for registration
ALLOWED_EMAILS = [
    "nyp.edu.sg",
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "test.com",  # For testing purposes
]
