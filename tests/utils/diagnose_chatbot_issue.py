#!/usr/bin/env python3
"""
Comprehensive diagnostic tool to identify chatbot UI integration issues.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_file_structure():
    """Check if all required files exist."""
    print("🔍 Checking file structure...")
    
    required_files = [
        "app.py",
        "gradio_modules/chatbot.py",
        "backend.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def check_imports():
    """Check if all imports work correctly."""
    print("\n🔍 Checking imports...")
    
    try:
        import gradio as gr
        print("  ✅ gradio imported")
    except Exception as e:
        print(f"  ❌ gradio import failed: {e}")
        return False
    
    try:
        import backend
        print("  ✅ backend imported")
    except Exception as e:
        print(f"  ❌ backend import failed: {e}")
        return False
    
    try:
        from gradio_modules.chatbot import chatbot_ui, load_all_chats
        print("  ✅ chatbot module imported")
    except Exception as e:
        print(f"  ❌ chatbot module import failed: {e}")
        return False
    
    try:
        from gradio_modules.file_classification import file_classification_interface
        print("  ✅ file_classification imported")
    except Exception as e:
        print(f"  ❌ file_classification import failed: {e}")
        return False
    
    print("✅ All imports successful")
    return True

def check_chatbot_ui_creation():
    """Test creating chatbot UI components."""
    print("\n🔍 Testing chatbot UI component creation...")
    
    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui
        
        # Create test states
        username_state = gr.State("test_user")
        chat_history_state = gr.State([])
        chat_id_state = gr.State("")
        
        # Test creating components without events
        components = chatbot_ui(username_state, chat_history_state, chat_id_state, setup_events=False)

        print(f"  ✅ Chatbot UI created with {len(components)} components")
        print(f"  ✅ Component types: {[type(c).__name__ for c in components]}")

        # Check that we have the expected minimum components
        if len(components) >= 6:
            print("  ✅ Sufficient components returned")
        else:
            print(f"  ❌ Expected at least 6 components, got {len(components)}")
            return False
        
        print("✅ Chatbot UI components created successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Chatbot UI creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_main_app_structure():
    """Check the main app components."""
    print("\n🔍 Checking main app components...")

    try:
        from gradio_modules.login_and_register import login_interface
        from gradio_modules.file_classification import file_classification_interface
        from gradio_modules.audio_input import audio_interface

        print("  ✅ Login interface can be imported")
        print("  ✅ File classification interface can be imported")
        print("  ✅ Audio interface can be imported")

        print("✅ Main app components are available")
        return True

    except Exception as e:
        print(f"  ❌ Main app component import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_backend_functions():
    """Test backend functions."""
    print("\n🔍 Testing backend functions...")
    
    try:
        import backend
        
        # Test chat creation
        test_user = "diagnostic_test_user"
        chat_id = backend.create_and_persist_new_chat(test_user)
        print(f"  ✅ Created test chat: {chat_id}")
        
        # Test chat listing
        chat_ids = backend.list_user_chat_ids(test_user)
        if chat_id in chat_ids:
            print(f"  ✅ Chat appears in user's chat list")
        else:
            print(f"  ❌ Chat not found in user's chat list")
            return False
        
        # Test load_all_chats
        from gradio_modules.chatbot import load_all_chats
        all_chats = load_all_chats(test_user)
        if isinstance(all_chats, dict) and len(all_chats) > 0:
            print(f"  ✅ load_all_chats returned {len(all_chats)} chats")
        else:
            print(f"  ❌ load_all_chats failed or returned empty")
            return False
        
        print("✅ Backend functions working correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Backend function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_app():
    """Create a minimal test app to verify integration."""
    print("\n🔍 Creating test app...")
    
    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui
        
        with gr.Blocks(title="Diagnostic Test App") as test_app:
            gr.Markdown("# 🧪 Chatbot Integration Diagnostic")
            
            # States
            username_state = gr.State("diagnostic_user")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")
            
            # Show username
            gr.Markdown("**Current User:** diagnostic_user")
            
            # Create chatbot UI
            gr.Markdown("## Chatbot Interface")
            chatbot_components = chatbot_ui(
                username_state, chat_history_state, chat_id_state, setup_events=True
            )
            print(f"  ✅ Chatbot UI created with {len(chatbot_components)} components")
        
        print("  ✅ Test app created successfully")
        return test_app
        
    except Exception as e:
        print(f"  ❌ Test app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_diagnostics():
    """Run all diagnostic checks."""
    print("🔧 Chatbot UI Integration Diagnostics")
    print("=" * 50)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Imports", check_imports),
        ("Chatbot UI Creation", check_chatbot_ui_creation),
        ("Main App Structure", check_main_app_structure),
        ("Backend Functions", check_backend_functions),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("-" * 30)
    passed = 0
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All diagnostics passed!")
        print("The chatbot UI integration should be working correctly.")
        
        # Offer to create test app
        test_app = create_test_app()
        if test_app:
            print("\n🚀 Test app created successfully!")
            response = input("Launch test app to verify UI? (y/n): ").strip().lower()
            if response == 'y':
                print("Launching test app on port 7864...")
                test_app.launch(server_port=7864, debug=True)
    else:
        print("\n❌ Some diagnostics failed!")
        print("This indicates issues with the chatbot UI integration.")
        print("Please check the failed items above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
