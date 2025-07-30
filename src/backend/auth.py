"""
Authentication and user management for the NYP FYP CNC Chatbot.

Handles login, registration, password changes, and user cleanup.
All API keys and secrets are loaded from environment variables using dotenv for security.
"""

from dotenv import load_dotenv

load_dotenv()

import re
import logging
from typing import Dict, Any
from hashing import verify_password, hash_password
from .config import ALLOWED_EMAILS
from .rate_limiting import check_rate_limit
from .consolidated_database import get_consolidated_database  # Updated import
from .chat import delete_chat_history_for_user  # Import for user cleanup

logger = logging.getLogger(__name__)


def _validate_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@")[1].lower()
    return domain in ALLOWED_EMAILS


def _validate_username(username: str) -> bool:
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", username))


def _validate_password(password: str) -> bool:
    if not password or len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    return bool(re.search(r"\d", password))


async def do_login(username: str, password: str) -> Dict[str, Any]:
    try:
        rate_limit_key = f"login:{username}"
        if not check_rate_limit("auth", rate_limit_key):
            logger.warning(f"Rate limit exceeded for login attempt: {username}")
            return {
                "success": False,
                "message": "Too many login attempts. Please try again later.",
            }

        db = get_consolidated_database()  # Use consolidated database
        user = db.get_user_by_username(username)

        if not user:
            db.record_login_failure(
                username
            )  # Record failure even for non-existent users to prevent enumeration
            logger.warning(f"Login failed: User '{username}' not found.")
            return {"success": False, "message": "Invalid username or password."}

        if not user["is_active"]:
            logger.warning(f"Login failed: User '{username}' is inactive.")
            return {"success": False, "message": "Account is inactive."}

        # Check for brute-force prevention (e.g., after 5 failed attempts, lock for 15 mins)
        login_failures = user.get("login_failures", 0)
        if login_failures >= 5:  # Example threshold
            # Implement a lockout time if desired
            logger.warning(
                f"Login failed: User '{username}' locked out due to too many failed attempts."
            )
            return {
                "success": False,
                "message": "Account temporarily locked due to too many failed attempts.",
            }

        if verify_password(password, user["hashed_password"]):
            db.update_user_last_login(username)
            db.reset_login_failures(username)
            logger.info(f"User '{username}' logged in successfully.")
            db.record_user_activity(
                username, "login_success", f"User {username} logged in."
            )
            return {
                "success": True,
                "message": "Login successful.",
                "username": username,
            }
        else:
            db.record_login_failure(username)
            logger.warning(f"Login failed: Invalid password for user '{username}'.")
            return {"success": False, "message": "Invalid username or password."}
    except Exception as e:
        logger.error(f"Login error for '{username}': {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}


async def do_register(username: str, password: str, email: str) -> Dict[str, Any]:
    try:
        rate_limit_key = f"register:{username}"
        if not check_rate_limit("auth", rate_limit_key):
            logger.warning(f"Rate limit exceeded for registration attempt: {username}")
            return {
                "success": False,
                "message": "Too many registration attempts. Please try again later.",
            }

        if not _validate_username(username):
            return {
                "success": False,
                "message": "Invalid username format. Must be 3-50 alphanumeric characters, underscores, or hyphens.",
            }
        if not _validate_password(password):
            return {
                "success": False,
                "message": "Invalid password format. Must be at least 8 characters, with uppercase, lowercase, and a digit.",
            }
        if not _validate_email(email):
            return {
                "success": False,
                "message": f"Invalid email format or domain not allowed. Allowed domains: {', '.join(ALLOWED_EMAILS)}",
            }

        db = get_consolidated_database()  # Use consolidated database
        hashed_password = hash_password(password)

        user_id = db.add_user(username, hashed_password, email)
        if user_id:
            logger.info(f"User '{username}' registered successfully with ID: {user_id}")
            db.record_user_activity(
                username, "registration_success", f"User {username} registered."
            )
            return {"success": True, "message": "Registration successful."}
        else:
            return {"success": False, "message": "Registration successful"}
    except Exception as e:
        logger.error(f"Registration error for '{username}': {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}


async def change_password(
    username: str, old_password: str, new_password: str
) -> Dict[str, Any]:
    try:
        db = get_consolidated_database()  # Use consolidated database
        user = db.get_user_by_username(username)

        if not user:
            logger.warning(f"Password change failed: User '{username}' not found.")
            return {"success": False, "message": "User not found."}

        if not verify_password(old_password, user["hashed_password"]):
            logger.warning(
                f"Password change failed: Invalid old password for '{username}'."
            )
            return {"success": False, "message": "Invalid old password."}

        if not _validate_password(new_password):
            return {
                "success": False,
                "message": "Invalid new password format. Must be at least 8 characters, with uppercase, lowercase, and a digit.",
            }

        new_hashed_password = hash_password(new_password)
        if db.update_user_password(username, new_hashed_password):
            logger.info(f"Password for '{username}' changed successfully.")
            db.record_user_activity(
                username,
                "password_change_success",
                f"User {username} changed password.",
            )
            return {"success": True, "message": "Password changed successfully."}
        else:
            logger.error(
                f"Password change failed: Database update issue for '{username}'."
            )
            return {"success": False, "message": "Failed to update password."}
    except Exception as e:
        logger.error(f"Change password error for '{username}': {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}


# --- Test User Functions (for CI/CD and local development) ---


async def do_login_test(username: str) -> Dict[str, Any]:
    """Logs in a test user without password, for testing purposes."""
    db = get_consolidated_database()  # Use consolidated database
    user = db.get_user_by_username(username)
    if user and user["is_test_user"]:
        db.update_user_last_login(username)
        db.reset_login_failures(username)
        logger.info(f"Test user '{username}' logged in successfully.")
        db.record_user_activity(
            username, "test_login_success", f"Test user {username} logged in."
        )
        return {
            "success": True,
            "message": "Test login successful.",
            "username": username,
        }
    else:
        logger.warning(
            f"Test login failed: Test user '{username}' not found or not marked as test user."
        )
        return {
            "success": False,
            "message": "Test user not found or not enabled for test login.",
        }


async def do_register_test(username: str, email: str = None) -> Dict[str, Any]:
    """Registers a test user without password, for testing purposes."""
    if not _validate_username(username):
        return {"success": False, "message": "Invalid username format."}

    db = get_consolidated_database()  # Use consolidated database
    # For test users, a dummy password can be used, or a flag is_test_user is set.
    # Using a placeholder password + is_test_user = 1
    hashed_password = hash_password("test_password_123!@#")
    test_email = email if email else f"{username}@test.com"

    user_id = db.add_user(username, hashed_password, test_email, is_test_user=1)
    if user_id:
        logger.info(f"Test user '{username}' registered successfully.")
        db.record_user_activity(
            username, "test_registration_success", f"Test user {username} registered."
        )
        return {"success": True, "message": "Test registration successful."}
    else:
        logger.warning(f"Test registration failed: User '{username}' already exists.")
        return {"success": False, "message": "Test user already exists."}


async def change_password_test(username: str, new_password: str) -> Dict[str, Any]:
    """Changes password for a test user."""
    db = get_consolidated_database()  # Use consolidated database
    user = db.get_user_by_username(username)

    if not user or not user["is_test_user"]:
        logger.warning(
            f"Test password change failed: Test user '{username}' not found or not a test user."
        )
        return {
            "success": False,
            "message": "Test user not found or not enabled for test password change.",
        }

    if not _validate_password(new_password):
        return {"success": False, "message": "Invalid new password format."}

    new_hashed_password = hash_password(new_password)
    if db.update_user_password(username, new_hashed_password):
        logger.info(f"Password for test user '{username}' changed successfully.")
        db.record_user_activity(
            username,
            "test_password_change_success",
            f"Test user {username} changed password.",
        )
        return {"success": True, "message": "Test password changed successfully."}
    else:
        logger.error(
            f"Test password change failed: Database update issue for test user '{username}'."
        )
        return {"success": False, "message": "Failed to update test user password."}


async def cleanup_test_user(username: str) -> Dict[str, Any]:
    """
    Clean up a specific test user's data from the database.
    This deletes the user record and associated chat sessions and messages.
    """
    try:
        db = get_consolidated_database()  # Use consolidated database
        user = db.get_user_by_username(username)

        if not user or not user["is_test_user"]:
            return {
                "success": False,
                "message": f"User '{username}' not found or not marked as a test user.",
            }

        # Delete chat sessions and messages for the test user
        await delete_chat_history_for_user(username)

        # Delete the user from the database
        deleted_count = db.delete_user(username)
        if deleted_count > 0:
            logger.info(f"Cleaned up test user '{username}' and associated data.")
            return {
                "success": True,
                "message": f"Successfully cleaned up test user '{username}'.",
            }
        else:
            logger.warning(
                f"Test user '{username}' not found during cleanup, or not a test user."
            )
            return {
                "success": False,
                "message": f"Test user '{username}' not found or not marked as a test user.",
            }

    except Exception as e:
        logger.error(f"Test user cleanup error for {username}: {e}")
        return {
            "success": False,
            "message": "An error occurred while cleaning up test user.",
        }


async def cleanup_all_test_users() -> Dict[str, Any]:
    """
    Clean up all test users.
    """
    try:
        db = get_consolidated_database()  # Use consolidated database

        # Get all test users
        # Fetching full rows because `delete_user` method might need username
        query = "SELECT username FROM users WHERE is_test_user = 1"
        test_users_rows = db.execute_query(query)

        if not test_users_rows:
            return {"success": True, "message": "No test users found to clean up."}

        deleted_count = 0
        for row in test_users_rows:
            username = row["username"]
            # Delete chat sessions and messages for each test user first
            await delete_chat_history_for_user(username)
            # Then delete the user
            if db.delete_user(username) > 0:
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
