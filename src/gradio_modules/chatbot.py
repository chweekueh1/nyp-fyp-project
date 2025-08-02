#!/usr/bin/env python3

"""
Chatbot Interface Module for the NYP FYP CNC Chatbot.

This module provides the main chatbot interface for the NYP FYP CNC Chatbot application.
Users can send messages, manage chat sessions, search history, and rename chats.

The module integrates with Gradio to provide a web-based chat interface with:
- Real-time messaging with LLM-powered responses
- Chat session management (create, load, rename, clear)
- Chat history search functionality
- User-friendly UI components and state management
- Integration with backend chat and authentication systems
"""

from typing import Tuple, Dict, Any, List
import gradio as gr
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# Import clear_chat_history from infra_utils

# Import specific backend functions
from backend.chat import (
    get_chatbot_response,  # This is now assumed to be an async generator
    rename_chat_session,
)

# --- Helper functions for chatbot_ui (these handle overall chat session management) ---


def _load_chat_by_id(
    selected_chat_id: str, username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, str]], str, str, str]:
    # Loads chat history for a selected chat ID from the `all_chats_data_state`.
    #
    # This function now only returns data/values, not interactive updates,
    # as interactivity is managed by app.py's _enable_chat_inputs_on_login.
    # It prepares the history as a list of lists (Gradio's chatbot format).

    if not selected_chat_id or selected_chat_id not in all_chats_data.get(username, {}):
        logger.warning(
            f"Attempted to load non-existent chat_id: {selected_chat_id} for user {username}"
        )
        # Return empty history and clear values if chat_id is invalid or not found
        return [], "", "", ""

    chat_data = all_chats_data[username][selected_chat_id]
    history = chat_data["history"]  # This is the stored [{"user": "", "bot": ""}, ...]
    chat_name = chat_data.get("chat_name", f"Chat {selected_chat_id}")
    last_updated_time = chat_data.get("last_updated_time", "N/A")

    formatted_history = []  # This will be the Gradio "messages" format
    for entry in history:
        if entry.get("user"):
            formatted_history.append({"role": "user", "content": entry["user"]})
        if entry.get("bot"):
            formatted_history.append({"role": "assistant", "content": entry["bot"]})

    return (
        formatted_history,
        selected_chat_id,
        chat_name,  # Pass the chat name for the rename input
        last_updated_time,
    )


async def _handle_new_chat(
    username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[gr.Dropdown, gr.State, gr.State, gr.State, gr.Textbox, gr.State]:
    """Handles creating a new chat session."""
    logger.info(f"Creating new chat for user: {username}")
    if not username:
        logger.warning("Attempted to create new chat without a username.")
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )  # Return unchanged if no username

    current_time_str = datetime.now().strftime("%Y%m%d%H%M%S")
    new_chat_id = f"chat_{current_time_str}"
    new_chat_name = f"New Chat {len(all_chats_data.get(username, {})) + 1}"

    if username not in all_chats_data:
        all_chats_data[username] = {}

    all_chats_data[username][new_chat_id] = {
        "chat_name": new_chat_name,
        "history": [],
        "creation_time": datetime.now().isoformat(),
        "last_updated_time": datetime.now().isoformat(),
    }

    # Update chat selector choices
    chat_choices = [(v["chat_name"], k) for k, v in all_chats_data[username].items()]
    chat_selector_update = gr.update(
        choices=chat_choices, value=new_chat_id, interactive=True
    )

    return (
        chat_selector_update,
        all_chats_data,  # Return updated all_chats_data_state
        new_chat_id,  # Set current chat_id_state
        [],  # Clear chat_history_state (Gradio messages format)
        new_chat_name,  # Set the rename input to the new chat's name
        datetime.now().isoformat(),  # Return current time for last_updated_time_state
    )


