from typing import Dict, Any, List, Tuple, Union
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
    """
    Create the chat interface components and add them to app_data.
    
    This function creates the chat UI components including:
    - Chat history display
    - Message input
    - Send button
    - Chat history state
    
    Args:
        app_data (Dict[str, Any]): Dictionary containing Gradio components and states.
    """
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