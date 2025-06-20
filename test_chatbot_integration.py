#!/usr/bin/env python3
"""
Test script for the integrated chatbot interface with chat history loading.

This script tests:
1. Chat history loading functionality
2. Chat session management (create new chat, select chat)
3. Message persistence to chat session files
4. Integration between frontend and backend
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import gradio as gr
from gradio_modules.chatbot import chatbot_ui, load_all_chats
import backend

def setup_test_environment():
    """Set up a temporary test environment."""
    # Create a temporary directory for test data
    test_dir = tempfile.mkdtemp(prefix="chatbot_test_")
    
    # Override the chatbot directory for testing
    original_get_chatbot_dir = backend.get_chatbot_dir
    def mock_get_chatbot_dir():
        return test_dir
    
    # Monkey patch the function
    backend.get_chatbot_dir = mock_get_chatbot_dir
    
    # Update paths
    backend.CHAT_SESSIONS_PATH = os.path.join(test_dir, 'data', 'chat_sessions')
    backend.USER_DB_PATH = os.path.join(test_dir, 'data', 'user_info', 'users.json')
    
    # Create necessary directories
    os.makedirs(backend.CHAT_SESSIONS_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(backend.USER_DB_PATH), exist_ok=True)
    
    return test_dir, original_get_chatbot_dir

def cleanup_test_environment(test_dir, original_get_chatbot_dir):
    """Clean up the test environment."""
    backend.get_chatbot_dir = original_get_chatbot_dir
    shutil.rmtree(test_dir, ignore_errors=True)

def create_test_chat_data(username="test_user"):
    """Create some test chat data."""
    user_folder = os.path.join(backend.CHAT_SESSIONS_PATH, username)
    os.makedirs(user_folder, exist_ok=True)
    
    # Create test chat 1
    chat1_data = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
            {"role": "user", "content": "What's the weather like?"},
            {"role": "assistant", "content": "I don't have access to real-time weather data, but I'd be happy to help you with other questions!"}
        ]
    }
    
    chat1_file = os.path.join(user_folder, "Chat 2024-01-01 10-00-00.json")
    with open(chat1_file, 'w', encoding='utf-8') as f:
        json.dump(chat1_data, f, indent=2)
    
    # Create test chat 2
    chat2_data = {
        "messages": [
            {"role": "user", "content": "Tell me a joke"},
            {"role": "assistant", "content": "Why don't scientists trust atoms? Because they make up everything!"}
        ]
    }
    
    chat2_file = os.path.join(user_folder, "Chat 2024-01-01 11-00-00.json")
    with open(chat2_file, 'w', encoding='utf-8') as f:
        json.dump(chat2_data, f, indent=2)
    
    return ["Chat 2024-01-01 10-00-00", "Chat 2024-01-01 11-00-00"]

def test_load_all_chats():
    """Test the load_all_chats function."""
    print("Testing load_all_chats function...")
    
    username = "test_user"
    create_test_chat_data(username)
    
    # Test loading chats
    all_chats = load_all_chats(username)
    
    assert len(all_chats) == 2, f"Expected 2 chats, got {len(all_chats)}"
    
    # Check chat content
    for chat_id, history in all_chats.items():
        assert len(history) > 0, f"Chat {chat_id} should have history"
        assert isinstance(history, list), f"History should be a list"
        for msg_pair in history:
            assert len(msg_pair) == 2, f"Each message pair should have 2 elements"
    
    print("✅ load_all_chats test passed")

def test_chat_history_loading():
    """Test chat history loading in the UI."""
    print("Testing chat history loading...")
    
    username = "test_user"
    chat_ids = create_test_chat_data(username)
    
    # Test get_chat_history function
    for chat_id in chat_ids:
        history = backend.get_chat_history(chat_id, username)
        assert len(history) > 0, f"Chat {chat_id} should have history"
        print(f"✅ Chat {chat_id} loaded with {len(history)} message pairs")
    
    print("✅ Chat history loading test passed")

def test_new_chat_creation():
    """Test creating new chat sessions."""
    print("Testing new chat creation...")
    
    username = "test_user"
    
    # Create a new chat
    new_chat_id = backend.create_and_persist_new_chat(username)
    assert new_chat_id, "New chat ID should not be empty"
    
    # Verify the chat file was created
    user_folder = os.path.join(backend.CHAT_SESSIONS_PATH, username)
    chat_file = os.path.join(user_folder, f"{new_chat_id}.json")
    assert os.path.exists(chat_file), f"Chat file should exist at {chat_file}"
    
    # Verify the file content
    with open(chat_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert "messages" in data, "Chat file should have 'messages' key"
        assert data["messages"] == [], "New chat should have empty messages"
    
    print(f"✅ New chat creation test passed - created {new_chat_id}")

def test_ui_components():
    """Test that UI components are created correctly."""
    print("Testing UI components...")
    
    # Create test states
    username_state = gr.State("test_user")
    chat_history_state = gr.State([])
    chat_id_state = gr.State("test_chat_id")
    
    # Test UI creation (without event setup to avoid Blocks context requirement)
    chat_selector, new_chat_btn, chatbot, chat_input, send_btn, debug_md = chatbot_ui(
        username_state, chat_history_state, chat_id_state, setup_events=False
    )
    
    # Verify components
    assert chat_selector is not None, "Chat selector should be created"
    assert new_chat_btn is not None, "New chat button should be created"
    assert chatbot is not None, "Chatbot component should be created"
    assert chat_input is not None, "Chat input should be created"
    assert send_btn is not None, "Send button should be created"
    assert debug_md is not None, "Debug markdown should be created"
    
    print("✅ UI components test passed")

def run_all_tests():
    """Run all tests."""
    print("🚀 Starting chatbot integration tests...")
    
    # Set up test environment
    test_dir, original_get_chatbot_dir = setup_test_environment()
    
    try:
        # Run tests
        test_load_all_chats()
        test_chat_history_loading()
        test_new_chat_creation()
        test_ui_components()
        
        print("\n🎉 All tests passed successfully!")
        print(f"Test data created in: {test_dir}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        # Clean up
        cleanup_test_environment(test_dir, original_get_chatbot_dir)
        print("🧹 Test environment cleaned up")

if __name__ == "__main__":
    run_all_tests()
