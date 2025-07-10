#!/usr/bin/env python3
"""
Test script to verify that all clear buttons are properly integrated and working.
This test checks the clear chat history, clear file history, and clear audio history functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import asyncio
import os


async def test_clear_chat_history_integration():
    """
    Test that the clear chat history button is properly integrated and working.
    """
    print("🗑️ Testing clear chat history integration...")

    try:
        from infra_utils import clear_chat_history
        from gradio_modules.chatbot import _clear_current_chat

        username = "test_clear_chat_user"
        chat_id = "test_chat_123"

        # Test the backend clear function
        print("  📝 Testing backend clear_chat_history function...")
        success, all_chats = clear_chat_history(chat_id, username)

        # Should return False for non-existent chat
        assert not success, "Should return False for non-existent chat"
        assert isinstance(all_chats, dict), "Should return a dict for all_chats"
        print("  ✅ Backend clear_chat_history function working correctly")

        # Test the UI handler function
        print("  🎨 Testing UI clear handler function...")
        result = _clear_current_chat(chat_id, username)

        # Should return 5 elements: cleared_history, chat_id, status, all_chats_data, debug_info
        assert len(result) == 5, f"Expected 5 elements, got {len(result)}"
        cleared_history, returned_chat_id, status, all_chats_data, debug_info = result

        assert isinstance(cleared_history, list), "cleared_history should be a list"
        assert isinstance(status, str), "status should be a string"
        assert isinstance(all_chats_data, dict), "all_chats_data should be a dict"

        print("  ✅ UI clear handler function working correctly")
        print("  ✅ Clear chat history integration test PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Error testing clear chat history: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_clear_file_history_integration():
    """
    Test that the clear file history button is properly integrated and working.
    """
    print("🗑️ Testing clear file history integration...")

    try:
        from gradio_modules.file_classification import handle_clear_uploaded_files
        from infra_utils import clear_uploaded_files, get_chatbot_dir

        # Test the backend clear function
        print("  📝 Testing backend clear_uploaded_files function...")

        # Create a temporary test file
        uploads_dir = os.path.join(get_chatbot_dir(), "data", "modelling", "data")
        os.makedirs(uploads_dir, exist_ok=True)

        test_file_path = os.path.join(uploads_dir, "test_clear_file.txt")
        with open(test_file_path, "w") as f:
            f.write("Test file for clearing")

        # Verify file exists
        assert os.path.exists(test_file_path), "Test file should exist before clearing"

        # Clear files
        clear_uploaded_files()

        # Verify file is gone
        assert not os.path.exists(test_file_path), (
            "Test file should be deleted after clearing"
        )
        print("  ✅ Backend clear_uploaded_files function working correctly")

        # Test the UI handler function
        print("  🎨 Testing UI clear handler function...")
        result = handle_clear_uploaded_files()

        # Should return a tuple with one element (status update)
        assert isinstance(result, tuple), "Result should be a tuple"
        assert len(result) == 1, f"Expected 1 element, got {len(result)}"

        # The result should be a gr.update object or similar
        print("  ✅ UI clear handler function working correctly")
        print("  ✅ Clear file history integration test PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Error testing clear file history: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_clear_audio_history_integration():
    """
    Test that the clear audio history button is properly integrated and working.
    """
    print("🗑️ Testing clear audio history integration...")

    try:
        from gradio_modules.audio_input import clear_audio_history, format_history

        # Test the clear function
        print("  📝 Testing clear_audio_history function...")
        result = clear_audio_history()

        # Should return a tuple with 2 elements: empty_history, success_message
        assert isinstance(result, tuple), "Result should be a tuple"
        assert len(result) == 2, f"Expected 2 elements, got {len(result)}"

        empty_history, success_message = result
        assert isinstance(empty_history, list), "empty_history should be a list"
        assert len(empty_history) == 0, "empty_history should be empty"
        assert isinstance(success_message, str), "success_message should be a string"
        assert "cleared" in success_message.lower(), (
            "Success message should mention clearing"
        )

        print("  ✅ clear_audio_history function working correctly")

        # Test the format_history function with empty history
        print("  📝 Testing format_history function with empty history...")
        formatted_empty = format_history([])
        assert isinstance(formatted_empty, str), "formatted_empty should be a string"
        assert "No audio processed" in formatted_empty, "Should show no audio message"

        print("  ✅ format_history function working correctly with empty history")
        print("  ✅ Clear audio history integration test PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Error testing clear audio history: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_clear_buttons_ui_integration():
    """
    Test that the clear buttons are properly integrated in the UI components.
    """
    print("🎨 Testing clear buttons UI integration...")

    try:
        # Test chat interface clear button
        print("  💬 Testing chat interface clear button...")
        from gradio_modules.chatbot import chatbot_ui
        import gradio as gr

        # Create mock states
        username_state = gr.State("test_user")
        chat_id_state = gr.State("test_chat")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")

        # Get components from chatbot_ui
        components = chatbot_ui(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )

        # Should return 12 components including clear_chat_btn and clear_chat_status
        assert len(components) == 12, f"Expected 12 components, got {len(components)}"

        # Extract clear button and status components
        clear_chat_btn = components[9]  # clear_chat_btn
        clear_chat_status = components[10]  # clear_chat_status

        assert isinstance(clear_chat_btn, gr.Button), (
            "clear_chat_btn should be a Button"
        )
        assert isinstance(clear_chat_status, gr.Markdown), (
            "clear_chat_status should be a Markdown"
        )

        print("  ✅ Chat interface clear button properly integrated")

        # Test file classification interface clear button
        print("  📁 Testing file classification interface clear button...")
        from gradio_modules.file_classification import file_classification_interface

        file_components = file_classification_interface(username_state)

        # Should return 17 components including clear_files_btn and clear_files_status
        assert len(file_components) == 17, (
            f"Expected 17 components, got {len(file_components)}"
        )

        # Extract clear button and status components
        clear_files_btn = file_components[15]  # clear_files_btn
        clear_files_status = file_components[16]  # clear_files_status

        assert isinstance(clear_files_btn, gr.Button), (
            "clear_files_btn should be a Button"
        )
        assert isinstance(clear_files_status, gr.Markdown), (
            "clear_files_status should be a Markdown"
        )

        print("  ✅ File classification interface clear button properly integrated")

        # Test audio interface clear button
        print("  🎤 Testing audio interface clear button...")
        from gradio_modules.audio_input import audio_interface

        audio_components = audio_interface(username_state, setup_events=False)

        # Should return 11 components including clear_history_btn
        assert len(audio_components) == 11, (
            f"Expected 11 components, got {len(audio_components)}"
        )

        # Extract clear button component
        clear_history_btn = audio_components[9]  # clear_history_btn

        assert isinstance(clear_history_btn, gr.Button), (
            "clear_history_btn should be a Button"
        )

        print("  ✅ Audio interface clear button properly integrated")
        print("  ✅ Clear buttons UI integration test PASSED")
        return True

    except Exception as e:
        print(f"  ❌ Error testing clear buttons UI integration: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """
    Run all clear button integration tests.
    """
    print("🗑️ Clear Buttons Integration Tests")
    print("=" * 60)

    test_results = []

    # Test 1: Clear chat history integration
    print("\n1️⃣ Testing clear chat history integration...")
    result1 = await test_clear_chat_history_integration()
    test_results.append(("Clear Chat History", result1))

    # Test 2: Clear file history integration
    print("\n2️⃣ Testing clear file history integration...")
    result2 = test_clear_file_history_integration()
    test_results.append(("Clear File History", result2))

    # Test 3: Clear audio history integration
    print("\n3️⃣ Testing clear audio history integration...")
    result3 = test_clear_audio_history_integration()
    test_results.append(("Clear Audio History", result3))

    # Test 4: Clear buttons UI integration
    print("\n4️⃣ Testing clear buttons UI integration...")
    result4 = test_clear_buttons_ui_integration()
    test_results.append(("Clear Buttons UI", result4))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All clear button integration tests PASSED!")
        print("\n✅ All clear buttons are properly integrated and working:")
        print("  💬 Clear Chat History: Functional backend + UI integration")
        print("  📁 Clear File History: Functional backend + UI integration")
        print("  🎤 Clear Audio History: Functional backend + UI integration")
    else:
        print("\n⚠️ Some clear button integration tests FAILED!")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
