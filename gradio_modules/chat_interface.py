#!/usr/bin/env python3
"""
Chat Interface Module

This module provides the main chat interface for the NYP FYP Chatbot application.
Users can send messages, view chat history, and manage multiple chat sessions.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import gradio as gr

from backend import (
    list_user_chat_ids,
    get_chat_history,
    ask_question,
    create_and_persist_new_chat,
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

    if not message.strip():
        return (
            "",
            chat_history,
            {"visible": True, "value": "Please enter a message."},
            chat_id,
        )
    if not chat_id:
        chat_id = create_and_persist_new_chat(username)
        chat_history = []
    result = await ask_question(message, chat_id, username)
    if result.get("code") == "200":
        answer = result.get("response", "")
        if isinstance(answer, dict) and "answer" in answer:
            answer = answer["answer"]
        chat_history.append([message, answer])
        return "", chat_history, {"visible": False, "value": ""}, chat_id
    else:
        chat_history.append([message, f"Error: {result.get('error', 'Unknown error')}"])
        return (
            "",
            chat_history,
            {"visible": True, "value": result.get("error", "Unknown error")},
            chat_id,
        )


def chat_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> None:
    """
    Create the chat interface components.

    Args:
        logged_in_state: State for tracking login status
        username_state: State for storing current username
        current_chat_id_state: State for storing current chat ID
        chat_history_state: State for storing chat history
    """
    with gr.Row():
        chat_selector = gr.Dropdown(choices=[], label="Select Chat")
        new_chat_btn = gr.Button("New Chat")
    chatbot = gr.Chatbot(label="Chatbot", type="messages")
    msg = gr.Textbox(label="Message", placeholder="Type your message here...")
    send_btn = gr.Button("Send")
    with gr.Row(visible=False, elem_id="search-row"):
        search_box = gr.Textbox(
            label="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
            placeholder="Fuzzy Search (Ctrl+Shift+K or Alt+K)",
        )
        search_results = gr.Markdown()

    def load_all_chats(username: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Load all chat histories for a user.

        Args:
            username: The username to load chats for

        Returns:
            Dictionary mapping chat IDs to their message histories
        """
        chat_ids = list_user_chat_ids(username)
        all_histories = {}
        for cid in chat_ids:
            try:
                hist = get_chat_history(cid, username)
                # Convert tuples to messages format
                if hist:
                    messages = []
                    for pair in hist:
                        messages.append({"role": "user", "content": pair[0]})
                        messages.append({"role": "assistant", "content": pair[1]})
                    all_histories[cid] = messages
                else:
                    all_histories[cid] = []
            except Exception as e:
                all_histories[cid] = [
                    {"role": "user", "content": "[Error loading chat]"},
                    {"role": "assistant", "content": str(e)},
                ]
        return all_histories

    def on_start(
        username: str,
    ) -> Tuple[gr.update, str, Dict[str, List[Dict[str, str]]], List[Dict[str, str]]]:
        """
        Initialize chat interface on startup.

        Args:
            username: The username to initialize for

        Returns:
            Tuple containing dropdown update, selected chat ID, all histories, and selected chat history
        """
        all_histories = load_all_chats(username)
        chat_ids = list(all_histories.keys())
        selected = chat_ids[0] if chat_ids else ""
        return (
            gr.update(choices=chat_ids, value=selected),
            selected,
            all_histories,
            all_histories[selected] if selected else [],
        )

    def start_new_chat(
        all_histories: Dict[str, List[Dict[str, str]]], username: str
    ) -> Tuple[gr.update, str, Dict[str, List[Dict[str, str]]], List[Dict[str, str]]]:
        """
        Start a new chat session.

        Args:
            all_histories: Current chat histories
            username: The username to create chat for

        Returns:
            Tuple containing dropdown update, new chat ID, updated histories, and empty chat history
        """
        new_id = create_and_persist_new_chat(username)
        all_histories[new_id] = []
        return (
            gr.update(choices=list(all_histories.keys()), value=new_id),
            new_id,
            all_histories,
            [],
        )

    new_chat_btn.click(
        start_new_chat,
        inputs=[chat_history_state, username_state],
        outputs=[chat_selector, current_chat_id_state, chat_history_state, chatbot],
    )

    def switch_chat(
        chat_id: str, all_histories: Dict[str, List[Dict[str, str]]]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Switch to a different chat.

        Args:
            chat_id: The chat ID to switch to
            all_histories: All chat histories

        Returns:
            Tuple containing chat ID and selected chat history
        """
        return chat_id, all_histories.get(chat_id, [])

    chat_selector.change(
        fn=switch_chat,
        inputs=[chat_selector, chat_history_state],
        outputs=[current_chat_id_state, chatbot],
    )

    def send_message_to_chat(
        message: str,
        chat_id: str,
        all_histories: Dict[str, List[Dict[str, str]]],
        username: str,
    ) -> Tuple[str, Dict[str, List[Dict[str, str]]], str, List[Dict[str, str]]]:
        """
        Send a message to the current chat.

        Args:
            message: The message to send
            chat_id: Current chat ID
            all_histories: All chat histories
            username: Current username

        Returns:
            Tuple containing empty message, updated histories, chat ID, and updated chat history
        """
        if not message.strip():
            return (
                "",
                all_histories,
                chat_id,
                [
                    {"role": "user", "content": ""},
                    {"role": "assistant", "content": "Please enter a message."},
                ],
            )
        if not chat_id:
            chat_id = create_and_persist_new_chat(username)
            all_histories[chat_id] = []
        result = asyncio.run(ask_question(message, chat_id, username))
        if result.get("code") == "200":
            answer = result.get("response", "")
            if isinstance(answer, dict) and "answer" in answer:
                answer = answer["answer"]
            all_histories[chat_id].extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": answer},
                ]
            )
        else:
            all_histories[chat_id].extend(
                [
                    {"role": "user", "content": message},
                    {
                        "role": "assistant",
                        "content": f"Error: {result.get('error', 'Unknown error')}",
                    },
                ]
            )
        return "", all_histories, chat_id, all_histories[chat_id]

    send_btn.click(
        fn=send_message_to_chat,
        inputs=[msg, current_chat_id_state, chat_history_state, username_state],
        outputs=[msg, chat_history_state, current_chat_id_state, chatbot],
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
        for cid, history in all_histories.items():
            # Extract content from messages format
            all_text = " ".join(
                [msg.get("content", "") for msg in history if isinstance(msg, dict)]
            )
            if query.lower() in all_text.lower() or get_close_matches(
                query, [all_text], n=1, cutoff=0.6
            ):
                results.append(f"Chat {cid}: {all_text[:100]}...")
        return "\n\n".join(results) if results else "No matching chats found."

    search_box.submit(
        fn=fuzzy_find_chats,
        inputs=[search_box, chat_history_state],
        outputs=[search_results],
    )
