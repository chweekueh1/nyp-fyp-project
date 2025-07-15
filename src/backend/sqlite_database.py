#!/usr/bin/env python3
"""
SQLite Database module for the NYP FYP CNC Chatbot backend.

This module provides SQLite database functionality including:

- SQLite database initialization and management
- User data storage and retrieval
- Chat session management
- Classification data storage
- Alpine Linux friendly database operations

The module uses SQLite3 (built into Python) for reliable database operations
on Alpine Linux without external dependencies.
"""

import sqlite3
import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from .config import get_chatbot_dir
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


# Database paths
def get_sqlite_db_path(db_name: str) -> str:
    """Get the SQLite database file path."""
    base_dir = get_chatbot_dir()
    db_dir = os.path.join(base_dir, "data", "sqlite")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f"{db_name}.db")


class SQLiteDatabase:
    """
    SQLite database handler for user data.

    Args:
        db_path (str): Path to the database file.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_name = os.path.basename(db_path).replace(".db", "")
        self._init_database()

    def _init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        is_test_user BOOLEAN DEFAULT 0
                    )
                """)

                # Create chat_sessions table
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

                # Create chat_messages table
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

                # Create classifications table
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
                        extraction_method TEXT
                    )
                """)

                # Create indexes for better performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_username ON chat_sessions(username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_classifications_username ON classifications(username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_classifications_file_path ON classifications(file_path)"
                )

                conn.commit()
                logger.info(
                    f"SQLite database '{self.db_name}' initialized successfully"
                )

        except Exception as e:
            logger.error(f"Failed to initialize SQLite database '{self.db_name}': {e}")
            raise

    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """Execute a SELECT query and return results.

        :param query: SQL query to execute
        :type query: str
        :param params: Query parameters
        :type params: tuple
        :return: List of result tuples
        :rtype: List[Tuple]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Execute an INSERT, UPDATE, or DELETE query.

        :param query: SQL query to execute
        :type query: str
        :param params: Query parameters
        :type params: tuple
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username.

        :param username: Username to look up
        :type username: str
        :return: User data dictionary or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        query = "SELECT id, username, email, password_hash, created_at, updated_at, is_active, is_test_user FROM users WHERE username = ?"
        results = self.execute_query(query, (username,))

        if results:
            row = results[0]
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password_hash": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "is_active": bool(row[6]),
                "is_test_user": bool(row[7]),
            }
        return None

    def create_user(
        self, username: str, email: str, password_hash: str, is_test_user: bool = False
    ) -> bool:
        """Create a new user.

        :param username: Username
        :type username: str
        :param email: Email address
        :type email: str
        :param password_hash: Hashed password
        :type password_hash: str
        :param is_test_user: Whether this is a test user
        :type is_test_user: bool
        :return: True if successful, False otherwise
        :rtype: bool
        """
        timestamp = get_utc_timestamp()
        query = """
            INSERT INTO users (username, email, password_hash, created_at, updated_at, is_test_user)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(
            query, (username, email, password_hash, timestamp, timestamp, is_test_user)
        )

    def update_user(self, username: str, **kwargs):
        """
        Updates user information in the database.

        Args:
            username (str): The username to update.
            **kwargs: Fields to update as keyword arguments.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not kwargs:
            return False

        set_clauses = []
        params = []

        for key, value in kwargs.items():
            if key in [
                "username",
                "email",
                "password_hash",
                "is_active",
                "is_test_user",
            ]:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        if not set_clauses:
            return False

        params.extend((get_utc_timestamp(), username))
        query = f"UPDATE users SET {', '.join(set_clauses)}, updated_at = ? WHERE username = ?"
        return self.execute_update(query, tuple(params))

    def delete_user(self, username: str) -> bool:
        """Delete a user.

        :param username: Username to delete
        :type username: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        query = "DELETE FROM users WHERE username = ?"
        return self.execute_update(query, (username,))

    def get_chat_sessions(self, username: str) -> List[Dict[str, Any]]:
        """Get chat sessions for a user.

        :param username: Username
        :type username: str
        :return: List of chat session dictionaries
        :rtype: List[Dict[str, Any]]
        """
        query = """
            SELECT session_id, session_name, created_at, updated_at, message_count, is_active
            FROM chat_sessions
            WHERE username = ? AND is_active = 1
            ORDER BY updated_at DESC
        """
        results = self.execute_query(query, (username,))

        sessions = []
        sessions.extend(
            {
                "session_id": row[0],
                "session_name": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": row[4],
                "is_active": bool(row[5]),
            }
            for row in results
        )
        return sessions

    def create_chat_session(
        self, session_id: str, username: str, session_name: str = None
    ) -> bool:
        """Create a new chat session.

        :param session_id: Unique session ID
        :type session_id: str
        :param username: Username
        :type username: str
        :param session_name: Optional session name
        :type session_name: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        timestamp = get_utc_timestamp()
        query = """
            INSERT INTO chat_sessions (session_id, username, session_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_update(
            query, (session_id, username, session_name, timestamp, timestamp)
        )

    def add_chat_message(
        self, session_id: str, message_type: str, content: str, metadata: Dict = None
    ) -> bool:
        """Add a message to a chat session.

        :param session_id: Session ID
        :type session_id: str
        :param message_type: Type of message (user/assistant)
        :type message_type: str
        :param content: Message content
        :type content: str
        :param metadata: Optional metadata
        :type metadata: Dict
        :return: True if successful, False otherwise
        :rtype: bool
        """
        timestamp = get_utc_timestamp()
        metadata_json = json.dumps(metadata) if metadata else None

        # Add message
        query = """
            INSERT INTO chat_messages (session_id, message_type, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """
        if not self.execute_update(
            query, (session_id, message_type, content, timestamp, metadata_json)
        ):
            return False

        # Update session message count and timestamp
        update_query = """
            UPDATE chat_sessions
            SET message_count = message_count + 1, updated_at = ?
            WHERE session_id = ?
        """
        return self.execute_update(update_query, (timestamp, session_id))

    def get_chat_messages(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a chat session.

        :param session_id: Session ID
        :type session_id: str
        :param limit: Maximum number of messages to return
        :type limit: int
        :return: List of message dictionaries
        :rtype: List[Dict[str, Any]]
        """
        query = """
            SELECT message_type, content, timestamp, metadata
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """
        results = self.execute_query(query, (session_id, limit))

        messages = []
        for row in results:
            metadata = json.loads(row[3]) if row[3] else {}
            messages.append(
                {
                    "message_type": row[0],
                    "content": row[1],
                    "timestamp": row[2],
                    "metadata": metadata,
                }
            )

        return messages

    def save_classification(
        self,
        file_path: str,
        username: str,
        classification_result: str,
        sensitivity_level: str = None,
        security_level: str = None,
        file_size: int = None,
        extraction_method: str = None,
    ) -> bool:
        """Save a classification result.

        :param file_path: Path to the classified file
        :type file_path: str
        :param username: Username who performed the classification
        :type username: str
        :param classification_result: Classification result JSON
        :type classification_result: str
        :param sensitivity_level: Sensitivity level
        :type sensitivity_level: str
        :param security_level: Security level
        :type security_level: str
        :param file_size: File size in bytes
        :type file_size: int
        :param extraction_method: Method used for text extraction
        :type extraction_method: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        timestamp = get_utc_timestamp()
        query = """
            INSERT INTO classifications
            (file_path, username, classification_result, sensitivity_level, security_level,
             created_at, file_size, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(
            query,
            (
                file_path,
                username,
                classification_result,
                sensitivity_level,
                security_level,
                timestamp,
                file_size,
                extraction_method,
            ),
        )

    def get_classifications(
        self, username: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get classification history for a user.

        :param username: Username
        :type username: str
        :param limit: Maximum number of classifications to return
        :type limit: int
        :return: List of classification dictionaries
        :rtype: List[Dict[str, Any]]
        """
        query = """
            SELECT file_path, classification_result, sensitivity_level, security_level,
                   created_at, file_size, extraction_method
            FROM classifications
            WHERE username = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = self.execute_query(query, (username, limit))

        classifications = []
        for row in results:
            classifications.append(
                {
                    "file_path": row[0],
                    "classification_result": row[1],
                    "sensitivity_level": row[2],
                    "security_level": row[3],
                    "created_at": row[4],
                    "file_size": row[5],
                    "extraction_method": row[6],
                }
            )

        return classifications


# Global database instances
_user_db = None
_chat_db = None
_classification_db = None


def get_user_database() -> SQLiteDatabase:
    """Get the user database instance."""
    global _user_db
    if _user_db is None:
        _user_db = SQLiteDatabase(get_sqlite_db_path("users"))
    return _user_db


def get_chat_database() -> SQLiteDatabase:
    """Get the chat database instance."""
    global _chat_db
    if _chat_db is None:
        _chat_db = SQLiteDatabase(get_sqlite_db_path("chat"))
    return _chat_db


def get_classification_database() -> SQLiteDatabase:
    """Get the classification database instance."""
    global _classification_db
    if _classification_db is None:
        _classification_db = SQLiteDatabase(get_sqlite_db_path("classifications"))
    return _classification_db
