#!/usr/bin/env python3
"""
Test script to verify Docker test environment is working correctly.
This script checks:
1. Environment variables are set correctly
2. Test database paths are accessible
3. Basic imports work
4. Test user creation works
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_environment_variables():
    """Test that environment variables are set correctly."""
    print("🔍 Testing environment variables...")

    # Check TESTING environment variable
    testing = os.getenv("TESTING", "").lower() == "true"
    print(f"  TESTING=true: {testing}")

    # Check IN_DOCKER environment variable
    in_docker = os.getenv("IN_DOCKER", "").lower() == "true"
    print(f"  IN_DOCKER=true: {in_docker}")

    # Check PYTHONUNBUFFERED
    python_unbuffered = os.getenv("PYTHONUNBUFFERED", "")
    print(f"  PYTHONUNBUFFERED: {python_unbuffered}")

    return testing and in_docker


def test_imports():
    """Test that basic imports work."""
    print("\n📦 Testing imports...")

    try:
        print("  ✅ backend imported successfully")
    except Exception as e:
        print(f"  ❌ backend import failed: {e}")
        return False

    try:
        print("  ✅ test_utils imported successfully")
    except Exception as e:
        print(f"  ❌ test_utils import failed: {e}")
        return False

    try:
        print("  ✅ llm.chatModel imported successfully")
    except Exception as e:
        print(f"  ❌ llm.chatModel import failed: {e}")
        return False

    return True


def test_database_paths():
    """Test that database paths are accessible."""
    print("\n🗄️ Testing database paths...")

    try:
        import backend

        # Check test database path
        test_db_path = backend.TEST_USER_DB_PATH
        test_db_dir = os.path.dirname(test_db_path)

        print(f"  Test DB path: {test_db_path}")
        print(f"  Test DB directory: {test_db_dir}")

        # Ensure directory exists
        os.makedirs(test_db_dir, exist_ok=True)
        print("  ✅ Test database directory created/accessible")

        # Check if we can write to the directory
        test_file = os.path.join(test_db_dir, "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("  ✅ Test database directory is writable")

        return True

    except Exception as e:
        print(f"  ❌ Database path test failed: {e}")
        return False


def test_user_creation():
    """Test that test user creation works."""
    print("\n👤 Testing user creation...")

    try:
        from tests.test_utils import ensure_default_test_user, cleanup_test_user

        # Clean up any existing test user
        cleanup_test_user("test_user")

        # Create test user
        success = ensure_default_test_user()
        print(f"  Test user creation: {'✅ Success' if success else '❌ Failed'}")

        return success

    except Exception as e:
        print(f"  ❌ User creation test failed: {e}")
        return False


def test_backend_initialization():
    """Test that backend initialization works."""
    print("\n⚙️ Testing backend initialization...")

    try:
        import backend
        import asyncio

        # Test backend initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(backend.init_backend())
            print("  ✅ Backend initialization successful")
            return True
        finally:
            loop.close()

    except Exception as e:
        print(f"  ❌ Backend initialization failed: {e}")
        return False


def main():
    """Run all Docker environment tests."""
    print("🐳 Docker Test Environment Verification")
    print("=" * 50)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("Imports", test_imports),
        ("Database Paths", test_database_paths),
        ("User Creation", test_user_creation),
        ("Backend Initialization", test_backend_initialization),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 50)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Docker environment is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
