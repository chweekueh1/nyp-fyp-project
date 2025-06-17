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
import traceback 

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

ALLOWED_EMAILS = [ 
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

# --- Helper Functions (Synchronous, for user/chat data management - local to login.py) ---

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
    """
    Loads all chat histories for a given user.
    Called to ensure the user's chat sessions directory is created/checked.
    """
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
# Populates the passed-in login_container_comp and returns the app_data_dict.
def login_interface(app_data_dict: dict) -> dict:

    # Retrieve core components from the dictionary (direct access, no .get() with fallbacks here)
    logged_in_state = app_data_dict['logged_in_state']
    username_state = app_data_dict['username_state']
    login_container_comp = app_data_dict['login_container_comp'] 

    # --- Password Visibility Toggle Helper ---
    def toggle_password_visibility(is_visible: bool):
        new_type = "password" if is_visible else "text"
        new_icon = "👁️" if is_visible else "🙈" 
        new_is_visible = not is_visible 

        return gr.update(type=new_type), gr.update(value=new_icon), new_is_visible

    # --- Login Logic (Refactored for minimal responsibility) ---
    async def _process_login_logic(username_val, password_val):
        try:
            print(f"DEBUG: _process_login_logic - Attempting login for user: {username_val}")
            users_data = await asyncio.to_thread(load_users_sync)
            users = users_data.get("users", {}) 

            if username_val not in users:
                print(f"DEBUG: _process_login_logic - User '{username_val}' not found. Returning error.")
                gr.Error("Incorrect username or password.") 
                return (gr.update(value=False),           
                        gr.update(value=None),             
                        gr.update(value="Incorrect username or password."), 
                        gr.update(visible=True))          

            elif hashing.verify_password(password_val, users[username_val]["hashedPassword"]):
                print(f"DEBUG: _process_login_logic - Password verified for user: {username_val}. Signaling success.")
                gr.Info("Login successful! Main application loading...") 
                
                await asyncio.to_thread(load_user_chats_sync, username_val) 
                print(f"DEBUG: _process_login_logic - Ensuring user chat session directory exists.")

                print("DEBUG: _process_login_logic - Returning minimal Gradio updates for success.")
                return (gr.update(value=True),       
                        gr.update(value=username_val), 
                        gr.update(value=""),          
                        gr.update(visible=False))      
            else: 
                print(f"DEBUG: _process_login_logic - User '{username_val}' found, but password incorrect. Returning error.")
                gr.Error("Incorrect username or password.") 
                return (gr.update(value=False), gr.update(value=None), gr.update(value="Incorrect username or password."), 
                        gr.update(visible=True))

        except Exception as e:
            print(f"ERROR: _process_login_logic - An unexpected fatal error occurred: {e}. Printing traceback.")
            traceback.print_exc() 
            gr.Error(f"An unexpected error occurred during login: {e}")
            return (gr.update(value=False), gr.update(value=None), gr.update(value=f"An unexpected error occurred: {e}"), 
                    gr.update(visible=True))


    # --- Register Logic ---
    async def _process_register_logic(username_val, email_val, password_val, confirm_val):
        try:
            if not username_val or not email_val or not password_val or not confirm_val:
                gr.Warning("Please fill all fields.")
                return "Please fill all fields." 
            if password_val != confirm_val:
                gr.Error("Passwords do not match.")
                return "Passwords do not match."
            if email_val not in ALLOWED_EMAILS: 
                gr.Error("This email is not allowed to register.")
                return "This email is not allowed to register."

            users_data = await asyncio.to_thread(load_users_sync)
            users = users_data.get("users", {}) 
            is_complex, message = hashing.is_password_complex(password_val)

            if username_val in users:
                gr.Warning("Username already exists.")
                return "Username already exists."
            if any(user["email"] == email_val for user in users.values()):
                gr.Warning("This email is already registered.")
                return "This email is already registered."
            if not is_complex:
                gr.Warning(message)
                return message 

            hashed_password = hashing.hash_password(password_val)
            users[username_val] = {
                "email": email_val,
                "hashedPassword": hashed_password
            }
            users_data["users"] = users 
            await asyncio.to_thread(save_users_sync, users_data)
            print(f"DEBUG: _process_register_logic - Registration successful for user: {username_val}. Calling gr.Info.")
            gr.Info("Registration successful! You can now log in.")
            return "Registration successful! You can now log in." 
        except Exception as e:
            print(f"ERROR: _process_register_logic - An unexpected error occurred during registration: {e}. Printing traceback.")
            traceback.print_exc()
            gr.Error(f"An unexpected error occurred during registration: {e}")
            return f"An unexpected error occurred: {e}"

    # --- UI Layout for Login/Register (now populates the passed-in container) ---
    with login_container_comp: 
        gr.Markdown("<div class='main-header'>NYP AI Chatbot Helper</div>") 
        gr.Markdown("## Login / Register")
        with gr.Tabs():
            with gr.Tab("Login"):
                username_login_input = gr.Textbox(label="Username")
                
                with gr.Row():
                    password_login_input = gr.Textbox(label="Password", type="password", scale=8)
                    show_password_login_btn = gr.Button("👁️", scale=1, min_width=50, elem_classes="eye-button") 
                    is_password_login_visible = gr.State(False) 

                login_message = gr.Markdown() 

                login_btn = gr.Button("Login", variant="primary")

                login_btn.click(
                    fn=_process_login_logic,
                    inputs=[username_login_input, password_login_input],
                    outputs=[logged_in_state, username_state, login_message, login_container_comp], 
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
                
                with gr.Row():
                    password_register_input = gr.Textbox(label="New Password", type="password", scale=8)
                    show_password_register_btn = gr.Button("👁️", scale=1, min_width=50, elem_classes="eye-button")
                    is_password_register_visible = gr.State(False) 

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
    
    return app_data_dict 

# --- Test Block for login.py (simulating app.py's main logic) ---
if __name__ == "__main__":
    load_dotenv() 

    # --- Minimal Helper for get_chat_interface_history (mocked as it's an app.py function) ---
    def mock_get_chat_interface_history(all_chat_messages, target_chat_id):
        print(f"DEBUG (Test): mock_get_chat_interface_history called for chat_id: {target_chat_id}")
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
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
            border-radius: 8px; 
        }
        .gr-row {
            align-items: center; 
        }
    """) as demo_app:
        # --- Centralized dictionary for all Gradio states and components ---
        app_data = {
            'logged_in_state': gr.State(False),
            'username_state': gr.State(None),
            'current_chat_id_state': gr.State(None),
            'chat_history_state': gr.State([]),
            'login_container_comp': gr.Column(visible=True), 
            'main_app_container_comp': gr.Column(visible=False), 
            'user_info_md_comp': gr.Markdown("", visible=False),
            'logout_button_comp': gr.Button("Logout", visible=False),
            'chat_list_group_comp': gr.Column(visible=False),
            'chatbot_gr_instance_comp': gr.Chatbot(visible=False),
            # Add gr.Audio as per previous user request.
            'audio_output_comp': gr.Audio(
                label="Audio Output",
                type="filepath", 
                autoplay=False,
                waveform_options={"waveform_progress_color": "green", "waveform_color": "blue"},
                visible=False, 
                elem_id="main_audio_output" 
            )
        }

        # Call the login_interface function, passing app_data.
        # login_interface will populate app_data['login_container_comp'] directly.
        # The returned app_data is re-assigned for explicit flow.
        app_data = login_interface(app_data_dict=app_data)

        # --- Main Application Content (simulates app.py's main layout) ---
        with app_data['main_app_container_comp']:
            gr.Markdown("## Welcome to the Main Application!")
            gr.Markdown("### If you see this, login was successful and `app.py` took over.")
            
            app_data['user_info_md_comp'] 
            app_data['logout_button_comp']
            
            app_data['logout_button_comp'].click(
                fn=lambda: (
                    app_data['login_container_comp'].update(visible=True),
                    app_data['main_app_container_comp'].update(visible=False),
                    app_data['user_info_md_comp'].update(value="", visible=False), 
                    app_data['logout_button_comp'].update(visible=False),
                    app_data['chat_list_group_comp'].update(visible=False),
                    app_data['username_state'].update(value=None), 
                    app_data['logged_in_state'].update(value=False), 
                    app_data['chatbot_gr_instance_comp'].update(value=[], visible=False),
                    app_data['current_chat_id_state'].update(value=None), 
                    app_data['chat_history_state'].update(value=[]), 
                    app_data['audio_output_comp'].update(visible=False, value=None), # Update audio component
                ),
                inputs=[],
                outputs=[
                    app_data['login_container_comp'], app_data['main_app_container_comp'], app_data['user_info_md_comp'],
                    app_data['logout_button_comp'], app_data['chat_list_group_comp'], app_data['username_state'],
                    app_data['logged_in_state'], app_data['chatbot_gr_instance_comp'],
                    app_data['current_chat_id_state'], app_data['chat_history_state'],
                    app_data['audio_output_comp'], # Add audio component to outputs
                ]
            )
            with app_data['chat_list_group_comp']:
                gr.Markdown("### Your Chats (This is the mock sidebar from app.py logic)")
                gr.HTML("Mock chat items will appear here once app.py loads them.")
            
            app_data['chatbot_gr_instance_comp'] 
            app_data['audio_output_comp'] # Place the audio component

        # --- Event Listener for logged_in_state (simulates app.py's main logic) ---
        @demo_app.load 
        @app_data['logged_in_state'].change 
        def handle_login_state_change(): 
            print(f"DEBUG (App Simulation): handle_login_state_change triggered.")
            
            is_logged_in = app_data['logged_in_state'].value
            current_username = app_data['username_state'].value

            print(f"DEBUG (App Simulation): Current states: logged_in={is_logged_in}, username={current_username}")
            
            # Direct access to component objects from the app_data dictionary.
            login_container = app_data['login_container_comp']
            main_app_container = app_data['main_app_container_comp']
            user_info_md = app_data['user_info_md_comp']
            logout_button = app_data['logout_button_comp']
            chat_list_group = app_data['chat_list_group_comp']
            chatbot_instance = app_data['chatbot_gr_instance_comp']
            current_chat_id_state = app_data['current_chat_id_state']
            chat_history_state = app_data['chat_history_state']
            audio_output = app_data['audio_output_comp'] # Retrieve audio component

            # Prepare tuple of gr.update objects in the exact order of handle_login_state_change_outputs
            if is_logged_in:
                print("DEBUG (App Simulation): User is logged in. Showing main app UI.")
                
                initial_chat_history = [] 
                current_chat_id = f"{current_username}_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"
                
                return (
                    gr.update(visible=False), # login_container
                    gr.update(visible=True),  # main_app_container
                    gr.update(value=f"**Logged in as:** {current_username}", visible=True), # user_info_md
                    gr.update(visible=True),  # logout_button
                    gr.update(visible=True),  # chat_list_group
                    gr.update(value=[], visible=True), # chatbot_instance
                    gr.update(value=current_chat_id), # current_chat_id_state
                    gr.update(value=initial_chat_history), # chat_history_state
                    gr.update(visible=True) # audio_output (show on login)
                )
            else:
                print("DEBUG (App Simulation): User is logged out. Showing login UI.")
                return (
                    gr.update(visible=True),  # login_container
                    gr.update(visible=False), # main_app_container
                    gr.update(value="", visible=False), # user_info_md
                    gr.update(visible=False), # logout_button
                    gr.update(visible=False), # chat_list_group
                    gr.update(value=[], visible=False), # chatbot_instance
                    gr.update(value=None), # current_chat_id_state
                    gr.update(value=[]), # chat_history_state
                    gr.update(visible=False, value=None) # audio_output (hide and clear on logout)
                )

        handle_login_state_change_inputs = [] 

        # Define outputs for handle_login_state_change as a LIST of component objects.
        # This list's ORDER MUST MATCH the order of gr.update objects returned by the function.
        handle_login_state_change_outputs = [
            app_data['login_container_comp'], 
            app_data['main_app_container_comp'], 
            app_data['user_info_md_comp'],
            app_data['logout_button_comp'], 
            app_data['chat_list_group_comp'], 
            app_data['chatbot_gr_instance_comp'],
            app_data['current_chat_id_state'], 
            app_data['chat_history_state'],
            app_data['audio_output_comp'], # Add audio component to the outputs list
        ]
        
        app_data['logged_in_state'].change(
            fn=handle_login_state_change,
            inputs=handle_login_state_change_inputs,
            outputs=handle_login_state_change_outputs
        )
        
        demo_app.load(
            fn=handle_login_state_change,
            inputs=handle_login_state_change_inputs,
            outputs=handle_login_state_change_outputs,
            queue=False
        )

    ensure_user_db_exists_sync() 
    
    demo_app.launch(debug=True, share=False)
