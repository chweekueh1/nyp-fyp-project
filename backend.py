from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import logging
import traceback
import html
import re
import secrets
import uuid
import time
import string
import magic
import zipfile
import tempfile
from openai import OpenAI
import mimetypes
import json
from unstructured.partition.common import UnsupportedFileFormatError
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from llm.dataProcessing import dataProcessing, initialiseDatabase, ExtractText # Assuming these are available
from datetime import datetime, timezone
import shutil
from llm.classificationModel import classify_text # Assuming this is available
from utils import rel2abspath # Assuming this is available
from llm.chatModel import get_convo_hist_answer # Assuming this is available

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# --- Configuration and Initialization ---
# Environment variables with sensible defaults and path resolution
CHAT_DATA_PATH = rel2abspath(os.getenv("CHAT_DATA_PATH", os.path.expanduser("~/.nypai-chatbot/data")))
DATABASE_PATH = rel2abspath(os.getenv("DATABASE_PATH", os.path.join(CHAT_DATA_PATH, "vector_store", "chroma_db")))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_SESSIONS_PATH = rel2abspath(os.getenv('CHAT_SESSIONS_PATH', os.path.join(CHAT_DATA_PATH, "chat_sessions")))
USER_DB_PATH = os.path.join(CHAT_DATA_PATH, "user_info", "users.json") # rel2abspath not strictly needed here if CHAT_DATA_PATH is already absolute

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY environment variable not set. Please set it in your .env file.")
    # In a production environment, you might want to exit or raise a more severe error
    # raise ValueError("OPENAI_API_KEY environment variable not set.")
    # For demonstration, we'll continue but log the error.
    client = None # Set client to None if API key is missing
else:
    client = OpenAI(api_key=OPENAI_API_KEY)


# Ensure directories exist
os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)
logging.info(f"Initialized chat sessions directory at {CHAT_SESSIONS_PATH}")

# Initialize Chroma DB
try:
    classification_db = Chroma(
        collection_name='classification',
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=DATABASE_PATH
    )
    if len(classification_db.get()['documents']) == 0:
        logging.info("Classification database is empty. Initializing database...")
        initialiseDatabase()
    logging.info("Chroma classification database initialized.")
except Exception as e:
    logging.error(f"Failed to initialize Chroma database: {e}")
    # Depending on criticality, you might want to exit the application here
    # sys.exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # Limit upload size to 25MB

logging.info("Flask application initialized.")

# --- Helper Functions ---

def sanitize_input(input_text):
    """
    Sanitizes user input to prevent common security vulnerabilities like XSS.
    Limits input length to prevent excessive resource usage.
    """
    if not isinstance(input_text, str):
        return "" # Or raise an error, depending on desired behavior
    sanitized = html.escape(input_text.strip())
    # Further restrict characters if needed, but be careful not to remove legitimate input
    # This regex removes anything not alphanumeric, space, dot, comma, exclamation, question mark, apostrophe, or hyphen
    sanitized = re.sub(r"[^a-zA-Z0-9\s\.,!?'-]", "", sanitized)
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
        logging.warning(f"Input truncated due to excessive length: {input_text[:50]}...")
    return sanitized

def transcribe_audio_file(audio_path):
    """
    Transcribes an audio file using OpenAI's Whisper model.
    """
    if not client:
        raise RuntimeError("OpenAI client not initialized. API key might be missing.")
    try:
        with open(audio_path, "rb") as audio_file:
            logging.info(f"Attempting to transcribe audio file: {audio_path}")
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            logging.info(f"Transcription successful for {os.path.basename(audio_path)}. Text: {transcript.text[:50]}...")
            return transcript.text
    except Exception as e:
        logging.error(f"Error transcribing audio file '{audio_path}': {str(e)}", exc_info=True)
        raise

def generate_unique_filename(original_filename, username, file_extension):
    """
    Generates a unique and secure filename using original filename, username,
    timestamp, and a random ID.
    """
    base_filename = os.path.splitext(secure_filename(original_filename))[0]
    # Remove underscores from the base_filename if specifically disallowed
    base_filename = base_filename.replace('_', '')
    
    alphabet = string.ascii_letters + string.digits
    random_id = ''.join(secrets.choice(alphabet) for _ in range(8))
    time_id = int(time.time_ns()) # Use int for nanoseconds
    
    # Ensure file_extension starts with a dot
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
        
    final_filename = f'{base_filename}_{username}_{time_id}_{random_id}{file_extension}'
    return final_filename

