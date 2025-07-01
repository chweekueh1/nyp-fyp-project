#!/usr/bin/env python3
"""
NYP FYP Chatbot Application - Modular Interface Design
Organized with tabbed interfaces and modular components.
"""

import sys
import asyncio
from pathlib import Path
import gradio as gr
from utils import setup_logging
from performance_utils import (
    perf_monitor,
    get_optimized_launch_config,
    apply_all_optimizations,
    start_app_startup_tracking,
    mark_startup_milestone,
    complete_app_startup_tracking,
)
from flexcyon_theme import FlexcyonTheme
import os

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
logger = setup_logging()

# Start comprehensive app startup tracking
start_app_startup_tracking()

# Apply all performance optimizations immediately
apply_all_optimizations()
mark_startup_milestone("optimizations_applied")

# Start performance monitoring
perf_monitor.start_timer("app_startup")


def initialize_backend_in_background():
    """Initialize the backend in a separate thread (truly non-blocking)."""
    import threading
    import tempfile
    import os

    # Create a status file to track initialization
    status_file = os.path.join(tempfile.gettempdir(), "nyp_chatbot_backend_status.txt")

    def background_init():
        """Background thread function for backend initialization."""
        try:
            # Write initializing status
            with open(status_file, "w") as f:
                f.write("initializing")

            logger.info("🚀 Starting background backend initialization...")
            logger.info("⏳ This will initialize ChromaDB and AI models...")

            # Delay the import until we're ready to initialize
            # This prevents ChromaDB from initializing during module import
            import importlib

            # Initialize backend asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Import backend module (this will trigger ChromaDB init)
                backend_module = importlib.import_module("backend")

                # Call the initialization function
                loop.run_until_complete(backend_module.init_backend())
                logger.info("✅ Backend initialization completed successfully")
                # Write success status
                with open(status_file, "w") as f:
                    f.write("ready")
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"⚠️ Backend initialization failed: {e}")
            # Write failure status
            with open(status_file, "w") as f:
                f.write("failed")

    # Start background thread
    thread = threading.Thread(target=background_init, daemon=True)
    thread.start()
    logger.info("🔄 Backend initialization started in background thread")


def get_backend_status():
    """Get the current backend status from file."""
    import tempfile
    import os

    status_file = os.path.join(tempfile.gettempdir(), "nyp_chatbot_backend_status.txt")
    try:
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                return f.read().strip()
        else:
            return "initializing"
    except Exception:
        return "initializing"


