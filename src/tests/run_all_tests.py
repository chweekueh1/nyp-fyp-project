#!/usr/bin/env python3
"""
Main Test Suite Runner

This script runs all tests in the project: backend, frontend, integration, and LLM tests.
"""

import sys
import os
import argparse
import traceback
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Check if running in the correct Docker container
if not (os.environ.get("DOCKER_MODE") == "test" or os.environ.get("IN_DOCKER") == "1"):
    print("WARNING: Tests should be run in Docker test environment!")
    sys.exit(1)


# Check if running in Docker test environment
if not os.environ.get("DOCKER_TEST_ENV"):
    print("⚠️  WARNING: Tests should be run in Docker test environment!")
    print(
        "   Use: docker build -f Dockerfile.test -t nyp-fyp-test . && docker run --rm nyp-fyp-test"
    )
    print("   Continuing with local execution...\n")


def run_backend_tests():
    """Run backend tests."""
    print("🔧 Running Backend Tests...")
    try:
        import asyncio
        from tests.backend.test_backend import (
            run_backend_tests as async_run_backend_tests,
        )

        success = asyncio.run(async_run_backend_tests())
        return success
    except ImportError as e:
        error_msg = f"Import error - {e}"
        print(f"❌ Backend tests failed: {error_msg}")
        print(
            "   This usually means the backend module or its dependencies are not available"
        )
        return False, error_msg
    except Exception as e:
        error_msg = f"{e}"
        print(f"❌ Backend tests failed: {error_msg}")
        print("   Full traceback:")
        traceback.print_exc()
        return False, error_msg


def run_frontend_tests():
    """Run frontend tests."""
    print("🎨 Running Frontend Tests...")
    try:
        from tests.frontend.run_frontend_tests import run_all_tests

        success = run_all_tests()
        return success
    except ImportError as e:
        error_msg = f"Import error - {e}"
        print(f"❌ Frontend tests failed: {error_msg}")
        print(
            "   This usually means the frontend modules or their dependencies are not available"
        )
        return False, error_msg
    except Exception as e:
        error_msg = f"{e}"
        print(f"❌ Frontend tests failed: {error_msg}")
        print("   Full traceback:")
        traceback.print_exc()
        return False, error_msg


def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running Integration Tests...")
    try:
        from tests.integration.test_integration import run_integration_tests

        success = run_integration_tests()
        return success
    except ImportError as e:
        error_msg = f"Import error - {e}"
        print(f"❌ Integration tests failed: {error_msg}")
        print(
            "   This usually means the integration modules or their dependencies are not available"
        )
        return False, error_msg
    except Exception as e:
        error_msg = f"{e}"
        print(f"❌ Integration tests failed: {error_msg}")
        print("   Full traceback:")
        traceback.print_exc()
        return False, error_msg


def run_llm_tests():
    """Run LLM tests."""
    print("🤖 Running LLM Tests...")
    try:
        from tests.llm.test_llm import run_llm_tests

        success = run_llm_tests()
        return success
    except ImportError as e:
        error_msg = f"Import error - {e}"
        print(f"❌ LLM tests failed: {error_msg}")
        print(
            "   This usually means the LLM modules or their dependencies are not available"
        )
        return False, error_msg
    except Exception as e:
        error_msg = f"{e}"
        print(f"❌ LLM tests failed: {error_msg}")
        print("   Full traceback:")
        traceback.print_exc()
        return False, error_msg


def run_all_tests():
    """Run all test suites."""
    print("🚀 Running All Test Suites...")
    print("=" * 60)

    # Ensure default test user exists before running tests
    print("👤 Setting up test environment...")
    try:
        from tests.test_utils import ensure_default_test_user

        ensure_default_test_user()
        print("✅ Test environment ready")
    except Exception as e:
        print(f"⚠️ Warning: Could not ensure test user exists: {e}")
        print("   Tests may fail if test user is not available")

    test_suites = [
        ("Backend Tests", run_backend_tests),
        ("Frontend Tests", run_frontend_tests),
        ("Integration Tests", run_integration_tests),
        ("LLM Tests", run_llm_tests),
    ]

    results = []
    failed_suites = []
    error_messages = []

    for suite_name, test_func in test_suites:
        try:
            print(f"\n{'=' * 50}")
            print(f"Running {suite_name}")
            print("=" * 50)
            result = test_func()

            # Handle both simple boolean and tuple (success, error_msg) returns
            if isinstance(result, tuple):
                success, error_msg = result
                if not success and error_msg:
                    error_messages.append(f"{suite_name}: {error_msg}")
            else:
                success = result
                error_msg = None

            results.append((suite_name, success))
            if not success:
                failed_suites.append(suite_name)
                if error_msg:
                    error_messages.append(f"{suite_name}: {error_msg}")

        except KeyboardInterrupt:
            print(f"\n⚠️  {suite_name} interrupted by user")
            results.append((suite_name, False))
            failed_suites.append(suite_name)
            error_messages.append(f"{suite_name}: Interrupted by user")
            break
        except Exception as e:
            error_msg = f"Unexpected exception: {e}"
            print(f"❌ {suite_name} failed with {error_msg}")
            print("   Full traceback:")
            traceback.print_exc()
            results.append((suite_name, False))
            failed_suites.append(suite_name)
            error_messages.append(f"{suite_name}: {error_msg}")

    # Summary
    print(f"\n{'=' * 60}")
    print("OVERALL TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for suite_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{suite_name}: {status}")

    print(f"\nOverall: {passed}/{total} test suites passed")

    if failed_suites:
        print(f"\nFailed test suites: {', '.join(failed_suites)}")

        # Display error messages
        if error_messages:
            print(f"\n{'=' * 60}")
            print("ERROR MESSAGES")
            print("=" * 60)
            for error_msg in error_messages:
                print(f"❌ {error_msg}")

    if passed == total:
        print("🎉 All test suites passed!")
    else:
        print("💥 Some test suites failed!")
        if len(failed_suites) == 1:
            print(
                f"   Only {failed_suites[0]} failed - you can run it individually with: --suite {failed_suites[0].lower().replace(' ', '')}"
            )

    return passed == total


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Main Test Suite Runner")
    parser.add_argument(
        "--suite",
        choices=["backend", "frontend", "integration", "llm", "all"],
        default="all",
        help="Test suite to run (default: all)",
    )

    args = parser.parse_args()

    try:
        if args.suite == "all":
            success = run_all_tests()
        elif args.suite == "backend":
            success = run_backend_tests()
        elif args.suite == "frontend":
            success = run_frontend_tests()
        elif args.suite == "integration":
            success = run_integration_tests()
        elif args.suite == "llm":
            success = run_llm_tests()
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            return 1

        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"❌ Unexpected error in test runner: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import run_tests

    run_tests.run_all()
