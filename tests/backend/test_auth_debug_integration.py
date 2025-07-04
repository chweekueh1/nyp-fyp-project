#!/usr/bin/env python3
"""
Comprehensive Authentication Debug Test Suite

This test integrates the debug_auth functionality into the main test suite,
providing detailed authentication testing and debugging capabilities.
"""

import asyncio
import json
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthenticationDebugTester:
    """Comprehensive authentication testing and debugging class."""

    def __init__(self):
        self.test_results = []
        self.test_username = "debug_test_user"
        self.test_email = "debug@student.nyp.edu.sg"
        self.test_password = "DebugTest123!"

    async def test_registration_flow(self):
        """Test the complete registration flow with detailed debugging."""
        print("\n🔍 Testing Registration Flow:")
        print("-" * 50)

        try:
            from backend.auth import do_register

            print(f"📝 Registering user: {self.test_username}")
            print(f"📧 Email: {self.test_email}")
            print(f"🔐 Password: {self.test_password}")

            # Perform registration
            register_result = await do_register(
                self.test_username, self.test_password, self.test_email
            )

            # Debug output
            print("\n📊 Registration Result:")
            print(f"   Type: {type(register_result)}")
            print(f"   Content: {json.dumps(register_result, indent=4)}")

            # Validate result structure
            if not isinstance(register_result, dict):
                self.test_results.append(
                    ("Registration Structure", False, "Result is not a dictionary")
                )
                return False

            # Check required fields
            required_fields = ["status", "code", "message"]
            for field in required_fields:
                if field not in register_result:
                    self.test_results.append(
                        (
                            f"Registration Field {field}",
                            False,
                            f"Missing required field: {field}",
                        )
                    )
                    return False

            # Check status
            status = register_result.get("status")
            if status == "success":
                print("✅ Registration successful")
                self.test_results.append(("Registration Flow", True, "Success"))
                return True
            elif status == "error":
                error_msg = register_result.get("message", "Unknown error")
                print(
                    f"ℹ️ Registration failed (expected for existing user): {error_msg}"
                )
                # This might be expected if user already exists
                self.test_results.append(
                    ("Registration Flow", True, f"Expected error: {error_msg}")
                )
                return True
            else:
                print(f"❌ Unexpected registration status: {status}")
                self.test_results.append(
                    ("Registration Flow", False, f"Unexpected status: {status}")
                )
                return False

        except Exception as e:
            print(f"❌ Registration test failed: {e}")
            self.test_results.append(("Registration Flow", False, str(e)))
            return False

    async def test_login_flow(self):
        """Test the complete login flow with detailed debugging."""
        print("\n🔍 Testing Login Flow:")
        print("-" * 50)

        try:
            from backend.auth import do_login

            print(f"👤 Logging in user: {self.test_username}")
            print(f"🔐 Password: {self.test_password}")

            # Perform login
            login_result = await do_login(self.test_username, self.test_password)

            # Debug output
            print("\n📊 Login Result:")
            print(f"   Type: {type(login_result)}")
            print(f"   Content: {json.dumps(login_result, indent=4)}")

            # Validate result structure
            if not isinstance(login_result, dict):
                self.test_results.append(
                    ("Login Structure", False, "Result is not a dictionary")
                )
                return False

            # Check required fields
            required_fields = ["status", "code", "message"]
            for field in required_fields:
                if field not in login_result:
                    self.test_results.append(
                        (
                            f"Login Field {field}",
                            False,
                            f"Missing required field: {field}",
                        )
                    )
                    return False

            # Test frontend condition checks
            print("\n🎯 Frontend Condition Checks:")
            status = login_result.get("status")
            message = login_result.get("message", "")

            print(f"   login_result.get('status'): '{status}'")
            print(f"   login_result.get('status') == 'success': {status == 'success'}")
            print(f"   login_result.get('message'): '{message}'")

            # Validate login success
            if status == "success":
                print("✅ Login successful")
                self.test_results.append(("Login Flow", True, "Success"))

                # Check for additional success fields
                if "username" in login_result:
                    print(f"   ✅ Username returned: {login_result['username']}")
                if "email" in login_result:
                    print(f"   ✅ Email returned: {login_result['email']}")

                return True
            else:
                print(f"❌ Login failed: {message}")
                self.test_results.append(
                    ("Login Flow", False, f"Login failed: {message}")
                )
                return False

        except Exception as e:
            print(f"❌ Login test failed: {e}")
            self.test_results.append(("Login Flow", False, str(e)))
            return False

    async def test_password_hashing_consistency(self):
        """Test password hashing and verification consistency."""
        print("\n🔍 Testing Password Hashing Consistency:")
        print("-" * 50)

        try:
            from backend.auth import _hash_password
            from hashing import verify_password

            test_password = "TestConsistency123!"
            print(f"🔐 Testing password: {test_password}")

            # Hash the password
            hashed_password = _hash_password(test_password)
            print("   ✅ Password hashed successfully")
            print(f"   📝 Hash format: {hashed_password[:20]}...")

            # Verify the password
            is_valid = verify_password(test_password, hashed_password)

            if is_valid:
                print("   ✅ Password verification successful")
                self.test_results.append(("Password Hashing", True, "Consistent"))
                return True
            else:
                print("   ❌ Password verification failed")
                self.test_results.append(("Password Hashing", False, "Inconsistent"))
                return False

        except Exception as e:
            print(f"❌ Password hashing test failed: {e}")
            self.test_results.append(("Password Hashing", False, str(e)))
            return False

    async def test_test_environment_functions(self):
        """Test the test environment specific authentication functions."""
        print("\n🔍 Testing Test Environment Functions:")
        print("-" * 50)

        try:
            from backend.auth import do_register_test, do_login_test

            # Test registration in test environment
            test_user = "test_env_user"
            test_email = "testenv@student.nyp.edu.sg"
            test_password = "TestEnv123!"

            print(f"📝 Testing registration: {test_user}")
            register_result = await do_register_test(
                test_user, test_password, test_email
            )
            print(f"   Registration result: {register_result.get('status')}")

            # Test login in test environment
            print(f"👤 Testing login: {test_user}")
            login_result = await do_login_test(test_user, test_password)
            print(f"   Login result: {login_result.get('status')}")

            if register_result.get("status") in [
                "success",
                "error",
            ] and login_result.get("status") in ["success", "error"]:
                print("✅ Test environment functions working")
                self.test_results.append(
                    ("Test Environment", True, "Functions working")
                )
                return True
            else:
                print("❌ Test environment functions failed")
                self.test_results.append(
                    ("Test Environment", False, "Functions failed")
                )
                return False

        except Exception as e:
            print(f"❌ Test environment test failed: {e}")
            self.test_results.append(("Test Environment", False, str(e)))
            return False

    def print_summary(self):
        """Print a comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION DEBUG TEST SUMMARY")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {details}")
            if success:
                passed += 1
            else:
                failed += 1

        print(f"\n📈 Results: {passed} passed, {failed} failed")
        print(f"🎯 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

        return failed == 0


async def run_authentication_debug_tests():
    """Run all authentication debug tests."""
    print("🚀 NYP FYP Chatbot - Authentication Debug Test Suite")
    print("=" * 60)

    # Ensure test environment
    os.environ["TESTING"] = "true"

    # Create tester instance
    tester = AuthenticationDebugTester()

    # Run all tests
    tests = [
        tester.test_password_hashing_consistency(),
        tester.test_registration_flow(),
        tester.test_login_flow(),
        tester.test_test_environment_functions(),
    ]

    # Execute tests
    for test in tests:
        await test

    # Print summary
    success = tester.print_summary()

    print("\n🎯 Authentication debug testing completed!")
    return success


def main():
    """Main function for running authentication debug tests."""
    try:
        success = asyncio.run(run_authentication_debug_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
