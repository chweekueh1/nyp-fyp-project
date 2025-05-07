from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os, logging, traceback
import html, re, secrets, json
import uuid, time, string, tempfile
import magic, zipfile, mimetypes, shutil

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

UPLOAD_FOLDER = 'uploads'
CHAT_DATA_PATH = os.getenv('CHAT_DATA_PATH')
DATABASE_PATH = os.getenv("DATABASE_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

classification_db = Chroma(
    collection_name = 'classification',
    embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    persist_directory=DATABASE_PATH
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # Limit upload size to 25MB

if len(classification_db.get()['documents']) == 0:
    initialiseDatabase()

# Create user uploads folder structure
def ensure_user_folder(username):
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

logging.info("Flask application initialized. Upload folder set up at %s", CHAT_DATA_PATH)

SESSION_HISTORY_DIR = "chat_sessions"
if not os.path.exists(SESSION_HISTORY_DIR):
    os.makedirs(SESSION_HISTORY_DIR)

# Helper function that retrieves the path to a chat-specific history file
def get_chat_history_file(chat_id):
    return os.path.join(SESSION_HISTORY_DIR, f"chat_{chat_id}.json")

def save_message(chat_id, message):
    history_file = get_chat_history_file(chat_id)
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

def load_history(chat_id):
    history_file = get_chat_history_file(chat_id)
    try:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logging.error(f"Error loading chat history for {chat_id}: {str(e)}")
        return []

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

# Generate a simple response when the ML model is unavailable
def generate_simple_response(question):
    """Generate a simple response when the ML model is unavailable"""
    q_lower = question.lower()

    if any(word in q_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "Hello! How can I help you today?"
    
    elif any(word in q_lower for word in ["bye", "goodbye", "see you"]):
        return "Goodbye! Feel free to return if you have more questions."
    
    elif "your name" in q_lower:
        return "I'm the NYP AI Chatbot Helper, designed to assist with your questions."
    
    elif any(word in q_lower for word in ["help", "how to", "guide"]):
        return "I'm here to help! Please let me know what specific information or assistance you need."
    
    elif any(word in q_lower for word in ["time", "date", "day"]):
        current_time = datetime.now().strftime("%A, %B %d, %Y at %H:%M")
        return f"The current time is {current_time}."

    else:
        return f"Thank you for your question about '{question}'. Let me find an answer for you."

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

# Route to answer questions
@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        if not data:
            logging.warning("No data provided in request.")
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        chat_id = data.get('chat_id', 'default')
        username = data.get('username', 'guest')
        
        if not question:
            logging.warning("No question provided in request.")
            return jsonify({'error': 'No question provided'}), 400

        sanitized_question = sanitize_input(question)
        logging.info(f"Received question from {username}: {sanitized_question[:50]}...")
        current_time = datetime.now().strftime("%H:%M")
        
        try:
            if 'get_convo_hist_answer' in globals():
                response = get_convo_hist_answer(sanitized_question)
                answer = response['answer']
            else:
                answer = generate_simple_response(sanitized_question)
            logging.info(f"Answer generated for {username}'s question")
        except Exception as e:
            logging.error(f"Error generating answer: {str(e)}")
            answer = "I'm having trouble processing your question. Please try again later."
        
        user_message = {
            "role": "user", 
            "content": question, 
            "time": current_time,
            "chat_id": chat_id
        }
        
        bot_message = {
            "role": "assistant", 
            "content": answer, 
            "time": current_time,
            "chat_id": chat_id
        }
        
        save_message(chat_id, user_message)
        save_message(chat_id, bot_message)
        return jsonify({
            'answer': answer,
            'chat_id': chat_id
        }), 200
        
    except Exception as e:
        logging.error(f"Error in /ask endpoint: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
# Route for getting conversation history
@app.route('/get_history', methods=['GET'])
def get_history():
    username = request.args.get('username')
    user_folder = ensure_user_folder(username)
    chat_files = [f for f in os.listdir(SESSION_HISTORY_DIR) if f.startswith(f"chat_")]
    all_chats = []
    for file in chat_files:
        with open(os.path.join(SESSION_HISTORY_DIR, file), "r") as f:
            all_chats.extend(json.load(f))
    return jsonify({'history': all_chats}), 200

# Simplified route for audio transcription only
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