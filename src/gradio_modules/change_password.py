#!/usr/bin/env python3
"""
Change Password Interface Module

This module provides the change password interface for the NYP FYP Chatbot application.
Users can change their password through a modal popup with password visibility toggles.
"""

import gradio as gr
import logging

logger = logging.getLogger(__name__)


def change_password_interface(
    username_state: gr.State, logged_in_state: gr.State, rate_limit_seconds: int = 60
) -> gr.Blocks:
    """
    Creates the change password UI components and returns the Blocks object for the tab content.
    The global button and last_change_time state are managed externally by app.py.
    """
    # Removed unused last_change_time_state

    with gr.Blocks(
        elem_id="change_password_popup", elem_classes=["change-password-popup"]
    ):
        gr.Markdown("## 🔐 Change Password", elem_id="change_password_title")
        gr.Markdown(
            "Please enter your current password and new password.",
            elem_id="change_password_instruction",
        )
        with gr.Row():
            gr.Textbox(
                label="Current Password",
                type="password",
                elem_id="old_password_input",
                placeholder="Enter your current password",
            )
            gr.Button("👁️", size="sm", elem_id="old_password_toggle")
        with gr.Row():
            gr.Textbox(
                label="New Password",
                type="password",
                elem_id="new_password_input",
                placeholder="Enter your new password",
            )
            gr.Button("👁️", size="sm", elem_id="new_password_toggle")
        with gr.Row():
            gr.Textbox(
                label="Confirm New Password",
                type="password",
                elem_id="confirm_new_password_input",
                placeholder="Confirm your new password",
            )
            gr.Button("👁️", size="sm", elem_id="confirm_new_password_toggle")
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
            visible=True,
        )
        gr.Markdown("", visible=False, elem_id="change_password_message")
        with gr.Row():
            gr.Button(
                "Change Password",
                variant="primary",
                elem_id="submit_change_password_btn",
            )
            gr.Button(
                "Cancel", variant="secondary", elem_id="cancel_change_password_btn"
            )
        gr.HTML(value="", visible=False, elem_classes=["loading-indicator"])

    # Removed unused internal states for password visibility

    # Event handlers and logic are wired here as in the original implementation

    # UI definition removed; only backend/event handler functions remain
