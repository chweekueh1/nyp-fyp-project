import streamlit as st
import requests
import io
import json
import re
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from datetime import datetime, timezone
from dateutil import tz
from collections import defaultdict
from utils import rel2abspath, get_home_directory_path
from hashing import hash_password, verify_password

# Set page configuration
st.set_page_config(
    page_title="NYP AI Chatbot Helper",
    page_icon="🤖",
    layout="wide"
)

# Apply custom styling
st.markdown('''
<style>
    .css-1egvi7u {margin-top: -3rem;}
    .stAudio {height: 45px;}
    .css-v37k9u a {color: #ff4c4b;}
    .css-nlntq9 a {color: #ff4c4b;}
    .main-header { font-size: 2rem; color: #0066cc; text-align: center; margin: 1rem 0 2rem 0; }
    .sub-header { font-size: 1.5rem; color: #0066cc; margin-top: 2rem; margin-bottom: 1rem; }
    .success-message { padding: 1rem; border-radius: 0.5rem; background-color: #d4edda; color: #155724; }
    .error-message { padding: 1rem; border-radius: 0.5rem; background-color: #f8d7da; color: #721c24;}
    
    /* Microphone button styling */
    .microphone-button { display: flex; justify-content: center; margin: 20px 0; }
    
    /* Recording indicator */
    .recording-indicator { color: #ff4b4b; font-weight: bold; text-align: center; margin-top: 10px; animation: blink 1s infinite; }
    
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; }}
    
    /* Audio player container */
    .audio-container { display: flex; align-items: center; margin: 15px 0; padding: 10px; border-radius: 8px; background-color: #f0f2f6; }
    
    /* Delete button */
    .delete-button { color: #ff4b4b; cursor: pointer; margin-left: 10px; }
    
    /* Recording button styling */
    .record-button { background-color: #0066cc; color: white; border-radius: 50%; width: 80px; height: 80px; font-size: 24px; border: none;
        cursor: pointer; transition: all 0.3s; }
    .record-button.recording { background-color: #ff4b4b; animation: pulse 1.5s infinite; }
    
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); }}
            
     .submit-button { background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    
    /* Input method selector styling */
    .input-selector { display: flex; margin-bottom: 20px; background-color: #f0f2f6; border-radius: 8px; overflow: hidden; }
    .input-option { flex: 1; text-align: center; padding: 10px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
    .input-option.active { background-color: #0066cc; color: white; }
    .input-option:hover:not(.active) { background-color: #dbe4f0; }
    
    /* Divider styling */
    .divider { margin: 20px 0; border-top: 1px solid #e0e0e0; }
    
    /* Response container styling */
    .response-container { margin-top: 20px; padding: 15px; border-radius: 8px; background-color: #f8f9fa; border-left: 4px solid #0066cc; }
    
    /* Chat message styling */
    .chat-container { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; padding: 10px; max-height: 500px; overflow-y: auto;
        border-radius: 8px; background-color: #f8f9fa; }
    .message-container { display: flex; flex-direction: column; max-width: 80%; padding: 10px 15px; border-radius: 15px; font-size: 16px; }
    .user-message { align-self: flex-end; background-color: #0066cc; color: white; border-bottom-right-radius: 5px; }
    .bot-message { align-self: flex-start; background-color: #e6f7ff; color: #333; border-bottom-left-radius: 5px; }
    .message-time { font-size: 12px; color: #888; align-self: flex-end; margin-top: 5px; }
    
    /* New chat button styling */
    .new-chat-button { background-color: #0066cc; color: white; border: none; padding: 8px 16px; border-radius: 5px; font-weight: bold; 
            margin-top: 10px; margin-bottom: 20px; width: 100%; transition: all 0.3s; }
    .new-chat-button:hover { background-color: #004c99; }
    
    /* Active chat styling */
    .active-chat { border-left: 3px solid #0066cc; background-color: #e6f7ff; }
</style>
''', unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'recorder' not in st.session_state:
    st.session_state.recorder = None
if 'recording_mode' not in st.session_state:
    st.session_state.recording_mode = False
if 'temp_transcript' not in st.session_state:
    st.session_state.temp_transcript = ""
if 'input_method' not in st.session_state:
    st.session_state.input_method = "text"
if 'question_input' not in st.session_state:
    st.session_state.question_input = ""
if 'chat_history' not in st.session_state:
     st.session_state.chat_history = []
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'chat_groups' not in st.session_state:
    st.session_state.chat_groups = {}

# List of allowed emails
ALLOWED_EMAILS = [
    "staff123@mymail.nyp.edu.sg",
    "staff345@mymail.nyp.edu.sg",
    "staff678@mymail.nyp.edu.sg",
]

load_dotenv()

USER_DB_PATH = rel2abspath(os.getenv('USER_DB_PATH', f'{get_home_directory_path()}\\.nypai-chatbot\\data\\user_info\\users.json'))
CHAT_SESSIONS_PATH = rel2abspath(os.getenv('CHAT_SESSIONS_PATH', ''))

# API Configuration
API_URL = "http://127.0.0.1:5001"

# Detect local timezone
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

# Helper function to handle API requests with error handling
def handle_api_request(endpoint, method="post", data=None, files=None, json=None):
    try:
        if method.lower() == "post":
            response = requests.post(f"{API_URL}/{endpoint}", data=data, files=files, json=json)
        else:
            response = requests.get(f"{API_URL}/{endpoint}", params=data)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        return None, "Oops! The system took too long to respond. Please try again later."
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}"

