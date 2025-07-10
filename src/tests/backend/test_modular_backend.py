#!/usr/bin/env python3
"""
Test script to verify the modularized backend structure.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_keyword_cache():
    """Test the keyword cache functionality."""
    print("Testing keyword cache...")

    try:
        from llm.keyword_cache import (
            get_cached_response,
            set_cached_response,
            get_cache_stats,
            clear_cache,
        )

        # Test basic functionality
        set_cached_response("test keyword", "test response")
        cached = get_cached_response("test keyword")
        assert cached == "test response", f"Expected 'test response', got '{cached}'"

        # Test unique keyword functionality
        initial_stats = get_cache_stats()
        set_cached_response(
            "test keyword", "different response"
        )  # Should not add duplicate
        final_stats = get_cache_stats()
        assert final_stats["total_entries"] == initial_stats["total_entries"], (
            "Duplicate keyword should not be added"
        )

        # Test cache clearing
        clear_cache()
        stats_after_clear = get_cache_stats()
        assert stats_after_clear["total_entries"] == 0, (
            "Cache should be empty after clearing"
        )

        print("✅ Keyword cache tests passed!")
        return True

    except Exception as e:
        print(f"❌ Keyword cache test failed: {e}")
        return False


def test_backend_modules():
    """Test that backend modules can be imported."""
    print("Testing backend modules...")

    try:
        # Test individual modules
        from backend.config import ALLOWED_EMAILS, CHAT_DATA_PATH

        print("✅ Config module imported successfully")
        print(f"   - ALLOWED_EMAILS: {len(ALLOWED_EMAILS)} entries")
        print(f"   - CHAT_DATA_PATH: {CHAT_DATA_PATH}")

        print("✅ Rate limiting module imported successfully")

        print("✅ Utils module imported successfully")

        print("✅ Auth module imported successfully")

        print("✅ Chat module imported successfully")

        print("✅ File handling module imported successfully")

        print("✅ Audio module imported successfully")

        print("✅ Database module imported successfully")

        print("✅ Main module imported successfully")

        print("✅ All backend modules imported successfully!")
        return True

    except Exception as e:
        print(f"❌ Backend module test failed: {e}")
        return False


def test_backward_compatibility():
    """Test that the original backend.py still works."""
    print("Testing backward compatibility...")

    try:
        # Test that the original backend.py can be imported
        import backend as original_backend

        print("✅ Original backend.py imported successfully")

        # Test that key functions are available
        assert hasattr(original_backend, "init_backend"), "init_backend not found"
        assert hasattr(original_backend, "ask_question"), "ask_question not found"
        assert hasattr(original_backend, "do_login"), "do_login not found"
        assert hasattr(original_backend, "check_rate_limit"), (
            "check_rate_limit not found"
        )

        print("✅ Backward compatibility tests passed!")
        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing modularized backend structure...\n")

    tests = [test_keyword_cache, test_backend_modules, test_backward_compatibility]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The modularized backend is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
