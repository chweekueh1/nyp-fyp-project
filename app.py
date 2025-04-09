from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import openai
from dotenv import load_dotenv
import logging
import traceback
import html
import re
import tempfile
import io
from openai import OpenAI
import zipfile
import mimetypes
import magic

# Import modules for text extraction, data chunking, and conversation history
from TextExtraction import get_pdf_text, get_docx_text, get_pptx_text, get_xlsx_text, get_img_text
# from DataChunking import load_text, split_text, split_list, create_db
# from modelWithConvoHist import get_convo_hist_answer

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

UPLOAD_FOLDER = 'uploads'
DATA_PATH = os.getenv("DATA_PATH", "./modelling/extracted_text.txt")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # Limit upload size to 25MB

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png', 'wav', 'mp3'}

# Ensure 'uploads' folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.info("Flask application initialized. Upload folder set up at %s", UPLOAD_FOLDER)

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to extract text based on file type
def extract_text(filepath, file_type):
    try:
        if file_type == 'pdf':
            return get_pdf_text([filepath])
        elif file_type == 'docx':
            return get_docx_text([filepath])
        elif file_type == 'xlsx':
            return get_xlsx_text([filepath])
        elif file_type == 'pptx':
            return get_pptx_text([filepath])
        elif file_type in ['jpg', 'jpeg', 'png']:
            return get_img_text([filepath])
        elif file_type in ['wav', 'mp3']:
            # Handle audio files - transcribe them
            return transcribe_audio_file(filepath)
    except Exception as e:
        logging.error("Error extracting text from %s: %s", filepath, str(e))
        raise
    return ""

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

# Helper function to process transcription with GPT-4o Mini
def process_transcript_with_gpt(transcript, context=""):
    try:
        # Create a system message
        system_message = """
        You are a helpful AI assistant. You're responding to transcribed audio from the user.
        Please help them with their query or question based on their voice input.
        """
        
        if context:
            system_message += f"\nHere is some context that may be relevant: {context}"
        
        # Generate response from GPT-4o Mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4o Mini model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": transcript}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error processing with GPT-4o Mini: {str(e)}")
        raise

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
        if file.filename == '' or not allowed_file(file.filename):
            logging.warning("Invalid file type or empty filename: %s", file.filename)
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logging.info("File saved: %s", filepath)

        # Extract and save text to DATA_PATH
        file_type = filename.rsplit('.', 1)[1].lower()
        text = extract_text(filepath, file_type)
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        logging.info("Text extracted and saved to %s", DATA_PATH)

        # Process extracted text for chunking and updating vector database
        documents = load_text(DATA_PATH)
        chunks = split_text(documents)
        split_chunked = list(split_list(chunks, 166))
        create_db(split_chunked)
        logging.info("Vector database updated.")

        return jsonify({'status': 'File uploaded and text extracted'}), 200
    except Exception as e:
        logging.error("Error in /upload endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Route for question answering with conversation history
@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        question = request.json.get('question')
        if not question:
            logging.warning("No question provided in request.")
            return jsonify({'error': 'No question provided'}), 400

        # Sanitize user input
        sanitized_question = sanitize_input(question)
        logging.info("Sanitized question: %s", sanitized_question)

        # Get answer from model with conversation history
        response = get_convo_hist_answer(sanitized_question)
        logging.info("Question answered: %s", sanitized_question)
        return jsonify({'answer': response['answer']}), 200
    except Exception as e:
        logging.error("Error in /ask endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

# Improved route for audio transcription
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
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return jsonify({"transcript": transcript.text}), 200
        except Exception as e:
            logging.error(f"Error in transcription: {str(e)}")
            # Clean up temporary file in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error in /transcribe endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

# New route for combined transcription and GPT-4o Mini processing
@app.route("/transcribe_and_process", methods=["POST"])
def transcribe_and_process():
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
            
            transcript_text = transcript.text
            logging.info(f"Transcription successful: {transcript_text[:50]}...")
            
            # Process the transcript with GPT-4o Mini
            response = process_transcript_with_gpt(transcript_text)
            logging.info(f"GPT-4o Mini processing successful")
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return jsonify({
                "transcript": transcript_text,
                "response": response
            }), 200
        except Exception as e:
            logging.error(f"Error in transcription or processing: {str(e)}")
            # Clean up temporary file in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": f"Operation failed: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Error in /transcribe_and_process endpoint: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    os.makedirs('modelling\\data\\error_files', exist_ok=True)
    os.makedirs('modelling\\data\\temp', exist_ok=True)
    logging.info("Starting Flask application on port 5001.")
    app.run(port=5001, debug=False)
    print(app.url_map)