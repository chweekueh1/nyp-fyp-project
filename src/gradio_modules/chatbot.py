# chat_interface.py
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

from typing import Tuple, Dict, Any, List  # noqa: F401
import gradio as gr
import logging
from datetime import datetime  # noqa: F401

logger = logging.getLogger(__name__)


# Import clear_chat_history from infra_utils
from infra_utils import clear_chat_history

# Import specific backend functions
from backend.chat import (
    _get_chat_metadata_cache_internal,  # Use the internal cache getter
)

# Import the search_interface function

# --- Helper functions for chatbot_ui (these handle overall chat session management) ---


def _load_chat_by_id(
    selected_chat_id: str, username: str, all_chats_data: Dict[str, Dict[str, Any]]
) -> Tuple[List[List[str]], str, str, str]:
    # Loads chat history for a selected chat ID from the `all_chats_data_state`.
    #
    # This function now only returns data/values, not interactive updates,
    # as interactivity is managed by app.py's _enable_chat_inputs_on_login.
    #
    # :param selected_chat_id: The ID of the chat to load.
    # :type selected_chat_id: str
    # :param username: The current username.
    # :type username: str
    # :param all_chats_data: Dictionary of all chat metadata and histories.
    # :type all_chats_data: Dict[str, Dict[str, Any]]
    # :return: A tuple containing the chat history, chat ID, rename input value, and debug message.
    # :rtype: Tuple[List[List[str]], str, str, str]
    if not selected_chat_id:
        return (
            [],
            "",
            "",  # rename_input value
            "Please select a chat.",  # debug_md
        )

    # Retrieve chat history from the in-memory state
    chat_info = all_chats_data.get(selected_chat_id, {})
    # Ensure history is a list of [user, bot] pairs as per backend format
    history = chat_info.get("history", [])
    # Defensive: If history is not a list of lists, convert it
    if history and (not isinstance(history[0], list) or len(history[0]) != 2):
        # Try to convert dicts to lists if needed
        history = [[msg.get("user", ""), msg.get("bot", "")] for msg in history]
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
    # Clears the history of the currently selected chat.
    #
    # Does not delete the chat, just its messages.
    # This function now only returns data/values, not interactive updates,
    # as interactivity is managed by app.py's _enable_chat_inputs_on_login.
    #
    # :param chat_id: The ID of the chat to clear.
    # :type chat_id: str
    # :param username: The current username.
    # :type username: str
    # :return: A tuple containing cleared chat history, current chat ID, status message,
    #          updated all_chats_data, and debug message.
    # :rtype: Tuple[List[List[str]], str, str, Dict[str, Any], str]
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

    Args:
        username: The current username.
        all_chats_data: Dictionary of all chat metadata and histories.

    Returns:
        A tuple containing the temporary chat ID, cleared chat history,
        temporary rename input value, all_chats_data (unchanged here),
        and an update for the chat selector.
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


import os


