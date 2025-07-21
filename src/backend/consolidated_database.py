#!/usr/bin/env python3
"""
Consolidated SQLite Database module for the NYP FYP CNC Chatbot backend.

This module provides consolidated database functionality including:

- User data management (single SQLite file)
- LLM data management (separate SQLite file)
- Performance tracking (separate SQLite file)
- Input sanitization and SQL injection prevention
- Docker build time, API call time, and app startup time tracking
- Proper database isolation and security

The module uses separate SQLite files for different purposes and includes
comprehensive security measures to prevent SQL injection attacks.
"""

import sqlite3
import os
import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from contextlib import contextmanager
from infra_utils import get_chatbot_dir

# Set up logging
logger = logging.getLogger(__name__)


# Database file paths
def get_database_path(db_name: str) -> str:
    """
    Returns the path to the user's database file.

    Args:
        db_name (str): The database name.

    Returns:
        str: The path to the user's database file.

    Raises:
        ValueError: If the db_name is invalid or the path cannot be determined.
    """
    # Sanitize database name to prevent path traversal
    if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
        raise ValueError(f"Invalid database name: {db_name}")

    # If running in Docker or benchmark mode and db_name is 'users', use a temp directory to avoid persistence
    if (
        os.environ.get("BENCHMARK_MODE")
        and os.environ.get("DOCKER_BUILD")
        and db_name == "users"
    ):
        db_dir = "/tmp/data/sqlite"
    else:
        base_dir = get_chatbot_dir()
        db_dir = os.path.join(base_dir, "data", "sqlite")

    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f"{db_name}.db")


