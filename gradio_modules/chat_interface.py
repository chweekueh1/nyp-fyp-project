from typing import Dict, Any, List, Tuple, Union
import gradio as gr
import logging
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from utils import setup_logging
from backend import get_chat_response

# Set up logging
logger = setup_logging()

def chat_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State
) -> None:
    """
    Create the chat interface components.
    
    This function creates the chat UI components including:
    - Chat history display
    - Message input
    - Send button
    - Chat history state
    
    Args:
        logged_in_state (gr.State): State for tracking login status
        username_state (gr.State): State for storing current username
        current_chat_id_state (gr.State): State for storing current chat ID
        chat_history_state (gr.State): State for storing chat history
    """
    with gr.Column(visible=False) as chat_container:
        chat_history = gr.Chatbot(
            label="Chat History",
            height=400,
            show_label=True
        )
        with gr.Row():
            msg = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
                show_label=False,
                container=False
            )
            send_button = gr.Button("Send")
            
        # Add send button click event
        send_button.click(
            fn=_handle_chat_message,
            inputs=[
                msg,
                chat_history_state,
                username_state
            ],
            outputs=[
                msg,
                chat_history_state
            ]
        )
        
        # Update chat display when history changes
        def update_chat_display(history):
            return history
            
        chat_history_state.change(
            fn=update_chat_display,
            inputs=[chat_history_state],
            outputs=[chat_history]
        )

def _handle_chat_message(msg: str, history: List[List[str]], username: str) -> Tuple[Dict[str, Any], List[List[str]]]:
    """
    Handle sending a chat message and updating the chat history.
    
    Args:
        msg (str): The message to send.
        history (List[List[str]]): Current chat history.
        username (str): Current username.
        
    Returns:
        Tuple[Dict[str, Any], List[List[str]]]: Updated message input and chat history.
    """
    if not msg:
        return {"value": ""}, history
        
    try:
        # Get response from backend
        response = get_chat_response(msg, username)
        # Update history with new message and response
        history.append([msg, response])
        return {"value": ""}, history
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        history.append([msg, f"Error: {str(e)}"])
        return {"value": ""}, history 