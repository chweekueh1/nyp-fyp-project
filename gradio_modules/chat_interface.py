#!/usr/bin/env python3
"""
Chat Interface Module

This module provides the core chat interface components for the NYP FYP Chatbot application.
Users can send messages, view chat history, search history, and rename chats.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, AsyncGenerator
import gradio as gr
from datetime import datetime

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions
from backend.chat import (
    ask_question,
    list_user_chat_ids,
    get_chat_history,
    rename_chat as backend_rename_chat,  # Renamed to avoid clash with local function if any
    search_chat_history as backend_search_chat_history,  # Renamed
    create_new_chat,  # Corrected to use create_new_chat
)
from infra_utils import setup_logging

# Set up logging
logger = setup_logging()

# --- Helper functions (specific to chat_interface or shared across chatbot_ui) ---


def load_all_chats(username: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all chat histories and metadata for a user.

    :param username: The username to load chats for.
    :type username: str
    :return: Dictionary mapping chat_id to a dictionary containing chat history (list of [user_msg, bot_msg] pairs) and name.
    :rtype: Dict[str, Dict[str, Any]]
    """
    if not username:
        return {}
    all_chats = list_user_chat_ids(username)
    # Sort chats by 'updated_at' timestamp, newest first
    sorted_chats = sorted(
        all_chats.items(),
        key=lambda item: datetime.fromisoformat(
            item[1].get("updated_at", datetime.min.isoformat())
        ),  # Handle missing updated_at
        reverse=True,
    )
    return {k: v for k, v in sorted_chats}


async def _handle_chat_message(
    message: str,
    chat_history: List[List[str]],
    username: str,
    chat_id: str,
    all_chats_data: Dict[str, Dict[str, Any]],
    debug_info: str,
) -> AsyncGenerator[
    Tuple[str, List[List[str]], Dict[str, Any], str, gr.Button, str, gr.Dropdown], None
]:
    """
    Handles user messages, sends them to the chatbot backend, and streams the response.
    Updates chat history and all_chats_data state.
    """
    if not message:
        yield (
            gr.update(value="", interactive=True),
            chat_history,
            all_chats_data,
            "Please enter a message.",
            gr.update(interactive=True),
            chat_id,
            gr.update(),  # No change to chat selector
        )
        return

    # Append user message to history
    chat_history.append([message, None])
    yield (
        "",
        chat_history,
        all_chats_data,
        debug_info,
        gr.update(interactive=False),
        chat_id,
        gr.update(),  # No change to chat selector
    )  # Clear input and disable send

    full_response_content = ""
    new_chat_id = chat_id  # Initialize new_chat_id with current chat_id

    # Placeholder for chat_selector_component update, will be replaced by actual component
    chat_selector_update = gr.update()

    try:
        # Determine if this is a new chat being created
        if chat_id == "new_chat_id":
            # Call create_new_chat to get a proper chat_id and initial data structure
            new_chat_details = create_new_chat(
                username
            )  # create_new_chat no longer takes message
            new_chat_id = new_chat_details["chat_id"]

            # Update the all_chats_data state with the new chat details
            all_chats_data[new_chat_id] = {
                "name": new_chat_details["name"],
                "history": [],  # History will be populated by ask_question
                "updated_at": new_chat_details["updated_at"],
            }
            chat_id = new_chat_id  # Update chat_id for the current session

            # Update chat selector choices after new chat is created
            updated_choices = [(v["name"], k) for k, v in all_chats_data.items()]
            chat_selector_update = gr.update(choices=updated_choices, value=new_chat_id)

        response_generator = ask_question(
            message, chat_id, username
        )  # Pass the (potentially new) chat_id

        # Stream response
        async for chunk_data in response_generator:
            if "response_chunk" in chunk_data:
                chunk = chunk_data["response_chunk"]
                full_response_content += chunk
                chat_history[-1][1] = (
                    full_response_content  # Update the last bot message
                )
                yield (
                    gr.update(value=""),
                    chat_history,
                    all_chats_data,
                    debug_info,
                    gr.update(interactive=False),
                    new_chat_id,
                    chat_selector_update,
                )
            if "debug_info" in chunk_data:
                debug_info = chunk_data["debug_info"]
                yield (
                    gr.update(value=""),
                    chat_history,
                    all_chats_data,
                    debug_info,
                    gr.update(interactive=False),
                    new_chat_id,
                    chat_selector_update,
                )
            if "error" in chunk_data:
                full_response_content += f"\n[Error: {chunk_data['error']}]"
                chat_history[-1][1] = full_response_content
                debug_info = f"Error during streaming: {chunk_data['error']}"
                yield (
                    gr.update(value=""),
                    chat_history,
                    all_chats_data,
                    debug_info,
                    gr.update(interactive=False),
                    new_chat_id,
                    chat_selector_update,
                )
                break  # Stop streaming on error

    except Exception as e:
        logger.error(f"Error in _handle_chat_message: {e}")
        full_response_content += f"\n[Error: An unexpected error occurred: {e}]"
        chat_history[-1][1] = full_response_content
        debug_info = f"Unexpected error in _handle_chat_message: {e}"

    finally:
        # After streaming, ensure history and metadata are fully updated for the chat
        final_history = get_chat_history(
            new_chat_id, username
        )  # Fetch the complete history
        all_chats_data[new_chat_id]["history"] = final_history
        all_chats_data[new_chat_id]["updated_at"] = (
            datetime.now().isoformat()
        )  # Update timestamp

        # Ensure the final yield includes all necessary updates, and re-enables inputs
        yield (
            gr.update(value="", interactive=True),
            final_history,
            all_chats_data,
            debug_info,
            gr.update(interactive=True),
            new_chat_id,
            chat_selector_update,  # Ensure this is always yielded
        )


