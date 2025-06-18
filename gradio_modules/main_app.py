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
    login_col = gr.Column(visible=True)
    main_col = gr.Column(visible=False)
    return {
        'logged_in_state': gr.State(False),
        'username_state': gr.State(""),
        'current_chat_id_state': gr.State(""),
        'chat_history_state': gr.State([]),
        'login_container_comp': login_col,
        'main_app_container_comp': main_col,
        'user_info': gr.Markdown(visible=False),
        'logout_btn': gr.Button("Logout", visible=False)
    }

def _add_components(app_data):
    """Add all UI components to the app, ensuring both containers are always present."""
    # Add login interface inside login_container_comp
    with app_data['login_container_comp']:
        login_interface(app_data)
    # Add main app interface inside main_app_container_comp
    with app_data['main_app_container_comp']:
        chat_interface(app_data)
        search_interface(app_data)
        # Add any other main app UI here

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
    
    # Add register navigation button click event (switch to register page)
    app_data['to_register_button'].click(
        fn=None,  # Navigation handled in login_and_register.py
        inputs=[],
        outputs=[]
    )
    
    # Add register account button click event (actual registration)
    app_data['register_account_button'].click(
        fn=do_register,
        inputs=[
            app_data['username'],
            app_data['password'],
            app_data['confirm_password'],
            app_data['is_registering'],
            app_data['login_button'],
            app_data['confirm_password'],
            app_data['to_register_button'],
            app_data['register_account_button'],
            app_data['back_to_login_button'],
            app_data['error_message']
        ],
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp'],
            app_data['error_message']
        ]
    )
    
    # Add back to login button click event (switch to login page)
    app_data['back_to_login_button'].click(
        fn=None,  # Navigation handled in login_and_register.py
        inputs=[],
        outputs=[]
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
        css_path = ensure_styles_dir()
        if not css_path:
            logger.warning("Could not load CSS file")
        app_data = initialize_app_data()
        with gr.Blocks(theme=flexcyon_theme) as app:
            # Show only login UI at startup
            with gr.Column(visible=True) as login_col:
                login_interface(app_data)
            with gr.Column(visible=False) as main_col:
                chat_interface(app_data)
                search_interface(app_data)
                # ... any other main app UI ...
            # Store containers in app_data for toggling
            app_data['login_container_comp'] = login_col
            app_data['main_app_container_comp'] = main_col
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
