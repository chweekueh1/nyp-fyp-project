# login_and_register.py
#!/usr/bin/env python3
"""Login and Registration Interface Module.

This module provides the login and registration interface components
for the NYP FYP Chatbot application.
"""

import gradio as gr
from infra_utils import setup_logging
from backend.auth import do_login, do_register
from backend.config import ALLOWED_EMAILS

logger = setup_logging()


def login_interface(
    logged_in_state: gr.State,  # ACCEPT PASSED-IN STATE from app.py
    username_state: gr.State,  # ACCEPT PASSED-IN STATE from app.py
    is_register_mode: gr.State,  # ACCEPT PASSED-IN STATE from app.py
) -> tuple:
    """Create the login and registration interface components."""

    # State variables for password visibility (managed locally within this UI part)
    password_visible = gr.State(False)
    confirm_password_visible = gr.State(False)

    # Create all components individually within a Column context
    with gr.Column(elem_id="login_register_container") as main_container:
        gr.Markdown("# 🚀 NYP FYP Chatbot", elem_id="auth_title")
        header_subtitle = gr.Markdown(
            "## 🔐 Login", elem_id="auth_subtitle"
        )  # Default to Login
        header_instruction = gr.Markdown(
            "Please log in to access the chatbot.", elem_id="auth_instruction"
        )  # Default to Login

        error_message = gr.Markdown("", elem_id="auth_error_message", visible=True)

        username_input = gr.Textbox(
            label="Username",
            placeholder="Enter your username",
            elem_id="username_input",
        )
        email_input = gr.Textbox(
            label="Email",
            placeholder="Enter your authorized email address",
            elem_id="email_input",
            visible=False,  # Initially hidden for login mode
        )
        email_info = gr.Markdown(
            f"**Note:** Only emails from `{', '.join(ALLOWED_EMAILS)}` are allowed for registration.",
            elem_id="email_info",
            visible=False,  # Initially hidden for login mode
        )
        password_input = gr.Textbox(
            label="Password",
            placeholder="Enter your password",
            type="password",
            elem_id="password_input",
        )
        show_password_btn = gr.Button("👁️", elem_id="show_password_btn", size="sm")

        confirm_password_input = gr.Textbox(
            label="Confirm Password",
            placeholder="Confirm your password",
            type="password",
            visible=False,  # Initially hidden for login mode
            elem_id="confirm_password_input",
        )
        show_confirm_btn = gr.Button(
            "👁️", elem_id="show_confirm_btn", size="sm", visible=False
        )  # Initially hidden for login mode

        password_requirements = gr.Markdown(
            """
        **Password Requirements:**
        <ul style="margin-top: 5px; margin-bottom: 5px;">
            <li>Minimum 8 characters</li>
            <li>At least one uppercase letter</li>
            <li>At least one lowercase letter</li>
            <li>At least one digit</li>
        </ul>
        """,
            visible=False,  # Initially hidden for login mode
            elem_id="password_requirements",
        )

        primary_btn = gr.Button(
            "Login", variant="primary", elem_id="primary_auth_btn"
        )  # Default to Login
        secondary_btn = gr.Button(
            "Don't have an account? Register",
            variant="secondary",
            elem_id="secondary_auth_btn",
        )  # Default to Register prompt

    # Event handlers (restored from older version, adapted for passed-in states)
    # Password toggle handlers
    def toggle_password(is_visible: bool) -> tuple:
        """Toggle password visibility."""
        if is_visible:
            return gr.update(type="password"), "👁️", False
        else:
            return gr.update(type="text"), "🙈", True

    def toggle_confirm_password(is_visible: bool) -> tuple:
        """Toggle confirm password visibility."""
        if is_visible:
            return gr.update(type="password"), "👁️", False
        else:
            return gr.update(type="text"), "🙈", True

    # Form switching handlers (adapted for passed-in is_register_mode)
    def switch_to_register() -> tuple:
        """Switch to register mode - show register fields and update labels."""
        return (
            gr.update(value=True),  # is_register_mode = True
            gr.update(value="## 📝 Register"),  # header_subtitle
            gr.update(
                value="Create a new account to access the chatbot."
            ),  # header_instruction
            gr.update(
                label="Username", placeholder="Choose a username (3-20 characters)"
            ),  # username_input
            gr.update(visible=True),  # email_input
            gr.update(visible=True),  # email_info
            gr.update(
                label="Password",
                placeholder="Choose a strong password (min 8 characters)",
            ),  # password_input
            gr.update(visible=True),  # confirm_password_input
            gr.update(visible=True),  # show_confirm_btn
            gr.update(visible=True),  # password_requirements
            gr.update(value="Register Account", variant="primary"),  # primary_btn
            gr.update(value="Back to Login", variant="secondary"),  # secondary_btn
            gr.update(
                value="", visible=False
            ),  # error_message (clear any previous errors)
        )

    def switch_to_login() -> tuple:
        """Switch to login mode - hide register fields and update labels."""
        return (
            gr.update(value=False),  # is_register_mode = False
            gr.update(value="## 🔐 Login"),  # header_subtitle
            gr.update(
                value="Please log in to access the chatbot."
            ),  # header_instruction
            gr.update(
                label="Username",
                placeholder="Enter your username",
            ),  # username_input
            gr.update(visible=False),  # email_input
            gr.update(visible=False),  # email_info
            gr.update(
                label="Password", placeholder="Enter your password"
            ),  # password_input
            gr.update(visible=False),  # confirm_password_input
            gr.update(visible=False),  # show_confirm_btn
            gr.update(visible=False),  # password_requirements
            gr.update(value="Login", variant="primary"),  # primary_btn
            gr.update(
                value="Don't have an account? Register", variant="secondary"
            ),  # secondary_btn
            gr.update(
                value="", visible=False
            ),  # error_message (clear any previous errors)
        )

    # Wire up password toggle events
    show_password_btn.click(
        fn=toggle_password,
        inputs=[password_visible],
        outputs=[password_input, show_password_btn, password_visible],
        queue=False,  # UI responsiveness
    )

    show_confirm_btn.click(
        fn=toggle_confirm_password,
        inputs=[confirm_password_visible],
        outputs=[
            confirm_password_input,
            show_confirm_btn,
            confirm_password_visible,
        ],
        queue=False,  # UI responsiveness
    )

    # Wire up form switching events
    def handle_secondary_btn_click_logic(current_is_register_mode_val: bool) -> tuple:
        """Logic for secondary button click - switches between login/register modes."""
        if current_is_register_mode_val:
            return switch_to_login()
        else:
            return switch_to_register()

    secondary_btn.click(
        fn=handle_secondary_btn_click_logic,
        inputs=[is_register_mode],  # Pass the value of the gr.State object
        outputs=[
            is_register_mode,  # Update the state itself
            header_subtitle,
            header_instruction,
            username_input,
            email_input,
            email_info,
            password_input,
            confirm_password_input,
            show_confirm_btn,
            password_requirements,
            primary_btn,
            secondary_btn,
            error_message,
        ],
        queue=False,  # UI responsiveness
    )

    # Wire up primary button (login or register based on mode)
    primary_btn.click(
        fn=handle_primary_btn_click,
        inputs=[
            is_register_mode,  # Boolean value of the state
            username_input,
            email_input,
            password_input,
            confirm_password_input,
            logged_in_state,  # Pass the current state objects
            username_state,  # Pass the current state objects
        ],
        outputs=[
            error_message,
            logged_in_state,
            username_state,
        ],  # Update the states directly
        queue=True,  # Allow queuing for backend operations
    )

    # Add Enter key support
    password_input.submit(
        fn=handle_primary_btn_click,
        inputs=[
            is_register_mode,
            username_input,
            email_input,
            password_input,
            confirm_password_input,
            logged_in_state,
            username_state,
        ],
        outputs=[error_message, logged_in_state, username_state],
        queue=True,
    )

    confirm_password_input.submit(
        fn=handle_primary_btn_click,
        inputs=[
            is_register_mode,
            username_input,
            email_input,
            password_input,
            confirm_password_input,
            logged_in_state,
            username_state,
        ],
        outputs=[error_message, logged_in_state, username_state],
        queue=True,
    )

    return (
        main_container,  # 1
        error_message,  # 2
        username_input,  # 3
        email_input,  # 4
        password_input,  # 5
        confirm_password_input,  # 6
        primary_btn,  # 7
        secondary_btn,  # 8
        show_password_btn,  # 9
        show_confirm_btn,  # 10
        password_visible,  # 11
        confirm_password_visible,  # 12
        header_subtitle,  # 13
        header_instruction,  # 14
        email_info,  # 15
        password_requirements,  # 16
    )


