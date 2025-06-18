import gradio as gr
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import tz
from dateutil.parser import parse as dateutil_parse
from collections import defaultdict
import json
import os
import sys 
from dotenv import load_dotenv
import traceback 
import logging
from typing import Dict, Any, Tuple, Optional
from backend import (
    do_login as backend_login,
    do_register as backend_register,
    USER_DB_PATH,
    CHAT_SESSIONS_PATH
)
from pathlib import Path
from utils import setup_logging

# Set up logging
logger = setup_logging()

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import modules from the parent directory
import backend 
import hashing
import utils 

# --- Configuration (moved from app.py to login.py) ---
load_dotenv() 

UTC_PLUS_8 = tz.tzoffset("UTC+8", timedelta(hours=8))
from_zone = tz.tzutc() 
to_zone = tz.tzlocal() 

ALLOWED_EMAILS = [ 
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

# --- Helper Functions (Synchronous, for user/chat data management - local to login.py) ---

def get_datetime_from_timestamp(ts_string: str) -> datetime:
    if not isinstance(ts_string, str) or not ts_string:
        return datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8)
        
    try:
        dt_obj = dateutil_parse(ts_string)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(UTC_PLUS_8)
    except ValueError as e:
        print(f"Warning: Could not parse timestamp '{ts_string}' using dateutil.parser.parse. Error: {e}. Using timezone-aware datetime.min as fallback for sorting/display.")
        return datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8)

def ensure_user_db_exists_sync():
    """Ensures the user database file and its directory exist."""
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": {}}, f, indent=2)

def load_users_sync() -> dict:
    """
    Loads user data from the JSON database with proper error handling.
    Returns {"users": {...}} format.
    """
    if not os.path.exists(USER_DB_PATH):
        return {"users": {}}
        
    try:
        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict) or "users" not in data:
                logging.warning("Invalid users data format, returning empty users dict")
                return {"users": {}}
            return data
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding users data: {e}")
        return {"users": {}}
    except Exception as e:
        logging.error(f"Error loading users data: {e}")
        return {"users": {}}

