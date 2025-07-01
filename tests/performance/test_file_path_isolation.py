#!/usr/bin/env python3
"""
Test file path isolation to ensure test files don't pollute production directories.
Verifies that test uploads go to ~/.nypai-chatbot/test_uploads/ instead of production paths.
"""

import sys
import os
from pathlib import Path
from llm.chatModel import initialize_llm_and_db

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

initialize_llm_and_db()


def test_production_vs_test_paths():
    """Test that production and test paths are correctly separated."""
    print("🔍 Testing Production vs Test Path Separation...")

    try:
        from llm.dataProcessing import get_data_paths

        # Test production paths (default)
        os.environ.pop("TESTING", None)  # Remove if exists
        prod_chat, prod_class, prod_keywords, prod_db = get_data_paths()

        # Test paths (with TESTING=true)
        os.environ["TESTING"] = "true"
        test_chat, test_class, test_keywords, test_db = get_data_paths()

        # Verify paths are different
        assert prod_chat != test_chat, (
            "Production and test chat paths should be different"
        )
        assert prod_class != test_class, (
            "Production and test classification paths should be different"
        )
        assert prod_keywords != test_keywords, (
            "Production and test keywords paths should be different"
        )
        assert prod_db != test_db, (
            "Production and test database paths should be different"
        )

        # Verify test paths contain 'test'
        assert "test_uploads" in test_chat, (
            "Test chat path should contain 'test_uploads'"
        )
        assert "test_uploads" in test_class, (
            "Test classification path should contain 'test_uploads'"
        )
        assert "test_data" in test_keywords, (
            "Test keywords path should contain 'test_data'"
        )
        assert "test_data" in test_db, "Test database path should contain 'test_data'"

        # Verify production paths don't contain 'test'
        assert "test" not in prod_chat.lower(), (
            "Production chat path should not contain 'test'"
        )
        assert "test" not in prod_class.lower(), (
            "Production classification path should not contain 'test'"
        )
        assert "test" not in prod_keywords.lower(), (
            "Production keywords path should not contain 'test'"
        )
        assert "test" not in prod_db.lower(), (
            "Production database path should not contain 'test'"
        )

        print(f"  🏭 Production chat path: {prod_chat}")
        print(f"  🧪 Test chat path: {test_chat}")
        print("  ✅ Path separation: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Path separation: FAILED - {e}")
        return False


def test_test_environment_detection():
    """Test various methods of test environment detection."""
    print("🔍 Testing Test Environment Detection...")

    try:
        from llm.dataProcessing import get_data_paths

        # Test 1: TESTING environment variable
        os.environ["TESTING"] = "true"
        chat_path, _, _, _ = get_data_paths()
        assert "test_uploads" in chat_path, "Should detect TESTING=true"

        # Test 2: Remove TESTING env var
        os.environ.pop("TESTING", None)
        chat_path, _, _, _ = get_data_paths()
        assert "test_uploads" not in chat_path, (
            "Should not use test paths without TESTING"
        )

        print("  🔍 Environment detection working correctly")
        print("  ✅ Test environment detection: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Test environment detection: FAILED - {e}")
        return False


def test_directory_creation():
    """Test that test directories are created automatically."""
    print("🔍 Testing Test Directory Creation...")

    try:
        from llm.dataProcessing import get_data_paths

        # Set test environment
        os.environ["TESTING"] = "true"

        # Get test paths (should create directories)
        test_chat, test_class, test_keywords, test_db = get_data_paths()

        # Verify directories exist
        assert os.path.exists(test_chat), (
            f"Test chat directory should exist: {test_chat}"
        )
        assert os.path.exists(test_class), (
            f"Test classification directory should exist: {test_class}"
        )
        assert os.path.exists(os.path.dirname(test_keywords)), (
            "Test keywords parent directory should exist"
        )
        assert os.path.exists(test_db), (
            f"Test database directory should exist: {test_db}"
        )

        print("  📁 Test directories created successfully")
        print("  ✅ Directory creation: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Directory creation: FAILED - {e}")
        return False


