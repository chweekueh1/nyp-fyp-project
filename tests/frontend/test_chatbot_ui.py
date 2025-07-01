#!/usr/bin/env python3
"""
Test script for chatbot UI component creation.
"""

import gradio as gr
from gradio_modules.chatbot import chatbot_ui


def test_chatbot_ui():
    """
    Test the chatbot UI components.

    This function tests that all required components are created correctly.
    """
    # Create test states
    username = gr.State("test_user")
    chat_history = gr.State([])
    chat_id = gr.State("test_chat_id")

    with gr.Blocks():
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
        ) = chatbot_ui(username, chat_history, chat_id, setup_events=False)
    assert chat_selector is not None, "Chat selector should be created"
    assert new_chat_btn is not None, "New chat button should be created"
    assert chatbot is not None, "Chatbot component should be created"
    assert chat_input is not None, "Chat input component should be created"
    assert send_btn is not None, "Send button should be created"
    assert search_input is not None, "Search input should be created"
    assert search_btn is not None, "Search button should be created"
    assert search_results is not None, "Search results should be created"
    assert rename_input is not None, "Rename input should be created"
    assert rename_btn is not None, "Rename button should be created"
    assert debug_md is not None, "Debug markdown should be created"
    print("test_chatbot_ui: PASSED")


if __name__ == "__main__":
    test_chatbot_ui()