async def _handle_rename_chat(
    chat_id: str, new_name: str, username: str, all_chats_data: Dict[str, Any]
) -> Tuple[str, gr.Textbox, Dict[str, Any], gr.Dropdown]:
    """
    Handles renaming a chat.
    """
    if not chat_id or chat_id == "new_chat_id" or not new_name:
        return (
            "Please select a chat and provide a new name.",
            gr.update(value=""),
            all_chats_data,
            gr.update(),
        )

    try:
        success = backend_rename_chat(
            chat_id, username, new_name
        )  # Corrected argument order
        if success:
            all_chats_data[chat_id]["name"] = new_name
            # Refresh choices for the dropdown
            updated_choices = [(v["name"], k) for k, v in all_chats_data.items()]
            return (
                f"Chat renamed to '{new_name}'.",
                gr.update(value=""),
                all_chats_data,
                gr.update(
                    choices=updated_choices, value=chat_id
                ),  # Update the dropdown with new choices and keep current chat selected
            )
        else:
            return (
                "Failed to rename chat.",
                gr.update(value=""),
                all_chats_data,
                gr.update(),
            )
    except Exception as e:
        logger.error(f"Error renaming chat {chat_id}: {e}")
        return (
            f"Error renaming chat: {e}",
            gr.update(value=""),
            all_chats_data,
            gr.update(),
        )


async def _handle_search_chat_history(
    query: str, username: str
) -> Tuple[str, gr.Textbox]:
    """
    Handles searching chat history for a given query.
    """
    if not query:
        return "Please enter a search query.", gr.update(value=query)

    try:
        results = backend_search_chat_history(
            username, query
        )  # Corrected argument order
        if not results:
            return "No results found.", gr.update(value=query)

        formatted_results = "### Search Results:\n"
        for chat_id, chat_name, match_text in results:
            formatted_results += (
                f"- **Chat**: {chat_name} (ID: `{chat_id}`)\n"
                f'  - **Match**: *"{match_text}"*\n'
            )
        return formatted_results, gr.update(value=query)
    except Exception as e:
        logger.error(f"Error searching chat history: {e}")
        return f"An error occurred during search: {e}", gr.update(value=query)


