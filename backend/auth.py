#!/usr/bin/env python3
"""
Authentication module for the backend.
Contains user authentication, registration, and password management functions.
"""

import os
import json
import re
import logging
from typing import Dict, Any
from hashing import verify_password, hash_password
from .config import USER_DB_PATH, TEST_USER_DB_PATH, ALLOWED_EMAILS
from .rate_limiting import check_rate_limit
from .utils import sanitize_input
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


def _load_users(db_path: str) -> Dict[str, Any]:
    """Load users from the specified database file."""
    try:
        if os.path.exists(db_path):
            with open(db_path, "r") as f:
                return json.load(f)
        else:
            # Create empty database
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            with open(db_path, "w") as f:
                json.dump({}, f)
            return {}
    except Exception as e:
        logger.error(f"Error loading users from {db_path}: {e}")
        return {}


def _save_users(users: Dict[str, Any], db_path: str) -> bool:
    """Save users to the specified database file."""
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, "w") as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving users to {db_path}: {e}")
        return False


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt (delegated to hashing.py)."""
    return hash_password(password)


def _validate_email(email: str) -> bool:
    """Validate email format and domain."""
    if not email:
        return False

    # Basic email format validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return False

    # Check if domain is allowed
    domain = email.split("@")[1].lower()
    return domain in ALLOWED_EMAILS or email.lower() in ALLOWED_EMAILS


def _validate_username(username: str) -> bool:
    """Validate username format."""
    if not username:
        return False

    # Username should be 3-20 characters, alphanumeric and underscores only
    username_pattern = r"^[a-zA-Z0-9_]{3,20}$"
    return bool(re.match(username_pattern, username))


def _validate_password(password: str) -> bool:
    """Validate password strength."""
    if not password:
        return False

    # Password should be at least 8 characters
    if len(password) < 8:
        return False

    # Password should contain at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)

    return has_letter and has_number


async def do_login(username_or_email: str, password: str) -> Dict[str, str]:
    """Authenticate a user login."""
    try:
        # Check rate limit
        if not await check_rate_limit(username_or_email, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username_or_email = sanitize_input(username_or_email)
        password = sanitize_input(password)

        if not username_or_email or not password:
            return {
                "status": "error",
                "code": "400",
                "message": "Username/email and password are required.",
            }

        # Load users
        users = _load_users(USER_DB_PATH)

        # Find user by username or email
        user = None
        username_key = None

        # Check if username_or_email is a direct username key
        if username_or_email in users:
            user = users[username_or_email]
            username_key = username_or_email
        else:
            # Search by email in user data
            for uname, user_data in users.items():
                if user_data.get("email") == username_or_email:
                    user = user_data
                    username_key = uname
                    break

        if not user:
            return {
                "status": "error",
                "code": "401",
                "message": "Invalid username/email or password.",
            }

        # Verify password
        if not verify_password(password, user.get("password", "")):
            return {
                "status": "error",
                "code": "401",
                "message": "Invalid username/email or password.",
            }

        logger.info(f"User {username_key} logged in successfully")
        return {
            "status": "success",
            "code": "200",
            "message": "Login successful.",
            "username": username_key,
            "email": user.get("email", ""),
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred during login.",
        }


async def do_register(username: str, password: str, email: str = "") -> Dict[str, str]:
    """Register a new user."""
    try:
        # Check rate limit
        if not await check_rate_limit(username, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username = sanitize_input(username)
        password = sanitize_input(password)
        email = sanitize_input(email)

        # Validate inputs
        if not username or not password:
            return {
                "status": "error",
                "code": "400",
                "message": "Username and password are required.",
            }

        if not _validate_username(username):
            return {
                "status": "error",
                "code": "400",
                "message": "Username must be 3-20 characters, alphanumeric and underscores only.",
            }

        if not _validate_password(password):
            return {
                "status": "error",
                "code": "400",
                "message": "Password must be at least 8 characters with letters and numbers.",
            }

        if email and not _validate_email(email):
            return {
                "status": "error",
                "code": "400",
                "message": "Invalid email format or domain not allowed.",
            }

        # Load users
        users = _load_users(USER_DB_PATH)

        # Check if username already exists
        if username in users:
            return {
                "status": "error",
                "message": "Username already exists.",
                "code": "409",
            }

        # Check if email already exists
        if email:
            for user_data in users.values():
                if user_data.get("email") == email:
                    return {
                        "status": "error",
                        "code": "409",
                        "message": "Email already registered.",
                    }

        # Create new user with username as key
        hashed_password = _hash_password(password)

        new_user = {
            "password": hashed_password,
            "email": email,
            "created_at": get_utc_timestamp(),
        }

        users[username] = new_user

        # Save users
        if _save_users(users, USER_DB_PATH):
            logger.info(f"User {username} registered successfully")
            return {
                "status": "success",
                "code": "200",
                "message": "Registration successful.",
                "username": username,
                "email": email,
            }
        else:
            return {
                "status": "error",
                "code": "500",
                "message": "Failed to save user data.",
            }

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred during registration.",
        }


async def change_password(
    username: str, old_password: str, new_password: str
) -> Dict[str, str]:
    """Change user password."""
    try:
        # Check rate limit
        if not await check_rate_limit(username, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username = sanitize_input(username)
        old_password = sanitize_input(old_password)
        new_password = sanitize_input(new_password)

        if not username or not old_password or not new_password:
            return {
                "status": "error",
                "code": "400",
                "message": "All fields are required.",
            }

        if not _validate_password(new_password):
            return {
                "status": "error",
                "code": "400",
                "message": "New password must be at least 8 characters with letters and numbers.",
            }

        # Load users
        users = _load_users(USER_DB_PATH)

        # Find user
        if username not in users:
            return {"status": "error", "code": "404", "message": "User not found."}

        # Verify old password
        if not verify_password(old_password, users[username].get("password", "")):
            return {
                "status": "error",
                "code": "401",
                "message": "Current password is incorrect.",
            }

        # Update password
        users[username]["password"] = _hash_password(new_password)

        # Save users
        if _save_users(users, USER_DB_PATH):
            logger.info(f"Password changed successfully for user {username}")
            return {
                "status": "success",
                "code": "200",
                "message": "Password changed successfully.",
            }
        else:
            return {
                "status": "error",
                "code": "500",
                "message": "Failed to save password change.",
            }

    except Exception as e:
        logger.error(f"Password change error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred while changing password.",
        }


# Test functions for development/testing
async def do_register_test(
    username: str, password: str, email: str = ""
) -> Dict[str, str]:
    """Register a new test user."""
    try:
        # Check rate limit
        if not await check_rate_limit(username, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username = sanitize_input(username)
        password = sanitize_input(password)
        email = sanitize_input(email)

        # Validate inputs
        if not username or not password:
            return {
                "status": "error",
                "code": "400",
                "message": "Username and password are required.",
            }

        if not _validate_username(username):
            return {
                "status": "error",
                "code": "400",
                "message": "Username must be 3-20 characters, alphanumeric and underscores only.",
            }

        if not _validate_password(password):
            return {
                "status": "error",
                "code": "400",
                "message": "Password must be at least 8 characters with letters and numbers.",
            }

        # Load test users
        users = _load_users(TEST_USER_DB_PATH)

        # Check if username already exists
        if username in users:
            return {
                "status": "error",
                "message": "Username already exists.",
                "code": "409",
            }

        # Check if email already exists
        if email:
            for user_data in users.values():
                if user_data.get("email") == email:
                    return {
                        "status": "error",
                        "code": "409",
                        "message": "Email already registered.",
                    }

        # Create new test user with username as key
        hashed_password = _hash_password(password)

        new_user = {
            "password": hashed_password,
            "email": email,
            "created_at": get_utc_timestamp(),
            "is_test_user": True,
        }

        users[username] = new_user

        # Save test users
        if _save_users(users, TEST_USER_DB_PATH):
            logger.info(f"Test user {username} registered successfully")
            return {
                "status": "success",
                "code": "200",
                "message": "Test registration successful.",
                "username": username,
                "email": email,
            }
        else:
            return {
                "status": "error",
                "code": "500",
                "message": "Failed to save test user data.",
            }

    except Exception as e:
        logger.error(f"Test registration error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred during test registration.",
        }


async def do_login_test(username_or_email: str, password: str) -> Dict[str, str]:
    """Authenticate a test user login."""
    try:
        # Check rate limit
        if not await check_rate_limit(username_or_email, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username_or_email = sanitize_input(username_or_email)
        password = sanitize_input(password)

        if not username_or_email or not password:
            return {
                "status": "error",
                "code": "400",
                "message": "Username/email and password are required.",
            }

        # Load test users
        users = _load_users(TEST_USER_DB_PATH)

        # Find test user by username or email
        user = None
        username_key = None

        # Check if username_or_email is a direct username key
        if username_or_email in users and users[username_or_email].get(
            "is_test_user", False
        ):
            user = users[username_or_email]
            username_key = username_or_email
        else:
            # Search by email in user data
            for uname, user_data in users.items():
                if user_data.get("email") == username_or_email and user_data.get(
                    "is_test_user", False
                ):
                    user = user_data
                    username_key = uname
                    break

        if not user:
            return {
                "status": "error",
                "code": "401",
                "message": "Invalid username/email or password.",
            }

        # Verify password
        if not verify_password(password, user.get("password", "")):
            return {
                "status": "error",
                "code": "401",
                "message": "Invalid username/email or password.",
            }

        logger.info(f"Test user {username_key} logged in successfully")
        return {
            "status": "success",
            "code": "200",
            "message": "Test login successful.",
            "username": username_key,
            "email": user.get("email", ""),
        }

    except Exception as e:
        logger.error(f"Test login error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred during test login.",
        }


async def change_password_test(
    username: str, old_password: str, new_password: str
) -> Dict[str, str]:
    """Change test user password."""
    try:
        # Check rate limit
        if not await check_rate_limit(username, "auth"):
            return {
                "status": "error",
                "code": "429",
                "message": "Rate limit exceeded. Please try again later.",
            }

        # Sanitize inputs
        username = sanitize_input(username)
        old_password = sanitize_input(old_password)
        new_password = sanitize_input(new_password)

        if not username or not old_password or not new_password:
            return {
                "status": "error",
                "code": "400",
                "message": "All fields are required.",
            }

        if not _validate_password(new_password):
            return {
                "status": "error",
                "code": "400",
                "message": "New password must be at least 8 characters with letters and numbers.",
            }

        # Load test users
        users = _load_users(TEST_USER_DB_PATH)

        # Find test user
        if username not in users or not users[username].get("is_test_user", False):
            return {"status": "error", "code": "404", "message": "Test user not found."}

        # Verify old password
        if not verify_password(old_password, users[username].get("password", "")):
            return {
                "status": "error",
                "code": "401",
                "message": "Current password is incorrect.",
            }

        # Update password
        users[username]["password"] = _hash_password(new_password)

        # Save test users
        if _save_users(users, TEST_USER_DB_PATH):
            logger.info(f"Password changed successfully for test user {username}")
            return {
                "status": "success",
                "code": "200",
                "message": "Test password changed successfully.",
            }
        else:
            return {
                "status": "error",
                "code": "500",
                "message": "Failed to save test password change.",
            }

    except Exception as e:
        logger.error(f"Test password change error: {e}")
        return {
            "status": "error",
            "code": "500",
            "message": "An error occurred while changing test password.",
        }


def cleanup_test_user(username: str) -> bool:
    """Remove a test user from the test database."""
    try:
        users = _load_users(TEST_USER_DB_PATH)

        # Find and remove test user
        if username in users and users[username].get("is_test_user", False):
            del users[username]
            if _save_users(users, TEST_USER_DB_PATH):
                logger.info(f"Test user {username} cleaned up successfully")
                return True

        return False

    except Exception as e:
        logger.error(f"Error cleaning up test user {username}: {e}")
        return False


def cleanup_all_test_users() -> bool:
    """Remove all test users from the test database."""
    try:
        users = _load_users(TEST_USER_DB_PATH)

        # Remove all test users
        test_usernames = [
            username
            for username, user_data in users.items()
            if user_data.get("is_test_user", False)
        ]

        for username in test_usernames:
            del users[username]

        if _save_users(users, TEST_USER_DB_PATH):
            logger.info(f"Cleaned up {len(test_usernames)} test users")
            return True

        return False

    except Exception as e:
        logger.error(f"Error cleaning up all test users: {e}")
        return False


def delete_test_user(username: str) -> bool:
    """Delete a test user (alias for cleanup_test_user)."""
    return cleanup_test_user(username)
