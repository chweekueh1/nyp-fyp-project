"""
Authentication and user management for the NYP FYP CNC Chatbot.

Handles login, registration, password changes, and user cleanup.
All API keys and secrets are loaded from environment variables using dotenv for security.
"""

from dotenv import load_dotenv

load_dotenv()

import re
import logging
from typing import Dict, Any  # noqa: F401
from hashing import verify_password, hash_password
from .config import ALLOWED_EMAILS
from .rate_limiting import check_rate_limit
from .timezone_utils import get_utc_timestamp
from .consolidated_database import get_user_database, InputSanitizer

# Set up logging
logger = logging.getLogger(__name__)


def _validate_email(email: str) -> bool:
    """
    Validate email format and domain.

    :param email: Email address to validate.
    :type email: str
    :return: True if valid, False otherwise.
    :rtype: bool
    """
    if not email or "@" not in email:
        return False

    # Check if email domain is in allowed list
    domain = email.split("@")[1].lower()
    return domain in ALLOWED_EMAILS


def _validate_username(username: str) -> bool:
    """
    Validate username format.

    :param username: Username to validate.
    :type username: str
    :return: True if valid, False otherwise.
    :rtype: bool
    """
    if not username or len(username) < 3 or len(username) > 50:
        return False

    # Allow alphanumeric characters, hyphens, and underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False

    return True


def _validate_password(password: str) -> bool:
    """
    Validate password strength.

    :param password: Password to validate.
    :type password: str
    :return: True if valid, False otherwise.
    :rtype: bool
    """
    if not password or len(password) < 8:
        return False

    # Check for at least one uppercase, one lowercase, and one digit
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False

    return True


async def do_login(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user login.

    :param username: Username for login.
    :type username: str
    :param password: Password for login.
    :type password: str
    :return: Dictionary containing login result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)
            password = InputSanitizer.sanitize_string(password, max_length=100)
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        if not username or not password:
            return {"success": False, "message": "Username and password are required."}

        # Get user from consolidated SQLite database
        db = get_user_database()
        user = db.get_user(username)

        if not user:
            return {"success": False, "message": "Invalid username or password."}

        if not user["is_active"]:
            return {"success": False, "message": "Account is deactivated."}

        # Verify password
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Invalid username or password."}

        # Update login statistics
        timestamp = get_utc_timestamp()
        db.update_user(
            username, last_login=timestamp, login_count=user.get("login_count", 0) + 1
        )

        logger.info(f"Successful login for user: {username}")
        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "username": user["username"],
                "email": user["email"],
                "is_test_user": user["is_test_user"],
                "last_login": user.get("last_login"),
                "login_count": user.get("login_count", 0),
            },
        }

    except Exception as e:
        logger.error(f"Login error for user {username}: {e}")
        return {"success": False, "message": "An error occurred during login."}


async def do_register(username: str, email: str, password: str) -> Dict[str, Any]:
    """
    Register a new user.

    :param username: Username for registration.
    :type username: str
    :param email: Email for registration.
    :type email: str
    :param password: Password for registration.
    :type password: str
    :return: Dictionary containing registration result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)
            email = InputSanitizer.sanitize_email(email)
            password = InputSanitizer.sanitize_string(password, max_length=100)
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        # Validate inputs
        if not username or not email or not password:
            return {"success": False, "message": "All fields are required."}

        if not _validate_username(username):
            return {
                "success": False,
                "message": "Username must be 3-50 characters long and contain only letters, numbers, hyphens, and underscores.",
            }

        if not _validate_email(email):
            return {
                "success": False,
                "message": "Invalid email address or domain not allowed.",
            }

        if not _validate_password(password):
            return {
                "success": False,
                "message": "Password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters.",
            }

        # Check if user already exists
        db = get_user_database()
        existing_user = db.get_user(username)
        if existing_user:
            return {"success": False, "message": "Username already exists."}

        # Hash password and create user
        password_hash = hash_password(password)
        if db.create_user(username, email, password_hash):
            logger.info(f"New user registered: {username}")
            return {"success": True, "message": "Registration successful."}
        else:
            return {"success": False, "message": "Failed to create user account."}

    except Exception as e:
        logger.error(f"Registration error for user {username}: {e}")
        return {"success": False, "message": "An error occurred during registration."}


async def change_password(
    username: str, current_pw_input: str, user_new_password_input: str
) -> Dict[str, Any]:
    """
    Change user password.

    :param username: Username.
    :type username: str
    :param current_pw_input: Current password.
    :type current_pw_input: str
    :param user_new_password_input: New password.
    :type user_new_password_input: str
    :return: Dictionary containing password change result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)
            current_pw_input = InputSanitizer.sanitize_string(
                current_pw_input,
                max_length=100,  # gitleaks:allow
            )
            user_new_password_input = InputSanitizer.sanitize_string(
                user_new_password_input, max_length=100
            )
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        if not username or not current_pw_input or not user_new_password_input:
            return {"success": False, "message": "All fields are required."}

        if not _validate_password(user_new_password_input):
            return {
                "success": False,
                "message": "New password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters.",
            }

        # Get user and verify current password
        db = get_user_database()
        user = db.get_user(username)

        if not user:
            return {"success": False, "message": "User not found."}

        # gitleaks:allow
        if not verify_password(current_pw_input, user["password_hash"]):
            return {"success": False, "message": "Authentication failed."}

        # Hash new password and update
        new_password_hash = hash_password(user_new_password_input)
        if db.update_user(username, password_hash=new_password_hash):
            logger.info(f"Password changed for user: {username}")
            return {"success": True, "message": "Password changed successfully."}
        else:
            return {"success": False, "message": "Failed to update password."}

    except Exception as e:
        logger.error(f"Password change error for user {username}: {e}")
        return {
            "success": False,
            "message": "An error occurred while changing password.",
        }