def chat_interface_ui(
    username_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
    all_chats_data_state: gr.State,
    debug_info_state: gr.State,
) -> Tuple[
    gr.Chatbot,
    gr.Textbox,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Dropdown,  # Add chat_selector_component here
    gr.Button,  # new_chat_btn
]:
    """
    Creates the main chat interface UI components, including chat display,
    message input, send button, rename functionality, and search functionality.

    :param username_state: Gradio state for the current username.
    :type username_state: gr.State
    :param chat_id_state: Gradio state for the current chat ID.
    :type chat_id_state: gr.State
    :param chat_history_state: Gradio state for the current chat history.
    :type chat_history_state: gr.State
    :param all_chats_data_state: Gradio state for all chat metadata and histories.
    :type all_chats_data_state: gr.State
    :param debug_info_state: Gradio state for displaying debug information.
    :type debug_info_state: gr.State
    :return: A tuple of Gradio components: chatbot, message input, send button,
             rename input, rename button, rename status markdown, search box,
             search button, search results markdown, chat selector dropdown, and new chat button.
    :rtype: Tuple[gr.Chatbot, gr.Textbox, gr.Button, gr.Textbox, gr.Button, gr.Markdown, gr.Textbox, gr.Button, gr.Markdown, gr.Dropdown, gr.Button]
    """
    with gr.Column(elem_classes=["chatbot-interface-container"]):
        gr.Markdown("### 💬 Chatbot")

        with gr.Row():
            chat_selector_component = gr.Dropdown(
                label="Select Chat",
                choices=[],  # Populated dynamically
                value="",
                interactive=False,
                elem_id="chat-selector-dropdown",
            )
            new_chat_btn = gr.Button("➕ New Chat", interactive=False)

        chatbot = gr.Chatbot(
            value=[],
            elem_id="chatbot",
            label="Chat History",
            height=400,
            show_copy_button=True,
            show_share_button=True,
            show_label=True,
            likeable=False,
        )
        msg = gr.Textbox(
            label="Message",
            placeholder="Type your message here...",
            show_label=False,
            container=False,
            scale=7,
            interactive=False,
        )
        send_btn = gr.Button("Send", scale=1, interactive=False)

        # Chat Renaming Section
        with gr.Accordion("⚙️ Chat Settings", open=False):
            with gr.Column():
                rename_input = gr.Textbox(
                    label="Rename Current Chat",
                    placeholder="Enter new chat name...",
                    interactive=False,
                )
                rename_btn = gr.Button("Rename Chat", interactive=False)
                rename_status_md = gr.Markdown("")

        # Search History Section
        with gr.Accordion("🔍 Search History", open=False):
            search_box = gr.Textbox(
                label="Search Query",
                placeholder="Enter keywords to search chat history...",
                interactive=False,
            )
            search_btn = gr.Button("Search", interactive=False)
            search_results_md = gr.Markdown("Search results will appear here.")

        # Event Handlers (inputs and outputs are carefully managed for state updates)

        # Handle new chat creation
        new_chat_btn.click(
            fn=lambda: (
                "new_chat_id",  # Set a special ID for new chat
                [],  # Clear chat history display
                "New Chat",  # Set temporary name for display
                gr.update(interactive=True),  # Enable message input
                gr.update(interactive=True),  # Enable send button
                "",  # Clear debug info
            ),
            outputs=[
                chat_id_state,
                chatbot,
                rename_input,  # Also set rename_input to "New Chat"
                msg,
                send_btn,
                debug_info_state,
            ],
            show_progress=False,
        )

        # Load chat when selected from dropdown
        chat_selector_component.change(
            fn=lambda selected_id, all_data, current_id: (
                selected_id
                if selected_id
                else current_id,  # Use selected_id or keep current if cleared
                all_data.get(selected_id, {}).get("history", [])
                if selected_id
                else [],  # Load history based on ID
                all_data.get(selected_id, {}).get("name", "New Chat")
                if selected_id
                else "New Chat",  # Set name in rename box
                gr.update(interactive=True),  # Enable message input
                gr.update(interactive=True),  # Enable send button
                gr.update(interactive=True),  # Enable rename input
                gr.update(interactive=True),  # Enable rename button
                gr.update(interactive=True),  # Enable search box
                gr.update(interactive=True),  # Enable search button
                "Chat Loaded.",  # Clear debug info
            ),
            inputs=[chat_selector_component, all_chats_data_state, chat_id_state],
            outputs=[
                chat_id_state,
                chatbot,
                rename_input,
                msg,
                send_btn,
                rename_input,
                rename_btn,
                search_box,
                search_btn,
                debug_info_state,
            ],
            show_progress=False,
        )

        # Handle message sending
        msg.submit(
            fn=_handle_chat_message,
            inputs=[
                msg,
                chatbot,  # Use chatbot component as chat_history for direct update
                username_state,
                chat_id_state,
                all_chats_data_state,
                debug_info_state,
            ],
            outputs=[
                msg,
                chatbot,
                all_chats_data_state,
                debug_info_state,
                send_btn,
                chat_id_state,
                chat_selector_component,  # New outputs for chat_id_state and chat_selector
            ],
            show_progress=True,
            queue=False,  # Do not queue messages, process immediately
        )
        send_btn.click(
            fn=_handle_chat_message,
            inputs=[
                msg,
                chatbot,  # Use chatbot component as chat_history for direct update
                username_state,
                chat_id_state,
                all_chats_data_state,
                debug_info_state,
            ],
            outputs=[
                msg,
                chatbot,
                all_chats_data_state,
                debug_info_state,
                send_btn,
                chat_id_state,
                chat_selector_component,  # New outputs for chat_id_state and chat_selector
            ],
            show_progress=True,
            queue=False,
        )

        # Chat renaming - updated outputs for chat_selector_component
        rename_btn.click(
            fn=_handle_rename_chat,
            inputs=[chat_id_state, rename_input, username_state, all_chats_data_state],
            outputs=[
                rename_status_md,
                rename_input,
                all_chats_data_state,
                chat_selector_component,  # Now directly updating the chat_selector
            ],
        )
        # Search history
        search_btn.click(
            fn=_handle_search_chat_history,
            inputs=[search_box, username_state],
            outputs=[search_results_md, search_box],
        )
        search_box.submit(  # Allow pressing Enter in search box
            fn=_handle_search_chat_history,
            inputs=[search_box, username_state],
            outputs=[search_results_md, search_box],
        )

    return (
        chatbot,
        msg,
        send_btn,
        rename_input,
        rename_btn,
        rename_status_md,
        search_box,
        search_btn,
        search_results_md,
        chat_selector_component,  # Return the chat selector component
        new_chat_btn,  # Return the new chat button
    )
