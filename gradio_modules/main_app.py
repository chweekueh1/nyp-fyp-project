# gradio_modules/main_app.py
import gradio as gr
import os
import sys
from pathlib import Path
import json
from difflib import get_close_matches

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import backend
from utils import setup_logging
from flexcyon_theme import flexcyon_theme

from .login_and_register import login_interface
from .chat_interface import chat_interface
from .search_interface import search_interface
from .file_upload import file_upload_ui
from .audio_input import audio_input_ui

logger = setup_logging()

STYLES_DIR = parent_dir / "styles"
CSS_PATH = STYLES_DIR / "styles.css"

def ensure_styles_dir():
    if STYLES_DIR.exists():
        return str(CSS_PATH) if CSS_PATH.exists() else None
    os.makedirs(STYLES_DIR, exist_ok=True)
    print(f"Warning: Styles directory not found. Created at {STYLES_DIR}")
    return None

def main_app():
    try:
        css_path = ensure_styles_dir()
        if not css_path:
            logger.warning("Could not load CSS file")
            
        with gr.Blocks(theme=flexcyon_theme) as app:
            # Initialize states
            logged_in_state = gr.State(False)
            username_state = gr.State("")
            current_chat_id_state = gr.State("")
            chat_history_state = gr.State([])
            is_registering = gr.State(False)
            all_chat_histories_state = gr.State({})
            selected_chat_id_state = gr.State("")

            # Sibling containers, not nested!
            with gr.Column(visible=True) as login_container:
                pass  # login_interface will populate this

            with gr.Column(visible=False) as main_container:
                user_info = gr.Markdown(visible=False)
                logout_button = gr.Button("Logout", visible=False)
                chat_selector = gr.Dropdown(choices=[], label="Select Chat")
                chatbot = gr.Chatbot(value=[], label="Chatbot")
                with gr.Tabs() as main_tabs:
                    with gr.TabItem("File Upload"):
                        file_upload_ui(
                            username_state=username_state,
                            chat_history_state=chat_history_state,
                            chat_id_state=current_chat_id_state
                        )
                    with gr.TabItem("Search Chat History"):
                        search_interface(
                            logged_in_state=logged_in_state,
                            username_state=username_state,
                            current_chat_id_state=current_chat_id_state,
                            chat_history_state=chat_history_state
                        )

            # --- Event Handlers ---
            def update_user_info(username):
                if not username:
                    return gr.update(visible=False)
                return gr.update(visible=True, value=f"Logged in as: {username}")
            
            username_state.change(
                fn=update_user_info,
                inputs=[username_state],
                outputs=[user_info]
            )
            
            def do_logout():
                # Reset all states and show a logout message
                return (
                    False,  # logged_in_state
                    "",    # username_state
                    "",    # current_chat_id_state
                    [],    # chat_history_state
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="You have been logged out. Please log in again."),   # user_info
                    gr.update(choices=[], value=""),  # chat_selector
                    gr.update(value=[]),  # chatbot
                    {},  # all_chat_histories_state
                    ""   # selected_chat_id_state
                )
            
            logout_button.click(
                fn=do_logout,
                outputs=[
                    logged_in_state,
                    username_state,
                    current_chat_id_state,
                    chat_history_state,
                    login_container,
                    main_container,
                    logout_button,
                    user_info,
                    chat_selector,
                    chatbot,
                    all_chat_histories_state,
                    selected_chat_id_state
                ]
            )

            # --- Chat Selector Logic ---
            def update_chat_selector_and_chatbot(all_histories, selected_chat_id):
                chat_ids = list(all_histories.keys())
                value = selected_chat_id if selected_chat_id in chat_ids else (chat_ids[0] if chat_ids else "")
                chat_history = all_histories.get(value, [])
                return (
                    gr.update(choices=chat_ids, value=value),
                    gr.update(value=chat_history)
                )

            chat_selector.change(
                fn=lambda chat_id, all_histories: gr.update(value=all_histories.get(chat_id, [])),
                inputs=[chat_selector, all_chat_histories_state],
                outputs=[chatbot]
            )

            all_chat_histories_state.change(
                fn=update_chat_selector_and_chatbot,
                inputs=[all_chat_histories_state, selected_chat_id_state],
                outputs=[chat_selector, chatbot]
            )

            # --- Login Interface ---
            login_interface(
                logged_in_state=logged_in_state,
                username_state=username_state,
                current_chat_id_state=current_chat_id_state,
                chat_history_state=chat_history_state,
                is_registering=is_registering,
                main_container=main_container,
                logout_button=logout_button,
                user_info=user_info,
                login_container=login_container,  # Pass the container to be used
                all_chat_histories_state=all_chat_histories_state,
                selected_chat_id_state=selected_chat_id_state
            )

            # --- Chatbot Logic ---
            def update_chatbot_on_login(all_histories, selected_chat_id):
                chat_ids = list(all_histories.keys())
                value = selected_chat_id if selected_chat_id in chat_ids else (chat_ids[0] if chat_ids else "")
                chat_history = all_histories.get(value, [])
                return gr.update(value=chat_history)

            selected_chat_id_state.change(
                fn=update_chatbot_on_login,
                inputs=[all_chat_histories_state, selected_chat_id_state],
                outputs=[chatbot]
            )

        return app
    except Exception as e:
        logger.error(f"Error creating main app: {e}")
        raise

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
