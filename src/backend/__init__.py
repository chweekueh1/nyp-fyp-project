#!/usr/bin/env python3
"""
Backend package for the NYP FYP CNC Chatbot.

This package provides authentication, chat, file handling, database, and analytics modules.
Environment variables (API keys, DB paths, etc.) are loaded from .env for secure configuration.
"""

# Import all modules explicitly to avoid star import issues
from .config import (
    client,
    ALLOWED_EMAILS,
    CHAT_DATA_PATH,
    DATABASE_PATH,
    CHAT_SESSIONS_PATH,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    CHAT_RATE_LIMIT_REQUESTS,
    CHAT_RATE_LIMIT_WINDOW,
    FILE_UPLOAD_RATE_LIMIT_REQUESTS,
    FILE_UPLOAD_RATE_LIMIT_WINDOW,
    AUDIO_RATE_LIMIT_REQUESTS,
    AUDIO_RATE_LIMIT_WINDOW,
    AUTH_RATE_LIMIT_REQUESTS,
    AUTH_RATE_LIMIT_WINDOW,
    EMBEDDING_MODEL,
)

from .rate_limiting import (
    check_rate_limit,
    get_rate_limit_info,
    RateLimiter,
    chat_rate_limiter,
)

from .auth import (
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

# Import password functions from hashing module
from hashing import hash_password, verify_password

from .chat import (
    get_chatbot_response,
    get_chat_history,
    search_chat_history,
    format_search_results,
    rename_chat,
    list_user_chat_ids,  # 'rename_chat_file' removed
)

from .file_handling import (
    handle_uploaded_file,
    upload_file,
    data_classification,
    detectFileType_async,
    generateUniqueFilename,
)

from .audio import (
    audio_to_text,
    transcribe_audio,
    transcribe_audio_async,
    transcribe_audio_file_async,
)

from .database import (
    get_chat_db,
    get_llm_functions,
    get_data_processing,
    get_classification,
)

# Import consolidated database functions
from .consolidated_database import (
    get_user_database,
    get_llm_database,
    get_performance_database,
    get_chat_database,
    get_classifications_database,
    ConsolidatedDatabase,
    InputSanitizer,
)

# Import performance tracking functions
from .performance_tracker import (
    get_performance_tracker,
    PerformanceTracker,
    track_docker_build,
    track_api_call,
    track_app_startup,
)

from .utils import (
    check_health,
    get_completion,
    sanitize_input,
    ensure_user_folder_file_exists_async,
    save_message_async,
)

from .main import init_backend, init_backend_async_internal, get_backend_status

from .timezone_utils import (
    get_app_timezone,
    now_singapore,
    utc_to_singapore,
    singapore_to_utc,
    format_singapore_datetime,
    get_iso_timestamp_singapore,
    get_utc_timestamp,
    parse_stored_timestamp,
    get_timezone_info,
)


# Export all public functions and constants
__all__ = [
    # Main initialization
    "init_backend",
    "init_backend_async_internal",
    "get_backend_status",
    # Chat functions
    "get_chatbot_response",
    "get_chat_history",
    "search_chat_history",
    "format_search_results",
    "rename_chat",
    "list_user_chat_ids",  # 'rename_chat_file' removed
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
    "RateLimiter",
    "chat_rate_limiter",
    # Password functions
    "hash_password",
    "verify_password",
    # Database functions
    "get_chat_db",
    "get_llm_functions",
    "get_data_processing",
    "get_classification",
    # Consolidated database functions
    "get_user_database",
    "get_llm_database",
    "get_performance_database",
    "get_chat_database",
    "get_classifications_database",
    "ConsolidatedDatabase",
    "InputSanitizer",
    # Performance tracking functions
    "get_performance_tracker",
    "PerformanceTracker",
    "track_docker_build",
    "track_api_call",
    "track_app_startup",
    # Configuration constants
    "client",
    "ALLOWED_EMAILS",
    "CHAT_DATA_PATH",
    "DATABASE_PATH",
    "CHAT_SESSIONS_PATH",
    "DEFAULT_RATE_LIMIT_REQUESTS",
    "DEFAULT_RATE_LIMIT_WINDOW",
    "CHAT_RATE_LIMIT_REQUESTS",
    "CHAT_RATE_LIMIT_WINDOW",
    "FILE_UPLOAD_RATE_LIMIT_REQUESTS",
    "FILE_UPLOAD_RATE_LIMIT_WINDOW",
    "AUDIO_RATE_LIMIT_REQUESTS",
    "AUDIO_RATE_LIMIT_WINDOW",
    "AUTH_RATE_LIMIT_REQUESTS",
    "AUTH_RATE_LIMIT_WINDOW",
    "EMBEDDING_MODEL",
    # Timezone utilities
    "get_app_timezone",
    "now_singapore",
    "utc_to_singapore",
    "singapore_to_utc",
    "format_singapore_datetime",
    "get_iso_timestamp_singapore",
    "get_utc_timestamp",
    "parse_stored_timestamp",
    "get_timezone_info",
]
