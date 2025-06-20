#!/usr/bin/env python3
"""
Test script for:
1. Backend initialization loop fix
2. Chat renaming functionality
"""

import sys
import os
import json
import tempfile
import shutil
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_test_environment():
    """Set up a temporary test environment."""
    test_dir = tempfile.mkdtemp(prefix="backend_fixes_test_")
    
    import backend
    original_get_chatbot_dir = backend.get_chatbot_dir
    def mock_get_chatbot_dir():
        return test_dir
    
    backend.get_chatbot_dir = mock_get_chatbot_dir
    backend.CHAT_SESSIONS_PATH = os.path.join(test_dir, 'data', 'chat_sessions')
    backend.USER_DB_PATH = os.path.join(test_dir, 'data', 'user_info', 'users.json')
    
    os.makedirs(backend.CHAT_SESSIONS_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(backend.USER_DB_PATH), exist_ok=True)
    
    return test_dir, original_get_chatbot_dir

def cleanup_test_environment(test_dir, original_get_chatbot_dir):
    """Clean up the test environment."""
    import backend
    backend.get_chatbot_dir = original_get_chatbot_dir
    shutil.rmtree(test_dir, ignore_errors=True)

def test_backend_initialization_no_loop():
    """Test that backend initialization doesn't loop infinitely."""
    print("🔄 Testing backend initialization (no infinite loops)...")
    
    try:
        import backend
        
        # Reset the initialization flag for testing
        backend._backend_initialized = False
        
        start_time = time.time()
        
        # Test multiple initialization calls - should not cause loops
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # First initialization
            loop.run_until_complete(backend.init_backend())
            first_init_time = time.time() - start_time
            
            # Second initialization (should be skipped)
            second_start = time.time()
            loop.run_until_complete(backend.init_backend())
            second_init_time = time.time() - second_start
            
            # Third initialization (should also be skipped)
            third_start = time.time()
            loop.run_until_complete(backend.init_backend())
            third_init_time = time.time() - third_start
            
        finally:
            loop.close()
        
        total_time = time.time() - start_time
        
        print(f"  ⏱️ First initialization: {first_init_time:.2f}s")
        print(f"  ⏱️ Second initialization: {second_init_time:.3f}s (should be fast)")
        print(f"  ⏱️ Third initialization: {third_init_time:.3f}s (should be fast)")
        print(f"  ⏱️ Total time: {total_time:.2f}s")
        
        # Verify subsequent calls are much faster (indicating they're skipped)
        assert second_init_time < 1.0, f"Second init too slow: {second_init_time:.3f}s"
        assert third_init_time < 1.0, f"Third init too slow: {third_init_time:.3f}s"
        assert total_time < 60.0, f"Total time too long: {total_time:.2f}s (possible infinite loop)"
        
        print("✅ Backend initialization loop fix working")
        return True
        
    except Exception as e:
        print(f"❌ Backend initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_renaming():
    """Test the chat renaming functionality."""
    print("🏷️ Testing chat renaming functionality...")
    
    try:
        import backend
        
        username = "test_user"
        
        # Create a test chat
        original_chat_id = backend.create_and_persist_new_chat(username)
        
        # Add some content to the chat
        user_folder = os.path.join(backend.CHAT_SESSIONS_PATH, username)
        chat_file = os.path.join(user_folder, f"{original_chat_id}.json")
        
        test_content = {
            "messages": [
                {"role": "user", "content": "Hello, this is a test message"},
                {"role": "assistant", "content": "Hello! How can I help you today?"}
            ]
        }
        
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(test_content, f, indent=2)
        
        print(f"  📝 Created test chat: '{original_chat_id}'")
        
        # Test renaming
        new_name = "My Awesome Chat"
        result = backend.rename_chat(original_chat_id, new_name, username)
        
        assert result["success"], f"Rename failed: {result.get('error', 'Unknown error')}"
        new_chat_id = result["new_chat_id"]
        
        print(f"  ✅ Renamed to: '{new_chat_id}'")
        
        # Verify old file is gone and new file exists
        old_file = os.path.join(user_folder, f"{original_chat_id}.json")
        new_file = os.path.join(user_folder, f"{new_chat_id}.json")
        
        assert not os.path.exists(old_file), "Old chat file should be deleted"
        assert os.path.exists(new_file), "New chat file should exist"
        
        # Verify content is preserved
        with open(new_file, 'r', encoding='utf-8') as f:
            preserved_content = json.load(f)
        
        assert preserved_content == test_content, "Chat content should be preserved"
        
        print("  ✅ Content preserved correctly")
        
        # Test edge cases
        print("  🧪 Testing edge cases...")
        
        # Empty name
        result = backend.rename_chat(new_chat_id, "", username)
        assert not result["success"], "Should fail with empty name"
        
        # Invalid characters in name
        result = backend.rename_chat(new_chat_id, "Test<>Chat", username)
        assert result["success"], "Should handle invalid characters"
        if result["success"]:
            print(f"    ✅ Invalid chars handled: '{result['new_chat_id']}'")
        
        # Non-existent chat
        result = backend.rename_chat("nonexistent_chat", "New Name", username)
        assert not result["success"], "Should fail for non-existent chat"
        
        print("✅ Chat renaming functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Chat renaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chatbot_ui_with_rename():
    """Test the enhanced chatbot UI with rename functionality."""
    print("🎨 Testing chatbot UI with rename functionality...")
    
    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui
        
        # Test creating UI with rename components
        with gr.Blocks() as test_app:
            username_state = gr.State("test_user")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")
            
            components = chatbot_ui(username_state, chat_history_state, chat_id_state, setup_events=False)
            
            # Should return 11 components now (including rename)
            assert len(components) == 11, f"Expected 11 components, got {len(components)}"
            
            chat_selector, new_chat_btn, chatbot, chat_input, send_btn, search_input, search_btn, search_results, rename_input, rename_btn, debug_md = components
            
            # Verify all components exist
            assert chat_selector is not None, "Chat selector should exist"
            assert new_chat_btn is not None, "New chat button should exist"
            assert chatbot is not None, "Chatbot should exist"
            assert chat_input is not None, "Chat input should exist"
            assert send_btn is not None, "Send button should exist"
            assert search_input is not None, "Search input should exist"
            assert search_btn is not None, "Search button should exist"
            assert search_results is not None, "Search results should exist"
            assert rename_input is not None, "Rename input should exist"
            assert rename_btn is not None, "Rename button should exist"
            assert debug_md is not None, "Debug markdown should exist"
            
            print(f"  ✅ All 11 components created successfully")
            print(f"    - Components: {[type(c).__name__ for c in components]}")
        
        print("✅ Chatbot UI with rename functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Chatbot UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests for backend fixes and rename functionality."""
    print("🔧 Testing Backend Fixes and Chat Renaming")
    print("=" * 50)
    print("Features being tested:")
    print("  1. Backend initialization loop prevention")
    print("  2. Chat renaming functionality")
    print("  3. Enhanced chatbot UI with rename")
    print("=" * 50)
    
    # Set up test environment
    test_dir, original_get_chatbot_dir = setup_test_environment()
    
    try:
        tests = [
            ("Backend Initialization Fix", test_backend_initialization_no_loop),
            ("Chat Renaming", test_chat_renaming),
            ("Chatbot UI with Rename", test_chatbot_ui_with_rename),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n📊 Test Results Summary")
        print("-" * 30)
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            print("✅ Backend initialization loops fixed")
            print("✅ Chat renaming functionality working")
            print("✅ Enhanced UI with rename feature")
            print("\n🚀 Ready to use enhanced chatbot!")
        else:
            print("\n❌ Some tests failed!")
            print("Please check the issues above.")
        
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
