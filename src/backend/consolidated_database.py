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
from typing import List, Tuple
from contextlib import contextmanager
from .config import get_chatbot_dir

# Set up logging
logger = logging.getLogger(__name__)


# Database file paths
def get_database_path(db_name: str) -> str:
    """
    Returns the path to the user's database file.

    Args:
        username (str): The username for which to get the database path.

    Returns:
        str: The path to the user's database file.

    Raises:
        ValueError: If the username is invalid or the path cannot be determined.
    """
    # Sanitize database name to prevent path traversal
    if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
        raise ValueError(f"Invalid database name: {db_name}")

    base_dir = get_chatbot_dir()
    db_dir = os.path.join(base_dir, "data", "sqlite")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f"{db_name}.db")


class InputSanitizer:
    """
    Sanitizes user input for database operations.
    """

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitizes a string value for safe database usage.

        Raises:
            ValueError: If the string is invalid or contains unsafe characters.
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def sanitize_username(username: str) -> str:
        """
        Sanitizes a username for safe database usage.

        Raises:
            ValueError: If the username is invalid or contains unsafe characters.
        """
        if not username:
            raise ValueError("Username cannot be empty")

        sanitized = InputSanitizer.sanitize_string(username, max_length=50)

        # Username must be alphanumeric with hyphens and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", sanitized):
            raise ValueError("Username contains invalid characters")

        return sanitized

    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitizes an email address for safe database usage.

        Raises:
            ValueError: If the email is invalid or contains unsafe characters.
        """
        if not email:
            raise ValueError("Email cannot be empty")

        sanitized = InputSanitizer.sanitize_string(email, max_length=100)

        # Basic email validation
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", sanitized):
            raise ValueError("Invalid email format")

        return sanitized.lower()

    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """
        Sanitizes a file path for safe database usage.

        Raises:
            ValueError: If the file path is invalid or contains unsafe characters.
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        sanitized = InputSanitizer.sanitize_string(file_path, max_length=500)

        # Prevent path traversal
        if ".." in sanitized or "//" in sanitized:
            raise ValueError("Invalid file path")

        return sanitized


class ConsolidatedDatabase:
    """
    Consolidated database handler for user data.

    Args:
        db_path (str): Path to the database file.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_name = os.path.basename(db_path).replace(
            ".db", ""
        )  # Extract db_name from path
        self._init_database()

    def _init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                cursor = conn.cursor()

                if self.db_name == "users":
                    self._init_users_database(cursor)
                elif self.db_name == "llm":
                    self._init_llm_database(cursor)
                elif self.db_name == "performance":
                    self._init_performance_database(cursor)
                elif self.db_name == "chat":
                    self._init_chat_database(cursor)
                elif self.db_name == "classifications":
                    self._init_classifications_database(cursor)
                else:
                    raise ValueError(f"Unknown database name: {self.db_name}")

                conn.commit()
                logger.info(
                    f"SQLite database '{self.db_name}' initialized successfully"
                )

        except Exception as e:
            logger.error(f"Failed to initialize SQLite database '{self.db_name}': {e}")
            raise

    def _init_users_database(self, cursor):
        """Initialize users database schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_test_user BOOLEAN DEFAULT 0,
                last_login TEXT,
                login_count INTEGER DEFAULT 0
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)"
        )

    def _init_llm_database(self, cursor):
        """Initialize LLM database schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                model_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                token_count INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES llm_sessions (session_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                embedding_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_sessions_username ON llm_sessions(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_sessions_session_id ON llm_sessions(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_messages_session_id ON llm_messages(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_llm_embeddings_hash ON llm_embeddings(content_hash)"
        )

    def _init_performance_database(self, cursor):
        """Initialize performance tracking database schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docker_builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                build_id TEXT UNIQUE NOT NULL,
                build_start_time TEXT NOT NULL,
                build_end_time TEXT,
                build_duration REAL,
                build_status TEXT NOT NULL,
                image_size REAL,
                build_logs TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration REAL,
                status_code INTEGER,
                response_size INTEGER,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_startups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                startup_id TEXT UNIQUE NOT NULL,
                startup_start_time TEXT NOT NULL,
                startup_end_time TEXT,
                startup_duration REAL,
                startup_status TEXT NOT NULL,
                component_load_times TEXT,
                memory_usage REAL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_docker_builds_username ON docker_builds(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_docker_builds_build_id ON docker_builds(build_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_calls_username ON api_calls(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON api_calls(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_app_startups_username ON app_startups(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_app_startups_startup_id ON app_startups(startup_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_username ON performance_metrics(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type)"
        )

    def _init_chat_database(self, cursor):
        """Initialize chat database schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                session_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"
        )

    def _init_classifications_database(self, cursor):
        """Initialize classifications database schema."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                username TEXT NOT NULL,
                classification_result TEXT NOT NULL,
                sensitivity_level TEXT,
                security_level TEXT,
                created_at TEXT NOT NULL,
                file_size INTEGER,
                extraction_method TEXT,
                processing_time REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                classification_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (classification_id) REFERENCES classifications (id)
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classifications_username ON classifications(username)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classifications_file_path ON classifications(file_path)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classifications_created_at ON classifications(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_classification_history_username ON classification_history(username)"
        )

    @contextmanager
    def get_connection(self):
        """
        Returns a database connection.

        Returns:
            Connection: A database connection object.

        Raises:
            Exception: If the connection cannot be established.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """Execute a SELECT query with parameterized queries to prevent SQL injection.

        :param query: SQL query to execute
        :type query: str
        :param params: Query parameters
        :type params: tuple
        :return: List of result tuples
        :rtype: List[Tuple]
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute an INSERT, UPDATE, or DELETE query with parameterized queries.

        :param query: SQL query to execute
        :type query: str
        :param params: Query parameters
        :type params: tuple
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            return False

    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """Execute multiple queries with parameterized queries.

        :param query: SQL query to execute
        :type query: str
        :param params_list: List of parameter tuples
        :type params_list: List[tuple]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            return False


# Global database instances
_user_db = None
_llm_db = None
_performance_db = None
_chat_db = None
_classifications_db = None


def get_user_database() -> ConsolidatedDatabase:
    """Get the user database instance."""
    global _user_db
    if _user_db is None:
        _user_db = ConsolidatedDatabase("users")
    return _user_db


def get_llm_database() -> ConsolidatedDatabase:
    """Get the LLM database instance."""
    global _llm_db
    if _llm_db is None:
        _llm_db = ConsolidatedDatabase("llm")
    return _llm_db


def get_performance_database() -> ConsolidatedDatabase:
    """Get the performance database instance."""
    global _performance_db
    if _performance_db is None:
        _performance_db = ConsolidatedDatabase("performance")
    return _performance_db


def get_chat_database() -> ConsolidatedDatabase:
    """Get the chat database instance."""
    global _chat_db
    if _chat_db is None:
        _chat_db = ConsolidatedDatabase("chat")
    return _chat_db


def get_classifications_database() -> ConsolidatedDatabase:
    """Get the classifications database instance."""
    global _classifications_db
    if _classifications_db is None:
        _classifications_db = ConsolidatedDatabase("classifications")
    return _classifications_db