def detect_file_type(file_path):
    """
    Detects file type using python-magic and mimetypes, with special handling for
    Office files that might be misidentified as zip files.
    Returns a tuple: (mime_type, file_extension)
    """
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    file_extension = mimetypes.guess_extension(mime_type)

    # Special handling for Office files detected as zip
    if file_extension == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                zip_contents = z.namelist()

                if any(f.startswith("ppt") for f in zip_contents):
                    file_extension = ".pptx"
                    mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                elif any(f.startswith("word") for f in zip_contents):
                    file_extension = ".docx"
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif any(f.startswith("xl") for f in zip_contents):
                    file_extension = ".xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except zipfile.BadZipFile:
            pass # Not a valid zip, or not an office zip

    # Fallback for common types if mimetypes.guess_extension fails or is generic
    if not file_extension and mime_type:
        if 'pdf' in mime_type:
            file_extension = '.pdf'
        elif 'text' in mime_type:
            file_extension = '.txt'
        elif 'image' in mime_type:
            file_extension = f".{mime_type.split('/')[-1]}" # e.g., .jpeg, .png
        # Add more specific fallbacks as needed

    return mime_type, file_extension

def ensure_chat_history_file_exists(username, chat_id):
    """
    Ensures the user's chat history folder and specific chat file exist.
    Returns the path to the chat history JSON file.
    """
    user_folder = os.path.join(CHAT_SESSIONS_PATH, sanitize_input(username)) # Sanitize username for path safety
    os.makedirs(user_folder, exist_ok=True)
    chat_file = os.path.join(user_folder, f"{sanitize_input(str(chat_id))}.json") # Sanitize chat_id too
    return chat_file

def save_chat_message(username, chat_id, message):
    """
    Appends a message to the specified chat history file.
    """
    history_file = ensure_chat_history_file_exists(username, chat_id)
    try:
        history = []
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        
        history.append(message)
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
        logging.info(f"Message saved to chat {chat_id} for user {username}.")
        return True
    except Exception as e:
        logging.error(f"Error saving message to chat {chat_id} for user {username}: {str(e)}", exc_info=True)
        return False

