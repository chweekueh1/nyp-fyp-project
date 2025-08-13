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

import gradio as gr
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from backend.chat import (
    get_chatbot_response,
    get_consolidated_database,
)


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
        pairs = []
        last_user = None
        for entry in history:
            if entry.get("role") == "user":
                last_user = entry.get("content", "")
            elif entry.get("role") == "assistant" and last_user is not None:
                pairs.append([last_user, entry.get("content", "")])
                last_user = None
        if last_user is not None:
            pairs.append([last_user, ""])
        return pairs

    import difflib

    if not user_message or not username:
        history = db.get_chat_messages(chat_id)
        yield (
            to_gradio_pairs(history),
            "",
            gr.State({}),
            to_gradio_pairs(history),
            gr.update(),
        )

    history = db.get_chat_messages(chat_id)
    logger.info(f"Sending message for user {username}, chat {chat_id}: {user_message}")

    # Save user message ONLY if not a duplicate (last message is not the same)
    if (
        not history
        or history[-1].get("role") != "user"
        or history[-1].get("content") != user_message
    ):
        db.add_chat_message(chat_id, username, len(history), "user", user_message)
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
            yield (
                to_gradio_pairs(
                    history
                    + [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": full_response},
                    ]
                ),
                gr.update(value=""),
                gr.State({}),
                to_gradio_pairs(
                    history
                    + [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": full_response},
                    ]
                ),
                datetime.now().isoformat(),
            )
        history = db.get_chat_messages(chat_id)
        yield (
            to_gradio_pairs(history),
            gr.update(value=""),
            gr.State({}),
            to_gradio_pairs(history),
            datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(
            f"Error getting chatbot response for {username}, chat {chat_id}: {e}",
            exc_info=True,
        )
        history = db.get_chat_messages(chat_id)
        yield (
            to_gradio_pairs(
                history + [{"role": "assistant", "content": f"Error: {e}"}]
            ),
            gr.update(value=""),
            gr.State({}),
            to_gradio_pairs(
                history + [{"role": "assistant", "content": f"Error: {e}"}]
            ),
            gr.update(),
        )


async def _handle_clear_chat(username: str, chat_id: str, *_) -> tuple:
    chat_id = "default"
    db = get_consolidated_database()
    logger.info(f"Clearing chat for user: {username}, chat_id: {chat_id}")
    try:
        db.delete_chat_session(chat_id)
        yield (
            gr.update(value=[]),
            gr.State({}),
            chat_id,
            gr.update(value=f"Chat {chat_id}"),
            None,
        )
    except Exception as e:
        logger.warning(f"Exception clearing chat: {e}")
        yield (
            gr.update(value=[]),
            gr.State({}),
            chat_id,
            gr.update(value=f"Chat {chat_id}"),
            None,
        )
