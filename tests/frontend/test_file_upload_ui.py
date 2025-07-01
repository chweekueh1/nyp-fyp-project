#!/usr/bin/env python3
"""
Test script for file upload UI component creation.
"""

import gradio as gr
from gradio_modules.file_upload import file_upload_ui


def test_file_upload_ui():
    """
    Test the file upload UI components.

    This function tests that all required components are created correctly.
    """
    # Create test states
    username = gr.State("test_user")
    chat_history = gr.State([])
    chat_id = gr.State("test_chat_id")

    # Test UI creation
    with gr.Blocks():
        file_upload, file_btn, file_debug_md = file_upload_ui(
            username, chat_history, chat_id
        )
    assert file_upload is not None, "File upload component should be created"
    assert file_btn is not None, "File button should be created"
    assert file_debug_md is not None, "Debug markdown should be created"
    print("test_file_upload_ui: PASSED")


if __name__ == "__main__":
    test_file_upload_ui()
