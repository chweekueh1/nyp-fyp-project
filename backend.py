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
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path

from utils import get_chatbot_dir, setup_logging
from llm.chatModel import get_convo_hist_answer, is_llm_ready, initialize_llm_and_db
from llm.dataProcessing import dataProcessing, ExtractText, initialiseDatabase
from llm.classificationModel import classify_text
from openai import OpenAI

# Set up logging
logger = setup_logging()

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_DATA_PATH = os.path.join(get_chatbot_dir(), os.getenv("CHAT_DATA_PATH", r'data\chats'))
DATABASE_PATH = os.path.join(get_chatbot_dir(), os.getenv("DATABASE_PATH", r"data\vector_store\chroma_db"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_SESSIONS_PATH = os.path.join(get_chatbot_dir(), os.getenv('CHAT_SESSIONS_PATH', r'data\chat_sessions'))
USER_DB_PATH = os.path.join(get_chatbot_dir(), os.getenv('USER_DB_PATH', r'data\user_info\users.json'))

class RateLimiter:
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)
    
    async def check_and_update(self, user_id: str) -> bool:
        now = asyncio.get_event_loop().time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        while user_requests and now - user_requests[0] > self.time_window:
            user_requests.popleft()
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True

# Initialize rate limiter
rate_limiter = RateLimiter()

async def check_rate_limit(user_id: str) -> bool:
    """Check if a user has exceeded their rate limit."""
    return await rate_limiter.check_and_update(user_id)

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
    if not input_text:
        return ""
    sanitized = html.escape(input_text)
    sanitized = re.sub(r"[^a-zA-Z0-9\s\.,!?'-]", "", sanitized)
    if len(sanitized) > 500:
        return sanitized[:500]
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
    if not filename:
        logging.warning("Empty filename: %s", filename)
        return {'error': 'Invalid Filename: Filename cannot be empty', 'code': '400'}
    if '_' in filename:
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
        if not username:
            return {'error': 'Invalid Username, aborting', 'code': '400'}
        new_file_name = await asyncio.to_thread(generateUniqueFilename, filename=sanitized_filename, username=username, filetype=file_type)
        full_directory = await asyncio.to_thread(os.path.join, directory, new_file_name)
        await asyncio.to_thread(shutil.copy, file_path, full_directory)
    return {'status': 'OK', 'code': '200', 'filename': new_file_name}

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

async def ask_question(question: str, chat_id: str, username: str) -> dict[str, str | dict]:
    if not question or not chat_id or not username:
        return {'error': 'Invalid question or chat_id or username', 'code': '400'}
    if not await check_rate_limit(username):
        return {'error': f"Rate limit exceeded. Please wait {rate_limiter.time_window} seconds.", 'code': '429'}
    sanitized_question = sanitize_input(question)
    try:
        if not is_llm_ready():
            logging.warning("LLM/DB not ready in ask_question. Attempting re-initialization.")
            initialize_llm_and_db()
        if not is_llm_ready():
            logging.error("LLM/DB still not ready after re-initialization in ask_question.")
            return {'error': 'AI assistant is not fully initialized. Please try again later.', 'code': '500'}
        response = get_convo_hist_answer(sanitized_question, chat_id)
        return {'status': 'OK', 'code': '200', 'response': response}
    except Exception as e:
        logging.error(f"Error in ask_question: {e}")
        return {'error': str(e), 'code': '500'}

async def transcribe_audio(audio_file, username: str) -> dict[str, str]:
    if not audio_file:
        return {'error': 'No audio file provided', 'code': '400'}

    if not await check_rate_limit(username):
        return {'error': f"Rate limit exceeded for transcription. Please wait {rate_limiter.time_window} seconds.", 'code': '429'}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_file)
        temp_audio_path = temp_audio.name

    try:
        transcript = await transcribe_audio_file_async(temp_audio_path)
        return {'status': 'OK', 'code': '200', 'transcript': transcript}
    except Exception as e:
        logging.error(f"Error in transcribe_audio: {e}")
        return {'error': str(e), 'code': '500'}
    finally:
        os.unlink(temp_audio_path)