# Test user management functions
async def do_login_test(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a test user login.

    :param username: Username for login.
    :type username: str
    :param password: Password for login.
    :type password: str
    :return: Dictionary containing login result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)
            password = InputSanitizer.sanitize_string(password, max_length=100)
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        if not username or not password:
            return {"success": False, "message": "Username and password are required."}

        # Get user from consolidated SQLite database
        db = get_user_database()
        user = db.get_user(username)

        if not user:
            return {"success": False, "message": "Invalid username or password."}

        if not user["is_test_user"]:
            return {"success": False, "message": "This account is not a test account."}

        if not user["is_active"]:
            return {"success": False, "message": "Account is deactivated."}

        # Verify password
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Invalid username or password."}

        # Update login statistics
        timestamp = get_utc_timestamp()
        db.update_user(
            username, last_login=timestamp, login_count=user.get("login_count", 0) + 1
        )

        logger.info(f"Successful test login for user: {username}")
        return {
            "success": True,
            "message": "Test login successful.",
            "user": {
                "username": user["username"],
                "email": user["email"],
                "is_test_user": user["is_test_user"],
                "last_login": user.get("last_login"),
                "login_count": user.get("login_count", 0),
            },
        }

    except Exception as e:
        logger.error(f"Test login error for user {username}: {e}")
        return {"success": False, "message": "An error occurred during test login."}


