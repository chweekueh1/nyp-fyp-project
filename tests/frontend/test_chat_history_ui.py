#!/usr/bin/env python3
"""
Test script for chat history UI component creation.
"""

import gradio as gr
from gradio_modules.chat_history import chat_history_ui


def test_chat_history_ui():
    """
    Test the chat history UI components.

    This function tests that all required components are created correctly.
    """
    # Create test states
    username = gr.State("test_user")
    chat_id = gr.State("test_chat_id")
    chat_history = gr.State([])

    # Test UI creation
    with gr.Blocks():
        search_box, search_btn, results_md = chat_history_ui(
            username, chat_id, chat_history
        )
    assert search_box is not None, "Search box component should be created"
    assert search_btn is not None, "Search button should be created"
    assert results_md is not None, "Results markdown should be created"
    print("test_chat_history_ui: PASSED")


if __name__ == "__main__":
    test_chat_history_ui()