def save_users_sync(users_data: dict) -> None:
    """
    Saves user data to the JSON database using atomic file operations.
    Expects and saves the {"users": {...}} format.
    """
    if not users_data:
        return
        
    try:
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        temp_path = f"{USER_DB_PATH}.tmp"
        
        with open(temp_path, 'w') as f:
            json.dump(users_data, f, indent=2)
        
        if os.path.exists(USER_DB_PATH):
            os.replace(temp_path, USER_DB_PATH)
        else:
            os.rename(temp_path, USER_DB_PATH)
            
        logging.info("Successfully saved users data")
    except Exception as e:
        logging.error(f"Error saving users data: {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise

def load_user_chats_sync(username: str) -> list:
    """
    Loads all chat histories for a given user.
    Called to ensure the user's chat sessions directory is created/checked.
    """
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    if not os.path.exists(user_folder):
        return []
    chat_files = [f for f in os.listdir(user_folder) if os.path.isfile(os.path.join(user_folder, f)) and f.endswith(".json")]
    chat_histories = []
    for chat_file in chat_files:
        try:
            with open(os.path.join(user_folder, chat_file), 'r') as f:
                chat_histories.append(json.load(f))
        except json.JSONDecodeError as e:
            print(f"Error reading chat file {chat_file}: {e}. Skipping this chat.")
        except Exception as e:
            print(f"Unexpected error with chat file {chat_file}: {e}. Skipping this chat.")
    return chat_histories

# --- Main login_interface function ---
def login_interface(app_data: Dict[str, Any]) -> None:
    """Create the login/register interface components with proper error handling and mode switching."""
    if not isinstance(app_data, dict):
        app_data = {}

    # State to track mode
    if 'is_registering' not in app_data:
        app_data['is_registering'] = gr.State(False)

    with gr.Column(visible=True) as login_container:
        app_data['username'] = gr.Textbox(
            label="Username",
            placeholder="Enter your username",
            show_label=True
        )
        with gr.Row():
            app_data['password'] = gr.Textbox(
                label="Password",
                placeholder="Enter your password",
                show_label=True,
                type="password",
                elem_id="password_input"
            )
            app_data['password_visibility'] = gr.Button(
                "👁️",
                elem_id="password_visibility",
                size="sm"
            )
        app_data['confirm_password'] = gr.Textbox(
            label="Confirm Password",
            placeholder="Confirm your password",
            show_label=True,
            type="password",
            visible=False
        )
        with gr.Row():
            app_data['login_button'] = gr.Button("Login", elem_classes=["primary"])
            app_data['register_button'] = gr.Button("Register", elem_classes=["primary"])
        app_data['proceed_register_button'] = gr.Button("Register Account", visible=False, elem_classes=["primary"])
        app_data['error_message'] = gr.Markdown(visible=False)
        app_data['username_state'] = gr.State("")
        app_data['logged_in_state'] = gr.State(False)
        app_data['chat_id_state'] = gr.State("")
        app_data['chat_history_state'] = gr.State([])
        app_data['password_visible'] = gr.State(False)

    app_data['login_container_comp'] = login_container

    # Password visibility toggle
    app_data['password_visibility'].click(
        fn=toggle_password_visibility,
        inputs=[app_data['password_visible']],
        outputs=[
            app_data['password_visible'],
            app_data['password'],
            app_data['password_visibility']
        ]
    )

    # Switch to register mode
    def to_register_mode(is_registering):
        return (
            gr.update(visible=not is_registering),  # login button
            gr.update(visible=is_registering),      # confirm password
            gr.update(visible=not is_registering),  # register button (switch)
            gr.update(visible=is_registering),      # proceed register button
            True
        )
    app_data['register_button'].click(
        fn=to_register_mode,
        inputs=[app_data['is_registering']],
        outputs=[
            app_data['login_button'],
            app_data['confirm_password'],
            app_data['register_button'],
            app_data['proceed_register_button'],
            app_data['is_registering']
        ]
    )

    # Switch to login mode
    def to_login_mode(is_registering):
        return (
            gr.update(visible=True),   # login button
            gr.update(visible=False),  # confirm password
            gr.update(visible=True),   # register button (switch)
            gr.update(visible=False),  # proceed register button
            False
        )
    app_data['login_button'].click(
        fn=to_login_mode,
        inputs=[app_data['is_registering']],
        outputs=[
            app_data['login_button'],
            app_data['confirm_password'],
            app_data['register_button'],
            app_data['proceed_register_button'],
            app_data['is_registering']
        ]
    )

    # Actual login action
    def safe_login(username, password):
        if not username or not password:
            logger.warning("Login attempt with empty fields")
            return False, "", gr.update(visible=True), gr.update(visible=True, value="Please enter both username and password")
        return do_login(username, password)
    app_data['login_button'].click(
        fn=safe_login,
        inputs=[app_data['username'], app_data['password']],
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp'],
            app_data['error_message']
        ]
    )

    # Actual register action
    def safe_register(username, password, confirm_password):
        if not username or not password or not confirm_password:
            logger.warning("Registration attempt with empty fields")
            return False, "All fields are required"
        return do_register(username, password, confirm_password)
    app_data['proceed_register_button'].click(
        fn=safe_register,
        inputs=[app_data['username'], app_data['password'], app_data['confirm_password']],
        outputs=[app_data['logged_in_state'], app_data['error_message']]
    )

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password complexity.
    
    Args:
        password: The password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, ""

