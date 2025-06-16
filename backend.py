from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import logging
import html
import re
import secrets
import uuid
import time
import string
import filetype
import zipfile
import tempfile
import json
from openai import OpenAI
import mimetypes
from unstructured.partition.common import UnsupportedFileFormatError
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from datetime import datetime, timezone
import shutil
import asyncio
from collections import deque, defaultdict

from utils import get_chatbot_dir
from llm.chatModel import get_convo_hist_answer
from llm.dataProcessing import dataProcessing, initialiseDatabase, ExtractText
from llm.classificationModel import classify_text

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_DATA_PATH = os.path.join(get_chatbot_dir(), os.getenv("CHAT_DATA_PATH", r'data\chats'))
DATABASE_PATH = os.path.join(get_chatbot_dir(), os.getenv("DATABASE_PATH", r"data\vector_store\chroma_db"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_SESSIONS_PATH = os.path.join(get_chatbot_dir(), os.getenv('CHAT_SESSIONS_PATH', r'data\chat_sessions'))
USER_DB_PATH = os.path.join(get_chatbot_dir(), os.getenv("CHAT_DATA_PATH", r"data\user_info\users.json"))

# --- Rate Limiting Configuration ---
user_ask_question_timestamps = defaultdict(deque)
user_transcribe_timestamps = defaultdict(deque)

ask_question_rate_limit_lock = asyncio.Lock()
transcribe_rate_limit_lock = asyncio.Lock()

ASK_QUESTION_RATE_LIMIT_COUNT = int(os.getenv("ASK_QUESTION_RATE_LIMIT_COUNT", 5))
ASK_QUESTION_RATE_LIMIT_DURATION = int(os.getenv("ASK_QUESTION_RATE_LIMIT_DURATION", 60))

TRANSCRIBE_RATE_LIMIT_COUNT = int(os.getenv("TRANSCRIBE_RATE_LIMIT_COUNT", 2))
TRANSCRIBE_RATE_LIMIT_DURATION = int(os.getenv("TRANSCRIBE_RATE_LIMIT_DURATION", 30))

async def _check_and_update_rate_limit(user_id: str, timestamps_deque: deque, lock: asyncio.Lock, limit_count: int, limit_duration: int) -> bool:
    current_time = time.time()

    async with lock:
        while timestamps_deque and timestamps_deque[0] <= current_time - limit_duration:
            timestamps_deque.popleft()

        if len(timestamps_deque) >= limit_count:
            logging.warning(f"User {user_id} is rate-limited. Limit: {limit_count} requests in {limit_duration} seconds.")
            return False
        else:
            timestamps_deque.append(current_time)
            return True

# Chroma DB initialization
classification_db = Chroma(
    collection_name='classification',
    embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    persist_directory=DATABASE_PATH
)

async def _ensure_db_and_folders_async():
    db_exists = await asyncio.to_thread(os.path.exists, DATABASE_PATH)
    initialise_db_needed = False

    if not db_exists:
        print(f"Database path '{DATABASE_PATH}' does not exist.")
        initialise_db_needed = True
    else:
        try:
            chroma_content = await asyncio.to_thread(classification_db.get)
            
            if not chroma_content or len(chroma_content.get('documents', [])) == 0:
                print("ChromaDB is empty or has no documents.")
                initialise_db_needed = True
            else:
                print("ChromaDB already contains documents.")
        except Exception as e:
            print(f"Error accessing ChromaDB: {e}. Assuming initialization is needed.")
            initialise_db_needed = True


    if initialise_db_needed:
        print("Initializing database...")
        await asyncio.to_thread(initialiseDatabase)
        print("Database initialization complete.")
    
    if not await asyncio.to_thread(os.path.exists, CHAT_SESSIONS_PATH):
        await asyncio.to_thread(os.makedirs, CHAT_SESSIONS_PATH, exist_ok=True)
        logging.info(f"Created conversations directory at {CHAT_SESSIONS_PATH}")

# Helper functions (asynchronous where I/O is involved)
def sanitize_input(input_text):
    sanitized = html.escape(input_text)
    sanitized = re.sub(r"[^a-zA-Z0-9\s\.,!?'-]", "", sanitized)
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
    return sanitized

async def transcribe_audio_file_async(audio_path):
    try:
        with await asyncio.to_thread(open, audio_path, "rb") as audio_file:
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

async def detectFileType_async(file_path):
    mime_type = None
    file_extension = None

    guessed_file_type = await asyncio.to_thread(filetype.guess, file_path)

    if guessed_file_type:
        mime_type = guessed_file_type.mime
        file_extension = "." + guessed_file_type.extension
    else:
        mime_type, _ = await asyncio.to_thread(mimetypes.guess_type, file_path)
        if mime_type:
            file_extension = await asyncio.to_thread(mimetypes.guess_extension, mime_type)

    if file_extension == ".zip":
        try:
            with await asyncio.to_thread(zipfile.ZipFile, file_path, "r") as z:
                zip_contents = await asyncio.to_thread(z.namelist)

                if any(f.startswith("ppt/") or f.startswith("ppt/_rels/") for f in zip_contents):
                    file_extension = ".pptx"
                elif any(f.startswith("word/") or f.startswith("word/_rels/") for f in zip_contents):
                    file_extension = ".docx"
                elif any(f.startswith("xl/") or f.startswith("xl/_rels/") for f in zip_contents):
                    file_extension = ".xlsx"
        except zipfile.BadZipFile:
            pass
        except Exception:
            pass
    return file_extension

async def ensure_user_folder_file_exists_async(username, chat_id):
    user_folder = await asyncio.to_thread(os.path.join, CHAT_SESSIONS_PATH, username)
    await asyncio.to_thread(os.makedirs, user_folder, exist_ok=True)
    chat_file = await asyncio.to_thread(os.path.join, user_folder, f"{chat_id}.json")
    return chat_file

async def save_message_async(username, chat_id, message):
    history_file = await ensure_user_folder_file_exists_async(username, chat_id)
    try:
        history = []
        if await asyncio.to_thread(os.path.exists, history_file):
            with await asyncio.to_thread(open, history_file, "r") as f:
                history = await asyncio.to_thread(json.load, f)
        
        history.append(message)
        with await asyncio.to_thread(open, history_file, "w") as f:
            await asyncio.to_thread(json.dump, history, f, indent=2)
        logging.info(f"Message saved to chat {chat_id}")
        return True
    except Exception as e:
        logging.error(f"Error saving message to chat {chat_id}: {str(e)}")
        return False

# Mimicking HTTP routes with asynchronous function calls
async def check_health() -> dict[str, str]:
    return {'status': 'OK', 'code': '200'}

async def upload_file(file_dict: dict) -> dict[str, str]:
    filename = file_dict.get("name", "")
    file_content = file_dict.get("file", None)
    username = file_dict.get("username", "")
    
    if file_content is None:
        logging.warning("No file content found: %s", filename)
        return {'error': 'No file content found', 'code': '400'}
    if filename == "":
        logging.warning("Empty filename: %s", filename)
        return {'error': 'Invalid Filename: Filename cannot be empty', 'code': '400'}
    elif '_' in filename:
        return {'error': 'Invalid Filename: Underscore are not allowed', 'code': '400'}
    
    sanitized_filename = await asyncio.to_thread(secure_filename, filename)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = await asyncio.to_thread(os.path.join, temp_dir, sanitized_filename)
        
        with await asyncio.to_thread(open, file_path, 'wb') as f:
            await asyncio.to_thread(f.write, file_content)

        try:
            await asyncio.to_thread(dataProcessing, file_path)
        except UnsupportedFileFormatError:
            return {'error': 'Invalid file type', 'code': '400'}
        
        file_type = await detectFileType_async(file_path)
        
        if file_type is None:
            return {'error': 'Could not determine file type', 'code': '400'}

        directory = await asyncio.to_thread(os.path.join, CHAT_DATA_PATH, f'{file_type[1:]}_files')
        await asyncio.to_thread(os.makedirs, directory, exist_ok=True)
        if username == "":
            return {'error': 'Invalid Username, aborting', 'code': '400'}
            
        new_file_name = await asyncio.to_thread(generateUniqueFilename, filename=sanitized_filename, username=username, filetype=file_type)
        full_directory = await asyncio.to_thread(os.path.join, directory, new_file_name)
        
        await asyncio.to_thread(shutil.copy, file_path, full_directory)

        return {'status': f'File {filename} uploaded and text extracted', 'code': '200', 'filename': filename}
        
async def data_classification(file_dict: dict) -> dict[str, str]:
    filename = file_dict.get("name", "")
    file_content = file_dict.get("file", None)
    mime_type = file_dict.get("type", "")

    if file_content is None:
        logging.warning("No file content found for classification: %s", filename)
        return {'error': 'No file content found', 'code': '400'}
    if filename == '':
        logging.warning("Empty filename for classification: %s", filename)
        return {'error': 'Invalid Filename: Filename cannot be empty', 'code': '400'}
    
    sanitized_filename = await asyncio.to_thread(secure_filename, filename)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = await asyncio.to_thread(os.path.join, temp_dir, sanitized_filename)
        
        with await asyncio.to_thread(open, file_path, 'wb') as f:
            await asyncio.to_thread(f.write, file_content)

        try:
            document = await asyncio.to_thread(ExtractText, file_path)
        except UnsupportedFileFormatError:
            return {'error': 'Invalid file type', 'code': '400'}
        except Exception as e:
            logging.error(f"Error extracting text for classification: {str(e)}")
            return {'error': f"Error extracting text: {str(e)}", 'code': '500'}

        content = document[0].page_content
        response = await asyncio.to_thread(classify_text, content)
        print(response)

        return {'answer': response['answer'], 'code': '200'}

async def ask_question(question_dict: dict[str, str]) -> dict[str, str | dict]:
    question = question_dict.get("question", "")
    chat_id = question_dict.get("chat_id", "0")
    username = question_dict.get("username", "")

    if question == "" or chat_id == "" or username == "":
        return {'error': 'Invalid question or chat_id or username', 'code': '400'}

    if not await _check_and_update_rate_limit(
        username, user_ask_question_timestamps[username], ask_question_rate_limit_lock,
        ASK_QUESTION_RATE_LIMIT_COUNT, ASK_QUESTION_RATE_LIMIT_DURATION
    ):
        return {'error': f"Rate limit exceeded. Please wait {ASK_QUESTION_RATE_LIMIT_DURATION} seconds.", 'code': '429'}

    sanitized_question = sanitize_input(question)
    logging.info(f"Received question from {username}: {sanitized_question}")
    question_time = datetime.now(timezone.utc).strftime(r'%Y-%m-%d %H:%M:%S.%f')

    try:
        response = await asyncio.to_thread(get_convo_hist_answer, sanitized_question, chat_id)
        context = response['context']
        answer = response['answer']
        logging.info("Context: %s", context)
        logging.info("Question answered: %s", sanitized_question)
    except Exception as e:
        logging.error(f"Error generating answer: {str(e)}")
        answer = "I'm having trouble processing your question. Please try again later."
        return {'error': answer, 'code': '500'}
    answer_time = datetime.now(timezone.utc).strftime(r'%Y-%m-%d %H:%M:%S.%f')

    user_message = {"role": "user", "content": question, "timestamp": question_time, "chat_id": chat_id}
    bot_message = {"role": "assistant", "content": answer, "timestamp": answer_time, "chat_id": chat_id}
    
    await save_message_async(username, chat_id, user_message)
    await save_message_async(username, chat_id, bot_message)
    
    return {'answer': answer, 'user_message': user_message, 'bot_message': bot_message, 'code': '200'}

async def transcribe_audio(audio_file_payload: dict) -> dict[str, str]:
    audio_bytes_io = audio_file_payload.get("audio", "00")[1]
    if audio_bytes_io == 0:
        return {'error': f"No audio file detected", 'code': '400'}
    
    username_for_transcription = audio_file_payload.get("username", "anonymous")
    
    if not await _check_and_update_rate_limit(
        username_for_transcription, user_transcribe_timestamps[username_for_transcription], transcribe_rate_limit_lock,
        TRANSCRIBE_RATE_LIMIT_COUNT, TRANSCRIBE_RATE_LIMIT_DURATION
    ):
        return {'error': f"Rate limit exceeded for transcription. Please wait {TRANSCRIBE_RATE_LIMIT_DURATION} seconds.", 'code': '429'}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        await asyncio.to_thread(temp_audio.write, audio_bytes_io.read())
        temp_path = temp_audio.name
            
    logging.info(f"Audio saved to temporary file: {temp_path}")
    
    try:
        transcript_text = ""
        transcript_text = await transcribe_audio_file_async(temp_path)
        
        logging.info(f"Transcription result: {transcript_text[:50]}...")
        
        if await asyncio.to_thread(os.path.exists, temp_path):
            await asyncio.to_thread(os.unlink, temp_path)
            
        return {"transcript": transcript_text, "code": "200"}
            
    except Exception as e:
        logging.error(f"Error in transcription: {str(e)}")
        if await asyncio.to_thread(os.path.exists, temp_path):
            await asyncio.to_thread(os.unlink, temp_path)
        return {"error": f"Transcription failed: {str(e)}", "code": "500"}


async def init_backend():
    print("Backend initialization starting...")
    await _ensure_db_and_folders_async()
    print("Backend initialization complete.")

