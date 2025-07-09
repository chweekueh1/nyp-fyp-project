"""
Debug and unit tests for search functionality in the backend of the NYP FYP CNC Chatbot project.
"""

#!/usr/bin/env python3
"""
Test script to verify search functionality and debug search-related issues.
This test focuses on sanitize_input, search functionality, and NLTK data availability.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import nltk
from backend import sanitize_input, search_chat_history
from backend.chat import _get_chat_metadata_cache_internal
import difflib


def test_sanitize_input():
    """Test input sanitization function with various inputs."""
    print("🔍 Testing sanitize_input function...")

    try:
        # Test normal input
        result = sanitize_input("Hello World")
        assert result == "Hello World", f"Expected 'Hello World', got '{result}'"
        print("  ✅ Normal input sanitization passed")

        # Test empty input
        result = sanitize_input("")
        assert result == "", f"Expected empty string, got '{result}'"
        result = sanitize_input(None)
        assert result == "", f"Expected empty string for None, got '{result}'"
        print("  ✅ Empty/None input sanitization passed")

        # Test input with special characters
        result = sanitize_input("Hello <script>alert('xss')</script>")
        expected = "Hello alert(&#x27;xss&#x27;)"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("  ✅ Special characters sanitization passed")

        # Test input with characters that should be removed (<>"')
        result = sanitize_input("Hello\"World<test>value'end")
        expected = "HelloWorldvalue"
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print("  ✅ Dangerous character removal passed")

        # Test input length limit
        long_input = "A" * 12000
        result = sanitize_input(long_input)
        assert len(result) <= 400000, f"Expected length <= 400000, got {len(result)}"
        print("  ✅ Input length limit passed")

        print("✅ test_sanitize_input: PASSED")
        return True

    except Exception as e:
        print(f"❌ test_sanitize_input: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_functionality():
    """Test basic search functionality."""
    print("🔍 Testing search functionality...")

    try:
        username = "test_search_debug_user"

        # Test search with empty query
        results, status = search_chat_history("", username)
        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert isinstance(status, str), f"Expected string, got {type(status)}"
        print("  ✅ Empty query search passed")

        # Test search with normal query
        results, status = search_chat_history("test", username)
        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert isinstance(status, str), f"Expected string, got {type(status)}"
        print("  ✅ Normal query search passed")

        # Test search with special characters (should be sanitized)
        results, status = search_chat_history(
            "test<script>alert('xss')</script>", username
        )
        assert isinstance(results, list), f"Expected list, got {type(results)}"
        assert isinstance(status, str), f"Expected string, got {type(status)}"
        print("  ✅ Special characters query search passed")

        print("✅ test_search_functionality: PASSED")
        return True

    except Exception as e:
        print(f"❌ test_search_functionality: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_nltk_data_availability():
    """Test that NLTK data is available for search functionality."""
    print("🔍 Testing NLTK data availability...")

    try:
        # Test if NLTK is available
        assert nltk is not None, "NLTK should be available"
        print("  ✅ NLTK import successful")

        # Test if required NLTK data is available
        try:
            # Try to access NLTK data that might be used in search
            nltk.data.find("tokenizers/punkt")
            print("  ✅ NLTK punkt tokenizer available")
        except LookupError:
            print("  ⚠️  NLTK punkt tokenizer not found (may need download)")

        try:
            # Try to access stopwords
            nltk.data.find("corpora/stopwords")
            print("  ✅ NLTK stopwords available")
        except LookupError:
            print("  ⚠️  NLTK stopwords not found (may need download)")

        # Test basic NLTK functionality
        from nltk.tokenize import word_tokenize

        tokens = word_tokenize("Hello world!")
        assert len(tokens) > 0, "NLTK tokenization should work"
        print("  ✅ NLTK tokenization working")

        print("✅ test_nltk_data_availability: PASSED")
        return True

    except Exception as e:
        print(f"❌ test_nltk_data_availability: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_internal_cache_access():
    """Test access to internal chat metadata cache."""
    print("🔍 Testing internal cache access...")

    try:
        # Get the internal cache
        internal_cache = _get_chat_metadata_cache_internal()

        # Check if the cache is accessible
        assert isinstance(internal_cache, dict), "Internal cache should be a dictionary"
        print("  ✅ Internal cache is accessible")

        # Check cache structure
        for username, user_chats in internal_cache.items():
            assert isinstance(user_chats, dict), (
                f"User chats for {username} should be a dictionary"
            )
            for chat_id, chat_data in user_chats.items():
                assert isinstance(chat_data, dict), (
                    f"Chat data for {chat_id} should be a dictionary"
                )
                if "history" in chat_data:
                    assert isinstance(chat_data["history"], list), (
                        f"History for {chat_id} should be a list"
                    )
                if "name" in chat_data:
                    assert isinstance(chat_data["name"], str), (
                        f"Name for {chat_id} should be a string"
                    )

        print("  ✅ Internal cache structure is valid")
        print("✅ test_internal_cache_access: PASSED")
        return True

    except Exception as e:
        print(f"❌ test_internal_cache_access: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_debug():
    """Test search functionality with debug output."""
    print("🔍 Testing search functionality with debug output...")

    username = "test_search_debug"

    # Create test chat data with the exact content from the logs
    test_chat_id = "test_search_debug_123"
    test_chat_data = {
        "name": "My Test Chat",
        "history": [
            [
                "hi",
                "Hello! How can I assist you today? If you need help with sensitivity labels or data security classifications, feel free to ask!",
            ]
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    print(f"✅ Added test data: {len(test_chat_data['history'])} messages")

    # Test 1: Search for "data" (should find it in bot response)
    print("\n📝 Testing search for 'data'...")
    results, status = search_chat_history("data", username)

    print(f"Results: {len(results)} found")
    print(f"Status: {status}")

    for i, result in enumerate(results):
        print(f"  Result {i + 1}:")
        print(f"    Chat: {result['chat_name']}")
        print(f"    Type: {result['message_type']}")
        print(f"    Score: {result['similarity_score']}")
        print(f"    Content: {result['content'][:100]}...")

    # Test 2: Manual difflib test
    print("\n📝 Manual difflib test...")
    query = "data"
    bot_message = "Hello! How can I assist you today? If you need help with sensitivity labels or data security classifications, feel free to ask!"

    similarity = difflib.SequenceMatcher(None, query, bot_message.lower()).ratio()
    print(f"Query: '{query}'")
    print(f"Message: '{bot_message[:50]}...'")
    print(f"Similarity score: {similarity:.3f}")
    print(f"Would match with threshold 0.25: {similarity >= 0.25}")

    # Test 3: Search for "hi" (should find it in user message)
    print("\n📝 Testing search for 'hi'...")
    results, status = search_chat_history("hi", username)

    print(f"Results: {len(results)} found")
    print(f"Status: {status}")

    for i, result in enumerate(results):
        print(f"  Result {i + 1}:")
        print(f"    Chat: {result['chat_name']}")
        print(f"    Type: {result['message_type']}")
        print(f"    Score: {result['similarity_score']}")
        print(f"    Content: {result['content'][:100]}...")

    # Test 4: Search for "security" (should find it in bot response)
    print("\n📝 Testing search for 'security'...")
    results, status = search_chat_history("security", username)

    print(f"Results: {len(results)} found")
    print(f"Status: {status}")

    for i, result in enumerate(results):
        print(f"  Result {i + 1}:")
        print(f"    Chat: {result['chat_name']}")
        print(f"    Type: {result['message_type']}")
        print(f"    Score: {result['similarity_score']}")
        print(f"    Content: {result['content'][:100]}...")

    print("\n✅ Search debug test completed!")


async def run_all_search_debug_tests():
    """Run all search debug tests."""
    print("🚀 Running all search debug tests...")
    print("=" * 60)

    # Test 1: Input sanitization
    test1_result = test_sanitize_input()

    # Test 2: Search functionality
    test2_result = test_search_functionality()

    # Test 3: NLTK data availability
    test3_result = test_nltk_data_availability()

    # Test 4: Internal cache access
    test4_result = test_internal_cache_access()

    # Test 5: Search debug
    test_search_debug()

    # Summary
    print("=" * 60)
    print("📊 Search Debug Test Summary")
    print("-" * 40)
    print(f"Input Sanitization: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Search Functionality: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"NLTK Data Availability: {'✅ PASS' if test3_result else '❌ FAIL'}")
    print(f"Internal Cache Access: {'✅ PASS' if test4_result else '❌ FAIL'}")

    overall_result = test1_result and test2_result and test3_result and test4_result
    print(
        f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}"
    )

    if overall_result:
        print("\n🎉 Search debug tests passed!")
        print("Search functionality should be working correctly.")
    else:
        print("\n⚠️  Some search debug tests failed.")
        print("Please check the failed tests above.")

    return overall_result


if __name__ == "__main__":
    asyncio.run(run_all_search_debug_tests())
