#!/usr/bin/env python3
import gradio as gr
from pathlib import Path
import sys
import os

parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def test_all_interfaces():
    """Test all frontend interfaces in one comprehensive app."""
    with gr.Blocks(title="All Interfaces Test") as app:
        # States
        current_chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])

        gr.Markdown("# All Interfaces Test")

        from gradio_modules.login_and_register import login_interface

        # Get login interface components
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
        ) = login_interface(setup_events=False)

        with gr.Tab("💬 Chat"):
            from gradio_modules.chat_interface import chat_interface

            chat_interface(
                logged_in_state=logged_in_state,
                username_state=username_state,
                current_chat_id_state=current_chat_id_state,
                chat_history_state=chat_history_state,
            )

        with gr.Tab("🔍 Search"):
            from gradio_modules.search_interface import search_interface

            search_interface(
                logged_in_state=logged_in_state,
                username_state=username_state,
                current_chat_id_state=current_chat_id_state,
                chat_history_state=chat_history_state,
            )
            # Add a search box matching the main app's shortcut
            gr.Textbox(
                label="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
                placeholder="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
                visible=True,
            )
            gr.Markdown()
            # No need to inject JS here; rely on the global script in /file/scripts/scripts.js

        with gr.Tab("📁 File Upload"):
            from gradio_modules.file_upload import file_upload_ui

            file_upload_ui(
                username_state=username_state,
                chat_history_state=chat_history_state,
                chat_id_state=current_chat_id_state,
            )

        with gr.Tab("🎤 Audio Input"):
            from gradio_modules.audio_input import audio_interface

            audio_interface(
                username_state=username_state,
                setup_events=False,
            )

        gr.Markdown(
            "## Test Instructions\n- All features are integrated.\n- Use Ctrl+Shift+K or Alt+K to focus the search box.\n- Use username: `test` for all actions.\n- All backend calls are real."
        )

    return app


if __name__ == "__main__":
    # Only launch if INTERACTIVE=1 is set in the environment
    if os.environ.get("INTERACTIVE") == "1":
        app = test_all_interfaces()
        launch_config = {
            "debug": True,
            "share": False,
            "inbrowser": False,
            "quiet": False,
            "show_error": True,
            "server_name": "0.0.0.0",  # Listen on all interfaces for Docker
            "server_port": 7860,  # Use the same port as main app
        }
        print(
            f"🌐 Launching test app on {launch_config['server_name']}:{launch_config['server_port']}"
        )
        app.launch(**launch_config)
    else:
        print("Skipping Gradio launch in automated test mode.")
