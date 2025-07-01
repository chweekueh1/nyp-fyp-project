#!/usr/bin/env python3
"""
Test that the comprehensive test suite has been properly fixed.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_help_functionality():
    """Test that help functionality works correctly."""
    print("🔍 Testing Help Functionality...")

    try:
        result = subprocess.run(
            [sys.executable, "tests/comprehensive_test_suite.py", "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        if result.returncode == 0:
            output = result.stdout

            # Check for key help sections
            required_sections = [
                "NYP FYP Chatbot - Comprehensive Test Suite",
                "Usage:",
                "Options:",
                "Test Categories:",
                "Demo Usage:",
            ]

            missing_sections = []
            for section in required_sections:
                if section not in output:
                    missing_sections.append(section)

            if missing_sections:
                print(f"  ❌ Missing help sections: {missing_sections}")
                return False
            else:
                print("  ✅ All help sections present")

            # Check for specific options
            required_options = ["--help", "--demos", "--quick", "--performance"]
            missing_options = []
            for option in required_options:
                if option not in output:
                    missing_options.append(option)

            if missing_options:
                print(f"  ❌ Missing options: {missing_options}")
                return False
            else:
                print("  ✅ All options documented")

            print("  ✅ Help functionality: PASSED")
            return True
        else:
            print(f"  ❌ Help command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Help functionality: FAILED - {e}")
        return False


def test_demos_listing():
    """Test that demos listing works correctly."""
    print("🔍 Testing Demos Listing...")

    try:
        result = subprocess.run(
            [sys.executable, "tests/comprehensive_test_suite.py", "--demos"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )

        if result.returncode == 0:
            output = result.stdout

            # Check for demo listing header
            if "Available Demos" not in output:
                print("  ❌ Missing demos header")
                return False

            # Check for expected demos
            expected_demos = [
                "demo_final_working_chatbot.py",
                "demo_enhanced_chatbot.py",
                "demo_file_classification.py",
                "demo_enhanced_classification.py",
            ]

            found_demos = []
            missing_demos = []

            for demo in expected_demos:
                if demo in output:
                    found_demos.append(demo)
                else:
                    missing_demos.append(demo)

            if missing_demos:
                print(f"  ⚠️ Missing demos: {missing_demos}")

            # Check that demos show correct location
            if "(tests/demos)" in output:
                print("  ✅ Demos correctly located in tests/demos/")
            else:
                print("  ❌ Demos not showing correct location")
                return False

            print(f"  ✅ Found {len(found_demos)} demos")
            print("  ✅ Demos listing: PASSED")
            return True
        else:
            print(f"  ❌ Demos listing failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Demos listing: FAILED - {e}")
        return False


def test_performance_tests_only():
    """Test that performance tests only option works."""
    print("🔍 Testing Performance Tests Only...")

    try:
        result = subprocess.run(
            [sys.executable, "tests/comprehensive_test_suite.py", "--performance"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        # Performance tests should run (may pass or fail, but should execute)
        output = result.stdout + result.stderr

        # Check for performance test execution
        if "Running Performance Tests" not in output:
            print("  ❌ Performance tests not executed")
            return False

        # Check for expected performance test files
        expected_perf_tests = [
            "test_demo_organization.py",
            "test_final_organization_verification.py",
            "test_logging_and_dependency_paths.py",
            "test_syntax_and_formatting_fixes.py",
        ]

        found_tests = []
        for test in expected_perf_tests:
            if test in output:
                found_tests.append(test)

        if len(found_tests) >= 3:  # Allow some flexibility
            print(f"  ✅ Found {len(found_tests)} performance tests")
        else:
            print(f"  ❌ Only found {len(found_tests)} performance tests")
            return False

        # Check that it doesn't run other test categories
        if "Running Unit Tests" in output or "Running Integration Tests" in output:
            print("  ❌ Other test categories ran when only performance requested")
            return False

        print("  ✅ Performance tests only: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Performance tests only: FAILED - {e}")
        return False


def test_comprehensive_suite_structure():
    """Test that comprehensive suite has proper structure."""
    print("🔍 Testing Comprehensive Suite Structure...")

    try:
        # Import the test suite
        from tests.comprehensive_test_suite import TestSuite

        suite = TestSuite()

        # Check that it has required methods
        required_methods = [
            "run_unit_tests",
            "run_integration_tests",
            "run_frontend_tests",
            "run_performance_tests",
            "run_demo_verification",
            "list_available_demos",
            "run_comprehensive_suite",
            "print_summary",
        ]

        missing_methods = []
        for method in required_methods:
            if not hasattr(suite, method):
                missing_methods.append(method)

        if missing_methods:
            print(f"  ❌ Missing methods: {missing_methods}")
            return False
        else:
            print("  ✅ All required methods present")

        # Test demo listing functionality
        demos = suite.list_available_demos()
        if len(demos) > 0:
            print(f"  ✅ Found {len(demos)} demo files")
        else:
            print("  ⚠️ No demo files found")

        print("  ✅ Comprehensive suite structure: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Comprehensive suite structure: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test that error handling works properly."""
    print("🔍 Testing Error Handling...")

    try:
        # Test with invalid option
        result = subprocess.run(
            [sys.executable, "tests/comprehensive_test_suite.py", "--invalid"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        # Should run normally (ignoring unknown options)
        if result.returncode in [0, 1]:  # 0 for success, 1 for test failures
            print("  ✅ Handles invalid options gracefully")
        else:
            print("  ❌ Crashes on invalid options")
            return False

        # Test that it can handle missing test files gracefully
        output = result.stdout + result.stderr
        if "SKIP" in output or "not found" in output:
            print("  ✅ Handles missing test files gracefully")
        else:
            print("  ✅ No missing files to handle")

        print("  ✅ Error handling: PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Error handling: FAILED - {e}")
        return False


def run_comprehensive_test_suite_fix_tests():
    """Run all comprehensive test suite fix tests."""
    print("🚀 Running Comprehensive Test Suite Fix Tests")
    print("=" * 60)

    tests = [
        test_help_functionality,
        test_demos_listing,
        test_performance_tests_only,
        test_comprehensive_suite_structure,
        test_error_handling,
    ]

    results = []

    for test_func in tests:
        print(f"\n{'=' * 40}")
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append((test_func.__name__, False))

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Comprehensive Test Suite Fix Results:")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All comprehensive test suite fix tests passed!")
        print("\n📋 Fixes Verified:")
        print("  ✅ Help functionality working correctly")
        print("  ✅ Demo listing with proper location detection")
        print("  ✅ Performance tests only option working")
        print("  ✅ Proper test suite structure and methods")
        print("  ✅ Graceful error handling for edge cases")
        print("\n🛠️ Improvements Achieved:")
        print("  🔧 Clean command-line interface with help")
        print("  🔧 Organized test categories and execution")
        print("  🔧 Proper demo organization verification")
        print("  🔧 Flexible test execution options")
        print("  🔧 Robust error handling and reporting")
        return True
    else:
        print("⚠️ Some comprehensive test suite fix tests failed")
        return False


if __name__ == "__main__":
    success = run_comprehensive_test_suite_fix_tests()
    sys.exit(0 if success else 1)
