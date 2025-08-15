import os
import sys
import time
import platform
import asyncio
import gradio as gr
from gradio_modules.login_and_register import login_interface, handle_primary_btn_click
from backend.main import init_backend


def load_custom_css():
    css = ""
    styles_dir = "/app/styles"
    if os.path.isdir(styles_dir):
        for filename in os.listdir(styles_dir):
            if filename.endswith(".css"):
                with open(os.path.join(styles_dir, filename), "r") as f:
                    css += f.read() + "\n"
    return css


async def main():
    # --- App startup analytics ---
    t0 = time.time()
    await init_backend()
    try:
        from backend.consolidated_database import get_consolidated_database

        db = get_consolidated_database()
        os_info = (
            f"{platform.system()} {platform.release()}"
            if hasattr(platform, "system")
            else "unknown"
        )
        python_version = (
            sys.version.split()[0] if hasattr(sys, "version") else "unknown"
        )
        duration_ms = int((time.time() - t0) * 1000)
        db.add_app_startup_record(
            username=None,
            duration_ms=duration_ms,
            os_info=os_info,
            python_version=python_version,
        )
    except Exception as startup_exc:
        print(f"[WARN] Failed to log app startup analytics: {startup_exc}")
    # --- End app startup analytics ---

    print("[DEBUG] Initializing all Gradio interfaces before app launch...")
    import logging

    logger = logging.getLogger(__name__)

    from performance_utils import perf_monitor

    launch_metrics = (
        perf_monitor.get_metrics() if hasattr(perf_monitor, "get_metrics") else {}
    )
    logger.info(f"[DEBUG] Launch config metrics: {launch_metrics}")
    print(f"[DEBUG] Launch config metrics: {launch_metrics}")

    print("[DEBUG] All interfaces initialized. Launching Gradio app...")

    css_str = load_custom_css()
    with gr.Blocks(title="NYP FYP Chatbot", css=css_str) as app:
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        is_register_mode_state = gr.State(False)
        all_chats_data_state = gr.State({})
        current_time_state = gr.State("")
        audio_history_state = gr.State([])

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

        try:
            from flexcyon_theme import apply_theme

            apply_theme()
        except ImportError:
            pass

        with gr.Column(visible=False) as main_container:
            main_tabs = gr.Tabs()
            with main_tabs:
                with gr.TabItem("Chat"):
                    gr.Markdown("## 💬 Chatbot")
                    from backend.chat import get_chat_history
                    from gradio_modules.chatbot import _handle_send_message

                    chat_id_state = gr.State("")
                    chat_history = gr.Chatbot()
                    chat_input = gr.Textbox(label="Type your message...")
                    send_btn = gr.Button("Send")

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
                            gr.State(None),
                            current_time_state,
                        ],
                        queue=True,
                    )

                with gr.TabItem("Files"):
                    from gradio_modules.file_management import file_management_interface

                    file_management_block = file_management_interface(
                        username_state, logged_in_state, all_chats_data_state
                    )
                    file_management_block

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
                    from gradio_modules.search_interface import search_interface

                    search_block = search_interface(
                        username_state=username_state,
                        all_chats_data_state=all_chats_data_state,
                        audio_history_state=audio_history_state,
                    )
                    search_block

                with gr.TabItem("Stats"):
                    from gradio_modules.stats_interface import StatsInterface

                    stats_instance = StatsInterface()
                    status_md = gr.Markdown("", visible=True)
                    mermaid_md = gr.Markdown("", visible=True)
                    pretty_stats_md = gr.Markdown("", visible=True)
                    refresh_btn = gr.Button("Refresh Stats")

                    async def refresh_stats(username=None):
                        user = username or (
                            username_state.value
                            if hasattr(username_state, "value")
                            else username_state
                        )
                        if not user:
                            return (
                                "Please log in to view statistics.",
                                "",
                                "You must be logged in to view statistics.",
                            )
                        result = stats_instance.get_user_statistics(user)
                        return result[:3]

                    refresh_btn.click(
                        fn=refresh_stats,
                        inputs=[username_state],
                        outputs=[
                            status_md,
                            mermaid_md,
                            pretty_stats_md,
                        ],
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
                        return False, ""

                    logout_btn.click(
                        fn=do_logout,
                        inputs=[],
                        outputs=[logged_in_state, username_state],
                        queue=True,
                    )

        def toggle_register_mode(current_mode):
            return not current_mode

        secondary_btn.click(
            fn=toggle_register_mode,
            inputs=[is_register_mode_state],
            outputs=[is_register_mode_state],
            queue=False,
        )

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

        def handle_login_state(logged_in, username):
            return (
                gr.update(visible=not logged_in),
                gr.update(visible=logged_in),
            )

        logged_in_state.change(
            fn=handle_login_state,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_container],
            queue=False,
        )

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
