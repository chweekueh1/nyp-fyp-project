import gradio as gr
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions directly
from backend import ask_question, get_chat_history, save_message_async

def test_chat_interface():
    """Test the chat interface with all features."""
    with gr.Blocks(title="Chat Interface Test") as app:
        # Initialize states
        logged_in_state = gr.State(True)  # Start logged in for testing
        username_state = gr.State("test")
        current_chat_id_state = gr.State("test_chat_id")
        chat_history_state = gr.State([])
        
        # Header
        gr.Markdown("# Chat Interface Test")
        
        # Import and create chat interface
        from gradio_modules.chat_interface import chat_interface
        
        chat_interface(
            logged_in_state=logged_in_state,
            username_state=username_state,
            current_chat_id_state=current_chat_id_state,
            chat_history_state=chat_history_state
        )
        
        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Send Message:** Type a message and click Send
        2. **Chat History:** Messages should appear in the chat history
        3. **Error Handling:** Try sending empty messages
        4. **State Updates:** Chat history should update properly
        
        **Expected Behavior:**
        - Send button should be responsive
        - Messages should appear in chat history
        - Backend functions should be called directly
        - Error messages should show for invalid inputs
        """)
    
    return app

def test_chatbot_interface():
    """Test the chatbot interface."""
    
    async def handle_chat_message(message, username, chat_id, chat_history):
        """Handle chat message using backend function directly."""
        print(f"Chat message: {message} from {username} in chat {chat_id}")
        try:
            if not message or not message.strip():
                return chat_history, "❌ Please enter a message"
            
            # Call backend function directly
            result = await ask_question(message, chat_id, username)
            print(f"Backend chat result: {result}")
            
            if result.get('code') == '200':
                # Add user message to history
                user_message = {"role": "user", "content": message, "timestamp": "2024-01-01T10:00:00Z"}
                assistant_message = {"role": "assistant", "content": result.get('answer', 'No response'), "timestamp": "2024-01-01T10:00:01Z"}
                
                new_history = chat_history + [user_message, assistant_message]
                return new_history, f"✅ Response: {result.get('answer', 'No response')}"
            else:
                return chat_history, f"❌ Chat error: {result.get('message', 'Unknown error')}"
        except Exception as e:
            print(f"Chat error: {e}")
            return chat_history, f"❌ Chat error: {str(e)}"
    
    with gr.Blocks(title="Chatbot Interface Test") as app:
        # Initialize states
        logged_in_state = gr.State(True)
        username_state = gr.State("test")
        chat_history_state = gr.State([])
        chat_id_state = gr.State("test_chat_id")
        
        # Header
        gr.Markdown("# Chatbot Interface Test")
        
        # Input and output
        message_input = gr.Textbox(label="Message", placeholder="Type your message here...")
        send_button = gr.Button("Send", variant="primary")
        chat_output = gr.Markdown("Chat history will appear here...")
        status_output = gr.Markdown("Status: Ready")
        
        # Event handler
        send_button.click(
            fn=handle_chat_message,
            inputs=[message_input, username_state, chat_id_state, chat_history_state],
            outputs=[chat_history_state, status_output],
            api_name="send_message"
        )
        
        # Update chat display when history changes
        def update_chat_display(history):
            if not history:
                return "No messages yet..."
            
            display = ""
            for msg in history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                display += f"**{role.title()}** ({timestamp}): {content}\n\n"
            return display
        
        chat_history_state.change(
            fn=update_chat_display,
            inputs=[chat_history_state],
            outputs=[chat_output],
            api_name="update_chat_display"
        )
        
        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Send Message:** Type a message and click Send
        2. **Chatbot Response:** Should get a response from the backend
        3. **History Updates:** Chat history should update with new messages
        4. **Error Handling:** Try sending empty messages
        
        **Expected Behavior:**
        - Send button should be responsive
        - Backend should generate responses
        - Chat history should update properly
        - Error messages should show for invalid inputs
        """)
    
    return app

if __name__ == "__main__":
    print("Creating chat interface test...")
    app = test_chat_interface()
    print("Launching chat interface test...")
    app.launch(debug=True, share=False)