#!/usr/bin/env python3

"""
Chatbot Interface Module

This module provides the main chatbot interface for the NYP FYP Chatbot application.
Users can send messages, manage chat sessions, search history, and rename chats.
"""

from typing import Tuple, Dict, Any, List
import gradio as gr
import logging

logger = logging.getLogger(__name__)


# Import clear_chat_history from infra_utils
from infra_utils import clear_chat_history

# Import specific backend functions
from backend.chat import (
    _get_chat_metadata_cache,  # Needed for direct cache manipulation in _clear_current_chat
)

# Import the core chat interface UI and its helper for loading all chats
from .chat_interface import chat_interface_ui, load_all_chats


# --- Helper functions for chatbot_ui (these handle overall chat session management) ---


def _load_chat_by_id(
    selected_chat_id: str, username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[List[List[str]], str, Dict[str, Any], Any, Any, Any]:
    """
    Loads chat history for a selected chat ID from the `all_chats_data_state`.

    :param selected_chat_id: The ID of the chat to load.
    :type selected_chat_id: str
    :param username: The current username.
    :type username: str
    :param all_chats_data: Dictionary of all chat metadata and histories.
    :type all_chats_data: Dict[str, Dict[str, Any]]
    :return: A tuple containing the chat history, chat ID, and all chats data.
    :rtype: Tuple[List[List[str]], str, Dict[str, Any], Any, Any, Any]
    """
    if not selected_chat_id:
        return (
            [],
            "",
            all_chats_data,
            gr.update(interactive=False),
            gr.update(interactive=False),
            "Please select a chat.",
        )

    # Retrieve chat history from the in-memory state
    chat_info = all_chats_data.get(selected_chat_id, {})
    history = chat_info.get("history", [])
    chat_name = chat_info.get("name", "New Chat")

    # The components need to be enabled/disabled based on whether a chat is selected
    return (
        history,
        selected_chat_id,
        gr.update(
            value=chat_name, interactive=True
        ),  # Set rename input value and enable
        gr.update(interactive=True),  # Enable message input
        gr.update(interactive=True),  # Enable send button
        f"Chat '{chat_name}' loaded.",
    )


def _clear_current_chat(
    chat_id: str,
    username: str,
) -> Tuple[
    List[List[str]], str, str, gr.Textbox, gr.Button, Dict[str, Any], gr.Markdown
]:
    """
    Clears the history of the currently selected chat.
    Does not delete the chat, just its messages.
    """
    if not chat_id or chat_id == "new_chat_id":
        return (
            [],
            "new_chat_id",
            "No chat selected or new chat. Nothing to clear.",
            gr.update(interactive=True),
            gr.update(interactive=True),
            {},
            gr.update(value=""),
        )
    try:
        success, all_chats = clear_chat_history(chat_id, username)
        if success:
            # Update the in-memory cache directly since clear_chat_history now returns all_chats
            _get_chat_metadata_cache()[username] = all_chats
            return (
                [],  # Clear chatbot display
                chat_id,  # Keep the same chat_id
                "Chat history cleared successfully.",
                gr.update(interactive=True),  # Enable message input
                gr.update(interactive=True),  # Enable send button
                all_chats,  # Pass the updated all_chats_data
                gr.update(value=""),  # Clear debug md
            )
        else:
            return (
                [],
                chat_id,
                "Failed to clear chat history.",
                gr.update(interactive=True),
                gr.update(interactive=True),
                all_chats,
                gr.update(value=""),
            )
    except Exception as e:
        logger.error(f"Error clearing chat history for {chat_id}: {e}")
        return (
            [],
            chat_id,
            f"An error occurred: {e}",
            gr.update(interactive=True),
            gr.update(interactive=True),
            {},
            gr.update(value=""),
        )


def _create_new_chat_ui_handler(
    username: str,
    all_chats_data: Dict[str, Dict[str, Any]],
    chat_selector_component: gr.Dropdown,
) -> Tuple[
    str, List[List[str]], str, gr.Textbox, gr.Button, Dict[str, Any], gr.Dropdown
]:
    """
    Handles the UI logic for creating a new chat.
    Sets the chat_id_state to a temporary "new_chat_id" and clears the chatbot.
    The actual chat creation (with a real ID) happens when the first message is sent.
    """
    # This handler needs to make sure the chat_id_state is set to a special value
    # that _handle_chat_message can interpret as a signal to create a new chat in the backend.
    # It also needs to clear the displayed chat history.

    # Remove unused variables updated_chat_id, updated_chat_history, chat_name
    current_all_chats_data = all_chats_data  # Use the passed in data

    # Temporarily set the chat_id_state to a special value indicating a new chat
    # The actual ID will be generated by the backend when the first message is sent
    new_chat_id_temp = "new_chat_id"

    # Update the chat selector to show a "New Chat" option, but don't select it yet
    # We will select it via client-side JS or another .then() call
    updated_choices = [(v["name"], k) for k, v in current_all_chats_data.items()]
    # Add a "New Chat" temporary option if not already there, and set it as selected
    if ("New Chat", new_chat_id_temp) not in updated_choices:
        updated_choices.insert(0, ("New Chat", new_chat_id_temp))

    return (
        new_chat_id_temp,  # Set chat_id_state to indicate new chat
        [],  # Clear chatbot history display
        "New Chat",  # Set the rename input to "New Chat" as a placeholder
        gr.update(interactive=True),  # Enable message input
        gr.update(interactive=True),  # Enable send button
        current_all_chats_data,  # No change to all_chats_data yet, but needs to be passed
        gr.update(
            choices=updated_choices, value=new_chat_id_temp
        ),  # Update dropdown choices and select "New Chat"
    )


# --- Main Chatbot UI Function ---


def chatbot_ui(
    username_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
    all_chats_data_state: gr.State,
) -> Tuple[
    gr.Dropdown,
    gr.Chatbot,
    gr.Textbox,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Button,
    gr.Markdown,
    gr.Button,
]:
    """
    Constructs the chatbot UI, integrating chat history, message input,
    send functionality, chat selection, renaming, and clearing.

    :param username_state: Gradio state holding the current username.
    :type username_state: gr.State
    :param chat_id_state: Gradio state holding the ID of the currently active chat.
    :type chat_id_state: gr.State
    :param chat_history_state: Gradio state holding the history of the current chat.
    :type chat_history_state: gr.State
    :param all_chats_data_state: Gradio state holding all chat metadata and histories.
    :type all_chats_data_state: gr.State
    :return: A tuple of Gradio components for the chatbot interface.
    :rtype: Tuple[gr.Dropdown, gr.Chatbot, gr.Textbox, gr.Button, gr.Textbox, gr.Button, gr.Markdown, gr.Textbox, gr.Button, gr.Markdown, gr.Button, gr.Markdown, gr.Button]
    """

    with gr.Column(elem_classes=["overall-chatbot-container"]):
        # Debugging Markdown (hidden by default, can be shown for troubleshooting)
        debug_md = gr.Markdown(visible=False, value="Debug Info:")
        debug_info_state = gr.State(value="")  # State to hold debug info

        (
            chatbot,
            msg,
            send_btn,
            rename_input,
            rename_btn,
            rename_status_md,
            search_box,
            search_btn_from_interface,
            search_results_md,
            chat_selector,  # Now returned directly from chat_interface_ui
        ) = chat_interface_ui(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )

        with gr.Row(elem_classes=["chat-management-buttons"]):
            new_chat_btn = gr.Button("➕ New Chat", interactive=False)
            clear_chat_btn = gr.Button(
                "🗑️ Clear Current Chat History", interactive=False
            )
            clear_chat_status = gr.Markdown("")

        # Link chatbot components to their backend logic
        username_state.change(
            fn=lambda: [
                gr.update(interactive=True) for _ in [new_chat_btn, clear_chat_btn]
            ],
            outputs=[new_chat_btn, clear_chat_btn],
        ).then(
            fn=load_all_chats,
            inputs=[username_state],
            outputs=[all_chats_data_state],
        ).then(
            fn=lambda all_data: gr.update(
                choices=[(v["name"], k) for k, v in all_data.items()],
                value=list(all_data.keys())[0]
                if all_data
                else "",  # Select the first chat if available
                interactive=bool(all_data),  # Enable selector if chats exist
            ),
            inputs=[all_chats_data_state],
            outputs=[chat_selector],
        ).then(
            fn=_load_chat_by_id,
            inputs=[chat_selector, username_state, all_chats_data_state],
            outputs=[
                chatbot,
                chat_id_state,
                rename_input,
                msg,
                send_btn,
                debug_md,  # Update debug_md with load status
            ],
            show_progress=False,
        )

        # New Chat Button logic
        new_chat_btn.click(
            fn=_create_new_chat_ui_handler,
            inputs=[username_state, all_chats_data_state, chat_selector],
            outputs=[
                chat_id_state,
                chatbot,
                rename_input,
                msg,
                send_btn,
                all_chats_data_state,
                chat_selector,
            ],
            show_progress=False,
        )

        # Chat selection logic
        chat_selector.change(
            fn=_load_chat_by_id,
            inputs=[chat_selector, username_state, all_chats_data_state],
            outputs=[
                chatbot,
                chat_id_state,  # Keep chat_id, only clear history
                rename_input,
                msg,  # Enable/disable msg input
                send_btn,  # Enable/disable send_btn
                debug_md,  # Was debug_info_state, update debug_md with load status
            ],
            show_progress=False,
        )

        # Clear chat logic
        clear_chat_btn.click(
            fn=_clear_current_chat,
            inputs=[chat_id_state, username_state],
            # Outputs: chatbot (cleared), chat_history_state (cleared), clear_chat_status, msg, send_btn, all_chats_data (updated), debug_md
            outputs=[
                chatbot,
                chat_id_state,  # Keep chat_id, only clear history
                clear_chat_status,
                msg,  # Enable/disable msg input
                send_btn,  # Enable/disable send_btn
                all_chats_data_state,  # Updated if chat history cleared
                debug_info_state,  # Was debug_md
            ],
        ).then(  # After clearing, ensure chat selector is updated with correct previews/timestamps
            fn=lambda all_data, current_id: gr.update(
                choices=[(v["name"], k) for k, v in all_data.items()],
                value=current_id,  # Keep the same chat selected
            ),
            inputs=[all_chats_data_state, chat_id_state],
            outputs=[chat_selector],
        )

    # Return all necessary components to the calling module (e.g., app.py)
    return (
        chat_selector,
        chatbot,
        msg,
        send_btn,
        search_box,  # This comes from chat_interface_ui
        search_btn_from_interface,  # This comes from chat_interface_ui, renamed to avoid clash
        search_results_md,  # This comes from chat_interface_ui
        rename_input,  # This comes from chat_interface_ui
        rename_btn,  # This comes from chat_interface_ui
        debug_md,  # This is defined here (renamed to debug_info_state inside chatbot_ui)
        clear_chat_btn,  # This is defined here
        clear_chat_status,  # This is defined here
        new_chat_btn,  # This is defined here
    )