# The handle_primary_btn_click function (modified to correctly update passed-in gr.State objects)
async def handle_primary_btn_click(
    mode: bool,  # This is the boolean value of is_register_mode_state
    username_val: str,
    email_val: str,
    password_val: str,
    confirm_password_val: str,
    logged_in_state: gr.State,  # Passed-in gr.State object
    username_state: gr.State,  # Passed-in gr.State object
) -> tuple:
    """Handles the primary button click for login or registration."""

    allowed_domains = ALLOWED_EMAILS

    # Common validation
    if not username_val or not password_val:
        return (
            gr.update(value="Username and password are required.", visible=True),
            gr.update(value=logged_in_state),
            gr.update(value=username_state),
        )

    if mode:  # Register mode
        if not email_val or "@" not in email_val:
            return (
                gr.update(
                    value="Valid email is required for registration.", visible=True
                ),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )

        if "@" in username_val:
            return (
                gr.update(value="Username cannot be an email address.", visible=True),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )

        email_domain = email_val.split("@")[1].lower()
        if email_domain not in allowed_domains:
            return (
                gr.update(
                    value=f"Email domain '{email_domain}' is not authorized. Allowed domains: {', '.join(allowed_domains)}",
                    visible=True,
                ),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )

        if password_val != confirm_password_val:
            return (
                gr.update(value="Passwords do not match.", visible=True),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )

        # Call the do_register function
        register_result = await do_register(username_val, password_val, email_val)
        if register_result["success"]:
            # On successful registration, we do not log the user in.
            # We display a success message and keep the login state as-is.
            return (
                gr.update(
                    value="Registration successful! Please log in.", visible=True
                ),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )
        else:
            return (
                gr.update(value=register_result["message"], visible=True),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )

    else:  # Login mode
        login_result = await do_login(username_val, password_val)
        if login_result["success"]:
            # On successful login, we update the logged_in_state to True
            # and the username_state to the logged-in username.
            # Assuming do_login returns the username on success.
            return (
                gr.update(value=login_result["message"], visible=True),
                gr.update(value=True),
                gr.update(value=username_val),
            )
        else:
            # On failed login, we display the error message and keep the states as-is.
            return (
                gr.update(value=login_result["message"], visible=True),
                gr.update(value=logged_in_state),
                gr.update(value=username_state),
            )
