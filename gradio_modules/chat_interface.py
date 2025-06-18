from typing import Dict, Any
import gradio as gr
import logging
import asyncio
import os
import sys
from pathlib import Path
from utils import setup_logging

# Set up logging
logger = setup_logging()

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions
try:
    from backend import get_chat_response
except ImportError as e:
    logger.error(f"Failed to import backend functions: {e}")
    raise

def chat_interface(app_data: Dict[str, Any]) -> None:
    """Create the chat interface components and add them to app_data."""
    with gr.Column(visible=False) as chat_container:
        app_data['chat_history'] = gr.Chatbot(
            label="Chat History",
            height=400,
            show_label=True
        )
        with gr.Row():
            app_data['msg'] = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
                show_label=False,
                container=False
            )
            app_data['send_button'] = gr.Button("Send")
        app_data['chat_history_state'] = gr.State([])
        app_data['chat_container'] = chat_container
        # Add send button click event
        app_data['send_button'].click(
            fn=_handle_chat_message,
            inputs=[
                app_data['msg'],
                app_data['chat_history_state'],
                app_data['username_state']
            ],
            outputs=[
                app_data['msg'],
                app_data['chat_history_state']
            ]
        )

def _handle_chat_message(message: str, history: list, username: str) -> tuple[str, list]:
    """Handle chat message submission.
    
    Args:
        message: The message to send
        history: The chat history
        username: The username of the sender
        
    Returns:
        Tuple of (empty message, updated history)
    """
    if not message.strip():
        return message, history
    
    if not username:
        history.append((message, "Error: You must be logged in to send messages."))
        return "", history
    
    try:
        # Get response from backend
        response = get_chat_response(message, username)
        if not response:
            history.append((message, "Error: No response received from the server."))
            return "", history
            
        history.append((message, response))
        return "", history
    except Exception as e:
        logger.error(f"Error in chat handling: {e}")
        error_msg = "Sorry, I encountered an error. Please try again."
        if isinstance(e, ConnectionError):
            error_msg = "Error: Could not connect to the server. Please check your connection."
        elif isinstance(e, TimeoutError):
            error_msg = "Error: Request timed out. Please try again."
        history.append((message, error_msg))
        return "", history 