async def _handle_send_message(
    user_message: str,
    chat_history: List[Dict[str, str]],  # Now expects Gradio messages format
    username: str,
    chat_id: str,
    all_chats_data: Dict[str, Dict[str, Any]],
) -> Tuple[
    gr.Chatbot, gr.Textbox, gr.State, gr.State, gr.State
]:  # Added last_updated_time_state output
    """Handles sending a message to the chatbot and updating history."""

    def to_gradio_pairs(history):
        # Convert a list of dicts (with 'role' and 'content') to list of [user, bot] pairs
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

    if not user_message:
        yield (
            to_gradio_pairs(chat_history),
            "",
            all_chats_data,
            to_gradio_pairs(chat_history),
            gr.update(),
        )  # Return unchanged if empty message

    if not username or not chat_id:
        logger.warning("Attempted to send message without valid username or chat ID.")
        yield (
            to_gradio_pairs(chat_history),
            "",
            all_chats_data,
            to_gradio_pairs(chat_history),
            gr.update(),
        )  # Return unchanged

    # Update the internal all_chats_data structure
    if username not in all_chats_data:
        all_chats_data[username] = {}
    if chat_id not in all_chats_data[username]:
        all_chats_data[username][chat_id] = {
            "chat_name": f"Chat {chat_id}",
            "history": [],  # Backend stores pairs
            "creation_time": datetime.now().isoformat(),
            "last_updated_time": datetime.now().isoformat(),
        }

    # Add user message to history for display (Gradio format)
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append(
        {"role": "assistant", "content": ""}
    )  # Placeholder for bot response

    # Append the user message to the stored history with an empty bot response placeholder
    all_chats_data[username][chat_id]["history"].append(
        {"user": user_message, "bot": ""}
    )
    current_time = datetime.now().isoformat()
    all_chats_data[username][chat_id]["last_updated_time"] = current_time

    logger.info(f"Sending message for user {username}, chat {chat_id}: {user_message}")

    try:
        # Get response from backend chatbot
        response_generator = get_chatbot_response(username, chat_id, user_message)
        full_response = ""
        async for chunk in response_generator:
            full_response += chunk
            # Update the content of the assistant message in the last entry
            chat_history[-1]["content"] = full_response
            yield (
                to_gradio_pairs(chat_history),
                gr.update(value=""),
                all_chats_data,
                to_gradio_pairs(chat_history),
                current_time,
            )  # Yield streamed response

        # After streaming completes, update the stored history with the full bot response
        all_chats_data[username][chat_id]["history"][-1]["bot"] = full_response
        current_time = datetime.now().isoformat()
        all_chats_data[username][chat_id]["last_updated_time"] = current_time

        logger.info(
            f"Received full response for user {username}, chat {chat_id}: {full_response[:50]}..."
        )
        # Final yield after all chunks are received and stored
        yield (
            to_gradio_pairs(chat_history),
            gr.update(value=""),
            all_chats_data,
            to_gradio_pairs(chat_history),
            current_time,
        )

    except Exception as e:
        logger.error(
            f"Error getting chatbot response for {username}, chat {chat_id}: {e}",
            exc_info=True,
        )
        error_message = f"Error: Could not get response ({e}). Please try again."
        chat_history[-1]["content"] = error_message  # Show error in chatbot
        yield (
            to_gradio_pairs(chat_history),
            gr.update(value=""),
            all_chats_data,
            to_gradio_pairs(chat_history),
            gr.update(),
        )


async def _handle_clear_chat(
    username: str,
    chat_id: str,
    all_chats_data: Dict[str, Dict[str, Any]],
) -> Tuple[
    gr.Chatbot, gr.State, gr.State, gr.Textbox, gr.State
]:  # Added last_updated_time_state output
    """Clears the current chat history for the specified chat ID."""
    logger.info(f"Clearing chat for user: {username}, chat_id: {chat_id}")
    if (
        not username
        or not chat_id
        or username not in all_chats_data
        or chat_id not in all_chats_data[username]
    ):
        logger.warning("Attempted to clear chat with invalid username or chat ID.")
        return (
            gr.update(value=[]),
            all_chats_data,
            None,
            gr.update(),
            gr.update(),
        )  # Return unchanged

    # Clear the history in the stored data
    all_chats_data[username][chat_id]["history"] = []
    current_time = datetime.now().isoformat()
    all_chats_data[username][chat_id]["last_updated_time"] = current_time

    # Clear the displayed chatbot history and reset chat_id_state
    return (
        gr.update(value=[]),  # Clear chatbot display
        all_chats_data,  # Return updated all_chats_data_state
        chat_id,  # Keep current chat ID, only clear history
        gr.update(
            value=all_chats_data[username][chat_id]["chat_name"]
        ),  # Reset rename input
        current_time,  # Return current time for last_updated_time_state
    )


async def _handle_rename_chat_session(
    username: str,
    chat_id: str,
    new_chat_name: str,
    all_chats_data: Dict[str, Dict[str, Any]],
) -> Tuple[gr.Dropdown, gr.State, gr.State]:
    """
    Renames the current chat session, updating both the in-memory cache and the database.
    """
    if not username or not chat_id or not new_chat_name:
        logger.warning("Attempted to rename chat with invalid inputs.")
        return gr.update(), gr.State(all_chats_data), gr.update()  # Return unchanged

    current_time = datetime.now().isoformat()

    # 1. Update the in-memory cache
    if username in all_chats_data and chat_id in all_chats_data[username]:
        all_chats_data[username][chat_id]["chat_name"] = new_chat_name
        # Use 'updated_at' key for consistency with database schema
        all_chats_data[username][chat_id]["updated_at"] = current_time
        logger.info(
            f"In-memory cache updated: Chat {chat_id} renamed to '{new_chat_name}' for user {username}"
        )
    else:
        logger.warning(
            f"Chat {chat_id} not found in in-memory cache for user {username}."
        )
        # Continue to update DB, as cache might be out of sync.

    # 2. Update the database
    try:
        db_update_result = await rename_chat_session(username, chat_id, new_chat_name)
        if not db_update_result.get("success"):
            logger.error(
                f"Failed to rename chat in database for {chat_id} by {username}: "
                f"{db_update_result.get('message', 'Unknown error')}"
            )
            # Potentially, you might want to revert the in-memory change here
            # or add a UI notification if the database update fails.
            # For simplicity, we log and proceed.
        else:
            logger.info(
                f"Database updated: Chat {chat_id} renamed to '{new_chat_name}' in DB."
            )
    except Exception as e:
        logger.error(f"Exception during database chat rename for {chat_id}: {e}")
        # Handle unexpected errors during DB call

    # Rebuild chat choices for the dropdown
    chat_choices = [
        (v["chat_name"], k) for k, v in all_chats_data.get(username, {}).items()
    ]
    # Sort by 'updated_at' to ensure the most recently updated chat appears first in the dropdown
    chat_choices.sort(
        key=lambda x: all_chats_data[username][x[1]].get("updated_at", ""), reverse=True
    )

    # Return updated Gradio components
    return (
        gr.update(choices=chat_choices, value=chat_id),
        gr.State(all_chats_data),
        gr.State(current_time),
    )


