import gradio as gr
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import tz
from dateutil.parser import parse as dateutil_parse
from collections import defaultdict
import json
import os
import sys # Required for modifying sys.path
from dotenv import load_dotenv
import traceback # Import traceback for printing full stack traces

# --- ONLY FOR STANDALONE TESTING: Adjust sys.path to find parent modules ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import modules from the parent directory
import backend 
import hashing
import utils 

# --- Configuration (moved from app.py to login.py) ---
load_dotenv() 

USER_DB_PATH = os.path.join(utils.get_chatbot_dir(), os.getenv('USER_DB_PATH', r'data\user_info\users.json'))
CHAT_SESSIONS_PATH = os.path.join(utils.get_chatbot_dir(), os.getenv('CHAT_SESSIONS_PATH', r'data\chat_sessions'))

UTC_PLUS_8 = tz.tzoffset("UTC+8", timedelta(hours=8))
from_zone = tz.tzutc() 
to_zone = tz.tzlocal() 

MAX_UPLOAD_SIZE = 25 
MAX_UPLOAD_SIZE_BYTE = MAX_UPLOAD_SIZE * 1024 * 1024 

ALLOWED_EMAILS = [ 
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

# --- Helper Functions (Synchronous, for user/chat data management - moved from app.py) ---

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
        print(f"Warning: Could not parse timestamp '{ts_string}' using dateutil.parser.parse. Error: {e}. Using timezone-aware datetime.min as fallback for sorting/display.")
        return fallback_dt

def ensure_user_db_exists_sync():
    """Ensures the user database file and its directory exist."""
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": {}}, f, indent=2)

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
            print("Warning: users.json format unexpected. Reinitializing.")
            ensure_user_db_exists_sync()
            return {"users": {}} 
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding users.json: {e}. File might be corrupted. Reinitializing.")
        ensure_user_db_exists_sync()
        return {"users": {}}
    except Exception as e:
        print(f"Unexpected error loading users.json: {e}. Reinitializing.")
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
    except Exception as e:
        print(f"Error saving users.json: {e}")

def load_user_chats_sync(username: str) -> list:
    """Loads all chat histories for a given user."""
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    if not os.path.exists(user_folder):
        return []
    chat_files = [f for f in os.listdir(user_folder) if os.path.isfile(os.path.join(user_folder, f)) and f.endswith(".json")]
    chat_histories = []
    for chat_file in chat_files:
        try:
            with open(os.path.join(user_folder, chat_file), 'r') as f:
                chat_histories.append(json.load(f))
        except json.JSONDecodeError as e:
            print(f"Error reading chat file {chat_file}: {e}. Skipping this chat.")
        except Exception as e:
            print(f"Unexpected error with chat file {chat_file}: {e}. Skipping this chat.")
    return chat_histories


# --- Main login_interface function ---
def login_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
    login_container_comp: gr.Column, 
    main_app_container_comp: gr.Column, 
    user_info_md_comp: gr.Markdown, 
    logout_button_comp: gr.Button, 
    chat_list_group_comp: gr.Column, 
    chatbot_gr_instance_comp: gr.Chatbot, 
    get_chat_interface_history_func 
) -> gr.Column:

    # --- Password Visibility Toggle Helper ---
    def toggle_password_visibility(is_visible: bool):
        """
        Toggles the password textbox type and button icon based on current visibility state.
        is_visible: True if password is currently visible (type="text"), False if hidden (type="password").
        """
        new_type = "password" if is_visible else "text"
        new_icon = "👁️" if is_visible else "🙈" 
        new_is_visible = not is_visible 

        return gr.update(type=new_type), gr.update(value=new_icon), new_is_visible

    # --- Login Logic ---
    async def _process_login_logic(username_val, password_val):
        # Clear previous messages in the login message area
        login_message_update = gr.update(value="") 
        
        try:
            print(f"DEBUG: _process_login_logic - Attempting login for user: {username_val}")
            users_data = await asyncio.to_thread(load_users_sync)
            users = users_data.get("users", {}) 

            if username_val not in users:
                print(f"DEBUG: _process_login_logic - User '{username_val}' not found. Returning error.")
                gr.Error("Incorrect username or password.") # This sends the red banner
                return (gr.update(value=False), gr.update(value=None), gr.update(value=None), gr.update(value="Incorrect username or password."), 
                        gr.update(visible=True), gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False), 
                        gr.update(visible=False), gr.update(value=[]))

            elif hashing.verify_password(password_val, users[username_val]["hashedPassword"]):
                print(f"DEBUG: _process_login_logic - Password verified for user: {username_val}. Preparing success updates.")
                gr.Info("Login successful! Redirecting to main app.") # This sends the green banner
                
                new_logged_in_state = True
                new_username_state = username_val
                new_current_chat_id = 0
                initial_chatbot_history = []
                
                # --- START: Critical section for post-login data loading/formatting ---
                # try:
                #     loaded_history = await asyncio.to_thread(load_user_chats_sync, new_username_state)
                #     chat_history_state.value = loaded_history 
                #     print(f"DEBUG: _process_login_logic - Chat history loaded. Length: {len(loaded_history)}")
                    
                #     new_current_chat_id = f"{new_username_state}_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"
                #     print(f"DEBUG: _process_login_logic - New current chat ID: {new_current_chat_id}")

                #     # Ensure all old messages have a chat_id for compatibility (if any were loaded)
                #     for msg in chat_history_state.value:
                #         if 'chat_id' not in msg:
                #             msg['chat_id'] = f"{new_username_state}_legacy_chat_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"
                #             print(f"DEBUG: _process_login_logic - Assigned legacy chat_id to a message.")

                #     # This call is a common point of failure if data is unexpected
                #     initial_chatbot_history = get_chat_interface_history_func(chat_history_state.value, new_current_chat_id)
                #     print(f"DEBUG: _process_login_logic - Chatbot history formatted. Length: {len(initial_chatbot_history)}")

                # except Exception as history_error:
                #     print(f"ERROR: _process_login_logic - Error during chat history loading/formatting: {history_error}")
                #     traceback.print_exc() # Print full traceback for deeper insights
                #     gr.Error(f"Login successful, but failed to load chat history: {history_error}")
                #     # If history loading fails, we might want to prevent access to main app
                #     # Or reset states to reflect a logged-out but error state.
                #     # For now, forcing back to login screen with specific error.
                #     return (gr.update(value=False), gr.update(value=None), gr.update(value=None), gr.update(value=f"Login successful, but failed to load chat history: {history_error}"), 
                #             gr.update(visible=True), gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False), 
                #             gr.update(visible=False), gr.update(value=[]))
                # --- END: Critical section ---

                print("DEBUG: _process_login_logic - All checks and history loading successful. Returning Gradio updates for success.")
                success_login_str = f"**Logged in as:** {new_username_state}"
                print(f"DEBUG: {success_login_str}")
                return (gr.update(value=new_logged_in_state),
                        gr.update(value=new_username_state),
                        gr.update(value=new_current_chat_id),
                        gr.update(value=""), # Clear the internal login_message on success
                        gr.update(visible=False), # Hide login container
                        gr.update(visible=True), # Show main app container
                        gr.update(value=success_login_str, visible=True), # Update user info, make visible
                        gr.update(visible=True), # Show logout button
                        gr.update(visible=True), # Show chat_list_group
                        gr.update(value=initial_chatbot_history) # Update chatbot display
                       ) 
            else: # User found, but password incorrect
                print(f"DEBUG: _process_login_logic - User '{username_val}' found, but password incorrect. Returning error.")
                gr.Error("Incorrect username or password.") 
                return (gr.update(value=False), gr.update(value=None), gr.update(value=None), gr.update(value="Incorrect username or password."), 
                        gr.update(visible=True), gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False), 
                        gr.update(visible=False), gr.update(value=[]))

        except Exception as e:
            print(f"ERROR: _process_login_logic - An unexpected fatal error occurred in the main try-except: {e}. Printing traceback.")
            traceback.print_exc() # Print full traceback for unexpected errors
            gr.Error(f"An unexpected error occurred during login: {e}")
            return (gr.update(value=False), gr.update(value=None), gr.update(value=None), gr.update(value=f"An unexpected error occurred: {e}"), 
                    gr.update(visible=True), gr.update(visible=False), gr.update(value="", visible=False), gr.update(visible=False), 
                    gr.update(visible=False), gr.update(value=[]))


    # --- Register Logic ---
    async def _process_register_logic(username_val, email_val, password_val, confirm_val):
        register_message_update = gr.update(value="") # Clear previous messages
        
        try:
            if not username_val or not email_val or not password_val or not confirm_val:
                gr.Warning("Please fill all fields.")
                return gr.update(value="Please fill all fields.")
            if password_val != confirm_val:
                gr.Error("Passwords do not match.")
                return gr.update(value="Passwords do not match.")
            if email_val not in ALLOWED_EMAILS: 
                gr.Error("This email is not allowed to register.")
                return gr.update(value="This email is not allowed to register.")

            users_data = await asyncio.to_thread(load_users_sync)
            users = users_data.get("users", {}) 
            is_complex, message = hashing.is_password_complex(password_val)

            if username_val in users:
                gr.Warning("Username already exists.")
                return gr.update(value="Username already exists.")
            if any(user["email"] == email_val for user in users.values()):
                gr.Warning("This email is already registered.")
                return gr.update(value="This email is already registered.")
            if not is_complex:
                gr.Warning(message)
                return gr.update(value=message) 

            hashed_password = hash_password(password_val)
            users[username_val] = {
                "email": email_val,
                "hashedPassword": hashed_password
            }
            users_data["users"] = users 
            await asyncio.to_thread(save_users_sync, users_data)
            print(f"DEBUG: _process_register_logic - Registration successful for user: {username_val}. Calling gr.Info.")
            gr.Info("Registration successful! You can now log in.")
            return gr.update(value="Registration successful! You can now log in.")
        except Exception as e:
            print(f"ERROR: _process_register_logic - An unexpected error occurred during registration: {e}. Printing traceback.")
            traceback.print_exc()
            gr.Error(f"An unexpected error occurred during registration: {e}")
            return gr.update(value=f"An unexpected error occurred: {e}")

    # --- UI Layout for Login/Register ---
    with gr.Column(visible=True) as login_ui_container:
        gr.Markdown("<div class='main-header'>NYP AI Chatbot Helper</div>") 
        gr.Markdown("## Login / Register")
        with gr.Tabs():
            with gr.Tab("Login"):
                username_login_input = gr.Textbox(label="Username")
                
                # Password input with toggle
                with gr.Row():
                    password_login_input = gr.Textbox(label="Password", type="password", scale=8)
                    show_password_login_btn = gr.Button("👁️", scale=1, min_width=50, elem_classes="eye-button") 
                    is_password_login_visible = gr.State(False) 

                login_message = gr.Markdown()

                login_btn = gr.Button("Login", variant="primary")

                login_btn.click(
                    fn=_process_login_logic,
                    inputs=[username_login_input, password_login_input],
                    outputs=[logged_in_state, username_state, current_chat_id_state, login_message,
                             login_container_comp, main_app_container_comp, user_info_md_comp, logout_button_comp,
                             chat_list_group_comp, chatbot_gr_instance_comp
                            ],
                    queue=False
                )

                show_password_login_btn.click(
                    fn=toggle_password_visibility,
                    inputs=[is_password_login_visible], 
                    outputs=[password_login_input, show_password_login_btn, is_password_login_visible],
                    queue=False
                )

            with gr.Tab("Register"):
                username_register_input = gr.Textbox(label="New Username")
                email_register_input = gr.Textbox(label="Email Address")
                
                # New Password input with toggle
                with gr.Row():
                    password_register_input = gr.Textbox(label="New Password", type="password", scale=8)
                    show_password_register_btn = gr.Button("👁️", scale=1, min_width=50, elem_classes="eye-button")
                    is_password_register_visible = gr.State(False) 

                # Confirm Password input with toggle
                with gr.Row():
                    confirm_password_input = gr.Textbox(label="Confirm Password", type="password", scale=8)
                    show_confirm_password_btn = gr.Button("👁️", scale=1, min_width=50, elem_classes="eye-button")
                    is_confirm_password_visible = gr.State(False) 

                register_btn = gr.Button("Register", variant="primary")
                register_message = gr.Markdown()

                register_btn.click(
                    fn=_process_register_logic,
                    inputs=[username_register_input, email_register_input, password_register_input, confirm_password_input],
                    outputs=[register_message]
                )

                show_password_register_btn.click(
                    fn=toggle_password_visibility,
                    inputs=[is_password_register_visible], 
                    outputs=[password_register_input, show_password_register_btn, is_password_register_visible],
                    queue=False
                )

                show_confirm_password_btn.click(
                    fn=toggle_password_visibility,
                    inputs=[is_confirm_password_visible], 
                    outputs=[confirm_password_input, show_confirm_password_btn, is_confirm_password_visible],
                    queue=False
                )
    
    return login_ui_container


