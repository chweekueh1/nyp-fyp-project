#!/usr/bin/env python3
"""Authentication module for the NYP FYP CNC Chatbot backend.

This module provides comprehensive user authentication and management functionality
including:

- User registration and login
- Password hashing and verification
- Email validation and domain restrictions
- Rate limiting for security
- Test user management for development
- Password change functionality

The module supports both production and test environments with separate
database paths and validation rules.
"""

import os
import json
import re
import logging
from typing import Dict, Any  # noqa: F401
from hashing import verify_password, hash_password
from .config import USER_DB_PATH, TEST_USER_DB_PATH, ALLOWED_EMAILS
from .rate_limiting import check_rate_limit
from .utils import sanitize_input
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


def _load_users(db_path: str) -> Dict[str, Any]:
    """
    Load users from the specified database file.

    :param db_path: Path to the JSON database file containing user data.
    :type db_path: str
    :return: Dictionary containing user data. Returns empty dict if file doesn't exist
             or on error.
    :rtype: Dict[str, Any]
    """
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
    """
    Save users to the specified database file.

    :param users: Dictionary containing user data to save.
    :type users: Dict[str, Any]
    :param db_path: Path to the JSON database file.
    :type db_path: str
    :return: True if save was successful, False otherwise.
    :rtype: bool
    """
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, "w") as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving users to {db_path}: {e}")
        return False


def _hash_password(password: str) -> str:
    """
    Hash a password using bcrypt (delegated to hashing.py).

    :param password: Plain text password to hash.
    :type password: str
    :return: Hashed password string.
    :rtype: str
    """
    return hash_password(password)


def _validate_email(email: str) -> bool:
    """
    Validate email format and domain.

    :param email: Email address to validate.
    :type email: str
    :return: True if email is valid and domain is allowed, False otherwise.
    :rtype: bool
    """
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
    """
    Validate username format.

    :param username: Username to validate.
    :type username: str
    :return: True if username meets requirements, False otherwise.
    :rtype: bool
    """
    if not username:
        return False

    # Username should be 3-20 characters, alphanumeric and underscores only
    username_pattern = r"^[a-zA-Z0-9_]{3,20}$"
    return bool(re.match(username_pattern, username))


def _validate_password(password: str) -> bool:
    """
    Validate password strength.

    :param password: Password to validate.
    :type password: str
    :return: True if password meets strength requirements, False otherwise.
    :rtype: bool
    """
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
    """
    Authenticate a user login.

    :param username_or_email: Username or email address for login.
    :type username_or_email: str
    :param password: User's password.
    :type password: str
    :return: Dictionary containing login result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Register a new user.

    :param username: Username for the new account.
    :type username: str
    :param password: Password for the new account.
    :type password: str
    :param email: Optional email address for the account.
    :type email: str
    :return: Dictionary containing registration result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Change user password.

    :param username: Username of the account.
    :type username: str
    :param old_password: Current password for verification.
    :type old_password: str
    :param new_password: New password to set.
    :type new_password: str
    :return: Dictionary containing password change result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Register a new test user.

    :param username: Username for the new test account.
    :type username: str
    :param password: Password for the new test account.
    :type password: str
    :param email: Optional email address for the test account.
    :type email: str
    :return: Dictionary containing test registration result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Authenticate a test user login.

    :param username_or_email: Username or email address for test login.
    :type username_or_email: str
    :param password: Test user's password.
    :type password: str
    :return: Dictionary containing test login result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Change test user password.

    :param username: Username of the test account.
    :type username: str
    :param old_password: Current password for verification.
    :type old_password: str
    :param new_password: New password to set.
    :type new_password: str
    :return: Dictionary containing test password change result with status, code, and message.
    :rtype: Dict[str, str]
    """
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
    """
    Remove a test user from the test database.

    :param username: Username of the test user to remove.
    :type username: str
    :return: True if test user was successfully removed, False otherwise.
    :rtype: bool
    """
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
    """
    Remove all test users from the test database.

    :return: True if all test users were successfully removed, False otherwise.
    :rtype: bool
    """
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
    """
    Delete a test user (alias for cleanup_test_user).

    :param username: Username of the test user to delete.
    :type username: str
    :return: True if test user was successfully deleted, False otherwise.
    :rtype: bool
    """
    return cleanup_test_user(username)
