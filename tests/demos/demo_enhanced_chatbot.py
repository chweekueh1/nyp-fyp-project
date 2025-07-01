#!/usr/bin/env python3
"""
Demo script showcasing the enhanced chatbot features:
1. 🔍 Searchable chat history
2. 🧠 Smart chat naming based on first message
3. 📝 Auto-updating dropdown when creating chats
"""

import sys
from pathlib import Path
import gradio as gr
from gradio_modules.chatbot import chatbot_ui

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def create_enhanced_demo():
    """Create a demo showcasing enhanced chatbot features."""

    with gr.Blocks(
        title="Enhanced Chatbot Demo",
        css="""
        .feature-highlight {
            background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
            border-left: 4px solid #0ea5e9;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0.5rem;
        }
        .demo-section {
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin: 1rem 0;
        }
    """,
    ) as app:
        gr.Markdown("# 🚀 Enhanced Chatbot Demo")

        gr.Markdown(
            """
        <div class="feature-highlight">
        <h3>✨ New Features Demonstrated:</h3>
        <ul>
            <li><strong>🔍 Smart Search:</strong> Search through all your chat history with intelligent matching</li>
            <li><strong>🧠 Auto-Naming:</strong> Chats get meaningful names based on your first message</li>
            <li><strong>📝 Live Updates:</strong> Chat dropdown updates automatically when you create new chats</li>
            <li><strong>🏷️ Chat Renaming:</strong> Rename any chat to organize your conversations better</li>
            <li><strong>🚀 Optimized Backend:</strong> No more infinite loading loops - fast and reliable</li>
        </ul>
        </div>
        """,
            elem_classes=["feature-highlight"],
        )

        # Login simulation
        with gr.Row():
            username_input = gr.Textbox(
                label="Username (Demo)",
                value="test",
                placeholder="Enter username for demo",
            )
            login_btn = gr.Button("Start Demo", variant="primary")

        login_status = gr.Markdown("Enter a username and click 'Start Demo' to begin")

        # Enhanced chatbot interface (initially hidden)
        with gr.Column(visible=False) as chatbot_container:
            gr.Markdown("## 💬 Enhanced Chatbot Interface")

            # States
            username_state = gr.State("")
            chat_history_state = gr.State([])
            chat_id_state = gr.State("")

            # Enhanced chatbot UI with search and rename
            (
                chat_selector,
                new_chat_btn,
                chatbot,
                msg,
                send_btn,
                search_input,
                search_btn,
                search_results,
                rename_input,
                rename_btn,
                debug_md,
            ) = chatbot_ui(
                username_state, chat_history_state, chat_id_state, setup_events=True
            )

            # Feature explanations
            with gr.Accordion("🎯 How to Test the Enhanced Features", open=False):
                gr.Markdown("""
                ### 🧠 Smart Chat Naming
                1. **Don't select a chat** from the dropdown
                2. Type a descriptive message like "How do I learn Python programming?"
                3. Click Send - a new chat will be created with a smart name like "Learn Python Programming"
                4. Notice the dropdown updates automatically with the new chat name

                ### 🏷️ Chat Renaming
                1. Select any chat from the dropdown
                2. Type a new name in the "Rename current chat" field
                3. Click the "🏷️ Rename" button or press Enter
                4. Watch the chat get renamed and the dropdown update instantly

                ### 🔍 Chat History Search
                1. Create a few chats with different topics (Python, JavaScript, databases, etc.)
                2. Use the search box to find specific conversations
                3. Try searching for keywords like "Python", "function", "database"
                4. Search results show matching chats with context

                ### 📝 Auto-Updating Dropdown
                1. Send messages without selecting a chat
                2. Watch the dropdown automatically update with new chat names
                3. Switch between chats to see your conversation history
                """)

            # Demo instructions
            gr.Markdown(
                """
            <div class="demo-section">
            <h3>🎮 Demo Instructions:</h3>
            <ol>
                <li><strong>Try Smart Naming:</strong> Type "How do I build a web application?" without selecting a chat</li>
                <li><strong>Create More Chats:</strong> Try "What is machine learning?" and "Database design best practices"</li>
                <li><strong>Test Renaming:</strong> Select a chat and rename it to "My Web Dev Chat" or similar</li>
                <li><strong>Test Search:</strong> Search for "web", "machine", or "database" to find your chats</li>
                <li><strong>Switch Chats:</strong> Use the dropdown to switch between your conversations</li>
            </ol>
            </div>
            """,
                elem_classes=["demo-section"],
            )

        def handle_login(username):
            """Handle demo login."""
            if not username.strip():
                return "❌ Please enter a username", gr.update(visible=False), ""

            return (
                f"✅ Demo started for: {username}",
                gr.update(visible=True),
                username.strip(),
            )

        # Login event
        login_btn.click(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state],
        )

        username_input.submit(
            fn=handle_login,
            inputs=[username_input],
            outputs=[login_status, chatbot_container, username_state],
        )

    return app


def main():
    """Run the enhanced chatbot demo."""
    print("🚀 Enhanced Chatbot Features Demo")
    print("=" * 50)
    print("🎯 Features being demonstrated:")
    print("   🔍 Smart search through chat history")
    print("   🧠 Intelligent chat naming from first message")
    print("   📝 Auto-updating chat dropdown")
    print("   💬 Enhanced user interface")
    print()
    print("📋 Demo Instructions:")
    print("   1. Enter a username and click 'Start Demo'")
    print("   2. Try sending messages without selecting a chat")
    print("   3. Watch how chats get smart names automatically")
    print("   4. Use the search feature to find your conversations")
    print("   5. Switch between chats using the dropdown")
    print()
    print("🌐 The demo will open in your browser...")
    print("=" * 50)

    try:
        app = create_enhanced_demo()

        app.launch(
            debug=True,
            share=False,
            server_name="127.0.0.1",
            server_port=7865,  # Different port to avoid conflicts
        )

    except Exception as e:
        print(f"❌ Error launching demo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
