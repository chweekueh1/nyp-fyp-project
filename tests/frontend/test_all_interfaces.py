import gradio as gr
from pathlib import Path
import sys

parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions for direct calls
from backend import ask_question, upload_file, transcribe_audio, search_chat_history

def test_all_interfaces():
    """Test all frontend interfaces in one comprehensive app."""
    with gr.Blocks(title="All Interfaces Test") as app:
        # States
        logged_in_state = gr.State(True)
        username_state = gr.State("test")
        current_chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        is_registering = gr.State(False)

        gr.Markdown("# All Interfaces Test")

        # Login interface (hidden, but included for completeness)
        with gr.Column(visible=False) as main_container:
            user_info = gr.Markdown(visible=False)
            logout_button = gr.Button("Logout", visible=False)
        from gradio_modules.login_and_register import login_interface
        login_interface(
            logged_in_state=logged_in_state,
            username_state=username_state,
            current_chat_id_state=current_chat_id_state,
            chat_history_state=chat_history_state,
            is_registering=is_registering,
            main_container=main_container,
            logout_button=logout_button,
            user_info=user_info
        )

        with gr.Tab("💬 Chat"):
            from gradio_modules.chat_interface import chat_interface
            chat_interface(
                logged_in_state=logged_in_state,
                username_state=username_state,
                current_chat_id_state=current_chat_id_state,
                chat_history_state=chat_history_state
            )

        with gr.Tab("🔍 Search"):
            from gradio_modules.search_interface import search_interface
            search_interface(
                logged_in_state=logged_in_state,
                username_state=username_state,
                current_chat_id_state=current_chat_id_state,
                chat_history_state=chat_history_state
            )
            # Add a search box with elem_id for Ctrl+K
            search_box = gr.Textbox(label="Search", elem_id="search_box", visible=True)
            gr.HTML("""
            <script>
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key === 'k') {
                    e.preventDefault();
                    var search = document.querySelector('input#search_box');
                    if (search) { search.focus(); }
                }
            });
            </script>
            """)

        with gr.Tab("📁 File Upload"):
            from gradio_modules.file_upload import file_upload_ui
            file_upload_ui(
                username_state=username_state,
                chat_history_state=chat_history_state,
                chat_id_state=current_chat_id_state
            )

        with gr.Tab("🎤 Audio Input"):
            from gradio_modules.audio_input import audio_input_ui
            audio_input_ui(
                username_state=username_state,
                chat_history_state=chat_history_state,
                chat_id_state=current_chat_id_state
            )

        gr.Markdown("## Test Instructions\n- All features are integrated.\n- Use Ctrl+K to focus the search box.\n- Use username: `test` for all actions.\n- All backend calls are real.")

    return app

if __name__ == "__main__":
    print("Creating all interfaces test...")
    app = test_all_interfaces()
    print("Launching all interfaces test...")
    app.launch(debug=True, share=False)