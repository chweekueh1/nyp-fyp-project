#!/usr/bin/env python3

"""
Chatbot Interface Module

This module provides the main chatbot interface for the NYP FYP Chatbot application.
Users can send messages, manage chat sessions, search history, and rename chats.
"""

from typing import Tuple, Dict, Any, List
import gradio as gr
import logging
from datetime import datetime  # Import datetime for handling timestamps


logger = logging.getLogger(__name__)


# Import clear_chat_history from infra_utils
from infra_utils import clear_chat_history

# Import specific backend functions
from backend.chat import (
    _get_chat_metadata_cache_internal,  # Use the internal cache getter
    list_user_chat_ids,  # Corrected: Import list_user_chat_ids instead of load_all_chats
    get_chatbot_response,  # Corrected: Import get_chatbot_response
    rename_chat,  # Assuming this is the function to rename chats
    search_chat_history,  # Assuming this is the function to search chat history
)


# --- Helper functions for chatbot_ui (these handle overall chat session management) ---


def _load_chat_by_id(
    selected_chat_id: str, username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[List[List[str]], str, str, str]:
    """
    Loads chat history for a selected chat ID from the `all_chats_data_state`.
    This function now only returns data/values, not interactive updates,
    as interactivity is managed by app.py's _enable_chat_inputs_on_login.

    :param selected_chat_id: The ID of the chat to load.
    :type selected_chat_id: str
    :param username: The current username.
    :type username: str
    :param all_chats_data: Dictionary of all chat metadata and histories.
    :type all_chats_data: Dict[str, Dict[str, Any]]
    :return: A tuple containing the chat history, chat ID, rename input value, and debug message.
    :rtype: Tuple[List[List[str]], str, str, str]
    """
    if not selected_chat_id:
        return (
            [],
            "",
            "",  # rename_input value
            "Please select a chat.",  # debug_md
        )

    # Retrieve chat history from the in-memory state
    chat_info = all_chats_data.get(selected_chat_id, {})
    history = chat_info.get("history", [])
    chat_name = chat_info.get("name", "New Chat")

    # Return values. Interactivity is handled by app.py.
    return (
        history,
        selected_chat_id,
        chat_name,  # Set rename input value
        f"Chat '{chat_name}' loaded.",  # debug_md
    )


def _clear_current_chat(
    chat_id: str,
    username: str,
) -> Tuple[List[List[str]], str, str, Dict[str, Any], str]:
    """
    Clears the history of the currently selected chat.
    Does not delete the chat, just its messages.
    This function now only returns data/values, not interactive updates,
    as interactivity is managed by app.py's _enable_chat_inputs_on_login.

    :param chat_id: The ID of the chat to clear.
    :type chat_id: str
    :param username: The current username.
    :type username: str
    :return: A tuple containing cleared chat history, current chat ID, status message,
             updated all_chats_data, and debug message.
    :rtype: Tuple[List[List[str]], str, str, Dict[str, Any], str]
    """
    if not chat_id or chat_id == "new_chat_id":
        return (
            [],
            "new_chat_id",
            "No chat selected or new chat. Nothing to clear.",
            {},  # all_chats_data
            "",  # debug_info_state
        )
    try:
        success, all_chats = clear_chat_history(chat_id, username)
        if success:
            # Update the in-memory cache directly since clear_chat_history now returns all_chats
            # Note: _get_chat_metadata_cache_internal() is used here to get the dict reference.
            # The clear_chat_history function should ideally handle the persistence.
            # Assuming `clear_chat_history` updates the persistent storage and returns the new state.
            _get_chat_metadata_cache_internal()[username] = all_chats
            return (
                [],  # Clear chatbot display
                chat_id,  # Keep the same chat_id
                "Chat history cleared successfully.",
                all_chats,  # Pass the updated all_chats_data
                "",  # Clear debug md
            )
        else:
            return (
                [],
                chat_id,
                "Failed to clear chat history.",
                all_chats,
                "",
            )
    except Exception as e:
        logger.error(f"Error clearing chat history for {chat_id}: {e}")
        return (
            [],
            chat_id,
            f"An error occurred: {e}",
            {},
            "",
        )


def _create_new_chat_ui_handler(
    username: str,
    all_chats_data: Dict[str, Dict[str, Any]],
) -> Tuple[str, List[List[str]], str, Dict[str, Any], gr.update]:
    """
    Handles the UI logic for creating a new chat.
    Sets the chat_id_state to a temporary "new_chat_id" and clears the chatbot.
    The actual chat creation (with a real ID) happens when the first message is sent.
    This function now only returns data/values, not interactive updates for individual components,
    as interactivity is managed by app.py's _enable_chat_inputs_on_login.

    :param username: The current username.
    :type username: str
    :param all_chats_data: Dictionary of all chat metadata and histories.
    :type all_chats_data: Dict[str, Dict[str, Any]]
    :return: A tuple containing the temporary chat ID, cleared chat history,
             temporary rename input value, all_chats_data (unchanged here),
             and an update for the chat selector.
    :rtype: Tuple[str, List[List[str]], str, Dict[str, Any], gr.update]
    """
    new_chat_id_temp = "new_chat_id"

    # Create a copy of all_chats_data to modify for the dropdown update
    temp_all_chats_data = all_chats_data.copy()
    # Add a temporary "New Chat" entry for immediate display in the dropdown
    temp_all_chats_data[new_chat_id_temp] = {
        "name": "New Chat",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    updated_choices = sorted(
        [(v["name"], k) for k, v in temp_all_chats_data.items()],
        key=lambda item: temp_all_chats_data[item[1]].get(
            "updated_at", datetime.min.isoformat()
        ),
        reverse=True,
    )

    # Return updates for all relevant components
    return (
        new_chat_id_temp,  # chat_id_state
        [],  # chatbot (clear history)
        "New Chat",  # rename_input (set placeholder name)
        all_chats_data,  # all_chats_data_state (no change here, actual creation is on first message)
        gr.update(
            choices=updated_choices, value=new_chat_id_temp
        ),  # chat_selector (update choices and select temp new chat)
    )


# --- Main Chatbot UI Function ---


def chatbot_ui(
    username_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
    all_chats_data_state: gr.State,
    debug_info_state: gr.State,
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
    gr.Markdown,  # debug_md
    gr.Button,  # clear_chat_btn
    gr.Markdown,  # clear_chat_status
    gr.Button,  # new_chat_btn
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
    :param debug_info_state: Gradio state for displaying debug information.
    :type debug_info_state: gr.State
    :return: A tuple of Gradio components for the chatbot interface.
    :rtype: Tuple[gr.Dropdown, gr.Chatbot, gr.Textbox, gr.Button, gr.Textbox, gr.Button, gr.Markdown, gr.Textbox, gr.Button, gr.Markdown, gr.Markdown, gr.Button, gr.Markdown, gr.Button]
    """

    with gr.Column(elem_classes=["overall-chatbot-container"]):
        # Debugging Markdown (hidden by default, can be shown for troubleshooting)
        # This debug_md component will be updated by its value, not interactive status
        debug_md = gr.Markdown(visible=False, value="Debug Info:")

        # Define all components directly within chatbot_ui
        with gr.Row(elem_classes=["chat-selection-row"]):
            chat_selector = gr.Dropdown(
                label="Select Chat",
                choices=[],  # Will be populated dynamically
                interactive=False,
                scale=2,
                elem_classes=["chat-selector"],
            )
            new_chat_btn_from_interface = gr.Button(
                "✨ New Chat", interactive=False, scale=0
            )

        with gr.Column(elem_classes=["chat-display-area"]):
            chatbot = gr.Chatbot(
                height=500,
                show_copy_button=True,
                avatar_images=(
                    "https://www.gravatar.com/avatar/?d=mp",  # User avatar
                    "https://i.imgur.com/g0W45C8.png",  # Bot avatar
                ),
                elem_classes=["chatbot-display"],
            )
            msg = gr.Textbox(
                show_label=False,
                placeholder="Enter your message and press Enter or click Send",
                container=False,
                elem_classes=["message-input"],
            )
            send_btn = gr.Button("Send", elem_classes=["send-button"])

        with gr.Row(elem_classes=["chat-management-row"]):
            rename_input = gr.Textbox(
                label="Chat Name",
                placeholder="Rename current chat",
                scale=1,
                elem_classes=["rename-input"],
            )
            rename_btn = gr.Button(
                "Rename Chat", scale=0, elem_classes=["rename-button"]
            )
            rename_status_md = gr.Markdown("")

        with gr.Row(elem_classes=["chat-search-row"]):
            search_box = gr.Textbox(
                label="Search Chat History",
                placeholder="Enter keywords to search chat history",
                scale=1,
                elem_classes=["search-box"],
            )
            search_btn_from_interface = gr.Button(
                "Search", scale=0, elem_classes=["search-button"]
            )
        search_results_md = gr.Markdown("", elem_classes=["search-results-display"])

        with gr.Row(elem_classes=["chat-management-buttons"]):
            # Use the new_chat_btn returned from chat_interface_ui
            new_chat_btn = new_chat_btn_from_interface
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
            fn=list_user_chat_ids,  # Corrected: Call list_user_chat_ids
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
                debug_md,  # Update debug_md with load status (string value)
            ],
            show_progress=False,
        )

        # New Chat Button logic
        # This now calls the _create_new_chat_ui_handler directly
        new_chat_btn.click(
            fn=_create_new_chat_ui_handler,
            inputs=[
                username_state,
                all_chats_data_state,
            ],
            outputs=[
                chat_id_state,
                chatbot,
                rename_input,
                all_chats_data_state,
                chat_selector,  # chat_selector is updated here
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
                debug_md,  # Update debug_md with load status (string value)
            ],
            show_progress=False,
        )

        # Send message logic
        msg.submit(
            fn=get_chatbot_response,  # Corrected: Call get_chatbot_response
            inputs=[
                msg,
                chat_history_state,
                username_state,
                chat_id_state,
            ],  # Reordered inputs to match get_chatbot_response signature
            outputs=[
                msg,
                chatbot,
                chat_id_state,
                all_chats_data_state,
                debug_info_state,
            ],
            show_progress=True,
        )
        send_btn.click(
            fn=get_chatbot_response,  # Corrected: Call get_chatbot_response
            inputs=[
                msg,
                chat_history_state,
                username_state,
                chat_id_state,
            ],  # Reordered inputs to match get_chatbot_response signature
            outputs=[
                msg,
                chatbot,
                chat_id_state,
                all_chats_data_state,
                debug_info_state,
            ],
            show_progress=True,
        )

        # Rename chat logic
        rename_btn.click(
            fn=rename_chat,
            inputs=[chat_id_state, rename_input, username_state, all_chats_data_state],
            outputs=[rename_status_md, all_chats_data_state],
        ).then(  # Update chat selector after renaming
            fn=lambda all_data, current_id: gr.update(
                choices=[(v["name"], k) for k, v in all_data.items()],
                value=current_id,
            ),
            inputs=[all_chats_data_state, chat_id_state],
            outputs=[chat_selector],
        )

        # Search chat history logic
        search_btn_from_interface.click(
            fn=search_chat_history,
            inputs=[search_box, username_state],
            outputs=[search_results_md],
        )

        # Clear chat logic
        clear_chat_btn.click(
            fn=_clear_current_chat,
            inputs=[chat_id_state, username_state],
            # Outputs: chatbot (cleared), chat_id_state (kept), clear_chat_status, all_chats_data (updated), debug_md
            outputs=[
                chatbot,
                chat_id_state,
                clear_chat_status,
                all_chats_data_state,
                debug_info_state,  # This is debug_md from chatbot_ui scope (string value)
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
        rename_input,
        rename_btn,
        rename_status_md,
        search_box,  # This comes from chat_interface_ui
        search_btn_from_interface,  # This comes from chat_interface_ui, renamed to avoid clash
        search_results_md,  # This comes from chat_interface_ui
        debug_md,  # This is defined here (renamed to debug_info_state inside chatbot_ui)
        clear_chat_btn,  # This is defined here
        clear_chat_status,  # This is defined here
        new_chat_btn,  # This is defined here
    )
