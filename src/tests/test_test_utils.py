#!/usr/bin/env python3
"""
Test script to verify test_utils functionality with default test user.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_default_user_creation():
    """Test that default test user can be created."""
    print("🧪 Testing default test user creation...")

    try:
        from tests.test_utils import (
            create_test_user,
            get_default_test_user,
            cleanup_test_user,
        )

        # Get default user credentials
        test_user = get_default_test_user()
        print(f"  📝 Default user: {test_user['username']}")

        # Create the user
        success = create_test_user()
        assert success, "Failed to create default test user"
        print("  ✅ Default test user created successfully")

        # Clean up
        cleanup_success = cleanup_test_user()
        assert cleanup_success, "Failed to cleanup default test user"
        print("  ✅ Default test user cleaned up successfully")

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ensure_default_user():
    """Test that ensure_default_test_user works."""
    print("🧪 Testing ensure_default_test_user...")

    try:
        from tests.test_utils import ensure_default_test_user, cleanup_test_user

        # Ensure user exists
        success = ensure_default_test_user()
        assert success, "Failed to ensure default test user exists"
        print("  ✅ Default test user ensured successfully")

        # Clean up
        cleanup_success = cleanup_test_user()
        assert cleanup_success, "Failed to cleanup default test user"
        print("  ✅ Default test user cleaned up successfully")

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_context_manager():
    """Test the TestUserContext manager."""
    print("🧪 Testing TestUserContext...")

    try:
        from tests.test_utils import TestUserContext

        with TestUserContext() as username:
            print(f"  📝 Created test user: {username}")
            assert username == "test_user", f"Expected 'test_user', got '{username}'"
            print("  ✅ Context manager created user successfully")

        print("  ✅ Context manager cleaned up successfully")
        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_decorator():
    """Test the with_test_user decorator."""
    print("🧪 Testing with_test_user decorator...")

    try:
        from tests.test_utils import with_test_user

        @with_test_user()
        def test_function():
            print("  📝 Test function executed with default user")
            return True

        result = test_function()
        assert result, "Test function should return True"
        print("  ✅ Decorator worked successfully")

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all test_utils tests."""
    print("🚀 Testing test_utils functionality")
    print("=" * 50)

    tests = [
        ("Default User Creation", test_default_user_creation),
        ("Ensure Default User", test_ensure_default_user),
        ("Context Manager", test_context_manager),
        ("Decorator", test_decorator),
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
        print("\n🎉 All test_utils tests passed!")
        print("✅ Default test user functionality working")
        print("✅ Context managers working")
        print("✅ Decorators working")
    else:
        print("\n❌ Some tests failed!")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
