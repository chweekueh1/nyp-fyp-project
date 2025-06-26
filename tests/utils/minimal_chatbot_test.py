#!/usr/bin/env python3
"""
Minimal test app to verify chatbot UI integration works.
This creates a simplified version of the main app with just the chatbot functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import gradio as gr
from gradio_modules.chatbot import chatbot_ui

def create_minimal_test_app():
    """Create a minimal test app with just the chatbot functionality."""
    
    with gr.Blocks(title="Minimal Chatbot Test") as app:
        gr.Markdown("# 🧪 Minimal Chatbot UI Test")
        gr.Markdown("This is a simplified version to test if the chatbot UI integration works.")
        
        # Simple login simulation
        with gr.Row():
            username_input = gr.Textbox(label="Username", value="test_user")
            login_btn = gr.Button("Set Username", variant="primary")
        
        login_status = gr.Markdown("Enter a username above")
        
        # Main chatbot interface
        with gr.Column(visible=False) as chatbot_container:
            gr.Markdown("## Enhanced Chatbot Interface")
            
            # States
            username_state = gr.State("")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")
            
            # Enhanced chatbot UI
            chat_selector, new_chat_btn, chatbot, msg, send_btn, debug_md = chatbot_ui(
                username_state, chat_history_state, chat_id_state, setup_events=True
            )
            
            # Show debug info
            gr.Markdown("### Debug Info")
            debug_md
        
        def handle_login(username):
            """Handle username setting."""
            if not username.strip():
                return "❌ Please enter a username", gr.update(visible=False), ""
            
            return (
                f"✅ Username set to: {username}",
                gr.update(visible=True),
                username.strip()
            )
        
        # Login event
        login_btn.click(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state]
        )
        
        username_input.submit(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state]
        )
    
    return app

def main():
    """Run the minimal test app."""
    print("🧪 Starting Minimal Chatbot UI Test...")
    print()
    print("This test app will help verify that the chatbot UI integration works correctly.")
    print("It includes:")
    print("  ✅ Enhanced chatbot interface")
    print("  ✅ Chat history loading")
    print("  ✅ Message persistence")
    print("  ✅ Chat session management")
    print()
    print("Instructions:")
    print("  1. Enter a username (e.g., 'test_user')")
    print("  2. Click 'Set Username'")
    print("  3. The chatbot interface should appear")
    print("  4. Try creating new chats and sending messages")
    print()
    
    try:
        app = create_minimal_test_app()
        
        print("🌐 Launching test app...")
        print("If successful, this proves the chatbot UI integration is working!")
        print()
        
        app.launch(
            debug=True,
            share=False,
            server_name="127.0.0.1",
            server_port=7863  # Different port to avoid conflicts
        )
        
    except Exception as e:
        print(f"❌ Error launching test app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
