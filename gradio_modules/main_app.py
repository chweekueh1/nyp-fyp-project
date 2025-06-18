# gradio_modules/main_app.py
import gradio as gr
import os
import sys
from pathlib import Path
import json
from difflib import get_close_matches
import backend
import logging
from utils import setup_logging
from flexcyon_theme import flexcyon_theme

# Set up logging
logger = setup_logging()

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import UI modules
from .login_and_register import login_interface, do_login, do_register
from .chat_interface import chat_interface
from .search_interface import search_interface
from .chat_history import chat_history_ui
from .file_upload import file_upload_ui
from .audio_input import audio_input_ui

# Get absolute path to styles directory
STYLES_DIR = parent_dir / "styles"
CSS_PATH = STYLES_DIR / "styles.css"

def ensure_styles_dir():
    if STYLES_DIR.exists():
        return str(CSS_PATH) if CSS_PATH.exists() else None
        
    os.makedirs(STYLES_DIR, exist_ok=True)
    print(f"Warning: Styles directory not found. Created at {STYLES_DIR}")
    return None

def initialize_app_data():
    """Initialize the app data dictionary with required components."""
    return {
        'logged_in_state': gr.State(False),
        'username_state': gr.State(""),
        'current_chat_id_state': gr.State(""),
        'chat_history_state': gr.State([]),
        'login_container_comp': gr.Column(visible=True),
        'main_app_container_comp': gr.Column(visible=False),
        'user_info': gr.Markdown(visible=False),
        'logout_btn': gr.Button("Logout", visible=False)
    }

def _add_components(app_data):
    """Add all UI components to the app."""
    # Add login interface
    login_interface(app_data)
    
    # Add chat interface
    chat_interface(app_data)
    
    # Add search interface
    search_interface(app_data)

def _add_login_handling(app_data):
    """Add login and register event handlers."""
    # Add login button click event
    app_data['login_button'].click(
        fn=do_login,
        inputs=[
            app_data['username'],
            app_data['password']
        ],
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp']
        ]
    )
    
    # Add register button click event
    app_data['register_button'].click(
        fn=do_register,
        inputs=[
            app_data['username'],
            app_data['password']
        ],
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp']
        ]
    )

def _add_logout_logic(app_data):
    """Add logout event handler."""
    def do_logout():
        return False, "", gr.update(visible=True)
    
    app_data['logout_btn'].click(
        fn=do_logout,
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp']
        ]
    )

def _add_chat_handling(app_data):
    """Add chat handling logic to the app."""
    # Add chat handling
    app_data['send_button'].click(
        fn=_handle_chat_message,
        inputs=[
            app_data['msg'],
            app_data['chat_history_state'],
            app_data['username_state']
        ],
        outputs=[
            app_data['msg'],
            app_data['chat_history_state']
        ]
    )
    
    # Add chat history update
    def update_chat_display(history):
        return history
        
    app_data['chat_history_state'].change(
        fn=update_chat_display,
        inputs=[app_data['chat_history_state']],
        outputs=[app_data['chat_history']]
    )

def _handle_chat_message(message: str, history: list, username: str) -> tuple[str, list]:
    """Handle chat message submission."""
    if not message.strip():
        return message, history
    
    if not username:
        history.append((message, "Error: You must be logged in to send messages."))
        return "", history
    
    try:
        # Get response from backend
        response = backend.get_chat_response(message, username)
        if not response:
            history.append((message, "Error: No response received from the server."))
            return "", history
            
        history.append((message, response))
        return "", history
    except Exception as e:
        logger.error(f"Error in chat handling: {e}")
        error_msg = "Sorry, I encountered an error. Please try again."
        if isinstance(e, ConnectionError):
            error_msg = "Error: Could not connect to the server. Please check your connection."
        elif isinstance(e, TimeoutError):
            error_msg = "Error: Request timed out. Please try again."
        history.append((message, error_msg))
        return "", history

def _add_user_info_update(app_data):
    """Add user info update logic."""
    def update_user_info(username):
        if not username:
            return gr.update(visible=False)
        return gr.update(visible=True, value=f"Logged in as: {username}")
        
    app_data['username_state'].change(
        fn=update_user_info,
        inputs=[app_data['username_state']],
        outputs=[app_data['user_info']]
    )

def main_app():
    """Create the main Gradio app."""
    try:
        # Ensure styles directory exists
        css_path = ensure_styles_dir()
        if not css_path:
            logger.warning("Could not load CSS file")
        
        # Initialize app data
        app_data = initialize_app_data()
        
        # Create the app
        with gr.Blocks(theme=flexcyon_theme) as app:
            # Add components
            _add_components(app_data)
            
            # Add event handlers
            _add_login_handling(app_data)
            _add_logout_logic(app_data)
            _add_chat_handling(app_data)
            _add_user_info_update(app_data)
        
        return app
    except Exception as e:
        logger.error(f"Error initializing app: {e}")
        raise

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