async def do_register_test(username: str, email: str, password: str) -> Dict[str, Any]:
    """
    Register a new test user.

    :param username: Username for registration.
    :type username: str
    :param email: Email for registration.
    :type email: str
    :param password: Password for registration.
    :type password: str
    :return: Dictionary containing registration result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)
            email = InputSanitizer.sanitize_email(email)
            password = InputSanitizer.sanitize_string(password, max_length=100)
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        # Validate inputs
        if not username or not email or not password:
            return {"success": False, "message": "All fields are required."}

        if not _validate_username(username):
            return {
                "success": False,
                "message": "Username must be 3-50 characters long and contain only letters, numbers, hyphens, and underscores.",
            }

        if not _validate_email(email):
            return {
                "success": False,
                "message": "Invalid email address or domain not allowed.",
            }

        if not _validate_password(password):
            return {
                "success": False,
                "message": "Password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters.",
            }

        # Check if user already exists
        db = get_user_database()
        existing_user = db.get_user(username)
        if existing_user:
            return {"success": False, "message": "Username already exists."}

        # Hash password and create test user
        password_hash = hash_password(password)
        if db.create_user(username, email, password_hash, is_test_user=True):
            logger.info(f"New test user registered: {username}")
            return {"success": True, "message": "Test registration successful."}
        else:
            return {"success": False, "message": "Failed to create test user account."}

    except Exception as e:
        logger.error(f"Test registration error for user {username}: {e}")
        return {
            "success": False,
            "message": "An error occurred during test registration.",
        }


async def change_password_test(
    username: str, current_pw_input: str, user_new_password_input: str
) -> Dict[str, Any]:
    """
    Change test user password.

    :param username: Username.
    :type username: str
    :param current_pw_input: Current password.
    :type current_pw_input: str
    :param user_new_password_input: New password.
    :type user_new_password_input: str
    :return: Dictionary containing password change result.
    :rtype: Dict[str, Any]
    """
    try:
        # Rate limiting check
        rate_limit_result = check_rate_limit("auth", username)
        if not rate_limit_result["allowed"]:
            return {
                "success": False,
                "message": f"Rate limit exceeded. Try again in {rate_limit_result['retry_after']} seconds.",
            }

        # Sanitize inputs using InputSanitizer
        try:
            username = InputSanitizer.sanitize_username(username)  # gitleaks:allow
            current_pw_input = InputSanitizer.sanitize_string(
                current_pw_input, max_length=100
            )
            user_new_password_input = InputSanitizer.sanitize_string(
                user_new_password_input, max_length=100
            )
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}

        if not username or not current_pw_input or not user_new_password_input:
            return {"success": False, "message": "All fields are required."}

        if not _validate_password(user_new_password_input):
            return {
                "success": False,
                "message": "New password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters.",
            }

        # Get user and verify current password
        db = get_user_database()
        user = db.get_user(username)

        if not user:
            return {"success": False, "message": "User not found."}

        if not user["is_test_user"]:
            return {"success": False, "message": "This account is not a test account."}

        # gitleaks:allow
        if not verify_password(current_pw_input, user["password_hash"]):
            return {"success": False, "message": "Authentication failed."}

        # Hash new password and update
        new_password_hash = hash_password(user_new_password_input)
        if db.update_user(username, password_hash=new_password_hash):
            logger.info(f"Password changed for test user: {username}")
            return {"success": True, "message": "Test password changed successfully."}
        else:
            return {"success": False, "message": "Failed to update test password."}

    except Exception as e:
        logger.error(f"Test password change error for user {username}: {e}")
        return {
            "success": False,
            "message": "An error occurred while changing test password.",
        }


async def cleanup_test_user(username: str) -> Dict[str, Any]:
    """
    Clean up a test user.

    :param username: Username to clean up.
    :type username: str
    :return: Dictionary containing cleanup result.
    :rtype: Dict[str, Any]
    """
    try:
        # Sanitize username
        try:
            username = InputSanitizer.sanitize_username(username)
        except ValueError as e:
            return {"success": False, "message": f"Invalid username: {e}"}

        db = get_user_database()
        user = db.get_user(username)

        if not user:
            return {"success": False, "message": "Test user not found."}

        if not user["is_test_user"]:
            return {"success": False, "message": "This account is not a test account."}

        if db.delete_user(username):
            logger.info(f"Test user cleaned up: {username}")
            return {
                "success": True,
                "message": f"Test user '{username}' cleaned up successfully.",
            }
        else:
            return {"success": False, "message": "Failed to clean up test user."}

    except Exception as e:
        logger.error(f"Test user cleanup error for {username}: {e}")
        return {
            "success": False,
            "message": "An error occurred while cleaning up test user.",
        }


async def cleanup_all_test_users() -> Dict[str, Any]:
    """
    Clean up all test users.

    :return: Dictionary containing cleanup result.
    :rtype: Dict[str, Any]
    """
    try:
        db = get_user_database()

        # Get all test users
        query = "SELECT username FROM users WHERE is_test_user = 1"
        test_users = db.execute_query(query)

        if not test_users:
            return {"success": True, "message": "No test users found to clean up."}

        # Delete all test users
        deleted_count = 0
        for (username,) in test_users:
            if db.delete_user(username):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} test users")
        return {
            "success": True,
            "message": f"Successfully cleaned up {deleted_count} test users.",
        }

    except Exception as e:
        logger.error(f"Test users cleanup error: {e}")
        return {
            "success": False,
            "message": "An error occurred while cleaning up test users.",
        }


async def delete_test_user(username: str) -> Dict[str, Any]:
    """
    Delete a test user (alias for cleanup_test_user).

    :param username: Username to delete.
    :type username: str
    :return: Dictionary containing deletion result.
    :rtype: Dict[str, Any]
    """
    return await cleanup_test_user(username)
