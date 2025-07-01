#!/usr/bin/env python3
"""
Test utilities for isolated testing without persisting to production database.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def cleanup_test_users():
    """Clean up all test users from the test database (not production)."""
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
    username: str = None, password: str = None, email: str = None
) -> bool:
    """Create a test user for testing purposes (uses test database)."""
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


def cleanup_test_user(username: str = None) -> bool:
    """Clean up a specific test user from test database."""
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


def test_login_user(username_or_email: str = None, password: str = None):
    """Test login using test database."""
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


def ensure_default_test_user():
    """Ensure the default test user exists for testing."""
    return create_test_user()


def get_default_test_user():
    """Get the default test user credentials."""
    return {
        "username": DEFAULT_TEST_USERNAME,
        "password": DEFAULT_TEST_PASSWORD,
        "email": DEFAULT_TEST_EMAIL,
    }


def with_test_user(username: str = None, password: str = None):
    """Decorator to create and cleanup a test user for a test function."""

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
    """Context manager for test users."""

    def __init__(self, username: str = None, password: str = None):
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


def run_with_cleanup(test_func, *args, **kwargs):
    """Run a test function and ensure cleanup happens."""
    try:
        return test_func(*args, **kwargs)
    finally:
        cleanup_test_users()


def get_docker_launch_config(debug=True, port=7860):
    """
    Get Docker-compatible launch configuration for Gradio apps.

    Args:
        debug (bool): Whether to run in debug mode
        port (int): Port to run on (default 7860)

    Returns:
        dict: Launch configuration dictionary
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


def launch_test_app_with_docker_config(app, test_name, port=7860):
    """
    Launch a test app with Docker-compatible configuration.

    Args:
        app: Gradio app to launch
        test_name (str): Name of the test for logging
        port (int): Port to run on (default 7860)
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
