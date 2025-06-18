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

# Now import from parent directory
import backend
from utils import setup_logging
from flexcyon_theme import flexcyon_theme

# Import UI modules
from .login_and_register import login_interface, do_login, do_register
from .chat_interface import chat_interface
from .search_interface import search_interface
from .chat_history import chat_history_ui
from .file_upload import file_upload_ui
from .audio_input import audio_input_ui

# Set up logging
logger = setup_logging()

# Get absolute path to styles directory
STYLES_DIR = parent_dir / "styles"
CSS_PATH = STYLES_DIR / "styles.css"

def ensure_styles_dir():
    """
    Ensure the styles directory exists and return the path to the CSS file.
    
    Returns:
        str: Path to the CSS file if it exists, None otherwise.
    """
    if STYLES_DIR.exists():
        return str(CSS_PATH) if CSS_PATH.exists() else None
        
    os.makedirs(STYLES_DIR, exist_ok=True)
    print(f"Warning: Styles directory not found. Created at {STYLES_DIR}")
    return None

def main_app():
    """
    Create the main Gradio app.
    
    Returns:
        gr.Blocks: The Gradio app interface.
    """
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
            
            # Create containers
            with gr.Column(visible=True) as login_container:
                with gr.Column(visible=False) as main_container:
                    # Add user info and logout
                    user_info = gr.Markdown(visible=False)
                    logout_button = gr.Button("Logout", visible=False)
                    
                    # Add main interfaces
                    chat_interface(
                        logged_in_state=logged_in_state,
                        username_state=username_state,
                        current_chat_id_state=current_chat_id_state,
                        chat_history_state=chat_history_state
                    )
                    
                    search_interface(
                        logged_in_state=logged_in_state,
                        username_state=username_state,
                        current_chat_id_state=current_chat_id_state,
                        chat_history_state=chat_history_state
                    )
                
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
            
            # Add event handlers
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
                return (
                    False,  # logged_in_state
                    "",    # username_state
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=False)   # user_info
                )
            
            logout_button.click(
                fn=do_logout,
                outputs=[
                    logged_in_state,
                    username_state,
                    login_container,
                    main_container,
                    logout_button,
                    user_info
                ]
            )
            
        return app
    except Exception as e:
        logger.error(f"Error creating main app: {e}")
        raise

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
