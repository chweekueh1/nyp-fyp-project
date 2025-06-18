import requests
import os
import json
import io # Needed for BytesIO for audio data
import tempfile
import shutil
import pytest
from gradio_modules.main_app import main_app
from backend import ask_question, transcribe_audio, upload_file, data_classification
import asyncio
import wave
import numpy as np

"""
Audio and file upload tests will fail. This is intentional.
"""

# --- Configuration ---
# Ensure this matches the FLASK_HOST and FLASK_PORT in your main_app.py
BASE_URL = "http://127.0.0.1:5001"

# --- Dummy Files for Testing ---
DUMMY_TEXT_FILENAME = "testdocument.txt"
DUMMY_TEXT_CONTENT = "This is a dummy document for testing purposes. It contains some sample text for classification."

DUMMY_AUDIO_FILENAME = "testaudio.wav"
# A valid WAV header for a 0.1-second silent WAV file (44.1 kHz, 16-bit, mono)
DUMMY_AUDIO_CONTENT = (
    b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
)

def create_dummy_files():
    """Creates dummy files required for testing."""
    with open(DUMMY_TEXT_FILENAME, "w") as f:
        f.write(DUMMY_TEXT_CONTENT)
    print(f"Created dummy file: {DUMMY_TEXT_FILENAME}")

    # Create dummy audio file for testing (0.1s of silence at 44.1kHz, mono, 16-bit)
    sample_rate = 44100
    n_samples = int(0.1 * sample_rate)
    silence = np.zeros(n_samples, dtype=np.int16)
    with wave.open(DUMMY_AUDIO_FILENAME, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(silence.tobytes())
    print(f"Created dummy file: {DUMMY_AUDIO_FILENAME}")

def cleanup_dummy_files():
    """Removes dummy files after testing."""
    if os.path.exists(DUMMY_TEXT_FILENAME):
        os.remove(DUMMY_TEXT_FILENAME)
        print(f"Removed dummy file: {DUMMY_TEXT_FILENAME}")
    if os.path.exists(DUMMY_AUDIO_FILENAME):
        os.remove(DUMMY_AUDIO_FILENAME)
        print(f"Removed dummy file: {DUMMY_AUDIO_FILENAME}")

def test_route(name, method, url, data=None, files=None, json_data=None):
    """Helper function to test a single route and print results."""
    print(f"\n--- Testing {name} ({method.upper()} {url}) ---")
    response = None # FIX: Initialize response to None to prevent unbound error
    try:
        if method.lower() == 'get':
            response = requests.get(url, params=data, timeout=10)
        elif method.lower() == 'post':
            response = requests.post(url, data=data, files=files, json=json_data, timeout=30)
        else:
            print(f"Error: Unsupported method '{method}'")
            return False

        if response: # FIX: Check if response was successfully assigned before proceeding
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Status Code: {response.status_code}")
            # Attempt to pretty-print JSON response if it exists
            try:
                print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
            except json.JSONDecodeError:
                print(f"Response Body (not JSON): {response.text}") # Fallback for non-JSON responses
            print(f"--- {name} Test PASSED ---")
            return True
        else:
            print(f"--- {name} Test FAILED (No response due to unsupported method or other issue) ---")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the backend at {url}. Is the Flask app running? (Error: {e})")
        print(f"--- {name} Test FAILED ---")
        return False
    except requests.exceptions.Timeout:
        print(f"Error: Request to {url} timed out.")
        print(f"--- {name} Test FAILED ---")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {url}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error Response Body: {e.response.text}")
        print(f"--- {name} Test FAILED ---")
        return False
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred during {name} test: {e}")
        print(f"--- {name} Test FAILED ---")
        return False

def run_all_tests():
    """Executes all backend route tests."""
    print("Starting backend route tests...")
    
    # Create dummy files at the start of testing
    create_dummy_files()

    # --- Test Health Check ---
    test_route("Health Check", "GET", f"{BASE_URL}/")

    # --- Test File Upload ---
    try:
        with open(DUMMY_TEXT_FILENAME, "rb") as f:
            files = {"file": (DUMMY_TEXT_FILENAME, f, "text/plain")}
            data = {"username": "testuser_upload"} # Use a distinct username
            test_route("File Upload", "POST", f"{BASE_URL}/upload", data=data, files=files)
    except FileNotFoundError:
        print(f"Error: Dummy text file '{DUMMY_TEXT_FILENAME}' not found. Please ensure it's created.")

    # --- Test File Classification ---
    try:
        with open(DUMMY_TEXT_FILENAME, "rb") as f:
            files = {"file": (DUMMY_TEXT_FILENAME, f, "text/plain")}
            test_route("File Classification", "POST", f"{BASE_URL}/classify", files=files)
    except FileNotFoundError:
        print(f"Error: Dummy text file '{DUMMY_TEXT_FILENAME}' not found. Please ensure it's created.")

    # --- Test Ask Question ---
    ask_payload = {
        "question": "What are the common data security practices?",
        "chat_id": "test_chat_ask_123", # Use a unique chat ID for testing
        "username": "testuser_chat" # Use a distinct username
    }
    test_route("Ask Question", "POST", f"{BASE_URL}/ask", json_data=ask_payload)

    # --- Test Audio Transcription ---
    try:
        with open(DUMMY_AUDIO_FILENAME, "rb") as f:
            files = {"audio": (DUMMY_AUDIO_FILENAME, f, "audio/wav")} # Specify MIME type
            test_route("Audio Transcription", "POST", f"{BASE_URL}/transcribe", files=files)
    except FileNotFoundError:
        print(f"Error: Dummy audio file '{DUMMY_AUDIO_FILENAME}' not found. Please ensure it's created.")

    print("\n--- All Backend Tests Completed ---")

def setup_user_chats(tmp_path, user, chats):
    user_dir = tmp_path / "data" / "chat_sessions" / user
    user_dir.mkdir(parents=True, exist_ok=True)
    for chat_id, messages in chats.items():
        with open(user_dir / f"{chat_id}.json", "w") as f:
            json.dump(messages, f)
    return user_dir

def test_fuzzy_search_chats(tmp_path, monkeypatch):
    # Prepare mock data
    user = "testuser"
    chats = {
        "chat1": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you!"}
        ],
        "chat2": [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny."}
        ]
    }
    setup_user_chats(tmp_path, user, chats)
    # Patch the data path
    monkeypatch.setattr("os.path.dirname", lambda _: str(tmp_path))
    from gradio_modules.main_app import fuzzy_search_chats
    # Fuzzy search for 'weather'
    result = fuzzy_search_chats(user, "weather")
    assert "chat2" in result
    assert "weather" in result.lower()
    # Fuzzy search for 'hello'
    result = fuzzy_search_chats(user, "hello")
    assert "chat1" in result
    assert "hello" in result.lower()
    # Fuzzy search for non-existent
    result = fuzzy_search_chats(user, "nonexistent")
    assert "No matching chats found" in result

