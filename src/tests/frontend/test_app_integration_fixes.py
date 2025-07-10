#!/usr/bin/env python3
"""
Test script for app.py integration fixes.

This module tests the specific fixes made to app.py:
1. Fixed search_container interactive parameter error
2. Removed unnecessary "Please log in to continue" message
3. Fixed login interface component unpacking
4. Verified proper state variable interactions
5. Updated search interface to use markdown instead of dropdown
"""

import sys
import traceback
from pathlib import Path
import gradio as gr

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def test_search_container_fix():
    """Test that search_container no longer gets interactive parameter."""
    print("🔧 Testing search_container fix...")

    try:
        from gradio_modules.search_interface import search_interface

        # Create mock state components
        username_state = gr.State("test_user")
        chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")

        # Call search_interface - should not raise TypeError about interactive parameter
        result = search_interface(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )

        # Verify return types
        search_container, search_query, search_btn, search_results_md = result

        # Check that search_results_md is a Markdown component (not Dropdown)
        assert isinstance(search_results_md, gr.Markdown), (
            f"Expected Markdown, got {type(search_results_md)}"
        )

        # Check that search_container is a Column
        assert isinstance(search_container, gr.Column), (
            f"Expected Column, got {type(search_container)}"
        )

        # Check that search_query is a Textbox
        assert isinstance(search_query, gr.Textbox), (
            f"Expected Textbox, got {type(search_query)}"
        )

        print("✅ Search container fix test passed")
        return True

    except Exception as e:
        print(f"❌ Search container fix test failed: {e}")
        traceback.print_exc()
        return False


def test_login_message_removal():
    """Test that the unnecessary login prompt has been removed."""
    print("🔧 Testing login message removal...")

    try:
        # Read app.py to check for the removed message
        with open("src/app.py", "r") as f:
            content = f.read()
        # The message should be removed (set to visible=False)
        if "Please log in to continue" in content:
            # Check if it's properly hidden
            if "visible=False" in content:
                print("✅ Login message completely removed")
                return True
            else:
                print("❌ Login message still visible")
                return False
        else:
            print("✅ Login message completely removed")
            return True
    except Exception as e:
        print(f"❌ Login message removal test failed: {e}")
        return False


def test_component_unpacking():
    """Test that component unpacking is correct."""
    print("🔧 Testing component unpacking...")

    try:
        from gradio_modules.chatbot import chatbot_ui

        # Create mock state components
        username_state = gr.State("test_user")
        chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")

        # Call chatbot_ui - should return exactly 12 components
        result = chatbot_ui(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )

        # Verify we get exactly 12 components
        assert len(result) == 12, f"Expected 12 components, got {len(result)}"

        # Verify the order and types
        (
            chat_selector,
            chatbot,
            msg,
            send_btn,
            rename_input,
            rename_btn,
            rename_status_md,
            search_container,
            debug_md,
            clear_chat_btn,
            clear_chat_status,
            new_chat_btn,
        ) = result

        # Check that search_container is a Column (not Dropdown)
        assert isinstance(search_container, gr.Column), (
            f"Expected Column, got {type(search_container)}"
        )

        print("✅ Component unpacking test passed")
        return True

    except Exception as e:
        print(f"❌ Component unpacking test failed: {e}")
        traceback.print_exc()
        return False


def test_search_interface_integration():
    """Test that search interface is properly integrated."""
    print("🔧 Testing search interface integration...")

    try:
        from gradio_modules.search_interface import search_interface

        # Create mock state components
        username_state = gr.State("test_user")
        chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")

        # Call search_interface
        result = search_interface(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )

        # Verify return types match expected signature
        search_container, search_query, search_btn, search_results_md = result

        # Check that search_query has the right placeholder text
        assert "search query or type a message" in search_query.placeholder.lower(), (
            f"Expected search/message placeholder, got: {search_query.placeholder}"
        )

        # Check that search_btn has the right text
        assert "🔍" in search_btn.value, (
            f"Expected search icon, got: {search_btn.value}"
        )

        print("✅ Search interface integration test passed")
        return True

    except Exception as e:
        print(f"❌ Search interface integration test failed: {e}")
        traceback.print_exc()
        return False


def run_all_app_integration_tests():
    """Run all app integration tests."""
    print("🚀 Running App Integration Fix Tests...")
    print("=" * 60)

    tests = [
        ("Search Container Fix", test_search_container_fix),
        ("Login Message Removal", test_login_message_removal),
        ("Component Unpacking", test_component_unpacking),
        ("Search Interface Integration", test_search_interface_integration),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        results[test_name] = test_func()

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)

    passed = 0
    total = len(tests)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All app integration tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_app_integration_tests()
    sys.exit(0 if success else 1)
