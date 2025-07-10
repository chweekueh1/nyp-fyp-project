#!/usr/bin/env python3
"""
Standalone test script to debug search functionality.
This file has been moved from the root directory to tests/backend/ for better organization.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend.chat import search_chat_history, _get_chat_metadata_cache_internal
from backend.utils import sanitize_input
import difflib


def test_search_debug():
    """Test search functionality with debug output."""
    print("🔍 Testing search functionality with debug output...")

    username = "test"

    # Get the current chat data
    internal_cache = _get_chat_metadata_cache_internal()
    if username not in internal_cache:
        print(f"❌ No chat data found for user '{username}'")
        return

    user_chats = internal_cache[username]
    print(f"✅ Found {len(user_chats)} chats for user '{username}'")

    # Test queries that should work
    test_queries = [
        "decision",
        "decision-making",
        "diagram",
        "reaching the end",
        "test",
    ]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")

        # Test sanitized vs unsanitized
        sanitized = sanitize_input(query)
        print(f"  Original query: '{query}'")
        print(f"  Sanitized query: '{sanitized}'")

        # Test search with original query
        results, status = search_chat_history(query, username)
        print(f"  Results with original query: {len(results)} found")

        # Test search with sanitized query
        results_sanitized, status_sanitized = search_chat_history(sanitized, username)
        print(f"  Results with sanitized query: {len(results_sanitized)} found")

        # Show some sample content from chats
        for chat_id, chat_data in user_chats.items():
            history = chat_data.get("history", [])
            if history:
                print(
                    f"  Chat '{chat_data.get('name', 'Unknown')}' has {len(history)} messages"
                )
                # Show first few messages
                for i, (user_msg, bot_msg) in enumerate(history[:2]):
                    print(
                        f"    Message {i}: User='{user_msg[:50]}...', Bot='{bot_msg[:50]}...'"
                    )

                    # Test direct matching
                    if query.lower() in user_msg.lower():
                        print("    ✅ Direct match found in user message!")
                    if query.lower() in bot_msg.lower():
                        print("    ✅ Direct match found in bot message!")

                    # Test fuzzy matching
                    user_score = difflib.SequenceMatcher(
                        None, query.lower(), user_msg.lower()
                    ).ratio()
                    bot_score = difflib.SequenceMatcher(
                        None, query.lower(), bot_msg.lower()
                    ).ratio()
                    print(
                        f"    Fuzzy scores - User: {user_score:.3f}, Bot: {bot_score:.3f}"
                    )


def test_sanitize_input():
    """Test the sanitize_input function to see if it's causing issues."""
    print("\n🧪 Testing sanitize_input function...")

    test_inputs = [
        "decision",
        "decision-making",
        "diagram",
        "reaching the end",
        "test",
        "hello world",
        "data security",
        "database design",
    ]

    for test_input in test_inputs:
        sanitized = sanitize_input(test_input)
        print(f"  '{test_input}' -> '{sanitized}'")
        if test_input != sanitized:
            print("    ⚠️  Input was modified!")


if __name__ == "__main__":
    test_sanitize_input()
    test_search_debug()
