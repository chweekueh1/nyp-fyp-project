#!/usr/bin/env python3
"""
Test utilities for isolated testing without persisting to production database.
"""

import sys
from pathlib import Path
from typing import Optional, Any

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def cleanup_test_users() -> bool:
    """
    Clean up all test users from the test database (not production).

    :return: True if cleanup succeeded, False otherwise.
    :rtype: bool
    """
    try:
        from backend import cleanup_all_test_users

        success = cleanup_all_test_users()
        if success:
            print("✅ Test database cleaned up successfully")
        else:
            print("❌ Failed to clean up test database")
        return success
    except Exception as e:
        print(f"❌ Error during test user cleanup: {e}")
        import traceback

        traceback.print_exc()
        return False


# Default test user configuration
DEFAULT_TEST_USERNAME = "test_user"
DEFAULT_TEST_PASSWORD = "TestPass123!"
DEFAULT_TEST_EMAIL = "test@example.com"


def create_test_user(
    username: Optional[str] = None,
    password: Optional[str] = None,
    email: Optional[str] = None,
) -> bool:
    """
    Create a test user for testing purposes (uses test database).

    :param username: Username for the test user. Defaults to DEFAULT_TEST_USERNAME.
    :type username: Optional[str]
    :param password: Password for the test user. Defaults to DEFAULT_TEST_PASSWORD.
    :type password: Optional[str]
    :param email: Email for the test user. Defaults to DEFAULT_TEST_EMAIL.
    :type email: Optional[str]
    :return: True if user was created or already exists, False otherwise.
    :rtype: bool
    """
    try:
        from backend import do_register_test
        import asyncio

        # Use defaults if not provided
        username = username or DEFAULT_TEST_USERNAME
        password = password or DEFAULT_TEST_PASSWORD
        email = email or DEFAULT_TEST_EMAIL
        result = asyncio.run(do_register_test(username, password, email))
        if result.get("code") == "200":
            print(f"✅ Created test user: {username}")
            return True
        elif result.get("code") == "409":
            print(f"ℹ️ Test user already exists: {username}")
            return True
        else:
            print(f"❌ Failed to create test user {username}: {result}")
            return False
    except Exception as e:
        print(f"❌ Error creating test user {username}: {e}")
        return False


def cleanup_test_user(username: Optional[str] = None) -> bool:
    """
    Clean up a specific test user from test database.

    :param username: Username to clean up. Defaults to DEFAULT_TEST_USERNAME.
    :type username: Optional[str]
    :return: True if user was cleaned up or did not exist, False otherwise.
    :rtype: bool
    """
    try:
        from backend import cleanup_test_user as backend_cleanup

        username = username or DEFAULT_TEST_USERNAME
        success = backend_cleanup(username)
        if success:
            print(f"✅ Cleaned up test user: {username}")
        else:
            print(f"❌ Failed to clean up test user: {username}")
        return success
    except Exception as e:
        print(f"❌ Error cleaning up test user {username}: {e}")
        return False


def test_login_user(
    username_or_email: Optional[str] = None, password: Optional[str] = None
) -> dict:
    """
    Test login using test database.

    :param username_or_email: Username or email to login with. Defaults to DEFAULT_TEST_USERNAME.
    :type username_or_email: Optional[str]
    :param password: Password to login with. Defaults to DEFAULT_TEST_PASSWORD.
    :type password: Optional[str]
    :return: Result dictionary from backend login function.
    :rtype: dict
    """
    try:
        from backend import do_login_test
        import asyncio

        username_or_email = username_or_email or DEFAULT_TEST_USERNAME
        password = password or DEFAULT_TEST_PASSWORD
        result = asyncio.run(do_login_test(username_or_email, password))
        return result
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return {"code": "500", "message": str(e)}


def ensure_default_test_user() -> bool:
    """
    Ensure the default test user exists for testing.

    :return: True if user was created or already exists, False otherwise.
    :rtype: bool
    """
    return create_test_user("test_user", "TestPass123!", "test@example.com")


def get_default_test_user() -> dict:
    """
    Get the default test user credentials.

    :return: Dictionary with username, password, and email for the default test user.
    :rtype: dict
    """
    return {
        "username": DEFAULT_TEST_USERNAME,
        "password": DEFAULT_TEST_PASSWORD,
        "email": DEFAULT_TEST_EMAIL,
    }


