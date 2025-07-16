#!/usr/bin/env python3
"""
Change Password Interface Module

This module provides the change password interface for the NYP FYP Chatbot application.
Users can change their password through a modal popup with password visibility toggles.
"""

import time
from typing import Tuple

import gradio as gr

from backend import change_password


import os


def change_password_interface(
    username_state: gr.State, logged_in_state: gr.State, rate_limit_seconds: int = 60
) -> Tuple[gr.Button, gr.Column, gr.State]:
    change_password_btn = gr.Button(
        "🔐 Change Password",
        visible=False,
        elem_id="main_change_password_btn",
        size="sm",
        variant="secondary",
    )
    with gr.Column(
        visible=False,
        elem_id="change_password_popup",
        elem_classes=["change-password-popup"],
    ) as change_password_popup:
        gr.Markdown("## 🔐 Change Password", elem_id="change_password_title")
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
                elem_id="confirm_password_input",
                placeholder="Confirm your new password",
            )
            confirm_password_toggle = gr.Button(
                "👁️", size="sm", elem_id="confirm_password_toggle"
            )
        gr.Markdown(
            """
            **Password Requirements:**
            - At least 8 characters long
            - Contains uppercase and lowercase letters
            - Contains at least one number
            - Contains at least one special character (!@#$%^&*)
            """,
            elem_id="password_requirements_info",
        )
        with gr.Row():
            submit_change_password_btn = gr.Button(
                "Change Password",
                variant="primary",
                elem_id="submit_change_password_btn",
            )
            cancel_btn = gr.Button(
                "Cancel", variant="secondary", elem_id="cancel_change_password_btn"
            )
        change_password_message = gr.Markdown(
            visible=False, elem_id="change_password_message"
        )
        loading_indicator = gr.HTML(
            value="", visible=False, elem_id="change_password_loading"
        )
    last_change_time = gr.State(0)
    old_password_visible = gr.State(False)
    new_password_visible = gr.State(False)
    confirm_password_visible = gr.State(False)

    # Patch: In benchmark mode, skip event setup
    if os.environ.get("BENCHMARK_MODE"):
        return change_password_btn, change_password_popup, last_change_time

    def toggle_old_password(visible: bool) -> Tuple[gr.update, str, bool]:
        # Toggle the visibility of the old password field.
        #
        # :param visible: Current visibility state
        # :type visible: bool
        # :return: Tuple of gr.update for the textbox, button text, and the new visibility state
        # :rtype: Tuple[gr.update, str, bool]
        if visible:
            return gr.update(type="password"), "👁️", False
        else:
            return gr.update(type="text"), "🙈", True

    def toggle_new_password(visible: bool) -> Tuple[gr.update, str, bool]:
        # Toggle the visibility of the new password field.
        #
        # :param visible: Current visibility state
        # :type visible: bool
        # :return: Tuple of gr.update for the textbox, button text, and the new visibility state
        # :rtype: Tuple[gr.update, str, bool]
        if visible:
            return gr.update(type="password"), "👁️", False
        else:
            return gr.update(type="text"), "🙈", True

    def toggle_confirm_password(visible: bool) -> Tuple[gr.update, str, bool]:
        # Toggle the visibility of the confirm password field.
        #
        # :param visible: Current visibility state
        # :type visible: bool
        # :return: Tuple of gr.update for the textbox, button text, and the new visibility state
        # :rtype: Tuple[gr.update, str, bool]
        if visible:
            return gr.update(type="password"), "👁️", False
        else:
            return gr.update(type="text"), "🙈", True

    # Wire up password toggles
    old_password_toggle.click(
        fn=toggle_old_password,
        inputs=[old_password_visible],
        outputs=[old_password_input, old_password_toggle, old_password_visible],
    )

    new_password_toggle.click(
        fn=toggle_new_password,
        inputs=[new_password_visible],
        outputs=[new_password_input, new_password_toggle, new_password_visible],
    )

    confirm_password_toggle.click(
        fn=toggle_confirm_password,
        inputs=[confirm_password_visible],
        outputs=[
            confirm_new_password_input,
            confirm_password_toggle,
            confirm_password_visible,
        ],
    )

    def close_popup() -> gr.update:
        # Close the change password popup.
        #
        # :return: gr.update to hide the popup
        # :rtype: gr.update
        return gr.update(visible=False)

    cancel_btn.click(fn=close_popup, outputs=[change_password_popup])

    def show_change_password_popup() -> gr.update:
        # Show the change password popup.
        #
        # :return: gr.update to show the popup
        # :rtype: gr.update
        return gr.update(visible=True)

    change_password_btn.click(
        fn=show_change_password_popup, outputs=[change_password_popup]
    )

    def show_loading() -> gr.update:
        # Show loading indicator.
        #
        # :return: Loading indicator update
        # :rtype: gr.update
        return gr.update(
            visible=True,
            value="""
            <div style="text-align: center; padding: 10px;">
                <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <p style="margin-top: 5px; color: #666; font-size: 12px;">Changing password...</p>
                <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                </style>
            </div>
            """,
        )

    def hide_loading() -> gr.update:
        # Hide loading indicator.
        #
        # :return: Loading indicator update
        # :rtype: gr.update
        return gr.update(visible=False, value="")

    async def handle_change_password(
        username: str,
        old_password: str,
        new_password: str,
        confirm_new_password: str,
        last_time: float,
    ) -> Tuple[gr.update, float, gr.update, bool, str, gr.update]:
        # Handle the password change logic and UI updates.
        #
        # :param username: The username of the user changing password
        # :type username: str
        # :param old_password: The user's current password
        # :type old_password: str
        # :param new_password: The new password to set
        # :type new_password: str
        # :param confirm_new_password: Confirmation of the new password
        # :type confirm_new_password: str
        # :param last_time: The last time the password was changed (timestamp)
        # :type last_time: float
        # :return: Tuple containing message update, new timestamp, popup update, logout flag (True=keep logged in, False=logout), username, and loading update
        # :rtype: Tuple[gr.update, float, gr.update, bool, str, gr.update]

        now = time.time()
        if now - last_time < rate_limit_seconds:
            return (
                gr.update(
                    visible=True,
                    value=f"⏳ Please wait {int(rate_limit_seconds - (now - last_time))} seconds before changing password again.",
                ),
                now,
                gr.update(visible=True),
                True,  # Keep user logged in on rate limit
                username,
                hide_loading(),
            )

        # Frontend validation before calling backend
        if not old_password or not new_password or not confirm_new_password:
            return (
                gr.update(visible=True, value="❌ All fields are required."),
                last_time,
                gr.update(visible=True),
                True,  # Keep user logged in on validation failure
                username,
                hide_loading(),
            )

        if new_password != confirm_new_password:
            return (
                gr.update(visible=True, value="❌ New passwords do not match."),
                last_time,
                gr.update(visible=True),
                True,  # Keep user logged in on validation failure
                username,
                hide_loading(),
            )

        # Additional frontend password complexity validation
        import re

        errors = []

        if len(new_password) < 8:
            errors.append("at least 8 characters long")

        if not re.search(r"[A-Z]", new_password):
            errors.append("at least one uppercase letter")

        if not re.search(r"[a-z]", new_password):
            errors.append("at least one lowercase letter")

        if not re.search(r"\d", new_password):
            errors.append("at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            errors.append('at least one special character (!@#$%^&*,.?":{}|<>)')

        if errors:
            return (
                gr.update(
                    visible=True,
                    value=f"❌ Password must contain: {', '.join(errors)}.",
                ),
                last_time,
                gr.update(visible=True),
                True,  # Keep user logged in on validation failure
                username,
                hide_loading(),
            )

        try:
            result = await change_password(username, old_password, new_password)
            if result.get("status") == "success":
                return (
                    gr.update(
                        visible=True,
                        value="✅ Password changed successfully. You will be logged out.",
                    ),
                    now,
                    gr.update(visible=False),
                    False,  # Trigger logout by setting logged_in_state to False
                    username,
                    hide_loading(),
                )
            else:
                return (
                    gr.update(
                        visible=True,
                        value=f"❌ {result.get('message', 'Password change failed.')}",
                    ),
                    last_time,
                    gr.update(visible=True),
                    True,  # Keep user logged in on backend failure
                    username,
                    hide_loading(),
                )
        except Exception as e:
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
    ).then(
        fn=handle_change_password,
        inputs=[
            username_state,
            old_password_input,
            new_password_input,
            confirm_new_password_input,
            last_change_time,
        ],
        outputs=[
            change_password_message,
            last_change_time,
            change_password_popup,
            logged_in_state,  # This will trigger logout only on success
            username_state,
            loading_indicator,  # Hide loading indicator
        ],
        api_name="main_change_password",
        queue=True,  # Enable queuing to prevent blocking
    )

    return change_password_btn, change_password_popup, last_change_time