def ensure_user_db_exists():
    """Ensure the user info directory and users.json exist."""
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
    
    if not os.path.exists(USER_DB_PATH):
        # Create default users.json with empty structure
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": {}}, f, indent=2)

def load_user_chats(username):
    """Load all saved chats for the given user."""
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    if not os.path.exists(user_folder):
        return []
    
    chat_files = [f for f in os.listdir(user_folder) if f.endswith(".json")]
    chat_histories = []

    for chat_file in chat_files:
        with open(os.path.join(user_folder, chat_file), 'r') as f:
            chat_histories.append(json.load(f))

    return chat_histories

def load_users():
    if not os.path.exists(USER_DB_PATH):
        return {"users": {}}

    with open(USER_DB_PATH, 'r') as f:
        return json.load(f)
    
    if "users" not in data:
        return {"users": data}
    
    return data

def save_users(users):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login / Register")
        tab1, tab2 = st.tabs(["Login", "Register"])

        # --- LOGIN TAB ---
        with tab1:
            username_login = st.text_input("Username", key="login_username")
            password_login = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                users_data = load_users()
                users = users_data.get("users", {})
                
                if username_login not in users:
                    st.error("Username not found.")
                elif verify_password(password_login, users[username_login]["hashedPassword"]):
                    st.session_state.logged_in = True
                    st.session_state.username = username_login
                    st.session_state.chat_history = []
                    fetch_user_history(username_login)
                    new_chat_id = f"{st.session_state.username}_{datetime.now(timezone.utc).strftime(r'%d%m%Y%H%M%S%f')}"
                    st.session_state.current_chat_id = new_chat_id
                    st.rerun()
                else:
                    st.error("Incorrect password.")

        # --- REGISTER TAB ---
        with tab2:
            username_register = st.text_input("New Username", key="register_username")
            email_register = st.text_input("Email Address", key="register_email")
            password_register = st.text_input("New Password", type="password", key="register_password")
            confirm_register = st.text_input("Confirm Password", type="password", key="confirm_password")

            if st.button("Register", use_container_width=True):
                if not username_register or not email_register or not password_register or not confirm_register:
                    st.warning("Please fill all fields.")
                elif password_register != confirm_register:
                    st.error("Passwords do not match.")
                elif email_register not in ALLOWED_EMAILS:
                    st.error("This email is not allowed to register.")
                else:
                    users_data = load_users()
                    users = users_data.get("users", {})

                    if username_register in users:
                        st.warning("Username already exists.")
                    elif any(user["email"] == email_register for user in users.values()):
                        st.warning("This email is already registered.")
                    else:
                        hashed_password = hash_password(password_register)
                        users[username_register] = {
                            "email": email_register,
                            "hashedPassword": hashed_password
                        }
                        users_data["users"] = users
                        save_users(users_data)
                        st.success("Registration successful! You can now log in.")

def fetch_user_history(username):
    try:
        local_history = load_user_chats(username)

        combined_history = []
        if local_history:
            for chat in local_history:
                combined_history.extend(chat)

        for msg in combined_history:
            if 'chat_id' not in msg:
                msg['chat_id'] = f"{st.session_state.username}_{datetime.now(timezone.utc).strftime(r'%d%m%Y%H%M%S%f')}"

        st.session_state.chat_history = combined_history

    except Exception as e:
        st.warning(f"Error loading chat history: {str(e)}")
        st.session_state.chat_history = []

# Sends question to backend and gets answer
def ask_question(question):
    with st.spinner("Getting answer..."):
        payload = {
            "username": st.session_state.username,
            "question": question,
            "chat_id": st.session_state.current_chat_id
        }
        result, error = handle_api_request("ask", json=payload)
        
        if error:
            st.error(error)
            return None
        
        answer = result.get("answer")
        user_message = result.get('user_message')
        bot_message = result.get('bot_message')
        st.session_state.chat_history.append(user_message)
        st.session_state.chat_history.append(bot_message)

        return answer