class InputSanitizer:
    """
    Provides methods for sanitizing user inputs to prevent SQL injection and other attacks.
    """

    @staticmethod
    def sanitize_text(input_string: str) -> str:
        """
        Sanitizes a string to prevent common injection attacks.
        This method is primarily for displaying or logging, not for direct SQL parameters.
        For SQL, always use parameterized queries.
        """
        if not isinstance(input_string, str):
            return ""
        # Basic sanitization: escape single quotes and potentially problematic characters
        # For display, you might use html.escape, but for general text processing, this is a start.
        sanitized_string = (
            input_string.replace("'", "''").replace("--", "").replace(";", "")
        )
        # Remove common control characters that could mess with display or logs
        sanitized_string = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", sanitized_string)
        return sanitized_string.strip()

    @staticmethod
    def sanitize_integer(input_value: Any) -> Optional[int]:
        """
        Converts input to an integer, returning None if not a valid integer.
        """
        try:
            return int(input_value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def sanitize_float(input_value: Any) -> Optional[float]:
        """
        Converts input to a float, returning None if not a valid float.
        """
        try:
            return float(input_value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def sanitize_boolean(input_value: Any) -> bool:
        """
        Converts input to a boolean.
        """
        if isinstance(input_value, bool):
            return input_value
        if isinstance(input_value, str):
            return input_value.lower() in ("true", "1", "t", "y", "yes")
        if isinstance(input_value, (int, float)):
            return bool(input_value)
        return False


class ConsolidatedDatabase:
    """
    Consolidated SQLite database handler.

    This class manages connections and operations for different SQLite database files.
    It provides a secure interface with input sanitization and SQL injection prevention.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_name = os.path.basename(db_path).replace(".db", "")
        self._init_database()

    @contextmanager
    def _get_db_connection(self):
        """
        Get a database connection.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
            yield conn
        finally:
            if conn:
                conn.close()

    def _init_database(self):
        """
        Initialize the database with required tables based on db_name.
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            if self.db_name == "users":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        hashed_password TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        is_active INTEGER DEFAULT 1,
                        is_test_user INTEGER DEFAULT 0
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        details TEXT,
                        FOREIGN KEY (username) REFERENCES users(username)
                    )
                """
                )
            elif self.db_name == "chat":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        chat_id TEXT NOT NULL UNIQUE,
                        chat_name TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT NOT NULL,
                        message_index INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (chat_id) REFERENCES chat_sessions(chat_id)
                    )
                """
                )
                # Index for faster message retrieval by chat_id and message_index
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id_index ON chat_messages (chat_id, message_index)"
                )
                # Index for faster session retrieval by username
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions (username)"
                )
            elif self.db_name == "classifications":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS classifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        classification_result TEXT NOT NULL,
                        sensitivity_level TEXT,
                        security_level TEXT,
                        created_at TEXT NOT NULL,
                        file_size INTEGER,
                        extraction_method TEXT
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_classifications_username ON classifications (username)"
                )
            elif self.db_name == "llm":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        session_id TEXT NOT NULL UNIQUE,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        model_used TEXT,
                        total_tokens INTEGER DEFAULT 0,
                        total_messages INTEGER DEFAULT 0
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        token_count INTEGER DEFAULT 0,
                        FOREIGN KEY (session_id) REFERENCES llm_sessions(session_id)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS llm_embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        content_type TEXT NOT NULL, -- e.g., 'document', 'chat_message'
                        content_id TEXT NOT NULL,
                        embedding_vector BLOB NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_llm_sessions_username ON llm_sessions (username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_llm_messages_session_id ON llm_messages (session_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_llm_embeddings_username ON llm_embeddings (username)"
                )
            elif self.db_name == "performance":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_startups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT, -- Can be NULL for initial app startup
                        timestamp TEXT NOT NULL,
                        duration_ms INTEGER,
                        os_info TEXT,
                        python_version TEXT
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS api_calls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT, -- Can be NULL for unauthenticated calls
                        endpoint TEXT NOT NULL,
                        method TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        response_time_ms INTEGER,
                        status_code INTEGER,
                        ip_address TEXT
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        metric_type TEXT NOT NULL, -- e.g., 'file_upload_size', 'audio_transcription_duration'
                        metric_value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        details TEXT -- JSON string for additional details if needed
                    )
                """
                )
                # Adding more specific tables for file uploads and audio transcriptions for richer summaries
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS file_uploads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_size_bytes INTEGER NOT NULL,
                        upload_timestamp TEXT NOT NULL,
                        file_type TEXT,
                        classification_id INTEGER, -- Optional: link to classifications table
                        FOREIGN KEY (username) REFERENCES users(username)
                    )
                """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audio_transcriptions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        audio_file_name TEXT NOT NULL,
                        duration_seconds REAL NOT NULL,
                        transcription_length_chars INTEGER NOT NULL,
                        transcription_timestamp TEXT NOT NULL,
                        model_used TEXT,
                        FOREIGN KEY (username) REFERENCES users(username)
                    )
                """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_api_calls_username ON api_calls (username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_app_startups_username ON app_startups (username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_performance_metrics_username_type ON performance_metrics (username, metric_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_file_uploads_username ON file_uploads (username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_audio_transcriptions_username ON audio_transcriptions (username)"
                )

            conn.commit()

    def _get_username_from_user_id(self, user_id: int) -> Optional[str]:
        """
        Helper to get username from user_id.
        This assumes 'users.db' is accessible or a global user_db instance is available.
        You might need to adjust this based on how user_id maps to username in your system.
        A more robust solution would be to pass the username directly if available.
        """
        # For this example, we'll assume we can directly query the 'users' database.
        # In a real application, you'd likely have a global user_db instance or pass username.
        try:
            # Import within the method to avoid circular dependencies if get_user_database
            # depends on ConsolidatedDatabase and vice-versa for helper methods.
            from .consolidated_database import get_user_database

            user_db = get_user_database()
            query = "SELECT username FROM users WHERE id = ?"
            result = user_db.fetch_one(query, (user_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting username for user_id {user_id}: {e}")
            return None

    def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Execute a read query and return results.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(
                f"Database error during query: {query} with params {params}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during query: {query} with params {params}: {e}"
            )
            raise

    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """
        Execute an insert query and return the last row ID.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(
                f"Database error during insert: {query} with params {params}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during insert: {query} with params {params}: {e}"
            )
            raise

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """
        Fetch a single row from a query.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(
                f"Database error during fetch_one: {query} with params {params}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during fetch_one: {query} with params {params}: {e}"
            )
            raise

    def fetch_all(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Fetch all rows from a query.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(
                f"Database error during fetch_all: {query} with params {params}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during fetch_all: {query} with params {params}: {e}"
            )
            raise

    # --- Existing Summary Functions (from your code/previous context) ---

    def get_user_chat_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of chat statistics for a given user.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {"error": "User not found", "total_chats": 0, "total_messages": 0}

        try:
            # Total chat sessions
            query_total_chats = (
                "SELECT COUNT(DISTINCT chat_id) FROM chat_sessions WHERE username = ?"
            )
            total_chats_result = self.fetch_one(query_total_chats, (username,))
            total_chats = total_chats_result[0] if total_chats_result else 0

            # Total messages
            query_total_messages = """
                SELECT COUNT(*) FROM chat_messages
                WHERE chat_id IN (SELECT chat_id FROM chat_sessions WHERE username = ?)
            """
            total_messages_result = self.fetch_one(query_total_messages, (username,))
            total_messages = total_messages_result[0] if total_messages_result else 0

            # Last active chat (name and last updated time)
            query_last_active_chat = """
                SELECT chat_name, updated_at FROM chat_sessions
                WHERE username = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """
            last_active_chat_result = self.fetch_one(
                query_last_active_chat, (username,)
            )
            last_active_chat = (
                {
                    "name": last_active_chat_result[0],
                    "updated_at": last_active_chat_result[1],
                }
                if last_active_chat_result
                else None
            )

            return {
                "total_chats": total_chats,
                "total_messages": total_messages,
                "last_active_chat": last_active_chat,
            }
        except Exception as e:
            logger.error(f"Error getting user chat summary for user_id {user_id}: {e}")
            return {"total_chats": 0, "total_messages": 0, "error": str(e)}

    def get_user_classification_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of classification statistics for a given user.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {
                "error": "User not found",
                "total_classifications": 0,
                "top_classification": None,
            }

        try:
            # Total number of classifications
            query_total_classifications = (
                "SELECT COUNT(*) FROM classifications WHERE username = ?"
            )
            total_classifications_result = self.fetch_one(
                query_total_classifications, (username,)
            )
            total_classifications = (
                total_classifications_result[0] if total_classifications_result else 0
            )

            # Most common classification result
            query_top_classification = """
                SELECT classification_result, COUNT(*) AS count
                FROM classifications
                WHERE username = ?
                GROUP BY classification_result
                ORDER BY count DESC
                LIMIT 1
            """
            top_classification_result = self.fetch_one(
                query_top_classification, (username,)
            )
            top_classification = (
                {
                    "result": top_classification_result[0],
                    "count": top_classification_result[1],
                }
                if top_classification_result
                else None
            )

            # Total size of classified files
            query_total_file_size = (
                "SELECT SUM(file_size) FROM classifications WHERE username = ?"
            )
            total_file_size_result = self.fetch_one(query_total_file_size, (username,))
            total_file_size_bytes = (
                total_file_size_result[0]
                if total_file_size_result and total_file_size_result[0] is not None
                else 0
            )

            return {
                "total_classifications": total_classifications,
                "top_classification": top_classification,
                "total_classified_file_size_bytes": total_file_size_bytes,
            }
        except Exception as e:
            logger.error(
                f"Error getting user classification summary for user_id {user_id}: {e}"
            )
            return {
                "total_classifications": 0,
                "top_classification": None,
                "error": str(e),
            }

    def get_user_llm_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of LLM usage statistics for a given user.
        Queries the 'llm' database.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {
                "error": "User not found",
                "total_llm_sessions": 0,
                "total_llm_messages": 0,
                "total_llm_tokens": 0,
            }

        try:
            # Total LLM sessions
            query_total_sessions = (
                "SELECT COUNT(*) FROM llm_sessions WHERE username = ?"
            )
            total_sessions_result = self.fetch_one(query_total_sessions, (username,))
            total_sessions = total_sessions_result[0] if total_sessions_result else 0

            # Total messages sent/received across all LLM sessions
            query_total_messages = """
                SELECT SUM(total_messages) FROM llm_sessions WHERE username = ?
            """
            total_messages_result = self.fetch_one(query_total_messages, (username,))
            total_messages = (
                total_messages_result[0]
                if total_messages_result and total_messages_result[0] is not None
                else 0
            )

            # Total tokens used across all LLM sessions
            query_total_tokens = """
                SELECT SUM(total_tokens) FROM llm_sessions WHERE username = ?
            """
            total_tokens_result = self.fetch_one(query_total_tokens, (username,))
            total_tokens = (
                total_tokens_result[0]
                if total_tokens_result and total_tokens_result[0] is not None
                else 0
            )

            # Most used LLM model
            query_most_used_model = """
                SELECT model_used, COUNT(*) AS count
                FROM llm_sessions
                WHERE username = ? AND model_used IS NOT NULL
                GROUP BY model_used
                ORDER BY count DESC
                LIMIT 1
            """
            most_used_model_result = self.fetch_one(query_most_used_model, (username,))
            most_used_model = (
                {
                    "model": most_used_model_result[0],
                    "count": most_used_model_result[1],
                }
                if most_used_model_result
                else None
            )

            return {
                "total_llm_sessions": total_sessions,
                "total_llm_messages": total_messages,
                "total_llm_tokens": total_tokens,
                "most_used_llm_model": most_used_model,
            }
        except Exception as e:
            logger.error(f"Error getting user LLM summary for user_id {user_id}: {e}")
            return {
                "total_llm_sessions": 0,
                "total_llm_messages": 0,
                "total_llm_tokens": 0,
                "error": str(e),
            }

    def get_user_app_usage_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of application usage statistics for a given user.
        Queries the 'performance' database for app_startups and api_calls.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {
                "error": "User not found",
                "total_app_startups": 0,
                "total_api_calls": 0,
                "avg_api_response_time_ms": 0,
            }

        try:
            # Total app startups
            query_total_app_startups = (
                "SELECT COUNT(*) FROM app_startups WHERE username = ?"
            )
            total_app_startups_result = self.fetch_one(
                query_total_app_startups, (username,)
            )
            total_app_startups = (
                total_app_startups_result[0] if total_app_startups_result else 0
            )

            # Total API calls
            query_total_api_calls = "SELECT COUNT(*) FROM api_calls WHERE username = ?"
            total_api_calls_result = self.fetch_one(query_total_api_calls, (username,))
            total_api_calls = total_api_calls_result[0] if total_api_calls_result else 0

            # Average API response time
            query_avg_api_response_time = (
                "SELECT AVG(response_time_ms) FROM api_calls WHERE username = ?"
            )
            avg_api_response_time_result = self.fetch_one(
                query_avg_api_response_time, (username,)
            )
            avg_api_response_time_ms = (
                avg_api_response_time_result[0]
                if avg_api_response_time_result
                and avg_api_response_time_result[0] is not None
                else 0.0
            )

            # Most frequent API endpoint
            query_most_frequent_endpoint = """
                SELECT endpoint, COUNT(*) AS count
                FROM api_calls
                WHERE username = ?
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 1
            """
            most_frequent_endpoint_result = self.fetch_one(
                query_most_frequent_endpoint, (username,)
            )
            most_frequent_endpoint = (
                {
                    "endpoint": most_frequent_endpoint_result[0],
                    "count": most_frequent_endpoint_result[1],
                }
                if most_frequent_endpoint_result
                else None
            )

            return {
                "total_app_startups": total_app_startups,
                "total_api_calls": total_api_calls,
                "avg_api_response_time_ms": round(avg_api_response_time_ms, 2),
                "most_frequent_api_endpoint": most_frequent_endpoint,
            }
        except Exception as e:
            logger.error(
                f"Error getting user app usage summary for user_id {user_id}: {e}"
            )
            return {
                "total_app_startups": 0,
                "total_api_calls": 0,
                "avg_api_response_time_ms": 0,
                "error": str(e),
            }

    def get_user_file_upload_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of file upload statistics for a given user.
        Queries the 'performance' database for file_uploads.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {
                "error": "User not found",
                "total_files_uploaded": 0,
                "total_upload_size_bytes": 0,
            }

        try:
            # Total files uploaded
            query_total_uploads = "SELECT COUNT(*) FROM file_uploads WHERE username = ?"
            total_uploads_result = self.fetch_one(query_total_uploads, (username,))
            total_files_uploaded = (
                total_uploads_result[0] if total_uploads_result else 0
            )

            # Total size of uploaded files
            query_total_upload_size = (
                "SELECT SUM(file_size_bytes) FROM file_uploads WHERE username = ?"
            )
            total_upload_size_result = self.fetch_one(
                query_total_upload_size, (username,)
            )
            total_upload_size_bytes = (
                total_upload_size_result[0]
                if total_upload_size_result and total_upload_size_result[0] is not None
                else 0
            )

            # Most common file type uploaded
            query_most_common_file_type = """
                SELECT file_type, COUNT(*) AS count
                FROM file_uploads
                WHERE username = ? AND file_type IS NOT NULL
                GROUP BY file_type
                ORDER BY count DESC
                LIMIT 1
            """
            most_common_file_type_result = self.fetch_one(
                query_most_common_file_type, (username,)
            )
            most_common_file_type = (
                {
                    "type": most_common_file_type_result[0],
                    "count": most_common_file_type_result[1],
                }
                if most_common_file_type_result
                else None
            )

            return {
                "total_files_uploaded": total_files_uploaded,
                "total_upload_size_bytes": total_upload_size_bytes,
                "most_common_file_type": most_common_file_type,
            }
        except Exception as e:
            logger.error(
                f"Error getting user file upload summary for user_id {user_id}: {e}"
            )
            return {
                "total_files_uploaded": 0,
                "total_upload_size_bytes": 0,
                "error": str(e),
            }

    def get_user_audio_transcription_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves a summary of audio transcription statistics for a given user.
        Queries the 'performance' database for audio_transcriptions.
        """
        username = self._get_username_from_user_id(user_id)
        if not username:
            return {
                "error": "User not found",
                "total_transcriptions": 0,
                "total_audio_duration_seconds": 0,
                "total_transcription_chars": 0,
            }

        try:
            # Total audio transcriptions
            query_total_transcriptions = (
                "SELECT COUNT(*) FROM audio_transcriptions WHERE username = ?"
            )
            total_transcriptions_result = self.fetch_one(
                query_total_transcriptions, (username,)
            )
            total_transcriptions = (
                total_transcriptions_result[0] if total_transcriptions_result else 0
            )

            # Total duration of audio transcribed
            query_total_duration = "SELECT SUM(duration_seconds) FROM audio_transcriptions WHERE username = ?"
            total_duration_result = self.fetch_one(query_total_duration, (username,))
            total_audio_duration_seconds = (
                total_duration_result[0]
                if total_duration_result and total_duration_result[0] is not None
                else 0.0
            )

            # Total characters transcribed
            query_total_chars = "SELECT SUM(transcription_length_chars) FROM audio_transcriptions WHERE username = ?"
            total_chars_result = self.fetch_one(query_total_chars, (username,))
            total_transcription_chars = (
                total_chars_result[0]
                if total_chars_result and total_chars_result[0] is not None
                else 0
            )

            # Most used transcription model
            query_most_used_model = """
                SELECT model_used, COUNT(*) AS count
                FROM audio_transcriptions
                WHERE username = ? AND model_used IS NOT NULL
                GROUP BY model_used
                ORDER BY count DESC
                LIMIT 1
            """
            most_used_model_result = self.fetch_one(query_most_used_model, (username,))
            most_used_model = (
                {
                    "model": most_used_model_result[0],
                    "count": most_used_model_result[1],
                }
                if most_used_model_result
                else None
            )

            return {
                "total_transcriptions": total_transcriptions,
                "total_audio_duration_seconds": round(total_audio_duration_seconds, 2),
                "total_transcription_chars": total_transcription_chars,
                "most_used_transcription_model": most_used_model,
            }
        except Exception as e:
            logger.error(
                f"Error getting user audio transcription summary for user_id {user_id}: {e}"
            )
            return {
                "total_transcriptions": 0,
                "total_audio_duration_seconds": 0,
                "total_transcription_chars": 0,
                "error": str(e),
            }


# Global database instances (lazy loading)
_user_db = None
_llm_db = None
_performance_db = None
_chat_db = None
_classifications_db = None


def get_user_database() -> ConsolidatedDatabase:
    """Get the user database instance."""
    global _user_db
    if _user_db is None:
        db_path = get_database_path("users")
        _user_db = ConsolidatedDatabase(db_path)
    return _user_db


def get_llm_database() -> ConsolidatedDatabase:
    """Get the LLM database instance."""
    global _llm_db
    if _llm_db is None:
        db_path = get_database_path("llm")
        _llm_db = ConsolidatedDatabase(db_path)
    return _llm_db


def get_performance_database() -> ConsolidatedDatabase:
    """Get the performance database instance."""
    global _performance_db
    if _performance_db is None:
        db_path = get_database_path("performance")
        _performance_db = ConsolidatedDatabase(db_path)
    return _performance_db


def get_chat_database() -> ConsolidatedDatabase:
    """Get the chat database instance."""
    global _chat_db
    if _chat_db is None:
        db_path = get_database_path("chat")
        _chat_db = ConsolidatedDatabase(db_path)
    return _chat_db


def get_classifications_database() -> ConsolidatedDatabase:
    """Get the classifications database instance."""
    global _classifications_db
    if _classifications_db is None:
        db_path = get_database_path("classifications")
        _classifications_db = ConsolidatedDatabase(db_path)
    return _classifications_db
