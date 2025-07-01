#!/usr/bin/env python3
import gradio as gr
from pathlib import Path
import sys

parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def test_all_interfaces():
    """Test all frontend interfaces in one comprehensive app."""
    with gr.Blocks(title="All Interfaces Test") as app:
        # States
        logged_in_state = gr.State(True)
        username_state = gr.State("test")
        current_chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        gr.State(False)

        gr.Markdown("# All Interfaces Test")

        # Login interface (hidden, but included for completeness)
        with gr.Column(visible=True) as login_container:
            error_message = gr.Markdown(visible=False)
        with gr.Column(visible=False) as main_container:
            gr.Markdown(visible=False)
            gr.Button("Logout", visible=False)

        from gradio_modules.login_and_register import login_interface

        login_interface(
            logged_in_state=logged_in_state,
            username_state=username_state,
            main_container=main_container,
            login_container=login_container,
            error_message=error_message,
        )

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
            from gradio_modules.audio_input import audio_input_ui

            audio_input_ui(
                username_state=username_state,
                chat_history_state=chat_history_state,
                chat_id_state=current_chat_id_state,
            )

        gr.Markdown(
            "## Test Instructions\n- All features are integrated.\n- Use Ctrl+Shift+K or Alt+K to focus the search box.\n- Use username: `test` for all actions.\n- All backend calls are real."
        )

    return app


if __name__ == "__main__":
    app = test_all_interfaces()
    # Use Docker-compatible launch configuration
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
