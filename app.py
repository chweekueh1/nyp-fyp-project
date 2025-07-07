#!/usr/bin/env python3
"""
NYP FYP Chatbot Application - Modular Interface Design

Organized with tabbed interfaces and modular components.
"""

import sys
import asyncio
from pathlib import Path
from typing import Tuple, List, Dict, Any
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
from datetime import datetime  # Import datetime for handling timestamps


# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
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
                            # Initialize chat components to None.
                            # These will be assigned if chat_interface_ui loads successfully.
                            chat_selector = None
                            chatbot = None
                            msg = None
                            send_btn = None
                            rename_input = None
                            rename_btn = None
                            rename_status_md = None
                            search_box = None
                            search_btn_from_interface = None
                            search_results_md = None
                            new_chat_btn = None
                            clear_chat_btn = None  # Added clear_chat_btn
                            clear_chat_status = None  # Added clear_chat_status
                            debug_md = None  # Added debug_md

                            try:
                                # Removed unused import: chat_interface_ui
                                from gradio_modules.chatbot import chatbot_ui

                                # Unpack components from chatbot_ui
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
                                    debug_md,  # Unpacked debug_md
                                    clear_chat_btn,  # Unpacked clear_chat_btn
                                    clear_chat_status,  # Unpacked clear_chat_status
                                    new_chat_btn,  # Unpacked new_chat_btn
                                ) = chatbot_ui(
                                    username_state,
                                    chat_id_state,
                                    chat_history_state,
                                    all_chats_data_state,
                                    debug_info_state,
                                )

                            except ImportError as e:
                                gr.Markdown(
                                    f"⚠️ **Chatbot interface not available:** {e}"
                                )
                                gr.Markdown("Using basic fallback interface.")
                                # Dummy components are not assigned to local variables here to avoid F841.
                                # They are only created if the import fails, but not used in app.py's logic.

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
                            # Initialize classification components to None.
                            # These will be assigned if file_classification_interface loads successfully.
                            file_upload = None
                            upload_btn = None
                            file_status_md = None
                            results_box = None
                            classification_result = None
                            sensitivity_result = None
                            file_info = None
                            reasoning_result = None
                            summary_result = None
                            file_history_md = None
                            refresh_file_history_btn = None
                            file_dropdown = None
                            refresh_files_dropdown_btn = None
                            classify_existing_btn = None
                            file_loading_indicator = None
                            clear_files_btn = None
                            clear_files_status = None

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
                                # No need to assign dummy components to local variables here.

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

        # --- Consolidated Login State Change Handler (Single Return for non-chat UI updates) ---
        def _handle_login_state_change_and_updates_atomic(
            logged_in: bool,
            username: str,
            user_role: str,
        ) -> Tuple[
            gr.update,  # chat_tab_item
            gr.update,  # audio_tab_item
            gr.update,  # classification_tab_item
            gr.update,  # logout_button
            gr.update,  # username_display
            gr.update,  # login_status_message
            gr.update,  # backend_status
            gr.update,  # refresh_status_btn
            gr.update,  # change_password_btn
            gr.update,  # logged_in_state
            gr.update,  # username_state
            gr.update,  # user_role_state
            gr.update,  # login_section
            gr.update,  # main_section
            gr.update,  # user_info
        ]:
            """
            Handles all non-chat UI updates based on login state changes in a single, atomic return.
            Chat-specific UI updates are handled by a separate, dedicated function.
            """
            # Initialize all updates to default (no change or hidden/disabled)
            update_chat_tab = gr.update()
            update_audio_tab = gr.update()
            update_classification_tab = gr.update()
            update_logout_btn = gr.update()
            update_username_display = gr.update()
            update_login_status_msg = gr.update()
            update_backend_status = gr.update()
            update_refresh_status_btn = gr.update()
            update_change_password_btn = gr.update()
            update_logged_in_state = gr.update()
            update_username_state = gr.update()
            update_user_role_state = gr.update()
            # Corrected: These should be gr.update objects, not the original components
            update_login_section_visibility = gr.update()
            update_main_section_visibility = gr.update()
            update_user_info_value = gr.update()

            if logged_in:
                # User logged in
                update_chat_tab = gr.update(interactive=True)
                update_audio_tab = gr.update(interactive=True)
                update_classification_tab = gr.update(interactive=True)
                update_logout_btn = gr.update(visible=True)
                update_username_display = gr.update(visible=True)
                update_login_status_msg = gr.update(visible=False)
                update_backend_status = gr.update(visible=True)
                update_refresh_status_btn = gr.update(visible=True)
                update_change_password_btn = gr.update(visible=True)

                update_login_section_visibility = gr.update(visible=False)
                update_main_section_visibility = gr.update(visible=True)
                update_user_info_value = gr.update(
                    value=f"Logged in as: **{username}**"
                )

            else:
                # User logged out (or password changed and forced logout)
                update_chat_tab = gr.update(interactive=False)
                update_audio_tab = gr.update(interactive=False)
                update_classification_tab = gr.update(interactive=False)
                update_logout_btn = gr.update(visible=False)
                update_username_display = gr.update(visible=False)
                update_login_status_msg = gr.update(
                    value="Please log in to continue.", visible=True
                )
                update_backend_status = gr.update(visible=False)
                update_refresh_status_btn = gr.update(visible=False)
                update_change_password_btn = gr.update(visible=False)

                update_login_section_visibility = gr.update(visible=True)
                update_main_section_visibility = gr.update(visible=False)
                update_user_info_value = gr.update(value="")

                update_logged_in_state = gr.update(value=False)
                update_username_state = gr.update(value="")
                update_user_role_state = gr.update(value="guest")

            return (
                update_chat_tab,
                update_audio_tab,
                update_classification_tab,
                update_logout_btn,
                update_username_display,
                update_login_status_msg,
                update_backend_status,
                update_refresh_status_btn,
                update_change_password_btn,
                update_logged_in_state,
                update_username_state,
                update_user_role_state,
                update_login_section_visibility,  # Corrected return
                update_main_section_visibility,  # Corrected return
                update_user_info_value,  # Corrected return
            )

        def _initialize_chat_states_on_login(
            logged_in: bool, username: str
        ) -> Tuple[Dict[str, Any], str]:
            """
            Initializes chat-related states upon login.
            Returns raw state values (not gr.update objects).
            """
            if logged_in and username:
                from backend.chat import ensure_chat_on_login

                initial_chat_id = ensure_chat_on_login(username)

                # all_chats_data_state will be populated by the username_state.change
                # event in chatbot_ui, which calls list_user_chat_ids.
                # chat_history_state will be populated when _load_chat_by_id is triggered
                # by the chat_selector.change event in chatbot_ui.
                return {}, initial_chat_id
            else:
                # If not logged in, clear all chat-related states
                return {}, ""

        def _update_chat_selector_on_state_change(
            all_chats_data: Dict[str, Any], chat_id: str
        ) -> gr.update:
            """
            Updates the chat_selector component when all_chats_data_state or chat_id_state changes.
            """
            updated_choices = sorted(
                [(v["name"], k) for k, v in all_chats_data.items()],
                key=lambda item: all_chats_data[item[1]].get(
                    "updated_at", datetime.min.isoformat()
                ),
                reverse=True,
            )
            selected_value_for_dropdown = (
                chat_id
                if chat_id in all_chats_data
                else (
                    updated_choices[0][1] if updated_choices else ""
                )  # Select the first chat if available
            )

            return gr.update(
                choices=updated_choices,
                value=selected_value_for_dropdown,
                interactive=bool(all_chats_data),
            )

        def _update_chatbot_on_state_change(chat_history: List[List[str]]) -> gr.update:
            """
            Updates the chatbot component when chat_history_state changes.
            """
            return gr.update(value=chat_history)

        def _enable_chat_inputs_on_login(
            logged_in: bool, all_chats_data: Dict[str, Any], chat_id: str
        ) -> Tuple[
            gr.update, gr.update, gr.update, gr.update, gr.update, gr.update, gr.update
        ]:
            """
            Enables/disables interactive chat components based on login status and chat data.
            """
            is_chat_active = logged_in and bool(
                chat_id
            )  # Chat inputs require a selected chat_id
            is_logged_in = logged_in  # New chat button only requires login

            return (
                gr.update(interactive=is_chat_active),  # msg
                gr.update(interactive=is_chat_active),  # send_btn
                gr.update(interactive=is_chat_active),  # rename_input
                gr.update(interactive=is_chat_active),  # rename_btn
                gr.update(interactive=is_chat_active),  # search_box
                gr.update(interactive=is_chat_active),  # search_btn_from_interface
                gr.update(interactive=is_logged_in),  # new_chat_btn
                gr.update(interactive=is_chat_active),  # clear_chat_btn
            )

        # --- Event Handlers for Auth and Tab Visibility (Consolidated) ---
        logged_in_state.change(
            fn=_handle_login_state_change_and_updates_atomic,
            inputs=[
                logged_in_state,
                username_state,
                user_role_state,
            ],
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
                logged_in_state,  # Update the state itself
                username_state,  # Update the state itself
                user_role_state,  # Update the state itself
                login_section,
                main_section,
                user_info,
            ],
            queue=False,
        )

        # --- Separate Event Handler for Chat State Initialization on Login Status Change ---
        logged_in_state.change(
            fn=_initialize_chat_states_on_login,
            inputs=[logged_in_state, username_state],
            outputs=[
                all_chats_data_state,
                chat_id_state,
            ],
            queue=False,
        )

        # --- Dedicated Event Handlers for Chat UI Component Updates ---
        # These are conditionally executed based on whether the components are defined
        # This check is crucial to prevent UnboundLocalError
        if chat_selector is not None:
            all_chats_data_state.change(
                fn=_update_chat_selector_on_state_change,
                inputs=[all_chats_data_state, chat_id_state],
                outputs=[chat_selector],
                queue=False,
            )
        if chatbot is not None:
            chat_history_state.change(
                fn=_update_chatbot_on_state_change,
                inputs=[chat_history_state],
                outputs=[chatbot],
                queue=False,
            )

        # --- New Event Handler to Enable/Disable Chat Inputs ---
        # This will be triggered when logged_in_state, all_chats_data_state, or chat_id_state changes
        # Only attach if all components are defined
        if all(
            c is not None
            for c in [
                msg,
                send_btn,
                rename_input,
                rename_btn,
                search_box,
                search_btn_from_interface,
                new_chat_btn,
                clear_chat_btn,
            ]
        ):
            gr.on(
                triggers=[
                    logged_in_state.change,
                    all_chats_data_state.change,
                    chat_id_state.change,
                ],
                fn=_enable_chat_inputs_on_login,
                inputs=[logged_in_state, all_chats_data_state, chat_id_state],
                outputs=[
                    msg,
                    send_btn,
                    rename_input,
                    rename_btn,
                    search_box,
                    search_btn_from_interface,
                    new_chat_btn,
                    clear_chat_btn,
                ],
                queue=False,
            )

        # Logout event: Clears username, hides tabs, clears chats
        # This now triggers the main logged_in_state.change handler
        logout_button.click(
            fn=lambda: [
                False,  # logged_in_state to False
                "",  # username_state to empty
                "guest",  # user_role_state to guest
            ],
            outputs=[
                logged_in_state,
                username_state,
                user_role_state,
            ],
            queue=False,
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
