import streamlit as st
import requests
from st_audiorec import st_audiorec
import io
import time
import base64
from audio_recorder_streamlit import audio_recorder

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
    .css-v37k9u a {color: #ff4c4b;} /* darkmode */
    .css-nlntq9 a {color: #ff4c4b;} /* lightmode */
    .main-header {
        font-size: 2.5rem;
        color: #0066cc;
        margin-bottom: 1rem;
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
</style>
''', unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'answer' not in st.session_state:
    st.session_state.answer = ""
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None
if 'recorder' not in st.session_state:
    st.session_state.recorder = None

# API Configuration
API_URL = "http://127.0.0.1:5001"

def login():
    with st.sidebar:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login"):
            if username == "staff" and password == "123":
                st.session_state.logged_in = True
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

def transcribe_and_process_audio(audio_data):
    """Send audio to backend for transcription and processing"""
    with st.spinner("Processing your audio..."):
        audio_bytes = io.BytesIO(audio_data)
        files = {"audio": ("recording.wav", audio_bytes, "audio/wav")}
        result, error = handle_api_request("transcribe_and_process", files=files)
        
        if error:
            st.error(error)
            return None, None
        
        return result.get("transcript"), result.get("response")

def upload_file(file):
    """Upload file to backend"""
    with st.spinner("Uploading and processing file..."):
        files = {"file": file}
        result, error = handle_api_request("upload", files=files)
        
        if error:
            st.error(error)
            return False
        
        return True

def audio_recorder_section():
    """Audio recording section with automatic recording"""
    st.markdown("<div class='sub-header'>Speech-to-Text</div>", unsafe_allow_html=True)

    # Automatically show recorder
    audio_bytes = audio_recorder(
        pause_threshold=100000,
        recording_color="#ff4b4b",
        neutral_color="#0066cc",
        icon_size="1.5x"
    )

    # Save recording once done
    if audio_bytes:
        st.session_state.audio_data = audio_bytes

    # Display audio player and submit/delete options if audio is recorded
    if st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format='audio/wav')

        if st.button("Submit Recording", key="submit_recording"):
            with st.spinner("Processing your recording..."):
                transcript, ai_response = transcribe_and_process_audio(st.session_state.audio_data)
                if transcript:
                    st.session_state.transcript = transcript
                    st.session_state.ai_response = ai_response
                    st.rerun()

        if st.button("Delete Recording", key="delete_btn"):
            st.session_state.audio_data = None
            st.session_state.transcript = ""
            st.session_state.ai_response = None
            st.rerun()

    # Display transcript and AI response
    if st.session_state.transcript:
        st.markdown("### Your Question")
        st.markdown(f'<div style="padding: 10px; border-radius: 5px; background-color: #f0f2f6;">{st.session_state.transcript}</div>', unsafe_allow_html=True)

    if st.session_state.ai_response:
        st.markdown("### AI Response")
        st.markdown(f'<div style="padding: 10px; border-radius: 5px; background-color: #e6f7ff;">{st.session_state.ai_response}</div>', unsafe_allow_html=True)


def file_upload_section():
    """Handle file upload"""
    st.markdown("<div class='sub-header'>Upload a File</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "xlsx", "pptx", "jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        if upload_file(uploaded_file):
            st.success("File uploaded and processed successfully!")

def question_section():
    """Handle question input and response"""
    st.markdown("<div class='sub-header'>Ask a Question</div>", unsafe_allow_html=True)
    
    # Use session state to remember the question
    if 'question_input' not in st.session_state:
        st.session_state.question_input = ""
    
    # Text input for question
    question = st.text_input("Enter your question", value=st.session_state.question_input)
    
    if st.button("Submit Question") and question:
        answer = ask_question(question)
        if answer:
            st.session_state.answer = answer
            st.markdown(f"<div class='success-message'><strong>Answer:</strong> {answer}</div>", unsafe_allow_html=True)

def ask_question(question):
    """Send question to backend and get answer"""
    with st.spinner("Getting answer..."):
        payload = {"question": question}
        result, error = handle_api_request("ask", json=payload)
        
        if error:
            st.error(error)
            return None
        
        return result.get("answer")

def main():
    st.markdown("<div class='main-header'>NYP AI Chatbot Helper</div>", unsafe_allow_html=True)

    # Check login status
    if not st.session_state.logged_in:
        login()
        return
    
    # Show logout button when logged in
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["Speech Input", "Text Input", "File Upload"])
    
    with tab1:
        audio_recorder_section()
    
    with tab2:
        question_section()
    
    with tab3:
        file_upload_section()

if __name__ == "__main__":
    main()