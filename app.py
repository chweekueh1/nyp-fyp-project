from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os, logging, traceback, html
import re, secrets, uuid, time, string
import magic, zipfile, tempfile
import mimetypes, json, shutil

from unstructured.partition.common import UnsupportedFileFormatError
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from dataProcessing import dataProcessing, initialiseDatabase, ExtractText
from classificationModel import classify_text
from chatModel import get_convo_hist_answer

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_DATA_PATH = os.getenv('CHAT_DATA_PATH')
DATABASE_PATH = os.getenv("DATABASE_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

classification_db = Chroma(
    collection_name = 'classification',
    embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    persist_directory=DATABASE_PATH
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # Limit upload size to 25MB

# Ensure 'uploads' folder exists
if len(classification_db.get()['documents']) == 0:
    initialiseDatabase()

logging.info("Flask application initialized. Upload folder set up at %s", CHAT_DATA_PATH)

# Create conversations directory if it doesn't exist
CONVERSATIONS_DIR = "conversations"
if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)
    logging.info(f"Created conversations directory at {CONVERSATIONS_DIR}")

# Updated history management functions to handle user-specific histories
def get_user_history_file(username):
    """Get the path to a user's conversation history file"""
    return os.path.join(CONVERSATIONS_DIR, f"{username}_history.json")

def save_message(username, message):
    """Save a message to a user's conversation history"""
    history_file = get_user_history_file(username)
    
    try:
        # Load existing history if it exists
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []
    
        history.append(message)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
        
        logging.info(f"Message saved to {username}'s history")
        return True
    except Exception as e:
        logging.error(f"Error saving message for {username}: {str(e)}")
        return False

# Helper function to load a user's conversation history
def load_history(username):
    history_file = get_user_history_file(username)
    try:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logging.error(f"Error loading history for {username}: {str(e)}")
        return []

def save_message_global(sender, message):
    new_entry = {
        "sender": sender,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        with open(HISTORY_FILE, "r+") as f:
            history = json.load(f)
            history.append(new_entry)
            f.seek(0)
            json.dump(history, f, indent=2)
    except FileNotFoundError:
        with open(HISTORY_FILE, "w") as f:
            json.dump([new_entry], f, indent=2)

def load_history_global():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def clear_conversation_global():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

# Helper function to sanitize user input
def sanitize_input(input_text):
    sanitized = html.escape(input_text)
    sanitized = re.sub(r"[^a-zA-Z0-9\s\.,!?'-]", "", sanitized)
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
    return sanitized

# Helper function to transcribe audio files
def transcribe_audio_file(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            logging.info(f"Transcribing audio file: {audio_path}")
            
            # Use the OpenAI client to transcribe audio
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
            logging.info(f"Transcription successful: {transcript.text[:50]}...")
            return transcript.text
    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        raise

def generateUniqueFilename(filename, username, filetype):
    alphabet = string.ascii_letters + string.digits
    random_id = ''.join(secrets.choice(alphabet) for i in range(8))
    time_id = time.time_ns()
    final_filename = f'{filename}_{username}_{time_id}_{random_id}{filetype}'
    return final_filename

# function to detect file type using magic and mimetypes
def detectFileType(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    file_extension = mimetypes.guess_extension(mime_type)

    # fix for Office files detected as zip
    if file_extension == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                zip_contents = z.namelist()

                if any(f.startswith("ppt") for f in zip_contents):
                    file_extension = ".pptx" 
                elif any(f.startswith("word") for f in zip_contents):
                    file_extension = ".docx"  
                elif any(f.startswith("xl") for f in zip_contents):
                    file_extension = ".xlsx"

        except zipfile.BadZipFile:
            pass

    return file_extension

# Route for file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logging.warning("No file part in the request.")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']

        if file.filename == '':
            logging.warning("Empty filename: %s", file.filename)
            return jsonify({'error': 'Invalid Filename: Filename cannot be empty'}), 400
        elif '_' in file.filename:
            return jsonify({'error': 'Invalid Filename: Underscore are not allowed'}), 400
        
        filename = secure_filename(file.filename)
        temp_directory = os.path.join(CHAT_DATA_PATH, 'temp', str(uuid.uuid4()))
        os.makedirs(temp_directory, exist_ok=True)
        file_path = os.path.join(temp_directory, filename)
        file.save(file_path)

        try:
            dataProcessing(file_path)
        except UnsupportedFileFormatError:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_type = detectFileType(file_path)
        directory = os.path.join(CHAT_DATA_PATH, f'{file_type[1:]}_files')
        os.makedirs(directory, exist_ok=True)
        username = request.form.get('username')
        new_file_name = generateUniqueFilename(filename=filename, username=username, filetype=file_type)
        full_directory = os.path.join(directory, new_file_name)
        shutil.copy(file_path, full_directory)
        shutil.rmtree(temp_directory)
        return jsonify({'status': 'File uploaded and text extracted'}), 200
    
    except Exception as e:
        logging.error("Error in /upload endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
    
# Route for data classification
@app.route('/classify', methods=['POST'])
def data_classification():
    try:
        if 'file' not in request.files:
            logging.warning("No file part in the request.")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            logging.warning("Empty filename: %s", file.filename)
            return jsonify({'error': 'Invalid Filename: Filename cannot be empty'}), 400
        
        filename = secure_filename(file.filename)
        temp_directory = os.path.join(CHAT_DATA_PATH, 'temp', 'classification', str(uuid.uuid4()))
        os.makedirs(temp_directory, exist_ok=True)
        file_path = os.path.join(temp_directory, filename)
        file.save(file_path)

        try:
            document = ExtractText(file_path)
        except UnsupportedFileFormatError:
            return jsonify({'error': 'Invalid file type'}), 400
        
        content = document[0].page_content
        response = classify_text(content)
        print(response)
        shutil.rmtree(temp_directory)
        return jsonify({'answer': response['answer']}), 200

    except Exception as e:
        logging.error("Error in /upload endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Route for question answering with conversation history
@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        question = request.json.get('question')
        session_id = request.json.get('session_id', 'default')  # Get session ID if provided
        username = request.json.get('username')  # Optional username for history
        
        if not question:
            logging.warning("No question provided in request.")
            return jsonify({'error': 'No question provided'}), 400

        # Sanitize user input
        sanitized_question = sanitize_input(question)
        logging.info("Sanitized question: %s", sanitized_question)

        # Get answer from model with conversation history
        response = get_convo_hist_answer(sanitized_question)
        logging.info("Question answered: %s", sanitized_question)
        
        # Save to specific user history if username is provided
        if username:
            user_message = {"role": "user", "content": question, "time": datetime.utcnow().strftime("%H:%M")}
            bot_message = {"role": "assistant", "content": response['answer'], "time": datetime.utcnow().strftime("%H:%M")}
            save_message(username, user_message)
            save_message(username, bot_message)
        
        # Also save to global history
        save_message_global("user", {"question": question, "session": session_id})
        save_message_global("assistant", {"answer": response['answer'], "session": session_id})
        
        return jsonify({'answer': response['answer']}), 200
    except Exception as e:
        logging.error("Error in /ask endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Simplified route for audio transcription only
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    try:
        if "audio" not in request.files:
            logging.warning("No audio file provided in request.")
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        
        # Save the audio file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
        
        logging.info(f"Audio saved to temporary file: {temp_path}")
        
        try:
            # Use the OpenAI client to transcribe the audio
            with open(temp_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            
            logging.info(f"Transcription successful: {transcript.text[:50]}...")
            os.unlink(temp_path)
            
            return jsonify({"transcript": transcript.text}), 200
        except Exception as e:
            logging.error(f"Error in transcription: {str(e)}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error in /transcribe endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/transcribe_and_process", methods=["POST"])
def transcribe_and_process():
    try:
        if "audio" not in request.files:
            logging.warning("No audio file provided in request.")
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
        
        logging.info(f"Audio saved to temporary file: {temp_path}")
        
        try:
            with open(temp_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                )
            
            transcript_text = transcript.text
            logging.info(f"Transcription successful: {transcript_text[:50]}...")
            os.unlink(temp_path)
            
            # Processes the transcript using the same method as text input
            sanitized_question = sanitize_input(transcript_text)
            response = get_convo_hist_answer(sanitized_question)
            
            return jsonify({
                "transcript": transcript_text,
                "response": response['answer']
            }), 200
        except Exception as e:
            logging.error(f"Error in transcription or processing: {str(e)}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": f"Operation failed: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error in /transcribe_and_process endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

# Updated to use the same answering method
@app.route("/process_text", methods=["POST"])
def process_text():
    try:
        data = request.json
        if not data or 'text' not in data:
            logging.warning("No text provided in request.")
            return jsonify({"error": "No text provided"}), 400

        text = data['text']
        sanitized_text = sanitize_input(text)
        logging.info(f"Processing text: {sanitized_text[:50]}...")
        response = get_convo_hist_answer(sanitized_text)
        logging.info(f"Text processed successfully")
        return jsonify({
            "response": response['answer']
        }), 200
    
    except Exception as e:
        logging.error(f"Error in /process_text endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':

    logging.info("Starting Flask application on port 5001.")
    app.run(port=5001, debug=False)
    print(app.url_map)