def do_login(username: str, password: str) -> Tuple[bool, str, Dict[str, Any], Dict[str, Any]]:
    """Handle login action.
    
    Args:
        username: The username to login with
        password: The password to login with
        
    Returns:
        Tuple of (success, username, UI updates, error message)
    """
    # Validate inputs
    if not username or not password:
        logger.warning("Login attempt with empty fields")
        return False, "", gr.update(visible=True), gr.update(visible=True, value="Please fill in all fields")
    
    try:
        # Hash the password
        hashed_password = hashing.hash_password(password)
        
        # Create event loop for async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Call backend login with hashed password
        result = loop.run_until_complete(backend_login(username, hashed_password))
        loop.close()
        
        if result and isinstance(result, dict) and result.get('code') == '200':
            return True, username, gr.update(visible=False), gr.update(visible=False)
        else:
            error_msg = result.get('message', 'Invalid username or password') if result else 'Invalid username or password'
            logger.warning(f"Login failed for user {username}: {error_msg}")
            return False, "", gr.update(visible=True), gr.update(visible=True, value=error_msg)
            
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return False, "", gr.update(visible=True), gr.update(visible=True, value="An unexpected error occurred")

def do_register(username: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """Handle user registration.
    
    Args:
        username: The username to register
        password: The password to register
        confirm_password: The password confirmation
        
    Returns:
        Tuple of (success, message)
    """
    # Validate inputs
    if not username or not password or not confirm_password:
        logger.warning("Registration attempt with empty fields")
        return False, "All fields are required"
        
    if password != confirm_password:
        logger.warning(f"Password mismatch for user {username}")
        return False, "Passwords do not match"
        
    if len(password) < 8:
        logger.warning(f"Password too short for user {username}")
        return False, "Password must be at least 8 characters long"
        
    # Validate password complexity
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        logger.warning(f"Invalid password complexity for user {username}: {error_msg}")
        return False, error_msg
        
    try:
        # Check if username exists
        if backend.user_exists(username):
            logger.warning(f"Username already exists: {username}")
            return False, "Username already exists"
            
        # Hash the password
        hashed_password = hashing.hash_password(password)
        
        # Register user
        success = backend.register_user(username, hashed_password)
        if not success:
            logger.warning(f"Failed to register user: {username}")
            return False, "Failed to register user"
            
        logger.info(f"Successfully registered user: {username}")
        return True, "Registration successful! Please log in."
        
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        return False, "An unexpected error occurred"

# --- Test functions ---
def test_login_interface() -> None:
    """Test the login interface components."""
    try:
        # Create test app_data
        app_data = {}
        
        # Test UI creation
        login_interface(app_data)
        assert app_data.get('username') is not None, "Username component should be created"
        assert app_data.get('password') is not None, "Password component should be created"
        assert app_data.get('login_button') is not None, "Login button should be created"
        assert app_data.get('register_button') is not None, "Register button should be created"
        assert app_data.get('error_message') is not None, "Error message component should be created"
        assert app_data.get('username_state') is not None, "Username state should be created"
        assert app_data.get('logged_in_state') is not None, "Logged in state should be created"
        assert app_data.get('chat_id_state') is not None, "Chat ID state should be created"
        assert app_data.get('chat_history_state') is not None, "Chat history state should be created"
        
        print("test_login_interface: PASSED")
    except Exception as e:
        print(f"test_login_interface: FAILED - {e}")
        raise

# --- Test Block for login.py (simulating app.py's main logic) ---
if __name__ == "__main__":
    # Create test app_data
    app_data = {}
    
    # Create the interface
    with gr.Blocks() as app:
        login_interface(app_data)
        
        # Add login button click event
        app_data['login_button'].click(
            fn=do_login,
            inputs=[app_data['username'], app_data['password']],
            outputs=[
                app_data['logged_in_state'],
                app_data['username_state'],
                app_data['login_container_comp']
            ]
        )
        
        # Add register button click event
        app_data['register_button'].click(
            fn=do_register,
            inputs=[app_data['username'], app_data['password']],
            outputs=[
                app_data['logged_in_state'],
                app_data['username_state'],
                app_data['login_container_comp']
            ]
        )
    
    app.launch()

if __name__ == "__main__":
    test_login_interface()
