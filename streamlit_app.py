import streamlit as st
import requests
from st_audiorec import st_audiorec
import io
import time
import base64
from audio_recorder_streamlit import audio_recorder
from app import load_history, save_message, clear_conversation

# Set page configuration
st.set_page_config(
    page_title="NYP AI Chatbot Helper",
    page_icon="🤖",
    layout="wide"
)

st.markdown('''
<style>
    .css-1egvi7u {margin-top: -3rem;}
    .stAudio {height: 45px;}
    .css-v37k9u a {color: #ff4c4b;} /* darkmode */
    .css-nlntq9 a {color: #ff4c4b;} /* lightmode */
    .main-header {
        font-size: 2rem;
        color: #0066cc;
        text-align: center;
        margin: 1rem 0 2rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0066cc;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        color: #155724;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        color: #721c24;
    }
    /* Microphone button styling */
    .microphone-button {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    
    /* Recording indicator */
    .recording-indicator {
        color: #ff4b4b;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Audio player container */
    .audio-container {
        display: flex;
        align-items: center;
        margin: 15px 0;
        padding: 10px;
        border-radius: 8px;
        background-color: #f0f2f6;
    }
    
    /* Delete button */
    .delete-button {
        color: #ff4b4b;
        cursor: pointer;
        margin-left: 10px;
    }
    
    /* Recording button styling */
    .record-button {
        background-color: #0066cc;
        color: white;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        font-size: 24px;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .record-button.recording {
        background-color: #ff4b4b;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
            
     .submit-button {
        background-color: #28a745;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 10px;
    }
    
    /* Input method selector styling */
    .input-selector {
        display: flex;
        margin-bottom: 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .input-option {
        flex: 1;
        text-align: center;
        padding: 10px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .input-option.active {
        background-color: #0066cc;
        color: white;
    }
    
    .input-option:hover:not(.active) {
        background-color: #dbe4f0;
    }
    
    /* Divider styling */
    .divider {
        margin: 20px 0;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Response container styling */
    .response-container {
        margin-top: 20px;
        padding: 15px;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
    }
    
    /* Chat message styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-top: 20px;
        padding: 10px;
        max-height: 500px;
        overflow-y: auto;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    
    .message-container {
        display: flex;
        flex-direction: column;
        max-width: 80%;
        padding: 10px 15px;
        border-radius: 15px;
        font-size: 16px;
    }
    
    .user-message {
        align-self: flex-end;
        background-color: #0066cc;
        color: white;
        border-bottom-right-radius: 5px;
    }
    
    .bot-message {
        align-self: flex-start;
        background-color: #e6f7ff;
        color: #333;
        border-bottom-left-radius: 5px;
    }
    
    .message-time {
        font-size: 12px;
        color: #888;
        align-self: flex-end;
        margin-top: 5px;
    }
    
    /* Clear history button */
    .clear-button {
        color: #ff4b4b;
        background-color: transparent;
        border: 1px solid #ff4b4b;
        border-radius: 5px;
        padding: 5px 10px;
        cursor: pointer;
        transition: all 0.3s;
        margin-top: 10px;
    }
    
    .clear-button:hover {
        background-color: #ff4b4b;
        color: white;
    }
    
    .sidebar .message-container {
        max-width: 100%;
        padding: 8px 10px;
        margin-bottom: 8px;
        font-size: 14px;
    }

    .sidebar .message-time {
        font-size: 10px;
    }

    /* Make sidebar scrollable if needed */
    .sidebar .stSidebar {
        max-height: 80vh;
        overflow-y: auto;
    }
    
    /* Clickable prompt in sidebar */
    .sidebar-prompt {
        cursor: pointer;
        padding: 8px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: #f0f2f6;
        border-left: 3px solid #0066cc;
        transition: all 0.2s;
    }
    
    .sidebar-prompt:hover {
        background-color: #e2e8f0;
    }
    
    .sidebar-prompt-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 14px;
    }
</style>
''', unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
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
    st.session_state.input_method = "text"  # Default to text input
if 'question_input' not in st.session_state:
    st.session_state.question_input = ""
# Chat history storage
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
# Session ID for tracking conversation with backend
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(int(time.time()))  # Simple timestamp-based session ID
# Selected conversation for viewing
if 'selected_message_index' not in st.session_state:
    st.session_state.selected_message_index = -1

# API Configuration
API_URL = "http://127.0.0.1:5001"

def login():
    # st.markdown("<div class='main-header'>NYP CNC AI Chatbot</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login"):
            if username == "staff" and password == "123":
                st.session_state.logged_in = True
                st.session_state.username = username
                # Load conversation history from persistent storage
                st.session_state.chat_history = load_history(username)
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")

def handle_api_request(endpoint, method="post", data=None, files=None, json=None):
    """Generic function to handle API requests with error handling"""
    try:
        if method.lower() == "post":
            response = requests.post(f"{API_URL}/{endpoint}", data=data, files=files, json=json, timeout=30)
        else:
            response = requests.get(f"{API_URL}/{endpoint}", params=data, timeout=30)
        
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to server. Is the backend running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out. The server might be busy."
    except requests.exceptions.HTTPError as e:
        try:
            error_msg = response.json().get("error", str(e))
        except:
            error_msg = str(e)
        return None, f"HTTP Error: {error_msg}"
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}"

