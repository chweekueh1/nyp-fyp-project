import gradio as gr
import io
import json
import re
import os
import asyncio
from datetime import datetime, timezone, timedelta
from dateutil import tz
from dateutil.parser import parse as dateutil_parse
from collections import defaultdict
from dotenv import load_dotenv

# Assuming these are available
from utils import get_chatbot_dir
from hashing import hash_password, verify_password, is_password_complex

# Import your asynchronous backend module
import backend 

# --- Configuration ---
load_dotenv() 

USER_DB_PATH = os.path.join(get_chatbot_dir(), os.getenv('USER_DB_PATH', r'data\user_info\users.json'))
CHAT_SESSIONS_PATH = os.path.join(get_chatbot_dir(), os.getenv('CHAT_SESSIONS_PATH', r'data\chat_sessions'))

UTC_PLUS_8 = tz.tzoffset("UTC+8", timedelta(hours=8))
from_zone = tz.tzutc() # Backend saves timestamps in UTC
to_zone = tz.tzlocal() # Display in local timezone

MAX_UPLOAD_SIZE = 25
MAX_UPLOAD_SIZE_BYTE = MAX_UPLOAD_SIZE * 1024 * 1024

ALLOWED_EMAILS = [
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

# --- Helper Functions (Synchronous, for data manipulation) ---

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
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": {}}, f, indent=2)

def load_users_sync() -> dict:
    if not os.path.exists(USER_DB_PATH):
        ensure_user_db_exists_sync() 
        return {"users": {}}
    try:
        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
        if "users" not in data:
            return {"users": data}
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding users.json: {e}. File might be corrupted. Reinitializing.")
        ensure_user_db_exists_sync()
        return {"users": {}}
    except Exception as e:
        print(f"Unexpected error loading users.json: {e}. Reinitializing.")
        ensure_user_db_exists_sync()
        return {"users": {}}

def save_users_sync(users) -> None:
    try:
        with open(USER_DB_PATH, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users.json: {e}") 

def load_user_chats_sync(username) -> list:
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

def get_chat_interface_history(all_chat_messages: list, target_chat_id: str) -> list[list[str]]:
    """
    Converts the flat chat_history_state into the [[user_msg, bot_msg], ...] format
    required by gr.Chatbot for a specific chat_id.
    """
    if not all_chat_messages or not target_chat_id:
        return []
    
    filtered_messages = [
        msg for msg in all_chat_messages
        if msg.get('chat_id') == target_chat_id
    ]
    
    try:
        sorted_messages = sorted(filtered_messages, key=lambda x: get_datetime_from_timestamp(x.get('timestamp', '')))
    except Exception:
        sorted_messages = filtered_messages # Fallback

    chat_interface_history = []
    user_message_content = None
    for msg in sorted_messages:
        if msg['role'] == 'user':
            user_message_content = msg['content']
        elif msg['role'] == 'assistant' and user_message_content is not None:
            chat_interface_history.append([user_message_content, msg['content']])
            user_message_content = None # Reset for next pair
    return chat_interface_history

def generate_chat_list_html(all_chat_messages, active_chat_id):
    chat_groups_display = {}
    for msg in all_chat_messages:
        chat_id = msg.get('chat_id')
        if chat_id and msg['role'] == 'user' and chat_id not in chat_groups_display:
            chat_groups_display[chat_id] = msg
    
    if not chat_groups_display:
        return "<div>No previous chats found.</div>"

    sorted_chat_ids = sorted(
        chat_groups_display.keys(),
        key=lambda chat_id: get_datetime_from_timestamp(chat_groups_display[chat_id].get('timestamp', '')),
        reverse=True
    )

    html_content = ""
    for chat_id in sorted_chat_ids:
        first_msg = chat_groups_display[chat_id]
        shortened_text = first_msg["content"][:50] + "..." if len(first_msg["content"]) > 50 else first_msg["content"]
        is_selected = active_chat_id == chat_id
        container_class = "active-chat-item" if is_selected else ""

        dt_object = get_datetime_from_timestamp(first_msg.get('timestamp', ''))
        display_time = dt_object.astimezone(to_zone).strftime('%H:%M') if dt_object != datetime.min.replace(tzinfo=timezone.utc).astimezone(UTC_PLUS_8) else "N/A"
        
        html_content += f"""
        <div class='{container_class}'>
            <button class='chat-item-button' onclick='(function(){{
                const event = new CustomEvent("change_chat_event", {{ detail: "{chat_id}" }});
                document.getElementById("change_chat_btn_hidden").dispatchEvent(event);
            }})()'>
                <span class='chat-item-text'>{shortened_text}</span>
                <span class='chat-item-time'>{display_time}</span>
            </button>
        </div>
        <hr style='margin: 5px 0; opacity: 0.3;'>
        """
    return html_content


# --- MAIN GRADIO APP INSTANCE ---
with gr.Blocks(title="NYP AI Chatbot Helper", css="./styles/styles.css") as app:

    # --- GLOBAL STATE VARIABLES ---
    logged_in = gr.State(False)
    username = gr.State(None)
    chat_history_state = gr.State([]) 
    current_chat_id = gr.State(None) 
    temp_transcript = gr.State("") 

    # Main containers controlling visibility
    login_container = gr.Column(visible=True) # Contains only login/register UI
    main_app_container = gr.Column(visible=False) # Contains all post-login UI

    # Components whose initial visibility is controlled by main_app_container (and within it)
    user_info_md = gr.Markdown("", visible=False) # Starts hidden and empty
    logout_button_comp = gr.Button("Logout", visible=False) # Starts hidden
    
    # Group for "Your Chats" section and its content
    chat_list_html = gr.HTML("No previous chats found.") # Content updated on login
    chat_list_group = gr.Column(visible=False) # Entire group starts hidden

    # References for ChatInterface, render=False means they are not independently drawn
    chatbot_gr_instance = gr.Chatbot(label="Conversation", elem_id="chatbot", render=False) 
    chatbot_gr_textbox = gr.Textbox(placeholder="Type your message...", container=False, scale=7, render=False)


    # --- ASYNC BACKEND INTERACTION FUNCTIONS (Internal to this file for Gradio callbacks) ---
    async def _ask_question_backend_call(message: str, chat_history_interface_format: list):
        if not username.value:
            gr.Warning("Please log in to ask questions.")
            return chat_history_interface_format

        try:
            result = await backend.ask_question({
                "username": username.value,
                "question": message,
                "chat_id": current_chat_id.value
            })

            if result.get("code") == "429":
                gr.Error(result.get("error"))
                return chat_history_interface_format + [[message, result.get("error") + " (Rate Limit)"]]
            elif result.get("code") != "200":
                gr.Error(result.get("error", "An unknown error has occurred"))
                return chat_history_interface_format + [[message, result.get("error", "Error")]]
            
            gr.Info("Answer received!")

            user_message_data = result.get('user_message')
            bot_message_data = result.get('bot_message')

            updated_chat_history_list = chat_history_state.value + [user_message_data, bot_message_data]
            chat_history_state.value = updated_chat_history_list

            return chat_history_interface_format + [[message, bot_message_data['content']]]

        except Exception as e:
            gr.Error(f"An error occurred while asking question: {e}")
            return chat_history_interface_format + [[message, f"Error: {e}"]]


    async def _process_audio_transcribe_backend_call(audio_filepath):
        if audio_filepath is None:
            gr.Warning("No audio recorded to transcribe.")
            return gr.update(value="")

        try:
            with open(audio_filepath, "rb") as f:
                audio_bytes = f.read()
            
            payload = {"audio": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav"), "username": username.value}
            result = await backend.transcribe_audio(payload)

            if result.get("code") == "429":
                gr.Error(result.get("error"))
                return gr.update(value="")
            elif result.get("code") != "200":
                gr.Error(result.get("error", "Failed to get transcription"))
                return gr.update(value="")
            
            gr.Info("Audio transcribed! Review and submit.")
            return gr.update(value=result.get("transcript", ""))
        except Exception as e:
            gr.Error(f"Error during audio transcription: {e}")
            return gr.update(value="")


    async def _process_upload_files_backend_call(files_list):
        success_count = 0
        failure_messages = []
        if not username.value:
            gr.Warning("Please log in to upload files.")
            return
        if not files_list:
            gr.Warning("No files selected for upload.")
            return

        for file_obj in files_list:
            try:
                with open(file_obj.name, "rb") as f:
                    file_content = f.read()
            except Exception as e:
                failure_messages.append(f"Could not read file '{file_obj.orig_name}': {e}")
                continue

            if file_obj.size >= MAX_UPLOAD_SIZE_BYTE:
                failure_messages.append(f"File '{file_obj.orig_name}' is too large (>{MAX_UPLOAD_SIZE}MB).")
                continue
            
            payload = {
                "file": file_content,
                "name": file_obj.orig_name,
                "type": file_obj.mime_type,
                "username": username.value
            }
            
            result = await backend.upload_file(payload)
            
            if result.get("code") == "200":
                success_count += 1
            else:
                failure_messages.append(f"File '{file_obj.orig_name}' failed: {result.get('error', 'Unknown error')}")
        
        if failure_messages:
            gr.Warning(f"Uploaded {success_count} file(s). Failed for: {'; '.join(failure_messages)}")
        else:
            gr.Info(f"Successfully uploaded {success_count} file(s).")

    async def _process_classify_file_backend_call(file_obj):
        if not file_obj:
            gr.Warning("Please upload a file for classification.")
            return (gr.update(value="##### Classification: "), gr.update(value="##### Sensitivity: "), gr.update(value="##### Reasoning: "))
        
        try:
            with open(file_obj.name, "rb") as f:
                file_content = f.read()
            
            payload = {
                "file": file_content,
                "name": file_obj.orig_name,
                "type": file_obj.mime_type
            }
            
            result = await backend.data_classification(payload)

            if result.get("code") == "200":
                json_str = result.get("answer")
                cleaned = re.sub(r"^```json\s*|\s*```$", "", json_str)
                try:
                    data = json.loads(cleaned)
                    gr.Info("File successfully classified!")
                    return (
                        gr.update(value=f"##### Classification: `{data.get('classification', 'N/A')}`"),
                        gr.update(value=f"##### Sensitivity: `{data.get('sensitivity', 'N/A')}`"),
                        gr.update(value=f"##### Reasoning:\n> {data.get('reasoning', 'N/A')}")
                    )
                except json.JSONDecodeError:
                    gr.Error("Failed to parse classification response. Invalid JSON format from backend.")
                    return (gr.update(value="##### Classification: Error"), gr.update(value="##### Sensitivity: Error"), gr.update(value="##### Reasoning: Error"))
            else:
                gr.Error(result.get("error", "Data classification failed."))
                return (gr.update(value="##### Classification: Failed"), gr.update(value="##### Sensitivity: Failed"), gr.update(value="##### Reasoning: Failed"))
        except Exception as e:
            gr.Error(f"Error during file classification: {e}")
            return (gr.update(value="##### Classification: Error"), gr.update(value="##### Sensitivity: Error"), gr.update(value="##### Reasoning: Error"))

    # --- LOGIN/REGISTER LOGIC ---
    async def _process_login_logic(username_val, password_val):
        try:
            users_data = await asyncio.to_thread(load_users_sync)
            users = users_data.get("users", {})

            if username_val not in users:
                gr.Error("Incorrect username or password.")
                return (gr.update(value=False), gr.update(value=None), gr.update(value=None), "Incorrect username or password.", 
                        gr.update(visible=True), gr.update(visible=False), gr.update(value=""), gr.update(visible=False), # Reset user_info_md to hidden, empty
                        gr.update(visible=False), # chat_list_group
                        gr.update(visible=False) # logout_button_comp
                       )

            elif verify_password(password_val, users[username_val]["hashedPassword"]): 
                gr.Info("Login successful!")
                new_logged_in_state = True
                new_username_state = username_val
                
                loaded_history = await asyncio.to_thread(load_user_chats_sync, new_username_state)
                chat_history_state.value = loaded_history
                
                new_current_chat_id = f"{new_username_state}_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"
                
                for msg in chat_history_state.value:
                    if 'chat_id' not in msg:
                        msg['chat_id'] = f"{new_username_state}_legacy_chat_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"

                initial_chatbot_history = get_chat_interface_history(chat_history_state.value, new_current_chat_id)

                return (gr.update(value=new_logged_in_state),
                        gr.update(value=new_username_state),
                        gr.update(value=new_current_chat_id),
                        "Login successful!",
                        gr.update(visible=False), # Hide login container
                        gr.update(visible=True), # Show main app container
                        gr.update(value=f"**Logged in as:** {new_username_state}", visible=True), # Update user info, make visible
                        gr.update(visible=True), # Show logout button
                        gr.update(visible=True), # Show chat_list_group
                        gr.update(value=initial_chatbot_history)
                       ) 
            else:
                gr.Error("Incorrect username or password.")
                return (gr.update(value=False), gr.update(value=None), gr.update(value=None), "Incorrect username or password.", 
                        gr.update(visible=True), gr.update(visible=False), gr.update(value=""), gr.update(visible=False), # Reset user_info_md to hidden, empty
                        gr.update(visible=False), # chat_list_group
                        gr.update(visible=False) # logout_button_comp
                       )
        except Exception as e:
            gr.Error(f"An unexpected error occurred during login: {e}")
            return (gr.update(value=False), gr.update(value=None), gr.update(value=None), f"An error occurred: {e}", 
                    gr.update(visible=True), gr.update(visible=False), gr.update(value=""), gr.update(visible=False), # Reset user_info_md to hidden, empty
                    gr.update(visible=False), # chat_list_group
                    gr.update(visible=False) # logout_button_comp
                   )


    async def _process_register_logic(username_val, email_val, password_val, confirm_val):
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
        is_complex, message = is_password_complex(password_val) 

        if username_val in users:
            gr.Warning("Username already exists.")
            return "Username already exists."
        if any(user["email"] == email_val for user in users.values()):
            gr.Warning("This email is already registered.")
            return "This email is already registered."
        if not is_complex:
            gr.Warning(message)
            return message

        hashed_password = hash_password(password_val) 
        users[username_val] = {
            "email": email_val,
            "hashedPassword": hashed_password
        }
        users_data["users"] = users
        await asyncio.to_thread(save_users_sync, users_data)
        gr.Info("Registration successful! You can now log in.")
        return "Registration successful! You can now log in."

    # --- LOGOUT LOGIC ---
    def _process_logout_logic():
        gr.Info("Logged out successfully!")
        chat_history_state.value = []
        return (
            gr.update(value=False), # logged_in
            gr.update(value=None), # username
            gr.update(value=None), # current_chat_id
            gr.update(visible=True), # login_container visibility
            gr.update(visible=False), # main_app_container visibility
            gr.update(value="", visible=False), # user_info_md text (empty, hidden)
            gr.update(visible=False), # logout_button_comp visibility
            gr.update(visible=False), # Hide chat_list_group
            gr.HTML("No previous chats found."), # chat_list_html content (reset to initial)
            gr.update(value=[]) # Clear chatbot display
        )


    # --- MAIN APPLICATION LAYOUT ASSEMBLY ---

    # The login UI: Initially visible. Includes the main header.
    with login_container:
        gr.Markdown("<div class='main-header'>NYP AI Chatbot Helper</div>") # Moved header here
        gr.Markdown("## Login / Register")
        with gr.Tabs():
            with gr.Tab("Login"):
                username_login_input = gr.Textbox(label="Username")
                password_login_input = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Login", variant="primary")
                login_message = gr.Markdown()

                login_btn.click(
                    fn=_process_login_logic,
                    inputs=[username_login_input, password_login_input],
                    outputs=[logged_in, username, current_chat_id, login_message,
                             login_container, main_app_container, user_info_md, logout_button_comp,
                             chat_list_group, 
                             chatbot_gr_instance 
                            ],
                    queue=False
                )

            with gr.Tab("Register"):
                username_register_input = gr.Textbox(label="New Username")
                email_register_input = gr.Textbox(label="Email Address")
                password_register_input = gr.Textbox(label="New Password", type="password")
                confirm_password_input = gr.Textbox(label="Confirm Password", type="password")
                register_btn = gr.Button("Register", variant="primary")
                register_message = gr.Markdown()

                register_btn.click(
                    fn=_process_register_logic,
                    inputs=[username_register_input, email_register_input, password_register_input, confirm_password_input],
                    outputs=[register_message]
                )

    # The main application UI: Initially hidden.
    with main_app_container:
        # Note: The main header is NOT duplicated here. It moves with login_container.
        with gr.Row():
            # Sidebar for chat list and user info
            with gr.Column(scale=1, min_width=250):
                user_info_md # Dynamically updated and made visible on login
                logout_button_comp # Dynamically visible/hidden
                
                new_chat_btn = gr.Button("New Chat", elem_classes="new-chat-button", variant="primary")
                new_chat_btn.click(
                    fn=lambda u: gr.update(value=f"{u}_{datetime.now(timezone.utc).strftime(r'%Y%m%d%H%M%S%f')}"),
                    inputs=[username],
                    outputs=[current_chat_id]
                ).success(
                    lambda: gr.Info("Started a new chat!"),
                    outputs=None
                )
                
                # Consolidated chat list display into a controllable group
                with chat_list_group: # This group's visibility is controlled by login/logout
                    gr.Markdown("### Your Chats")
                    chat_list_html

            # Main content area with TabbedInterface
            with gr.Column(scale=3):
                # Defining the content for each tab directly here
                # Ensuring all nested components start with visible=False if they should not appear prematurely.
                with gr.Blocks() as chatbot_tab_block:
                    gr.Markdown("<div class='sub-header'>Ask a Question</div>")
                    gr.ChatInterface(
                        fn=_ask_question_backend_call,
                        textbox=chatbot_gr_textbox, 
                        chatbot=chatbot_gr_instance, 
                        multimodal=False,
                    )
                    with gr.Column():
                        gr.Markdown("#### Or use Speech Input:")
                        transcribe_btn = gr.Button("Transcribe Audio", variant="secondary")
                        audio_recorder_comp = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Record your question", waveform_options=gr.WaveformOptions(
                                waveform_progress_color="#ff4b4b",waveform_color="#0066cc", show_recording_waveform=True 
                            ))
                        transcribe_btn.click(
                            fn=_process_audio_transcribe_backend_call,
                            inputs=[audio_recorder_comp],
                            outputs=[chatbot_gr_textbox],
                            show_progress="full",
                            queue=True
                        )

                with gr.Blocks() as file_upload_tab_block:
                    gr.Markdown("<div class='sub-header'>Upload Files</div>")
                    file_uploader = gr.File(file_count="multiple", type="filepath", label="Choose file(s)") 
                    upload_btn = gr.Button("Upload", variant="primary")
                    upload_btn.click(
                        fn=_process_upload_files_backend_call,
                        inputs=[file_uploader],
                        outputs=None, 
                        show_progress="full",
                        queue=True
                    ).then(lambda: gr.update(value=[]), outputs=[file_uploader], queue=False)

                with gr.Blocks() as data_classification_tab_block:
                    gr.Markdown("<div class='sub-header'>Classify File</div>")
                    classify_file_uploader = gr.File(file_count="single", type="filepath", label="Choose a file")
                    classify_btn = gr.Button("Classify", variant="primary")
                    classification_md = gr.Markdown("##### Classification: ")
                    sensitivity_md = gr.Markdown("##### Sensitivity: ")
                    reasoning_md = gr.Markdown("##### Reasoning: ")
                    classify_btn.click(
                        fn=_process_classify_file_backend_call,
                        inputs=[classify_file_uploader],
                        outputs=[classification_md, sensitivity_md, reasoning_md],
                        show_progress="full",
                        queue=True
                    ).then(lambda: gr.update(value=None), outputs=[classify_file_uploader], queue=False)

                gr.TabbedInterface(
                    [chatbot_tab_block, file_upload_tab_block, data_classification_tab_block],
                    ["Ask Questions", "File Upload", "Data Classification"]
                )

    # --- GLOBAL EVENT HANDLERS ---

    chat_history_state.change(
        fn=generate_chat_list_html,
        inputs=[chat_history_state, current_chat_id],
        outputs=[chat_list_html]
    )
    current_chat_id.change(
        fn=generate_chat_list_html,
        inputs=[chat_history_state, current_chat_id],
        outputs=[chat_list_html]
    )
    current_chat_id.change(
        fn=get_chat_interface_history,
        inputs=[chat_history_state, current_chat_id],
        outputs=[chatbot_gr_instance],
        queue=False
    )
    
    logout_button_comp.click(
        fn=_process_logout_logic,
        inputs=[],
        outputs=[logged_in, username, current_chat_id, 
                 login_container, main_app_container, user_info_md, logout_button_comp, chat_list_group, chat_list_html,
                 chatbot_gr_instance 
                ],
        queue=False
    )

    change_chat_btn_hidden = gr.Button("Change Chat (Hidden)", elem_id="change_chat_btn_hidden", visible=False)
    change_chat_btn_hidden.click(
        fn=lambda chat_id_detail: chat_id_detail,
        inputs=[gr.Textbox(value="", elem_id="change_chat_event_data_input")],
        outputs=[current_chat_id],
        queue=False
    )
    app.load(js="""
        const targetButton = document.getElementById('change_chat_btn_hidden');
        if (targetButton) {
            targetButton.addEventListener('change_chat_event', function(e) {
                const dataInput = document.getElementById('change_chat_event_data_input');
                if (dataInput) {
                    dataInput.value = e.detail;
                    dataInput.dispatchEvent(new Event('input', { bubbles: true }));
                    targetButton.click();
                }
            });
        }
    """)
    gr.Textbox(value="", elem_id="change_chat_event_data_input", visible=False)

    # --- Backend Initialization ---
    app.load(fn=backend.init_backend, outputs=None, queue=True)


# --- Launch the Gradio Application ---
if __name__ == "__main__":
    ensure_user_db_exists_sync()
    
    print("Launching Gradio app...")
    app.launch(debug=True, share=False)
