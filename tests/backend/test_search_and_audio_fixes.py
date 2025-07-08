#!/usr/bin/env python3
"""
Test script to verify that the search function is using difflib correctly and audio transcription fixes.
This test verifies both the hybrid search algorithm and audio transcription error handling.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
import difflib
from unittest.mock import patch, MagicMock
from backend.chat import (
    search_chat_history,
    _get_chat_metadata_cache_internal,
    _update_chat_history,
    create_new_chat,
)
from backend.audio import transcribe_audio


async def test_search_difflib_integration():
    """
    Test that the search function is using difflib correctly for fuzzy matching.
    """
    print("🔍 Testing search difflib integration...")

    username = "test_difflib_user"

    # Create test chat data with specific content for difflib testing
    test_chat_id = "test_difflib_123"
    test_chat_data = {
        "name": "Test Difflib Chat",
        "history": [
            ["python programming", "Python is a great programming language."],
            ["artificial intelligence", "AI is transforming the world."],
            ["machine learning", "ML is a subset of AI."],
            ["data science", "Data science combines statistics and programming."],
            [
                "natural language processing",
                "NLP helps computers understand human language.",
            ],
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    try:
        # Test 1: Verify difflib is imported and working
        print("  📝 Testing difflib import and basic functionality...")

        # Test basic difflib functionality
        test_string1 = "python programming"
        test_string2 = "pythn programing"  # Intentional typos
        similarity = difflib.SequenceMatcher(None, test_string1, test_string2).ratio()

        assert 0.0 <= similarity <= 1.0, (
            f"Similarity score should be between 0 and 1, got {similarity}"
        )
        assert similarity > 0.5, (
            f"Similarity should be high for similar strings, got {similarity}"
        )
        print(f"  ✅ Difflib similarity test passed: {similarity:.3f}")

        # Test 2: Verify search uses difflib for longer queries (3+ chars)
        print("  📝 Testing search with difflib for longer queries...")

        # Test with typo in query
        results, status = search_chat_history("pythn programing", username)

        # Should find match in "python programming" using fuzzy matching
        assert len(results) > 0, (
            f"Expected results for 'pythn programing', got {len(results)}"
        )
        print(f"  ✅ Fuzzy search found {len(results)} results for typo query")

        # Check that we found the expected match
        found_contents = [result["content"] for result in results]
        assert any("python programming" in content for content in found_contents), (
            "Expected to find 'python programming' in results"
        )

        # Check similarity scores are reasonable
        for result in results:
            score = result["similarity_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} should be between 0.0 and 1.0"
            print(f"    Found '{result['content']}' with score {score}")

        # Test 3: Verify search uses substring matching for short queries (1-2 chars)
        print("  📝 Testing search with substring matching for short queries...")

        results, status = search_chat_history("ai", username)

        # Should find match in "artificial intelligence" using substring matching
        assert len(results) > 0, f"Expected results for 'ai', got {len(results)}"
        print(f"  ✅ Substring search found {len(results)} results for short query")

        # Check that we found the expected match
        found_contents = [result["content"] for result in results]
        assert any(
            "artificial intelligence" in content for content in found_contents
        ), "Expected to find 'artificial intelligence' in results"

        # Check similarity scores are reasonable for substring matching
        for result in results:
            score = result["similarity_score"]
            assert 0.1 <= score <= 1.0, (
                f"Score {score} should be between 0.1 and 1.0 for substring matching"
            )
            print(f"    Found '{result['content']}' with score {score}")

        # Test 4: Verify search algorithm selection logic
        print("  📝 Testing search algorithm selection logic...")

        # Test boundary conditions
        short_results, _ = search_chat_history("a", username)
        medium_results, _ = search_chat_history("ai", username)
        long_results, _ = search_chat_history("artificial intelligence", username)

        # All should find results
        assert len(short_results) > 0, "Short query should find results"
        assert len(medium_results) > 0, "Medium query should find results"
        assert len(long_results) > 0, "Long query should find results"

        print("  ✅ All query length categories found results")

        print("✅ All search difflib integration tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error testing search difflib integration: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_audio_transcription_fixes():
    """
    Test that the audio transcription fixes are working correctly.
    """
    print("🎤 Testing audio transcription fixes...")

    try:
        # Test 1: Verify client initialization check
        print("  📝 Testing client initialization check...")

        # Mock the client as None to test the error handling
        with patch("backend.audio.client", None):
            result = transcribe_audio("nonexistent_file.wav")
            assert "OpenAI client not initialized" in result, (
                f"Expected client error message, got: {result}"
            )
            print("  ✅ Client initialization check working")

        # Test 2: Verify file existence check
        print("  📝 Testing file existence check...")

        # Mock the client as a valid client
        mock_client = MagicMock()
        with patch("backend.audio.client", mock_client):
            result = transcribe_audio("nonexistent_file.wav")
            assert "File not found" in result, (
                f"Expected file not found message, got: {result}"
            )
            print("  ✅ File existence check working")

        # Test 3: Verify file size check
        print("  📝 Testing file size check...")

        # Create a mock file that's too large
        with patch("backend.audio.client", mock_client):
            with patch("os.path.exists", return_value=True):
                with patch("os.access", return_value=True):
                    with patch(
                        "os.path.getsize", return_value=30 * 1024 * 1024
                    ):  # 30MB
                        result = transcribe_audio("large_file.wav")
                        assert "File too large" in result, (
                            f"Expected file too large message, got: {result}"
                        )
                        print("  ✅ File size check working")

        # Test 4: Verify successful transcription (when client is available)
        print("  📝 Testing successful transcription...")

        # Mock successful transcription
        mock_response = MagicMock()
        mock_response.text = "This is a test transcription"
        mock_client.audio.transcriptions.create.return_value = mock_response

        with patch("backend.audio.client", mock_client):
            with patch("os.path.exists", return_value=True):
                with patch("os.access", return_value=True):
                    with patch("os.path.getsize", return_value=1024):  # 1KB
                        result = transcribe_audio("test_file.wav")
                        assert result == "This is a test transcription", (
                            f"Expected transcription text, got: {result}"
                        )
                        print("  ✅ Successful transcription working")

        print("✅ All audio transcription fix tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error testing audio transcription fixes: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_algorithm_verification():
    """
    Test to verify the search algorithm is working correctly with both methods.
    """
    print("🔍 Testing search algorithm verification...")

    username = "test_algorithm_user"

    # Create test chat data
    test_chat_id = "test_algorithm_123"
    test_chat_data = {
        "name": "Test Algorithm Chat",
        "history": [
            ["hello world", "Hello! How can I help you today?"],
            ["python code", "Here's some Python code for you."],
            ["machine learning", "ML is fascinating."],
            ["a simple test", "This is a simple test message."],
            ["artificial intelligence", "AI is the future."],
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    try:
        # Test 1: Verify substring matching for single character
        print("  📝 Testing substring matching for single character...")
        results, status = search_chat_history("a", username)

        # Should find "a simple test" and "artificial intelligence"
        assert len(results) >= 2, (
            f"Expected at least 2 results for 'a', got {len(results)}"
        )

        found_contents = [result["content"] for result in results]
        assert any("a simple test" in content for content in found_contents), (
            "Expected to find 'a simple test'"
        )
        assert any(
            "artificial intelligence" in content for content in found_contents
        ), "Expected to find 'artificial intelligence'"

        print("  ✅ Substring matching for single character working")

        # Test 2: Verify substring matching for two characters
        print("  📝 Testing substring matching for two characters...")
        results, status = search_chat_history("he", username)

        # Should find "hello world"
        assert len(results) > 0, f"Expected results for 'he', got {len(results)}"

        found_contents = [result["content"] for result in results]
        assert any("hello world" in content for content in found_contents), (
            "Expected to find 'hello world'"
        )

        print("  ✅ Substring matching for two characters working")

        # Test 3: Verify fuzzy matching for longer queries
        print("  📝 Testing fuzzy matching for longer queries...")
        results, status = search_chat_history("pythn", username)

        # Should find "python code" using fuzzy matching
        assert len(results) > 0, f"Expected results for 'pythn', got {len(results)}"

        found_contents = [result["content"] for result in results]
        assert any("python code" in content for content in found_contents), (
            "Expected to find 'python code'"
        )

        print("  ✅ Fuzzy matching for longer queries working")

        # Test 4: Verify similarity score ranges
        print("  📝 Testing similarity score ranges...")

        # Test substring matching scores
        results, _ = search_chat_history("a", username)
        for result in results:
            score = result["similarity_score"]
            assert 0.1 <= score <= 1.0, (
                f"Substring matching score {score} should be between 0.1 and 1.0"
            )

        # Test fuzzy matching scores
        results, _ = search_chat_history("pythn", username)
        for result in results:
            score = result["similarity_score"]
            assert 0.0 <= score <= 1.0, (
                f"Fuzzy matching score {score} should be between 0.0 and 1.0"
            )

        print("  ✅ Similarity score ranges correct")

        print("✅ All search algorithm verification tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error testing search algorithm verification: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_updates_with_new_messages():
    """
    Test that the search interface properly updates when new messages are added.
    This verifies that the metadata cache is being updated correctly.
    """
    print("🔍 Testing search updates with new messages...")

    username = "test_search_update_user"

    try:
        # Create a test chat
        chat_id = create_new_chat(username, "Test Search Update Chat")
        print(f"   Created test chat: {chat_id}")

        # Add initial messages
        _update_chat_history(
            chat_id, username, "hello world", "Hello! How can I help you?"
        )
        _update_chat_history(
            chat_id, username, "python programming", "Python is a great language!"
        )

        # Test search before adding new message
        results_before, status_before = search_chat_history("python", username)
        print(f"   Search before new message: {len(results_before)} results")

        # Add a new message that should be searchable
        _update_chat_history(
            chat_id, username, "machine learning with python", "ML is fascinating!"
        )

        # Test search after adding new message
        results_after, status_after = search_chat_history("python", username)
        print(f"   Search after new message: {len(results_after)} results")

        # Verify that the search found the new message
        assert len(results_after) >= len(results_before), (
            "Search should find at least as many results after adding message"
        )

        # Check if the new message is in the results
        new_message_found = False
        for result in results_after:
            if "machine learning with python" in result.get("content", ""):
                new_message_found = True
                break

        assert new_message_found, "New message should be found in search results"
        print("   ✅ New message found in search results")

        # Verify cache is updated
        internal_cache = _get_chat_metadata_cache_internal()
        if username in internal_cache:
            user_chats = internal_cache[username]
            if chat_id in user_chats:
                history_length = len(user_chats[chat_id].get("history", []))
                assert history_length == 3, f"Expected 3 messages, got {history_length}"
                print(f"   ✅ Cache updated correctly: {history_length} messages")

        print("✅ Search updates with new messages test passed")
        return True

    except Exception as e:
        print(f"❌ Search updates with new messages test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_refresh_integration():
    """
    Test the complete search refresh integration to ensure it works end-to-end.
    """
    print("🔄 Testing search refresh integration...")

    username = "test_refresh_integration_user"

    try:
        # Create a test chat
        chat_id = create_new_chat(username, "Test Refresh Integration Chat")
        print(f"   Created test chat: {chat_id}")

        # Add some test messages
        _update_chat_history(chat_id, username, "initial message", "Initial response")
        _update_chat_history(
            chat_id, username, "searchable content", "This should be found"
        )

        # Test the search function directly
        results, status = search_chat_history("searchable", username)
        print(f"   Direct search results: {len(results)} results")
        assert len(results) > 0, "Should find searchable content"

        # Add a new message
        _update_chat_history(
            chat_id, username, "new searchable message", "New response"
        )

        # Test search again to ensure it finds the new message
        results_after, status_after = search_chat_history("searchable", username)
        print(f"   Search after new message: {len(results_after)} results")
        assert len(results_after) >= len(results), (
            "Should find at least as many results"
        )

        # Check if new message is found
        new_message_found = False
        for result in results_after:
            if "new searchable message" in result.get("content", ""):
                new_message_found = True
                break

        assert new_message_found, "New message should be found in search results"
        print("   ✅ New message found in search results")

        print("✅ Search refresh integration test passed")
        return True

    except Exception as e:
        print(f"❌ Search refresh integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """
    Run all tests for search and audio fixes.
    """
    print("🔍 Search and Audio Fixes Verification Tests")
    print("=" * 60)

    test_results = []

    # Test 1: Search difflib integration
    print("\n1️⃣ Testing search difflib integration...")
    result1 = await test_search_difflib_integration()
    test_results.append(("Search Difflib Integration", result1))

    # Test 2: Audio transcription fixes
    print("\n2️⃣ Testing audio transcription fixes...")
    result2 = await test_audio_transcription_fixes()
    test_results.append(("Audio Transcription Fixes", result2))

    # Test 3: Search algorithm verification
    print("\n3️⃣ Testing search algorithm verification...")
    result3 = await test_search_algorithm_verification()
    test_results.append(("Search Algorithm Verification", result3))

    # Test 4: Search updates with new messages
    print("\n4️⃣ Testing search updates with new messages...")
    result4 = await test_search_updates_with_new_messages()
    test_results.append(("Search Updates with New Messages", result4))

    # Test 5: Search refresh integration
    print("\n5️⃣ Testing search refresh integration...")
    result5 = await test_search_refresh_integration()
    test_results.append(("Search Refresh Integration", result5))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All search and audio fix tests PASSED!")
        print("\n✅ Fixes confirmed:")
        print("  🔍 Search function correctly uses difflib for fuzzy matching")
        print("  🔍 Search function uses substring matching for short queries")
        print("  🎤 Audio transcription has proper error handling")
        print("  🎤 Audio transcription checks client initialization")
        print("  🎤 Audio transcription validates file existence and size")
        print("  📊 Both search methods provide appropriate similarity scores")
    else:
        print("\n⚠️ Some search and audio fix tests FAILED!")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