async def init_backend():
    print("Backend initialization starting...")
    await _ensure_db_and_folders_async()
    print("Backend initialization complete.")

def get_chatbot_response(ui_state: dict) -> dict:
    """
    Chatbot interface: generates a response using the LLM and updates history.
    """
    print(f"[DEBUG] backend.get_chatbot_response called with ui_state: {ui_state}")
    user = ui_state.get('user')
    message = ui_state.get('message')
    history = ui_state.get('history', [])
    chat_id = ui_state.get('chat_id', 'default')
    if not message:
        return {'history': history, 'response': '[No message provided]', 'debug': 'No message.'}
    try:
        # Use your LLM chat model
        result = get_convo_hist_answer(message, chat_id)
        response = result['answer']
        history = history + [[message, response]]
        response_dict = {'history': history, 'response': response, 'debug': 'Chatbot response generated.'}
        print(f"[DEBUG] backend.get_chatbot_response returning: {response_dict}")
        return response_dict
    except Exception as e:
        print(f"[ERROR] backend.get_chatbot_response exception: {e}")
        return {'history': history, 'response': f'[Error] {e}', 'debug': f'Exception: {e}'}

def audio_to_text(ui_state: dict) -> dict:
    """
    Audio input interface: transcribes audio and gets a chatbot response.
    """
    print(f"[DEBUG] backend.audio_to_text called with ui_state: {ui_state}")
    user = ui_state.get('user')
    audio_file = ui_state.get('audio_file')
    history = ui_state.get('history', [])
    chat_id = ui_state.get('chat_id', 'default')
    if not audio_file:
        return {'history': history, 'response': '[No audio file provided]', 'debug': 'No audio.'}
    try:
        if not is_llm_ready():
            logging.warning("LLM/DB not ready in audio_to_text. Attempting re-initialization.")
            initialize_llm_and_db()
        if not is_llm_ready():
            logging.error("LLM/DB still not ready after re-initialization in audio_to_text.")
            return {'history': history, 'response': '[Error] AI assistant is not fully initialized. Please try again later.', 'debug': 'LLM/DB not ready.'}
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            ).text
        # Now get chatbot response
        result = get_convo_hist_answer(transcript, chat_id)
        response = result['answer']
        history = history + [[f"[Audio: {audio_file}]", response]]
        response_dict = {'history': history, 'response': response, 'debug': f'Audio transcribed and response generated.'}
        print(f"[DEBUG] backend.audio_to_text returning: {response_dict}")
        return response_dict
    except Exception as e:
        print(f"[ERROR] backend.audio_to_text exception: {e}")
        return {'history': history, 'response': f'[Error] {e}', 'debug': f'Exception: {e}'}

def handle_uploaded_file(ui_state: dict) -> dict:
    """
    File upload interface: processes the file and returns a message.
    """
    print(f"[DEBUG] backend.handle_uploaded_file called with ui_state: {ui_state}")
    user = ui_state.get('user')
    file_obj = ui_state.get('file_obj')
    history = ui_state.get('history', [])
    chat_id = ui_state.get('chat_id', 'default')
    if not file_obj:
        return {'history': history, 'response': '[No file uploaded]', 'debug': 'No file.'}
    try:
        if not is_llm_ready():
            logging.warning("LLM/DB not ready in handle_uploaded_file. Attempting re-initialization.")
            initialize_llm_and_db()
        if not is_llm_ready():
            logging.error("LLM/DB still not ready after re-initialization in handle_uploaded_file.")
            return {'history': history, 'response': '[Error] AI assistant is not fully initialized. Please try again later.', 'debug': 'LLM/DB not ready.'}
        import tempfile, shutil
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(file_obj, tmp)
            tmp_path = tmp.name
        # Process file
        dataProcessing(tmp_path)
        response = f"File '{getattr(file_obj, 'name', '[unknown]')}' uploaded and processed."
        history = history + [[f"[File: {getattr(file_obj, 'name', '[unknown]')}]", response]]
        response_dict = {'history': history, 'response': response, 'debug': 'File uploaded and processed.'}
        print(f"[DEBUG] backend.handle_uploaded_file returning: {response_dict}")
        return response_dict
    except Exception as e:
        print(f"[ERROR] backend.handle_uploaded_file exception: {e}")
        return {'history': history, 'response': f'[Error] {e}', 'debug': f'Exception: {e}'}

