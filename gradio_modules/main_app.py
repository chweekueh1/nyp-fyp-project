# gradio_modules/main_app.py
import gradio as gr
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import tz
from dateutil.parser import parse as dateutil_parse
from collections import defaultdict
import json
import os
import sys
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Path setup for module imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import necessary local modules directly
import backend # Expects backend.ask_question(user_message, chat_history_for_backend, username) to exist
import hashing 
import utils 

# --- Configuration (Copied from your login.py example) ---
load_dotenv() 

USER_DB_PATH = os.path.join(utils.get_chatbot_dir(), os.getenv('USER_DB_PATH', r'data\user_info\users.json'))
CHAT_SESSIONS_PATH = os.path.join(utils.get_chatbot_dir(), os.getenv('CHAT_SESSIONS_PATH', r'data\chat_sessions'))

# Ensure base directories exist for local file backend
os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)


UTC_PLUS_8 = tz.tzoffset("UTC+8", timedelta(hours=8))

ALLOWED_EMAILS = [
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

# --- Helper Functions for User/Chat Data Management ---

def get_datetime_from_timestamp(ts_string: str) -> datetime:
    fallback_dt = datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8)
    if not isinstance(ts_string, str) or not ts_string:
        return fallback_dt
    try:
        dt_obj = dateutil_parse(ts_string)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(UTC_PLUS_8)
    except ValueError as e:
        logging.warning(f"Warning: Could not parse timestamp '{ts_string}' using dateutil.parser.parse. Error: {e}. Using timezone-aware datetime.min as fallback for sorting/display.")
        return fallback_dt

def ensure_user_db_exists_sync():
    """Ensures the user database file and its directory exist."""
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": {}}, f, indent=2)
        logging.info(f"Created new user DB at: {USER_DB_PATH}")

def load_users_sync() -> dict:
    """
    Loads user data from the JSON database.
    Handles the {"users": {...}} format.
    """
    if not os.path.exists(USER_DB_PATH):
        ensure_user_db_exists_sync()
        return {"users": {}}
    try:
        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
        if "users" not in data or not isinstance(data["users"], dict):
            logging.warning("Warning: users.json format unexpected. Reinitializing.")
            ensure_user_db_exists_sync()
            return {"users": {}}
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding users.json: {e}. File might be corrupted. Reinitializing.")
        ensure_user_db_exists_sync()
        return {"users": {}}
    except Exception as e:
        logging.error(f"Unexpected error loading users.json: {e}. Reinitializing.")
        ensure_user_db_exists_sync()
        return {"users": {}}

def save_users_sync(users_data: dict) -> None:
    """
    Saves user data to the JSON database.
    Expects and saves the {"users": {...}} format.
    """
    try:
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        with open(USER_DB_PATH, 'w') as f:
            json.dump(users_data, f, indent=2)
        logging.info(f"User data saved to: {USER_DB_PATH}")
    except Exception as e:
        logging.error(f"Error saving users.json: {e}")

def load_chat_filenames_for_user(username: str) -> list[str]:
    """
    Loads all chat history filenames for a given user.
    """
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    os.makedirs(user_folder, exist_ok=True) # Ensure folder exists on load
    
    chat_filenames = [f for f in os.listdir(user_folder) if os.path.isfile(os.path.join(user_folder, f)) and f.endswith(".json")]
    
    logging.info(f"Found {len(chat_filenames)} chat filenames for user: {username}")
    return chat_filenames

def load_raw_chat_history_from_file(username: str, chat_id: str) -> list[dict]:
    """
    Loads a specific chat history by its ID from file in its raw list[dict] format.
    """
    chat_file_path = os.path.join(CHAT_SESSIONS_PATH, username, f"{chat_id}.json")
    if not os.path.exists(chat_file_path):
        logging.warning(f"Chat file not found: {chat_file_path}. Returning empty raw history.")
        return [] 
    try:
        with open(chat_file_path, 'r') as f:
            history = json.load(f)
            if not isinstance(history, list) or not all(isinstance(item, dict) and "role" in item and "content" in item for item in history):
                logging.error(f"Invalid raw chat history format in {chat_file_path}. Expected list of dicts with 'role' and 'content'. Returning empty.")
                return []
            return history
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding raw chat file {chat_file_path}: {e}. Returning empty history.")
        return [] 
    except Exception as e:
        logging.error(f"Unexpected error loading raw chat file {chat_file_path}: {e}. Returning empty history.")
        return []

