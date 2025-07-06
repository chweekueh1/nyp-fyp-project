#!/usr/bin/env python3
"""
NYP FYP Chatbot Application - Modular Interface Design
Organized with tabbed interfaces and modular components.
"""

import sys
import asyncio
from pathlib import Path
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
    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    logger.info("LLM and embedding models initialized.")
except Exception as e:
    logger.error(f"Failed to initialize LLM or embedding: {e}")

# Initialize DuckDB vector stores
classification_db = None
chat_db = None
try:
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
            logger.info("⏳ This will initialize DuckDB vector store and AI models...")

            # Delay the import until we're ready to initialize
            # This prevents DuckDB vector store from initializing during module import
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
        backend_status_state = gr.State("initializing")
        # Initialize these states here to ensure they are always defined
        chat_history_state = gr.State([])
        selected_chat_id = gr.State("")

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

                # Corrected unpacking for login_interface (19 components)
                (
                    logged_in_state_from_login,  # This is the state returned by login_interface
                    username_state_from_login,  # This is the state returned by login_interface
                    is_register_mode,
                    main_container_login,  # Renamed to avoid conflict with main_content_container
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

        # Main application container (hidden initially)
        mark_startup_milestone("creating_main_interface")
        with gr.Column(visible=False) as main_section:
            gr.Markdown("# 🎉 Welcome to NYP FYP Chatbot!")

            # User info and logout
            with gr.Row():
                user_info = gr.Markdown("", elem_id="user_info")
                logout_btn = gr.Button("🚪 Logout", variant="secondary", size="sm")

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
                with (
                    gr.Tabs() as main_tabs
                ):  # Added name for tabs to control visibility
                    # Chat Tab
                    with gr.TabItem("💬 Chat", id="chat_tab"):
                        with gr.Column(
                            visible=False
                        ) as chat_tab_content_column:  # Content column for chat tab
                            try:
                                from gradio_modules.chatbot import (
                                    chatbot_ui,
                                )  # Assuming chatbot_ui is the main function

                                # Corrected unpacking for chatbot_ui (13 components)
                                (
                                    chat_selector,
                                    chatbot,
                                    chat_input,
                                    send_btn,
                                    search_input_chat,  # Renamed to avoid conflict with search_interface
                                    search_btn_chat,  # Renamed to avoid conflict with search_interface
                                    search_results_chat,  # Renamed to avoid conflict with search_interface
                                    rename_input,
                                    rename_btn,
                                    debug_md,
                                    clear_chat_btn,
                                    clear_chat_status,
                                    new_chat_btn,  # This was the missing one causing 12 vs 13
                                ) = chatbot_ui(
                                    username_state,
                                    chat_history_state,
                                    selected_chat_id,
                                    setup_events=True,
                                )
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

                    # Search History Tab (assuming it's a separate tab)
                    with gr.TabItem("🔍 Search History", id="search_tab"):
                        with gr.Column(
                            visible=False
                        ) as search_tab_content_column:  # Content column for search tab
                            try:
                                from gradio_modules.search_interface import (
                                    search_interface,
                                )

                                # Corrected unpacking for search_interface (4 components)
                                (
                                    search_container,
                                    search_query,
                                    search_btn_search,  # Renamed to avoid conflict with chat tab's search_btn
                                    search_results_dropdown,
                                ) = search_interface(
                                    logged_in_state,
                                    username_state,
                                    selected_chat_id,  # This is the current chat ID
                                    chat_history_state,  # This is the current chat history
                                )
                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **Search interface not available:** {e}"
                                )
                                gr.Markdown(
                                    "Please check the gradio_modules.search_interface module."
                                )
                                gr.Textbox(
                                    label="Search Query",
                                    placeholder="Enter search query...",
                                )
                                gr.Button("Search")
                                gr.Dropdown(label="Search Results", choices=[])

                    # File Classification Tab
                    with gr.TabItem("📄 File Classification", id="classification_tab"):
                        with (
                            gr.Column(
                                visible=False
                            ) as classification_tab_content_column
                        ):  # Content column for classification tab
                            try:
                                from gradio_modules.file_classification import (
                                    file_classification_interface,
                                    setup_file_classification_events,
                                )

                                components = file_classification_interface(
                                    username_state
                                )
                                # Corrected unpacking for file_classification_interface (17 components)
                                (
                                    file_upload,
                                    upload_btn,
                                    status_md,
                                    results_box,  # Corrected from results_section based on previous analysis
                                    classification_result,
                                    sensitivity_result,
                                    file_info,
                                    reasoning_result,
                                    summary_result,
                                    history_md,
                                    refresh_history_btn,
                                    file_dropdown,
                                    refresh_files_btn,
                                    classify_existing_btn,
                                    loading_indicator,
                                    clear_files_btn,
                                    clear_files_status,
                                ) = components

                                # Set up event handlers within Blocks context
                                setup_file_classification_events(
                                    components, username_state
                                )
                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **File classification interface not available:** {e}"
                                )
                                gr.Markdown(
                                    "Please check the gradio_modules.file_classification module."
                                )

                    # Audio Input Tab
                    with gr.TabItem("🎤 Audio Input", id="audio_tab"):
                        with gr.Column(
                            visible=False
                        ) as audio_tab_content_column:  # Content column for audio tab
                            try:
                                from gradio_modules.audio_input import audio_interface

                                # Corrected unpacking for audio_interface (11 components)
                                (
                                    audio_input,
                                    process_audio_btn,
                                    transcription_output,
                                    response_output,
                                    status_message,
                                    edit_transcription,
                                    edit_btn,
                                    send_edited_btn,
                                    history_output,
                                    clear_history_btn,
                                    audio_history,
                                ) = audio_interface(username_state, setup_events=True)
                            except ImportError as e:
                                gr.Markdown(f"⚠️ **Audio interface not available:** {e}")
                                gr.Markdown(
                                    "Please check the gradio_modules.audio_input module."
                                )
                                gr.Audio(label="Record Audio", type="filepath")
                                gr.Button("Process Audio", variant="primary")
                                gr.Textbox(label="Transcription", interactive=False)

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

        # Event handlers for login/logout
        def handle_login_success(logged_in, username, backend_status_state_val):
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
                    gr.update(visible=True),  # Show change password button
                    gr.update(selected=0),  # Switch to the first tab (Chat tab)
                    gr.update(visible=True),  # Show Chat Tab content
                    gr.update(visible=True),  # Show Search Tab content
                    gr.update(visible=True),  # Show File Classification Tab content
                    gr.update(visible=True),  # Show Audio Input Tab content
                )
            else:
                return (
                    gr.update(visible=True),  # Show login section
                    gr.update(visible=False),  # Hide main section
                    "",  # Clear user info
                    gr.update(visible=False),  # Hide backend status
                    gr.update(visible=False),  # Hide refresh button
                    gr.update(visible=False),  # Hide change password button
                    gr.update(selected=0),  # Switch back to login tab or default
                    gr.update(visible=False),  # Hide Chat Tab content
                    gr.update(visible=False),  # Hide Search Tab content
                    gr.update(visible=False),  # Hide File Classification Tab content
                    gr.update(visible=False),  # Hide Audio Input Tab content
                )

        # Link login state change to UI updates
        logged_in_state.change(
            fn=handle_login_success,
            inputs=[logged_in_state, username_state, backend_status_state],
            outputs=[
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,
                change_password_btn,
                main_tabs,
                chat_tab_content_column,
                search_tab_content_column,
                classification_tab_content_column,
                audio_tab_content_column,
            ],
        )

        def handle_logout():
            """Handle logout with proper state reset for dynamic login interface."""
            logger.info("User logged out")
            # Clear all relevant states and inputs
            return (
                False,  # logged_in_state
                "",  # username_state
                False,  # is_register_mode (reset to login view)
                gr.update(visible=True),  # Show login section
                gr.update(visible=False),  # Hide main section
                "",  # Clear user info
                gr.update(visible=False),  # Hide backend status
                gr.update(visible=False),  # Hide refresh button
                gr.update(visible=False),  # Hide change password button
                # Reset login/register form inputs
                "",  # username_input
                "",  # email_input
                "",  # password_input
                "",  # confirm_password_input
                gr.update(visible=False),  # error_message
                gr.update(value="## 🔐 Login"),  # header_subtitle
                gr.update(
                    value="Please log in to access the chatbot."
                ),  # header_instruction
                gr.update(visible=False),  # email_info
                gr.update(visible=False),  # password_requirements
                gr.update(visible=False),  # confirm_password_input visibility
                gr.update(visible=False),  # show_confirm_btn visibility
                gr.update(value="Login", variant="primary"),  # primary_btn
                gr.update(value="Register", variant="secondary"),  # secondary_btn
                gr.update(selected=0),  # Switch to Auth tab
                gr.update(visible=False),  # Hide Chat Tab content
                gr.update(visible=False),  # Hide Search Tab content
                gr.update(visible=False),  # Hide File Classification Tab content
                gr.update(visible=False),  # Hide Audio Input Tab content
            )

        # Wire up logout event with proper state reset for dynamic login interface
        logout_btn.click(
            fn=handle_logout,
            inputs=[],
            outputs=[
                logged_in_state,
                username_state,
                is_register_mode,
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,
                change_password_btn,
                username_input,
                email_input,
                password_input,
                confirm_password_input,
                error_message,
                header_subtitle,
                header_instruction,
                email_info,
                password_requirements,
                confirm_password_input,  # This is a component, not a state
                show_confirm_btn,  # This is a component, not a state
                primary_btn,
                secondary_btn,
                main_tabs,  # Control tab selection
                chat_tab_content_column,
                search_tab_content_column,
                classification_tab_content_column,
                audio_tab_content_column,
            ],
        )

        # Handle logout triggered by password change
        def handle_password_change_logout(logged_in, username):
            """Handle logout triggered by successful password change."""
            if not logged_in:  # Password change was successful and logged out
                return handle_logout()
            # If still logged in, return current state (no changes)
            # This return needs to match the handle_logout outputs
            return (
                logged_in,
                username,
                False,  # is_register_mode
                gr.update(),  # login_section
                gr.update(),  # main_section
                gr.update(),  # user_info
                gr.update(),  # backend_status
                gr.update(),  # refresh_status_btn
                gr.update(),  # change_password_btn
                gr.update(),  # username_input
                gr.update(),  # email_input
                gr.update(),  # password_input
                gr.update(),  # confirm_password_input
                gr.update(),  # error_message
                gr.update(),  # header_subtitle
                gr.update(),  # header_instruction
                gr.update(),  # email_info
                gr.update(),  # password_requirements
                gr.update(),  # confirm_password_input
                gr.update(),  # show_confirm_btn
                gr.update(),  # primary_btn
                gr.update(),  # secondary_btn
                gr.update(),  # main_tabs selection
                gr.update(),  # chat_tab_content_column
                gr.update(),  # search_tab_content_column
                gr.update(),  # classification_tab_content_column
                gr.update(),  # audio_tab_content_column
            )

        # Monitor logged_in_state for password change logout
        logged_in_state.change(
            fn=handle_password_change_logout,
            inputs=[logged_in_state, username_state],
            outputs=[
                logged_in_state,
                username_state,
                is_register_mode,
                login_section,
                main_section,
                user_info,
                backend_status,
                refresh_status_btn,
                change_password_btn,
                username_input,
                email_input,
                password_input,
                confirm_password_input,
                error_message,
                header_subtitle,
                header_instruction,
                email_info,
                password_requirements,
                confirm_password_input,
                show_confirm_btn,
                primary_btn,
                secondary_btn,
                main_tabs,
                chat_tab_content_column,
                search_tab_content_column,
                classification_tab_content_column,
                audio_tab_content_column,
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
