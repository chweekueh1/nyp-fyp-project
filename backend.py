import os
from dotenv import load_dotenv
import logging
import html
import re
import json
import filetype
import zipfile
import tempfile
from openai import OpenAI
import mimetypes
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from datetime import datetime, timezone
import asyncio
from collections import deque, defaultdict
from typing import List, Tuple, Dict, Any, Union

from utils import get_chatbot_dir, setup_logging
from llm.chatModel import get_convo_hist_answer, is_llm_ready, initialize_llm_and_db
from llm.dataProcessing import dataProcessing, ExtractText, initialiseDatabase
from llm.classificationModel import classify_text
from openai import OpenAI
from hashing import hash_password, verify_password

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

# Test database path (separate from production)
TEST_USER_DB_PATH = os.path.join(get_chatbot_dir(), r'data\user_info\test_users.json')

# Allowed email domains/addresses for registration
ALLOWED_EMAILS = [
    # NYP email domains
    "student.nyp.edu.sg",
    "nyp.edu.sg",

    # Development/testing emails
    "test@example.com",
    "demo@nyp.edu.sg",
    "admin@nyp.edu.sg",

    # Add more allowed emails here as needed
    "user@nyp.edu.sg",
    "faculty@nyp.edu.sg",
    "staff@nyp.edu.sg",
]

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
        # Load existing history
        history_obj = {"messages": []}
        if await asyncio.to_thread(os.path.exists, history_file):
            with await asyncio.to_thread(open, history_file, "r") as f:
                loaded = await asyncio.to_thread(json.load, f)
                if isinstance(loaded, dict) and "messages" in loaded:
                    history_obj = loaded
                elif isinstance(loaded, list):  # migrate old format
                    history_obj["messages"] = loaded

        # Append new message
        history_obj["messages"].append(message)

        with await asyncio.to_thread(open, history_file, "w") as f:
            await asyncio.to_thread(json.dump, history_obj, f, indent=2)
        logging.info(f"Message saved_handle_chat_message to chat {chat_id}")
        return True
    except Exception as e:
        logging.error(f"Error saving message to chat {chat_id}: {str(e)}")
        return False

# Mimicking HTTP routes with asynchronous function calls
async def check_health() -> dict[str, str]:
    return {'status': 'OK', 'code': '200'}





async def ask_question(question: str, chat_id: str, username: str) -> dict[str, str | dict]:
    logging.error(f"ask_question called with question={question!r}, chat_id={chat_id!r}, username={username!r}")
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
        # Save user message
        await save_message_async(username, chat_id, {"role": "user", "content": sanitized_question})
        # Save bot response
        if isinstance(response, dict) and "answer" in response:
            answer = response["answer"]
        else:
            answer = str(response)
        await save_message_async(username, chat_id, {"role": "assistant", "content": answer})
        return {'status': 'OK', 'code': '200', 'response': response}
    except Exception as e:
        logging.error(f"Error in ask_question: {e}")
        return {'error': str(e), 'code': '500'}





def get_chatbot_response(ui_state: dict) -> dict:
    """
    Chatbot interface: generates a response using the LLM and updates history.
    """
    print(f"[DEBUG] backend.get_chatbot_response called with ui_state: {ui_state}")
    username = ui_state.get('username')
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
    username = ui_state.get('username')
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
    username = ui_state.get('username')
    file_obj = ui_state.get('file_obj')
    history = ui_state.get('history', [])
    chat_id = ui_state.get('chat_id')  # Now optional
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
            with open(file_obj, "rb") as f:
                shutil.copyfileobj(f, tmp)
            tmp_path = tmp.name
        # Process file
        dataProcessing(tmp_path)
        response = f"File '{getattr(file_obj, 'name', '[unknown]')}' uploaded and processed."
        # Only add to history if chat_id is provided (i.e., called from chat)
        if chat_id:
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
    try:
        if not chat_id or not username:
            return []
        user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
        chat_file = os.path.join(user_folder, f"{chat_id}.json")
        if not os.path.exists(chat_file):
            return []
        with open(chat_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict) and "messages" in loaded:
                history = loaded["messages"]
            else:
                history = loaded  # fallback for old format
        # ...existing logic to convert to pairs...
        result = []
        for entry in history:
            if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                if entry['role'] == 'user':
                    user_msg = entry['content']
                elif entry['role'] == 'assistant':
                    if result:
                        result[-1] = (result[-1][0], entry['content'])
                    continue
                else:
                    continue
                result.append((user_msg, ""))
            elif isinstance(entry, list) and len(entry) == 2:
                result.append((entry[0], entry[1]))
        return result
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

