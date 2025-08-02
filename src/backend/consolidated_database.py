#!/usr/bin/env python3
"""
Consolidated SQLite Database module for the NYP FYP CNC Chatbot backend.

This module provides consolidated database functionality including:

- User data management (single SQLite file for all purposes)
- LLM data management (now within the consolidated file)
- Performance tracking (now within the consolidated file)
- Input sanitization and SQL injection prevention
- Docker build time, API call time, and app startup time tracking
- Proper database isolation and security

The module uses a single SQLite file for all purposes and includes
comprehensive security measures to prevent SQL injection attacks.
"""

import json
import sqlite3
import os
import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from contextlib import contextmanager
from infra_utils import get_chatbot_dir
from .timezone_utils import get_utc_timestamp  # Ensure this is imported for timestamps

# Set up logging
logger = logging.getLogger(__name__)


# Database file path
def get_database_path(db_name: str) -> str:
    """
    Returns the path to the specified database file.

    Args:
        db_name (str): The name of the database file (e.g., 'main_db').

    Returns:
        str: The path to the database file.

    Raises:
        ValueError: If the db_name is invalid or the path cannot be determined.
    """
    # Sanitize database name to prevent path traversal
    if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
        raise ValueError(f"Invalid database name: {db_name}")

    # If running in Docker or benchmark mode and db_name is 'users', use a temp directory to avoid persistence
    # This logic from original consolidated_database.py seems specific to 'users' but for a single DB,
    # it implies the primary DB. Let's make it for the main consolidated DB if needed.
    if (
        os.environ.get("BENCHMARK_MODE")
        and os.environ.get("DOCKER_BUILD")
        and db_name == "main_db"  # Assuming "main_db" is the consolidated one
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
    def sanitize_username(input_string: str) -> str:
        """
        Sanitizes a username string.
        Allows alphanumeric characters, underscores, and hyphens.
        """
        if not isinstance(input_string, str):
            return ""
        # Remove any characters not allowed in a username (alphanumeric, _, -)
        sanitized_string = re.sub(r"[^a-zA-Z0-9_-]", "", input_string)
        return sanitized_string.strip()

    @staticmethod
    def sanitize_email(input_string: str) -> str:
        """
        Sanitizes an email address string.
        Performs basic validation and sanitization.
        """
        if not isinstance(input_string, str):
            return ""
        # A more robust regex for email validation
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.fullmatch(email_regex, input_string):
            # If it matches, we can be reasonably sure it's safe, but strip whitespace
            return input_string.strip()
        return ""  # Return empty string for invalid email format

    @staticmethod
    def sanitize_string(input_string: str, max_length: Optional[int] = None) -> str:
        """
        Sanitizes a general string input to prevent common injection attacks.
        This method is primarily for displaying or logging, not for direct SQL parameters.
        For SQL, always use parameterized queries.

        Args:
            input_string (str): The string to sanitize.
            max_length (Optional[int]): The maximum allowed length for the sanitized string.
                                        If the string exceeds this length, it will be truncated.
                                        Defaults to None (no length limit).
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
        sanitized_string = sanitized_string.strip()

        # Apply max_length if provided
        if max_length is not None and isinstance(max_length, int) and max_length >= 0:
            return sanitized_string[:max_length]

        return sanitized_string

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
    def generate_pdf_report(self, username, stats):
        """
        Placeholder for PDF report generation. Returns a dummy file path.
        """
        # TODO: Implement actual PDF generation logic
        return None

    """
    Consolidated SQLite database handler.

    This class manages connections and operations for a single SQLite database file
    containing all application-related tables. It provides a secure interface with
    input sanitization and SQL injection prevention.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = get_database_path("main_db")  # Use a single main DB file
        else:
            self.db_path = db_path
        self.db_name = os.path.basename(self.db_path).replace(
            ".db", ""
        )  # For logging or debug
        self._init_database()

    @contextmanager
    def get_db_connection(self):
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
        Initialize the database with all required tables.
        """
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # --- Users Table (from both consolidated_database.py and sqlite_database.py) ---
            # Merging columns, prioritizing the more comprehensive set from sqlite_database.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    hashed_password TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_test_user INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login TEXT,
                    login_count INTEGER DEFAULT 0,
                    last_login_success TEXT,
                    login_failures INTEGER DEFAULT 0
                )
            """)

            # --- User Activity Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- Chat Sessions Table (from both consolidated_database.py and sqlite_database.py) ---
            # Merging columns, prioritizing the more comprehensive set from sqlite_database.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    session_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- Chat Messages Table (from both consolidated_database.py and sqlite_database.py) ---
            # Merging columns, prioritizing the more comprehensive set from sqlite_database.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    message_index INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TEXT NOT NULL, -- Added to match updated_at pattern
                    token_count INTEGER DEFAULT 0, -- From llm_messages table, can be useful here
                    metadata TEXT, -- For any extra info
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                )
            """)
            # Add index for (session_id, username) for efficient lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id_username ON chat_messages (session_id, username)
            """)

            # --- Classifications Table (from both consolidated_database.py and sqlite_database.py) ---
            # Merging columns, prioritizing the more comprehensive set from sqlite_database.py
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    classification_result TEXT NOT NULL,
                    sensitivity_level TEXT,
                    security_level TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    file_size INTEGER,
                    extraction_method TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- LLM Sessions Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    session_id TEXT NOT NULL UNIQUE,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    model_used TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL, -- Added for consistency
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- LLM Messages Table (from consolidated_database.py) ---
            # Note: The logic for chat_messages above already covers message content.
            # This table might be redundant if chat_messages covers all message types.
            # However, if 'llm_messages' is specifically for LLM-related internal logs
            # or different structure, we'll keep it. For now, consolidating to chat_messages.
            # If explicit separate LLM message tracking is needed, this table can be
            # re-added with unique purpose. Assuming chat_messages covers this for now.
            # Removed: LLM_messages table, as its columns are largely covered by chat_messages.
            # If there's a specific need for LLM interaction logging distinct from
            # user chat, it should be re-evaluated.

            # --- LLM Embeddings Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    content_type TEXT NOT NULL, -- e.g., 'document', 'chat_message'
                    content_id TEXT NOT NULL,
                    embedding_vector BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- App Startups Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_startups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT, -- Can be NULL for initial app startup
                    timestamp TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    duration_ms INTEGER,
                    os_info TEXT,
                    python_version TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- API Calls Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT, -- Can be NULL for unauthenticated calls
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    duration_ms INTEGER,
                    status_code INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- Database Operations Table (from consolidated_database.py) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS database_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL, -- e.g., 'INSERT', 'UPDATE', 'DELETE', 'QUERY'
                    table_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    duration_ms INTEGER,
                    rows_affected INTEGER,
                    username TEXT, -- Optional, if linked to a user action
                    details TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # --- Indexes ---
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_activity_username ON user_activity (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id_index ON chat_messages (session_id, message_index)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_classifications_username ON classifications (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_llm_sessions_username ON llm_sessions (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_llm_embeddings_username ON llm_embeddings (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_app_startups_username ON app_startups (username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_calls_endpoint ON api_calls (endpoint)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_database_operations_table_name ON database_operations (table_name)"
            )

            conn.commit()

    def execute_query(
        self, query: str, params: Optional[Tuple] = None
    ) -> List[sqlite3.Row]:
        """
        Executes a SELECT query and returns the results.
        Always use parameterized queries to prevent SQL injection.
        """
        if params is None:
            params = ()
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(
                f"Database query error in {self.db_name}: {e} for query: {query} with params: {params}"
            )
            raise

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Executes an INSERT, UPDATE, or DELETE query and returns the number of rows affected.
        Always use parameterized queries to prevent SQL injection.
        """
        if params is None:
            params = ()
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(
                f"Database update error in {self.db_name}: {e} for query: {query} with params: {params}"
            )
            raise

    # --- User Management Methods ---
    def add_user(
        self, username, hashed_password, email, is_test_user=0
    ) -> Optional[int]:
        """Adds a new user to the database."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_email = InputSanitizer.sanitize_email(email)
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO users (username, hashed_password, email, created_at, updated_at, is_test_user)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            hashed_password,
            sanitized_email,
            current_timestamp,
            current_timestamp,
            is_test_user,
        )
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                logger.info(f"User '{sanitized_username}' added successfully.")
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(
                f"Attempted to add existing user: '{sanitized_username}' or email '{sanitized_email}'."
            )
            return None
        except sqlite3.Error as e:
            logger.error(f"Error adding user '{sanitized_username}': {e}")
            raise

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by username."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = "SELECT * FROM users WHERE username = ?"
        result = self.execute_query(query, (sanitized_username,))
        return dict(result[0]) if result else None

    def update_user_last_login(self, username: str):
        """Updates a user's last login timestamp and increments login count."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        current_timestamp = get_utc_timestamp()
        query = """
            UPDATE users SET last_login = ?, login_count = login_count + 1, updated_at = ? WHERE username = ?
        """
        rows_affected = self.execute_update(
            query, (current_timestamp, current_timestamp, sanitized_username)
        )
        if rows_affected == 0:
            logger.warning(
                f"User '{sanitized_username}' not found for last login update."
            )

    def update_user_password(self, username: str, new_hashed_password: str) -> bool:
        """Updates a user's password."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        current_timestamp = get_utc_timestamp()
        query = (
            "UPDATE users SET hashed_password = ?, updated_at = ? WHERE username = ?"
        )
        rows_affected = self.execute_update(
            query, (new_hashed_password, current_timestamp, sanitized_username)
        )
        return rows_affected > 0

    def record_login_failure(self, username: str):
        """Records a login failure for a user."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = """
            UPDATE users SET login_failures = login_failures + 1, updated_at = ? WHERE username = ?
        """
        current_timestamp = get_utc_timestamp()
        self.execute_update(query, (current_timestamp, sanitized_username))

    def reset_login_failures(self, username: str):
        """Resets login failures for a user upon successful login."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = """
            UPDATE users SET login_failures = 0, last_login_success = ?, updated_at = ? WHERE username = ?
        """
        current_timestamp = get_utc_timestamp()
        self.execute_update(
            query, (current_timestamp, current_timestamp, sanitized_username)
        )

    def get_user_login_failures(self, username: str) -> int:
        """Gets the number of login failures for a user."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = "SELECT login_failures FROM users WHERE username = ?"
        result = self.execute_query(query, (sanitized_username,))
        return result[0]["login_failures"] if result else 0

    def record_user_activity(
        self, username: str, activity_type: str, details: Optional[str] = None
    ):
        """Records user activity."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_activity_type = InputSanitizer.sanitize_string(activity_type)
        sanitized_details = InputSanitizer.sanitize_text(details) if details else None
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO user_activity (username, activity_type, timestamp, details)
            VALUES (?, ?, ?, ?)
        """
        self.execute_update(
            query,
            (
                sanitized_username,
                sanitized_activity_type,
                current_timestamp,
                sanitized_details,
            ),
        )

    # --- Chat Session Management Methods ---
    def create_chat_session(
        self, username: str, session_id: str, session_name: str
    ) -> int:
        """Creates a new chat session."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        sanitized_session_name = InputSanitizer.sanitize_string(session_name)
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO chat_sessions (username, session_id, session_name, created_at, updated_at, message_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            sanitized_session_id,
            sanitized_session_name,
            current_timestamp,
            current_timestamp,
            0,
            True,
        )
        return self.execute_update(query, params)

    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a chat session by ID."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        query = "SELECT * FROM chat_sessions WHERE session_id = ?"
        result = self.execute_query(query, (sanitized_session_id,))
        return dict(result[0]) if result else None

    def get_chat_sessions_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Retrieves all chat sessions for a given user."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = (
            "SELECT * FROM chat_sessions WHERE username = ? ORDER BY updated_at DESC"
        )
        results = self.execute_query(query, (sanitized_username,))
        return [dict(row) for row in results]

    def update_chat_session_timestamp(self, session_id: str):
        """Updates the updated_at timestamp of a chat session."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        current_timestamp = get_utc_timestamp()
        query = "UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?"
        self.execute_update(query, (current_timestamp, sanitized_session_id))

    def update_chat_session_message_count(self, session_id: str, increment: int = 1):
        """Increments the message count for a chat session."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        current_timestamp = get_utc_timestamp()
        query = """
            UPDATE chat_sessions SET message_count = message_count + ?, updated_at = ? WHERE session_id = ?
        """
        self.execute_update(query, (increment, current_timestamp, sanitized_session_id))

    def add_chat_message(
        self,
        session_id: str,
        message_index: int,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        """Adds a new message to a chat session."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        sanitized_role = InputSanitizer.sanitize_string(role)
        sanitized_content = InputSanitizer.sanitize_text(content)
        current_timestamp = get_utc_timestamp()
        metadata_json = json.dumps(metadata) if metadata else None

        query = """
            INSERT INTO chat_messages (session_id, message_index, role, content, timestamp, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_session_id,
            message_index,
            sanitized_role,
            sanitized_content,
            current_timestamp,
            current_timestamp,
            metadata_json,
        )
        # Increment message count on session
        self.update_chat_session_message_count(session_id, 1)
        return self.execute_update(query, params)

    def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all messages for a given chat session."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        query = "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY message_index ASC"
        results = self.execute_query(query, (sanitized_session_id,))
        return [dict(row) for row in results]

    def delete_chat_session(self, session_id: str) -> int:
        """Deletes a chat session and its associated messages."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        messages_deleted = self.execute_update(
            "DELETE FROM chat_messages WHERE session_id = ?", (sanitized_session_id,)
        )
        sessions_deleted = self.execute_update(
            "DELETE FROM chat_sessions WHERE session_id = ?", (sanitized_session_id,)
        )
        logger.info(
            f"Deleted session '{session_id}': {sessions_deleted} sessions, {messages_deleted} messages."
        )
        return sessions_deleted

    def delete_all_chat_sessions_for_user(self, username: str) -> int:
        """Deletes all chat sessions and their messages for a given user."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sessions_to_delete = self.get_chat_sessions_by_username(sanitized_username)
        total_sessions_deleted = 0
        total_messages_deleted = 0
        for session in sessions_to_delete:
            session_id = session["session_id"]
            messages_deleted = self.execute_update(
                "DELETE FROM chat_messages WHERE session_id = ?", (session_id,)
            )
            sessions_deleted = self.execute_update(
                "DELETE FROM chat_sessions WHERE session_id = ?", (session_id,)
            )
            total_messages_deleted += messages_deleted
            total_sessions_deleted += sessions_deleted
        logger.info(
            f"Deleted all sessions for user '{sanitized_username}': {total_sessions_deleted} sessions, {total_messages_deleted} messages."
        )
        return total_sessions_deleted

    # --- Classification Management Methods ---
    def add_classification_result(
        self,
        username: str,
        file_path: str,
        classification_result: str,
        sensitivity_level: Optional[str] = None,
        security_level: Optional[str] = None,
        file_size: Optional[int] = None,
        extraction_method: Optional[str] = None,
    ) -> int:
        """Adds a new classification result."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_file_path = InputSanitizer.sanitize_string(file_path)
        sanitized_classification_result = InputSanitizer.sanitize_string(
            classification_result
        )
        sanitized_sensitivity_level = (
            InputSanitizer.sanitize_string(sensitivity_level)
            if sensitivity_level
            else None
        )
        sanitized_security_level = (
            InputSanitizer.sanitize_string(security_level) if security_level else None
        )
        sanitized_extraction_method = (
            InputSanitizer.sanitize_string(extraction_method)
            if extraction_method
            else None
        )
        current_timestamp = get_utc_timestamp()

        query = """
            INSERT INTO classifications (username, file_path, classification_result, sensitivity_level,
                                         security_level, created_at, updated_at, file_size, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            sanitized_file_path,
            sanitized_classification_result,
            sanitized_sensitivity_level,
            sanitized_security_level,
            current_timestamp,
            current_timestamp,
            file_size,
            sanitized_extraction_method,
        )
        return self.execute_update(query, params)

    def get_classifications_by_username(
        self, username: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves classification results for a given user."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        query = """
            SELECT file_path, classification_result, sensitivity_level, security_level,
                   created_at, file_size, extraction_method, updated_at
            FROM classifications
            WHERE username = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = self.execute_query(query, (sanitized_username, limit))
        return [dict(row) for row in results]

    # --- LLM Session and Embeddings Management Methods ---
    def create_llm_session(
        self, username: str, session_id: str, model_used: str
    ) -> int:
        """Creates a new LLM session."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        sanitized_model_used = InputSanitizer.sanitize_string(model_used)
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO llm_sessions (username, session_id, start_time, model_used, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            sanitized_session_id,
            current_timestamp,
            sanitized_model_used,
            current_timestamp,
        )
        return self.execute_update(query, params)

    def update_llm_session(
        self, session_id: str, end_time: str, total_tokens: int, total_messages: int
    ) -> int:
        """Updates an LLM session with end time, tokens, and message count."""
        sanitized_session_id = InputSanitizer.sanitize_string(session_id)
        current_timestamp = get_utc_timestamp()
        query = """
            UPDATE llm_sessions SET end_time = ?, total_tokens = ?, total_messages = ?, updated_at = ?
            WHERE session_id = ?
        """
        params = (
            end_time,
            total_tokens,
            total_messages,
            current_timestamp,
            sanitized_session_id,
        )
        return self.execute_update(query, params)

    def add_llm_embedding(
        self, username: str, content_type: str, content_id: str, embedding_vector: bytes
    ) -> int:
        """Adds a new LLM embedding."""
        sanitized_username = InputSanitizer.sanitize_username(username)
        sanitized_content_type = InputSanitizer.sanitize_string(content_type)
        sanitized_content_id = InputSanitizer.sanitize_string(content_id)
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO llm_embeddings (username, content_type, content_id, embedding_vector, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            sanitized_content_type,
            sanitized_content_id,
            embedding_vector,
            current_timestamp,
            current_timestamp,
        )
        return self.execute_update(query, params)

    # --- Performance Tracking Methods ---
    def add_app_startup_record(
        self,
        username: Optional[str],
        duration_ms: int,
        os_info: str,
        python_version: str,
    ) -> int:
        """Adds a record for application startup time."""
        sanitized_username = (
            InputSanitizer.sanitize_username(username) if username else None
        )
        sanitized_os_info = InputSanitizer.sanitize_string(os_info)
        sanitized_python_version = InputSanitizer.sanitize_string(python_version)
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO app_startups (username, timestamp, updated_at, duration_ms, os_info, python_version)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            current_timestamp,
            current_timestamp,
            duration_ms,
            sanitized_os_info,
            sanitized_python_version,
        )
        return self.execute_update(query, params)

    def add_api_call_record(
        self,
        username: Optional[str],
        endpoint: str,
        method: str,
        duration_ms: int,
        status_code: int,
        error_message: Optional[str] = None,
    ) -> int:
        """Adds a record for API call performance."""
        sanitized_username = (
            InputSanitizer.sanitize_username(username) if username else None
        )
        sanitized_endpoint = InputSanitizer.sanitize_string(endpoint)
        sanitized_method = InputSanitizer.sanitize_string(method)
        sanitized_error_message = (
            InputSanitizer.sanitize_text(error_message) if error_message else None
        )
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO api_calls (username, endpoint, method, timestamp, updated_at, duration_ms, status_code, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_username,
            sanitized_endpoint,
            sanitized_method,
            current_timestamp,
            current_timestamp,
            duration_ms,
            status_code,
            sanitized_error_message,
        )
        return self.execute_update(query, params)

    def get_llm_performance_summary(self, username: Optional[str] = None) -> list:
        """Returns LLM performance summary for a user or all users."""
        logger.info(
            f"[DEBUG] get_llm_performance_summary called for username={username}"
        )
        query = """
            SELECT model_used as model_name, COUNT(*) as total_calls, SUM(total_tokens) as total_tokens,
                   AVG(julianday(end_time) - julianday(start_time)) * 86400.0 as avg_latency_ms
            FROM llm_sessions
            {where_clause}
            GROUP BY model_used
        """
        where_clause = "WHERE username = ?" if username else ""
        final_query = query.format(where_clause=where_clause)
        params = (username,) if username else ()
        results = self.execute_query(final_query, params)
        return [dict(row) for row in results]

    def get_api_call_summary(self, username: Optional[str] = None) -> list:
        """Returns API call performance summary for a user or all users."""
        logger.info(f"[DEBUG] get_api_call_summary called for username={username}")
        query = """
            SELECT endpoint, method, COUNT(*) as total_calls,
                   AVG(duration_ms) as avg_duration_ms,
                   SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as successful_calls,
                   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as failed_calls
            FROM api_calls
            {where_clause}
            GROUP BY endpoint, method
        """
        where_clause = "WHERE username = ?" if username else ""
        final_query = query.format(where_clause=where_clause)
        params = (username,) if username else ()
        results = self.execute_query(final_query, params)
        return [dict(row) for row in results]

    def get_document_classifications_by_user(
        self, username: str, limit: int = 10
    ) -> list:
        """Returns recent file classification results for a user."""
        logger.info(
            f"[DEBUG] get_document_classifications_by_user called for username={username}"
        )
        return self.get_classifications_by_username(username, limit)

    def get_app_startup_records(self, limit: int = 100) -> list:
        """Returns recent app startup records."""
        logger.info(f"[DEBUG] get_app_startup_records called with limit={limit}")
        query = """
            SELECT *, (duration_ms / 1000.0) as startup_time_seconds
            FROM app_startups
            ORDER BY timestamp DESC
            LIMIT ?
        """
        results = self.execute_query(query, (limit,))
        return [dict(row) for row in results]

    def add_database_operation_record(
        self,
        operation_type: str,
        table_name: str,
        duration_ms: int,
        rows_affected: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[str] = None,
    ) -> int:
        """Adds a record for database operation performance."""
        sanitized_operation_type = InputSanitizer.sanitize_string(operation_type)
        sanitized_table_name = InputSanitizer.sanitize_string(table_name)
        sanitized_username = (
            InputSanitizer.sanitize_username(username) if username else None
        )
        sanitized_details = InputSanitizer.sanitize_text(details) if details else None
        current_timestamp = get_utc_timestamp()
        query = """
            INSERT INTO database_operations (operation_type, table_name, timestamp, updated_at, duration_ms, rows_affected, username, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sanitized_operation_type,
            sanitized_table_name,
            current_timestamp,
            current_timestamp,
            duration_ms,
            rows_affected,
            sanitized_username,
            sanitized_details,
        )
        return self.execute_update(query, params)


# Global database instance (lazy loading, single instance for all SQLite needs)
_consolidated_db = None


def get_consolidated_database() -> ConsolidatedDatabase:
    """
    Get the single, consolidated SQLite database instance.
    """
    global _consolidated_db
    if _consolidated_db is None:
        _consolidated_db = ConsolidatedDatabase(get_database_path("main_db"))
    return _consolidated_db
