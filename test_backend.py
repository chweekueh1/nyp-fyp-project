# test_backend.py
import requests
import os
import json
import io

# --- Configuration ---
# Ensure this matches the FLASK_HOST and FLASK_PORT in your run.py and backend.py
BASE_URL = "http://127.0.0.1:5001"

# --- Dummy Files for Testing ---
# Create a dummy text file for upload and classification tests
DUMMY_TEXT_FILENAME = "test_document.txt"
DUMMY_TEXT_CONTENT = "This is a dummy document for testing purposes. It contains some sample text for classification."

# Create a dummy audio file for transcription tests (this will be a silent WAV)
DUMMY_AUDIO_FILENAME = "test_audio.wav"
# A very basic silent WAV header (44 bytes for a 1-second silent WAV)
# This is enough to create a valid-looking WAV file for upload testing.
# For actual transcription testing, you'd replace this with a real audio file.
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
    try:
        if method.lower() == 'get':
            response = requests.get(url, params=data, timeout=10)
        elif method.lower() == 'post':
            response = requests.post(url, data=data, files=files, json=json_data, timeout=30) # Increased timeout for processing
        else:
            print(f"Error: Unsupported method '{method}'")
            return False

        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
        print(f"--- {name} Test PASSED ---")
        return True
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
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON response from {url}. Response text: {response.text}")
        print(f"--- {name} Test FAILED ---")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during {name} test: {e}")
        print(f"--- {name} Test FAILED ---")
        return False

def run_all_tests():
    """Executes all backend route tests."""
    print("Starting backend route tests...")
