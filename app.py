#!/usr/bin/env python3
"""
NYP FYP Chatbot Application - Modular Interface Design

Organized with tabbed interfaces and modular components.
"""

import sys
import asyncio
from pathlib import Path
from typing import Tuple
import gradio as gr
from infra_utils import setup_logging
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

# --- Centralized LLM, Embedding, DuckDB Vector Store, and OpenAI Client Initialization ---
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import openai
from backend.database import get_duckdb_collection
from backend import config as backend_config

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
else:
    logger.critical(
        "OPENAI_API_KEY environment variable not set. Chat features will not work."
    )

# Initialize LLM and embedding
llm = None
embedding = None
try:
    # Using direct model and temperature as per old app.py
    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    logger.info("LLM and embedding models initialized.")
except Exception as e:
    logger.error(f"Failed to initialize LLM or embedding: {e}")

# Initialize DuckDB vector stores
classification_db = None
chat_db = None
try:
    # Passing only one argument as per old app.py
    classification_db = get_duckdb_collection("classification")
    chat_db = get_duckdb_collection("chat")
    logger.info("DuckDB vector stores initialized.")
except Exception as e:
    logger.error(f"Failed to initialize DuckDB vector stores: {e}")

# Inject into modules
import llm.classificationModel as classificationModel
import llm.dataProcessing as dataProcessing


# Inject dependencies for classification workflow
classificationModel.llm = llm
classificationModel.embedding = embedding
classificationModel.db = classification_db
classificationModel.initialize_classification_workflow()

dataProcessing.embedding = embedding
dataProcessing.classification_db = classification_db
dataProcessing.chat_db = chat_db

backend_config.client = client


def initialize_backend_in_background() -> None:
    """
    Initializes the backend in a separate thread to avoid blocking the Gradio UI startup.

    This function sets up a status file to track the initialization progress
    and logs messages to indicate the status.
    """
    import threading
    import tempfile
    import os

    # Create a status file to track initialization
    status_file = os.path.join(tempfile.gettempdir(), "nyp_chatbot_backend_status.txt")

    def background_init() -> None:
        """
        Background thread function for backend initialization.

        This function performs the actual backend setup, including importing
        and initializing the backend module, and updates the status file.
        """
        try:
            # Write initializing status
            with open(status_file, "w") as f:
                f.write("initializing")

            logger.info("🚀 Starting background backend initialization...")
            logger.info("⏳ This will initialize DuckDB vector store and AI models...")

            # Delay the import until we're ready to initialize
            # This prevents DuckDB vector store from initializing during module import
            import importlib

            # Initialize backend asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Import backend module (this will trigger ChromaDB init)
            backend_module = importlib.import_module("backend")

            # Call the initialization function
            loop.run_until_complete(backend_module.init_backend())
            logger.info("✅ Backend initialization completed successfully")
            # Write success status
            with open(status_file, "w") as f:
                f.write("ready")
        except Exception as e:
            logger.warning(f"⚠️ Backend initialization failed: {e}")
            # Write failure status
            with open(status_file, "w") as f:
                f.write("failed")
        finally:
            loop.close()

    # Start background thread
    thread = threading.Thread(target=background_init, daemon=True)
    thread.start()
    logger.info("🔄 Backend initialization started in background thread")


def get_backend_status() -> str:
    """
    Gets the current backend status from the status file.

    :return: The status string ('initializing', 'ready', 'failed').
    :rtype: str
    """
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


