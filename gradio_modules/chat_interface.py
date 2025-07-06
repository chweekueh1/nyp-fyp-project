#!/usr/bin/env python3
"""
Chat Interface Module

This module provides the main chat interface for the NYP FYP Chatbot application.
Users can send messages, view chat history, and manage multiple chat sessions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import gradio as gr

from backend import (
    list_user_chat_ids,
    get_chat_history,
    ask_question,
    create_and_persist_new_chat,
    get_chat_name,  # Added this import
)
from infra_utils import setup_logging

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
logger = setup_logging()


# Module-level function for testing
async def _handle_chat_message(
    message: str,
    chat_history: List[List[str]],
    username: str,
    chat_id: str,
) -> Tuple[str, List[List[str]], Dict[str, Any], str]:
    """
    Handle chat message processing - module level function for testing.

    Args:
        message: The message to process
        chat_history: The current chat history
        username: The username of the user
        chat_id: The chat ID

    Returns:
        Tuple containing:
        - updated_message: Empty string after processing
        - updated_chat_history: Updated chat history with new message/response
        - error_dict: Error information if any
        - updated_chat_id: Updated chat ID
    """
    if not message:
        return "", chat_history, {}, chat_id  # Return empty if no message

    logger.info(f"Received message: {message} for chat_id: {chat_id}")

    try:
        # Use the backend function to ask the question
        result = await ask_question(message, chat_id, username)
        if result.get("status") == "OK":
            bot_message = result["response"].get("answer", str(result["response"]))
            chat_history.append([message, bot_message])
            return "", chat_history, {}, chat_id
        else:
            error_msg = result.get("error", "An unknown error occurred.")
            error_code = result.get("code", "500")
            logger.error(f"Error from ask_question (Code: {error_code}): {error_msg}")
            chat_history.append(
                [
                    message,
                    f"Error: Could not get a response from the chatbot ({error_msg})",
                ]
            )
            return "", chat_history, {"error": error_msg, "code": error_code}, chat_id
    except Exception as e:
        logger.exception("Exception in _handle_chat_message:")
        chat_history.append([message, f"Error: An unexpected error occurred: {str(e)}"])
        return "", chat_history, {"error": str(e), "code": "500"}, chat_id


def chat_interface_ui(
    username_state: gr.State, chat_id_state: gr.State, chat_history_state: gr.State
) -> Tuple[
    gr.Chatbot,
    gr.Textbox,
    gr.Button,
    gr.Dropdown,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Textbox,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
]:
    """
    Create the chat interface UI components.

    Args:
        username_state: Gradio State holding the current username.
        chat_id_state: Gradio State holding the current chat ID.
        chat_history_state: Gradio State holding the chat history.

    Returns:
        A tuple of Gradio components:
        - chatbot: The main chatbot display.
        - msg: The message input textbox.
        - send_btn: The send message button.
        - chat_selector: Dropdown to select chat sessions.
        - new_chat_btn: Button to create a new chat.
        - rename_input: Textbox for renaming chats.
        - rename_btn: Button to rename a chat.
        - rename_status_md: Markdown for rename status.
        - search_box: Textbox for search query.
        - search_btn: Button to initiate search.
        - search_results_md: Markdown to display search results.
        - clear_chat_btn: Button to clear chat history.
        - clear_chat_status_md: Markdown for clear chat status.
    """
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Column():
                chat_selector = gr.Dropdown(
                    label="Select Chat",
                    choices=[],
                    value=None,
                    interactive=True,
                    allow_custom_value=False,
                )
                new_chat_btn = gr.Button("➕ New Chat")
                rename_input = gr.Textbox(
                    label="Rename Current Chat", placeholder="Enter new chat name..."
                )
                rename_btn = gr.Button("Rename Chat")
                rename_status_md = gr.Markdown("")
                clear_chat_btn = gr.Button("🗑️ Clear Chat History")
                clear_chat_status_md = gr.Markdown("")
            with gr.Accordion("Search Chat History", open=False):
                search_box = gr.Textbox(
                    label="Search chats", placeholder="Enter search query..."
                )
                search_btn = gr.Button("Search")
                search_results_md = gr.Markdown("")

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=500, label="Chat History", show_copy_button=True
            )
            msg = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
                scale=7,
                container=False,
            )
            send_btn = gr.Button("Send", scale=1)

    # State for all chat histories, mapping chat_id to a dictionary
    # { 'history': List[List[str]], 'name': str }
    all_chat_histories_memory = gr.State({})

    # Helper function to load chat histories and update dropdown
    def load_user_chats_and_metadata(username: str) -> Tuple[Dict, List, str, List]:
        if not username:
            return {}, [], "", []

        all_chats_data = {}
        chat_choices = []
        all_chats_list = list_user_chat_ids(username)

        if all_chats_list:
            for chat_id in all_chats_list:
                name = get_chat_name(chat_id, username)
                history = get_chat_history(chat_id, username)
                all_chats_data[chat_id] = {
                    "history": [list(pair) for pair in history] if history else [],
                    "name": name,
                }
                chat_choices.append((name, chat_id))

            # Sort chats by name for consistent display
            chat_choices.sort(key=lambda x: x[0].lower())

            # Select the most recent chat or the first one if no explicit selection
            # For simplicity, let's select the first one for now
            selected_chat_id = chat_choices[0][1] if chat_choices else ""
            selected_chat_history = (
                all_chats_data.get(selected_chat_id, {}).get("history", [])
                if selected_chat_id
                else []
            )

            return (
                all_chats_data,
                gr.update(choices=chat_choices, value=selected_chat_id),
                selected_chat_id,
                selected_chat_history,
            )
        return {}, gr.update(choices=[], value=None), "", []

    # Chat selector logic
    chat_selector.change(
        fn=lambda chat_id, all_histories: (
            all_histories.get(chat_id, {}).get("history", []),
            chat_id,
        ),
        inputs=[chat_selector, all_chat_histories_memory],
        outputs=[chatbot, chat_id_state],
        show_progress=False,
    )

    # New Chat Button
    def handle_new_chat(username: str) -> Tuple[gr.Dropdown, str, List, Dict]:
        if not username:
            gr.Warning("Please login to create a new chat.")
            return gr.update(), "", [], {}

        create_and_persist_new_chat(username)  # Removed new_chat_id assignment
        # After creating, reload all chats to update the dropdown and memory
        all_chats_data, chat_dropdown_update, new_chat_id, new_chat_history = (
            load_user_chats_and_metadata(username)
        )
        return chat_dropdown_update, new_chat_id, new_chat_history, all_chats_data

    new_chat_btn.click(
        fn=handle_new_chat,
        inputs=[username_state],
        outputs=[chat_selector, chat_id_state, chatbot, all_chat_histories_memory],
    )

    # Rename Chat Button
    def handle_rename_chat(
        username: str, chat_id: str, new_name: str
    ) -> Tuple[gr.Dropdown, gr.Markdown, Dict]:
        if not username or not chat_id:
            return gr.update(), gr.Markdown("Please select a chat to rename."), {}
        if not new_name.strip():
            return gr.update(), gr.Markdown("Chat name cannot be empty."), {}

        try:
            from backend import rename_chat  # Import locally to avoid circular

            rename_chat(chat_id, username, new_name.strip())
            all_chats_data, chat_dropdown_update, _, _ = load_user_chats_and_metadata(
                username
            )
            return (
                chat_dropdown_update,
                gr.Markdown(f"Chat renamed to '{new_name.strip()}'."),
                all_chats_data,
            )
        except Exception as e:
            return gr.update(), gr.Markdown(f"Error renaming chat: {e}"), {}

    rename_btn.click(
        fn=handle_rename_chat,
        inputs=[username_state, chat_id_state, rename_input],
        outputs=[chat_selector, rename_status_md, all_chat_histories_memory],
    )

    # Clear Chat History Button
    def handle_clear_chat_history(username: str, chat_id: str) -> gr.Markdown:
        if not username or not chat_id:
            return gr.Markdown("Please select a chat to clear.")
        try:
            from infra_utils import clear_chat_history

            clear_chat_history(username, chat_id)
            return gr.Markdown(f"History for chat '{chat_id}' cleared.")
        except Exception as e:
            return gr.Markdown(f"Error clearing chat history: {e}")

    clear_chat_btn.click(
        fn=handle_clear_chat_history,
        inputs=[username_state, chat_id_state],
        outputs=[clear_chat_status_md],
    )

    # Send message logic
    async def send_message_to_chat(
        message: str,
        chat_id: str,
        all_histories: Dict[str, List[List[str]]],
        username: str,
    ) -> Tuple[str, Dict[str, List[List[str]]], str, List[List[str]]]:
        if not username:
            gr.Warning("Please login to send messages.")
            return "", all_histories, chat_id, []

        if not chat_id:
            gr.Warning("Please create or select a chat session first.")
            return "", all_histories, chat_id, []

        if not message.strip():
            return (
                "",
                all_histories,
                chat_id,
                all_histories.get(chat_id, {}).get("history", []),
            )

        # Update UI immediately with user message
        current_chat_history = all_histories.get(chat_id, {}).get("history", [])
        current_chat_history.append([message, None])  # Display user message
        all_histories[chat_id]["history"] = current_chat_history

        # Call backend for response
        try:
            result = await ask_question(message, chat_id, username)
            if result.get("status") == "OK":
                bot_message = result["response"].get("answer", str(result["response"]))
                # Replace the None with the actual bot message
                current_chat_history[-1][1] = bot_message
            else:
                error_msg = result.get("error", "Unknown error")
                current_chat_history[-1][1] = f"Error: {error_msg}"

        except Exception as e:
            logger.exception("Error during ask_question call:")
            current_chat_history[-1][1] = f"Error: {str(e)}"

        # Return updated history for display
        return "", all_histories, chat_id, current_chat_history

    send_btn.click(
        fn=send_message_to_chat,
        inputs=[msg, chat_id_state, all_chat_histories_memory, username_state],
        outputs=[msg, all_chat_histories_memory, chat_id_state, chatbot],
    )

    def fuzzy_find_chats(
        query: str, all_histories: Dict[str, List[Dict[str, str]]]
    ) -> str:
        """
        Perform fuzzy search through chat histories.

        Args:
            query: The search query
            all_histories: All chat histories to search through

        Returns:
            Formatted string containing matching chat results
        """
        from difflib import get_close_matches

        results = []
        for cid, chat_data in all_histories.items():
            history = chat_data.get("history", [])
            chat_name = chat_data.get("name", cid)
            # Extract content from messages format
            all_text = (
                chat_name
                + " "
                + " ".join(
                    [msg.get("content", "") for msg in history if isinstance(msg, dict)]
                )
            )
            if query.lower() in all_text.lower() or get_close_matches(
                query, [all_text], n=1, cutoff=0.6
            ):
                results.append(f"**{chat_name} (ID: {cid})**: {all_text[:100]}...")
        return "\n\n".join(results) if results else "No matching chats found."

    search_btn.click(
        fn=fuzzy_find_chats,
        inputs=[search_box, all_chat_histories_memory],
        outputs=[search_results_md],
    )

    return (
        chatbot,
        msg,
        send_btn,
        chat_selector,
        new_chat_btn,
        rename_input,
        rename_btn,
        rename_status_md,
        search_box,
        search_btn,
        search_results_md,
        clear_chat_btn,
        clear_chat_status_md,
    )