def with_test_user(username: Optional[str] = None, password: Optional[str] = None):
    """
    Decorator to create and cleanup a test user for a test function.

    :param username: Username for the test user. Defaults to DEFAULT_TEST_USERNAME.
    :type username: Optional[str]
    :param password: Password for the test user. Defaults to DEFAULT_TEST_PASSWORD.
    :type password: Optional[str]
    :return: Decorator function.
    :rtype: function
    """

    def decorator(test_func):
        def wrapper(*args, **kwargs):
            # Use default test user if not specified
            username_to_use = username or DEFAULT_TEST_USERNAME
            password_to_use = password or DEFAULT_TEST_PASSWORD
            # Create test user
            if not create_test_user(username_to_use, password_to_use):
                raise Exception(f"Failed to create test user: {username_to_use}")
            try:
                # Run the test
                return test_func(*args, **kwargs)
            finally:
                # Clean up test user
                cleanup_test_user(username_to_use)

        return wrapper

    return decorator


class TestUserContext:
    """
    Context manager for test users.

    :param username: Username for the test user. Defaults to DEFAULT_TEST_USERNAME.
    :type username: Optional[str]
    :param password: Password for the test user. Defaults to DEFAULT_TEST_PASSWORD.
    :type password: Optional[str]
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or DEFAULT_TEST_USERNAME
        self.password = password or DEFAULT_TEST_PASSWORD
        self.created = False

    def __enter__(self):
        self.created = create_test_user(self.username, self.password)
        if not self.created:
            raise Exception(f"Failed to create test user: {self.username}")
        return self.username

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.created:
            cleanup_test_user(self.username)


def run_with_cleanup() -> Any:
    """
    Run a function and ensure cleanup is performed after execution.

    :return: Any: The result of the function call.
    """
    try:
        result = cleanup_test_users()
    except Exception:
        return Exception("Failed to run with clean up")
    return result


def get_docker_launch_config(debug: bool = True, port: int = 7860) -> dict:
    """
    Get Docker launch configuration for test app.

    :param debug: Whether to enable debug mode.
    :type debug: bool
    :param port: Port to use for the test app.
    :type port: int
    :return: Docker launch configuration dictionary.
    :rtype: dict
    """
    return {
        "debug": debug,
        "share": False,
        "inbrowser": False,
        "quiet": False,
        "show_error": True,
        "server_name": "0.0.0.0",  # Listen on all interfaces for Docker
        "server_port": port,  # Use specified port
    }


def launch_test_app_with_docker_config(
    app: object, test_name: str, port: int = 7860
) -> None:
    """
    Launch the test app with Docker configuration.

    :param app: The app object to launch.
    :type app: object
    :param test_name: Name of the test.
    :type test_name: str
    :param port: Port to use for the test app.
    :type port: int
    """
    launch_config = get_docker_launch_config(debug=True, port=port)
    print(
        f"🌐 Launching {test_name} test app on {launch_config['server_name']}:{launch_config['server_port']}"
    )
    app.launch(**launch_config)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test utilities for NYP FYP Chatbot")
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up all test users"
    )
    parser.add_argument(
        "--create-default", action="store_true", help="Create default test user"
    )
    parser.add_argument(
        "--ensure-default", action="store_true", help="Ensure default test user exists"
    )

    args = parser.parse_args()

    if args.cleanup:
        print("🧹 Running test user cleanup...")
        success = cleanup_test_users()
        if success:
            print("✅ Test user cleanup completed successfully")
            sys.exit(0)
        else:
            print("❌ Test user cleanup failed")
            sys.exit(1)

    elif args.create_default:
        print(f"👤 Creating default test user: {DEFAULT_TEST_USERNAME}")
        success = create_test_user()
        if success:
            print("✅ Default test user created successfully")
            sys.exit(0)
        else:
            print("❌ Failed to create default test user")
            sys.exit(1)

    elif args.ensure_default:
        print(f"🔍 Ensuring default test user exists: {DEFAULT_TEST_USERNAME}")
        success = ensure_default_test_user()
        if success:
            print("✅ Default test user is ready for testing")
            sys.exit(0)
        else:
            print("❌ Failed to ensure default test user")
            sys.exit(1)

    else:
        print("Usage:")
        print("  python test_utils.py --cleanup        # Clean up all test users")
        print("  python test_utils.py --create-default # Create default test user")
        print(
            "  python test_utils.py --ensure-default # Ensure default test user exists"
        )
        sys.exit(1)
