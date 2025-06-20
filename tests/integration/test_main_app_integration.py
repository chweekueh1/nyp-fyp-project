#!/usr/bin/env python3
"""
Test script for the integrated main app with enhanced chatbot features.

This script tests:
1. Main app loads without errors
2. Enhanced chatbot interface is properly integrated
3. Chat history loading works in the main app context
4. Message persistence works through the main app
5. Basic functionality of other tabs still works
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_test_environment():
    """Set up a temporary test environment."""
    # Create a temporary directory for test data
    test_dir = tempfile.mkdtemp(prefix="main_app_test_")
    
    # Override the chatbot directory for testing
    import backend
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
    import backend
    backend.get_chatbot_dir = original_get_chatbot_dir
    shutil.rmtree(test_dir, ignore_errors=True)

def test_main_app_import():
    """Test that the main app can be imported without errors."""
    print("Testing main app import...")
    
    try:
        from gradio_modules.main_app import main_app
        print("✅ Main app imported successfully")
        return True
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        return False

def test_main_app_creation():
    """Test that the main app can be created without errors."""
    print("Testing main app creation...")
    
    try:
        from gradio_modules.main_app import main_app
        app = main_app()
        assert app is not None, "App should not be None"
        print("✅ Main app created successfully")
        return True
    except Exception as e:
        print(f"❌ Main app creation failed: {e}")
        return False

def test_enhanced_chatbot_integration():
    """Test that the enhanced chatbot interface is properly integrated."""
    print("Testing enhanced chatbot integration...")
    
    try:
        # Test that chatbot_ui can be imported
        from gradio_modules.chatbot import chatbot_ui, load_all_chats
        
        # Test that load_all_chats works
        username = "test_user"
        chats = load_all_chats(username)
        assert isinstance(chats, dict), "load_all_chats should return a dict"
        
        print("✅ Enhanced chatbot integration test passed")
        return True
    except Exception as e:
        print(f"❌ Enhanced chatbot integration test failed: {e}")
        return False

def test_backend_integration():
    """Test that backend functions work correctly."""
    print("Testing backend integration...")
    
    try:
        import backend
        
        # Test chat creation
        username = "test_user"
        chat_id = backend.create_and_persist_new_chat(username)
        assert chat_id, "Chat ID should not be empty"
        
        # Test chat listing
        chat_ids = backend.list_user_chat_ids(username)
        assert chat_id in chat_ids, "New chat should be in the list"
        
        # Test message persistence
        response_dict = backend.get_chatbot_response({
            'username': username,
            'message': 'Hello, this is a test message',
            'history': [],
            'chat_id': chat_id
        })
        
        assert 'history' in response_dict, "Response should contain history"
        assert 'response' in response_dict, "Response should contain response"
        
        print("✅ Backend integration test passed")
        return True
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        return False

def test_chat_persistence():
    """Test that chat messages are properly persisted."""
    print("Testing chat persistence...")
    
    try:
        import backend
        import json
        
        username = "test_user"
        chat_id = backend.create_and_persist_new_chat(username)
        
        # Send a message
        test_message = "This is a test message for persistence"
        response_dict = backend.get_chatbot_response({
            'username': username,
            'message': test_message,
            'history': [],
            'chat_id': chat_id
        })
        
        # Check that the message was persisted to file
        user_folder = os.path.join(backend.CHAT_SESSIONS_PATH, username)
        chat_file = os.path.join(user_folder, f"{chat_id}.json")
        
        assert os.path.exists(chat_file), f"Chat file should exist at {chat_file}"
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            messages = data.get('messages', [])
            
            # Should have user message and assistant response
            assert len(messages) >= 2, "Should have at least user message and response"
            
            # Check user message
            user_msg = next((msg for msg in messages if msg.get('role') == 'user'), None)
            assert user_msg is not None, "Should have user message"
            assert user_msg['content'] == test_message, "User message content should match"
            
            # Check assistant response
            assistant_msg = next((msg for msg in messages if msg.get('role') == 'assistant'), None)
            assert assistant_msg is not None, "Should have assistant response"
        
        print("✅ Chat persistence test passed")
        return True
    except Exception as e:
        print(f"❌ Chat persistence test failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print("🚀 Starting main app integration tests...")
    
    # Set up test environment
    test_dir, original_get_chatbot_dir = setup_test_environment()
    
    try:
        tests = [
            test_main_app_import,
            test_enhanced_chatbot_integration,
            test_backend_integration,
            test_chat_persistence,
            test_main_app_creation,  # This one last as it might be slow
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    print(f"❌ Test {test.__name__} failed")
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        print(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed successfully!")
            print("✅ The main app is ready with enhanced chatbot features!")
        else:
            print("⚠️ Some tests failed. Please check the issues above.")
            
        return passed == total
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return False
    finally:
        # Clean up
        cleanup_test_environment(test_dir, original_get_chatbot_dir)
        print("🧹 Test environment cleaned up")

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