def load_css_file(filename):
    """Load CSS from external file for better performance."""
    try:
        with open(f"styles/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"CSS file {filename} not found, using minimal styles")
        return ".gradio-container { max-width: 1200px !important; margin: 0 auto !important; }"


def create_main_app():
    """Create the main application with performance optimizations."""

    # Load optimized CSS and theme
    mark_startup_milestone("loading_css")
    performance_css = load_css_file("performance.css")
    styles_css = load_css_file("styles.css")
    combined_css = performance_css + "\n" + styles_css

    # Create custom theme
    custom_theme = FlexcyonTheme()

    mark_startup_milestone("creating_gradio_blocks")
    with gr.Blocks(
        title="NYP FYP Chatbot", theme=custom_theme, css=combined_css
    ) as app:
        # State variables
        logged_in_state = gr.State(False)
        username_state = gr.State("")
        backend_status_state = gr.State(
            "initializing"
        )  # "initializing", "ready", "failed"

        # Loading screen (visible initially)
        with gr.Column(visible=True) as loading_section:
            gr.Markdown("# 🚀 NYP FYP Chatbot")
            gr.Markdown("## ⏳ Loading Application...")

            # Loading spinner
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; margin: 30px;">
                <div class="loading-spinner"></div>
            </div>
            """)

            loading_status = gr.Markdown(
                "🎨 **Loading user interface...** Please wait..."
            )

            gr.Markdown("""
            **Initializing:**
            - 🎨 User interface components
            - 🔐 Authentication system
            - 🤖 AI models (in background)
            - 🗄️ Database connections (in background)
            - 📊 Vector stores (in background)

            *The interface will load first, then backend services will initialize in the background.*
            """)

            # Button to manually proceed if backend takes too long
            start_backend_btn = gr.Button(
                "⚡ Proceed Anyway (Limited Mode)", variant="secondary", visible=True
            )

        # Login interface container (hidden initially)
        mark_startup_milestone("creating_login_interface")
        with gr.Column(visible=False) as login_section:
            # Import and create login interface
            try:
                from gradio_modules.login_and_register import login_interface

                login_components = login_interface(setup_events=True)

                # Unpack new dynamic login components
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
                ) = login_components

            except ImportError as e:
                gr.Markdown(f"⚠️ **Login interface not available:** {e}")
                gr.Markdown(
                    "Please check the gradio_modules.login_and_register module."
                )

        # Main application container (hidden initially)
        mark_startup_milestone("creating_main_interface")
        with gr.Column(visible=False) as main_section:
            gr.Markdown("# 🎉 Welcome to NYP FYP Chatbot!")

            # User info and logout
            with gr.Row():
                user_info = gr.Markdown("", elem_id="user_info")
                logout_btn = gr.Button("🚪 Logout", variant="secondary", size="sm")

            # Tabbed interface for different functionalities
            mark_startup_milestone("creating_tabbed_interface")
            with gr.Tabs():
                # Chat Tab
                with gr.TabItem("💬 Chat", id="chat_tab"):
                    try:
                        from gradio_modules.chatbot import chatbot_ui

                        # Create states for the chatbot interface
                        chat_history_state = gr.State([])
                        selected_chat_id = gr.State("")

                        # Create the chatbot interface
                        chatbot_ui(
                            username_state,
                            chat_history_state,
                            selected_chat_id,
                            setup_events=True,
                        )

                    except ImportError as e:
                        gr.Markdown(f"⚠️ **Chatbot interface not available:** {e}")
                        gr.Markdown("Using basic fallback interface.")

                        # Fallback basic interface
                        gr.Textbox(
                            label="Message", placeholder="Type your message here..."
                        )
                        gr.Button("Send", variant="primary")
                        gr.Textbox(label="Response", interactive=False)

                # File Classification Tab
                with gr.TabItem("📄 File Classification", id="classification_tab"):
                    try:
                        from gradio_modules.file_classification import (
                            file_classification_interface,
                        )

                        # Create the file classification interface
                        file_classification_interface(username_state)

                    except ImportError as e:
                        gr.Markdown(
                            f"⚠️ **File classification interface not available:** {e}"
                        )
                        gr.Markdown(
                            "Please check the gradio_modules.file_classification module."
                        )

                # Audio Input Tab
                with gr.TabItem("🎤 Audio Input", id="audio_tab"):
                    try:
                        from gradio_modules.audio_input import audio_interface

                        # Create the audio interface
                        audio_interface(username_state, setup_events=True)

                    except ImportError as e:
                        gr.Markdown(f"⚠️ **Audio interface not available:** {e}")
                        gr.Markdown(
                            "Please check the gradio_modules.audio_input module."
                        )

                        # Fallback basic interface
                        gr.Audio(label="Record Audio", type="filepath")
                        gr.Button("Process Audio", variant="primary")
                        gr.Textbox(label="Transcription", interactive=False)

        # File Upload Tab removed - functionality integrated into File Classification tab

        # Backend status indicator
        with gr.Row():
            backend_status = gr.Markdown(
                "🔄 **Backend Status:** Checking...", visible=False
            )
            refresh_status_btn = gr.Button(
                "🔄 Refresh Status", size="sm", visible=False
            )

        # Event handlers for login/logout
        def handle_login_success(logged_in, username, backend_status_state):
            """Handle successful login."""
            if logged_in and username:
                # Check current backend status from file
                current_status = get_backend_status()
                if current_status == "ready":
                    status_msg = "✅ **Backend ready!** All features available."
                elif current_status == "failed":
                    status_msg = (
                        "⚠️ **Limited mode:** Some features may not be available."
                    )
                else:
                    status_msg = "🔄 **Backend initializing...** Please wait for full functionality."

                return (
                    gr.update(visible=False),  # Hide login section
                    gr.update(visible=True),  # Show main section
                    f"**Logged in as:** {username}",  # Update user info
                    gr.update(visible=True, value=status_msg),  # Show backend status
                    gr.update(visible=True),  # Show refresh button
                )
            else:
                return (
                    gr.update(visible=True),  # Show login section
                    gr.update(visible=False),  # Hide main section
                    "",  # Clear user info
                    gr.update(visible=False),  # Hide backend status
                    gr.update(visible=False),  # Hide refresh button
                )

        def handle_logout():
            """Handle logout with proper state reset for dynamic login interface."""
            logger.info("User logged out")
            return (
                False,  # Reset logged_in_state to False
                "",  # Reset username_state to empty
                False,  # Reset is_register_mode to False (login mode)
                gr.update(visible=True),  # Show login section
                gr.update(visible=False),  # Hide main section
                "",  # Clear user info
                gr.update(visible=False),  # Hide backend status
                gr.update(visible=False),  # Hide refresh button
                "",  # Clear username input
                "",  # Clear email input
                "",  # Clear password input
                "",  # Clear confirm password input
                gr.update(visible=False),  # Hide error message
                gr.update(value="## 🔐 Login"),  # Reset header to login mode
                gr.update(
                    value="Please log in to access the chatbot."
                ),  # Reset instruction
                gr.update(visible=False),  # Hide email info
                gr.update(visible=False),  # Hide password requirements
                gr.update(visible=False),  # Hide confirm password input
                gr.update(visible=False),  # Hide confirm password button
                gr.update(value="Login", variant="primary"),  # Reset primary button
                gr.update(
                    value="Register", variant="secondary"
                ),  # Reset secondary button
            )

        # Wire up logout event with proper state reset for dynamic login interface
        logout_btn.click(
            fn=handle_logout,
            outputs=[
                logged_in_state,
                username_state,
                is_register_mode,  # Reset login states
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,  # UI updates
                username_input,
                email_input,
                password_input,
                confirm_password_input,
                error_message,  # Clear form inputs
                header_subtitle,
                header_instruction,
                email_info,
                password_requirements,  # Reset form content
                confirm_password_input,
                show_confirm_btn,
                primary_btn,
                secondary_btn,  # Reset form controls
            ],
        )

        # Monitor login state changes
        logged_in_state.change(
            fn=handle_login_success,
            inputs=[logged_in_state, username_state, backend_status_state],
            outputs=[
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,
            ],
        )

        def check_backend_status():
            """Check the current backend initialization status."""
            current_status = get_backend_status()
            if current_status == "initializing":
                return gr.update(value="🔄 **Initializing backend...** Please wait...")
            elif current_status == "ready":
                return gr.update(value="✅ **Backend ready!** All features available.")
            else:
                return gr.update(
                    value="⚠️ **Limited mode:** Some features may not be available."
                )

        # Wire up refresh status button
        refresh_status_btn.click(fn=check_backend_status, outputs=[backend_status])

        # Wire up refresh status button
        refresh_status_btn.click(fn=check_backend_status, outputs=[backend_status])

        # UI Loading sequence - start backend, wait for completion, then show login
        def start_backend_and_wait_for_completion():
            """Start backend initialization and wait for it to complete before showing login."""
            import time

            # Step 1: Start backend initialization in background (non-blocking)
            initialize_backend_in_background()

            # Step 2: Wait for backend initialization to complete
            max_wait_time = 120  # Maximum 2 minutes wait
            poll_interval = 3  # Check every 3 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                status = get_backend_status()

                if status == "ready":
                    # Backend is ready, show login interface
                    return (
                        gr.update(visible=False),  # Hide loading screen
                        gr.update(visible=True),  # Show login interface
                        "✅ **Backend ready!** You can now log in.",  # Update status
                    )
                elif status == "failed":
                    # Backend failed, show login interface anyway (limited mode)
                    return (
                        gr.update(visible=False),  # Hide loading screen
                        gr.update(visible=True),  # Show login interface
                        "⚠️ **Limited mode:** Backend initialization failed. Some features may not be available.",
                    )

                # Still initializing, wait and check again
                time.sleep(poll_interval)
                elapsed_time += poll_interval

            # Timeout reached, show login interface anyway
            return (
                gr.update(visible=False),  # Hide loading screen
                gr.update(visible=True),  # Show login interface
                "⚠️ **Timeout:** Backend initialization took too long. You can log in but some features may not be available.",
            )

        # Start backend and wait for completion when app loads
        app.load(
            fn=start_backend_and_wait_for_completion,
            outputs=[loading_section, login_section, loading_status],
        )

        # Manual proceed button (for users who don't want to wait)
        def proceed_anyway():
            """Allow users to proceed to login even if backend isn't ready."""
            return (
                gr.update(visible=False),  # Hide loading screen
                gr.update(visible=True),  # Show login interface
                "⚠️ **Limited mode:** You chose to proceed before backend initialization completed. Some features may not be available.",
            )

        start_backend_btn.click(
            fn=proceed_anyway, outputs=[loading_section, login_section, loading_status]
        )

    return app


if __name__ == "__main__":
    print("🚀 Starting NYP FYP Chatbot - Modular Interface Design")
    print("=" * 60)
    print("🎨 Creating application with tabbed interfaces...")
    print("⚡ Features:")
    print("  - Modular interface design")
    print("  - Optional backend initialization")
    print("  - Tabbed interface layout")
    print("  - Enhanced user experience")
    print("=" * 60)

    try:
        # Detect Docker and print a message
        if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
            print(
                "🐳 Running inside a Docker container. All dependencies should be pre-installed."
            )

        # Apply performance optimizations
        perf_monitor.start_timer("app_creation")
        mark_startup_milestone("starting_app_creation")

        # Create the main application
        app = create_main_app()
        perf_monitor.end_timer("app_creation")
        mark_startup_milestone("app_creation_complete")

        print("✅ Application interface created successfully")
        print("🌐 Launching application...")
        print("=" * 60)
        print("🔄 Available Features:")
        print("  - 💬 Chat Interface")
        print("  - 📄 File Classification & Upload")
        print("  - 🎤 Audio Input & Transcription")
        print("=" * 60)
        print("🔐 Authentication Features:")
        print("  - Username or email login")
        print("  - Authorized email domains")
        print("  - Enhanced password requirements")
        print("  - Password visibility toggles")
        print("=" * 60)
        print("📧 Authorized Email Domains:")
        print("  - @nyp.edu.sg (NYP staff/faculty)")
        print("  - @student.nyp.edu.sg (NYP students)")
        print("  - Selected test emails for development")
        print("=" * 60)

        # Get optimized launch configuration
        launch_config = get_optimized_launch_config()

        # Complete startup tracking BEFORE launching (to exclude runtime)
        perf_monitor.end_timer("app_startup")
        mark_startup_milestone("app_ready_to_launch")
        total_startup_time = complete_app_startup_tracking()

        # Additional summary for console
        print("=" * 60)
        print(f"🎉 APP STARTUP COMPLETED IN {total_startup_time:.2f}s")
        print("🚀 Launching application...")
        print("=" * 60)

        # Launch with performance optimizations (this includes runtime, not startup)
        perf_monitor.start_timer("app_runtime")
        mark_startup_milestone("app_launched")

        app.launch(**launch_config)

        # This will only be reached when the app shuts down
        perf_monitor.end_timer("app_runtime")
        runtime = perf_monitor.get_metrics().get("app_runtime", 0)
        logger.info(f"🏁 App runtime: {runtime:.2f}s")

    except Exception as e:
        logger.error(f"❌ Failed to create or launch application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
