#!/usr/bin/env python3

"""
Combined File Management Interface Module.

This module consolidates the file upload and file classification interfaces
into a single Gradio Blocks object for streamlined file management.
"""

import gradio as gr

# Import individual file modules
from gradio_modules.file_upload import file_upload_ui
from gradio_modules.file_classification import file_classification_interface


def combined_file_interfaces_ui(
    username_state: gr.State,
    logged_in_state: gr.State,
    debug_info_state: gr.State,
    all_chats_data_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> gr.Blocks:
    """
    Combines file upload and file classification UIs into a single Gradio Blocks.
    Uses internal tabs to separate the two functionalities.
    """
    with gr.Blocks() as combined_file_block:
        with gr.Tabs(
            selected=0, elem_id="file_management_tabs"
        ):  # Use tabs within this block for separation
            with gr.TabItem("⬆️ Upload File", id="upload_tab"):
                # Call file_upload_ui, passing all necessary states
                # Note: file_upload_ui expects all_chats_data_state, debug_info_state,
                # chat_id_state, and chat_history_state which are now explicitly passed.
                file_upload_ui(
                    username_state=username_state,
                    all_chats_data_state=all_chats_data_state,
                    debug_info_state=debug_info_state,
                    chat_id_state=chat_id_state,
                    chat_history_state=chat_history_state,
                )

            with gr.TabItem("📂 Classify Files", id="classify_tab"):
                # Call file_classification_interface, passing necessary states
                file_classification_interface(
                    username_state=username_state,
                    logged_in_state=logged_in_state,
                    debug_info_state=debug_info_state,
                )

    return combined_file_block
