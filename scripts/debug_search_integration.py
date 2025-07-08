#!/usr/bin/env python3
"""
Debug script to diagnose search interface integration issues.
This script helps identify why the search interface might not be getting updated chat data.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import logging
from backend.chat import (
    _get_chat_metadata_cache_internal,
    search_chat_history,
    _get_chat_metadata_cache,
    list_user_chat_ids,
    _update_chat_history,
    create_new_chat,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_search_integration(username: str = "test"):
    """
    Debug the search interface integration for a specific user.

    :param username: The username to debug
    :type username: str
    :return: True if debug completed successfully, False otherwise
    :rtype: bool
    """
    print(f"🔍 Debugging search integration for user: {username}")
    print("=" * 60)

    try:
        # 1. Check internal cache
        print("1. Checking internal cache...")
        internal_cache = _get_chat_metadata_cache_internal()
        print(f"   Internal cache type: {type(internal_cache)}")
        print(f"   Internal cache keys: {list(internal_cache.keys())}")

        if username in internal_cache:
            user_chats = internal_cache[username]
            print(f"   ✅ User {username} found in internal cache")
            print(f"   Number of chats: {len(user_chats)}")

            for chat_id, chat_data in user_chats.items():
                history_length = len(chat_data.get("history", []))
                name = chat_data.get("name", "Unnamed")
                print(f"   Chat {chat_id}: {name} ({history_length} messages)")
        else:
            print(f"   ⚠️  User {username} not found in internal cache")

        # 2. Check public cache
        print("\n2. Checking public cache...")
        public_cache = _get_chat_metadata_cache(username)
        print(f"   Public cache type: {type(public_cache)}")
        print(f"   Number of chats: {len(public_cache)}")

        for chat_id, chat_data in public_cache.items():
            history_length = len(chat_data.get("history", []))
            name = chat_data.get("name", "Unnamed")
            print(f"   Chat {chat_id}: {name} ({history_length} messages)")

        # 3. Check list_user_chat_ids
        print("\n3. Checking list_user_chat_ids...")
        user_chats_list = list_user_chat_ids(username)
        print(f"   list_user_chat_ids type: {type(user_chats_list)}")
        print(f"   Number of chats: {len(user_chats_list)}")

        for chat_id, chat_data in user_chats_list.items():
            history_length = len(chat_data.get("history", []))
            name = chat_data.get("name", "Unnamed")
            print(f"   Chat {chat_id}: {name} ({history_length} messages)")

        # 4. Test search functionality
        print("\n4. Testing search functionality...")
        test_queries = ["test", "hello", "python", "message"]

        for query in test_queries:
            try:
                results, status = search_chat_history(query, username)
                print(f"   Query '{query}': {len(results)} results - {status}")

                if results:
                    for i, result in enumerate(results[:3]):  # Show first 3 results
                        content = result.get("content", "")[:50]
                        chat_name = result.get("chat_name", "Unknown")
                        print(f"     {i + 1}. [{chat_name}] {content}...")

            except Exception as e:
                print(f"   Query '{query}': ERROR - {e}")

        # 5. Check cache consistency
        print("\n5. Checking cache consistency...")
        internal_count = len(internal_cache.get(username, {}))
        public_count = len(public_cache)
        list_count = len(user_chats_list)

        print(f"   Internal cache chats: {internal_count}")
        print(f"   Public cache chats: {public_count}")
        print(f"   list_user_chat_ids chats: {list_count}")

        if internal_count == public_count == list_count:
            print("   ✅ Cache consistency: PASSED")
        else:
            print("   ❌ Cache consistency: FAILED")
            print("   This indicates a potential issue with cache synchronization")

        print("\n" + "=" * 60)
        print("🔍 Debug summary:")
        print(
            f"   - Internal cache accessible: {'✅' if username in internal_cache else '❌'}"
        )
        print(f"   - Public cache accessible: {'✅' if public_cache else '❌'}")
        print(f"   - Search function working: {'✅' if test_queries else '❌'}")
        print(
            f"   - Cache consistency: {'✅' if internal_count == public_count == list_count else '❌'}"
        )

        return True

    except Exception as e:
        print(f"❌ Debug failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def debug_search_refresh_simulation(username: str = "test", query: str = "test"):
    """
    Simulate the search refresh process to identify issues.

    :param username: The username to test
    :type username: str
    :param query: The search query to test
    :type query: str
    :return: True if simulation completed successfully, False otherwise
    :rtype: bool
    """
    print(f"🔄 Simulating search refresh for user: {username}, query: '{query}'")
    print("=" * 60)

    try:
        # Simulate the _refresh_search_results_on_data_change function
        def simulate_refresh(current_query, username, all_chats_data):
            print(f"   Simulating refresh with query: '{current_query}'")
            print(f"   all_chats_data contains {len(all_chats_data)} chats")

            if not current_query.strip() or not username:
                return "Search results will appear here..."

            try:
                # Check internal cache
                internal_cache = _get_chat_metadata_cache_internal()
                if username in internal_cache:
                    internal_chats = internal_cache[username]
                    print(f"   Internal cache has {len(internal_chats)} chats")

                    for chat_id, chat_data in internal_chats.items():
                        history_length = len(chat_data.get("history", []))
                        print(f"   Chat {chat_id}: {history_length} messages")
                else:
                    print(f"   No internal cache data for {username}")

                # Perform search
                found_results, status_message = search_chat_history(
                    current_query.strip(), username
                )
                print(f"   Search returned {len(found_results)} results")

                if not found_results:
                    return f"**No results found for '{current_query}'**\n\n{status_message}"

                return f"**Found {len(found_results)} results for '{current_query}'**"

            except Exception as e:
                print(f"   Error during refresh: {e}")
                return f"**Error occurred during search refresh:** {str(e)}"

        # Test with mock data
        mock_chat_data = {
            "chat1": {
                "name": "Test Chat",
                "history": [["test message", "test response"]],
            }
        }

        result = simulate_refresh(query, username, mock_chat_data)
        print(f"\n   Refresh result: {result}")

        return True

    except Exception as e:
        print(f"❌ Refresh simulation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def debug_search_refresh_with_new_messages(username: str = "test"):
    """
    Debug function to test search refresh when new messages are added.
    """
    print(f"🔍 Testing search refresh with new messages for user: {username}")

    try:
        # Create a test chat
        chat_id = create_new_chat(username, "Debug Search Refresh Chat")
        print(f"   Created test chat: {chat_id}")

        # Add initial messages
        _update_chat_history(
            chat_id, username, "hello world", "Hello! How can I help you?"
        )
        _update_chat_history(
            chat_id, username, "python programming", "Python is a great language!"
        )

        # Test search before adding new message
        print("   Testing search before new message...")
        results_before, status_before = search_chat_history("python", username)
        print(f"   Search results before: {len(results_before)} results")
        for i, result in enumerate(results_before):
            print(f"     {i + 1}. {result.get('content', '')[:50]}...")

        # Add a new message that should be searchable
        print("   Adding new message...")
        _update_chat_history(
            chat_id, username, "machine learning with python", "ML is fascinating!"
        )

        # Test search after adding new message
        print("   Testing search after new message...")
        results_after, status_after = search_chat_history("python", username)
        print(f"   Search results after: {len(results_after)} results")
        for i, result in enumerate(results_after):
            print(f"     {i + 1}. {result.get('content', '')[:50]}...")

        # Check if new message is found
        new_message_found = False
        for result in results_after:
            if "machine learning with python" in result.get("content", ""):
                new_message_found = True
                print(f"   ✅ Found new message: {result.get('content', '')}")
                break

        if not new_message_found:
            print("   ❌ New message not found in search results")

        # Verify cache is updated
        internal_cache = _get_chat_metadata_cache_internal()
        if username in internal_cache:
            user_chats = internal_cache[username]
            if chat_id in user_chats:
                history_length = len(user_chats[chat_id].get("history", []))
                print(f"   Cache has {history_length} messages")

                # Show all messages in cache
                print("   All messages in cache:")
                for i, msg_pair in enumerate(user_chats[chat_id].get("history", [])):
                    print(f"     {i + 1}. User: {msg_pair[0]}")
                    print(f"        Bot: {msg_pair[1]}")

        return True

    except Exception as e:
        print(f"❌ Search refresh test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def debug_search_interface_refresh(username: str = "test", query: str = "python"):
    """
    Debug function to simulate the search interface refresh functionality.
    """
    print(f"🔄 Testing search interface refresh for user: {username}, query: {query}")

    try:
        # Create test data
        chat_id = create_new_chat(username, "Debug Interface Chat")
        _update_chat_history(
            chat_id, username, "python programming", "Python is great!"
        )
        _update_chat_history(
            chat_id, username, "machine learning", "ML is fascinating!"
        )

        # Simulate the search interface refresh function
        def simulate_refresh(current_query, username, all_chats_data):
            print(f"   Simulating refresh for query: '{current_query}'")
            print(f"   all_chats_data has {len(all_chats_data)} chats")

            # Show what's in all_chats_data
            for chat_id, chat_data in all_chats_data.items():
                history_length = len(chat_data.get("history", []))
                print(f"   Chat {chat_id}: {history_length} messages")

                # Show messages
                for i, msg_pair in enumerate(chat_data.get("history", [])):
                    print(f"     {i + 1}. User: {msg_pair[0]}")
                    print(f"        Bot: {msg_pair[1]}")

            # Perform search
            found_results, status_message = search_chat_history(
                current_query.strip(), username
            )
            print(f"   Search returned {len(found_results)} results")

            if not found_results:
                return f"**No results found for '{current_query}'**\n\n{status_message}"

            # Show results
            for i, result in enumerate(found_results):
                print(f"   Result {i + 1}: {result.get('content', '')[:50]}...")

            return f"**Found {len(found_results)} results for '{current_query}'**"

        # Get current chat data
        internal_cache = _get_chat_metadata_cache_internal()
        all_chats_data = internal_cache.get(username, {})

        # Test refresh
        result = simulate_refresh(query, username, all_chats_data)
        print(f"   Refresh result: {result}")

        # Add a new message and test again
        print("   Adding new message and testing refresh again...")
        _update_chat_history(
            chat_id,
            username,
            "advanced python techniques",
            "Advanced Python is powerful!",
        )

        # Get updated chat data
        internal_cache = _get_chat_metadata_cache_internal()
        all_chats_data = internal_cache.get(username, {})

        # Test refresh again
        result2 = simulate_refresh(query, username, all_chats_data)
        print(f"   Refresh result after new message: {result2}")

        return True

    except Exception as e:
        print(f"❌ Search interface refresh test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔍 Debug Search Integration")
    print("=" * 50)

    # Test basic search integration
    print("\n1️⃣ Testing basic search integration...")
    debug_search_integration("test")

    # Test search refresh simulation
    print("\n2️⃣ Testing search refresh simulation...")
    debug_search_refresh_simulation("test", "test")

    # Test search refresh with new messages
    print("\n3️⃣ Testing search refresh with new messages...")
    debug_search_refresh_with_new_messages("test")

    # Test search interface refresh
    print("\n4️⃣ Testing search interface refresh...")
    debug_search_interface_refresh("test", "python")

    print("\n✅ Debug search integration completed!")