def test_render_all_chats(tmp_path, monkeypatch):
    user = "testuser"
    chats = {
        "chat1": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you!"}
        ],
        "chat2": [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny."}
        ]
    }
    setup_user_chats(tmp_path, user, chats)
    monkeypatch.setattr("os.path.dirname", lambda _: str(tmp_path))
    from gradio_modules.main_app import render_all_chats
    chatbots = render_all_chats(user)
    assert any("chat1" in str(bot.label) for bot in chatbots)
    assert any("chat2" in str(bot.label) for bot in chatbots)

async def test_ask_question():
    """Test the ask_question function directly."""
    question = "What are the common data security practices?"
    chat_id = "test_chat_ask_123"
    username = "testuser_chat"
    response = await ask_question(question, chat_id, username)
    print(f"Ask Question Response: {response}")
    assert response.get('code') == '200'

async def test_transcribe_audio():
    """Test the transcribe_audio function directly."""
    with open(DUMMY_AUDIO_FILENAME, "rb") as f:
        audio_file = f.read()
    username = "testuser_audio"
    response = await transcribe_audio(audio_file, username)
    print(f"Transcribe Audio Response: {response}")
    assert response.get('code') == '200'

async def test_upload_file():
    """Test the upload_file function directly."""
    with open(DUMMY_TEXT_FILENAME, "rb") as f:
        file_content = f.read()
    file_dict = {"name": DUMMY_TEXT_FILENAME, "file": file_content, "username": "testuser_upload"}
    response = await upload_file(file_dict)
    print(f"Upload File Response: {response}")
    assert response.get('code') == '200'

async def test_data_classification():
    """Test the data_classification function directly."""
    with open(DUMMY_TEXT_FILENAME, "rb") as f:
        file_content = f.read()
    file_dict = {"name": DUMMY_TEXT_FILENAME, "file": file_content, "type": "text/plain"}
    response = await data_classification(file_dict)
    print(f"Data Classification Response: {response}")
    assert response.get('code') == '200'

def run_all_unit_tests():
    """Executes all backend tests directly."""
    print("Starting backend tests...")
    create_dummy_files()
    try:
        asyncio.run(test_ask_question())
        asyncio.run(test_transcribe_audio())
        asyncio.run(test_upload_file())
        asyncio.run(test_data_classification())
        print("All backend tests completed successfully.")
    finally:
        cleanup_dummy_files()

if __name__ == "__main__":
    run_all_unit_tests()