async def do_login(username_or_email: str, password: str) -> Dict[str, str]:
    """Handle user login with username or email support."""
    try:
        if not os.path.exists(USER_DB_PATH):
            return {'code': '404', 'message': 'User database not found'}

        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
        users = data.get("users", {})

        # Find user by username or email
        actual_username = None
        user_data = None

        # First, try direct username lookup
        if username_or_email in users:
            actual_username = username_or_email
            user_data = users[username_or_email]
            print(f"Found user by username: {actual_username}")
        else:
            # Try email lookup
            username_or_email_lower = username_or_email.lower()
            for username, data in users.items():
                if data.get('email', '').lower() == username_or_email_lower:
                    actual_username = username
                    user_data = data
                    print(f"Found user by email: {username_or_email} -> username: {actual_username}")
                    break

        if not actual_username or not user_data:
            print(f"User not found: {username_or_email}")
            print(f"Available users: {list(users.keys())}")
            print(f"Available emails: {[data.get('email', 'N/A') for data in users.values()]}")
            return {'code': '404', 'message': 'User not found'}

        print(f"Attempting login for user: {actual_username}")
        stored_hash = user_data.get('hashedPassword')
        print(f"Stored hash for user: {stored_hash}")
        print(f"Against stored hash: {stored_hash}")

        if not stored_hash or not verify_password(password, stored_hash):
            return {'code': '401', 'message': 'Invalid password'}

        return {
            'code': '200',
            'message': 'Login successful',
            'username': actual_username  # Return the actual username
        }
    except Exception as e:
        logging.error(f"Error in login: {e}")
        return {'code': '500', 'message': 'Internal server error'}

async def do_register(username: str, password: str, email: str = "") -> Dict[str, str]:
    """Handle user registration with validation."""
    try:
        from hashing import validate_username, is_password_complex, validate_email_allowed, hash_password

        # Validate username
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return {'code': '400', 'message': username_msg}

        # Validate password complexity
        password_valid, password_msg = is_password_complex(password)
        if not password_valid:
            return {'code': '400', 'message': password_msg}

        # Validate email if provided
        if email:
            email_valid, email_msg = validate_email_allowed(email, ALLOWED_EMAILS)
            if not email_valid:
                return {'code': '400', 'message': email_msg}

        # Check if user database exists
        if not os.path.exists(USER_DB_PATH):
            os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
            with open(USER_DB_PATH, 'w') as f:
                json.dump({"users": {}}, f)

        # Load existing users
        with open(USER_DB_PATH, 'r') as f:
            data = json.load(f)
        users = data.get("users", {})

        # Check if username already exists
        if username in users:
            return {'code': '409', 'message': 'Username already exists'}

        # Check if email already exists (if email provided)
        if email:
            for existing_user, user_data in users.items():
                if user_data.get('email', '').lower() == email.lower():
                    return {'code': '409', 'message': 'Email already registered'}

        # Hash password and create user
        hashed_pw = hash_password(password)
        user_data = {
            'hashedPassword': hashed_pw,
            'created_at': str(datetime.now(timezone.utc))
        }

        # Add email if provided
        if email:
            user_data['email'] = email.strip().lower()

        users[username] = user_data

        # Save updated users
        with open(USER_DB_PATH, 'w') as f:
            json.dump({"users": users}, f, indent=2)

        return {'code': '200', 'message': 'Registration successful'}
    except Exception as e:
        logging.error(f"Error in registration: {e}")
        return {'code': '500', 'message': 'Internal server error'}

def list_user_chat_ids(username: str) -> list:
    """Return a list of all chat IDs for the given user."""
    try:
        user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
        if not os.path.exists(user_folder):
            return []
        chat_files = [f for f in os.listdir(user_folder) if f.endswith('.json')]
        return [os.path.splitext(f)[0] for f in chat_files]
    except Exception as e:
        logger.error(f"Error listing chat IDs: {e}")
        return []

from datetime import datetime

