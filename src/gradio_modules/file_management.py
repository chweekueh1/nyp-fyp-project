#!/usr/bin/env python3

"""
Combined File Management Interface Module.

This module consolidates the file upload and file classification interfaces
into a single Gradio Blocks object for streamlined file management.
"""

import gradio as gr
from gradio_modules.file_upload import file_upload_ui
from gradio_modules.file_classification import file_classification_interface


def file_management_interface(
    username_state: gr.State, logged_in_state: gr.State, all_chats_data_state: gr.State
) -> gr.Blocks:
    """
    Combines File Upload and File Classification UIs into a single Gradio Blocks container.
    Render **section** headings only once; inner UIs should not have duplicate headers!
    """
    with gr.Blocks() as file_management_block:
        gr.Markdown("")  # No FILE-wide heading! Only global one in app.py
        # Section: Upload
        gr.Markdown("### Upload Files")
        file_upload_block = file_upload_ui(
            username_state,
            all_chats_data_state,
            gr.State(""),
            gr.State("default"),
            gr.State([]),
        )
        # Section: Classification
        gr.Markdown("### Classify Existing Files")
        file_classification_block = file_classification_interface(
            username_state, logged_in_state, gr.State("")
        )
        # Don't call render!
        file_upload_block
        file_classification_block
    return file_management_block