# Sends audio to backend for transcription
def transcribe_and_process_audio(audio_data):
    audio_bytes = io.BytesIO(audio_data)
    files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
    result, error = handle_api_request("transcribe", files=files)
    if error:
        st.error(error)
        return None
    return result.get("transcript")

def upload_file(file):
    """Upload file to backend"""
    with st.spinner("Uploading and processing file(s)..."):
        files = {"file": file}
        username = st.session_state.username
        response, error = handle_api_request("upload", data={"username": username}, files=files)

        if error:
            st.error(error)
            return False
        
        return True

# Handles file upload
def file_upload_section():
    failure = 0
    with st.form('Upload file(s)', clear_on_submit=True):
        uploaded_files = st.file_uploader("Choose a file", type=[
        'bmp', 'csv', 'doc', 'docx', 'eml', 'epub', 'heic', 'html',
        'jpeg', 'jpg', 'png', 'md', 'msg', 'odt', 'org', 'p7s', 'pdf',
        'ppt', 'pptx', 'rst', 'rtf', 'tiff', 'txt', 'tsv', 'xls', 'xlsx', 'xml'
        ], accept_multiple_files=True)
    
        submitted = st.form_submit_button('Upload')

        if submitted and uploaded_files != []:
            for uploaded_file in uploaded_files:
                if not upload_file(uploaded_file):
                    failure += 1
            success = len(uploaded_files) - failure
            st.success(f'Uploaded {success} file(s) successfully, {failure} file(s) failed')

# Handles file classification
def file_classification_section():
    with st.form('Classify file', clear_on_submit=True):
        uploaded_file = st.file_uploader("Choose a file", type=[
        'bmp', 'csv', 'doc', 'docx', 'eml', 'epub', 'heic', 'html',
        'jpeg', 'jpg', 'png', 'md', 'msg', 'odt', 'org', 'p7s', 'pdf',
        'ppt', 'pptx', 'rst', 'rtf', 'tiff', 'txt', 'tsv', 'xls', 'xlsx', 'xml'])
    
        submitted = st.form_submit_button('Classify')

        if submitted:
            if uploaded_file is None:
                st.warning("Please upload a file before submitting")
            else:
                with st.spinner("Classifying file..."):
                    files = {"file": uploaded_file}
                    response = requests.post("http://127.0.0.1:5001/classify", files=files)

            if response.status_code == 200:
                json_str = response.json().get("answer")
                cleaned = re.sub(r"^```json\s*|\s*```$", "",json_str)
                data = json.loads(cleaned)

                st.success("File successfully classified!")
                st.markdown(f"##### Classification:`{data.get('classification')}`")
                st.markdown(f"##### Sensitivity:`{data.get('sensitivity')}`")
                st.markdown("##### Reasoning:")
                st.markdown(f"> {data.get('reasoning')}")   
                
            else:
                st.error(f"Data classification failed: {response.json().get('error')}")
            
