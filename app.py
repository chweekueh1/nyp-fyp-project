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
from dataProcessing import dataProcessing, initialiseDatabase, ExtractText
from datetime import datetime, timezone
import shutil
from classificationModel import classify_text
from utils import rel2abspath
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

CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
DATABASE_PATH = os.getenv("DATABASE_PATH", ".\\data\\vector_store\\chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_SESSIONS_PATH = rel2abspath(os.getenv('CHAT_SESSIONS_PATH'))
USER_DB_PATH = os.path.join(os.getenv("CHAT_DATA_PATH"),"users.json")

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
if not os.path.exists(CHAT_SESSIONS_PATH):
    os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)
    logging.info(f"Created conversations directory at {CHAT_SESSIONS_PATH}")

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

# Helper function that retrieves the path to a chat-specific history file
def ensure_user_folder_file_exists(username, chat_id):
    # Creates a folder for the user if it doesn't exist.
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    os.makedirs(user_folder, exist_ok=True)
    chat_file = os.path.join(user_folder, f"{chat_id}.json")
    return chat_file

def save_message(username, chat_id, message):
    history_file = ensure_user_folder_file_exists(username, chat_id)
    try:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []
        history.append(message)
        with open(history_file, "w") as f: 
            json.dump(history, f, indent=2)
        logging.info(f"Message saved to chat {chat_id}")
        return True
    except Exception as e:
        logging.error(f"Error saving message to chat {chat_id}: {str(e)}")
        return False

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
        data = request.json
        if not data:
            logging.warning("No data provided in request.")
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        chat_id = data.get('chat_id')
        username = data.get('username')

        if not question:
            logging.warning("No question provided in request.")
            return jsonify({'error': 'No question provided'}), 400

        # Sanitize user input
        sanitized_question = sanitize_input(question)
        logging.info(f"Received question from {username}: {sanitized_question}")
        question_time = datetime.now(timezone.utc).strftime(r'%Y-%m-%d %H:%M:%S.%f')

        try:
            # Get answer from model with conversation history
            response = get_convo_hist_answer(sanitized_question, chat_id)
            context = response['context']
            answer = response['answer']
            logging.info("Context: %s", context)
            logging.info("Question answered: %s", sanitized_question)
        except Exception as e:
            logging.error(f"Error generating answer: {str(e)}")
            answer = "I'm having trouble processing your question. Please try again later."
        answer_time = datetime.now(timezone.utc).strftime(r'%Y-%m-%d %H:%M:%S.%f')

        user_message = {"role": "user", "content": question, "timestamp": question_time, "chat_id": chat_id}
        bot_message = {"role": "assistant", "content": answer, "timestamp": answer_time, "chat_id": chat_id}
        save_message(username, chat_id, user_message)
        save_message(username, chat_id, bot_message)
        
        return jsonify({'answer': answer, 'user_message': user_message, 'bot_message': bot_message}), 200
    except Exception as e:
        logging.error("Error in /ask endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Audio transcription route
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
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
            transcript_text = ""
            try:
                with open(temp_path, "rb") as audio:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio
                    )
                transcript_text = transcript.text
            except Exception as whisper_e:
                logging.error(f"OpenAI transcription failed: {str(whisper_e)}")
                transcript_text = "This is a placeholder transcript. In production, your speech would be converted to text."
            logging.info(f"Transcription result: {transcript_text[:50]}...")
            
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            return jsonify({"transcript": transcript_text}), 200
            
        except Exception as e:
            logging.error(f"Error in transcription: {str(e)}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            
    except Exception as e:
        logging.error(f"Error in /transcribe endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    logging.info("Starting Flask application on port 5001.")
    app.run(port=5001, debug=False)
    print(app.url_map)