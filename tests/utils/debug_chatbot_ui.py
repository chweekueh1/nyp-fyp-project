#!/usr/bin/env python3
"""
Debug script to check if the chatbot UI components are being created correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_chatbot_ui():
    """Debug the chatbot UI integration."""
    print("🔍 Debugging chatbot UI integration...")

    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui, load_all_chats

        print("✅ Chatbot imports successful")

        # Test creating the chatbot UI components
        print("🧪 Testing chatbot UI component creation...")

        with gr.Blocks():
            # Create test states
            username_state = gr.State("test_user")
            chat_history_state = gr.State([])
            selected_chat_id = gr.State("")

            # Create the chatbot UI
            chat_selector, new_chat_btn, chatbot, msg, send_btn, chat_debug = (
                chatbot_ui(
                    username_state,
                    chat_history_state,
                    selected_chat_id,
                    setup_events=False,
                )
            )

            print("✅ Chatbot UI components created successfully")
            print(f"   - Chat selector: {type(chat_selector).__name__}")
            print(f"   - New chat button: {type(new_chat_btn).__name__}")
            print(f"   - Chatbot: {type(chatbot).__name__}")
            print(f"   - Message input: {type(msg).__name__}")
            print(f"   - Send button: {type(send_btn).__name__}")
            print(f"   - Debug markdown: {type(chat_debug).__name__}")

        # Test the load_all_chats function
        print("🧪 Testing load_all_chats function...")
        chats = load_all_chats("test_user")
        print(
            f"✅ load_all_chats returned: {type(chats).__name__} with {len(chats)} chats"
        )

        # Test the main app creation
        print("🧪 Testing main app creation...")
        from gradio_modules.main_app import main_app

        app = main_app()
        print("✅ Main app created successfully")

        # Check if the app has the expected structure
        print("🔍 Checking main app structure...")

        # Try to access the app's internal structure (this is a bit hacky but useful for debugging)
        if hasattr(app, "blocks"):
            print(f"✅ App has blocks: {len(app.blocks)} components")

            # Look for chatbot-related components
            chatbot_components = []
            for block in app.blocks.values():
                if hasattr(block, "label"):
                    if (
                        "chat" in str(block.label).lower()
                        or "message" in str(block.label).lower()
                    ):
                        chatbot_components.append(
                            f"{type(block).__name__}: {block.label}"
                        )

            if chatbot_components:
                print("✅ Found chatbot-related components:")
                for comp in chatbot_components:
                    print(f"   - {comp}")
            else:
                print("⚠️ No chatbot-related components found in app structure")

        return True

    except Exception as e:
        print(f"❌ Error debugging chatbot UI: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_manual_integration():
    """Test manual integration of chatbot UI in a simple app."""
    print("\n🧪 Testing manual chatbot UI integration...")

    try:
        import gradio as gr
        from gradio_modules.chatbot import chatbot_ui

        with gr.Blocks(title="Debug Chatbot UI") as debug_app:
            gr.Markdown("# Debug Chatbot UI Integration")

            # States
            username_state = gr.State("debug_user")
            chat_history_state = gr.State([])
            selected_chat_id = gr.State("")

            # Create chatbot UI
            with gr.Tab("Chat"):
                chat_selector, new_chat_btn, chatbot, msg, send_btn, chat_debug = (
                    chatbot_ui(
                        username_state,
                        chat_history_state,
                        selected_chat_id,
                        setup_events=True,
                    )
                )

        print("✅ Manual integration test successful")
        print(
            "🌐 You can launch this debug app to see if the chatbot UI displays correctly"
        )

        # Optionally launch the debug app
        response = input("Launch debug app? (y/n): ").strip().lower()
        if response == "y":
            print("🚀 Launching debug app...")
            debug_app.launch(debug=True, share=False, server_port=7862)

        return True

    except Exception as e:
        print(f"❌ Error in manual integration test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 Chatbot UI Debug Tool")
    print("=" * 50)

    success1 = debug_chatbot_ui()
    success2 = test_manual_integration()

    if success1 and success2:
        print("\n🎉 All debug tests passed!")
        print("The chatbot UI should be working correctly.")
        print(
            "If you're still not seeing it in the main app, it might be a visual/CSS issue."
        )
    else:
        print("\n❌ Some debug tests failed!")
        print("There may be integration issues that need to be fixed.")

    sys.exit(0 if (success1 and success2) else 1)
