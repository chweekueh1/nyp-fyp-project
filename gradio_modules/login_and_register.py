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
from hashing import is_password_complex

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
    Returns the users dict (not the whole file).
    """
    if not os.path.exists(USER_DB_PATH):
        return {}
    try:
        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
            users = data.get("users", {})
            if not isinstance(users, dict):
                logging.warning("Invalid users data format, returning empty users dict")
                return {}
            return users
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding users data: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error loading users data: {e}")
        return {}

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
            json.dump({"users": users_data}, f, indent=2)
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
    """
    Create the login/register interface components with proper error handling and mode switching.
    This function initializes the UI components for login and registration, and sets up event handlers for button clicks.
    """
    if not isinstance(app_data, dict):
        app_data = {}

    # State to track mode
    if 'is_registering' not in app_data:
        app_data['is_registering'] = gr.State(False)
    if 'main_app_container_comp' not in app_data:
        app_data['main_app_container_comp'] = gr.Column(visible=False)

    # Create login container and add it to app_data
    with gr.Column(visible=True) as login_container:
        app_data['logout_button'] = gr.Button("Logout", visible=False, elem_classes=["secondary"])
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
            app_data['to_register_button'] = gr.Button("Register", elem_classes=["secondary"])
            app_data['register_account_button'] = gr.Button("Register Account", visible=False, elem_classes=["primary"])
            app_data['back_to_login_button'] = gr.Button("Back to Login", visible=False, elem_classes=["secondary"])
        app_data['error_message'] = gr.Markdown(visible=False)
        app_data['username_state'] = gr.State("")
        app_data['logged_in_state'] = gr.State(False)
        app_data['chat_id_state'] = gr.State("")
        app_data['chat_history_state'] = gr.State([])
        app_data['password_visible'] = gr.State(False)

    # Store login container in app_data
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
        """
        Switch the UI to register mode, hiding login-related components and showing register-related components.
        """
        return (
            gr.update(visible=False),  # login button
            gr.update(visible=False),  # to_register_button
            gr.update(visible=True),   # register_account_button
            gr.update(visible=True),   # back_to_login_button
            gr.update(visible=True),   # confirm_password
            True
        )
    app_data['to_register_button'].click(
        fn=to_register_mode,
        inputs=[app_data['is_registering']],
        outputs=[
            app_data['login_button'],
            app_data['to_register_button'],
            app_data['register_account_button'],
            app_data['back_to_login_button'],
            app_data['confirm_password'],
            app_data['is_registering']
        ]
    )

    # Switch to login mode
    def to_login_mode(is_registering):
        """
        Switch the UI to login mode, hiding register-related components and showing login-related components.
        """
        return (
            gr.update(visible=True),   # login button
            gr.update(visible=True),   # to_register_button
            gr.update(visible=False),  # register_account_button
            gr.update(visible=False),  # back_to_login_button
            gr.update(visible=False),  # confirm_password
            False
        )
    app_data['back_to_login_button'].click(
        fn=to_login_mode,
        inputs=[app_data['is_registering']],
        outputs=[
            app_data['login_button'],
            app_data['to_register_button'],
            app_data['register_account_button'],
            app_data['back_to_login_button'],
            app_data['confirm_password'],
            app_data['is_registering']
        ]
    )

    # Actual login action
    def safe_login(username, password):
        """
        Handle the login action, validating inputs and calling the backend login function.
        Returns the appropriate UI updates based on the login result.
        """
        if not username or not password:
            logger.warning("Login attempt with empty fields")
            # Only use gr.update for UI components, raw values for gr.State
            result = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="Please enter both username and password"))
            logger.info(f"safe_login returning: {result}")
            return result
        result = do_login(username, password)
        # If login is successful, hide login_container and show main_app_container
        if result[0]:
            out = (True, result[1], gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False))
            logger.info(f"safe_login returning: {out}")
            return out
        else:
            error_msg = result[3] if len(result) > 3 and isinstance(result[3], dict) else gr.update(visible=True, value="Login failed")
            out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), error_msg)
            logger.info(f"safe_login returning: {out}")
            return out
    app_data['login_button'].click(
        fn=safe_login,
        inputs=[app_data['username'], app_data['password']],
        outputs=[
            app_data['logged_in_state'],
            app_data['username_state'],
            app_data['login_container_comp'],
            app_data['main_app_container_comp'],
            app_data['logout_button'],
            app_data['error_message']
        ]
    )

    # Actual register action
    def safe_register(*args):
        """
        Handle the registration action, calling the backend register function and returning appropriate UI updates.
        """
        result = safe_register_impl(*args)
        # If registration is successful, switch to login mode and show success message
        if result[0] is False and isinstance(result[3], dict) and result[3].get("value", "").startswith("Registration successful"):
            out = (
                False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), result[3]
            )
            logger.info(f"safe_register returning (success): {out}")
            return out
        error_msg = result[3] if len(result) > 3 and isinstance(result[3], dict) else gr.update(visible=True, value="Registration failed")
        out = (
            result[0] if len(result) > 0 else False,
            result[1] if len(result) > 1 else "",
            result[2] if len(result) > 2 else gr.update(visible=True),
            result[3] if len(result) > 3 and isinstance(result[3], dict) else gr.update(visible=False),
            result[4] if len(result) > 4 else gr.update(visible=False),
            error_msg
        )
        logger.info(f"safe_register returning (fail): {out}")
        return out

    def safe_register_impl(username, password, confirm_password, is_registering, login_button, confirm_password_box, to_register_button, register_account_button, back_to_login_button, error_message_box):
        """
        Implementation of the registration logic, calling the backend register function and handling exceptions.
        """
        try:
            return do_register(username, password, confirm_password, is_registering, login_button, confirm_password_box, to_register_button, register_account_button, back_to_login_button, error_message_box)
        except Exception as e:
            logger.error(f"Exception in safe_register: {e}")
            return False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="An unexpected error occurred")

    app_data['register_account_button'].click(
        fn=safe_register,
        inputs=[app_data['username'], app_data['password'], app_data['confirm_password'], app_data['is_registering'], app_data['login_button'], app_data['confirm_password'], app_data['to_register_button'], app_data['register_account_button'], app_data['back_to_login_button'], app_data['error_message']],
        outputs=[app_data['logged_in_state'], app_data['username_state'], app_data['login_container_comp'], app_data['main_app_container_comp'], app_data['logout_button'], app_data['error_message']]
    )

    # Logout button (shown only when logged in)
    def do_logout():
        """
        Handle the logout action, resetting the UI to the login state.
        """
        # Only use gr.update for UI components, raw values for gr.State
        out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
        logger.info(f"do_logout returning: {out}")
        return out
    app_data['logout_button'].click(
        fn=do_logout,
        outputs=[app_data['logged_in_state'], app_data['username_state'], app_data['login_container_comp'], app_data['main_app_container_comp'], app_data['logout_button'], app_data['error_message']]
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

def toggle_password_visibility(current_visible):
    # Toggle between password and text
    return not current_visible, gr.update(type="text" if not current_visible else "password"), gr.update(value="👁️" if not current_visible else "👁️‍🗨️")

def do_login(username: str, password: str):
    if not username or not password:
        logger.warning("Login attempt with empty fields")
        # Only use gr.update for UI components, raw values for gr.State
        result = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="Please fill in all fields"))
        logger.info(f"do_login returning: {result}")
        return result
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        backend_result = loop.run_until_complete(backend_login(username, password))
        loop.close()
        if backend_result and backend_result.get('code') == '200':
            out = (True, username, gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False))
            logger.info(f"do_login returning: {out}")
            return out
        else:
            error_msg = backend_result.get('message', 'Invalid username or password')
            out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=error_msg))
            logger.info(f"do_login returning: {out}")
            return out
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="An unexpected error occurred"))
        logger.info(f"do_login returning: {out}")
        return out

def do_register(username: str, password: str, confirm_password: str, is_registering: bool, login_button, confirm_password_box, register_button, proceed_register_button, is_registering_state, error_message_box):
    # Validate inputs
    if not username or not password or not confirm_password:
        logger.warning("Registration attempt with empty fields")
        result = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="All fields are required"))
        logger.info(f"do_register returning: {result}")
        return result
    if password != confirm_password:
        logger.warning(f"Password mismatch for user {username}")
        result = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="Passwords do not match"))
        logger.info(f"do_register returning: {result}")
        return result
    is_valid, complexity_msg = is_password_complex(password)
    if not is_valid:
        logger.warning(f"Password complexity failed for user {username}: {complexity_msg}")
        result = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=complexity_msg))
        logger.info(f"do_register returning: {result}")
        return result
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        backend_result = loop.run_until_complete(backend_register(username, password))
        loop.close()
        if backend_result and backend_result.get('code') == '200':
            out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="Registration successful! Please log in."))
            logger.info(f"do_register returning: {out}")
            return out
        else:
            error_msg = backend_result.get('message', 'Registration failed')
            out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=error_msg))
            logger.info(f"do_register returning: {out}")
            return out
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        out = (False, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value="An unexpected error occurred"))
        logger.info(f"do_register returning: {out}")
        return out

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
        assert app_data.get('to_register_button') is not None, "Register button should be created"
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
                app_data['login_container_comp'],
                app_data['main_app_container_comp'],
                app_data['logout_button'],
                app_data['error_message']
            ]
        )
        
        # Add register button click event
        app_data['to_register_button'].click(
            fn=do_register,
            inputs=[app_data['username'], app_data['password']],
            outputs=[
                app_data['logged_in_state'],
                app_data['username_state'],
                app_data['login_container_comp'],
                app_data['main_app_container_comp'],
                app_data['logout_button'],
                app_data['error_message']
            ]
        )
    
    app.launch()

if __name__ == "__main__":
    test_login_interface()
