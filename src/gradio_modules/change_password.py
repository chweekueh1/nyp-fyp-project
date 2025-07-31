#!/usr/bin/env python3
"""
Change Password Interface Module

This module provides the change password interface for the NYP FYP Chatbot application.
Users can change their password through a modal popup with password visibility toggles.
"""

import time
from typing import Tuple
import gradio as gr
import logging
from backend.auth import change_password

logger = logging.getLogger(__name__)


def change_password_interface(
    username_state: gr.State, logged_in_state: gr.State, rate_limit_seconds: int = 60
) -> gr.Blocks:
    """
    Creates the change password UI components and returns the Blocks object for the tab content.
    The global button and last_change_time state are managed externally by app.py.

    :param username_state: Gradio State for the current username.
    :type username_state: gr.State
    :param logged_in_state: Gradio State for the login status.
    :type logged_in_state: gr.State
    :param rate_limit_seconds: Seconds to wait between password change attempts.
    :type rate_limit_seconds: int
    :return: The Blocks object containing the password change popup UI.
    :rtype: gr.Blocks
    """

    last_change_time_state = gr.State(0)

    # The actual password change popup UI, returned as a Blocks fragment for the tab
    with gr.Blocks(
        elem_id="change_password_popup", elem_classes=["change-password-popup"]
    ) as change_password_popup:
        gr.Markdown("## 🔐 Change Password", elem_id="change_password_title")
        gr.Markdown(
            "Please enter your current password and new password.",
            elem_id="change_password_instruction",
        )

        # Password fields with visibility toggles
        with gr.Row():
            old_password_input = gr.Textbox(
                label="Current Password",
                type="password",
                elem_id="old_password_input",
                placeholder="Enter your current password",
            )
            old_password_toggle = gr.Button(
                "👁️", size="sm", elem_id="old_password_toggle"
            )

        with gr.Row():
            new_password_input = gr.Textbox(
                label="New Password",
                type="password",
                elem_id="new_password_input",
                placeholder="Enter your new password",
            )
            new_password_toggle = gr.Button(
                "👁️", size="sm", elem_id="new_password_toggle"
            )

        with gr.Row():
            confirm_new_password_input = gr.Textbox(
                label="Confirm New Password",
                type="password",
                elem_id="confirm_new_password_input",
                placeholder="Confirm your new password",
            )
            confirm_new_password_toggle = gr.Button(
                "👁️", size="sm", elem_id="confirm_new_password_toggle"
            )

        # Password requirements markdown (now explicitly visible=True)
        gr.Markdown(
            """
            **Password Requirements:**
            - At least 8 characters long
            - Contains at least one uppercase letter
            - Contains at least one lowercase letter
            - Contains at least one digit
            - Contains at least one special character (e.g., !@#$%^&*)
            """,
            elem_id="password_requirements",
            visible=True,  # <--- ADDED explicit visible=True
        )

        # Message display for success/error
        change_password_message = gr.Markdown(
            "", visible=False, elem_id="change_password_message"
        )

        # Action buttons
        with gr.Row():
            submit_change_password_btn = gr.Button(
                "Change Password",
                variant="primary",
                elem_id="submit_change_password_btn",
            )
            cancel_change_password_btn = gr.Button(
                "Cancel", variant="secondary", elem_id="cancel_change_password_btn"
            )

        loading_indicator = gr.HTML(
            value="", visible=False, elem_classes=["loading-indicator"]
        )

    # Internal states for password visibility (these are local to this Blocks)
    old_password_visible = gr.State(False)
    new_password_visible = gr.State(False)
    confirm_new_password_visible = gr.State(False)

    # --- Event Handlers ---

    # Password visibility toggles
    old_password_toggle.click(
        fn=lambda x: (not x, "🙈" if not x else "👁️"),
        inputs=[old_password_visible],
        outputs=[old_password_visible, old_password_toggle],
        queue=False,
    ).then(
        fn=lambda x: gr.update(type="text" if x else "password"),
        inputs=[old_password_visible],
        outputs=[old_password_input],
        queue=False,
    )

    new_password_toggle.click(
        fn=lambda x: (not x, "🙈" if not x else "👁️"),
        inputs=[new_password_visible],
        outputs=[new_password_visible, new_password_toggle],
        queue=False,
    ).then(
        fn=lambda x: gr.update(type="text" if x else "password"),
        inputs=[new_password_visible],
        outputs=[new_password_input],
        queue=False,
    )

    confirm_new_password_toggle.click(
        fn=lambda x: (not x, "🙈" if not x else "👁️"),
        inputs=[confirm_new_password_visible],
        outputs=[confirm_new_password_visible, confirm_new_password_toggle],
        queue=False,
    ).then(
        fn=lambda x: gr.update(type="text" if x else "password"),
        inputs=[confirm_new_password_visible],
        outputs=[confirm_new_password_input],
        queue=False,
    )

    # Handle password change submission
    def show_loading() -> gr.update:
        return gr.update(
            visible=True,
            value="""
        <div style="text-align: center; padding: 20px;">
            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto; }
            </style>
            <div class="spinner"></div>
            <p>Processing...</p>
        </div>
        """,
        )

    def hide_loading() -> gr.update:
        return gr.update(visible=False, value="")

    async def handle_change_password(
        username: str,
        old_password: str,
        new_password: str,
        confirm_new_password: str,
        last_time: float,
    ) -> Tuple[gr.update, float, gr.update, bool, str, gr.update]:
        """Handles the password change request."""
        logger.info(f"Change password attempt for user: {username}")
        current_time = time.time()
        if current_time - last_time < rate_limit_seconds:
            remaining_time = int(rate_limit_seconds - (current_time - last_time))
            return (
                gr.update(
                    visible=True,
                    value=f"⚠️ Please wait {remaining_time} seconds before trying again.",
                ),
                last_time,
                gr.update(visible=True),
                True,  # Keep logged in on rate limit
                username,
                hide_loading(),
            )

        if not username:
            return (
                gr.update(visible=True, value="❌ Not logged in!"),
                last_time,
                gr.update(visible=True),
                True,
                username,
                hide_loading(),
            )

        try:
            # Call backend change_password function
            result = await change_password(
                username, old_password, new_password, confirm_new_password
            )

            if result.get("success"):
                logger.info(f"Password changed successfully for user: {username}")
                # On success, log out the user by setting logged_in_state to False
                # This will trigger the app.py's logged_in_state.change handler
                return (
                    gr.update(
                        visible=True,
                        value="✅ Password changed successfully! Please log in with your new password.",
                    ),
                    current_time,  # Update last_time on success
                    gr.update(visible=False),  # Hide popup on success
                    False,  # Log user out
                    "",  # Clear username
                    hide_loading(),
                )
            else:
                logger.warning(
                    f"Password change failed for user {username}: {result.get('message', 'Unknown error')}"
                )
                return (
                    gr.update(
                        visible=True,
                        value=f"❌ {result.get('message', 'Password change failed.')}",
                    ),
                    last_time,
                    gr.update(visible=True),  # Keep popup visible on failure
                    True,  # Keep user logged in on backend failure
                    username,
                    hide_loading(),
                )
        except Exception as e:
            logger.error(
                f"System error during password change for {username}: {e}",
                exc_info=True,
            )
            return (
                gr.update(visible=True, value=f"❌ System error: {str(e)}"),
                last_time,
                gr.update(visible=True),
                True,  # Keep user logged in on system error
                username,
                hide_loading(),
            )

    # Wire up submit button with loading indicator
    submit_change_password_btn.click(
        fn=show_loading,
        outputs=[loading_indicator],
        queue=False,  # Show loading immediately
    ).then(
        fn=handle_change_password,
        inputs=[
            username_state,
            old_password_input,
            new_password_input,
            confirm_new_password_input,
            last_change_time_state,  # Use the local state here
        ],
        outputs=[
            change_password_message,
            last_change_time_state,  # Update the local state
            change_password_popup,  # Control popup visibility
            logged_in_state,  # This will trigger logout only on success
            username_state,
            loading_indicator,
        ],
        api_name="main_change_password",
        queue=True,
    )

    # Cancel button hides the popup and clears fields
    cancel_change_password_btn.click(
        fn=lambda: (
            gr.update(visible=False),  # Hide popup
            gr.update(value="", visible=False),  # Clear message
            gr.update(value=""),  # Clear old password
            gr.update(value=""),  # Clear new password
            gr.update(value=""),  # Clear confirm password
            gr.update(type="password"),  # Reset old password type
            gr.update(type="password"),  # Reset new password type
            gr.update(type="password"),  # Reset confirm password type
            gr.update(value=False),  # Reset old_password_visible state
            gr.update(value=False),  # Reset new_password_visible state
            gr.update(value=False),  # Reset confirm_new_password_visible state
            gr.update(value="👁️"),  # Reset old_password_toggle icon
            gr.update(value="👁️"),  # Reset new_password_toggle icon
            gr.update(value="👁️"),  # Reset confirm_new_password_toggle icon
        ),
        outputs=[
            change_password_popup,
            change_password_message,
            old_password_input,
            new_password_input,
            confirm_new_password_input,
            old_password_input,  # Output again to change type
            new_password_input,  # Output again to change type
            confirm_new_password_input,  # Output again to change type
            old_password_visible,
            new_password_visible,
            confirm_new_password_visible,
            old_password_toggle,
            new_password_toggle,
            confirm_new_password_toggle,
        ],
        queue=False,
    )

    return change_password_popup
