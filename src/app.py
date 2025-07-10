#!/usr/bin/env python3
"""
Main application entry point for the NYP FYP CNC Chatbot.

This file initializes the Gradio UI, loads environment variables (API keys, configuration) from .env,
and wires together all backend, frontend, and LLM components.

Environment variables are loaded using dotenv for secure configuration.
"""

import sys
from pathlib import Path
import gradio as gr

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from gradio_modules.login_and_register import login_interface
from gradio_modules.chatbot import chatbot_ui
from gradio_modules.search_interface import search_interface
from gradio_modules.file_upload import file_upload_ui
from gradio_modules.audio_input import audio_interface


def main():
    with gr.Blocks(title="NYP FYP CNC Chatbot") as app:
        # Login interface
        (
            logged_in_state,
            username_state,
            is_register_mode,
            main_container,
            error_message,
            username_input,
            email_input,
            password_input,
            confirm_password_input,
            primary_btn,
            secondary_btn,
            show_password_btn,
            show_confirm_btn,
            password_visible,
            confirm_password_visible,
            header_subtitle,
            header_instruction,
            email_info,
            password_requirements,
        ) = login_interface(setup_events=True)

        # Shared states for all tabs
        chat_id_state = gr.State("")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")
        audio_history_state = gr.State([])  # For audio session history

        with gr.Tabs(visible=logged_in_state):
            with gr.Tab("💬 Chat"):
                chatbot_ui(
                    username_state,
                    chat_id_state,
                    chat_history_state,
                    all_chats_data_state,
                    debug_info_state,
                )
            with gr.Tab("🔍 Search"):
                # Pass audio_history_state for future integration
                search_interface(
                    username_state,
                    chat_id_state,
                    chat_history_state,
                    all_chats_data_state,
                    debug_info_state,
                    audio_history_state,  # Now passed to search_interface
                )
            with gr.Tab("📁 File Upload"):
                file_upload_ui(
                    username_state,
                    chat_history_state,
                    chat_id_state,
                )
            with gr.Tab("🎤 Audio Input"):
                audio_interface(
                    username_state,
                    setup_events=True,
                )

    app.launch()


if __name__ == "__main__":
    main()
