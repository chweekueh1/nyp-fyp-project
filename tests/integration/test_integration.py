#!/usr/bin/env python3
"""
Integration tests for backend API endpoints and LLM services.
Tests the integration between frontend, backend, and LLM components.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path to import modules
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from backend import ask_question, transcribe_audio_async, upload_file, data_classification, fuzzy_search_chats, render_all_chats
import asyncio
import wave
import numpy as np

"""
Integration tests for backend functions (no Flask routes - this backend uses Gradio).
"""

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



def run_all_tests():
    """Executes backend function tests (no Flask routes since this backend doesn't use Flask)."""
    print("Starting backend function tests...")
    print("Note: This backend uses Gradio interface, not Flask routes.")

    # Create dummy files at the start of testing
    create_dummy_files()

    test_username = "testuser_integration"

    try:
        # Test backend functions directly
        print("\n--- Testing Backend Functions Directly ---")

        # Test check_health function
        print("Testing check_health function...")
        from backend import check_health
        health_result = asyncio.run(check_health())
        print(f"Health check result: {health_result}")
        assert health_result.get('status') == 'OK'
        print("✅ Health check passed")

        # Test login/register functions
        print("Testing login/register functions...")
        from backend import do_login, do_register

        # Test registration
        register_result = asyncio.run(do_register(test_username, "testpass123"))
        print(f"Registration result: {register_result}")

        # Test login
        login_result = asyncio.run(do_login(test_username, "testpass123"))
        print(f"Login result: {login_result}")
        assert login_result.get('code') == '200'
        print("✅ Login/register functions passed")

        # Test chat functions
        print("Testing chat functions...")
        from backend import list_user_chat_ids, create_and_persist_new_chat

        # Create a chat
        chat_id = create_and_persist_new_chat(test_username)
        print(f"Created chat: {chat_id}")

        # List user chats
        user_chats = list_user_chat_ids(test_username)
        print(f"User chats: {user_chats}")
        assert chat_id in user_chats
        print("✅ Chat functions passed")

        print("\n--- All Backend Function Tests Completed Successfully ---")

    except Exception as e:
        print(f"❌ Backend function test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Clean up test user
        try:
            from backend import delete_test_user
            if delete_test_user(test_username):
                print(f"✅ Cleaned up test user: {test_username}")
            else:
                print(f"⚠️ Warning: Could not clean up test user: {test_username}")
        except Exception as cleanup_error:
            print(f"⚠️ Warning: Error during test user cleanup: {cleanup_error}")

        cleanup_dummy_files()

def setup_user_chats(tmp_path, user, chats):
    user_dir = tmp_path / "data" / "chat_sessions" / user
    user_dir.mkdir(parents=True, exist_ok=True)
    for chat_id, messages in chats.items():
        with open(user_dir / f"{chat_id}.json", "w") as f:
            json.dump(messages, f)
    return user_dir

def test_fuzzy_search_chats(tmp_path, monkeypatch):
    """Test fuzzy search functionality."""
    print("🔍 Testing fuzzy_search_chats function...")
    try:
        # Prepare mock data
        user = "testuser"
        chats = {
            "chat1": [
                {"role": "user", "content": "Hello, how are you?", "timestamp": "2024-01-01T10:00:00Z"},
                {"role": "assistant", "content": "I'm fine, thank you!", "timestamp": "2024-01-01T10:00:01Z"}
            ],
            "chat2": [
                {"role": "user", "content": "What is the weather today?", "timestamp": "2024-01-01T11:00:00Z"},
                {"role": "assistant", "content": "It's sunny.", "timestamp": "2024-01-01T11:00:01Z"}
            ]
        }
        setup_user_chats(tmp_path, user, chats)
        
        # Patch the data path
        monkeypatch.setattr("backend.CHAT_SESSIONS_PATH", str(tmp_path / "data" / "chat_sessions"))
        
        # Test fuzzy search for 'weather'
        result = fuzzy_search_chats(user, "weather")
        assert "chat2" in result
        assert "weather" in result.lower()
        print("  ✅ Weather search passed")
        
        # Test fuzzy search for 'hello'
        result = fuzzy_search_chats(user, "hello")
        assert "chat1" in result
        assert "hello" in result.lower()
        print("  ✅ Hello search passed")
        
        # Test fuzzy search for non-existent
        result = fuzzy_search_chats(user, "nonexistent")
        assert "No matching chats found" in result
        print("  ✅ Non-existent search passed")
        
        print("✅ test_fuzzy_search_chats: PASSED")
    except Exception as e:
        print(f"❌ test_fuzzy_search_chats: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_render_all_chats(tmp_path, monkeypatch):
    """Test render all chats functionality."""
    print("🔍 Testing render_all_chats function...")
    try:
        user = "testuser"
        chats = {
            "chat1": [
                {"role": "user", "content": "Hello, how are you?", "timestamp": "2024-01-01T10:00:00Z"},
                {"role": "assistant", "content": "I'm fine, thank you!", "timestamp": "2024-01-01T10:00:01Z"}
            ],
            "chat2": [
                {"role": "user", "content": "What is the weather today?", "timestamp": "2024-01-01T11:00:00Z"},
                {"role": "assistant", "content": "It's sunny.", "timestamp": "2024-01-01T11:00:01Z"}
            ]
        }
        setup_user_chats(tmp_path, user, chats)
        
        # Patch the data path
        monkeypatch.setattr("backend.CHAT_SESSIONS_PATH", str(tmp_path / "data" / "chat_sessions"))
        
        # Test rendering all chats
        result = render_all_chats(user)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == 2, f"Expected 2 chats, got {len(result)}"
        
        # Check chat structure
        for chat in result:
            assert 'chat_id' in chat, "Chat should have chat_id"
            assert 'chat_name' in chat, "Chat should have chat_name"
            assert 'message_count' in chat, "Chat should have message_count"
            assert 'last_message' in chat, "Chat should have last_message"
            assert 'timestamp' in chat, "Chat should have timestamp"
        
        print("  ✅ Chat structure validation passed")
        
        # Check that chat IDs are present
        chat_ids = [chat['chat_id'] for chat in result]
        assert "chat1" in chat_ids, "chat1 should be in results"
        assert "chat2" in chat_ids, "chat2 should be in results"
        print("  ✅ Chat IDs validation passed")
        
        print("✅ test_render_all_chats: PASSED")
    except Exception as e:
        print(f"❌ test_render_all_chats: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

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
    response = await transcribe_audio_async(audio_file, username)
    print(f"Transcribe Audio Response: {response}")
    assert response.get('code') == '200'

async def test_upload_file():
    """Test the upload_file function directly."""
    with open(DUMMY_TEXT_FILENAME, "rb") as f:
        file_content = f.read()
    filename = DUMMY_TEXT_FILENAME
    username = "testuser_upload"
    response = await upload_file(file_content, filename, username)
    print(f"Upload File Response: {response}")
    assert response.get('code') == '200'

async def test_data_classification():
    """Test the data_classification function directly."""
    with open(DUMMY_TEXT_FILENAME, "r") as f:
        content = f.read()
    response = await data_classification(content)
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

def run_integration_tests():
    """Run all integration tests."""
    print("🚀 Running integration tests...")
    print("=" * 60)
    
    test_functions = [
        run_all_tests,
        run_all_unit_tests,
    ]
    
    results = []
    failed_tests = []
    error_messages = []
    
    for test_func in test_functions:
        try:
            print(f"\n{'='*40}")
            print(f"Running: {test_func.__name__}")
            print(f"{'='*40}")
            test_func()
            print(f"✅ {test_func.__name__}: PASSED")
            results.append((test_func.__name__, True))
        except KeyboardInterrupt:
            print(f"\n⚠️  {test_func.__name__} interrupted by user")
            results.append((test_func.__name__, False))
            failed_tests.append(test_func.__name__)
            error_messages.append(f"{test_func.__name__}: Interrupted by user")
            break
        except Exception as e:
            error_msg = f"{e}"
            print(f"❌ {test_func.__name__}: FAILED - {error_msg}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
            failed_tests.append(test_func.__name__)
            error_messages.append(f"{test_func.__name__}: {error_msg}")
            # Continue with other tests instead of exiting
    
    # Summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} integration tests passed")
    
    if failed_tests:
        print(f"\nFailed tests: {', '.join(failed_tests)}")
        
        # Display error messages
        if error_messages:
            print(f"\n{'='*60}")
            print("ERROR MESSAGES")
            print('='*60)
            for error_msg in error_messages:
                print(f"❌ {error_msg}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
    else:
        print("💥 Some integration tests failed!")
    
    # Return tuple with success status and error messages if any
    if error_messages:
        return False, "; ".join(error_messages)
    else:
        return True

if __name__ == "__main__":
    result = run_integration_tests()
    if isinstance(result, tuple):
        success, error_messages = result
    else:
        success = result
    sys.exit(0 if success else 1) 