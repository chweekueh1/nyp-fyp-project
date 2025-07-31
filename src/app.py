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
    with gr.Blocks(title="NYP FYP Chatbot", css=load_custom_css()) as app:
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        is_register_mode_state = gr.State(False)

        # Login/Register container (wrap all login/register UI in a column for visibility toggling)
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

        # Wire secondary_btn to toggle register/login mode
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
                gr.update(
                    value="Register Account" if is_reg else "Login"
                ),  # primary_btn
                gr.update(
                    value="Back to Login"
                    if is_reg
                    else "Don't have an account? Register"
                ),  # secondary_btn
                gr.update(visible=is_reg),  # email_input
                gr.update(visible=is_reg),  # confirm_password_input
                gr.update(visible=is_reg),  # show_confirm_btn
                gr.update(visible=is_reg),  # password_requirements
                gr.update(visible=is_reg),  # email_info
                gr.update(
                    value="## 📝 Register" if is_reg else "## 🔐 Login"
                ),  # header_subtitle
                gr.update(
                    value="Create a new account to access the chatbot."
                    if is_reg
                    else "Please log in to access the chatbot."
                ),  # header_instruction
                gr.update(value=""),  # error_message (clear)
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

        # Main app container (TabbedInterface + Logout)
        with gr.Column(visible=False) as main_container:
            # State objects for interfaces
            all_chats_data_state = gr.State({})
            chat_id_state = gr.State("")
            chat_history_state = gr.State([])
            debug_info_state = gr.State("")
            audio_history_state = gr.State([])

            # Import actual interfaces
            from gradio_modules.chatbot import chatbot_ui
            from gradio_modules.stats_interface import stats_interface
            from gradio_modules.search_interface import search_interface
            from gradio_modules.change_password import change_password_interface
            from gradio_modules.file_management import combined_file_interfaces_ui
            from gradio_modules.audio_input import audio_interface

            # Logout tab as a Blocks
            with gr.Blocks() as logout_tab:
                gr.Markdown("## Logout")
                gr.Markdown("Click the button below to log out of your account.")
                logout_btn = gr.Button("Logout", variant="secondary")

                def do_logout():
                    return gr.update(value=False), gr.update(value="")

                logout_btn.click(
                    fn=do_logout,
                    outputs=[logged_in_state, username_state],
                    queue=False,
                )

            # Build actual tabs
            demo_tabs = gr.TabbedInterface(
                [
                    chatbot_ui(
                        username_state,
                        all_chats_data_state,
                        chat_id_state,
                        chat_history_state,
                        debug_info_state,
                    ),
                    combined_file_interfaces_ui(
                        username_state,
                        logged_in_state,
                        debug_info_state,
                        all_chats_data_state,
                        chat_id_state,
                        chat_history_state,
                    ),
                    audio_interface(
                        username_state, audio_history_state, debug_info_state
                    ),
                    search_interface(
                        username_state,
                        all_chats_data_state,
                        audio_history_state,
                        debug_info_state,
                    ),
                    stats_interface(username_state, logged_in_state, debug_info_state),
                    change_password_interface(username_state, logged_in_state),
                    logout_tab,
                ],
                [
                    "Chat",
                    "Files",
                    "Audio",
                    "Search",
                    "Stats",
                    "Change Password",
                    "Logout",
                ],
            )
            demo_tabs

        # Show/hide containers after login/logout
        def handle_login_state(logged_in, username):
            print(
                f"[DEBUG] handle_login_state called: logged_in={logged_in}, username={username}"
            )
            # Hide login/register UI and show main app container after login
            result = (
                gr.update(visible=not logged_in),  # login_container
                gr.update(visible=logged_in),  # main_container
            )
            print(
                f"[DEBUG] handle_login_state result: login_container.visible={not logged_in}, main_container.visible={logged_in}"
            )
            return result

        logged_in_state.change(
            fn=handle_login_state,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_container],
            queue=False,
        )

        app.load(
            fn=handle_login_state,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_container],
            queue=False,
        )

        # The logout button logic is now handled within the logout interface

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

        # Login/Register button logic (ensure handle_primary_btn_click is always called)
        def call_handle_primary_btn_click(*args):
            # Always call the async handle_primary_btn_click
            return asyncio.run(handle_primary_btn_click(*args))

        # Wrap handle_primary_btn_click to ensure UI state is updated after login/register
        async def handle_and_update(*args):
            error_msg, logged_in, username_val = await handle_primary_btn_click(*args)
            print(
                f"[DEBUG] handle_and_update: logged_in={logged_in}, username_val={username_val}"
            )
            # If login was successful, update states to trigger UI change
            if logged_in is True:
                print("[DEBUG] Login successful, updating states to True and username.")
                return (
                    error_msg,
                    True,  # Update logged_in_state to True
                    username_val.value
                    if hasattr(username_val, "value")
                    else username_val,  # Update username_state
                )
            else:
                print("[DEBUG] Login failed, keeping login_container visible.")
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
