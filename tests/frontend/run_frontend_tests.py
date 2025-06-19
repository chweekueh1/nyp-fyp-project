#!/usr/bin/env python3
"""
Frontend Test Suite Runner

This script runs all frontend tests or individual tests based on command line arguments.
"""

import sys
import argparse
import traceback
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def run_login_tests():
    """Run login interface tests."""
    print("🔐 Running Login Interface Tests...")
    try:
        from .test_login_ui import test_login_interface, test_simple_login
        
        print("Testing simple login interface...")
        app = test_simple_login()
        print("✅ Simple login test created successfully")
        
        print("Testing full login interface...")
        app = test_login_interface()
        print("✅ Full login test created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Login tests failed: Import error - {e}")
        print(f"   This usually means the login UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Login tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_chat_tests():
    """Run chat interface tests."""
    print("💬 Running Chat Interface Tests...")
    try:
        from .test_chat_ui import test_chat_interface, test_chatbot_interface
        
        print("Testing chat interface...")
        app = test_chat_interface()
        print("✅ Chat interface test created successfully")
        
        print("Testing chatbot interface...")
        app = test_chatbot_interface()
        print("✅ Chatbot interface test created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Chat tests failed: Import error - {e}")
        print(f"   This usually means the chat UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Chat tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_search_tests():
    """Run search interface tests."""
    print("🔍 Running Search Interface Tests...")
    try:
        from .test_search_ui import test_search_interface, test_chat_history_interface
        
        print("Testing search interface...")
        app = test_search_interface()
        print("✅ Search interface test created successfully")
        
        print("Testing chat history interface...")
        app = test_chat_history_interface()
        print("✅ Chat history interface test created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Search tests failed: Import error - {e}")
        print(f"   This usually means the search UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Search tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_file_audio_tests():
    """Run file upload and audio input tests."""
    print("📁🎤 Running File Upload and Audio Input Tests...")
    try:
        from .test_file_audio_ui import test_file_upload_interface, test_audio_input_interface
        
        print("Testing file upload interface...")
        app = test_file_upload_interface()
        print("✅ File upload interface test created successfully")
        
        print("Testing audio input interface...")
        app = test_audio_input_interface()
        print("✅ Audio input interface test created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ File/Audio tests failed: Import error - {e}")
        print(f"   This usually means the file/audio UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ File/Audio tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_ui_state_interaction_tests():
    """Run enhanced UI state interaction tests."""
    print("🔄 Running UI State Interaction Tests...")
    try:
        from .test_ui_state_interactions import run_ui_state_tests

        success = run_ui_state_tests()
        return success
    except ImportError as e:
        print(f"❌ UI State tests failed: Import error - {e}")
        print(f"   This usually means the UI state interaction modules are not available")
        return False
    except Exception as e:
        print(f"❌ UI State tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_theme_styles_tests():
    """Run theme and styles tests."""
    print("🎨 Running Theme and Styles Tests...")
    try:
        from .test_theme_styles import run_theme_styles_tests

        success = run_theme_styles_tests()
        return success
    except ImportError as e:
        print(f"❌ Theme/Styles tests failed: Import error - {e}")
        print(f"   This usually means the theme/styles modules are not available")
        return False
    except Exception as e:
        print(f"❌ Theme/Styles tests failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all frontend tests."""
    print("🚀 Running All Frontend Tests...")
    
    tests = [
        ("Login Tests", run_login_tests),
        ("Chat Tests", run_chat_tests),
        ("Search Tests", run_search_tests),
        ("File/Audio Tests", run_file_audio_tests),
        ("UI State Interaction Tests", run_ui_state_interaction_tests),
        ("Theme/Styles Tests", run_theme_styles_tests),
    ]
    
    results = []
    failed_tests = []
    error_messages = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"Running {test_name}")
            print('='*50)
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} completed successfully")
            else:
                print(f"❌ {test_name} failed")
                failed_tests.append(test_name)
                error_messages.append(f"{test_name}: Test function returned False")
        except KeyboardInterrupt:
            print(f"\n⚠️  {test_name} interrupted by user")
            results.append((test_name, False))
            failed_tests.append(test_name)
            error_messages.append(f"{test_name}: Interrupted by user")
            break
        except Exception as e:
            error_msg = f"Unexpected exception: {e}"
            print(f"❌ {test_name} failed with {error_msg}")
            print(f"   Full traceback:")
            traceback.print_exc()
            results.append((test_name, False))
            failed_tests.append(test_name)
            error_messages.append(f"{test_name}: {error_msg}")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if failed_tests:
        print(f"\nFailed test suites: {', '.join(failed_tests)}")
        
        # Display error messages
        if error_messages:
            print(f"\n{'='*50}")
            print("ERROR MESSAGES")
            print('='*50)
            for error_msg in error_messages:
                print(f"❌ {error_msg}")
    
    # Return tuple with success status and error messages if any
    if error_messages:
        return False, "; ".join(error_messages)
    else:
        return True

def launch_test_app(test_name):
    """Launch a specific test app."""
    print(f"🚀 Launching {test_name} test app...")
    
    if test_name == "login":
        from .test_login_ui import test_login_interface
        app = test_login_interface()
    elif test_name == "simple-login":
        from .test_login_ui import test_simple_login
        app = test_simple_login()
    elif test_name == "chat":
        from .test_chat_ui import test_chat_interface
        app = test_chat_interface()
    elif test_name == "chatbot":
        from .test_chat_ui import test_chatbot_interface
        app = test_chatbot_interface()
    elif test_name == "search":
        from .test_search_ui import test_search_interface
        app = test_search_interface()
    elif test_name == "chat-history":
        from .test_search_ui import test_chat_history_interface
        app = test_chat_history_interface()
    elif test_name == "file-upload":
        from .test_file_audio_ui import test_file_upload_interface
        app = test_file_upload_interface()
    elif test_name == "audio":
        from .test_file_audio_ui import test_audio_input_interface
        app = test_audio_input_interface()
    elif test_name == "all":
        from .test_all_interfaces import test_all_interfaces
        app = test_all_interfaces()
    elif test_name == "ui-state":
        from .test_ui_state_interactions import run_ui_state_tests
        run_ui_state_tests()
        return True
    elif test_name == "theme-styles":
        from .test_theme_styles import run_theme_styles_tests
        run_theme_styles_tests()
        return True
    else:
        print(f"❌ Unknown test: {test_name}")
        print("Available tests: login, simple-login, chat, chatbot, search, chat-history, file-upload, audio, ui-state, theme-styles, all")
        return False
    
    print(f"✅ {test_name} test app created successfully")
    print("Launching Gradio app...")
    app.launch(debug=True, share=False)
    return True

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Frontend Test Suite Runner")
    parser.add_argument(
        "action",
        choices=["test", "launch"],
        help="Action to perform: 'test' to run tests, 'launch' to launch a test app"
    )
    parser.add_argument(
        "--test",
        choices=["login", "simple-login", "chat", "chatbot", "search", "chat-history", "file-upload", "audio", "ui-state", "theme-styles", "all"],
        help="Specific test to run or launch"
    )
    
    args = parser.parse_args()
    
    if args.action == "test":
        if args.test:
            # Run specific test
            if args.test == "login":
                success = run_login_tests()
            elif args.test == "chat":
                success = run_chat_tests()
            elif args.test == "search":
                success = run_search_tests()
            elif args.test == "file-upload":
                success = run_file_audio_tests()
            elif args.test == "ui-state":
                success = run_ui_state_interaction_tests()
            elif args.test == "theme-styles":
                success = run_theme_styles_tests()
            else:
                print(f"❌ Unknown test: {args.test}")
                return 1
        else:
            # Run all tests
            success = run_all_tests()
        
        return 0 if success else 1
    
    elif args.action == "launch":
        if not args.test:
            print("❌ Please specify a test to launch with --test")
            return 1
        
        success = launch_test_app(args.test)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 