def chatbot_ui(
    username_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
    all_chats_data_state: gr.State,
    debug_info_state: gr.State,
) -> Tuple[
    gr.State,
    gr.Chatbot,
    gr.Textbox,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Column,  # This will be the search_container
    gr.Markdown,  # search_stats_md
    gr.Markdown,  # debug_md
    gr.Button,  # clear_chat_btn
    gr.Markdown,  # clear_chat_status
    gr.Button,  # new_chat_btn
]:
    """
    Constructs the chatbot UI, integrating chat history, message input,
    send functionality, chat selection, renaming, and clearing.
    """
    with gr.Column(elem_classes=["overall-chatbot-container"]):
        debug_md = gr.Markdown(visible=False, value="Debug Info:")
        with gr.Row(elem_classes=["chat-selection-row"]):
            chat_selector = gr.Dropdown(
                label="Select Chat",
                choices=[],
                interactive=False,
                scale=2,
                elem_classes=["chat-selector"],
            )
            new_chat_btn_from_interface = gr.Button(
                "✨ New Chat", interactive=False, scale=0
            )
        with gr.Column(elem_classes=["chat-display-area"]):
            chatbot = gr.Chatbot(
                show_copy_button=True,
                avatar_images=(
                    "https://www.gravatar.com/avatar/?d=mp",
                    "https://i.imgur.com/g0W45C8.png",
                ),
                elem_classes=["chatbot-display"],
                render_markdown=True,
                type="messages",
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
        from gradio_modules.search_interface import search_interface

        (
            search_container,
            search_query,
            search_btn_from_interface,
            search_results_md,
            search_stats_md,
        ) = search_interface(
            username_state,
            chat_id_state,
            chat_history_state,
            all_chats_data_state,
            debug_info_state,
        )
        with gr.Row(elem_classes=["chat-management-buttons"]):
            new_chat_btn = new_chat_btn_from_interface
            clear_chat_btn = gr.Button(
                "🗑️ Clear Current Chat History", interactive=False
            )
            clear_chat_status = gr.Markdown("")

    # Patch: In benchmark mode, skip all event setup and just return components
    if os.environ.get("BENCHMARK_MODE"):
        return (
            chat_selector,
            chatbot,
            msg,
            send_btn,
            rename_input,
            rename_btn,
            rename_status_md,
            search_container,
            search_stats_md,
            debug_md,
            clear_chat_btn,
            clear_chat_status,
            new_chat_btn,
        )

    # --- Enable interactivity for chat UI components after login ---
    chat_selector.interactive = True
    msg.interactive = True
    send_btn.interactive = True
    new_chat_btn_from_interface.interactive = True
    clear_chat_btn.interactive = True

    # --- Event Handlers ---

    # 1. Load chat when chat_selector changes
    def on_chat_selector_change(selected_chat_id, username, all_chats_data):
        return _load_chat_by_id(selected_chat_id, username, all_chats_data)

    chat_selector.change(
        fn=on_chat_selector_change,
        inputs=[chat_selector, username_state, all_chats_data_state],
        outputs=[chat_history_state, chat_id_state, rename_input, debug_md],
    )

    # 2. Send message (on send_btn click or msg.submit)
    async def on_send_message(message, history, username, chat_id, all_chats_data):
        from backend.chat import get_chatbot_response

        # Defensive: If chat_id is empty, create a new chat
        if not chat_id or chat_id == "new_chat_id":
            chat_id = "new_chat_id"
        # Await backend response
        result = await get_chatbot_response(message, history, username, chat_id)
        # result: (empty_message, updated_history, current_chat_id, all_user_chats_data, debug_info)
        (
            empty_message,
            updated_history,
            current_chat_id,
            all_user_chats_data,
            debug_info,
        ) = result
        return (
            updated_history,
            current_chat_id,
            all_user_chats_data,
            "",  # Clear message input
            debug_info,
        )

    send_btn.click(
        fn=on_send_message,
        inputs=[
            msg,
            chat_history_state,
            username_state,
            chat_id_state,
            all_chats_data_state,
        ],
        outputs=[
            chat_history_state,
            chat_id_state,
            all_chats_data_state,
            msg,
            debug_md,
        ],
        api_name="send_message",
    )
    msg.submit(
        fn=on_send_message,
        inputs=[
            msg,
            chat_history_state,
            username_state,
            chat_id_state,
            all_chats_data_state,
        ],
        outputs=[
            chat_history_state,
            chat_id_state,
            all_chats_data_state,
            msg,
            debug_md,
        ],
        api_name="send_message_submit",
    )

    # 3. New chat button
    def on_new_chat(username, all_chats_data):
        return _create_new_chat_ui_handler(username, all_chats_data)

    new_chat_btn_from_interface.click(
        fn=on_new_chat,
        inputs=[username_state, all_chats_data_state],
        outputs=[
            chat_id_state,
            chat_history_state,
            rename_input,
            all_chats_data_state,
            chat_selector,
        ],
    )

    # 4. Clear chat button
    def on_clear_chat(chat_id, username):
        return _clear_current_chat(chat_id, username)

    clear_chat_btn.click(
        fn=on_clear_chat,
        inputs=[chat_id_state, username_state],
        outputs=[
            chat_history_state,
            chat_id_state,
            clear_chat_status,
            all_chats_data_state,
            debug_md,
        ],
    )

    # 5. Rename chat button
    def on_rename_chat(chat_id, new_name, username, all_chats_data):
        from backend.chat import rename_chat

        status, updated_chats = rename_chat(chat_id, new_name, username, all_chats_data)
        return status, updated_chats

    rename_btn.click(
        fn=on_rename_chat,
        inputs=[chat_id_state, rename_input, username_state, all_chats_data_state],
        outputs=[rename_status_md, all_chats_data_state],
    )

    return (
        chat_selector,
        chatbot,
        msg,
        send_btn,
        rename_input,
        rename_btn,
        rename_status_md,
        search_container,
        search_stats_md,
        debug_md,
        clear_chat_btn,
        clear_chat_status,
        new_chat_btn,
    )