def ask_question(question):
    """Send question to backend and get answer"""
    with st.spinner("Getting answer..."):
        # Include session ID in payload
        payload = {
            "question": question,
            "session_id": st.session_state.session_id
        }
        result, error = handle_api_request("ask", json=payload)
        
        if error:
            st.error(error)
            return None
        
        # Current timestamp for message time
        current_time = time.strftime("%H:%M")
        
        # Add to chat history
        user_message = {"role": "user", "content": question, "time": current_time}
        st.session_state.chat_history.append(user_message)
        
        answer = result.get("answer")
        bot_message = {"role": "assistant", "content": answer, "time": current_time}
        st.session_state.chat_history.append(bot_message)
        
        # Save to persistent storage
        if st.session_state.username:
            save_message(st.session_state.username, user_message)
            save_message(st.session_state.username, bot_message)
        
        return answer

def transcribe_and_process_audio(audio_data):
    """Send audio to backend for transcription only"""
    with st.spinner("Processing your audio..."):
        audio_bytes = io.BytesIO(audio_data)
        files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
        result, error = handle_api_request("transcribe", files=files)
        
        if error:
            st.error(error)
            return False
        
        return True

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


def file_upload_section():
    failure = 0

    """Handle file upload"""
    with st.form('Upload file(s)', clear_on_submit=True):
        uploaded_files = st.file_uploader("Choose a file", type=[
        'bmp', 'csv', 'doc', 'docx', 'eml', 'epub', 'heic', 'html',
        'jpeg', 'jpg', 'png', 'md', 'msg', 'odt', 'org', 'p7s', 'pdf',
        'ppt', 'pptx', 'rst', 'rtf', 'tiff', 'txt', 'tsv', 'xls', 'xlsx', 'xml'
        ]
        , accept_multiple_files=True)
    
        submitted = st.form_submit_button('Upload')

        if submitted and uploaded_files is not None:
            for uploaded_file in uploaded_files:
                if not upload_file(uploaded_file):
                    failure += 1
            success = len(uploaded_files) - failure
            st.success(f'Uploaded {success} file(s) successfully, {failure} file(s) failed')


def audio_input_section():
    """Audio recording section with automatic recording and transcript correction"""
    # Only show the recorder if no audio is recorded yet or if we're in "re-record" mode
    if not st.session_state.audio_data or 'recording_mode' in st.session_state and st.session_state.recording_mode:
        audio_bytes = audio_recorder(
            pause_threshold=100000,
            recording_color="#ff4b4b",
            neutral_color="#0066cc",
            icon_size="2.5x"
        )
        
        # Save recording once done
        if audio_bytes:
            st.session_state.audio_data = audio_bytes
            st.session_state.recording_mode = False
            
            # Immediately transcribe the audio
            with st.spinner("Transcribing your audio..."):
                # Send only for transcription
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Submit", key="submit_transcript"):
                if corrected_transcript:
                    # Use the regular ask_question function which now handles chat history
                    answer = ask_question(corrected_transcript)
                    if answer:
                        # Clear audio after successful submission
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

