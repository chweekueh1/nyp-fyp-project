#!/usr/bin/env python3
"""
Standalone Authentication Debug Test Runner

This script runs only the authentication debug tests for focused debugging
and validation of authentication functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check if running in Docker test environment
if not os.environ.get("DOCKER_TEST_ENV"):
    print("⚠️  WARNING: Tests should be run in Docker test environment!")
    print(
        "   Use: docker build -f Dockerfile.test -t nyp-fyp-test . && docker run --rm nyp-fyp-test"
    )
    print("   Continuing with local execution...\n")


def main():
    """Main function to run authentication debug tests."""
    print("🔍 NYP FYP Chatbot - Authentication Debug Test Runner")
    print("=" * 60)

    try:
        # Set testing environment
        os.environ["TESTING"] = "true"

        # Import and run the authentication debug tests
        from tests.backend.test_auth_debug_integration import (
            run_authentication_debug_tests,
        )

        # Run the tests
        success = asyncio.run(run_authentication_debug_tests())

        if success:
            print("\n🎉 All authentication debug tests passed!")
            return 0
        else:
            print("\n❌ Some authentication debug tests failed!")
            return 1

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required modules are available")
        return 1
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
