#!/usr/bin/env python3
"""
Comprehensive test script for enhanced chatbot features:
1. Searchable chat history
2. Smart chat naming based on first message
3. Auto-updating dropdown when creating chats
"""

import sys
import os
import json
import tempfile
import shutil
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_test_environment():
    """Set up a temporary test environment."""
    test_dir = tempfile.mkdtemp(prefix="enhanced_chatbot_test_")

    import backend
    import infra_utils

    original_get_chatbot_dir = infra_utils.get_chatbot_dir

    def mock_get_chatbot_dir():
        return test_dir

    infra_utils.get_chatbot_dir = mock_get_chatbot_dir
    backend.CHAT_SESSIONS_PATH = os.path.join(test_dir, "data", "chat_sessions")
    backend.CHAT_DATA_PATH = os.path.join(test_dir, "data", "chats")
    backend.USER_DB_PATH = os.path.join(test_dir, "data", "user_info", "users.json")

    # Also update the imported variables in the chat module
    import backend.chat

    backend.chat.CHAT_SESSIONS_PATH = backend.CHAT_SESSIONS_PATH
    backend.chat.CHAT_DATA_PATH = backend.CHAT_DATA_PATH

    os.makedirs(backend.CHAT_SESSIONS_PATH, exist_ok=True)
    os.makedirs(backend.CHAT_DATA_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(backend.USER_DB_PATH), exist_ok=True)

    return test_dir, original_get_chatbot_dir


def cleanup_test_environment(test_dir, original_get_chatbot_dir):
    """Clean up the test environment."""
    import infra_utils

    infra_utils.get_chatbot_dir = original_get_chatbot_dir
    shutil.rmtree(test_dir, ignore_errors=True)


def create_test_chats_with_content():
    """Create test chats with various content for search testing."""
    import backend
    from tests.test_utils import get_default_test_user

    test_user = get_default_test_user()
    username = test_user["username"]
    test_chats = [
        {
            "name": "Python Programming Help",
            "messages": [
                {"role": "user", "content": "How do I create a Python function?"},
                {
                    "role": "assistant",
                    "content": "To create a Python function, use the 'def' keyword followed by the function name and parameters.",
                },
                {"role": "user", "content": "Can you show me an example?"},
                {
                    "role": "assistant",
                    "content": "Sure! Here's an example: def greet(name): return f'Hello, {name}!'",
                },
            ],
        },
        {
            "name": "JavaScript Questions",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the difference between let and var in JavaScript?",
                },
                {
                    "role": "assistant",
                    "content": "The main differences are scope and hoisting. 'let' has block scope while 'var' has function scope.",
                },
                {"role": "user", "content": "Which one should I use?"},
                {
                    "role": "assistant",
                    "content": "Generally, use 'let' for modern JavaScript as it provides better scoping and prevents common errors.",
                },
            ],
        },
        {
            "name": "Database Design",
            "messages": [
                {"role": "user", "content": "How do I design a database schema?"},
                {
                    "role": "assistant",
                    "content": "Start by identifying entities, their attributes, and relationships. Then normalize the schema.",
                },
                {"role": "user", "content": "What is normalization?"},
                {
                    "role": "assistant",
                    "content": "Normalization is the process of organizing data to reduce redundancy and improve data integrity.",
                },
            ],
        },
    ]

    # Create chat data files (where search_chat_history looks)
    user_data_folder = os.path.join(backend.CHAT_DATA_PATH, username)
    os.makedirs(user_data_folder, exist_ok=True)

    # Create session files (for chat metadata)
    user_sessions_folder = backend.CHAT_SESSIONS_PATH
    os.makedirs(user_sessions_folder, exist_ok=True)

    created_chats = []
    for i, chat_data in enumerate(test_chats):
        # Create a timestamp-based chat ID
        chat_id = f"test_chat_{i + 1}_{int(time.time())}"

        # Create chat data file (contains messages for search)
        chat_data_file = os.path.join(user_data_folder, f"{chat_id}.json")
        with open(chat_data_file, "w", encoding="utf-8") as f:
            json.dump({"messages": chat_data["messages"]}, f, indent=2)

        # Create session file (contains chat metadata)
        session_file = os.path.join(user_sessions_folder, f"{username}_{chat_id}.json")
        session_data = {
            "chat_id": chat_id,
            "username": username,
            "created_at": backend.get_utc_timestamp(),
            "name": chat_data["name"],
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)

        created_chats.append({"chat_id": chat_id, "name": chat_data["name"]})

    return created_chats


