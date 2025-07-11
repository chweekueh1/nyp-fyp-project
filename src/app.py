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
from flexcyon_theme import flexcyon_theme


def load_custom_css():
    """Load custom CSS styles from the styles directory."""
    styles_dir = Path(__file__).parent.parent / "styles"
    css_content = ""

    # Load main styles.css
    styles_file = styles_dir / "styles.css"
    if styles_file.exists():
        with open(styles_file, "r", encoding="utf-8") as f:
            css_content += f.read() + "\n"

    # Load performance.css
    performance_file = styles_dir / "performance.css"
    if performance_file.exists():
        with open(performance_file, "r", encoding="utf-8") as f:
            css_content += f.read() + "\n"

    return css_content


def main():
    # Load custom CSS
    custom_css = load_custom_css()

    with gr.Blocks(
        title="NYP FYP CNC Chatbot", theme=flexcyon_theme, css=custom_css
    ) as app:
        # Login interface - only visible when not logged in
        with gr.Column(visible=gr.State(True)) as login_container:
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

        # Main application tabs - visibility controlled by login state
        with gr.Tabs(visible=False) as main_tabs:
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

        # Add logout functionality
        def handle_logout():
            """Handle logout - reset authentication state."""
            return (
                False,  # logged_in_state = False
                "",  # username_state = ""
                gr.update(visible=False),  # main_tabs visible = False (hide tabs)
                gr.update(visible=True),  # login_container visible = True (show login)
            )

        # Add logout button to the main tabs
        with main_tabs:
            logout_btn = gr.Button("🚪 Logout", variant="secondary")
            logout_btn.click(
                fn=handle_logout,
                outputs=[logged_in_state, username_state, main_tabs, login_container],
            )

        # Handle login state changes to show/hide appropriate interfaces
        def handle_login_state_change(logged_in: bool, username: str):
            """Handle login state changes to show/hide appropriate interfaces."""
            if logged_in:
                # User logged in - hide login, show main tabs
                return (
                    gr.update(visible=False),  # login_container
                    gr.update(visible=True),  # main_tabs
                )
            else:
                # User not logged in - show login, hide main tabs
                return (
                    gr.update(visible=True),  # login_container
                    gr.update(visible=False),  # main_tabs
                )

        # Connect login state changes to interface visibility
        logged_in_state.change(
            fn=handle_login_state_change,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_tabs],
        )

    app.launch()


if __name__ == "__main__":
    main()
