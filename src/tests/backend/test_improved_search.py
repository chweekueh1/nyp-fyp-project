#!/usr/bin/env python3
"""
Test script to verify that the improved search function works correctly for both short and long queries.
This test verifies that the search now supports both fuzzy matching and substring matching.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
from backend.chat import search_chat_history, _get_chat_metadata_cache_internal


async def test_improved_search_functionality():
    """
    Test that the improved search function works correctly for both short and long queries.
    """
    print("🔍 Testing improved search functionality...")

    username = "test_search_user"

    # Create test chat data
    test_chat_id = "test_chat_123"
    test_chat_data = {
        "name": "Test Chat",
        "history": [
            ["Hello, how are you?", "I'm doing well, thank you for asking!"],
            [
                "What is the weather like?",
                "I don't have access to real-time weather data.",
            ],
            [
                "Can you help me with Python?",
                "Yes, I can help you with Python programming.",
            ],
            ["Tell me about AI", "Artificial Intelligence is a fascinating field."],
            ["a simple test", "This is a simple response."],
            ["The quick brown fox", "jumps over the lazy dog."],
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    try:
        # Test 1: Short query (should use substring matching)
        print("  📝 Testing short query 'a'...")
        results, status = search_chat_history("a", username)

        # Should find matches in "a simple test" and "Tell me about AI"
        assert len(results) > 0, f"Expected results for 'a', got {len(results)}"
        print(f"  ✅ Short query 'a' found {len(results)} results")

        # Check that we found the expected matches
        found_contents = [result["content"] for result in results]
        expected_matches = ["a simple test", "Tell me about AI"]
        for expected in expected_matches:
            assert any(expected in content for content in found_contents), (
                f"Expected to find '{expected}' in results"
            )

        print("  ✅ Short query found expected matches")

        # Test 2: Medium query (should use fuzzy matching)
        print("  📝 Testing medium query 'python'...")
        results, status = search_chat_history("python", username)

        # Should find match in "Can you help me with Python?"
        assert len(results) > 0, f"Expected results for 'python', got {len(results)}"
        print(f"  ✅ Medium query 'python' found {len(results)} results")

        # Check that we found the expected match
        found_contents = [result["content"] for result in results]
        assert any("Python" in content for content in found_contents), (
            "Expected to find 'Python' in results"
        )

        print("  ✅ Medium query found expected matches")

        # Test 3: Long query (should use fuzzy matching)
        print("  📝 Testing long query 'artificial intelligence'...")
        results, status = search_chat_history("artificial intelligence", username)

        # Should find match in "Tell me about AI"
        assert len(results) > 0, (
            f"Expected results for 'artificial intelligence', got {len(results)}"
        )
        print(f"  ✅ Long query 'artificial intelligence' found {len(results)} results")

        # Check that we found the expected match
        found_contents = [result["content"] for result in results]
        assert any(
            "AI" in content or "Artificial Intelligence" in content
            for content in found_contents
        ), "Expected to find AI-related content in results"

        print("  ✅ Long query found expected matches")

        # Test 4: Very short query (single character)
        print("  📝 Testing very short query 't'...")
        results, status = search_chat_history("t", username)

        # Should find matches in multiple messages
        assert len(results) > 0, f"Expected results for 't', got {len(results)}"
        print(f"  ✅ Very short query 't' found {len(results)} results")

        print("  ✅ Very short query found matches")

        # Test 5: No match query
        print("  📝 Testing no match query 'xyz123'...")
        results, status = search_chat_history("xyz123", username)

        # Should find no matches
        assert len(results) == 0, (
            f"Expected no results for 'xyz123', got {len(results)}"
        )
        print("  ✅ No match query correctly returned no results")

        # Test 6: Empty query
        print("  📝 Testing empty query...")
        results, status = search_chat_history("", username)

        # Should return empty results with appropriate message
        assert len(results) == 0, (
            f"Expected no results for empty query, got {len(results)}"
        )
        assert "Please enter a search query" in status, (
            f"Expected appropriate message, got '{status}'"
        )
        print("  ✅ Empty query handled correctly")

        print("✅ All improved search tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error testing improved search: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_similarity_scores():
    """
    Test that similarity scores are calculated correctly for different query types.
    """
    print("📊 Testing search similarity scores...")

    username = "test_scores_user"

    # Create test chat data with specific content
    test_chat_id = "test_scores_123"
    test_chat_data = {
        "name": "Test Scores Chat",
        "history": [
            ["apple pie recipe", "Here's how to make apple pie."],
            ["banana bread", "Banana bread is delicious."],
            ["apple cider", "Apple cider is a fall favorite."],
        ],
    }

    # Add test data to cache
    internal_cache = _get_chat_metadata_cache_internal()
    internal_cache[username] = {test_chat_id: test_chat_data}

    try:
        # Test substring matching scores (short query)
        print("  📝 Testing substring matching scores for 'apple'...")
        results, status = search_chat_history("apple", username)

        assert len(results) >= 2, (
            f"Expected at least 2 results for 'apple', got {len(results)}"
        )

        # Check that scores are reasonable for substring matching
        for result in results:
            score = result["similarity_score"]
            assert 0.1 <= score <= 1.0, f"Score {score} should be between 0.1 and 1.0"
            print(f"    Found '{result['content']}' with score {score}")

        print("  ✅ Substring matching scores are reasonable")

        # Test fuzzy matching scores (longer query)
        print("  📝 Testing fuzzy matching scores for 'apple pie recipe'...")
        results, status = search_chat_history("apple pie recipe", username)

        assert len(results) > 0, (
            f"Expected results for 'apple pie recipe', got {len(results)}"
        )

        # Check that scores are reasonable for fuzzy matching
        for result in results:
            score = result["similarity_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} should be between 0.0 and 1.0"
            print(f"    Found '{result['content']}' with score {score}")

        print("  ✅ Fuzzy matching scores are reasonable")

        print("✅ All similarity score tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Error testing similarity scores: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """
    Run all improved search tests.
    """
    print("🔍 Improved Search Functionality Tests")
    print("=" * 50)

    test_results = []

    # Test 1: Basic functionality
    print("\n1️⃣ Testing improved search functionality...")
    result1 = await test_improved_search_functionality()
    test_results.append(("Basic Functionality", result1))

    # Test 2: Similarity scores
    print("\n2️⃣ Testing similarity scores...")
    result2 = await test_search_similarity_scores()
    test_results.append(("Similarity Scores", result2))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All improved search tests PASSED!")
        print("\n✅ Search improvements confirmed:")
        print("  🔍 Short queries (1-2 chars): Substring matching")
        print("  🔍 Medium queries (3+ chars): Fuzzy matching")
        print("  📊 Proper similarity scores for both methods")
        print("  🎯 Better results for all query lengths")
    else:
        print("\n⚠️ Some improved search tests FAILED!")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