# Records audio and transcript correction
def audio_input_section():
    if not st.session_state.audio_data or 'recording_mode' in st.session_state and st.session_state.recording_mode:
        audio_bytes = audio_recorder(
            pause_threshold=100000,
            recording_color="#ff4b4b",
            neutral_color="#0066cc",
            icon_size="2.5x"
        )

        if audio_bytes:
            st.session_state.audio_data = audio_bytes
            st.session_state.recording_mode = False
            with st.spinner("Transcribing your audio..."):
                transcript = transcribe_and_process_audio(audio_bytes)
                if transcript:
                    st.session_state.temp_transcript = transcript
                else:
                    st.error("Failed to get transcription")
            st.rerun()

    if st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format='audio/wav')
        if 'temp_transcript' not in st.session_state:
            st.session_state.temp_transcript = ""
        st.markdown("### Your Transcription")
        corrected_transcript = st.text_area(
            "Review and correct the transcription if needed:",
            value=st.session_state.temp_transcript,
            key="transcript_editor"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", key="submit_transcript"):
                if corrected_transcript:
                    answer = ask_question(corrected_transcript)
                    if answer:
                        st.session_state.audio_data = None
                        st.session_state.temp_transcript = ""
                        st.rerun()
                    else:
                        st.error("Failed to get AI response") 
        with col2:
            if st.button("Re-record Audio", key="rerecord_btn"):
                st.session_state.recording_mode = True
                st.session_state.audio_data = None
                st.session_state.temp_transcript = ""
                st.rerun()

# Handles question input and response
def text_input_section():
    question = st.text_input("Type your question here", key="question_input", placeholder="Ask anything...")
    if st.button("Submit", key="submit_text") and question:
        answer = ask_question(question)
        if answer:
            del st.session_state["question_input"]
            st.rerun()

# Displays conversation history
def display_chat_history():
    if not st.session_state.chat_history:
        st.info("No conversation history yet. Ask a question to get started!")
        return

    if st.session_state.current_chat_id:
        current_chat_messages = [
            msg for msg in st.session_state.chat_history 
            if 'chat_id' not in msg or msg.get('chat_id') == st.session_state.current_chat_id
        ]
    else:
        current_chat_messages = st.session_state.chat_history

    if not current_chat_messages:
        st.info("No messages in this chat. Ask a question to get started!")
        return

    # Sort by timestamp
    try:
        sorted_messages = sorted(
            current_chat_messages,
            key=lambda x: datetime.strptime(x['timestamp'], r'%Y-%m-%d %H:%M:%S.%f')
        )
    except KeyError:
        sorted_messages = current_chat_messages  # Fallback if no timestamp

    # Group messages by timestamp (assumes same timestamp = paired user/bot)
    grouped = defaultdict(list)
    for msg in sorted_messages:
        ts = msg['timestamp']
        grouped[ts].append(msg)

    st.markdown("### Conversation History")
    chat_container = st.container()
    with chat_container:
        for ts, msgs in grouped.items():
            user_msg = next((m for m in msgs if m["role"] == "user"), None)
            bot_msg = next((m for m in msgs if m["role"] == "assistant"), None)

            if user_msg:
                st.markdown(f"""
                <div class="message-container user-message">
                    {user_msg["content"]}
                </div>
                """, unsafe_allow_html=True)

            if bot_msg:
                st.markdown(f"""
                <div class="message-container bot-message">
                    {bot_msg["content"]}
                </div>
                """, unsafe_allow_html=True)

def combined_input_section():
    """Combined input section with toggle between text and speech"""
    st.markdown("<div class='sub-header'>Ask a Question</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Text Input", key="text_btn", use_container_width=True, type="primary" if st.session_state.input_method == "text" else "secondary"):
            st.session_state.input_method = "text"
            st.session_state.audio_data = None
            st.session_state.temp_transcript = ""
            st.rerun()
    with col2:
        if st.button("Speech Input", key="speech_btn", use_container_width=True, type="primary" if st.session_state.input_method == "speech" else "secondary"):
            st.session_state.input_method = "speech"
            st.rerun()
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    if st.session_state.input_method == "text":
        text_input_section()
    else:
        audio_input_section()

    display_chat_history()

# Request new chats and view old chats
def display_sidebar_prompts():
    if st.sidebar.button("New Chat", key="new_chat_btn", help="Start a new conversation", use_container_width=True, type="primary"):
        st.session_state.current_chat_id = f"{st.session_state.username}_{datetime.now(timezone.utc).strftime(r'%d%m%Y%H%M%S%f')}"
        st.rerun()
    
    st.sidebar.markdown("### Your Chats")
    chat_groups = {}
    for msg in st.session_state.chat_history:
        chat_id = msg.get('chat_id')
        if not chat_id:
            continue
        if chat_id not in chat_groups and msg['role'] == 'user':
            chat_groups[chat_id] = msg
            
    st.session_state.chat_groups = chat_groups
    
    if chat_groups:
        for chat_id, first_msg in sorted(chat_groups.items(), key=lambda x: x[0], reverse=True):
            shortened_text = first_msg["content"][:50] + "..." if len(first_msg["content"]) > 50 else first_msg["content"]
            is_selected = st.session_state.current_chat_id == chat_id
            time = datetime.strptime(first_msg['timestamp'], r'%Y-%m-%d %H:%M:%S.%f')
            first_msg_ts = time.replace(tzinfo=from_zone).astimezone(to_zone).strftime('%H:%M')
            container_style = "active-chat" if is_selected else ""
            with st.sidebar.container():
                st.markdown(f"<div class='{container_style}'>", unsafe_allow_html=True)
                col1, col2 = st.sidebar.columns([4, 1])
                with col1:
                    if st.button(shortened_text, key=f"chat_btn_{chat_id}",help=f"View this conversation", use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                with col2:
                    st.markdown(f"<p style='font-size: 0.7em; color: #888; text-align: right;'>{first_msg_ts}</p>", 
                               unsafe_allow_html=True)
                st.markdown("</div><hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
    else:
        st.sidebar.info("No previous chats found.")

def main():
    ensure_user_db_exists()
    st.markdown("<div class='main-header'>NYP AI Chatbot Helper</div>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        login()
        return
    
    if st.session_state.logged_in:
        with st.container():
            st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.current_chat_id = None
            st.session_state.chat_history = []
            st.session_state.chat_groups = {}
            st.rerun()

    display_sidebar_prompts()

    tab1, tab2, tab3 = st.tabs(["Ask Questions", "File Upload", "Data Classification"])
    with tab1:
        combined_input_section()
    with tab2:
        file_upload_section()
    with tab3:
        file_classification_section()

if __name__ == "__main__":
    main()
