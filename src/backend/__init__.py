#!/usr/bin/env python3
"""
Backend package for the NYP FYP CNC Chatbot.

This package provides authentication, chat, file handling, database, and analytics modules.
Environment variables (API keys, DB paths, etc.) are loaded from .env for secure configuration.
"""

# Import all modules explicitly to avoid star import issues
# from .config import (
#     client,
#     ALLOWED_EMAILS,
#     CHAT_DATA_PATH,
#     DATABASE_PATH,
#     CHAT_SESSIONS_PATH,
#     DEFAULT_RATE_LIMIT_REQUESTS,
#     DEFAULT_RATE_LIMIT_WINDOW,
#     CHAT_RATE_LIMIT_REQUESTS,
#     CHAT_RATE_LIMIT_WINDOW,
#     FILE_UPLOAD_RATE_LIMIT_REQUESTS,
#     FILE_UPLOAD_RATE_LIMIT_WINDOW,
#     AUDIO_RATE_LIMIT_REQUESTS,
#     AUDIO_RATE_LIMIT_WINDOW,
#     AUTH_RATE_LIMIT_REQUESTS,
#     AUTH_RATE_LIMIT_WINDOW,
#     EMBEDDING_MODEL,
# )

# from .rate_limiting import (
#     check_rate_limit,
#     get_rate_limit_info,
#     RateLimiter,
#     chat_rate_limiter,
# )

# from .auth import (
#     do_login,
#     do_register,
#     change_password,
#     do_login_test,
#     do_register_test,
#     change_password_test,
#     cleanup_test_user,
#     cleanup_all_test_users,
#     delete_test_user,
# )

# # Import password functions from hashing module
# from hashing import hash_password, verify_password

# from .chat import (
#     get_chatbot_response,
#     get_chat_history,
#     get_chat_metadata,
#     save_message_async,
#     delete_chat_history_for_user,
#     delete_single_chat_session,
#     rename_chat_session_session,
#     search_chat_history,
# )

# from .file_handling import (
#     handle_uploaded_file,
#     upload_file,
#     data_classification,
#     process_zip_file,
#     generateUniqueFilename,
# )

# from .audio import audio_to_text

# from .main import init_backend, get_backend_status

# from .timezone_utils import get_utc_timestamp, get_app_timezone

# from .utils import (
#     sanitize_input,
#     health_check,
#     get_completion,
#     _ensure_db_and_folders_async
# )

# from .database import (
#     get_chat_db,
#     get_llm_functions,
#     get_data_processing,
#     get_classification,
# )

# from .consolidated_database import (
#     get_consolidated_database,
#     ConsolidatedDatabase,
#     InputSanitizer,
# )

# from performance_utils import (
#     PerformanceTracker,
#     start_docker_build,
#     track_api_call,
#     track_app_startup,
# )

# __all__ = [
#     # Config
#     "client",
#     "ALLOWED_EMAILS",
#     "CHAT_DATA_PATH",
#     "DATABASE_PATH",
#     "CHAT_SESSIONS_PATH",
#     "DEFAULT_RATE_LIMIT_REQUESTS",
#     "DEFAULT_RATE_LIMIT_WINDOW",
#     "CHAT_RATE_LIMIT_REQUESTS",
#     "CHAT_RATE_LIMIT_WINDOW",
#     "FILE_UPLOAD_RATE_LIMIT_REQUESTS",
#     "FILE_UPLOAD_RATE_LIMIT_WINDOW",
#     "AUDIO_RATE_LIMIT_REQUESTS",
#     "AUDIO_RATE_LIMIT_WINDOW",
#     "AUTH_RATE_LIMIT_REQUESTS",
#     "AUTH_RATE_LIMIT_WINDOW",
#     "EMBEDDING_MODEL",
#     # Auth
#     "do_login",
#     "do_register",
#     "change_password",
#     "do_login_test",
#     "do_register_test",
#     "change_password_test",
#     "cleanup_test_user",
#     "cleanup_all_test_users",
#     "delete_test_user",
#     # Chat
#     "get_chatbot_response",
#     "get_chat_history",
#     "get_chat_metadata",
#     "save_message_async",
#     "delete_chat_history_for_user",
#     "delete_single_chat_session",
#     "rename_chat_session_session",
#     "search_chat_history",
#     # File Management
#     "handle_uploaded_file",
#     "upload_file",
#     "data_classification",
#     "process_zip_file",
#     "generateUniqueFilename",
#     # Audio
#     "audio_to_text",
#     # Main backend
#     "init_backend",
#     "get_backend_status",
#     # Timezone
#     "get_utc_timestamp",
#     "get_app_timezone",
#     # Utils
#     "sanitize_input",
#     "health_check",
#     "get_completion",
#     "_ensure_db_and_folders_async",
#     # Rate limiting
#     "check_rate_limit",
#     "get_rate_limit_info",
#     "RateLimiter",
#     "chat_rate_limiter",
#     # Password functions
#     "hash_password",
#     "verify_password",
#     # Database functions (DuckDB related)
#     "get_chat_db",
#     "get_llm_functions",
#     "get_data_processing",
#     "get_classification",
#     # Consolidated database functions (SQLite related)
#     "get_consolidated_database",
#     "ConsolidatedDatabase",
#     "InputSanitizer",
#     # Performance tracking functions
#     "PerformanceTracker",
#     "track_docker_build",
#     "track_api_call",
#     "track_app_startup",
# ]
