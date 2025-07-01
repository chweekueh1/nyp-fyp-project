import gradio as gr


def change_password_interface(
    username_state: gr.State, rate_limit_seconds: int = 60
) -> tuple[gr.Button, gr.Column, gr.State]:
    """
    Change Password UI for main app.

    :param username_state: Gradio state containing the current username.
    :type username_state: gr.State
    :param rate_limit_seconds: Number of seconds to rate limit password changes.
    :type rate_limit_seconds: int
    :return: Tuple containing the change password button, section, and last change time state.
    :rtype: tuple[gr.Button, gr.Column, gr.State]
    """
    # Button to show the change password form
    change_password_btn = gr.Button(
        "Change Password", visible=True, elem_id="main_change_password_btn"
    )

    # Change Password UI (hidden by default)
    change_password_section = gr.Column(
        visible=False, elem_id="main_change_password_section"
    )
    old_password_input = gr.Textbox(
        label="Current Password", type="password", elem_id="main_old_password_input"
    )
    new_password_input = gr.Textbox(
        label="New Password", type="password", elem_id="main_new_password_input"
    )
    confirm_new_password_input = gr.Textbox(
        label="Confirm New Password",
        type="password",
        elem_id="main_confirm_new_password_input",
    )
    submit_change_password_btn = gr.Button(
        "Change Password", variant="primary", elem_id="main_submit_change_password_btn"
    )
    change_password_message = gr.Markdown(
        visible=False, elem_id="main_change_password_message"
    )
    last_change_time = gr.State(0)

    def show_change_password_section() -> gr.update:
        """Show the change password section."""
        return gr.update(visible=True)

    change_password_btn.click(
        fn=show_change_password_section, outputs=[change_password_section]
    )

    async def handle_change_password(
        username: str,
        old_password: str,
        new_password: str,
        confirm_new_password: str,
        last_time: float,
    ) -> tuple[gr.update, float, gr.update]:
        """
        Handle the password change logic and UI updates.

        :param username: The username of the user changing password.
        :type username: str
        :param old_password: The user's current password.
        :type old_password: str
        :param new_password: The new password to set.
        :type new_password: str
        :param confirm_new_password: Confirmation of the new password.
        :type confirm_new_password: str
        :param last_time: The last time the password was changed (timestamp).
        :type last_time: float
        :return: Tuple of (message update, new last_time, section update).
        :rtype: tuple[gr.update, float, gr.update]
        """
        import time

        now = time.time()
        if now - last_time < rate_limit_seconds:
            return (
                gr.update(
                    visible=True,
                    value=f"⏳ Please wait {int(rate_limit_seconds - (now - last_time))} seconds before changing password again.",
                ),
                now,
                gr.update(visible=True),
            )
        if not old_password or not new_password or not confirm_new_password:
            return (
                gr.update(visible=True, value="❌ All fields are required."),
                last_time,
                gr.update(visible=True),
            )
        if new_password != confirm_new_password:
            return (
                gr.update(visible=True, value="❌ New passwords do not match."),
                last_time,
                gr.update(visible=True),
            )
        try:
            from backend import change_password

            result = await change_password(username, old_password, new_password)
            if result.get("code") == "200":
                return (
                    gr.update(visible=True, value="✅ Password changed successfully."),
                    now,
                    gr.update(visible=False),
                )
            else:
                return (
                    gr.update(
                        visible=True,
                        value=f"❌ {result.get('message', 'Password change failed.')}",
                    ),
                    last_time,
                    gr.update(visible=True),
                )
        except Exception as e:
            return (
                gr.update(visible=True, value=f"❌ System error: {str(e)}"),
                last_time,
                gr.update(visible=True),
            )

    submit_change_password_btn.click(
        fn=handle_change_password,
        inputs=[
            username_state,
            old_password_input,
            new_password_input,
            confirm_new_password_input,
            last_change_time,
        ],
        outputs=[change_password_message, last_change_time, change_password_section],
        api_name="main_change_password",
    )

    return change_password_btn, change_password_section, last_change_time
