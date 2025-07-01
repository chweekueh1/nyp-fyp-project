#!/usr/bin/env python3
"""
Demo script for the integrated chatbot interface with chat history loading.

This demonstrates the enhanced chatbot interface that:
1. Loads existing chat sessions for a user
2. Allows switching between different chat sessions
3. Creates new chat sessions
4. Persists messages to chat session files
5. Displays chat history from previous sessions
"""

import gradio as gr
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from gradio_modules.chatbot import chatbot_ui


def create_demo_app():
    """Create a demo application with the integrated chatbot interface."""

    with gr.Blocks(title="Chatbot with History Demo") as app:
        gr.Markdown("# 🤖 Chatbot with Chat History Integration")
        gr.Markdown("""
        This demo showcases the enhanced chatbot interface with:
        - **Chat History Loading**: Automatically loads your previous chat sessions
        - **Chat Session Management**: Switch between different conversations
        - **New Chat Creation**: Start fresh conversations anytime
        - **Message Persistence**: All messages are saved to your chat history

        **Instructions:**
        1. Enter a username to simulate login
        2. Your existing chats will load in the dropdown
        3. Select a chat to view its history
        4. Send messages - they'll be saved automatically
        5. Create new chats using the "New Chat" button
        """)

        # User login simulation
        with gr.Row():
            username_input = gr.Textbox(
                label="Username (for demo)",
                placeholder="Enter username (e.g., 'test')",
                value="test",
            )
            login_btn = gr.Button("Login", variant="primary")

        # Login status
        login_status = gr.Markdown("Please enter a username and click Login")

        # Main chatbot interface (initially hidden)
        with gr.Column(visible=False) as chatbot_container:
            gr.Markdown("## Chat Interface")

            # States
            username_state = gr.State("")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")

            # Chat management row
            chatbot_ui(username_state, chat_history_state, chat_id_state)
            # Components are automatically displayed by the chatbot_ui function

        def handle_login(username):
            """Handle user login and show chatbot interface."""
            if not username.strip():
                return (
                    gr.update(value="❌ Please enter a username"),
                    gr.update(visible=False),
                    "",
                )

            return (
                gr.update(value=f"✅ Logged in as: {username}"),
                gr.update(visible=True),
                username.strip(),
            )

        # Login event
        login_btn.click(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state],
        )

        # Also allow Enter key in username field
        username_input.submit(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state],
        )

    return app


def main():
    """Run the demo application."""
    print("🚀 Starting Chatbot with History Demo...")
    print("📝 This demo shows the integrated chatbot interface with:")
    print("   - Chat history loading")
    print("   - Chat session management")
    print("   - Message persistence")
    print("   - New chat creation")
    print()

    app = create_demo_app()

    # Launch the app
    app.launch(debug=True, share=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()