def initial_chat_setup(
    username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[
    gr.Dropdown,  # 1 chat_selector
    gr.Textbox,  # 2 msg
    gr.Button,  # 3 send_btn
    gr.Button,  # 4 new_chat_btn_from_interface
    gr.Button,  # 5 clear_chat_btn
    gr.Textbox,  # 6 rename_input (gr.update with value and interactive)
    gr.Button,  # 7 rename_btn
    Dict[str, Dict[str, Any]],  # 8 all_chats_data_state
    List[Dict[str, str]],  # 9 chat_history_state (now List[Dict])
    str,  # 10 chat_id_state
    str,  # 11 last_updated_time_state (new)
]:
    logger.info(f"Initial chat setup triggered for user: '{username}'")
    if not username:
        logger.info("No username provided. Skipping initial chat setup.")
        # Return default disabled/empty states for all outputs
        return (
            gr.update(choices=[], value=None, interactive=False),  # 1 chat_selector
            gr.update(value="", interactive=False),  # 2 msg
            gr.update(interactive=False),  # 3 send_btn
            gr.update(interactive=False),  # 4 new_chat_btn_from_interface
            gr.update(interactive=False),  # 5 clear_chat_btn
            gr.update(value="", interactive=False),  # 6 rename_input
            gr.update(interactive=False),  # 7 rename_btn
            {},  # 8 all_chats_data_state
            [],  # 9 chat_history_state
            None,  # 10 chat_id_state
            "",  # 11 last_updated_time_state
        )

    # Initialize or load user's chat data
    if username not in all_chats_data or not all_chats_data[username]:
        # If no chats exist for the user, create a default first chat
        logger.info(f"No existing chats for {username}. Creating initial chat.")
        current_time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        initial_chat_id = f"chat_{current_time_str}"
        initial_chat_name = "My First Chat"
        all_chats_data[username] = {
            initial_chat_id: {
                "chat_name": initial_chat_name,
                "history": [],
                "creation_time": datetime.now().isoformat(),
                "last_updated_time": datetime.now().isoformat(),
            }
        }
        current_chat_id = initial_chat_id
        current_chat_history_formatted = []  # Gradio messages format
        current_rename_value = initial_chat_name
        current_last_updated_time = datetime.now().isoformat()
    else:
        # Load the most recent chat if available, or the first one if sorting isn't implemented
        # For now, just pick the most recently updated chat
        sorted_chats = sorted(
            all_chats_data[username].items(),
            key=lambda item: item[1].get("last_updated_time", ""),
            reverse=True,
        )
        current_chat_id = sorted_chats[0][0] if sorted_chats else None

        current_chat_history_formatted = []
        current_last_updated_time = "N/A"
        if current_chat_id:
            chat_data = all_chats_data[username][current_chat_id]
            history = chat_data[
                "history"
            ]  # This is the stored [{"user": "", "bot": ""}, ...]
            for entry in history:
                if entry.get("user"):
                    current_chat_history_formatted.append(
                        {"role": "user", "content": entry["user"]}
                    )
                if entry.get("bot"):
                    current_chat_history_formatted.append(
                        {"role": "assistant", "content": entry["bot"]}
                    )
            current_rename_value = chat_data.get("chat_name", "")
            current_last_updated_time = chat_data.get("last_updated_time", "N/A")
        else:
            current_rename_value = ""

        logger.info(
            f"Loaded existing chats for {username}. Current chat: {current_chat_id}"
        )

    # Prepare chat selector choices
    chat_choices = [(v["chat_name"], k) for k, v in all_chats_data[username].items()]

    return (
        gr.update(
            choices=chat_choices, value=current_chat_id, interactive=True
        ),  # 1 chat_selector
        gr.update(value="", interactive=True),  # 2 msg
        gr.update(interactive=True),  # 3 send_btn
        gr.update(interactive=True),  # 4 new_chat_btn_from_interface
        gr.update(interactive=True),  # 5 clear_chat_btn
        gr.update(
            value=current_rename_value, interactive=True
        ),  # 6 rename_input (value and interactivity)
        gr.update(interactive=True),  # 7 rename_btn
        all_chats_data,  # 8 all_chats_data_state
        current_chat_history_formatted,  # 9 chat_history_state
        current_chat_id,  # 10 chat_id_state
        current_last_updated_time,  # 11 last_updated_time_state
    )
