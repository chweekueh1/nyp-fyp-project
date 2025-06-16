import requests
import os
import json
import io # Needed for BytesIO for audio data

"""
Audio and file upload tests will fail. This is intentional.
"""

# --- Configuration ---
# Ensure this matches the FLASK_HOST and FLASK_PORT in your main_app.py
BASE_URL = "http://127.0.0.1:5001"

# --- Dummy Files for Testing ---
DUMMY_TEXT_FILENAME = "test_document.txt"
DUMMY_TEXT_CONTENT = "This is a dummy document for testing purposes. It contains some sample text for classification."

DUMMY_AUDIO_FILENAME = "test_audio.wav"
# A very basic silent WAV header (44 bytes for a 1-second silent WAV)
# For actual transcription testing, you'd replace this with a real audio file
# that is at least 0.1 seconds long to avoid the "Audio file is too short" error.
DUMMY_AUDIO_CONTENT = (
    b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
)

def create_dummy_files():
    """Creates dummy files required for testing."""
    with open(DUMMY_TEXT_FILENAME, "w") as f:
        f.write(DUMMY_TEXT_CONTENT)
    print(f"Created dummy file: {DUMMY_TEXT_FILENAME}")

    with open(DUMMY_AUDIO_FILENAME, "wb") as f:
        f.write(DUMMY_AUDIO_CONTENT)
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

if __name__ == "__main__":
    try:
        run_all_tests()
    finally:
        # Ensure dummy files are cleaned up even if tests fail
        cleanup_dummy_files()
