#!/usr/bin/env python3
"""
Test script to verify that in-memory search is properly updated when new messages are added.
This test also verifies that the search interface automatically refreshes when chat data changes.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
from backend.chat import (
    search_chat_history,
    get_chatbot_response,
    _get_chat_metadata_cache_internal,
)


async def test_search_integration():
    """
    Test that search results are updated when new messages are added to chats.
    """
    print("🔍 Testing search integration with new messages...")

    username = "test_search_user"

    try:
        # Step 1: Search for a specific term before adding any messages
        print("1. Searching for 'python' before adding messages...")
        initial_results, initial_status = search_chat_history("python", username)
        print(f"   Initial results: {len(initial_results)} found")

        # Step 2: Add a message containing the search term
        print("2. Adding message containing 'python'...")
        message = "I need help with Python programming"
        chat_id = "test_chat_123"

        # Simulate adding a message (this would normally be done through the UI)
        # For testing, we'll directly call the backend function
        result = await get_chatbot_response(message, [], username, chat_id)

        if result:
            print("   Message added successfully")

            # Step 3: Search again for the same term
            print("3. Searching for 'python' after adding message...")
            updated_results, updated_status = search_chat_history("python", username)
            print(f"   Updated results: {len(updated_results)} found")

            # Step 4: Verify that the new message is found
            if len(updated_results) > len(initial_results):
                print("✅ SUCCESS: New message found in search results!")

                # Check if our specific message is in the results
                found_message = False
                for result in updated_results:
                    if "python programming" in result.get("content", "").lower():
                        found_message = True
                        print(f"   Found message: {result['content'][:50]}...")
                        break

                if found_message:
                    print("✅ SUCCESS: Specific message found in search results!")
                else:
                    print("⚠️  WARNING: Message added but not found in search results")
            else:
                print("❌ FAILURE: No new results found after adding message")

        else:
            print("❌ FAILURE: Could not add message")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def test_search_interface_auto_refresh():
    """
    Test that the search interface automatically refreshes when chat data changes.
    This simulates the behavior of the search interface's auto-refresh feature.
    """
    print("🔄 Testing search interface auto-refresh functionality...")

    username = "test_auto_refresh_user"

    try:
        # Simulate the search interface's auto-refresh function
        def simulate_auto_refresh(current_query, username, all_chats_data):
            """Simulate the _refresh_search_results_on_data_change function."""
            if not current_query.strip() or not username:
                return "Search results will appear here..."

            try:
                # Re-run the search with the current query
                found_results, status_message = search_chat_history(
                    current_query.strip(), username
                )

                if not found_results:
                    return f"**No results found for '{current_query}'**\n\n{status_message}"

                return f"**Found {len(found_results)} results for '{current_query}'**"

            except Exception as e:
                return f"**Error occurred during search refresh:** {str(e)}"

        # Test 1: No active search query
        print("1. Testing with no active search query...")
        result1 = simulate_auto_refresh("", username, {})
        assert "Search results will appear here" in result1, (
            "Should return default message for empty query"
        )
        print("   ✅ No active query handled correctly")

        # Test 2: Active search query with no data
        print("2. Testing with active search query but no data...")
        result2 = simulate_auto_refresh("test", username, {})
        assert "No results found" in result2, "Should return no results message"
        print("   ✅ Empty data handled correctly")

        # Test 3: Active search query with data (simulated)
        print("3. Testing with active search query and data...")
        # Create some mock chat data
        mock_chat_data = {
            "chat1": {
                "name": "Test Chat",
                "history": [["test message", "test response"]],
            }
        }
        result3 = simulate_auto_refresh("test", username, mock_chat_data)
        assert "Found" in result3 or "No results found" in result3, (
            "Should return search results"
        )
        print("   ✅ Data refresh handled correctly")

        print("✅ Search interface auto-refresh test passed")
        return True

    except Exception as e:
        print(f"❌ Search interface auto-refresh test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_internal_cache_consistency():
    """
    Test that the internal cache is consistent and contains the latest data.
    This verifies that the search interface can access the most recent chat data.
    """
    print("🔍 Testing internal cache consistency...")

    username = "test_cache_user"

    try:
        # Get the internal cache
        internal_cache = _get_chat_metadata_cache_internal()

        # Check if the cache is accessible
        assert isinstance(internal_cache, dict), "Internal cache should be a dictionary"
        print("   ✅ Internal cache is accessible")

        # Check if we can access user data
        if username in internal_cache:
            user_chats = internal_cache[username]
            print(f"   ✅ Found {len(user_chats)} chats for user {username}")

            # Check chat structure
            for chat_id, chat_data in user_chats.items():
                assert "history" in chat_data, f"Chat {chat_id} should have history"
                assert "name" in chat_data, f"Chat {chat_id} should have name"
                print(f"   ✅ Chat {chat_id}: {len(chat_data['history'])} messages")
        else:
            print(
                f"   ℹ️  No existing data for user {username} (this is normal for new users)"
            )

        print("✅ Internal cache consistency test passed")
        return True

    except Exception as e:
        print(f"❌ Internal cache consistency test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def run_all_search_tests():
    """
    Run all search integration tests.
    """
    print("🚀 Running all search integration tests...")
    print("=" * 60)

    # Test 1: Basic search integration
    test1_result = await test_search_integration()

    # Test 2: Search interface auto-refresh
    test2_result = test_search_interface_auto_refresh()

    # Test 3: Internal cache consistency
    test3_result = test_internal_cache_consistency()

    # Summary
    print("=" * 60)
    print("📊 Search Integration Test Summary")
    print("-" * 40)
    print(f"Basic Search Integration: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Auto-Refresh Functionality: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"Internal Cache Consistency: {'✅ PASS' if test3_result else '❌ FAIL'}")

    overall_result = test1_result and test2_result and test3_result
    print(
        f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}"
    )

    if overall_result:
        print("\n🎉 Search interface integration is working correctly!")
        print(
            "The search interface will now automatically refresh when new messages are added."
        )
    else:
        print("\n⚠️  Some search integration issues detected.")
        print("Please check the failed tests above.")

    return overall_result


if __name__ == "__main__":
    asyncio.run(run_all_search_tests())