def create_new_chat_id(username: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    return f"Chat {timestamp}"

def create_and_persist_new_chat(username: str) -> str:
    """Create a new chat with a human-readable name and persist it, returning the chat_id."""
    chat_id = create_new_chat_id(username)
    user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
    os.makedirs(user_folder, exist_ok=True)
    chat_file = os.path.join(user_folder, f"{chat_id}.json")
    if not os.path.exists(chat_file):
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump({"messages": []}, f, indent=2)
    return chat_id

# Additional functions for test compatibility
def generateUniqueFilename(prefix: str, username: str, extension: str) -> str:
    """Generate a unique filename with timestamp and random component."""
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for uniqueness
    return f"{prefix}_{username}_{timestamp}_{unique_id}{extension}"

def get_user_chats(username: str) -> list:
    """Get list of chat IDs for a user (alias for list_user_chat_ids)."""
    return list_user_chat_ids(username)

def get_user_chats_with_names(username: str) -> list:
    """Get list of chats with names for a user."""
    try:
        chat_ids = list_user_chat_ids(username)
        result = []
        for chat_id in chat_ids:
            name = get_chat_name(chat_id, username)
            result.append({"id": chat_id, "name": name})
        return result
    except Exception as e:
        logger.error(f"Error getting user chats with names: {e}")
        return []

def get_chat_name(chat_id: str, username: str) -> str:
    """Get the name of a chat (returns chat_id if no custom name)."""
    try:
        # For now, just return the chat_id as the name
        # In the future, this could be extended to support custom names
        return chat_id
    except Exception as e:
        logger.error(f"Error getting chat name: {e}")
        return chat_id

def set_chat_name(chat_id: str, username: str, name: str) -> bool:
    """Set a custom name for a chat."""
    try:
        # For now, this is a placeholder that always returns True
        # In the future, this could be extended to support custom names
        return True
    except Exception as e:
        logger.error(f"Error setting chat name: {e}")
        return False

def rename_chat_file(old_chat_id: str, new_chat_id: str, username: str) -> bool:
    """Rename a chat file."""
    try:
        user_folder = os.path.join(CHAT_SESSIONS_PATH, username)
        old_file = os.path.join(user_folder, f"{old_chat_id}.json")
        new_file = os.path.join(user_folder, f"{new_chat_id}.json")

        if os.path.exists(old_file) and not os.path.exists(new_file):
            os.rename(old_file, new_file)
            return True
        return False
    except Exception as e:
        logger.error(f"Error renaming chat file: {e}")
        return False

async def init_backend():
    """Initialize the backend."""
    try:
        # This function is called during startup
        await init_backend_async_internal()
        logger.info("Backend initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing backend: {e}")
        raise

async def init_backend_async_internal():
    """Internal backend initialization function."""
    # Initialize LLM and database
    initialize_llm_and_db()

    # Ensure required directories exist
    os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)

    logger.info("Backend initialization completed")

def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio file to text."""
    try:
        with open(audio_file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            ).text
        return transcript
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return f"Error transcribing audio: {e}"

async def transcribe_audio_async(audio_file: bytes, username: str) -> dict:
    """Transcribe audio file content to text (async version for integration tests)."""
    try:
        if not audio_file:
            return {'error': 'No audio file provided', 'code': '400'}

        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_file)
            temp_audio_path = temp_audio.name

        try:
            transcript = await transcribe_audio_file_async(temp_audio_path)
            return {'status': 'OK', 'code': '200', 'transcript': transcript}
        finally:
            os.unlink(temp_audio_path)
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {'error': str(e), 'code': '500'}

async def upload_file(file_content: bytes, filename: str, username: str) -> dict:
    """Upload and process a file."""
    try:
        # Simple implementation for testing
        if not file_content or not filename or not username:
            return {'error': 'Invalid file, filename, or username', 'code': '400'}

        # For now, just return success - in a real implementation this would process the file
        return {'status': 'OK', 'code': '200', 'filename': filename, 'message': 'File uploaded successfully'}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return {'error': str(e), 'code': '500'}

async def data_classification(content: str) -> dict:
    """Classify data content."""
    try:
        response = await asyncio.to_thread(classify_text, content)
        return {'answer': response['answer'], 'code': '200'}
    except Exception as e:
        logger.error(f"Error in data classification: {e}")
        return {'error': str(e), 'code': '500'}

def fuzzy_search_chats(username: str, query: str) -> str:
    """Perform fuzzy search on user's chats."""
    try:
        if not username or not query:
            return "No matching chats found"

        chat_ids = list_user_chat_ids(username)
        if not chat_ids:
            return "No matching chats found"

        from difflib import get_close_matches
        results = []

        for chat_id in chat_ids:
            history = get_chat_history(chat_id, username)
            all_text = " ".join([f"{msg[0]} {msg[1]}" for msg in history])

            if query.lower() in all_text.lower() or get_close_matches(query, [all_text], n=1, cutoff=0.6):
                results.append(f"Chat {chat_id}: {all_text[:100]}...")

        return "\n\n".join(results) if results else "No matching chats found"
    except Exception as e:
        logger.error(f"Error in fuzzy search: {e}")
        return "No matching chats found"

