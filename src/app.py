# app.py
import os
import asyncio
import gradio as gr
import logging
from typing import Tuple

# Set up basic logging for the main application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import necessary modules
from gradio_modules.login_and_register import login_interface, handle_primary_btn_click
from gradio_modules.chatbot import chatbot_ui
from gradio_modules.file_management import (
    combined_file_interfaces_ui,
)  # Combined file interface
from gradio_modules.audio_input import (
    audio_interface,
)  # This now returns a gr.Blocks object
from gradio_modules.change_password import (
    change_password_interface,
)  # Change password interface
from gradio_modules.stats_interface import (
    create_stats_interface,
)  # Import stats interface
from gradio_modules.search_interface import search_interface  # Import search interface


# Import theme and utility functions
from flexcyon_theme import flexcyon_theme
from performance_utils import (
    start_app_startup_tracking,
    mark_startup_milestone,
    complete_app_startup_tracking,
    get_total_startup_time,
    apply_all_optimizations,
    get_optimized_launch_config,
)
from backend import (
    init_backend,
)  # This imports the async init_backend from backend/main.py


def load_custom_css():
    """Loads custom CSS from the styles directory."""
    css = ""
    styles_dir = "styles"
    for filename in os.listdir(styles_dir):
        if filename.endswith(".css"):
            with open(os.path.join(styles_dir, filename), "r") as f:
                css += f.read() + "\n"
    return css


# Function to toggle password visibility
def toggle_password_visibility(
    current_type: str, current_visibility_state: bool
) -> Tuple[str, bool, str]:
    """Toggles the visibility of a password input field and its button icon."""
    new_type = "text" if current_type == "password" else "password"
    new_visibility_state = not current_visibility_state
    new_icon = "🙈" if new_visibility_state else "👁️"
    return gr.update(type=new_type), new_visibility_state, gr.update(value=new_icon)


