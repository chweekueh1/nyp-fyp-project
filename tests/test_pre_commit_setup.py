#!/usr/bin/env python3
"""
Test script to verify pre-commit setup functionality.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_pre_commit_installation():
    """Test that pre-commit is installed in the virtual environment."""
    print("🧪 Testing pre-commit installation...")

    try:
        # Determine virtual environment path
        if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
            venv_path = "/home/appuser/.nypai-chatbot/venv"
        else:
            venv_path = os.path.join(project_root, ".venv")

        # Determine pre-commit executable path
        if sys.platform == "win32":
            pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit.exe")
        else:
            pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")

        if os.path.exists(pre_commit_path):
            print(f"  ✅ pre-commit found at: {pre_commit_path}")

            # Test pre-commit version
            try:
                result = subprocess.run(
                    [pre_commit_path, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                version = result.stdout.strip()
                print(f"  📦 pre-commit version: {version}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Could not get pre-commit version: {e}")
                return False
        else:
            print(f"  ❌ pre-commit not found at: {pre_commit_path}")
            return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pre_commit_config():
    """Test that .pre-commit-config.yaml exists and is valid."""
    print("🧪 Testing pre-commit configuration...")

    try:
        config_file = os.path.join(project_root, ".pre-commit-config.yaml")

        if not os.path.exists(config_file):
            print(f"  ❌ .pre-commit-config.yaml not found: {config_file}")
            return False

        print(f"  ✅ .pre-commit-config.yaml found: {config_file}")

        # Read and validate config
        with open(config_file, "r") as f:
            content = f.read()

        # Check for ruff hooks
        if "ruff-pre-commit" in content:
            print("  ✅ ruff-pre-commit hook configured")
        else:
            print("  ❌ ruff-pre-commit hook not found in config")
            return False

        if "ruff" in content:
            print("  ✅ ruff hook configured")
        else:
            print("  ❌ ruff hook not found in config")
            return False

        if "ruff-format" in content:
            print("  ✅ ruff-format hook configured")
        else:
            print("  ❌ ruff-format hook not found in config")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pre_commit_hooks_installed():
    """Test that pre-commit hooks are installed."""
    print("🧪 Testing pre-commit hooks installation...")

    try:
        # Determine virtual environment path
        if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
            venv_path = "/home/appuser/.nypai-chatbot/venv"
        else:
            venv_path = os.path.join(project_root, ".venv")

        # Determine pre-commit executable path
        if sys.platform == "win32":
            pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit.exe")
        else:
            pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")

        if not os.path.exists(pre_commit_path):
            print(f"  ❌ pre-commit not found: {pre_commit_path}")
            return False

        # Test pre-commit installed hooks
        try:
            result = subprocess.run(
                [pre_commit_path, "installed-hooks"],
                capture_output=True,
                text=True,
                check=True,
            )
            output = result.stdout.strip()

            if "ruff" in output:
                print("  ✅ ruff hook installed")
            else:
                print("  ❌ ruff hook not installed")
                return False

            if "ruff-format" in output:
                print("  ✅ ruff-format hook installed")
            else:
                print("  ❌ ruff-format hook not installed")
                return False

            return True

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Could not check installed hooks: {e}")
            return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pre_commit_validation():
    """Test that pre-commit configuration is valid."""
    print("🧪 Testing pre-commit configuration validation...")

    try:
        # Determine virtual environment path
        if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
            venv_path = "/home/appuser/.nypai-chatbot/venv"
        else:
            venv_path = os.path.join(project_root, ".venv")

        # Determine pre-commit executable path
        if sys.platform == "win32":
            pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit.exe")
        else:
            pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")

        if not os.path.exists(pre_commit_path):
            print(f"  ❌ pre-commit not found: {pre_commit_path}")
            return False

        # Test pre-commit validate-config
        try:
            subprocess.run(
                [pre_commit_path, "validate-config"],
                capture_output=True,
                text=True,
                check=True,
            )
            print("  ✅ pre-commit configuration is valid")
            return True

        except subprocess.CalledProcessError as e:
            print(f"  ❌ pre-commit configuration validation failed: {e}")
            if e.stderr:
                print(f"  Error details: {e.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all pre-commit setup tests."""
    print("🚀 Testing Pre-commit Setup")
    print("=" * 50)

    tests = [
        ("Pre-commit Installation", test_pre_commit_installation),
        ("Pre-commit Configuration", test_pre_commit_config),
        ("Pre-commit Hooks Installation", test_pre_commit_hooks_installed),
        ("Pre-commit Validation", test_pre_commit_validation),
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
        print("\n🎉 All pre-commit setup tests passed!")
        print("✅ pre-commit is properly installed")
        print("✅ Configuration is valid")
        print("✅ Hooks are installed")
        print("✅ Ready for code quality checks")
    else:
        print("\n❌ Some tests failed!")
        print("Run 'python setup.py --pre-commit' to set up pre-commit")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