def render_all_chats(username: str) -> list:
    """Render all chats for a user."""
    try:
        if not username:
            return []

        chat_ids = list_user_chat_ids(username)
        result = []

        for chat_id in chat_ids:
            history = get_chat_history(chat_id, username)
            result.append({
                "id": chat_id,
                "name": get_chat_name(chat_id, username),
                "history": history
            })

        return result
    except Exception as e:
        logger.error(f"Error rendering all chats: {e}")
        return []

# Test-specific functions that don't persist to production database
async def do_register_test(username: str, password: str, email: str = "") -> Dict[str, str]:
    """Handle user registration for testing (uses test database)."""
    try:
        from hashing import validate_username, is_password_complex, validate_email_allowed, hash_password

        # Validate username
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return {'code': '400', 'message': username_msg}

        # Validate password complexity
        password_valid, password_msg = is_password_complex(password)
        if not password_valid:
            return {'code': '400', 'message': password_msg}

        # Validate email if provided
        if email:
            email_valid, email_msg = validate_email_allowed(email, ALLOWED_EMAILS)
            if not email_valid:
                return {'code': '400', 'message': email_msg}

        # Use test database
        test_db_path = TEST_USER_DB_PATH

        # Check if test database exists
        if not os.path.exists(test_db_path):
            os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
            with open(test_db_path, 'w') as f:
                json.dump({"users": {}}, f)

        # Load existing test users
        with open(test_db_path, 'r') as f:
            data = json.load(f)
        users = data.get("users", {})

        # Check if username already exists
        if username in users:
            return {'code': '409', 'message': 'Username already exists'}

        # Check if email already exists (if email provided)
        if email:
            for existing_user, user_data in users.items():
                if user_data.get('email', '').lower() == email.lower():
                    return {'code': '409', 'message': 'Email already registered'}

        # Hash password and create user
        hashed_pw = hash_password(password)
        user_data = {
            'hashedPassword': hashed_pw,
            'created_at': str(datetime.now(timezone.utc))
        }

        # Add email if provided
        if email:
            user_data['email'] = email.strip().lower()

        users[username] = user_data

        # Save updated test users
        with open(test_db_path, 'w') as f:
            json.dump({"users": users}, f, indent=2)

        return {'code': '200', 'message': 'Registration successful'}
    except Exception as e:
        logging.error(f"Error in test registration: {e}")
        return {'code': '500', 'message': 'Internal server error'}

async def do_login_test(username_or_email: str, password: str) -> Dict[str, str]:
    """Handle user login for testing (uses test database)."""
    try:
        test_db_path = TEST_USER_DB_PATH

        if not os.path.exists(test_db_path):
            return {'code': '404', 'message': 'Test user database not found'}

        with open(test_db_path, 'r') as f:
            data = json.load(f)
        users = data.get("users", {})

        # Find user by username or email
        actual_username = None
        user_data = None

        # First, try direct username lookup
        if username_or_email in users:
            actual_username = username_or_email
            user_data = users[username_or_email]
        else:
            # Try email lookup
            username_or_email_lower = username_or_email.lower()
            for username, data in users.items():
                if data.get('email', '').lower() == username_or_email_lower:
                    actual_username = username
                    user_data = data
                    break

        if not actual_username or not user_data:
            return {'code': '404', 'message': 'User not found'}

        stored_hash = user_data.get('hashedPassword')

        if not stored_hash or not verify_password(password, stored_hash):
            return {'code': '401', 'message': 'Invalid password'}

        return {
            'code': '200',
            'message': 'Login successful',
            'username': actual_username
        }
    except Exception as e:
        logging.error(f"Error in test login: {e}")
        return {'code': '500', 'message': 'Internal server error'}

def cleanup_test_user(username: str) -> bool:
    """Remove a test user from the test database."""
    try:
        test_db_path = TEST_USER_DB_PATH

        if not os.path.exists(test_db_path):
            return True  # Nothing to clean up

        with open(test_db_path, 'r') as f:
            data = json.load(f)
        users = data.get("users", {})

        if username in users:
            del users[username]

            with open(test_db_path, 'w') as f:
                json.dump({"users": users}, f, indent=2)

            logger.info(f"Cleaned up test user: {username}")
            return True

        return True  # User didn't exist, nothing to clean up
    except Exception as e:
        logger.error(f"Error cleaning up test user {username}: {e}")
        return False

def cleanup_all_test_users() -> bool:
    """Remove all test users and reset test database."""
    try:
        test_db_path = TEST_USER_DB_PATH

        if os.path.exists(test_db_path):
            with open(test_db_path, 'w') as f:
                json.dump({"users": {}}, f, indent=2)
            logger.info("Cleaned up all test users")

        return True
    except Exception as e:
        logger.error(f"Error cleaning up all test users: {e}")
        return False

