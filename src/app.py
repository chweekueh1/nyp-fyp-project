import os
import asyncio
import gradio as gr

from gradio_modules.login_and_register import login_interface
from gradio_modules.chatbot import chatbot_ui
from gradio_modules.search_interface import search_interface
from gradio_modules.audio_input import audio_interface
from gradio_modules.stats_interface import create_stats_interface
from flexcyon_theme import flexcyon_theme

from performance_utils import (
    start_app_startup_tracking,
    mark_startup_milestone,
    complete_app_startup_tracking,
    get_total_startup_time,
    apply_all_optimizations,
)
from backend import init_backend


def load_custom_css():
    css = ""
    styles_dir = os.path.join(os.path.dirname(__file__), "../styles")
    for fname in ["performance.css", "styles.css"]:
        fpath = os.path.join(styles_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                css += f.read() + "\n"
    return css


def main():
    # --- Performance and startup tracking ---
    start_app_startup_tracking()
    apply_all_optimizations()
    mark_startup_milestone("optimizations_applied")

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
            backend_ready["ready"] = True
        except Exception as e:
            mark_startup_milestone(f"app.py: backend init failed ({e})")
            backend_ready["ready"] = False
        finally:
            complete_app_startup_tracking()
            total_time = get_total_startup_time()
            print(
                f"🟢 [DEBUG] App startup tracking complete. Total startup time: {total_time:.2f}s"
            )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(backend_init_thread)

    # --- Gradio App UI ---
    # --- Wait for backend to be ready before exposing the UI ---
    import time

    print("⏳ Waiting for backend to initialize before starting Gradio app...")
    while not backend_ready["ready"]:
        time.sleep(0.2)
    print("✅ Backend initialized. Launching Gradio app...")

    with gr.Blocks(
        title="NYP FYP CNC Chatbot", theme=flexcyon_theme, css=custom_css
    ) as app:
        # --- Shared States ---
        chat_id_state = gr.State("")
        chat_history_state = gr.State([])
        all_chats_data_state = gr.State({})
        debug_info_state = gr.State("")
        audio_history_state = gr.State([])

        # --- Login Interface ---
        # Place all login/register components in a visible column.
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
        with gr.Column(visible=True) as login_container:
            # Do NOT call main_container.render() here! All components are already created and events are wired up in login_interface.
            pass

        # --- Main Tabs (hidden until login) ---
        with gr.Tabs(visible=False) as main_tabs:
            pass  # Tabs will be constructed after login

        # --- Logout Handler ---
        def handle_logout():
            return (
                False,  # logged_in_state = False
                "",  # username_state = ""
                gr.update(visible=False),  # main_tabs
                gr.update(visible=True),  # login_container
            )

        # --- Main Tabs Construction ---
        def construct_main_tabs():
            with main_tabs:
                # --- Chatbot Tab ---
                with gr.Tab("💬 Chat"):
                    chatbot_ui(
                        username_state,
                        chat_id_state,
                        chat_history_state,
                        all_chats_data_state,
                        debug_info_state,
                    )

                # --- Search Tab ---
                with gr.Tab("🔍 Search"):
                    search_interface(
                        username_state,
                        chat_id_state,
                        chat_history_state,
                        all_chats_data_state,
                        debug_info_state,
                        audio_history_state,
                    )

                # --- File Upload Tab ---
                with gr.Tab("📁 File Upload"):
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
                    stats_interface = create_stats_interface()
                    if hasattr(stats_interface, "launch"):
                        stats_interface.launch(inline=True, share=False)

                # --- Reset Password Tab ---
                with gr.Tab("🔑 Reset Password"):
                    from gradio_modules.change_password import change_password_interface

                    change_password_interface(
                        username_state=username_state,
                        logged_in_state=logged_in_state,
                    )

                # --- Logout Button ---
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

        # --- Login State Change Handler ---
        def handle_login_state_change(logged_in: bool, username: str):
            if logged_in:
                if not hasattr(main_tabs, "_initialized") or not main_tabs._initialized:
                    construct_main_tabs()
                    main_tabs._initialized = True
                return (
                    gr.update(visible=False),  # login_container
                    gr.update(visible=True),  # main_tabs
                )
            else:
                return (
                    gr.update(visible=True),  # login_container
                    gr.update(visible=False),  # main_tabs
                )

        logged_in_state.change(
            fn=handle_login_state_change,
            inputs=[logged_in_state, username_state],
            outputs=[login_container, main_tabs],
        )

    # Use optimized Gradio launch config to ensure server persists
    from performance_utils import get_optimized_launch_config

    launch_config = get_optimized_launch_config()
    app.launch(**launch_config)


if __name__ == "__main__":
    main()