# --- API Routes ---

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles file uploads, processes them, and stores them.
    """
    if 'file' not in request.files:
        logging.warning("No file part in the /upload request.")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    username = request.form.get('username', 'anonymous') # Default to anonymous

    if file.filename == '':
        logging.warning(f"Empty filename provided by user {username}.")
        return jsonify({'error': 'Invalid Filename: Filename cannot be empty'}), 400

    # Specific check for underscore as per original request, applied to original filename
    # This check is performed on the original filename before any sanitization.

    original_filename = str(file.filename)
    # Use secure_filename to sanitize the filename before saving it to the filesystem.
    secured_filename = secure_filename(original_filename)
    if '_' in original_filename:
        return jsonify({'error': 'Invalid Filename: Underscores are not allowed'}), 400

    # --- IMPORTANT FIX: Early MIME type validation ---
    # This check uses the MIME type reported by the browser (file.content_type)
    # to quickly reject clearly unsupported file types before saving them to disk
    # and incurring more processing. This improves efficiency and security.
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'application/msword', # .doc
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # .docx
        'application/vnd.ms-excel', # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # .xlsx
        'application/vnd.ms-powerpoint', # .ppt
        'application/vnd.openxmlformats-officedocument.presentationml.presentation', # .pptx
        'text/plain',
        'audio/mpeg', # .mp3
        'audio/wav',
        'audio/ogg',
        'audio/aac',
        # Add any other MIME types that your 'dataProcessing' function is designed to handle.
        # This list should match the file types you intend to support.
    ]
    if file.content_type not in ALLOWED_MIME_TYPES:
        logging.warning(f"Unsupported MIME type '{file.content_type}' for file '{file.filename}'.")
        return jsonify({'error': f'Unsupported file type: {file.content_type}'}), 400

    temp_directory = os.path.join(CHAT_DATA_PATH, 'temp', str(uuid.uuid4()))
    os.makedirs(temp_directory, exist_ok=True)
    file_path = os.path.join(temp_directory, secured_filename) # Use the secured_filename here
    
    # The rest of your function (file.save(), dataProcessing, etc.) would follow here
    # within a try-finally block to ensure proper cleanup of temp_directory.
    try:
        file.save(file_path)
        logging.info(f"File '{original_filename}' saved temporarily to {file_path}")

        # Process data
        dataProcessing(file_path) # This function should handle adding to vector store
        logging.info(f"Data processing completed for '{original_filename}'.")
        
        # Detect file type and move to categorized folder
        mime_type, file_extension = detect_file_type(file_path) # Assuming detect_file_type exists as defined in previous response
        
        if not file_extension:
            logging.warning(f"Could not determine a valid file extension for '{original_filename}'. MIME: {mime_type}")
            return jsonify({'error': 'Could not determine file type or extension'}), 400

        # Remove leading dot from extension for directory naming
        dir_name = file_extension[1:] if file_extension.startswith('.') else file_extension
        directory = os.path.join(CHAT_DATA_PATH, f'{dir_name}_files')
        os.makedirs(directory, exist_ok=True)
        
        new_file_name = generate_unique_filename( # Assuming generate_unique_filename exists
            original_filename=original_filename, 
            username=sanitize_input(username), # Assuming sanitize_input exists
            file_extension=file_extension
        )
        full_destination_path = os.path.join(directory, new_file_name)
        shutil.copy(file_path, full_destination_path)
        logging.info(f"File moved to permanent location: {full_destination_path}")

        return jsonify({'status': 'File uploaded and text extracted', 'filename': new_file_name, 'file_type': file_extension}), 200
        
    except UnsupportedFileFormatError:
        logging.warning(f"Unsupported file format for upload: {original_filename}")
        return jsonify({'error': 'Unsupported file type'}), 400
    except Exception as e:
        logging.error(f"Error during file upload process for '{original_filename}': {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_directory):
            shutil.rmtree(temp_directory)
            logging.info(f"Cleaned up temporary directory: {temp_directory}")

@app.route('/classify', methods=['POST'])
def data_classification():
    """
    Handles data classification for uploaded files.
    """
    if 'file' not in request.files:
        logging.warning("No file part in the /classify request.")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    username = request.form.get('username', 'anonymous') # Default to anonymous

    if file.filename == '':
        logging.warning(f"Empty filename provided for classification by user {username}.")
        return jsonify({'error': 'Invalid Filename: Filename cannot be empty'}), 400
        
    original_filename = str(file.filename)
    temp_directory = os.path.join(CHAT_DATA_PATH, 'temp', 'classification', str(uuid.uuid4()))
    os.makedirs(temp_directory, exist_ok=True)
    file_path = os.path.join(temp_directory, secure_filename(original_filename))
    
    try:
        file.save(file_path)
        logging.info(f"File '{original_filename}' saved temporarily for classification to {file_path}")

        document_parts = ExtractText(file_path) # This returns a list of documents
        if not document_parts:
            logging.warning(f"No text extracted from file '{original_filename}' for classification.")
            return jsonify({'error': 'Could not extract text from file'}), 400

        # Assuming classify_text can take a single string, concatenate all page content
        content = " ".join([doc.page_content for doc in document_parts])
        
        if not content.strip():
            logging.warning(f"Extracted content is empty for file '{original_filename}'.")
            return jsonify({'error': 'Extracted content is empty, cannot classify'}), 400

        response = classify_text(content)
        logging.info(f"Classification successful for '{original_filename}'. Result: {response.get('answer', 'N/A')}")
        
        return jsonify({'answer': response.get('answer', 'Classification failed or returned no answer.')}), 200

    except UnsupportedFileFormatError:
        logging.warning(f"Unsupported file format for classification: {original_filename}")
        return jsonify({'error': 'Unsupported file type'}), 400
    except Exception as e:
        logging.error(f"Error during data classification process for '{original_filename}': {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    finally:
        if os.path.exists(temp_directory):
            shutil.rmtree(temp_directory)
            logging.info(f"Cleaned up temporary classification directory: {temp_directory}")

@app.route('/ask', methods=['POST'])
def ask_question():
    """
    Answers a user's question, leveraging conversation history.
    """
    try:
        data = request.json
        if not data:
            logging.warning("No JSON data provided in /ask request.")
            return jsonify({'error': 'No data provided'}), 400
            
        question = data.get('question')
        chat_id = data.get('chat_id')
        username = data.get('username')

        # Validate essential inputs
        if not question:
            logging.warning("No 'question' provided in /ask request.")
            return jsonify({'error': 'No question provided'}), 400
        if not chat_id:
            logging.warning("No 'chat_id' provided in /ask request.")
            return jsonify({'error': 'No chat_id provided'}), 400
        if not username:
            logging.warning("No 'username' provided in /ask request.")
            # Consider a default or reject if username is mandatory for history
            username = "guest"
            logging.info("Using 'guest' as username for /ask request due to missing username.")


        sanitized_question = sanitize_input(question)
        logging.info(f"Received question from {username} (Chat ID: {chat_id}): '{sanitized_question}'")
        question_time = datetime.now(timezone.utc).isoformat() # ISO format is better for timestamps

        answer = "I'm having trouble processing your question. Please try again later."
        context = [] # Initialize context

        try:
            response = get_convo_hist_answer(sanitized_question, chat_id)
            context = response.get('context', [])
            answer = response.get('answer', answer) # Use default answer if not found
            logging.info(f"Answer generated for user {username} (Chat ID: {chat_id}).")
        except Exception as e:
            logging.error(f"Error generating answer for user {username} (Chat ID: {chat_id}): {str(e)}", exc_info=True)
            # 'answer' remains the default error message

        answer_time = datetime.now(timezone.utc).isoformat()

        user_message = {"role": "user", "content": question, "timestamp": question_time, "chat_id": chat_id}
        bot_message = {"role": "assistant", "content": answer, "timestamp": answer_time, "chat_id": chat_id}
        
        # Save messages, handle potential failure
        if not save_chat_message(username, chat_id, user_message):
            logging.error(f"Failed to save user message for chat {chat_id}.")
        if not save_chat_message(username, chat_id, bot_message):
            logging.error(f"Failed to save bot message for chat {chat_id}.")
            
        return jsonify({
            'answer': answer, 
            'user_message': user_message, 
            'bot_message': bot_message,
            'context': context # Optionally return context for debugging/UI
        }), 200
        
    except Exception as e:
        logging.error(f"Unhandled error in /ask endpoint: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route("/transcribe", methods=["POST"])
def transcribe_audio_route(): # Renamed to avoid conflict with helper
    """
    Transcribes an uploaded audio file.
    """
    if "audio" not in request.files:
        logging.warning("No audio file provided in /transcribe request.")
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    # Use a more specific suffix and ensure tempfile is correctly used
    temp_audio_path = None
    try:
        # Create a temporary file with a recognizable extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode='wb') as temp_audio:
            audio_file.save(temp_audio)
            temp_audio_path = temp_audio.name
        
        logging.info(f"Audio saved to temporary file: {temp_audio_path}")
        
        transcript_text = transcribe_audio_file(temp_audio_path)
        
        return jsonify({"transcript": transcript_text}), 200
            
    except RuntimeError as re: # Specific for OpenAI client not initialized
        logging.error(f"Runtime error in /transcribe: {re}")
        return jsonify({"error": str(re)}), 500
    except Exception as e:
        logging.error(f"Error during audio transcription process: {traceback.format_exc()}")
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    finally:
        # Ensure temporary file is deleted
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
            logging.info(f"Cleaned up temporary audio file: {temp_audio_path}")

if __name__ == '__main__':
    # Make port configurable via environment variable
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
    logging.info(f"Starting Flask application on port {FLASK_PORT}.")
    app.run(port=FLASK_PORT, debug=False)
    # print(app.url_map) # This will print routes only if app.run() is stopped