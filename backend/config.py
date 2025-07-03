#!/usr/bin/env python3
"""
Configuration module for the backend.
Contains all environment variables, paths, and configuration constants.
"""

import os
from dotenv import load_dotenv
from infra_utils import get_chatbot_dir

# Load environment variables
load_dotenv()

# OpenAI client
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

default_user_path = os.path.join("data", "user_info", "users.json")
USER_DB_PATH = os.path.join(
    get_chatbot_dir(), os.getenv("USER_DB_PATH", default_user_path)
)

# Test database path (separate from production)
default_test_path = os.path.join("data", "user_info", "test_users.json")
TEST_USER_DB_PATH = os.path.join(get_chatbot_dir(), default_test_path)

# Allowed email domains/addresses for registration
ALLOWED_EMAILS = [
    # NYP email domains
    "student.nyp.edu.sg",
    "nyp.edu.sg",
    # Development/testing emails
    "test@example.com",
    "demo@nyp.edu.sg",
    "admin@nyp.edu.sg",
    # Add more allowed emails here as needed
    "user@nyp.edu.sg",
    "faculty@nyp.edu.sg",
    "staff@nyp.edu.sg",
]