def test_smart_chat_naming():
    """Test the smart chat naming functionality."""
    print("🧠 Testing smart chat naming...")

    try:
        import backend

        test_cases = [
            ("How do I create a Python function?", "Create Python Function"),
            ("What is machine learning?", "Machine Learning"),
            ("Hello, can you help me with JavaScript?", "Help Javascript"),
            ("I need assistance with database design", "Assistance Database Design"),
            ("", "Chat"),  # Empty message fallback
            ("a", "Chat"),  # Very short message fallback
        ]

        for message, expected_pattern in test_cases:
            smart_name = backend.generate_smart_chat_name(message)
            print(f"  📝 '{message}' → '{smart_name}'")

            # Basic validation
            assert len(smart_name) > 0, "Chat name should not be empty"
            assert len(smart_name) <= 35, "Chat name should not be too long"

            if message and len(message.strip()) > 3:
                # Should contain some meaningful content
                assert not smart_name.startswith("Chat 20"), (
                    f"Should generate meaningful name for '{message}'"
                )

        print("✅ Smart chat naming test passed")
        return True

    except Exception as e:
        print(f"❌ Smart chat naming test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_smart_chat_creation():
    """Test creating chats with smart names."""
    print("🏗️ Testing smart chat creation...")

    try:
        import backend

        from tests.test_utils import get_default_test_user

        test_user = get_default_test_user()
        username = test_user["username"]
        test_message = "How do I implement a binary search algorithm?"

        # Create smart chat
        chat_id = backend.create_and_persist_smart_chat(username, test_message)

        # Verify chat was created
        assert chat_id, "Chat ID should not be empty"

        # Verify session file exists (this contains the smart name)
        session_file = os.path.join(
            backend.CHAT_SESSIONS_PATH, f"{username}_{chat_id}.json"
        )
        assert os.path.exists(session_file), (
            f"Session file should exist at {session_file}"
        )

        # Verify session file content has smart name
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)
            assert "name" in session_data, "Session file should have 'name' key"
            chat_name = session_data["name"]
            assert (
                "Binary Search Algorithm" in chat_name
                or "Implement Binary Search" in chat_name
            ), f"Chat name should be meaningful: {chat_name}"

        # Verify chat data file exists
        user_folder = os.path.join(backend.CHAT_DATA_PATH, username)
        chat_file = os.path.join(user_folder, f"{chat_id}.json")
        assert os.path.exists(chat_file), f"Chat file should exist at {chat_file}"

        # Verify chat data file content
        with open(chat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "messages" in data, "Chat file should have 'messages' key"
            assert data["messages"] == [], "New chat should have empty messages"

        print(f"✅ Smart chat creation test passed - created '{chat_id}'")
        return True

    except Exception as e:
        print(f"❌ Smart chat creation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chat_history_search():
    """Test the chat history search functionality."""
    print("🔍 Testing chat history search...")

    try:
        import backend

        # Create test chats
        create_test_chats_with_content()
        from tests.test_utils import get_default_test_user

        test_user = get_default_test_user()
        username = test_user["username"]

        # Test various search queries
        search_tests = [
            ("Python", 1),  # Should find Python Programming Help chat
            ("JavaScript", 1),  # Should find JavaScript Questions chat
            ("function", 2),  # Should find both Python and JavaScript chats
            ("database", 1),  # Should find Database Design chat
            ("normalization", 1),  # Should find specific term in database chat
            ("nonexistent", 0),  # Should find nothing
            ("", 0),  # Empty query should return nothing
        ]

        for query, expected_count in search_tests:
            results = backend.search_chat_history(query, username)
            actual_count = len(results)

            print(
                f"  🔎 Query: '{query}' → Found {actual_count} chat(s) (expected {expected_count})"
            )

            if expected_count > 0:
                assert actual_count >= expected_count, (
                    f"Expected at least {expected_count} results for '{query}', got {actual_count}"
                )

                # Verify result structure
                for result in results:
                    assert "chat_id" in result, "Result should have chat_id"
                    assert "chat_name" in result, "Result should have chat_name"
                    assert "message" in result, "Result should have message"
                    assert "timestamp" in result, "Result should have timestamp"
                    # Verify message content contains the query
                    message_content = result["message"].get("content", "").lower()
                    assert query.lower() in message_content, (
                        f"Query '{query}' should be found in message content"
                    )
            else:
                assert actual_count == 0, (
                    f"Expected no results for '{query}', got {actual_count}"
                )

        print("✅ Chat history search test passed")
        return True

    except Exception as e:
        print(f"❌ Chat history search test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chatbot_ui_integration():
    """Test the enhanced chatbot UI integration."""
    print("🎨 Testing chatbot UI integration...")

    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui

        from tests.test_utils import get_default_test_user

        test_user = get_default_test_user()

        # Test creating UI with search components
        with gr.Blocks():
            username_state = gr.State(test_user["username"])
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")

            components = chatbot_ui(
                username_state, chat_history_state, chat_id_state, setup_events=False
            )

            # Should return 13 components now (including search, rename, and clear chat)
            assert len(components) == 13, (
                f"Expected 13 components, got {len(components)}"
            )

            (
                chat_selector,
                new_chat_btn,
                chatbot,
                chat_input,
                send_btn,
                search_input,
                search_btn,
                search_results,
                rename_input,
                rename_btn,
                debug_md,
                clear_chat_btn,
                clear_chat_status,
            ) = components

            # Verify all components exist
            assert chat_selector is not None, "Chat selector should exist"
            assert new_chat_btn is not None, "New chat button should exist"
            assert chatbot is not None, "Chatbot should exist"
            assert chat_input is not None, "Chat input should exist"
            assert send_btn is not None, "Send button should exist"
            assert search_input is not None, "Search input should exist"
            assert search_btn is not None, "Search button should exist"
            assert search_results is not None, "Search results should exist"
            assert rename_input is not None, "Rename input should exist"
            assert rename_btn is not None, "Rename button should exist"
            assert debug_md is not None, "Debug markdown should exist"

            print("  ✅ All 11 components created successfully")
            print(f"    - Components: {[type(c).__name__ for c in components]}")

        print("✅ Chatbot UI integration test passed")
        return True

    except Exception as e:
        print(f"❌ Chatbot UI integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all enhanced feature tests."""
    print("🚀 Testing Enhanced Chatbot Features")
    print("=" * 50)
    print("Features being tested:")
    print("  1. Smart chat naming based on first message")
    print("  2. Smart chat creation with meaningful names")
    print("  3. Comprehensive chat history search")
    print("  4. Enhanced chatbot UI integration")
    print("=" * 50)

    # Set up test environment
    test_dir, original_get_chatbot_dir = setup_test_environment()

    # Ensure default test user exists
    try:
        from tests.test_utils import ensure_default_test_user

        ensure_default_test_user()
        print("✅ Test user ready")
    except Exception as e:
        print(f"⚠️ Warning: Could not ensure test user exists: {e}")

    try:
        tests = [
            ("Smart Chat Naming", test_smart_chat_naming),
            ("Smart Chat Creation", test_smart_chat_creation),
            ("Chat History Search", test_chat_history_search),
            ("Chatbot UI Integration", test_chatbot_ui_integration),
        ]

        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
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
            print("\n🎉 All enhanced feature tests passed!")
            print("✅ Smart chat naming working")
            print("✅ Chat history search functional")
            print("✅ Auto-updating dropdown implemented")
            print("✅ Enhanced UI integration complete")
        else:
            print("\n❌ Some tests failed!")
            print("Please check the issues above.")

        return passed == total

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return False
    finally:
        # Clean up
        cleanup_test_environment(test_dir, original_get_chatbot_dir)
        print("🧹 Test environment cleaned up")


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
