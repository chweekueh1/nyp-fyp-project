def load_custom_css():
    import os

    css = ""
    styles_dir = os.path.join(os.path.dirname(__file__), "../styles")
    for fname in ["styles.css", "performance.css"]:
        fpath = os.path.join(styles_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                css += f.read() + "\n"
    return css


import asyncio
import gradio as gr

from gradio_modules.login_and_register import login_interface
from gradio_modules.chatbot import chatbot_ui
from gradio_modules.search_interface import search_interface
from gradio_modules.audio_input import audio_interface
from gradio_modules.stats_interface import create_stats_interface
from gradio_modules.theme import flexcyon_theme

from performance_utils import (
    mark_startup_milestone,
    complete_app_startup_tracking,
)
from backend import init_backend, get_backend_status


def main():
    # Load custom CSS
    custom_css = load_custom_css()

    # --- Backend Initialization in Background Thread ---
    import concurrent.futures

    backend_ready = {"ready": False}

    def backend_init_thread():
        mark_startup_milestone("app.py: before backend init")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_backend())
            mark_startup_milestone("app.py: after backend init")
            complete_app_startup_tracking()
            backend_ready["ready"] = True
        except Exception:
            backend_ready["ready"] = False

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(backend_init_thread)

    # --- Loading Screen ---
    with gr.Blocks(
        title="NYP FYP CNC Chatbot", theme=flexcyon_theme, css=custom_css
    ) as app:
        with gr.Column(visible=True) as loading_container:
            gr.Markdown(
                """
                # 🕒 Initializing Chatbot...
                <div style="font-size:1.2em;">Please wait while the backend is starting up.<br>
                This may take up to a minute on first launch.</div>
                """,
                elem_id="loading_screen",
            )
            loading_status = gr.Markdown(
                "Backend status: Initializing...", elem_id="loading_status"
            )

        # Login interface - only visible when backend is ready and not logged in
        with gr.Column(visible=False) as login_container:
            (
                logged_in_state,
                username_state,
                is_register_mode,
                main_container,
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
            ) = login_interface(setup_events=True)

        # Shared states for all tabs
        chat_id_state = gr.State("")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")
        audio_history_state = gr.State([])  # For audio session history

        # Main application tabs - visibility controlled by login state
        with gr.Tabs(visible=False) as main_tabs:
            pass  # Tabs will be dynamically constructed after backend is ready

        # Add logout functionality
        def handle_logout():
            """Handle logout - reset authentication state."""
            return (
                False,  # logged_in_state = False
                "",  # username_state = ""
                gr.update(visible=False),  # main_tabs visible = False (hide tabs)
                gr.update(visible=True),  # login_container visible = True (show login)
            )

        # Handle login state changes to show/hide appropriate interfaces
        def handle_login_state_change(logged_in: bool, username: str):
            """Handle login state changes to show/hide appropriate interfaces."""
            if logged_in:
                # User logged in - hide login, show main tabs
                return (
                    gr.update(visible=False),  # login_container
                    gr.update(visible=True),  # main_tabs
                )
            else:
                # User not logged in - show login, hide main tabs
                return (
                    gr.update(visible=True),  # login_container
                    gr.update(visible=False),  # main_tabs
                )

        # Connect login state changes to interface visibility
        logged_in_state.change(
            fn=handle_login_state_change,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_tabs],
        )

        # Dynamically construct main tabs after backend is ready
        def construct_main_tabs():
            with main_tabs:
                # --- Chatbot Tab ---
                with gr.Tab("💬 Chat"):
                    (
                        chat_selector,
                        chatbot,
                        msg,
                        send_btn,
                        rename_input,
                        rename_btn,
                        rename_status_md,
                        search_container,
                        search_stats_md,
                        debug_md,
                        clear_chat_btn,
                        clear_chat_status,
                        new_chat_btn,
                    ) = chatbot_ui(
                        username_state,
                        chat_id_state,
                        chat_history_state,
                        all_chats_data_state,
                        debug_info_state,
                    )

                # --- Search Tab ---
                with gr.Tab("🔍 Search"):
                    (
                        search_container,
                        search_query,
                        search_btn,
                        search_results_md,
                        search_stats_md,
                    ) = search_interface(
                        username_state,
                        chat_id_state,
                        chat_history_state,
                        all_chats_data_state,
                        debug_info_state,
                        audio_history_state,
                    )

                # --- File Upload Tab ---
                with gr.Tab("📁 File Upload"):
                    # Use the new file_classification interface and event setup
                    from gradio_modules.file_classification import (
                        file_classification_interface,
                        setup_file_classification_events,
                    )

                    file_classification_components = file_classification_interface(
                        username_state
                    )
                    setup_file_classification_events(
                        file_classification_components, username_state
                    )

                # --- Audio Input Tab ---
                with gr.Tab("🎤 Audio Input"):
                    audio_interface(
                        username_state,
                        setup_events=True,
                    )

                # --- Stats Tab ---
                with gr.Tab("📊 Stats"):
                    # Use the new stats interface (returns a Gradio Interface)
                    stats_interface = create_stats_interface()
                    if hasattr(stats_interface, "launch"):
                        stats_interface.launch(inline=True, share=False)

                # --- Reset Password Tab (if needed) ---
                with gr.Tab("🔑 Reset Password"):
                    from gradio_modules.change_password import change_password_interface

                    change_password_interface(
                        username_state=username_state,
                        logged_in_state=logged_in_state,
                    )

                # Add logout button to the main tabs
                logout_btn = gr.Button("🚪 Logout", variant="secondary")
                logout_btn.click(
                    fn=handle_logout,
                    outputs=[
                        logged_in_state,
                        username_state,
                        main_tabs,
                        login_container,
                    ],
                )

        # --- Polling function to check backend status ---
        def poll_backend_status():
            try:
                status = get_backend_status()
                if status.get("ready", False) or backend_ready["ready"]:
                    if (
                        not hasattr(main_tabs, "_initialized")
                        or not main_tabs._initialized
                    ):
                        construct_main_tabs()
                        main_tabs._initialized = True
                    return (
                        gr.update(visible=False),  # loading_container
                        gr.update(visible=True),  # login_container
                        gr.update(visible=True),  # main_tabs
                        "Backend status: Ready! Please log in.",
                    )
                msg = "Backend status: Initializing..."
                if "error" in status:
                    msg = f"Backend error: {status['error']}"
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    msg,
                )
            except Exception as e:
                msg = f"Backend error: {e}"
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    msg,
                )

        # --- Hidden polling button and thread ---
        polling_btn = gr.Button(visible=False)

        polling_btn.click(
            fn=poll_backend_status,
            outputs=[loading_container, login_container, main_tabs, loading_status],
            queue=False,
        )

        def start_polling():
            import threading
            import time

            def poll():
                while True:
                    try:
                        polling_btn.click()
                        time.sleep(1)
                        # Stop polling if backend is ready and main_tabs is initialized
                        if (
                            hasattr(main_tabs, "_initialized")
                            and main_tabs._initialized
                        ):
                            break
                    except Exception:
                        break

            threading.Thread(target=poll, daemon=True).start()

        # Start polling as soon as the UI is loaded
        app.load(fn=lambda: None, outputs=[])  # dummy load to trigger UI load event
        start_polling()

    app.launch()


if __name__ == "__main__":
    main()