def get_chat_response(message: str, username: str) -> str:
    """Get a response from the chatbot for a given message.
    
    Args:
        message: The user's message
        username: The username of the current user
        
    Returns:
        The chatbot's response
    """
    try:
        # TODO: Implement actual chat response logic
        return f"Echo: {message}"
    except Exception as e:
        logger.error(f"Error getting chat response: {e}")
        return "Sorry, I encountered an error. Please try again."

def search_chat_history(query: str, username: str) -> List[Dict[str, Any]]:
    """Search chat history for a given query.
    
    Args:
        query: The search query
        username: The username of the current user
        
    Returns:
        List of chat history entries matching the query
    """
    try:
        # TODO: Implement actual chat search logic
        return []
    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        return []

def get_chat_history(chat_id: str, username: str) -> List[Tuple[str, str]]:
    """Get chat history for a given chat ID.
    
    Args:
        chat_id: The ID of the chat to retrieve
        username: The username of the current user
        
    Returns:
        List of (message, response) tuples
    """
    try:
        # TODO: Implement actual chat history retrieval
        return []
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return []

def get_completion(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 150, temperature: float = 0.7) -> Union[str, Dict[str, Any]]:
    """Get a completion from the OpenAI API.
    
    Args:
        prompt: The prompt to send to the API
        model: The model to use for completion
        max_tokens: Maximum number of tokens to generate
        temperature: Controls randomness in the output
        
    Returns:
        The completion text or error information
    """
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        content = response.choices[0].message.content
        if content is None:
            return {"error": "No content in response"}
        return content
    except Exception as e:
        logger.error(f"Error getting completion: {e}")
        return {"error": str(e)}

async def do_login(username: str, password: str) -> Dict[str, str]:
    """Handle user login.
    
    Args:
        username: The username to login with
        password: The password to login with
        
    Returns:
        Dict containing status code and message
    """
    try:
        # Check if user exists
        if not os.path.exists(USER_DB_PATH):
            return {'code': '404', 'message': 'User database not found'}
            
        with open(USER_DB_PATH, 'r') as f:
            users = json.load(f)
            
        if username not in users:
            return {'code': '404', 'message': 'User not found'}
            
        if users[username]['password'] != password:  # In production, use proper password hashing
            return {'code': '401', 'message': 'Invalid password'}
            
        return {'code': '200', 'message': 'Login successful'}
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return {'code': '500', 'message': 'Internal server error'}

async def do_register(username: str, password: str) -> Dict[str, str]:
    """Handle user registration.
    
    Args:
        username: The username to register
        password: The password to register with
        
    Returns:
        Dict containing status code and message
    """
    try:
        # Create user database if it doesn't exist
        if not os.path.exists(USER_DB_PATH):
            os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
            with open(USER_DB_PATH, 'w') as f:
                json.dump({}, f)
                
        # Load existing users
        with open(USER_DB_PATH, 'r') as f:
            users = json.load(f)
            
        # Check if user already exists
        if username in users:
            return {'code': '409', 'message': 'Username already exists'}
            
        # Add new user
        users[username] = {
            'password': password,  # In production, use proper password hashing
            'created_at': str(datetime.now(timezone.utc))
        }
        
        # Save updated users
        with open(USER_DB_PATH, 'w') as f:
            json.dump(users, f, indent=2)
            
        return {'code': '200', 'message': 'Registration successful'}
    except Exception as e:
        logging.error(f"Error in registration: {e}")
        return {'code': '500', 'message': 'Internal server error'}

