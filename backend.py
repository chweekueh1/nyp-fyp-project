#!/usr/bin/env python3
"""
Backend module for the NYP FYP Chatbot.
This file provides backward compatibility by importing from the modular backend.
"""

import sys
import os

# Add current directory to Python path to ensure backend package is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all functions and constants explicitly from the modular backend modules
from backend.main import init_backend, init_backend_async_internal
from backend.chat import (
    ask_question,
    get_chatbot_response,
    get_chat_response,
    get_chat_history,
    search_chat_history,
    create_new_chat_id,
    generate_smart_chat_name,
    create_and_persist_new_chat,
    create_and_persist_smart_chat,
    get_user_chats,
    get_user_chats_with_names,
    get_chat_name,
    set_chat_name,
    rename_chat,
    fuzzy_search_chats,
    render_all_chats,
)
from backend.file_handling import (
    handle_uploaded_file,
    upload_file,
    data_classification,
    detectFileType_async,
    generateUniqueFilename,
)
from backend.audio import (
    audio_to_text,
    transcribe_audio,
    transcribe_audio_async,
    transcribe_audio_file_async,
)
from backend.auth import (
    do_login,
    do_register,
    change_password,
    do_login_test,
    do_register_test,
    change_password_test,
    cleanup_test_user,
    cleanup_all_test_users,
    delete_test_user,
)
from backend.utils import (
    check_health,
    get_completion,
    sanitize_input,
    ensure_user_folder_file_exists_async,
    save_message_async,
)
from backend.rate_limiting import check_rate_limit, get_rate_limit_info
from backend.config import (
    ALLOWED_EMAILS,
    CHAT_DATA_PATH,
    DATABASE_PATH,
    CHAT_SESSIONS_PATH,
    USER_DB_PATH,
    TEST_USER_DB_PATH,
)

# Export all functions and constants for backward compatibility
__all__ = [
    # Main initialization
    "init_backend",
    "init_backend_async_internal",
    # Chat functions
    "ask_question",
    "get_chatbot_response",
    "get_chat_response",
    "get_chat_history",
    "search_chat_history",
    "create_new_chat_id",
    "generate_smart_chat_name",
    "create_and_persist_new_chat",
    "create_and_persist_smart_chat",
    "get_user_chats",
    "get_user_chats_with_names",
    "get_chat_name",
    "set_chat_name",
    "rename_chat",
    "fuzzy_search_chats",
    "render_all_chats",
    # File handling
    "handle_uploaded_file",
    "upload_file",
    "data_classification",
    "detectFileType_async",
    "generateUniqueFilename",
    # Audio functions
    "audio_to_text",
    "transcribe_audio",
    "transcribe_audio_async",
    "transcribe_audio_file_async",
    # Authentication
    "do_login",
    "do_register",
    "change_password",
    "do_login_test",
    "do_register_test",
    "change_password_test",
    "cleanup_test_user",
    "cleanup_all_test_users",
    "delete_test_user",
    # Utility functions
    "check_health",
    "get_completion",
    "sanitize_input",
    "ensure_user_folder_file_exists_async",
    "save_message_async",
    # Rate limiting
    "check_rate_limit",
    "get_rate_limit_info",
    # Configuration
    "ALLOWED_EMAILS",
    "CHAT_DATA_PATH",
    "DATABASE_PATH",
    "CHAT_SESSIONS_PATH",
    "USER_DB_PATH",
    "TEST_USER_DB_PATH",
]
