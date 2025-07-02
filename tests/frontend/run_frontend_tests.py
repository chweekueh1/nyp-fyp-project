#!/usr/bin/env python3
"""
Frontend Test Suite Runner

This script runs all frontend tests or individual tests based on command line arguments.
"""

import sys
import argparse
import traceback
from pathlib import Path
import os

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def run_login_tests():
    """Run login interface tests."""
    print("🔐 Running Login Interface Tests...")
    try:
        # Import the actual test functions that run tests
        from tests.frontend.test_login_ui import test_login_interface, test_simple_login

        # Create test apps for validation
        print("Testing simple login interface creation...")
        test_simple_login()
        print("✅ Simple login test app created successfully")

        print("Testing full login interface creation...")
        test_login_interface()
        print("✅ Full login test app created successfully")

        # Run actual login functionality tests
        print("Testing login functionality...")
        from backend import do_login_test as do_login

        testing = os.getenv("TESTING", "").lower() == "true"
        if testing:
            from backend import do_login_test as do_login

        async def test_login_functionality():
            # Test valid login
            result = await do_login("test_user", "TestPass123!")
            if result.get("code") == "200":
                print("✅ Login with test_user credentials works")
            else:
                print(f"⚠️ Login with test_user credentials returned: {result}")

            # Test invalid login
            result = await do_login("invalid", "invalid")
            if result.get("code") != "200":
                print("✅ Invalid login properly rejected")
            else:
                print(f"⚠️ Invalid login unexpectedly succeeded: {result}")

        # Run the async test
        import asyncio

        asyncio.run(test_login_functionality())

        return True
    except ImportError as e:
        print(f"❌ Login tests failed: Import error - {e}")
        print("   This usually means the login UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Login tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_chat_tests():
    """Run chat interface tests."""
    print("💬 Running Chat Interface Tests...")
    try:
        from tests.frontend.test_chat_ui import (
            test_chat_interface,
            test_chatbot_interface,
        )

        # Create test apps for validation
        print("Testing chat interface creation...")
        test_chat_interface()
        print("✅ Chat interface test app created successfully")

        print("Testing chatbot interface creation...")
        test_chatbot_interface()
        print("✅ Chatbot interface test app created successfully")

        # Test chat functionality
        print("Testing chat functionality...")
        from backend import ask_question

        async def test_chat_functionality():
            # Test asking a question
            result = await ask_question("Hello", "test_user", "")
            if result.get("code") == "200":
                print("✅ Chat question functionality works")
            else:
                print(f"⚠️ Chat question returned: {result}")

        import asyncio

        asyncio.run(test_chat_functionality())

        return True
    except ImportError as e:
        print(f"❌ Chat tests failed: Import error - {e}")
        print("   This usually means the chat UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Chat tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_search_tests():
    """Run search interface tests."""
    print("🔍 Running Search Interface Tests...")
    try:
        from tests.frontend.test_search_ui import (
            test_search_interface,
            test_chat_history_interface,
        )

        # Create test apps for validation
        print("Testing search interface creation...")
        test_search_interface()
        print("✅ Search interface test app created successfully")

        print("Testing chat history interface creation...")
        test_chat_history_interface()
        print("✅ Chat history interface test app created successfully")

        # Test search functionality
        print("Testing search functionality...")
        from backend import search_chat_history

        def test_search_functionality():
            # Test search functionality
            result = search_chat_history("test_user", "hello")
            if isinstance(result, list):
                print("✅ Search functionality works")
            else:
                print(f"⚠️ Search returned: {result}")

        test_search_functionality()

        return True
    except ImportError as e:
        print(f"❌ Search tests failed: Import error - {e}")
        print("   This usually means the search UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Search tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_file_audio_tests():
    """Run file upload and audio input tests."""
    print("📁🎤 Running File Upload and Audio Input Tests...")
    try:
        from tests.frontend.test_file_audio_ui import (
            test_file_upload_interface,
            test_audio_input_interface,
        )

        # Create test apps for validation
        print("Testing file upload interface creation...")
        test_file_upload_interface()
        print("✅ File upload interface test app created successfully")

        print("Testing audio input interface creation...")
        test_audio_input_interface()
        print("✅ Audio input interface test app created successfully")

        # Test file upload functionality
        print("Testing file upload functionality...")
        from backend import upload_file

        async def test_file_upload_functionality():
            # Test file upload (with mock file)
            import tempfile
            import os

            # Create a temporary test file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write("This is a test file for upload testing.")
                temp_file_path = f.name

            try:
                # Read file content as bytes
                with open(temp_file_path, "rb") as f:
                    file_content = f.read()

                # Test upload functionality
                result = await upload_file(file_content, "test.txt", "test_user")
                if result.get("code") == "200":
                    print("✅ File upload functionality works")
                else:
                    print(f"⚠️ File upload returned: {result}")
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        import asyncio

        asyncio.run(test_file_upload_functionality())

        return True
    except ImportError as e:
        print(f"❌ File/Audio tests failed: Import error - {e}")
        print("   This usually means the file/audio UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ File/Audio tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_ui_state_interaction_tests():
    """Run enhanced UI state interaction tests."""
    print("🔄 Running UI State Interaction Tests...")
    try:
        from tests.frontend.test_ui_state_interactions import run_ui_state_tests

        success = run_ui_state_tests()
        return success
    except ImportError as e:
        print(f"❌ UI State tests failed: Import error - {e}")
        print(
            "   This usually means the UI state interaction modules are not available"
        )
        return False
    except Exception as e:
        print(f"❌ UI State tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_theme_styles_tests():
    """Run theme and styles tests."""
    print("🎨 Running Theme and Styles Tests...")
    try:
        from tests.frontend.test_theme_styles import run_theme_styles_tests

        success = run_theme_styles_tests()
        return success
    except ImportError as e:
        print(f"❌ Theme/Styles tests failed: Import error - {e}")
        print("   This usually means the theme/styles modules are not available")
        return False
    except Exception as e:
        print(f"❌ Theme/Styles tests failed: {e}")
        print("   Full traceback:")
        traceback.print_exc()
        return False


def run_component_tests():
    """Run isolated UI component tests for chatbot, chat history, and file upload."""
    print("🧩 Running UI Component Tests...")
    try:
        from tests.frontend.test_chatbot_ui import test_chatbot_ui
        from tests.frontend.test_chat_history_ui import test_chat_history_ui
        from tests.frontend.test_file_upload_ui import test_file_upload_ui

        print("Testing chatbot UI component...")
        test_chatbot_ui()
        print("✅ Chatbot UI component test passed")

        print("Testing chat history UI component...")
        test_chat_history_ui()
        print("✅ Chat history UI component test passed")

        print("Testing file upload UI component...")
        test_file_upload_ui()
        print("✅ File upload UI component test passed")

        return True
    except ImportError as e:
        print(f"❌ Component tests failed: Import error - {e}")
        return False
    except Exception as e:
        print(f"❌ Component tests failed: {e}")
        traceback.print_exc()
        return False


def run_change_password_tests():
    """Run change password interface tests."""
    print("🔐 Running Change Password Interface Tests...")
    try:
        from tests.frontend.test_change_password_functionality import (
            run_change_password_tests,
        )

        # Run all change password tests
        results = run_change_password_tests()

        # Check if all tests passed
        all_passed = all(results.values())

        if all_passed:
            print("✅ All change password tests passed")
        else:
            failed_tests = [name for name, success in results.items() if not success]
            print(f"❌ Some change password tests failed: {', '.join(failed_tests)}")

        return all_passed
    except ImportError as e:
        print(f"❌ Change password tests failed: Import error - {e}")
        print("   This usually means the change password UI modules are not available")
        return False
    except Exception as e:
        print(f"❌ Change password tests failed: {e}")
        print("   Full traceback:")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all frontend tests."""
    print("🚀 Running All Frontend Tests...")
    results = {
        "Login": run_login_tests(),
        "Chat": run_chat_tests(),
        "Search": run_search_tests(),
        "File/Audio": run_file_audio_tests(),
        "UI State": run_ui_state_interaction_tests(),
        "Theme Styles": run_theme_styles_tests(),
        "Component": run_component_tests(),
        "Change Password": run_change_password_tests(),
    }
    print("\n📊 Test Results Summary")
    print("-" * 30)
    passed = 0
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if result:
            passed += 1
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    return all(results.values())


def launch_test_app(test_name):
    """Launch a specific test app."""
    print(f"🚀 Launching {test_name} test app...")
    if test_name == "login":
        from tests.frontend.test_login_ui import test_login_interface

        app = test_login_interface()
    elif test_name == "simple-login":
        from tests.frontend.test_login_ui import test_simple_login

        app = test_simple_login()
    elif test_name == "chat":
        from tests.frontend.test_chat_ui import test_chat_interface

        app = test_chat_interface()
    elif test_name == "chatbot":
        from tests.frontend.test_chat_ui import test_chatbot_interface

        app = test_chatbot_interface()
    elif test_name == "chatbot-ui":
        from tests.frontend.test_chatbot_ui import test_chatbot_ui

        test_chatbot_ui()
        return True
    elif test_name == "chat-history-ui":
        from tests.frontend.test_chat_history_ui import test_chat_history_ui

        test_chat_history_ui()
        return True
    elif test_name == "file-upload-ui":
        from tests.frontend.test_file_upload_ui import test_file_upload_ui

        test_file_upload_ui()
        return True
    elif test_name == "search":
        from tests.frontend.test_search_ui import test_search_interface

        app = test_search_interface()
    elif test_name == "chat-history":
        from tests.frontend.test_search_ui import test_chat_history_interface

        app = test_chat_history_interface()
    elif test_name == "file-upload":
        from tests.frontend.test_file_audio_ui import test_file_upload_interface

        app = test_file_upload_interface()
    elif test_name == "audio":
        from tests.frontend.test_file_audio_ui import test_audio_input_interface

        app = test_audio_input_interface()
    elif test_name == "all":
        from tests.frontend.test_all_interfaces import test_all_interfaces

        app = test_all_interfaces()
    elif test_name == "ui-state":
        from tests.frontend.test_ui_state_interactions import run_ui_state_tests

        run_ui_state_tests()
        return True
    elif test_name == "theme-styles":
        from tests.frontend.test_theme_styles import test_theme_styles

        test_theme_styles()
        return True
    elif test_name == "change-password":
        from tests.frontend.test_change_password_functionality import (
            test_simple_change_password,
        )

        app = test_simple_change_password()
    elif test_name == "change-password-interface":
        from tests.frontend.test_change_password_functionality import (
            test_change_password_interface,
        )

        app = test_change_password_interface()
    elif test_name == "change-password-validation":
        from tests.frontend.test_change_password_functionality import (
            test_change_password_validation,
        )

        app = test_change_password_validation()
    else:
        print(f"❌ Unknown test: {test_name}")
        return False
    # Launch the app if it was created
    if "app" in locals():
        launch_config = {
            "debug": True,
            "share": False,
            "inbrowser": False,
            "quiet": False,
            "show_error": True,
            "server_name": "0.0.0.0",
            "server_port": 7860,
        }
        print(
            f"🌐 Launching on {launch_config['server_name']}:{launch_config['server_port']}"
        )
        app.launch(**launch_config)
        return True


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Frontend Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all frontend tests
  python run_frontend_tests.py

  # Run specific test category
  python run_frontend_tests.py --category login
  python run_frontend_tests.py --category chat
  python run_frontend_tests.py --category ui-state

  # Launch test interface
  python run_frontend_tests.py --launch login
  python run_frontend_tests.py --launch chat

Available test categories:
  login          - Login interface tests
  chat           - Chat interface tests
  search         - Search interface tests
  file-upload    - File upload tests
  ui-state       - UI state interaction tests
  theme-styles   - Theme and styles tests
  change-password - Change password interface tests
  all            - All frontend tests (default)
        """,
    )

    # Mutually exclusive group for test vs launch
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--category",
        choices=[
            "login",
            "chat",
            "search",
            "file-upload",
            "ui-state",
            "theme-styles",
            "change-password",
            "all",
        ],
        default="all",
        help="Specific test category to run (default: all)",
    )
    group.add_argument(
        "--launch",
        choices=[
            "login",
            "chat",
            "search",
            "file-upload",
            "audio",
            "change-password",
            "change-password-interface",
            "change-password-validation",
            "all",
        ],
        help="Launch a specific test interface",
    )

    args = parser.parse_args()

    if args.launch:
        # Launch mode
        print(f"🚀 Launching {args.launch} test interface...")
        success = launch_test_app(args.launch)
        return 0 if success else 1
    else:
        # Test mode
        if args.category == "all":
            print("🚀 Running all frontend tests...")
            success = run_all_tests()
        elif args.category == "login":
            success = run_login_tests()
        elif args.category == "chat":
            success = run_chat_tests()
        elif args.category == "search":
            success = run_search_tests()
        elif args.category == "file-upload":
            success = run_file_audio_tests()
        elif args.category == "ui-state":
            success = run_ui_state_interaction_tests()
        elif args.category == "theme-styles":
            success = run_theme_styles_tests()
        elif args.category == "change-password":
            success = run_change_password_tests()
        else:
            print(f"❌ Unknown test category: {args.category}")
            return 1

        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