def text_input_section():
    """Handle question input and response"""
    question = st.text_input("Enter your question", key="question_input", placeholder="Ask anything...")
    
    if st.button("Submit", key="submit_text") and question:
        answer = ask_question(question)
        if answer:
            st.rerun()

def display_chat_history():
    """Display the chat history in a conversational format"""
    if not st.session_state.chat_history:
        st.info("No conversation history yet. Ask a question to get started!")
        return
    
    # st.markdown("### Conversation History")

    if st.session_state.selected_message_index >= 0:
        user_message = st.session_state.chat_history[st.session_state.selected_message_index]
        bot_message = None
        if st.session_state.selected_message_index + 1 < len(st.session_state.chat_history):
            next_message = st.session_state.chat_history[st.session_state.selected_message_index + 1]
            if next_message["role"] == "assistant":
                bot_message = next_message
        
        st.markdown(f"""
        <div class="message-container user-message">
            {user_message["content"]}
            <div class="message-time">{user_message["time"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if bot_message:
            st.markdown(f"""
            <div class="message-container bot-message">
                {bot_message["content"]}
                <div class="message-time">{bot_message["time"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # if st.button("Back to All Messages"):
        #     st.session_state.selected_message_index = -1
        #     st.rerun()
    # else:
    #     chat_container = st.container()
        
    #     with chat_container:
    #         for message in st.session_state.chat_history:
    #             if message["role"] == "user":
    #                 st.markdown(f"""
    #                 <div class="message-container user-message">
    #                     {message["content"]}
    #                     <div class="message-time">{message["time"]}</div>
    #                 </div>
    #                 """, unsafe_allow_html=True)
    #             else:
    #                 st.markdown(f"""
    #                 <div class="message-container bot-message">
    #                     {message["content"]}
    #                     <div class="message-time">{message["time"]}</div>
    #                 </div>
    #                 """, unsafe_allow_html=True)

def combined_input_section():
    st.markdown("<div class='sub-header'>Ask a Question</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Text Input", key="text_btn", 
                     use_container_width=True,
                     type="primary" if st.session_state.input_method == "text" else "secondary"):
            st.session_state.input_method = "text"
            st.session_state.audio_data = None
            st.session_state.temp_transcript = ""
            st.rerun()
    
    with col2:
        if st.button("Speech Input", key="speech_btn", 
                     use_container_width=True,
                     type="primary" if st.session_state.input_method == "speech" else "secondary"):
            st.session_state.input_method = "speech"
            st.rerun()
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    if st.session_state.input_method == "text":
        text_input_section()
    else:
        audio_input_section()
    
    display_chat_history()

def display_sidebar_prompts():
    st.sidebar.markdown("### Your Questions")

    user_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
    
    if user_messages:
        for i, msg in enumerate([m for m in st.session_state.chat_history if m["role"] == "user"]):
            full_index = st.session_state.chat_history.index(msg)
            
            prompt_id = f"prompt_{i}"
            shortened_text = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            st.sidebar.markdown(f"""
            <div class="sidebar-prompt" id="{prompt_id}" onclick="handlePromptClick('{prompt_id}')" data-index="{full_index}">
                <div class="sidebar-prompt-text">{shortened_text}</div>
                <div class="message-time">{msg["time"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.sidebar.button(f"View {i}", key=f"view_btn_{i}", help=f"View conversation for '{shortened_text}'"):
                st.session_state.selected_message_index = full_index
                st.rerun()
        
        st.sidebar.markdown("""
        <script>
        function handlePromptClick(id) {
            const element = document.getElementById(id);
            const index = element.getAttribute('data-index');
            const buttonId = `view_btn_${id.split('_')[1]}`;
            document.getElementById(buttonId).click();
        }
        </script>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.info("No questions asked yet.")

def main():
    st.markdown("<div class='main-header'>NYP AI Chatbot Helper</div>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        login()
        return
    
    display_sidebar_prompts()
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.sidebar.markdown(f"**Session ID:** {st.session_state.session_id}")
    st.sidebar.markdown(f"**User:** {st.session_state.username}")

    tab1, tab2 = st.tabs(["Ask Questions", "File Upload"])
    
    with tab1:
        combined_input_section()
    
    with tab2:
        file_upload_section()

if __name__ == "__main__":
    main()