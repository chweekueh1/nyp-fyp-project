#!/usr/bin/env python3
"""
Chatbot Interface Module for the NYP FYP CNC Chatbot.

This module provides the main chatbot interface for the NYP FYP CNC Chatbot application.
Users can send messages.
The module integrates with Gradio to provide a web-based chat interface with:
- Real-time messaging with LLM-powered responses
- User-friendly UI components and state management
- Integration with backend chat and authentication systems
"""

#!/usr/bin/env python3
"""
Chatbot Interface Module for the NYP FYP CNC Chatbot.

This module provides the main chatbot interface for the NYP FYP CNC Chatbot application.
Users can send messages.
The module integrates with Gradio to provide a web-based chat interface with:
- Real-time messaging with LLM-powered responses
- User-friendly UI components and state management
- Integration with backend chat and authentication systems
"""

import logging
import difflib
import gradio as gr
from backend.chat import get_chatbot_response, get_consolidated_database

logger = logging.getLogger(__name__)


async def _handle_send_message(
    user_message: str,
    chat_history: list,  # Not used; real history from DB
    username: str,
    _unused_chat_id: str,
    *_,
) -> tuple:
    chat_id = "default"
    db = get_consolidated_database()

    def to_gradio_pairs(history):
        # Returns list of [user, bot] pairs for gr.Chatbot
        pairs = []
        current_pair = [None, None]
        for entry in history:
            if entry["role"] == "user":
                if current_pair[0] is not None or current_pair[1] is not None:
                    pairs.append(tuple(current_pair))
                    current_pair = [None, None]
                current_pair[0] = entry["content"]
            elif entry["role"] == "assistant":
                current_pair[1] = entry["content"]
                pairs.append(tuple(current_pair))
                current_pair = [None, None]
        if current_pair[0] is not None or current_pair[1] is not None:
            pairs.append(tuple(current_pair))
        return pairs

    if not user_message or not username:
        history = db.get_chat_messages(chat_id)
        return (
            to_gradio_pairs(history),
            "",  # Clear user input box
            gr.State({}),
            to_gradio_pairs(history),
            gr.update(),
        )

    history = db.get_chat_messages(chat_id)
    # Add user message to DB and history
    db.add_chat_message(chat_id, username, len(history), "user", user_message)
    history = db.get_chat_messages(chat_id)  # Refresh to include user message
    # Track API call for chat message
    db.add_api_call_record(
        username=username,
        endpoint="chat/send_message",
        method="POST",
        duration_ms=0,
        status_code=200,
        error_message=None,
    )

    # Debug: difflib matching score
    for msg in history:
        score = difflib.SequenceMatcher(
            None, user_message, msg.get("content", "")
        ).ratio()
        logger.debug(
            f"[DIFFLIB] Matching '{user_message}' with '{msg.get('content', '')}' => Score: {score}"
        )

    try:
        response_generator = get_chatbot_response(username, chat_id, user_message)
        full_response = ""
        async for chunk in response_generator:
            full_response += chunk
            # Track LLM call for each chunk
            db.add_api_call_record(
                username=username,
                endpoint="chatbot/llm_response",
                method="STREAM",
                duration_ms=0,
                status_code=200,
                error_message=None,
            )
        # Add assistant reply to DB and history
        db.add_chat_message(chat_id, username, len(history), "assistant", full_response)
        updated_history = db.get_chat_messages(chat_id)
        return (
            to_gradio_pairs(updated_history),  # gr.Chatbot history
            "",  # Clear user input box
            gr.State({}),
            to_gradio_pairs(updated_history),
            gr.update(),
        )
    except Exception as e:
        logger.error(f"Error during chatbot response: {e}", exc_info=True)
        return (
            to_gradio_pairs(history),
            f"Error: {str(e)}",
            gr.State({}),
            to_gradio_pairs(history),
            gr.update(),
        )
    except Exception as e:
        logger.error(f"Error during chatbot response: {e}", exc_info=True)
        return (
            to_gradio_pairs(history),
            f"Error: {str(e)}",
            gr.State({}),
            to_gradio_pairs(history),
            gr.update(),
        )