def load_css_file(filename: str) -> str:
    """
    Loads CSS from an external file for better performance.

    :param filename: The name of the CSS file.
    :type filename: str
    :return: The content of the CSS file, or a minimal style if not found.
    :rtype: str
    """
    try:
        with open(f"styles/{filename}", "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"CSS file {filename} not found, using minimal styles")
        return ".gradio-container { max-width: 1200px !important; margin: 0 auto !important; }"


def create_main_app() -> gr.Blocks:
    """
    Creates the main Gradio application with performance optimizations.

    :return: The configured Gradio Blocks application instance.
    :rtype: gr.Blocks
    """

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
        # State variables - ALL REQUIRED STATES MUST BE INITIALIZED HERE
        username_state = gr.State("")
        logged_in_state = gr.State(False)
        user_role_state = gr.State("guest")  # e.g., 'guest', 'user', 'admin'

        # State for current chat session
        chat_id_state = gr.State("")
        chat_history_state = gr.State(
            []
        )  # Stores the history for the currently loaded chat
        all_chats_data_state = gr.State(
            {}
        )  # Stores metadata and history for ALL user chats {chat_id: {name, history}}
        debug_info_state = gr.State("")  # For displaying debug messages

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
            try:
                # Corrected import: Using login_interface from login_and_register
                from gradio_modules.login_and_register import login_interface

                # login_interface returns a tuple of 19 Gradio components (based on snippet)
                # It handles its own event setup internally. We only need the states.
                (
                    logged_in_state_from_login,  # This is the state returned by login_interface
                    username_state_from_login,  # This is the state returned by login_interface
                    _is_register_mode,  # Internal state, not directly used by app.py's UI logic
                    _main_container_login,
                    _error_message,
                    _username_input,
                    _email_input,
                    _password_input,
                    _confirm_password_input,
                    _primary_btn,
                    _secondary_btn,
                    _show_password_btn,
                    _show_confirm_btn,
                    _password_visible,
                    _confirm_password_visible,
                    _header_subtitle,  # This is the "Login" or "Register" markdown
                    _header_instruction,  # This is the instruction markdown
                    _email_info,
                    _password_requirements,
                ) = login_interface()

                # Link the states from login_interface to the main app states
                logged_in_state_from_login.change(
                    lambda x: x,
                    inputs=[logged_in_state_from_login],
                    outputs=[logged_in_state],
                )
                username_state_from_login.change(
                    lambda x: x,
                    inputs=[username_state_from_login],
                    outputs=[username_state],
                )

            except ImportError as e:
                gr.Markdown(f"⚠️ **Login interface not available:** {e}")
                gr.Markdown(
                    "Please check the gradio_modules.login_and_register module."
                )

            # Define components for overall login status display, managed by main_interface
            # These are defined here, outside the try-except, to ensure they always exist
            login_status_message = gr.Markdown(
                "Please log in to continue.", elem_id="login-status-message"
            )
            logout_button = gr.Button("Logout", visible=False, elem_id="logout-button")
            username_display = gr.Markdown("", elem_id="username-display")

        # Main application container (hidden initially)
        mark_startup_milestone("creating_main_interface")
        with gr.Column(visible=False) as main_section:
            gr.Markdown("# 🎉 Welcome to NYP FYP Chatbot!")

            # User info and logout
            with gr.Row():
                user_info = gr.Markdown("", elem_id="user_info")

            # Import and use the change password interface
            from gradio_modules.change_password import change_password_interface

            # Corrected unpacking for change_password_interface (3 components)
            change_password_btn, change_password_popup, last_change_time = (
                change_password_interface(username_state, logged_in_state)
            )

            # Main app content (tabs) in a container for easy show/hide
            main_content_container = gr.Column(visible=True)
            with main_content_container:
                mark_startup_milestone("creating_tabbed_interface")
                with gr.Tabs():  # Added name for tabs to control visibility
                    # Chat Tab
                    with gr.TabItem("💬 Chat", id="chat_tab") as chat_tab_item:
                        with gr.Column():
                            try:
                                from gradio_modules.chat_interface import (  # Corrected import from chatbot to chat_interface
                                    chat_interface_ui,
                                    load_all_chats,  # Still need load_all_chats
                                )

                                # Corrected unpacking for chat_interface_ui (11 components now)
                                (
                                    chat_selector,
                                    chatbot,
                                    msg,
                                    send_btn,
                                    rename_input,
                                    rename_btn,
                                    rename_status_md,
                                    search_box,
                                    search_btn_from_interface,
                                    search_results_md,
                                    new_chat_btn,  # Added new_chat_btn
                                ) = chat_interface_ui(  # Passed debug_info_state
                                    username_state,
                                    chat_id_state,
                                    chat_history_state,
                                    all_chats_data_state,
                                    debug_info_state,
                                )

                                # Link debug_info_state to the debug_md in chatbot_ui (if it exists)
                                # The chat_interface_ui does not return debug_md directly, it uses debug_info_state
                                # So, this link is not needed here.

                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **Chatbot interface not available:** {e}"
                                )
                                gr.Markdown("Using basic fallback interface.")
                                gr.Textbox(
                                    label="Message",
                                    placeholder="Type your message here...",
                                )
                                gr.Button("Send", variant="primary")
                                gr.Textbox(label="Response", interactive=False)

                    # Document Ingestion Tab
                    with gr.TabItem(
                        "📁 Document Ingestion", id="document_ingestion_tab"
                    ):
                        with gr.Column():
                            try:
                                from gradio_modules.document_ingestion import (
                                    document_ingestion_ui,
                                )

                                document_ingestion_ui(
                                    logged_in_state, username_state, user_role_state
                                )
                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **Document Ingestion interface not available:** {e}"
                                )
                                gr.Markdown(
                                    "Please check the gradio_modules.document_ingestion module."
                                )

                    # Classification Tab (Assuming this exists based on the previous error context)
                    with gr.TabItem(
                        "🔍 Classification", id="classification_tab"
                    ) as classification_tab_item:
                        with gr.Column():
                            try:
                                from gradio_modules.file_classification import (
                                    file_classification_interface as classification_interface,
                                    setup_file_classification_events,
                                )

                                file_components_tuple = classification_interface(
                                    username_state
                                )
                                (
                                    file_upload,
                                    upload_btn,
                                    file_status_md,
                                    results_box,
                                    classification_result,
                                    sensitivity_result,
                                    file_info,
                                    reasoning_result,
                                    summary_result,
                                    file_history_md,
                                    refresh_file_history_btn,
                                    file_dropdown,
                                    refresh_files_dropdown_btn,
                                    classify_existing_btn,
                                    file_loading_indicator,
                                    clear_files_btn,
                                    clear_files_status,
                                ) = file_components_tuple

                                # Set up event handlers for file classification
                                setup_file_classification_events(
                                    file_components_tuple,
                                    username_state,
                                )

                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **Classification interface not available:** {e}"
                                )
                                gr.Markdown(
                                    "Please check the gradio_modules.classification_interface module."
                                )

                    # Audio Tab (Assuming this exists based on the previous error context)
                    with gr.TabItem("🎤 Audio", id="audio_tab") as audio_tab_item:
                        with gr.Column():
                            try:
                                from gradio_modules.audio_input import (
                                    audio_interface,
                                )

                                audio_interface(username_state)
                            except ImportError as e:
                                gr.Markdown(f"⚠️ **Audio interface not available:** {e}")
                                gr.Markdown(
                                    "Please check the gradio_modules.audio_interface module."
                                )

            # By default, show tabbed interface, hide change password button initially
            main_content_container.visible = True
            change_password_btn.visible = False

        # Backend status indicator
        with gr.Row():
            backend_status = gr.Markdown(
                "🔄 **Backend Status:** Checking...", visible=False
            )
            refresh_status_btn = gr.Button(
                "🔄 Refresh Status", size="sm", visible=False
            )

        # Event Handlers for Auth and Tab Visibility
        # This logic for showing/hiding tabs and updating status is now triggered by the app's global logged_in_state
        logged_in_state.change(
            fn=lambda logged_in: [
                gr.update(interactive=logged_in),  # Chatbot tab
                gr.update(interactive=logged_in),  # Audio Input tab
                gr.update(interactive=logged_in),  # File Classification tab
                gr.update(visible=logged_in),  # Logout button visibility
                gr.update(visible=logged_in),  # Username display visibility
                gr.update(
                    visible=not logged_in
                ),  # Login status message visibility when logged out
                gr.update(visible=logged_in),  # Backend status markdown visibility
                gr.update(visible=logged_in),  # Refresh status button visibility
                gr.update(visible=logged_in),  # Change password button visibility
            ],
            inputs=[logged_in_state],
            outputs=[
                chat_tab_item,
                audio_tab_item,
                classification_tab_item,
                logout_button,
                username_display,
                login_status_message,
                backend_status,
                refresh_status_btn,
                change_password_btn,
            ],
            queue=False,
        ).then(
            fn=lambda logged_in, username: (
                f"Welcome, {username}!" if logged_in else "Please log in to continue."
            ),
            inputs=[logged_in_state, username_state],
            outputs=[login_status_message],
            queue=False,
        ).then(
            fn=lambda logged_in, username: (
                f"Logged in as: **{username}**" if logged_in else ""
            ),
            inputs=[logged_in_state, username_state],
            outputs=[username_display],
            queue=False,
        ).then(
            fn=load_all_chats,
            inputs=[username_state],
            outputs=[all_chats_data_state],
        ).then(
            fn=lambda all_data: gr.update(
                choices=[(v["name"], k) for k, v in all_data.items()]
            ),
            inputs=[all_chats_data_state],
            outputs=[chat_selector],
        )

        # Logout event: Clears username, hides tabs, clears chats
        logout_button.click(
            fn=lambda: [
                "",
                False,
                {},
                [],
                "",
                "guest",
            ],  # Clear username, logged_in_state, all_chats_data_state, chat_history_state, chat_id_state, user_role_state
            outputs=[
                username_state,
                logged_in_state,
                all_chats_data_state,
                chat_history_state,
                chat_id_state,
                user_role_state,
            ],
            queue=False,
        ).then(
            fn=lambda: gr.update(choices=[], value=""),  # Clear chat selector dropdown
            outputs=[chat_selector],
            queue=False,
        ).then(
            fn=lambda: gr.update(value=[]),  # Clear chatbot display
            outputs=[chatbot],
            queue=False,
        )

        def handle_password_change_logout(
            logged_in: bool, username: str, user_role: str
        ) -> Tuple[
            bool,
            str,
            str,
            gr.Column,
            gr.Column,
            str,
            gr.Markdown,
            gr.Button,
            gr.Button,
            gr.Dropdown,  # chat_selector
            gr.Chatbot,  # chatbot
            gr.State,  # chat_id_state
            gr.State,  # chat_history_state
            gr.State,  # all_chats_data_state
        ]:
            """
            Handles logout triggered by successful password change.

            :param logged_in: True if the user is logged in, False otherwise.
            :type logged_in: bool
            :param username: The username of the logged-in user.
            :type username: str
            :param user_role: The role of the logged-in user.
            :type user_role: str
            :return: A tuple of Gradio updates to reset states and UI components.
            :rtype: Tuple[...]
            """
            if not logged_in:  # Password change was successful and logged out
                # Perform the same actions as a regular logout
                return (
                    False,  # logged_in_state
                    "",  # username_state
                    "guest",  # user_role_state reset to guest
                    gr.update(visible=True),  # Show login section
                    gr.update(visible=False),  # Hide main section
                    "",  # Clear user info
                    gr.update(visible=False),  # Hide backend status
                    gr.update(visible=False),  # Hide refresh button
                    gr.update(visible=False),  # Hide change password button
                    gr.update(choices=[], value=""),  # Clear chat selector
                    gr.update(value=[]),  # Clear chatbot
                    "",  # chat_id_state
                    [],  # chat_history_state
                    {},  # all_chats_data_state
                )
            # If still logged in, return current state (no changes)
            return (
                logged_in,
                username,
                user_role,
                gr.update(),  # login_section
                gr.update(),  # main_section
                gr.update(),  # user_info
                gr.update(),  # backend_status
                gr.update(),  # refresh_status_btn
                gr.update(),  # change_password_btn
                gr.update(),  # chat_selector
                gr.update(),  # chatbot
                gr.update(),  # chat_id_state
                gr.update(),  # chat_history_state
                gr.update(),  # all_chats_data_state
            )

        # Monitor logged_in_state for password change logout
        logged_in_state.change(
            fn=handle_password_change_logout,
            inputs=[
                logged_in_state,
                username_state,
                user_role_state,
            ],
            outputs=[
                logged_in_state,
                username_state,
                user_role_state,
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,
                change_password_btn,
                chat_selector,  # Added to outputs
                chatbot,  # Added to outputs
                chat_id_state,  # Added to outputs
                chat_history_state,  # Added to outputs
                all_chats_data_state,  # Added to outputs
            ],
        )

        def check_backend_status() -> gr.Markdown:
            """
            Checks the current backend initialization status and returns a formatted message.

            :return: Gradio Markdown update with the backend status.
            :rtype: gr.Markdown
            """
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

        def start_backend_and_wait_for_completion() -> Tuple[gr.Column, gr.Column, str]:
            """
            Starts backend initialization in the background and waits for it to complete
            before showing the login interface.

            :return: A tuple of Gradio updates to show/hide sections and update status.
            :rtype: Tuple[gr.Column, gr.Column, str]
            """
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
                    # Backend is ready, initialize LLM and DB for UI context
                    try:
                        from llm.chatModel import initialize_llm_and_db

                        initialize_llm_and_db()
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize LLM and DB in UI: {e}")
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

        def proceed_anyway() -> Tuple[gr.Column, gr.Column, str]:
            """
            Allows users to proceed to login even if backend isn't ready.

            :return: A tuple of Gradio updates to show/hide sections and update status.
            :rtype: Tuple[gr.Column, gr.Column, str]
            """
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
