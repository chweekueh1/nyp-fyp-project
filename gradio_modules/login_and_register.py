#!/usr/bin/env python3
"""
Login and Registration Interface Module

This module provides the login and registration interface components
for the NYP FYP Chatbot application.
"""

import gradio as gr
import asyncio
from utils import setup_logging

logger = setup_logging()

def login_interface(setup_events=True):
    """
    Create the login and registration interface with dynamic form switching.

    This version shows only one form at a time for better performance and UX.
    Features:
    - Dynamic switching between login and registration
    - Password visibility toggles
    - Email validation
    - Password requirements
    - Proper state management

    Args:
        setup_events: Whether to set up event handlers (default: True)

    Returns:
        Tuple of components and state variables
    """

    # State variables
    logged_in_state = gr.State(False)
    username_state = gr.State("")
    is_register_mode = gr.State(False)  # Track which form is active

    # State variables for password visibility
    password_visible = gr.State(False)
    confirm_password_visible = gr.State(False)

    # Create all components individually (avoid Gradio 5.x context manager issues)
    # Header that changes based on mode
    header_title = gr.Markdown("# 🚀 NYP FYP Chatbot", elem_id="auth_title")
    header_subtitle = gr.Markdown("## 🔐 Login", elem_id="auth_subtitle")
    header_instruction = gr.Markdown("Please log in to access the chatbot.", elem_id="auth_instruction")

    # Dynamic form fields
    username_input = gr.Textbox(
        label="Username or Email",
        placeholder="Enter your username or email",
        elem_id="username_input"
    )

    # Email field (only visible in register mode)
    email_input = gr.Textbox(
        label="Email",
        placeholder="Enter your authorized email address",
        elem_id="email_input",
        visible=False
    )

    # Email domains info (only visible in register mode)
    email_info = gr.Markdown("""
    **Authorized Email Domains:**
    - @nyp.edu.sg (NYP staff/faculty)
    - @student.nyp.edu.sg (NYP students)
    - Selected test emails for development
    """, elem_id="email_info", visible=False)

    password_input = gr.Textbox(
        label="Password",
        placeholder="Enter your password",
        type="password",
        elem_id="password_input"
    )
    show_password_btn = gr.Button("👁️", elem_id="show_password_btn", size="sm")

    # Confirm password field (only visible in register mode)
    confirm_password_input = gr.Textbox(
        label="Confirm Password",
        placeholder="Confirm your password",
        type="password",
        elem_id="confirm_password_input",
        visible=False
    )
    show_confirm_btn = gr.Button("👁️", elem_id="show_confirm_btn", size="sm", visible=False)

    # Password requirements (only visible in register mode)
    password_requirements = gr.Markdown("""
    **Password Requirements:**
    - At least 8 characters long
    - Contains uppercase and lowercase letters
    - Contains at least one number
    - Contains at least one special character (!@#$%^&*)
    """, elem_id="password_requirements", visible=False)

    # Action buttons
    primary_btn = gr.Button("Login", variant="primary", elem_id="primary_btn")
    secondary_btn = gr.Button("Register", variant="secondary", elem_id="secondary_btn")

    # Error/success messages
    error_message = gr.Markdown(visible=False, elem_id="error_message")

    # Create a simple container without context manager
    main_container = gr.Column(elem_classes=["auth-container"])

    if not setup_events:
        return (
            logged_in_state, username_state, is_register_mode, main_container, error_message,
            username_input, email_input, password_input, confirm_password_input,
            primary_btn, secondary_btn, show_password_btn, show_confirm_btn,
            password_visible, confirm_password_visible,
            header_subtitle, header_instruction, email_info, password_requirements
        )

    # Event handlers (only when setup_events=True)
    if setup_events:
        def handle_login(username, password):
            logger.info(f"Login attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Username is required")
            if not password or not password.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Password is required")

            try:
                from backend import do_login

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_login(username.strip(), password))
                loop.close()

                if result.get("code") == "200":
                    actual_username = result.get("username", username.strip())
                    logger.info(f"Login successful for user: {actual_username}")
                    return True, actual_username, gr.update(visible=False)
                else:
                    error_msg = result.get("message", "Login failed")
                    logger.warning(f"Login failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=True, value=f"❌ **Login failed:** {error_msg}")
            except Exception as e:
                logger.error(f"Login error for user {username}: {e}")
                return False, "", gr.update(visible=True, value=f"❌ **System error:** {str(e)}")

        def handle_register(username, email, password, confirm):
            logger.info(f"Registration attempt for user: {username}")

            # Input validation
            if not username or not username.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Username is required")
            if not email or not email.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Email is required")
            if not password or not password.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Password is required")
            if not confirm or not confirm.strip():
                return False, "", gr.update(visible=True, value="❌ **Error:** Please confirm your password")
            if password != confirm:
                return False, "", gr.update(visible=True, value="❌ **Error:** Passwords do not match")

            try:
                from backend import do_register

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(do_register(username.strip(), password, email.strip()))
                loop.close()

                if result.get("code") == "200":
                    logger.info(f"Registration successful for user: {username}")
                    # Switch back to login mode and show success message
                    return False, "", gr.update(visible=True, value="✅ **Registration successful!** Please log in with your new account.")
                else:
                    error_msg = result.get("message", "Registration failed")
                    logger.warning(f"Registration failed for user {username}: {error_msg}")
                    return False, "", gr.update(visible=True, value=f"❌ **Registration failed:** {error_msg}")
            except Exception as e:
                logger.error(f"Registration error for user {username}: {e}")
                return False, "", gr.update(visible=True, value=f"❌ **System error:** {str(e)}")

        # Password toggle handlers
        def toggle_password(is_visible):
            if is_visible:
                return gr.update(type="password"), "👁️", False
            else:
                return gr.update(type="text"), "🙈", True

        def toggle_confirm_password(is_visible):
            if is_visible:
                return gr.update(type="password"), "👁️", False
            else:
                return gr.update(type="text"), "🙈", True

        # Form switching handlers
        def switch_to_register():
            """Switch to register mode - show register fields and update labels."""
            return (
                True,  # is_register_mode = True
                gr.update(value="## 📝 Register"),  # header_subtitle
                gr.update(value="Create a new account to access the chatbot."),  # header_instruction
                gr.update(label="Username", placeholder="Choose a username (3-20 characters)"),  # username_input
                gr.update(visible=True),  # email_input
                gr.update(visible=True),  # email_info
                gr.update(label="Password", placeholder="Choose a strong password (min 8 characters)"),  # password_input
                gr.update(visible=True),  # confirm_password_input
                gr.update(visible=True),  # show_confirm_btn
                gr.update(visible=True),  # password_requirements
                gr.update(value="Register Account", variant="primary"),  # primary_btn
                gr.update(value="Back to Login", variant="secondary"),  # secondary_btn
                gr.update(visible=False)  # error_message
            )

        def switch_to_login():
            """Switch to login mode - hide register fields and update labels."""
            return (
                False,  # is_register_mode = False
                gr.update(value="## 🔐 Login"),  # header_subtitle
                gr.update(value="Please log in to access the chatbot."),  # header_instruction
                gr.update(label="Username or Email", placeholder="Enter your username or email"),  # username_input
                gr.update(visible=False),  # email_input
                gr.update(visible=False),  # email_info
                gr.update(label="Password", placeholder="Enter your password"),  # password_input
                gr.update(visible=False),  # confirm_password_input
                gr.update(visible=False),  # show_confirm_btn
                gr.update(visible=False),  # password_requirements
                gr.update(value="Login", variant="primary"),  # primary_btn
                gr.update(value="Register", variant="secondary"),  # secondary_btn
                gr.update(visible=False)  # error_message
            )

        # Wire up password toggle events
        show_password_btn.click(
            fn=toggle_password,
            inputs=[password_visible],
            outputs=[password_input, show_password_btn, password_visible]
        )

        show_confirm_btn.click(
            fn=toggle_confirm_password,
            inputs=[confirm_password_visible],
            outputs=[confirm_password_input, show_confirm_btn, confirm_password_visible]
        )

        # Wire up form switching events
        def handle_secondary_btn_click(is_register_mode):
            """Handle secondary button click - switches between login/register modes."""
            if is_register_mode:
                # Currently in register mode, switch to login
                return switch_to_login()
            else:
                # Currently in login mode, switch to register
                return switch_to_register()

        secondary_btn.click(
            fn=handle_secondary_btn_click,
            inputs=[is_register_mode],
            outputs=[
                is_register_mode, header_subtitle, header_instruction, username_input,
                email_input, email_info, password_input, confirm_password_input,
                show_confirm_btn, password_requirements, primary_btn, secondary_btn, error_message
            ]
        )

        # Wire up primary button (login or register based on mode)
        def handle_primary_btn_click(is_register_mode, username, email, password, confirm_password):
            """Handle primary button click - login or register based on current mode."""
            if is_register_mode:
                # Register mode
                return handle_register(username, email, password, confirm_password)
            else:
                # Login mode
                return handle_login(username, password)

        primary_btn.click(
            fn=handle_primary_btn_click,
            inputs=[is_register_mode, username_input, email_input, password_input, confirm_password_input],
            outputs=[logged_in_state, username_state, error_message]
        )

        # Add Enter key support
        password_input.submit(
            fn=handle_primary_btn_click,
            inputs=[is_register_mode, username_input, email_input, password_input, confirm_password_input],
            outputs=[logged_in_state, username_state, error_message]
        )

        confirm_password_input.submit(
            fn=handle_primary_btn_click,
            inputs=[is_register_mode, username_input, email_input, password_input, confirm_password_input],
            outputs=[logged_in_state, username_state, error_message]
        )

    return (
        logged_in_state, username_state, is_register_mode, main_container, error_message,
        username_input, email_input, password_input, confirm_password_input,
        primary_btn, secondary_btn, show_password_btn, show_confirm_btn,
        password_visible, confirm_password_visible,
        header_subtitle, header_instruction, email_info, password_requirements
    )