# --- Test Block for login.py (using actual backend and hashing) ---
if __name__ == "__main__":
    load_dotenv() 

    # --- Minimal Helper for get_chat_interface_history (mocked for this standalone test) ---
    def mock_get_chat_interface_history(all_chat_messages, target_chat_id):
        print(f"DEBUG: mock_get_chat_interface_history called for chat_id: {target_chat_id}")
        return [] 

    # --- Create a dummy Gradio app context for testing the login interface ---
    with gr.Blocks(title="Login Module Test App", css="""
        .main-header {color: orange; font-size: 2em; text-align: center; margin-bottom: 20px;}
        .eye-button {
            min-width: 50px !important; 
            padding: 5px; 
            font-size: 1.2em; 
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .gradio-container {
            max-width: 600px;
            margin: auto;
            padding: 20px;
        }
        .gr-row {
            align-items: center; 
        }
    """) as demo_app:
        # Global states and components (mimicking app.py's global setup)
        mock_logged_in = gr.State(False)
        mock_username = gr.State(None)
        mock_current_chat_id = gr.State(None)
        mock_chat_history_state = gr.State([])

        # Mock UI containers and components for visibility updates
        mock_login_container = gr.Column(visible=True) 
        mock_main_app_container = gr.Column(visible=False) 
        mock_user_info_md = gr.Markdown("", visible=False) 
        mock_logout_button = gr.Button("Logout", visible=False) 
        mock_chat_list_group = gr.Column(visible=False) 
        mock_chatbot_gr_instance = gr.Chatbot(visible=False) 

        # Call the login_interface function, passing actual modules and mock components
        login_ui_component_group = login_interface(
            logged_in_state=mock_logged_in,
            username_state=mock_username,
            current_chat_id_state=mock_current_chat_id,
            chat_history_state=mock_chat_history_state,
            login_container_comp=mock_login_container,
            main_app_container_comp=mock_main_app_container,
            user_info_md_comp=mock_user_info_md,
            logout_button_comp=mock_logout_button, 
            chat_list_group_comp=mock_chat_list_group, 
            chatbot_gr_instance_comp=mock_chatbot_gr_instance,
            get_chat_interface_history_func=mock_get_chat_interface_history 
        )

        # Place the returned login UI into the mock login container
        with mock_login_container:
            login_ui_component_group

        # --- Placeholder for the "Main Application" content ---
        with mock_main_app_container:
            gr.Markdown("## Welcome to the Main Application!")
            gr.Markdown("### If you see this, login was successful.")
            mock_user_info_md 
            
            mock_logout_button.click(
                fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(value="", visible=False), 
                            gr.update(visible=False), gr.update(visible=False), gr.update(value=None), gr.update(value=None), gr.update(value=[])),
                inputs=[],
                outputs=[mock_login_container, mock_main_app_container, mock_user_info_md, 
                         mock_logout_button, mock_chat_list_group, mock_username, mock_current_chat_id, mock_chat_history_state]
            )
            with mock_chat_list_group:
                gr.Markdown("### Your Chats (This is the mock sidebar)")
                gr.HTML("Mock chat items will appear here after successful login.")
            
            mock_chatbot_gr_instance

        # Call backend's init_backend function on app load (mimicking app.py)
        demo_app.load(fn=backend.init_backend, outputs=None, queue=True)

    ensure_user_db_exists_sync() 
    
    demo_app.launch(debug=True, share=False)
