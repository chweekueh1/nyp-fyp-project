from typing import Dict, Any, List, Tuple, Union
import gradio as gr
import logging
import asyncio
import os
import sys
from pathlib import Path
import uuid

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from utils import setup_logging
from backend import ask_question, get_chat_history

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
        error_msg = gr.Markdown(visible=False, value="", elem_classes=["error-message"])
        with gr.Row():
            msg = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
                show_label=False,
                container=False
            )
            send_button = gr.Button("Send")

        # Ensure chat_id is initialized when chat starts
        def ensure_chat_id(chat_id):
            if not chat_id:
                return str(uuid.uuid4())
            return chat_id

        # Add send button click event
        send_button.click(
            fn=_handle_chat_message,
            inputs=[
                msg,
                chat_history_state,
                username_state,
                current_chat_id_state
            ],
            outputs=[
                msg,
                chat_history_state,
                error_msg
            ]
        )
        current_chat_id_state.change(
            fn=ensure_chat_id,
            inputs=[current_chat_id_state],
            outputs=[current_chat_id_state]
        )

        # Update chat display when history changes
        def update_chat_display(history):
            if not history:
                return []
            return history

        chat_history_state.change(
            fn=update_chat_display,
            inputs=[chat_history_state],
            outputs=[chat_history]
        )

    # Show chat_container when logged_in_state is True
    def show_chat(logged_in):
        return gr.update(visible=bool(logged_in))

    logged_in_state.change(
        fn=show_chat,
        inputs=[logged_in_state],
        outputs=[chat_container]
    )

async def _handle_chat_message(msg: str, history: List[List[str]], username: str, chat_id: str):
    """
    Handle sending a chat message and updating the chat history.
    Returns:
        Tuple[Dict[str, Any], List[List[str]], Dict[str, Any], str]: Updated message input, chat history, error message state, and chat_id.
    """
    if not msg or not msg.strip():
        return {"value": ""}, history or [], {"value": "Please enter a message.", "visible": True}, chat_id

    try:
        temp_chat_id = chat_id or str(uuid.uuid4())
        result = await ask_question(msg, temp_chat_id, username)
        logger.debug(f"ask_question result: {result}")

        # Use chat_id returned by backend if present, else fallback
        chat_id = str(result.get('chat_id', temp_chat_id))

        if result.get('code') == '200':
            response = result.get('response')
            if isinstance(response, dict) and 'answer' in response:
                answer = response['answer']
            else:
                answer = response if isinstance(response, str) else str(response)
            new_history = (history or []) + [[msg, answer]]
            return {"value": ""}, new_history, {"value": "", "visible": False}, chat_id
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"ask_question error: {error_msg}")
            return {"value": msg}, history or [], {"value": f"Error: {error_msg}", "visible": True}, chat_id
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        new_history = (history or []) + [[msg, f"Error: {str(e)}"]]
        return {"value": ""}, new_history, {"value": f"Error: {str(e)}", "visible": True}, chat_id