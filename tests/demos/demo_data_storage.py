#!/usr/bin/env python3
"""
Demo Data Storage Utility

This module provides demo data storage utilities for testing and demonstration purposes.
It should be located in the test suite (e.g., tests/demos/) and not in the project root.
"""

import os
import json
from pathlib import Path


def show_data_storage_info():
    """Show information about the data storage configuration."""
    print("📊 NYP FYP Chatbot - Data Storage Configuration")
    print("=" * 60)

    # Import after adding project root to path
    import sys

    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    from infra_utils import get_chatbot_dir, ensure_chatbot_dir_exists
    from backend import USER_DB_PATH, TEST_USER_DB_PATH

    # Ensure directories exist
    ensure_chatbot_dir_exists()
    chatbot_dir = get_chatbot_dir()

    print(f"\n🏠 Chatbot Directory: {chatbot_dir}")

    # Check if we're in Docker
    in_docker = os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"
    if in_docker:
        print("🐳 Environment: Docker")
    else:
        print("💻 Environment: Local Development")

    print("\n📁 Directory Structure:")
    subdirs = [
        "data/chat_sessions",
        "data/user_info",
        "data/vector_store/duckdb/chat",
    ]

    for subdir in subdirs:
        full_path = os.path.join(chatbot_dir, subdir)
        status = "✅" if os.path.exists(full_path) else "❌"
        print(f"  {status} {subdir}")

    print("\n👥 User Databases:")
    print(f"  📄 Production Users: {USER_DB_PATH}")
    print(f"  🧪 Test Users: {TEST_USER_DB_PATH}")

    # Show if files exist
    prod_exists = "✅" if os.path.exists(USER_DB_PATH) else "❌"
    test_exists = "✅" if os.path.exists(TEST_USER_DB_PATH) else "❌"

    print(f"  {prod_exists} Production database exists")
    print(f"  {test_exists} Test database exists")

    # Show user counts if databases exist
    if os.path.exists(USER_DB_PATH):
        try:
            with open(USER_DB_PATH, "r") as f:
                data = json.load(f)
                users = data.get("users", {})
                print(f"  📊 Production users: {len(users)}")
        except Exception as e:
            print(f"  ⚠️ Could not read production database: {e}")

    if os.path.exists(TEST_USER_DB_PATH):
        try:
            with open(TEST_USER_DB_PATH, "r") as f:
                data = json.load(f)
                users = data.get("users", {})
                print(f"  📊 Test users: {len(users)}")
        except Exception as e:
            print(f"  ⚠️ Could not read test database: {e}")

    print("\n🔒 Data Protection:")
    print("  ✅ User data stored in ~/.nypai-chatbot")
    print("  ✅ Test users stored separately in test_users.json")
    print("  ✅ Build system won't override existing data")
    print("  ✅ Scripts can read/write data normally")

    print("\n📝 Example Usage:")
    print("  # Create a test user")
    print("  python tests/test_utils.py --create-default")
    print("")
    print("  # Clean up test users")
    print("  python tests/test_utils.py --cleanup")
    print("")
    print("  # Run data storage tests")
    print("  python tests/test_data_storage.py")


if __name__ == "__main__":
    show_data_storage_info()