def save_raw_chat_history_to_file(username: str, chat_id: str, chat_history_raw: list[dict]) -> None:
    """Saves a raw chat history (list[dict]) to its file."""
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    os.makedirs(user_folder, exist_ok=True) 
    chat_file_path = os.path.join(user_folder, f"{chat_id}.json")
    try:
        with open(chat_file_path, 'w') as f:
            json.dump(chat_history_raw, f, indent=2)
        logging.info(f"Raw chat history saved to: {chat_file_path}")
    except Exception as e:
        logging.error(f"Error saving raw chat history to {chat_file_path}: {e}")

# --- Chat History Format Conversion Functions ---

def convert_raw_to_chatbot_format(raw_history: list[dict]) -> list[list[str, str]]:
    """Converts a raw chat history (list of dicts) to Gradio Chatbot format (list of lists)."""
    chatbot_history = []
    
    current_user_message = None
    for msg in raw_history:
        if msg["role"] == "user":
            # If there's an unmatched user message from previous iteration, add it before new user message
            if current_user_message is not None:
                chatbot_history.append([current_user_message, None])
            current_user_message = msg["content"]
        elif msg["role"] == "assistant":
            if current_user_message is not None:
                # Pair with the pending user message
                chatbot_history.append([current_user_message, msg["content"]])
                current_user_message = None # Reset after pairing
            else:
                # If assistant message without preceding user message, append as standalone bot message (rare, but handle)
                chatbot_history.append([None, msg["content"]])
    
    # After loop, if a user message is still pending, add it
    if current_user_message is not None:
        chatbot_history.append([current_user_message, None])
        
    return chatbot_history

def convert_chatbot_to_raw_format(chatbot_history: list[list[str, str]], chat_id: str) -> list[dict]:
    """
    Converts Gradio Chatbot format (list of lists) to raw chat history (list of dicts).
    Assigns current timestamp and given chat_id to new messages.
    """
    raw_history = []
    for user_msg, bot_msg in chatbot_history:
        # We need to determine if this is a new message or an existing one being re-saved.
        # For simplicity, we assign new timestamps. A more robust solution might
        # preserve original timestamps if loading from file. For new messages being sent,
        # new timestamps are correct.
        
        if user_msg is not None:
            raw_history.append({
                "role": "user",
                "content": user_msg,
                "timestamp": datetime.now(UTC_PLUS_8).isoformat(), # New timestamp for saving
                "chat_id": chat_id
            })
        if bot_msg is not None:
            raw_history.append({
                "role": "assistant",
                "content": bot_msg,
                "timestamp": datetime.now(UTC_PLUS_8).isoformat(), # New timestamp for saving
                "chat_id": chat_id
            })
    return raw_history


