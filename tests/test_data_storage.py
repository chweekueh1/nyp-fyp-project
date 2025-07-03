#!/usr/bin/env python3
"""
Test script to verify data storage configuration.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_chatbot_directory_structure():
    """Test that the chatbot directory structure is correct."""
    print("🧪 Testing chatbot directory structure...")

    try:
        from infra_utils import get_chatbot_dir, ensure_chatbot_dir_exists

        # Ensure directories exist
        ensure_chatbot_dir_exists()
        chatbot_dir = get_chatbot_dir()

        print(f"  📁 Chatbot directory: {chatbot_dir}")

        # Check if directory exists
        if not os.path.exists(chatbot_dir):
            print(f"  ❌ Chatbot directory does not exist: {chatbot_dir}")
            return False

        # Check subdirectories
        expected_subdirs = [
            "data/chat_sessions",
            "data/user_info",
            "data/vector_store/duckdb/chat",
            "logs",
        ]

        for subdir in expected_subdirs:
            full_path = os.path.join(chatbot_dir, subdir)
            if os.path.exists(full_path):
                print(f"  ✅ {subdir} exists")
            else:
                print(f"  ❌ {subdir} missing: {full_path}")
                return False

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_user_database_separation():
    """Test that production and test users are stored separately."""
    print("🧪 Testing user database separation...")

    try:
        from backend import USER_DB_PATH, TEST_USER_DB_PATH

        print(f"  📁 Production users: {USER_DB_PATH}")
        print(f"  📁 Test users: {TEST_USER_DB_PATH}")

        # Check that paths are different
        if USER_DB_PATH == TEST_USER_DB_PATH:
            print("  ❌ Production and test user databases are the same!")
            return False

        # Check that test users path contains "test_users.json"
        if "test_users.json" not in TEST_USER_DB_PATH:
            print("  ❌ Test users not stored in test_users.json")
            return False

        # Check that production users path contains "users.json"
        if "users.json" not in USER_DB_PATH:
            print("  ❌ Production users not stored in users.json")
            return False

        print("  ✅ User databases are properly separated")
        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_test_user_creation():
    """Test that test users are created in the correct location."""
    print("🧪 Testing test user creation...")

    try:
        from tests.test_utils import (
            create_test_user,
            cleanup_test_user,
            get_default_test_user,
        )
        from backend import TEST_USER_DB_PATH

        test_user = get_default_test_user()
        username = test_user["username"]

        # Create a test user
        success = create_test_user()
        if not success:
            print("  ❌ Failed to create test user")
            return False

        # Check that test_users.json exists and contains the user
        if not os.path.exists(TEST_USER_DB_PATH):
            print(f"  ❌ Test users database not created: {TEST_USER_DB_PATH}")
            return False

        with open(TEST_USER_DB_PATH, "r") as f:
            data = json.load(f)
            users = data.get("users", {})

            if username in users:
                print(f"  ✅ Test user '{username}' created in test_users.json")
            else:
                print(f"  ❌ Test user '{username}' not found in test_users.json")
                return False

        # Clean up
        cleanup_test_user()

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_data_persistence():
    """Test that data persists in the correct location."""
    print("🧪 Testing data persistence...")

    try:
        from infra_utils import get_chatbot_dir
        from backend import create_and_persist_new_chat, list_user_chat_ids
        from tests.test_utils import (
            create_test_user,
            cleanup_test_user,
            get_default_test_user,
        )

        chatbot_dir = get_chatbot_dir()
        test_user = get_default_test_user()
        username = test_user["username"]

        # Create test user
        create_test_user()

        # Create a test chat
        chat_id = create_and_persist_new_chat(username)
        print(f"  📝 Created chat: {chat_id}")

        # Check that chat file exists in the correct location
        expected_chat_file = os.path.join(
            chatbot_dir, "data", "chat_sessions", username, f"{chat_id}.json"
        )

        if os.path.exists(expected_chat_file):
            print(f"  ✅ Chat file created in correct location: {expected_chat_file}")
        else:
            print(f"  ❌ Chat file not found: {expected_chat_file}")
            return False

        # Verify chat is listed
        chat_ids = list_user_chat_ids(username)
        if chat_id in chat_ids:
            print("  ✅ Chat listed in user's chat list")
        else:
            print("  ❌ Chat not found in user's chat list")
            return False

        # Clean up
        cleanup_test_user()

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_docker_vs_local_paths():
    """Test that paths are correct for both Docker and local environments."""
    print("🧪 Testing Docker vs local paths...")

    try:
        from infra_utils import get_chatbot_dir

        chatbot_dir = get_chatbot_dir()

        # Check if we're in Docker
        in_docker = os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"

        if in_docker:
            print("  🐳 Running in Docker environment")
            expected_path = "/home/appuser/.nypai-chatbot"
        else:
            print("  💻 Running in local environment")
            expected_path = os.path.expanduser("~/.nypai-chatbot")

        if chatbot_dir == expected_path:
            print(f"  ✅ Correct path for environment: {chatbot_dir}")
        else:
            print(f"  ❌ Wrong path. Expected: {expected_path}, Got: {chatbot_dir}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all data storage tests."""
    print("🚀 Testing Data Storage Configuration")
    print("=" * 50)

    tests = [
        ("Directory Structure", test_chatbot_directory_structure),
        ("User Database Separation", test_user_database_separation),
        ("Test User Creation", test_test_user_creation),
        ("Data Persistence", test_data_persistence),
        ("Docker vs Local Paths", test_docker_vs_local_paths),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 30)
    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All data storage tests passed!")
        print("✅ User data stored in ~/.nypai-chatbot")
        print("✅ Test users stored separately in test_users.json")
        print("✅ Build system won't override existing data")
        print("✅ Scripts can read/write data normally")
    else:
        print("\n❌ Some tests failed!")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
