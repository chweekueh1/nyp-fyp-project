#!/usr/bin/env python3
"""
Simple test to verify the password hashing fix works correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set testing environment
os.environ["TESTING"] = "true"


def test_password_hashing_consistency():
    """Test that password hashing and verification work consistently."""
    print("🔍 Testing Password Hashing Consistency...")

    try:
        # Import the functions
        from backend.auth import _hash_password
        from hashing import verify_password

        # Test password
        test_password = "TestPassword123!"

        # Hash the password using the auth module
        hashed_password = _hash_password(test_password)
        print("  ✅ Password hashed successfully")
        print(f"  📝 Hash format: {hashed_password[:20]}...")

        # Verify the password using the hashing module
        is_valid = verify_password(test_password, hashed_password)

        if is_valid:
            print("  ✅ Password verification successful")
            print("  ✅ Password hashing consistency: PASSED")
            return True
        else:
            print("  ❌ Password verification failed")
            print("  ❌ Password hashing consistency: FAILED")
            return False

    except Exception as e:
        print(f"  ❌ Password hashing consistency: FAILED - {e}")
        return False


def test_change_password_function():
    """Test the change_password function directly."""
    print("🔍 Testing Change Password Function...")

    try:
        from backend.auth import change_password_test

        # Test with valid credentials
        result = change_password_test(
            username="test_user",
            current_password="TestPass123!",
            new_password="NewPass456!",
            confirm_password="NewPass456!",
        )

        success = (
            result[0] if isinstance(result, tuple) else result.get("success", False)
        )

        if success:
            print("  ✅ Change password function: PASSED")
            return True
        else:
            message = (
                result[1]
                if isinstance(result, tuple)
                else result.get("message", "Unknown error")
            )
            print(f"  ❌ Change password function: FAILED - {message}")
            return False

    except Exception as e:
        print(f"  ❌ Change password function: FAILED - {e}")
        return False


if __name__ == "__main__":
    print("🚀 Running Password Fix Tests")
    print("=" * 50)

    test1_passed = test_password_hashing_consistency()
    print()
    test2_passed = test_change_password_function()

    print()
    print("=" * 50)
    print("📊 Password Fix Test Results:")
    print("=" * 50)

    if test1_passed:
        print("  ✅ PASSED test_password_hashing_consistency")
    else:
        print("  ❌ FAILED test_password_hashing_consistency")

    if test2_passed:
        print("  ✅ PASSED test_change_password_function")
    else:
        print("  ❌ FAILED test_change_password_function")

    total_passed = sum([test1_passed, test2_passed])
    print(f"\n🎯 Summary: {total_passed}/2 tests passed")

    if total_passed == 2:
        print("✅ All password fix tests passed!")
        sys.exit(0)
    else:
        print("❌ Some password fix tests failed")
        sys.exit(1)
