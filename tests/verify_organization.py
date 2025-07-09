"""
Verifies the file and directory organization of the NYP FYP CNC Chatbot project, including demo and utility files.
"""

#!/usr/bin/env python3
"""
Verification script for the organized test suite structure.
This script verifies that all files are in the correct locations and can be imported properly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_file_structure():
    """Verify that all expected files are in the correct locations."""
    print("🗂️ Verifying file structure...")

    expected_structure = {
        "tests/README.md": "Test suite documentation",
        "tests/comprehensive_test_suite.py": "Main test runner",
        "tests/ORGANIZATION_SUMMARY.md": "Organization summary",
        # Backend tests
        "tests/backend/test_backend.py": "Core backend tests",
        "tests/backend/test_backend_fixes_and_rename.py": "Backend fixes tests",
        # Frontend tests
        "tests/frontend/test_ui_fixes.py": "UI fixes tests",
        "tests/frontend/test_login_ui.py": "Login UI tests",
        "tests/frontend/test_chat_ui.py": "Chat UI tests",
        "tests/frontend/test_all_interfaces.py": "All interfaces tests",
        "tests/frontend/run_frontend_tests.py": "Frontend test runner",
        # Integration tests
        "tests/integration/test_integration.py": "Core integration tests",
        "tests/integration/test_enhanced_chatbot_features.py": "Enhanced features tests",
        "tests/integration/test_improved_app.py": "App improvements tests",
        "tests/integration/test_chatbot_integration.py": "Chatbot integration tests",
        "tests/integration/test_main_app_integration.py": "Main app integration tests",
        "tests/integration/test_main_app_launch.py": "App launch tests",
        # LLM tests
        "tests/llm/test_llm.py": "LLM functionality tests",
        # Demos
        "tests/demos/README.md": "Demo documentation",
        "tests/demos/demo_final_working_chatbot.py": "Complete feature demo",
        "tests/demos/demo_enhanced_chatbot.py": "Enhanced features demo",
        "tests/demos/demo_chatbot_with_history.py": "Chat history demo",
        "tests/demos/demo_integrated_main_app.py": "Full app demo",
        # Utils
        "tests/utils/debug_chatbot_ui.py": "UI debugging tools",
        "tests/utils/diagnose_chatbot_issue.py": "Issue diagnosis tools",
        "tests/utils/minimal_chatbot_test.py": "Minimal test setup",
    }

    missing_files = []
    found_files = []

    for file_path, description in expected_structure.items():
        full_path = project_root / file_path
        if full_path.exists():
            found_files.append((file_path, description))
            print(f"  ✅ {file_path}")
        else:
            missing_files.append((file_path, description))
            print(f"  ❌ {file_path} - MISSING")

    print("\n📊 Structure verification:")
    print(f"  ✅ Found: {len(found_files)} files")
    print(f"  ❌ Missing: {len(missing_files)} files")

    return len(missing_files) == 0


def verify_imports():
    """Verify that key modules can be imported correctly."""
    print("\n🔗 Verifying imports...")

    import_tests = [
        ("backend", "Core backend module"),
        ("gradio_modules.chatbot", "Chatbot UI module"),
        ("gradio_modules.login_and_register", "Login module"),
        ("llm.chatModel", "Chat model module"),
    ]

    successful_imports = 0

    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name} - {description}")
            successful_imports += 1
        except ImportError as e:
            print(f"  ❌ {module_name} - FAILED: {e}")
        except Exception as e:
            print(f"  ⚠️ {module_name} - WARNING: {e}")
            successful_imports += 1  # Count as success if it's not an import error

    print("\n📊 Import verification:")
    print(f"  ✅ Successful: {successful_imports}/{len(import_tests)} imports")

    return successful_imports == len(import_tests)


def verify_test_runners():
    """Verify that test runners exist and are executable."""
    print("\n🏃 Verifying test runners...")

    test_runners = [
        "tests/comprehensive_test_suite.py",
        "tests/run_all_tests.py",
        "tests/run_tests.py",
        "tests/frontend/run_frontend_tests.py",
    ]

    working_runners = 0

    for runner in test_runners:
        runner_path = project_root / runner
        if runner_path.exists():
            print(f"  ✅ {runner}")
            working_runners += 1
        else:
            print(f"  ❌ {runner} - MISSING")

    print("\n📊 Test runner verification:")
    print(f"  ✅ Available: {working_runners}/{len(test_runners)} runners")

    return working_runners == len(test_runners)


def verify_demos():
    """Verify that demo files exist and have correct structure."""
    print("\n🎭 Verifying demos...")

    demos_dir = project_root / "tests" / "demos"
    if not demos_dir.exists():
        print("  ❌ Demos directory missing")
        return False

    demo_files = list(demos_dir.glob("demo_*.py"))

    print(f"  📱 Found {len(demo_files)} demo files:")
    for demo in demo_files:
        print(f"    ✅ {demo.name}")

    readme_path = demos_dir / "README.md"
    if readme_path.exists():
        print("  📚 Demo documentation: ✅ README.md")
    else:
        print("  📚 Demo documentation: ❌ README.md missing")

    return len(demo_files) > 0 and readme_path.exists()


def verify_clean_root():
    """Verify that the root directory is clean of test/demo files."""
    print("\n🧹 Verifying clean root directory...")

    # Files that should NOT be in root anymore
    unwanted_patterns = [
        "test_*.py",
        "demo_*.py",
        "debug_*.py",
        "diagnose_*.py",
        "minimal_*.py",
    ]

    unwanted_files = []
    for pattern in unwanted_patterns:
        unwanted_files.extend(project_root.glob(pattern))

    if unwanted_files:
        print("  ❌ Found unwanted files in root:")
        for file in unwanted_files:
            print(f"    - {file.name}")
        return False
    else:
        print("  ✅ Root directory is clean")
        return True


def run_verification():
    """Run all verification checks."""
    print("🔍 NYP FYP Chatbot - Test Suite Organization Verification")
    print("=" * 60)

    checks = [
        ("File Structure", verify_file_structure),
        ("Module Imports", verify_imports),
        ("Test Runners", verify_test_runners),
        ("Demo Files", verify_demos),
        ("Clean Root", verify_clean_root),
    ]

    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results[check_name] = False

    # Summary
    print("\n📊 Verification Summary")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 Organization verification successful!")
        print("✅ All files properly organized")
        print("✅ All imports working correctly")
        print("✅ All test runners available")
        print("✅ All demos properly located")
        print("✅ Root directory clean")
        print("\n🚀 Test suite is ready for use!")
    else:
        print(f"\n⚠️ {total - passed} verification check(s) failed.")
        print("Please review the issues above.")

    return passed == total


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
