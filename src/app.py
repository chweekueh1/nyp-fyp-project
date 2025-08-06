# app.py

import os
import asyncio
import gradio as gr
from gradio_modules.login_and_register import login_interface, handle_primary_btn_click
from backend.main import init_backend


def load_custom_css():
    css = ""
    styles_dir = "styles"
    if os.path.isdir(styles_dir):
        for filename in os.listdir(styles_dir):
            if filename.endswith(".css"):
                with open(os.path.join(styles_dir, filename), "r") as f:
                    css += f.read() + "\n"
    return css


async def main():
    await init_backend()
    print("[DEBUG] Initializing all Gradio interfaces before app launch...")
    import logging

    logger = logging.getLogger(__name__)

    # Only import and initialize interfaces inside lazy loader functions below

    # Fetch and log launch config from performance_utils
    from performance_utils import perf_monitor

    launch_metrics = (
        perf_monitor.get_metrics() if hasattr(perf_monitor, "get_metrics") else {}
    )
    logger.info(f"[DEBUG] Launch config metrics: {launch_metrics}")
    print(f"[DEBUG] Launch config metrics: {launch_metrics}")

    print("[DEBUG] All interfaces initialized. Launching Gradio app...")

    with gr.Blocks(title="NYP FYP Chatbot", css=load_custom_css()) as app:
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        is_register_mode_state = gr.State(False)
        # Initialize all_chats_data_state as an empty dict to avoid NoneType errors
        all_chats_data_state = gr.State({})

        # Login/Register container
        with gr.Column(visible=True) as login_container:
            (
                error_message,
                username_input,
                email_input,
                password_input,
                confirm_password_input,
                primary_btn,
                secondary_btn,
                show_password_btn,
                show_confirm_btn,
                password_visible,
                confirm_password_visible,
                header_subtitle,
                header_instruction,
                email_info,
                password_requirements,
            ) = login_interface(
                logged_in_state,
                username_state,
                is_register_mode_state,
            )

        # Load theme from flexcyon_theme.py
        try:
            from flexcyon_theme import apply_theme

            apply_theme()
        except ImportError:
            pass

        # Main app containers implemented directly here, now using gr.Tabs and gr.TabItem
        main_tabs = None
        with gr.Column(visible=False) as main_container:
            main_tabs = gr.Tabs()
            with main_tabs:
                with gr.TabItem("Chat"):
                    gr.Markdown("## 💬 Chatbot")

                    from backend.chat import (
                        get_chat_history,
                        get_chat_metadata,
                        get_chatbot_response,
                    )
                    from gradio_modules.chatbot import _handle_send_message

                    chat_id_state = gr.State("")
                    chat_history = gr.Chatbot()
                    chat_input = gr.Textbox(label="Type your message...")
                    send_btn = gr.Button("Send")
                    send_btn.click(
                        fn=_handle_send_message,
                        inputs=[
                            chat_input,
                            chat_history,
                            username_state,
                            chat_id_state,
                            all_chats_data_state,
                        ],
                        outputs=[
                            chat_history,
                            chat_input,
                            all_chats_data_state,
                            chat_history,
                            gr.State(),
                        ],
                        queue=True,
                    )

                    # Load chat history after login using async Gradio event
                    async def load_chat_history(username):
                        if username:
                            return await get_chat_history("default", username)
                        return []

                    username_state.change(
                        fn=load_chat_history,
                        inputs=[username_state],
                        outputs=[chat_history],
                        queue=True,
                    )
                    new_chat_btn = gr.Button("New Chat")
                    chat_dropdown = gr.Dropdown(
                        label="Select Chat Session", choices=[], value=None
                    )

                    # State to hold current chat_id
                    chat_id_state = gr.State("")

                    # Load chat sessions for dropdown
                    async def load_chat_sessions(username):
                        if not username:
                            return gr.update(choices=[], value=None)
                        metadata = await get_chat_metadata(username)
                        choices = [
                            f"{v['session_name']} ({k[:8]})"
                            for k, v in metadata.items()
                        ]
                        values = list(metadata.keys())
                        dropdown_map = dict(zip(choices, values))
                        chat_dropdown.dropdown_map = dropdown_map
                        # Default to the most recent chat (first in metadata)
                        value = choices[0] if choices else None
                        return gr.update(choices=choices, value=value)

                    username_state.change(
                        fn=load_chat_sessions,
                        inputs=[username_state],
                        outputs=[chat_dropdown],
                        queue=True,
                    )

                    # Load chat history for selected chat
                    async def load_selected_chat_history(selected, username):
                        if not username or not selected:
                            return []
                        chat_id = chat_dropdown.dropdown_map.get(selected, "")
                        chat_id_state.value = chat_id
                        return await get_chat_history(chat_id, username)

                    chat_dropdown.change(
                        fn=load_selected_chat_history,
                        inputs=[chat_dropdown, username_state],
                        outputs=[chat_history],
                        queue=True,
                    )

                    # New chat button logic
                    async def start_new_chat(username):
                        from backend.chat import (
                            get_chat_metadata,
                            _update_chat_history,
                            get_chat_history,
                        )
                        import uuid

                        if not username:
                            return [], gr.update()
                        chat_id = f"chat_{uuid.uuid4().hex[:8]}"
                        # Actually create the new chat session in backend (empty message, empty response)
                        await _update_chat_history(chat_id, username, "", "")
                        # Reload metadata and dropdown
                        metadata = await get_chat_metadata(username)
                        choices = [
                            f"{v['session_name']} ({k[:8]})"
                            for k, v in metadata.items()
                        ]
                        values = list(metadata.keys())
                        dropdown_map = dict(zip(choices, values))
                        chat_dropdown.dropdown_map = dropdown_map
                        # Set dropdown to new chat
                        new_choice = [
                            c for c, k in dropdown_map.items() if k == chat_id
                        ][0]
                        # Load empty history for new chat
                        history = await get_chat_history(chat_id, username)
                        return history, gr.update(choices=choices, value=new_choice)

                    new_chat_btn.click(
                        fn=start_new_chat,
                        inputs=[username_state],
                        outputs=[chat_history, chat_dropdown],
                        queue=True,
                    )

                    # Send message logic
                    async def send_message(message):
                        username = (
                            username_state.value
                            if hasattr(username_state, "value")
                            else username_state
                        )
                        chat_id = (
                            chat_id_state.value
                            if hasattr(chat_id_state, "value")
                            else chat_id_state
                        )
                        if not username or not chat_id:
                            return [], ""
                        # Use backend chat logic
                        await get_chatbot_response(username, chat_id, message)
                        # Reload chat history after sending
                        history = await get_chat_history(chat_id, username)
                        return history, ""

                    send_btn.click(
                        fn=send_message,
                        inputs=[chat_input],
                        outputs=[chat_history, chat_input],
                        queue=True,
                    )

                with gr.TabItem("Files"):
                    gr.Markdown("## 📁 File Upload & Management")
                    from gradio_modules.file_upload import file_upload_ui

                    file_upload = gr.File(label="Upload File")
                    upload_btn = gr.Button("Upload")
                    upload_status = gr.Markdown(visible=False)

                    async def upload_file(file):
                        result = await file_upload_ui(
                            username_state,
                            gr.State([]),
                            gr.State(""),
                            gr.State(""),
                            gr.State([]),
                        )
                        return gr.update(visible=True, value=result)

                    upload_btn.click(
                        fn=upload_file,
                        inputs=[file_upload],
                        outputs=[upload_status],
                        queue=True,
                    )

                with gr.TabItem("Audio"):
                    gr.Markdown("## 🎤 Audio Input")
                    from gradio_modules.audio_input import (
                        transcribe_and_respond_wrapper,
                    )

                    audio_input = gr.Audio(label="Record or Upload Audio")
                    transcribe_btn = gr.Button("Transcribe & Chat")
                    transcript_output = gr.Textbox(
                        label="Transcript", interactive=False
                    )

                    async def transcribe_audio(audio):
                        result = await transcribe_and_respond_wrapper(audio)
                        return result

                    transcribe_btn.click(
                        fn=transcribe_audio,
                        inputs=[audio_input],
                        outputs=[transcript_output],
                        queue=True,
                    )

                with gr.TabItem("Search"):
                    gr.Markdown("## 🔎 Search Chat & Audio History")
                    from gradio_modules.search_interface import _handle_search_query

                    search_query = gr.Textbox(label="Search Query")
                    search_btn = gr.Button("Search")
                    search_results = gr.Markdown(visible=False)

                    async def search_history(query):
                        result = await _handle_search_query(query)
                        return gr.update(visible=True, value=result)

                    search_btn.click(
                        fn=search_history,
                        inputs=[search_query],
                        outputs=[search_results],
                        queue=True,
                    )

                with gr.TabItem("Stats"):
                    gr.Markdown("## 📊 User Statistics & Performance Dashboard")
                    from gradio_modules.stats_interface import StatsInterface

                    stats_instance = StatsInterface()
                    stats_md = gr.Markdown("Stats will appear here.")
                    refresh_btn = gr.Button("Refresh Stats")

                    async def refresh_stats():
                        result = await stats_instance.get_user_statistics()
                        return gr.update(value=result)

                    refresh_btn.click(
                        fn=refresh_stats,
                        inputs=[],
                        outputs=[stats_md],
                        queue=True,
                    )

                with gr.TabItem("Change Password"):
                    gr.Markdown("## 🔐 Change Password")
                    from backend.auth import change_password

                    current_pw = gr.Textbox(label="Current Password", type="password")
                    new_pw = gr.Textbox(label="New Password", type="password")
                    confirm_new_pw = gr.Textbox(
                        label="Confirm New Password", type="password"
                    )
                    change_pw_btn = gr.Button("Change Password")
                    change_pw_status = gr.Markdown(visible=False)

                    async def handle_change_password(current, new, confirm):
                        # Use username from state
                        username = (
                            username_state.value
                            if hasattr(username_state, "value")
                            else username_state
                        )
                        if not username:
                            return gr.update(
                                visible=True,
                                value="You must be logged in to change your password.",
                            )
                        if new != confirm:
                            return gr.update(
                                visible=True, value="New passwords do not match."
                            )
                        result = await change_password(username, current, new)
                        msg = result.get("message", "Unknown error.")
                        return gr.update(visible=True, value=msg)

                    change_pw_btn.click(
                        fn=handle_change_password,
                        inputs=[current_pw, new_pw, confirm_new_pw],
                        outputs=[change_pw_status],
                        queue=True,
                    )

                with gr.TabItem("Logout"):
                    gr.Markdown("## Logout")
                    logout_btn = gr.Button("Logout")

                    def do_logout():
                        # Reset login state and username
                        return False, ""

                    logout_btn.click(
                        fn=do_logout,
                        inputs=[],
                        outputs=[logged_in_state, username_state],
                        queue=True,
                    )

        # Toggle login/register mode
        def toggle_register_mode(current_mode):
            return not current_mode

        secondary_btn.click(
            fn=toggle_register_mode,
            inputs=[is_register_mode_state],
            outputs=[is_register_mode_state],
            queue=False,
        )

        # Update UI elements when mode changes
        def update_auth_ui(is_reg):
            return (
                gr.update(value="Register Account" if is_reg else "Login"),
                gr.update(
                    value="Back to Login"
                    if is_reg
                    else "Don't have an account? Register"
                ),
                gr.update(visible=is_reg),
                gr.update(visible=is_reg),
                gr.update(visible=is_reg),
                gr.update(visible=is_reg),
                gr.update(visible=is_reg),
                gr.update(value="## 📝 Register" if is_reg else "## 🔐 Login"),
                gr.update(
                    value="Create a new account to access the chatbot."
                    if is_reg
                    else "Please log in to access the chatbot."
                ),
                gr.update(value=""),
            )

        is_register_mode_state.change(
            fn=update_auth_ui,
            inputs=[is_register_mode_state],
            outputs=[
                primary_btn,
                secondary_btn,
                email_input,
                confirm_password_input,
                show_confirm_btn,
                password_requirements,
                email_info,
                header_subtitle,
                header_instruction,
                error_message,
            ],
            queue=False,
        )

        # Show/hide containers after login/logout
        def handle_login_state(logged_in, username):
            return (
                gr.update(visible=not logged_in),  # login_container
                gr.update(visible=logged_in),  # main_container
            )

        logged_in_state.change(
            fn=handle_login_state,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_container],
            queue=False,
        )

        # Logout button logic (inside logout tab)
        # Should set logged_in_state to False and username_state to ""
        # ...existing code for logout_btn.click...

        # Toggle password visibility
        show_password_btn.click(
            fn=lambda current_type, current_visibility_state: (
                gr.update(type="text" if not current_visibility_state else "password"),
                not current_visibility_state,
                gr.update(value="🙈" if not current_visibility_state else "👁️"),
            ),
            inputs=[password_input, password_visible],
            outputs=[password_input, password_visible, show_password_btn],
            queue=False,
        )
        show_confirm_btn.click(
            fn=lambda current_type, current_visibility_state: (
                gr.update(type="text" if not current_visibility_state else "password"),
                not current_visibility_state,
                gr.update(value="🙈" if not current_visibility_state else "👁️"),
            ),
            inputs=[confirm_password_input, confirm_password_visible],
            outputs=[
                confirm_password_input,
                confirm_password_visible,
                show_confirm_btn,
            ],
            queue=False,
        )

        # Login/Register button logic
        async def handle_and_update(*args):
            error_msg, logged_in, username_val = await handle_primary_btn_click(*args)
            if logged_in is True:
                return (
                    error_msg,
                    True,
                    username_val if hasattr(username_val, "value") else username_val,
                )
            else:
                return error_msg, False, ""

        primary_btn.click(
            fn=handle_and_update,
            inputs=[
                is_register_mode_state,
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
        password_input.submit(
            fn=handle_and_update,
            inputs=[
                is_register_mode_state,
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
            fn=handle_and_update,
            inputs=[
                is_register_mode_state,
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

    app.queue()
    app.launch()


if __name__ == "__main__":
    asyncio.run(main())