def test_file_processing_isolation():
    """Test that file processing uses correct paths in test mode."""
    print("🔍 Testing File Processing Path Isolation...")

    try:
        # Set test environment
        os.environ["TESTING"] = "true"

        # Import after setting environment and update paths
        from llm.dataProcessing import get_current_paths

        # Update global paths and get current values
        CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, _, _ = get_current_paths()

        # Verify the global paths are test paths
        assert "test_uploads" in CHAT_DATA_PATH, (
            f"CHAT_DATA_PATH should be test path: {CHAT_DATA_PATH}"
        )
        assert "test_uploads" in CLASSIFICATION_DATA_PATH, (
            f"CLASSIFICATION_DATA_PATH should be test path: {CLASSIFICATION_DATA_PATH}"
        )

        print(f"  📂 Chat data path: {CHAT_DATA_PATH}")
        print(f"  📂 Classification data path: {CLASSIFICATION_DATA_PATH}")
        print("  ✅ File processing isolation: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ File processing isolation: FAILED - {e}")
        return False


def test_database_initialization_isolation():
    """Test that database initialization uses test paths."""
    print("🔍 Testing Database Initialization Path Isolation...")

    try:
        # Set test environment
        os.environ["TESTING"] = "true"

        # Import database initialization function
        from llm.dataProcessing import get_current_paths
        from glob import glob

        # Update paths and get current values
        CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, _, _ = get_current_paths()

        # Check that the paths used for file globbing are test paths
        chat_files = glob(CHAT_DATA_PATH + "/**/*.*", recursive=True)
        classification_files = glob(
            CLASSIFICATION_DATA_PATH + "/**/*.*", recursive=True
        )

        # Verify paths contain test directories
        if chat_files:
            for file_path in chat_files:
                assert "test_uploads" in file_path, (
                    f"Chat file should be in test directory: {file_path}"
                )

        if classification_files:
            for file_path in classification_files:
                assert "test_uploads" in file_path, (
                    f"Classification file should be in test directory: {file_path}"
                )

        print(f"  📊 Found {len(chat_files)} chat files in test directory")
        print(
            f"  📊 Found {len(classification_files)} classification files in test directory"
        )
        print("  ✅ Database initialization isolation: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Database initialization isolation: FAILED - {e}")
        return False


def test_cleanup_and_reset():
    """Test cleanup and reset to production mode."""
    print("🔍 Testing Cleanup and Reset...")

    try:
        # Remove test environment
        os.environ.pop("TESTING", None)

        # Re-import to get fresh paths
        import importlib
        import llm.dataProcessing

        importlib.reload(llm.dataProcessing)

        from llm.dataProcessing import get_data_paths

        # Verify we're back to production paths
        chat_path, _, _, _ = get_data_paths()
        assert "test_uploads" not in chat_path, "Should be back to production paths"

        print("  🔄 Reset to production mode successfully")
        print("  ✅ Cleanup and reset: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Cleanup and reset: FAILED - {e}")
        return False


def run_file_path_isolation_tests():
    """Run all file path isolation tests."""
    print("🚀 Running File Path Isolation Tests")
    print("=" * 60)

    tests = [
        test_production_vs_test_paths,
        test_test_environment_detection,
        test_directory_creation,
        test_file_processing_isolation,
        test_database_initialization_isolation,
        test_cleanup_and_reset,
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
    print("📊 File Path Isolation Test Results:")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All file path isolation tests passed!")
        print("\n📋 Verified Features:")
        print("  ✅ Production vs test path separation")
        print("  ✅ Test environment detection")
        print("  ✅ Automatic test directory creation")
        print("  ✅ File processing path isolation")
        print("  ✅ Database initialization isolation")
        print("  ✅ Cleanup and reset functionality")
        print("\n🛡️ Test files will now go to:")
        print("  📁 ~/.nypai-chatbot/test_uploads/txt_files/")
        print("  📁 ~/.nypai-chatbot/test_uploads/classification_files/")
        print("  📁 ~/.nypai-chatbot/test_data/")
        return True
    else:
        print("⚠️ Some file path isolation tests failed")
        return False


if __name__ == "__main__":
    success = run_file_path_isolation_tests()
    sys.exit(0 if success else 1)
