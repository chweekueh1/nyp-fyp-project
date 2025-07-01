#!/usr/bin/env python3
"""
Test utilities for isolated testing without persisting to production database.
"""

import os
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

def create_test_user(username: str, password: str = "TestPass123!", email: str = "") -> bool:
    """Create a test user for testing purposes (uses test database)."""
    try:
        from backend import do_register_test
        import asyncio

        # Use test email if none provided
        if not email:
            email = "test@example.com"

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

def cleanup_test_user(username: str) -> bool:
    """Clean up a specific test user from test database."""
    try:
        from backend import cleanup_test_user as backend_cleanup

        success = backend_cleanup(username)
        if success:
            print(f"✅ Cleaned up test user: {username}")
        else:
            print(f"❌ Failed to clean up test user: {username}")

        return success

    except Exception as e:
        print(f"❌ Error cleaning up test user {username}: {e}")
        return False

def test_login_user(username_or_email: str, password: str):
    """Test login using test database."""
    try:
        from backend import do_login_test
        import asyncio

        result = asyncio.run(do_login_test(username_or_email, password))
        return result

    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return {'code': '500', 'message': str(e)}

def with_test_user(username: str, password: str = "testpass123"):
    """Decorator to create and cleanup a test user for a test function."""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            # Create test user
            if not create_test_user(username, password):
                raise Exception(f"Failed to create test user: {username}")
            
            try:
                # Run the test
                return test_func(*args, **kwargs)
            finally:
                # Clean up test user
                cleanup_test_user(username)
        
        return wrapper
    return decorator

class TestUserContext:
    """Context manager for test users."""
    
    def __init__(self, username: str, password: str = "testpass123"):
        self.username = username
        self.password = password
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
        "server_port": port,        # Use specified port
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
    print(f"🌐 Launching {test_name} test app on {launch_config['server_name']}:{launch_config['server_port']}")
    app.launch(**launch_config)

if __name__ == "__main__":
    print("🧹 Running test user cleanup...")
    success = cleanup_test_users()
    if success:
        print("✅ Test user cleanup completed successfully")
        sys.exit(0)
    else:
        print("❌ Test user cleanup failed")
        sys.exit(1)
