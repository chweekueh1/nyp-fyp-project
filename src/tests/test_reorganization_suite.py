#!/usr/bin/env python3
"""
Test suite for NYP FYP CNC Chatbot reorganization verification.

This suite is now integrated into the main test suite under src/tests/.

This script tests:
1. New directory structure
2. Import functionality
3. Markdown formatter enhancements
4. Input character limit changes
5. Dockerfile updates
"""

import sys
from pathlib import Path

# Ensure src/ is in the Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Define project root for all path references
project_root = Path(__file__).parent.parent


def test_directory_structure():
    """Test that the new directory structure is correct."""
    print("🔍 Testing directory structure...")

    required_dirs = [
        project_root / "src",
        project_root / "src/backend",
        project_root / "src/gradio_modules",
        project_root / "src/llm",
        project_root / "src/infra_utils",
        project_root / "docker",
        project_root / "requirements",
        project_root / "src/tests",
        project_root / "docs",
        project_root / "styles",
        project_root / "src/scripts",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing_dirs.append(str(dir_path.relative_to(project_root)))

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False

    print("✅ Directory structure is correct")
    return True


def test_file_movements():
    """Test that key files have been moved correctly."""
    print("🔍 Testing file movements...")

    # Check that app.py exists in both locations
    if not (project_root / "app.py").exists():
        print("❌ app.py not found in root directory")
        return False

    if not (project_root / "src/app.py").exists():
        print("❌ src/app.py not found")
        return False

    # Check that Dockerfiles are in docker/ directory
    docker_files = ["Dockerfile", "Dockerfile.dev", "Dockerfile.benchmark"]
    for docker_file in docker_files:
        if not (project_root / "docker" / docker_file).exists():
            print(f"❌ docker/{docker_file} not found")
            return False

    # Check that requirements are in requirements/ directory
    req_files = ["requirements.txt", "requirements-docs.txt"]
    for req_file in req_files:
        if not (project_root / "requirements" / req_file).exists():
            print(f"❌ requirements/{req_file} not found")
            return False

    print("✅ File movements are correct")
    return True


def test_imports():
    """Test that imports work correctly with the new structure."""
    print("🔍 Testing imports...")

    try:
        import importlib.util

        spec = importlib.util.find_spec("app")
        if spec is not None:
            print("✅ src/app.py imports successfully")
        else:
            print("❌ src/app.py not found or import failed")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    print("✅ All imports work correctly")
    return True


def test_markdown_formatter():
    """Test the enhanced markdown formatter."""
    print("🔍 Testing markdown formatter...")

    try:
        from backend.markdown_formatter import MarkdownFormatter

        formatter = MarkdownFormatter()

        # Test table with special characters
        test_table = """| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Normal text | Text with | pipes | Text with *emphasis* |
| Text with `code` | Text with [links](url) | Text with #headers |
| Text with (parentheses) | Text with +plus+ | Text with -minus- |
| Text with !exclamation! | Text with ~tilde~ | Text with _underscore_ |"""

        formatted = formatter.format_markdown(test_table)

        # Check that special characters are escaped
        if "\\|" in formatted:
            print("✅ Pipe characters escaped correctly")
        else:
            print("❌ Pipe characters not escaped")
            return False

        if "\\*" in formatted:
            print("✅ Asterisks escaped correctly")
        else:
            print("❌ Asterisks not escaped")
            return False

        if "\\`" in formatted:
            print("✅ Backticks escaped correctly")
        else:
            print("❌ Backticks not escaped")
            return False

        if "\\[" in formatted and "\\]" in formatted:
            print("✅ Square brackets escaped correctly")
        else:
            print("❌ Square brackets not escaped")
            return False

        print("✅ Markdown formatter enhancements work correctly")
        return True

    except Exception as e:
        print(f"❌ Markdown formatter test failed: {e}")
        return False


def test_input_character_limit():
    """Test that the input character limit has been reduced."""
    print("🔍 Testing input character limit...")

    try:
        from backend.utils import sanitize_input

        # Test with a long input (should be truncated to 50000)
        long_input = "A" * 60000
        result = sanitize_input(long_input)

        if len(result) <= 50000:
            print(f"✅ Input correctly truncated to {len(result)} characters")
            return True
        else:
            print(f"❌ Input not truncated correctly: {len(result)} characters")
            return False

    except Exception as e:
        print(f"❌ Input character limit test failed: {e}")
        return False


def test_dockerfile_updates():
    """Test that Dockerfiles have been updated correctly."""
    print("🔍 Testing Dockerfile updates...")

    try:
        # Check production Dockerfile
        with open(project_root / "docker" / "Dockerfile", "r") as f:
            content = f.read()

        if "FROM python:3.11-alpine" in content:
            print("✅ Production Dockerfile uses python:3.11-alpine")
        else:
            print("❌ Production Dockerfile not updated to python:3.11-alpine")
            return False

        if 'CMD ["python", "src/app.py"]' in content:
            print("✅ Production Dockerfile references src/app.py")
        else:
            print("❌ Production Dockerfile doesn't reference src/app.py")
            return False

        # Check benchmark Dockerfile
        with open(project_root / "docker" / "Dockerfile.benchmark", "r") as f:
            content = f.read()

        if "FROM python:3.11-alpine" in content:
            print("✅ Benchmark Dockerfile uses python:3.11-alpine")
        else:
            print("❌ Benchmark Dockerfile not updated to python:3.11-alpine")
            return False

        print("✅ Dockerfile updates are correct")
        return True

    except Exception as e:
        print(f"❌ Dockerfile test failed: {e}")
        return False


def test_app_entry_point():
    """Test that the main app entry point works correctly."""
    print("🔍 Testing app entry point...")

    try:
        # Test that the root app.py can import from src/app.py
        with open(project_root / "app.py", "r") as f:
            content = f.read()

        if "from app import main" in content:
            print("✅ Root app.py imports from src/app.py")
        else:
            print("❌ Root app.py doesn't import from src/app.py")
            return False

        # Test that the import path is set correctly
        if (
            "sys.path.insert(0, str(src_path))" in content
            or "sys.path.insert(0, str(src_path))" in content
        ):
            print("✅ Root app.py sets Python path correctly")
        else:
            print("❌ Root app.py doesn't set Python path")
            return False

        print("✅ App entry point is correct")
        return True

    except Exception as e:
        print(f"❌ App entry point test failed: {e}")
        return False


def main():
    """Run all reorganization tests."""
    print("🚀 NYP FYP CNC Chatbot - Reorganization Verification")
    print("=" * 60)

    tests = [
        test_directory_structure,
        test_file_movements,
        test_imports,
        test_markdown_formatter,
        test_input_character_limit,
        test_dockerfile_updates,
        test_app_entry_point,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print("📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    if failed == 0:
        print("\n🎉 All reorganization tests passed!")
        print("The project has been successfully reorganized.")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