# --- Main Application Block (gr.Blocks) ---
if __name__ == "__main__":
    # Environment variables are already loaded at the top.
    
    with gr.Blocks(title="NYP AI Chatbot Helper - Landing Page", css="../styles/styles.css") as demo_app:
        # --- 1. State Variables ---
        logged_in_state = gr.State(True) 
        username_state = gr.State("test") # Default user is "test"
        current_page_state = gr.State("landing_page") 
        current_chat_id_state = gr.State(None) # Stores the ID of the currently active chat
        
        # This proxy textbox is hidden and used to trigger a Gradio event from JavaScript clicks on chat list items
        selected_chat_id_proxy = gr.Textbox(
            label="Selected Chat ID Proxy", 
            visible=False, 
            elem_id="selected_chat_id_proxy_textbox" # IMPORTANT for JS targeting
        )

        app_data_state = gr.State(value={}) # Placeholder for any future dynamic, serializable data

        # --- 2. UI Components (All defined directly within gr.Blocks) ---
        main_app_container_comp = gr.Column(visible=True, elem_classes="main-app-container")

        # Header components
        user_info_md_comp = gr.Markdown("")
        logout_button_comp = gr.Button("Logout")

        # Left Sidebar elements: Navigation and Chat History List
        sidebar_nav_group = gr.Column(scale=1, min_width=250, elem_classes="left-sidebar")
        chat_nav_btn = gr.Button("💬 Chatbot", elem_classes="nav-button")
        search_nav_btn = gr.Button("🔍 Search Chats", elem_classes="nav-button") # NEW search button
        about_nav_btn = gr.Button("ℹ️ About", elem_classes="nav-button")
        chat_list_html = gr.HTML("Loading chats...", elem_classes="chat-list-area") 

        # Right Content Area: Pages for dynamic content
        content_pages_group = gr.Column(scale=4, elem_classes="right-content-area")
        landing_page_group = gr.Group(visible=False, elem_classes="content-page-group")
        chatbot_page_group = gr.Group(visible=False, elem_classes="content-page-group")
        search_page_group = gr.Group(visible=False, elem_classes="content-page-group") # NEW search group
        about_page_group = gr.Group(visible=False, elem_classes="content-page-group")

        # Chatbot specific UI components
        chatbot_gr_instance_comp = gr.Chatbot(visible=False, type='messages', height=400, elem_classes="main-chatbot-display")
        chat_input_textbox = gr.Textbox(placeholder="Type your message here...", label="Your Message", scale=7)
        send_message_button = gr.Button("Send", scale=1)
        
        # Search page specific UI components
        search_query_textbox = gr.Textbox(label="Search Query", placeholder="Enter keywords to search chat history...", visible=False)
        search_button = gr.Button("Search", visible=False)
        search_results_chatbot = gr.Chatbot(label="Search Results", height=400, visible=False, elem_classes="search-results-chatbot")


        # Audio Output (managed by backend.ask_question if it returns audio)
        audio_output_comp = gr.Audio(
            label="Audio Output", type="filepath", autoplay=False,
            waveform_options={"waveform_progress_color": "green", "waveform_color": "blue"},
            visible=False, elem_id="main_audio_output"
        )


        # --- 3. UI Layout (defines the static structure using instantiated components) ---

        with main_app_container_comp:
            with gr.Row(elem_classes="main-app-header"):
                user_info_md_comp
                gr.Markdown("# NYP AI Chatbot Helper") # Changed title slightly for main app
                logout_button_comp

            # Main content area row: Left Sidebar (Navigation + Chat List) and Right Content Area
            with gr.Row(elem_classes="app-content-area"):
                # Left Sidebar Column (fixed navigation and chat list)
                with sidebar_nav_group:
                    gr.Markdown("## Main Features", elem_classes="sidebar-section-title")
                    chat_nav_btn
                    search_nav_btn # NEW search button in sidebar
                    gr.Markdown("---", elem_classes="sidebar-separator")
                    gr.Markdown("### Application Info", elem_classes="sidebar-section-title")
                    about_nav_btn
                    gr.Markdown("---", elem_classes="sidebar-separator")
                    gr.Markdown("### Your Chat Sessions", elem_classes="sidebar-section-title")
                    chat_list_html # Chat history displays here
                    selected_chat_id_proxy 

                # Right Content Area Column (dynamic pages)
                with content_pages_group:
                    with landing_page_group: # This group contains the landing page content
                        gr.Markdown("## Welcome to the NYP AI Chatbot Helper!", elem_classes="page-title")
                        gr.Markdown("""
                        This application is designed to assist you with inquiries related to **NYP CNC and data security**.
                        
                        **How to Use:**
                        1. Click on the '💬 Chatbot' button in the left sidebar to start a new conversation or select an existing chat session from the list below.
                        2. Type your questions into the chat input field and press Enter or click 'Send'.
                        3. The AI will respond with relevant information.
                        
                        Feel free to explore the different sections of the application!
                        """)
                    
                    with chatbot_page_group: # This group contains the chatbot UI
                        gr.Markdown("## Chatbot Page", elem_classes="page-title")
                        chatbot_gr_instance_comp
                        with gr.Row():
                            chat_input_textbox
                            send_message_button
                        gr.Button("Back to Home", elem_classes="back-button").click(lambda: "landing_page", outputs=current_page_state, queue=False)
                    
                    with search_page_group: # NEW search page UI
                        gr.Markdown("## Search Chat History", elem_classes="page-title")
                        with gr.Row():
                            search_query_textbox
                            search_button
                        search_results_chatbot
                        gr.Button("Back to Home", elem_classes="back-button").click(lambda: "landing_page", outputs=current_page_state, queue=False)

                    with about_page_group: # This group contains the about page content
                        gr.Markdown("## About This Software", elem_classes="page-title")
                        gr.Markdown("""
                        **Version:** 1.0.0
                        **Developed by:** Your Team Name
                        **Purpose:** To provide AI-powered assistance for questions concerning NYP's Computer Networking & Cyber Security (CNC) curriculum and general data security topics.
                        
                        This application leverages advanced language models (via the `backend` module) to understand your queries and provide accurate, contextually relevant responses.
                        
                        **Technologies Used:**
                        * Gradio: For building the interactive web interface.
                        * Python: The core programming language.
                        * Local File System: For user authentication and chat history persistence.
                        * LangChain (managed by `backend` module): For integrating and orchestrating large language models.
                        
                        For more information or support, please contact your administrator.
                        """)
                        gr.Button("Back to Home", elem_classes="back-button").click(lambda: "landing_page", outputs=current_page_state, queue=False)
            
            # Place audio component at the bottom of the main app container
            audio_output_comp


        # --- 4. Core Logic Functions (Handlers) ---

        def generate_chat_list_html_content_for_display(username: str) -> str:
            """
            Generates HTML for the chat session list for display in the sidebar.
            Each chat item is a clickable div that updates a hidden textbox via JS.
            Includes a preview of the chat content.
            """
            logging.info(f"Generating chat list HTML for user: {username}")
            
            chat_filenames = load_chat_filenames_for_user(username) 

            if not chat_filenames:
                return "<p class='no-chats-message'>No chat sessions found.</p>"

            html_list = "<div class='chat-session-list-container'>"
            # Sort chats, e.g., by modification time or a timestamp within the chat file if available
            # For simplicity, sorting by filename for now.
            for filename in sorted(chat_filenames): 
                chat_id = filename.replace(".json", "") 
                chat_name = filename.replace(".json", "").replace("_", " ").title() 
                
                # Load a small preview of the chat content
                raw_history = load_raw_chat_history_from_file(username, chat_id)
                preview_text = "Empty chat."
                if raw_history:
                    # Find the first user message for a preview
                    first_user_msg = next((msg["content"] for msg in raw_history if msg["role"] == "user"), None)
                    if first_user_msg:
                        preview_text = first_user_msg[:50] + ("..." if len(first_user_msg) > 50 else "")
                    else:
                        # If no user message, take first assistant message
                        first_assistant_msg = next((msg["content"] for msg in raw_history if msg["role"] == "assistant"), None)
                        if first_assistant_msg:
                            preview_text = first_assistant_msg[:50] + ("..." if len(first_assistant_msg) > 50 else "")
                
                # JavaScript to update the hidden textbox value and trigger its change event
                js_onclick = f"document.getElementById('selected_chat_id_proxy_textbox').value='{chat_id}'; document.getElementById('selected_chat_id_proxy_textbox').dispatchEvent(new Event('change'));"
                
                html_list += f"""
                <div class='chat-session-item' data-chat-id='{chat_id}' onclick='{js_onclick}'>
                    <div class='chat-session-name'>{chat_name}</div>
                    <div class='chat-session-preview'>{preview_text}</div>
                </div>
                """
            html_list += "</div>"
            logging.info(f"Generated HTML for {len(chat_filenames)} chats.")
            return html_list

        def load_selected_chat_messages(username: str, chat_id: str) -> tuple[list, str, str]:
            """
            Loads the chat history for the selected chat ID, updates the chatbot.
            Also sets the current_chat_id_state and returns the page to switch to ('chatbot').
            """
            if not chat_id:
                logging.info("No chat ID provided to load_selected_chat_messages. Clearing chatbot.")
                return [], None, "landing_page" # Clear chatbot, no current chat, go to landing page

            logging.info(f"Loading messages for chat ID: {chat_id} for user: {username}")
            raw_history = load_raw_chat_history_from_file(username, chat_id)
            chatbot_history = convert_raw_to_chatbot_format(raw_history)
            logging.info(f"Loaded {len(raw_history)} raw messages, converted to {len(chatbot_history)} pairs for Chatbot display for chat ID: {chat_id}")
            
            # Return the history for the chatbot, the chat_id for state update, and the target page
            return chatbot_history, chat_id, "chatbot" 

        async def send_chat_message(
            user_message: str, 
            current_chatbot_history: list[list[str, str]], # This is the history from gr.Chatbot
            username: str, 
            current_chat_id: str
        ) -> tuple[list, str, str, gr.Audio]:
            """
            Handles sending a new message, updating chat history, and calling the actual backend.
            """
            if not user_message.strip():
                return current_chatbot_history, "", gr.skip(), gr.update(value=None, visible=False) 

            # If no chat is selected, create a new one based on current timestamp
            if not current_chat_id:
                current_chat_id = f"chat_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"
                logging.info(f"No current chat selected. Creating new chat with ID: {current_chat_id}")

            logging.info(f"User '{username}' sending message to chat '{current_chat_id}': {user_message}")

            # Append user message to current Gradio chatbot history format
            current_chatbot_history.append([user_message, None]) 

            # Prepare history for backend (backend.ask_question typically expects list[list[str, str]])
            history_for_backend = current_chatbot_history 

            bot_response_text = "Error: Backend call failed."
            audio_file_path = None

            try:
                # Call the actual backend.ask_question function
                bot_response_text, audio_file_path = await asyncio.to_thread(
                    backend.ask_question, user_message, history_for_backend, username
                )
                logging.info(f"Backend responded with text: {bot_response_text[:50]}...")
                if audio_file_path:
                    logging.info(f"Backend also provided audio at: {audio_file_path}")

            except AttributeError:
                logging.error(f"backend.ask_question not found or callable. Ensure backend.py defines this function.", exc_info=True)
                bot_response_text = "Error: Backend function `ask_question` not found. Please check `backend.py`."
            except Exception as e:
                logging.error(f"Error calling backend.ask_question: {e}", exc_info=True)
                bot_response_text = "Sorry, I encountered an error communicating with the backend."
                gr.Error("Error communicating with the backend. Please try again.")

            # Update bot response in current Gradio chatbot history format
            current_chatbot_history[-1][1] = bot_response_text

            # Convert the current Gradio chatbot history back to raw format for saving
            raw_history_to_save = convert_chatbot_to_raw_format(current_chatbot_history, current_chat_id)
            save_raw_chat_history_to_file(username, current_chat_id, raw_history_to_save)
            
            # Re-generate sidebar content to reflect any new chat (if current_chat_id was newly generated)
            updated_chat_list_html = generate_chat_list_html_content_for_display(username)

            return (
                current_chatbot_history, # Updated history for chatbot display
                "", # Clear the input textbox
                updated_chat_list_html, # Updated chat list for sidebar
                gr.update(value=audio_file_path, visible=bool(audio_file_path)) # Audio update
            )
        
        def perform_chat_search(username: str, query: str) -> list[list[str, str]]:
            """
            Searches through all chat histories for the given username and query.
            Returns matching message pairs in Gradio Chatbot format.
            """
            if not query.strip():
                return [] # Return empty if no query

            logging.info(f"Performing search for user '{username}' with query: '{query}'")
            search_results = []
            lower_query = query.lower()

            chat_filenames = load_chat_filenames_for_user(username)
            
            for filename in sorted(chat_filenames):
                chat_id = filename.replace(".json", "")
                raw_history = load_raw_chat_history_from_file(username, chat_id)
                chatbot_history = convert_raw_to_chatbot_format(raw_history)

                for user_msg, bot_msg in chatbot_history:
                    match_found = False
                    if user_msg and lower_query in user_msg.lower():
                        match_found = True
                    if bot_msg and lower_query in bot_msg.lower():
                        match_found = True
                    
                    if match_found:
                        # Append the entire message pair if a match is found in either part
                        search_results.append([user_msg, bot_msg])
            
            logging.info(f"Found {len(search_results)} matching message pairs for query: '{query}'")
            return search_results


        def update_ui_visibility(current_page_val: str, is_logged_in_val: bool, username_val: str, current_chat_id_val: str):
            """
            Takes the current app state values and returns UI updates.
            """
            logging.info(f"Updating UI visibility: page='{current_page_val}', logged_in={is_logged_in_val}, user='{username_val}', current_chat='{current_chat_id_val}'")
            
            main_app_visible = is_logged_in_val and bool(username_val)

            landing_visible = False
            chatbot_visible = False
            search_visible = False # NEW search page visibility
            about_visible = False

            if main_app_visible: 
                if current_page_val == "landing_page":
                    landing_visible = True
                elif current_page_val == "chatbot":
                    chatbot_visible = True
                elif current_page_val == "search_page": # NEW search page condition
                    search_visible = True
                elif current_page_val == "about_page":
                    about_visible = True
            
            chat_list_html_content = generate_chat_list_html_content_for_display(username_val)

            actual_chatbot_ui_visible = chatbot_visible 
            chatbot_history_update = gr.skip() 

            if not actual_chatbot_ui_visible: 
                chatbot_history_update = [] 
            
            actual_audio_visible = actual_chatbot_ui_visible

            return (
                gr.update(visible=main_app_visible),         # main_app_container_comp
                gr.update(visible=landing_visible),          # landing_page_group
                gr.update(visible=chatbot_visible),          # chatbot_page_group (parent group visibility)
                gr.update(visible=search_visible),           # NEW search_page_group visibility
                gr.update(visible=about_visible),            # about_page_group
                gr.update(value=f"**Logged in as:** {username_val}", visible=main_app_visible), # user_info_md_comp
                gr.update(visible=main_app_visible),         # logout_button_comp
                gr.update(value=chat_list_html_content),     # chat_list_html (update content)
                gr.update(visible=actual_chatbot_ui_visible, value=chatbot_history_update), # chatbot_gr_instance_comp
                gr.update(visible=actual_chatbot_ui_visible),  # chat_input_textbox
                gr.update(visible=actual_chatbot_ui_visible),  # send_message_button
                gr.update(visible=search_visible),           # NEW search_query_textbox visible
                gr.update(visible=search_visible),           # NEW search_button visible
                gr.update(visible=search_visible, value=[] if not search_visible else gr.skip()), # NEW search_results_chatbot visible (clear on hide)
                gr.update(visible=actual_audio_visible, value=None) # audio_output_comp
            )

        def initial_app_setup() -> tuple[str, bool, str, dict, str]:
            """
            Runs ONCE on app load. Performs initial backend setup (user DB, etc.)
            and returns the initial values for app states.
            """
            logging.info("Performing initial app setup...")
            
            ensure_user_db_exists_sync() 
            user_data = load_users_sync() 
            
            default_test_user = "test" 
            if default_test_user not in user_data.get("users", {}):
                user_data["users"][default_test_user] = {
                    "email": "test@example.com",
                    "hashedPassword": hashing.hash_password("password123") 
                }
                save_users_sync(user_data) 
                logging.info(f"Created default test user: {default_test_user}")
            
            # Create sample chat files for the "test" user if none exists
            test_user_chat_folder = os.path.join(CHAT_SESSIONS_PATH, default_test_user)
            os.makedirs(test_user_chat_folder, exist_ok=True)
            
            sample_chat_files = {
                "welcome_chat.json": [
                    {"role": "user", "content": "Hello there!", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "welcome_chat"},
                    {"role": "assistant", "content": "Hi! Welcome to the NYP AI Chatbot Helper. How can I assist you today?", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "welcome_chat"}
                ],
                "data_security_query.json": [
                    {"role": "user", "content": "What are the common threats to data security?", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "data_security_query"},
                    {"role": "assistant", "content": "Common threats include malware, phishing, SQL injection, denial-of-service attacks, and insider threats. Protecting data requires a multi-layered approach.", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "data_security_query"}
                ],
                "nyp_cnc_info.json": [
                    {"role": "user", "content": "Tell me about the Computer Networking & Cyber Security course at NYP.", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "nyp_cnc_info"},
                    {"role": "assistant", "content": "The Diploma in Computer Networking & Cyber Security (N97) at NYP equips students with skills in network infrastructure, cloud computing, and cybersecurity operations. It's a comprehensive program designed to prepare you for the digital security landscape.", "timestamp": datetime.now(UTC_PLUS_8).isoformat(), "chat_id": "nyp_cnc_info"}
                ]
            }

            for chat_filename, content in sample_chat_files.items():
                chat_file_path = os.path.join(test_user_chat_folder, chat_filename)
                if not os.path.exists(chat_file_path):
                    with open(chat_file_path, 'w') as f:
                        json.dump(content, f, indent=2)
                    logging.info(f"Created sample chat file: {chat_filename} for user: {default_test_user}")

            load_chat_filenames_for_user(default_test_user) 

            initialized_username = default_test_user
            initial_login_status = True 

            initial_app_data = {} 
            logging.info("Initial app_data prepared. Backend modules/functions accessed directly.")

            initial_page = "landing_page" 
            initial_chat_id = None # No chat selected initially

            return initial_page, initial_login_status, initialized_username, initial_app_data, initial_chat_id

        # --- 5. Event Binding ---
        
        # --- App Load Event ---
        demo_app.load(
            fn=initial_app_setup,
            inputs=None,
            outputs=[current_page_state, logged_in_state, username_state, app_data_state, current_chat_id_state],
            queue=False
        ).success( 
            fn=update_ui_visibility,
            inputs=[current_page_state, logged_in_state, username_state, current_chat_id_state],
            outputs=[
                main_app_container_comp, 
                landing_page_group,
                chatbot_page_group,
                search_page_group, # NEW output
                about_page_group,
                user_info_md_comp,
                logout_button_comp,
                chat_list_html,     
                chatbot_gr_instance_comp,
                chat_input_textbox,
                send_message_button,
                search_query_textbox, # NEW output
                search_button, # NEW output
                search_results_chatbot, # NEW output
                audio_output_comp
            ],
            queue=False
        )

        # --- Dynamic UI Updates (triggered by state changes) ---
        ui_update_outputs = [
            main_app_container_comp, 
            landing_page_group,
            chatbot_page_group,
            search_page_group, # NEW output
            about_page_group,
            user_info_md_comp,
            logout_button_comp,
            chat_list_html,     
            chatbot_gr_instance_comp,
            chat_input_textbox,
            send_message_button,
            search_query_textbox, # NEW output
            search_button, # NEW output
            search_results_chatbot, # NEW output
            audio_output_comp
        ]
        
        ui_update_inputs = [
            current_page_state, 
            logged_in_state, 
            username_state,
            current_chat_id_state
        ]

        current_page_state.change(
            fn=update_ui_visibility,
            inputs=ui_update_inputs,
            outputs=ui_update_outputs,
            queue=False
        )
        
        logged_in_state.change(
            fn=update_ui_visibility,
            inputs=ui_update_inputs,
            outputs=ui_update_outputs,
            queue=False
        )
        
        username_state.change( 
            fn=update_ui_visibility,
            inputs=ui_update_inputs,
            outputs=ui_update_outputs,
            queue=False
        )

        current_chat_id_state.change( 
            fn=update_ui_visibility,
            inputs=ui_update_inputs,
            outputs=ui_update_outputs,
            queue=False
        )

        # --- Navigation Button Clicks ---
        chat_nav_btn.click(
            fn=lambda: ("chatbot", None), 
            outputs=[current_page_state, current_chat_id_state], 
            queue=False
        )
        search_nav_btn.click(lambda: "search_page", outputs=current_page_state, queue=False) # NEW nav button click
        about_nav_btn.click(lambda: "about_page", outputs=current_page_state, queue=False)
        
        # --- Chat Selection from Sidebar ---
        selected_chat_id_proxy.change(
            fn=load_selected_chat_messages,
            inputs=[username_state, selected_chat_id_proxy], 
            outputs=[chatbot_gr_instance_comp, current_chat_id_state, current_page_state], 
            queue=False 
        )

        # --- Send Message Functionality ---
        send_message_button.click(
            fn=send_chat_message,
            inputs=[
                chat_input_textbox, 
                chatbot_gr_instance_comp, 
                username_state, 
                current_chat_id_state
            ],
            outputs=[
                chatbot_gr_instance_comp, 
                chat_input_textbox,
                chat_list_html, 
                audio_output_comp
            ],
            queue=False
        )
        chat_input_textbox.submit(
            fn=send_chat_message,
            inputs=[
                chat_input_textbox, 
                chatbot_gr_instance_comp, 
                username_state, 
                current_chat_id_state
            ],
            outputs=[
                chatbot_gr_instance_comp, 
                chat_input_textbox,
                chat_list_html, 
                audio_output_comp
            ],
            queue=False
        )

        # --- Search Functionality ---
        search_button.click(
            fn=perform_chat_search,
            inputs=[username_state, search_query_textbox],
            outputs=search_results_chatbot,
            queue=False
        )
        search_query_textbox.submit( # Allow Enter key to submit search
            fn=perform_chat_search,
            inputs=[username_state, search_query_textbox],
            outputs=search_results_chatbot,
            queue=False
        )

        # --- Logout Button ---
        logout_button_comp.click(
            fn=lambda: (False, None, "landing_page", None), # Clear current chat ID on logout
            outputs=[logged_in_state, username_state, current_page_state, current_chat_id_state],
            queue=False
        )

    # Launch the Gradio app
    demo_app.launch(debug=True, share=False) 