async def main():
    start_app_startup_tracking()

    logger.info("Initializing backend...")
    await init_backend()
    mark_startup_milestone("backend_initialized")
    logger.info("Backend initialized.")

    logger.info("Creating Gradio UI components...")
    with gr.Blocks(
        theme=flexcyon_theme,
        css=load_custom_css(),
        title="NYP FYP Chatbot",
    ) as app:
        # Global state variables shared across the application
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        all_chats_data_state = gr.State({})  # Keep track of all chats data
        chat_id_state = gr.State(None)  # Current chat ID
        chat_history_state = gr.State([])  # Current chat history
        debug_info_state = gr.State("")  # For displaying debug info
        audio_history_state = gr.State([])  # For displaying audio history
        is_register_mode_state = gr.State(
            False
        )  # Track which form is active in login/register

        # Global UI components that need to be accessible for visibility/content updates
        user_info_display = gr.Markdown(
            value="", visible=False, elem_id="user_info_display"
        )
        logout_btn_global = gr.Button(
            "Logout", elem_id="logout_btn_global", visible=False
        )
        change_password_btn_global = gr.Button(
            "Change Password", elem_id="change_password_btn_global", visible=False
        )

        # Define containers for login and main application views
        with gr.Column(
            elem_id="login_register_container", visible=True
        ) as login_view_container:
            # Pass the top-level states to login_interface
            # Ensure 16 variables are unpacked to match login_interface's return
            (
                login_main_container,
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
                is_register_mode_state,  # Pass is_register_mode_state
            )

            # Wire the secondary_btn to toggle the mode state
            secondary_btn.click(
                fn=lambda is_reg: not is_reg,
                inputs=[is_register_mode_state],
                outputs=[is_register_mode_state],
                queue=False,
            )

            # Wire is_register_mode_state.change to update UI elements
            is_register_mode_state.change(
                fn=lambda is_reg: (
                    gr.update(value="Register" if is_reg else "Login"),  # primary_btn
                    gr.update(
                        value="Already have an account?"
                        if is_reg
                        else "Don't have an account?"
                    ),  # secondary_btn
                    gr.update(visible=is_reg),  # email_input
                    gr.update(visible=is_reg),  # confirm_password_input
                    gr.update(visible=is_reg),  # show_confirm_btn
                    gr.update(visible=not is_reg),  # email_info
                    gr.update(visible=is_reg),  # password_requirements
                    gr.update(
                        value="## 📝 Register" if is_reg else "## 🔐 Login"
                    ),  # header_subtitle
                    gr.update(
                        value="Please register to create an account."
                        if is_reg
                        else "Please log in to access the chatbot."
                    ),  # header_instruction
                    gr.update(value=""),  # Clear username/email input
                    gr.update(value=""),  # Clear password input
                    gr.update(value=""),  # Clear confirm password input
                    gr.update(
                        value="", visible=False
                    ),  # Clear error message and hide it
                ),
                inputs=[is_register_mode_state],
                outputs=[
                    primary_btn,
                    secondary_btn,
                    email_input,
                    confirm_password_input,
                    show_confirm_btn,  # Added to outputs for update
                    email_info,
                    password_requirements,
                    header_subtitle,  # Added to outputs for update
                    header_instruction,  # Added to outputs for update
                    username_input,  # Added for clearing
                    password_input,  # Added for clearing
                    confirm_password_input,  # Added for clearing
                    error_message,  # Added for clearing
                ],
                queue=False,
            )

            # Wire password visibility toggles
            show_password_btn.click(
                fn=toggle_password_visibility,
                inputs=[password_input, password_visible],
                outputs=[password_input, password_visible, show_password_btn],
                queue=False,
            )
            show_confirm_btn.click(
                fn=toggle_password_visibility,
                inputs=[confirm_password_input, confirm_password_visible],
                outputs=[
                    confirm_password_input,
                    confirm_password_visible,
                    show_confirm_btn,
                ],
                queue=False,
            )

            # Wire primary button click for login/registration
            primary_btn.click(
                fn=handle_primary_btn_click,
                inputs=[
                    is_register_mode_state,  # Pass the gr.State object, its value will be used
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

            # Add Enter key support for login/registration
            password_input.submit(
                fn=handle_primary_btn_click,
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
                fn=handle_primary_btn_click,
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

        with gr.Column(
            elem_id="main_app_view_container", visible=False
        ) as main_app_view_container:
            with gr.Row(elem_id="header_row"):
                with gr.Column(scale=1):
                    user_info_display  # Removed .render()
                with gr.Column(scale=1, elem_id="header_buttons_container"):
                    with gr.Row():
                        change_password_btn_global  # Removed .render()
                        logout_btn_global  # Removed .render()

            # Main tabbed interface for the application
            with gr.Tabs(
                selected="💬 Chatbot", elem_id="main_tabs"
            ) as main_tabs_interface:
                with gr.TabItem("💬 Chatbot", id="chatbot_tab"):
                    chatbot_ui(
                        username_state,
                        all_chats_data_state,
                        chat_id_state,
                        chat_history_state,
                        debug_info_state,
                    )
                with gr.TabItem("📁 File Management", id="file_management_tab"):
                    combined_file_interfaces_ui(
                        username_state,
                        logged_in_state,
                        debug_info_state,
                        all_chats_data_state,
                        chat_id_state,
                        chat_history_state,
                    )
                with gr.TabItem("🎤 Audio Input", id="audio_input_tab"):
                    audio_interface(
                        username_state, audio_history_state, debug_info_state
                    )
                with gr.TabItem("📊 Statistics", id="stats_tab"):
                    create_stats_interface(
                        username_state, logged_in_state, debug_info_state
                    )
                with gr.TabItem("🔍 Search", id="search_tab"):
                    search_interface(
                        username_state, logged_in_state, debug_info_state, chat_id_state
                    )
                with gr.TabItem("🔑 Change Password", id="change_password_tab"):
                    # The change password interface is displayed directly as content for this tab
                    change_password_interface(username_state, logged_in_state)

        # --- Event Handlers for Global State and View Management ---
        logger.info("Wiring global event handlers...")
        logged_in_state.change(
            fn=lambda logged_in, username: (
                gr.update(visible=not logged_in),  # login_view_container visibility
                gr.update(visible=logged_in),  # main_app_view_container visibility
                gr.update(
                    value=f"Logged in as: {username}", visible=logged_in
                ),  # user_info_display
                gr.update(visible=logged_in),  # logout_btn_global
                gr.update(visible=logged_in),  # change_password_btn_global
                gr.update(
                    selected="💬 Chatbot" if logged_in else None
                ),  # Set default tab on login
            ),
            inputs=[logged_in_state, username_state],
            outputs=[
                login_view_container,
                main_app_view_container,
                user_info_display,
                logout_btn_global,
                change_password_btn_global,
                main_tabs_interface,  # Also update the tabbed interface on login/logout
            ],
            queue=False,  # UI updates should not be queued
        )

        # Initial visibility setup when the app loads
        app.load(
            fn=lambda logged_in, username: (
                gr.update(visible=not logged_in),
                gr.update(visible=logged_in),
                gr.update(value=f"Logged in as: {username}", visible=logged_in),
                gr.update(visible=logged_in),
                gr.update(visible=logged_in),
                gr.update(
                    selected="💬 Chatbot" if logged_in else None
                ),  # Set default tab on login
            ),
            inputs=[logged_in_state, username_state],
            outputs=[
                login_view_container,
                main_app_view_container,
                user_info_display,
                logout_btn_global,
                change_password_btn_global,
                main_tabs_interface,  # Also update the tabbed interface on load
            ],
            queue=False,
            show_progress="hidden",
        )

        # --- Global Logout Button ---
        logout_btn_global.click(
            fn=lambda: [
                False,
                "",
            ],  # Set logged_in_state to False, username_state to empty
            outputs=[logged_in_state, username_state],
            queue=False,
        )

        # Wire global change password button to select its tab
        change_password_btn_global.click(
            fn=lambda: gr.update(
                selected="🔑 Change Password"  # Use 'selected' with the tab title string
            ),
            outputs=[main_tabs_interface],  # Target the TabbedInterface to change tab
            queue=False,
        )

    # Apply performance optimizations (ensure this runs AFTER all components are defined)
    apply_all_optimizations()
    mark_startup_milestone("optimizations_applied")
    logger.info("Performance optimizations applied.")

    # Initialize the queue for backend operations
    app.queue()  # This should set up the queueing system fully
    mark_startup_milestone("queue_initialized")
    logger.info("Gradio queue initialized.")

    # Use optimized Gradio launch config
    launch_config = get_optimized_launch_config()

    complete_app_startup_tracking()
    total_startup_time = get_total_startup_time()
    logger.info(f"APP STARTUP COMPLETED IN {total_startup_time:.2f}s")
    logger.info("🚀 Launching application...")

    app.launch(**launch_config)


if __name__ == "__main__":
    asyncio.run(main())
