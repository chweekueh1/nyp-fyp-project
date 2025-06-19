import gradio as gr
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import tz
from dateutil.parser import parse as dateutil_parse
import json
import os
import sys 
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Tuple, Optional, Union, List
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from backend import (
    do_login as backend_login,
    do_register as backend_register,
    USER_DB_PATH,
    CHAT_SESSIONS_PATH
)
from utils import setup_logging
from hashing import is_password_complex

# Set up logging
logger = setup_logging()

# --- Configuration ---
load_dotenv() 

UTC_PLUS_8 = tz.tzoffset("UTC+8", timedelta(hours=8))
from_zone = tz.tzutc() 
to_zone = tz.tzlocal() 

# --- Helper Functions ---
def get_datetime_from_timestamp(ts_string: str) -> datetime:
    if not isinstance(ts_string, str) or not ts_string:
        return datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8)
        
    try:
        dt_obj = dateutil_parse(ts_string)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(UTC_PLUS_8)
    except ValueError as e:
        logger.warning(f"Could not parse timestamp '{ts_string}'. Error: {e}. Using timezone-aware datetime.min as fallback.")
        return datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8)

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password complexity."""
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

# --- UI Functions ---
def login_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
    is_registering: gr.State,
    main_container: gr.Column,
    logout_button: gr.Button,
    user_info: gr.Markdown,
    login_container: gr.Column,  # <-- Add this
    all_chat_histories_state: gr.State,
    selected_chat_id_state: gr.State
) -> None:
    """Create the login interface with all necessary components and states."""
    
    # Use the passed-in login_container
    with login_container:
        # Initialize states
        states = {
            'logged_in': logged_in_state,
            'username': username_state,
            'current_chat_id': current_chat_id_state,
            'chat_history': chat_history_state,
            'is_registering': is_registering,
            'password_visible': gr.State(False)
        }
        
        with gr.Column(visible=True) as login_container:
            username = gr.Textbox(
                label="Username",
                placeholder="Enter your username",
                show_label=True
            )
            
            with gr.Row():
                password = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    show_label=True,
                    type="password",
                    elem_id="password_input"
                )
                password_visibility = gr.Button(
                    "👁️",
                    elem_id="password_visibility",
                    size="sm"
                )
                
            confirm_password = gr.Textbox(
                label="Confirm Password",
                placeholder="Confirm your password",
                show_label=True,
                type="password",
                visible=False
            )
            
            with gr.Row():
                login_button = gr.Button("Login", elem_classes=["primary"])
                to_register_button = gr.Button("Register", elem_classes=["secondary"])
                register_account_button = gr.Button("Register Account", visible=False, elem_classes=["primary"])
                back_to_login_button = gr.Button("Back to Login", visible=False, elem_classes=["secondary"])
                
            error_message = gr.Markdown(visible=False)
    
        # --- Event Handlers ---
        def handle_login(username: str, password: str):
            if not username or not password:
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="Please fill in all fields"),  # error_message
                    "",     # user_info
                    [],     # chat_history_state
                    ""      # current_chat_id_state
                )
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                backend_result = loop.run_until_complete(backend_login(username, password))
                loop.close()
                if backend_result.get('code') != '200':
                    return (
                        False,  # logged_in
                        "",    # username
                        gr.update(visible=True),   # login_container
                        gr.update(visible=False),  # main_container
                        gr.update(visible=False),  # logout_button
                        gr.update(visible=True, value=backend_result.get('message', 'Invalid username or password')),  # error_message
                        "",     # user_info
                        [],     # chat_history_state
                        ""      # current_chat_id_state
                    )
                # Load chat history and chat_id after successful login
                from backend import get_chat_history
                # You may want to select the most recent chat_id, here we just use a default or empty string
                chat_id = ""
                history = get_chat_history(chat_id, username)
                history = [list(pair) for pair in history] if history else []
                return (
                    True,   # logged_in
                    username,  # username
                    gr.update(visible=False),  # login_container
                    gr.update(visible=True),   # main_container
                    gr.update(visible=True),   # logout_button
                    gr.update(visible=False),  # error_message
                    f"Welcome, {username}!",   # user_info
                    history,                   # chat_history_state
                    chat_id                    # current_chat_id_state
                )
            except Exception as e:
                logger.error(f"Unexpected error during login: {e}")
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="An unexpected error occurred"),  # error_message
                    "",     # user_info
                    [],     # chat_history_state
                    ""      # current_chat_id_state
                )
        
        def handle_register(username: str, password: str, confirm_password: str, is_registering: bool) -> Tuple[bool, str, Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], str]:
            """Handle registration attempt."""
            if not username or not password or not confirm_password:
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="All fields are required"),  # error_message
                    ""     # user_info
                )
                
            if password != confirm_password:
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="Passwords do not match"),  # error_message
                    ""     # user_info
                )
                
            is_valid, complexity_msg = validate_password(password)
            if not is_valid:
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value=complexity_msg),  # error_message
                    ""     # user_info
                )
                
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                backend_result = loop.run_until_complete(backend_register(username, password))
                loop.close()
                
                if backend_result.get('code') != '200':
                    return (
                        False,  # logged_in
                        "",    # username
                        gr.update(visible=True),   # login_container
                        gr.update(visible=False),  # main_container
                        gr.update(visible=False),  # logout_button
                        gr.update(visible=True, value=backend_result.get('message', 'Registration failed')),  # error_message
                        ""     # user_info
                    )
                    
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="Registration successful! Please log in."),  # error_message
                    ""     # user_info
                )
            except Exception as e:
                logger.error(f"Unexpected error during registration: {e}")
                return (
                    False,  # logged_in
                    "",    # username
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    gr.update(visible=False),  # logout_button
                    gr.update(visible=True, value="An unexpected error occurred"),  # error_message
                    ""     # user_info
                )
        
        def toggle_password_visibility(current_visible: bool) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
            """Toggle password visibility."""
            return (
                not current_visible,
                gr.update(type="text" if not current_visible else "password"),
                gr.update(value="👁️" if not current_visible else "👁️‍🗨️")
            )
        
        def switch_to_register(is_registering: bool) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], bool]:
            """Switch to register mode."""
            return (
                gr.update(visible=False),  # login button
                gr.update(visible=False),  # to_register_button
                gr.update(visible=True),   # register_account_button
                gr.update(visible=True),   # back_to_login_button
                gr.update(visible=True),   # confirm_password
                True                       # is_registering
            )
        
        def switch_to_login(is_registering: bool) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], bool]:
            """Switch to login mode."""
            return (
                gr.update(visible=True),   # login button
                gr.update(visible=True),   # to_register_button
                gr.update(visible=False),  # register_account_button
                gr.update(visible=False),  # back_to_login_button
                gr.update(visible=False),  # confirm_password
                False                      # is_registering
            )
        
        # --- Event Bindings ---
        login_button.click(
            fn=handle_login,
            inputs=[username, password],
            outputs=[
                logged_in_state,
                username_state,
                login_container,
                main_container,
                logout_button,
                error_message,
                user_info,
                all_chat_histories_state,   # <-- Add this
                selected_chat_id_state      # <-- Add this
            ],
            api_name="login"
        )
        
        register_account_button.click(
            fn=handle_register,
            inputs=[username, password, confirm_password, states['is_registering']],
            outputs=[
                states['logged_in'],
                states['username'],
                login_container,  # This will be updated with visibility
                main_container,   # This will be updated with visibility
                logout_button,    # This will be updated with visibility
                error_message,
                user_info
            ],
            api_name="register"
        )
        
        password_visibility.click(
            fn=toggle_password_visibility,
            inputs=[states['password_visible']],
            outputs=[states['password_visible'], password, password_visibility],
            api_name="toggle_password"
        )
        
        to_register_button.click(
            fn=switch_to_register,
            inputs=[states['is_registering']],
            outputs=[
                login_button,
                to_register_button,
                register_account_button,
                back_to_login_button,
                confirm_password,
                states['is_registering']
            ],
            api_name="to_register"
        )
        
        back_to_login_button.click(
            fn=switch_to_login,
            inputs=[states['is_registering']],
            outputs=[
                login_button,
                to_register_button,
                register_account_button,
                back_to_login_button,
                confirm_password,
                states['is_registering']
            ],
            api_name="to_login"
        )

# Export the functions needed by main_app.py
__all__ = ['login_interface']

# Re-export backend functions with new names
do_login = backend_login
do_register = backend_register

def test_login_interface() -> None:
    """Test the login interface components."""
    try:
        # Create test states
        test_states = {
            'logged_in_state': gr.State(False),
            'username_state': gr.State(""),
            'current_chat_id_state': gr.State(""),
            'chat_history_state': gr.State([]),
            'is_registering': gr.State(False)
        }
        
        # Create test app
        with gr.Blocks() as app:
            with gr.Column(visible=False) as main_container:
                user_info = gr.Markdown(visible=False)
                logout_button = gr.Button("Logout", visible=False)
            login_interface(**test_states, main_container=main_container, logout_button=logout_button, user_info=user_info)
        
        # Verify components exist
        components = app.blocks
        
        # Initialize component flags
        has_username = False
        has_password = False
        has_login = False
        has_register = False
        has_error = False
        
        # Check each component
        for block in components:
            if isinstance(block, gr.Textbox):
                if block.label == "Username":
                    has_username = True
                elif block.label == "Password":
                    has_password = True
            elif isinstance(block, gr.Button):
                if block.value == "Login":
                    has_login = True
                elif block.value == "Register":
                    has_register = True
            elif isinstance(block, gr.Markdown):
                has_error = True
        
        # Verify all required components exist
        assert has_username, "Username component should be created"
        assert has_password, "Password component should be created"
        assert has_login, "Login button should be created"
        assert has_register, "Register button should be created"
        assert has_error, "Error message component should be created"
        
        print("test_login_interface: PASSED")
    except Exception as e:
        print(f"test_login_interface: FAILED - {e}")
        raise

if __name__ == "__main__":
    # Create test states
    test_states = {
        'logged_in_state': gr.State(False),
        'username_state': gr.State(""),
        'current_chat_id_state': gr.State(""),
        'chat_history_state': gr.State([]),
        'is_registering': gr.State(False)
    }
    
    # Create and launch app
    with gr.Blocks() as app:
        with gr.Column(visible=False) as main_container:
            user_info = gr.Markdown(visible=False)
            logout_button = gr.Button("Logout", visible=False)
        login_interface(**test_states, main_container=main_container, logout_button=logout_button, user_info=user_info)
    app.launch(debug=True, share=False)
