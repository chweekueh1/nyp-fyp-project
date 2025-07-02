#!/usr/bin/env python3
"""
Chat History Interface Module

This module provides the chat history interface for the NYP FYP Chatbot application.
Users can search through their chat history and view previous conversations.
"""

import json
import logging
import os
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Any, Tuple

import gradio as gr

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import backend functions
try:
    from backend import search_chat_history, get_chat_history
except ImportError as e:
    logger.error(f"Failed to import backend functions: {e}")
    raise


def chat_history_ui(
    username_state: gr.State, chat_id_state: gr.State, chat_history_state: gr.State
) -> Tuple[gr.Textbox, gr.Button, gr.Markdown]:
    """Create the chat history UI components.

    Args:
        username_state: State containing the username
        chat_id_state: State containing the current chat ID
        chat_history_state: State containing the chat history

    Returns:
        Tuple of (search box, search button, results markdown)
    """
    search_box = gr.Textbox(
        label="Search chat history",
        placeholder="Enter search query...",
        show_label=True,
    )
    search_btn = gr.Button("Search History")
    results_md = gr.Markdown(visible=True)

    def search_history(user: str, chat_id: str, query: str) -> Dict[str, Any]:
        """Search through chat history.

        Args:
            user: The username
            chat_id: The chat ID
            query: The search query

        Returns:
            Updated markdown with search results
        """
        if not user or not chat_id:
            return gr.update(value="Not logged in or no chat selected.")

        try:
            # Get search results from backend
            results = search_chat_history(query, user)
            if not results:
                return gr.update(value="No results found.")

            # Format results
            formatted_results = []
            for result in results:
                history = get_chat_history(str(result), user)
                if history:
                    formatted_results.append(f"**Chat {result}**:")
                    for msg in history:
                        formatted_results.append(f"{msg[0]}: {msg[1]}")
                    formatted_results.append("---")

            return gr.update(value="\n".join(formatted_results))
        except Exception as e:
            logger.error(f"Error searching chat history: {e}")
            return gr.update(value=f"Error searching chat history: {e}")

    search_btn.click(
        fn=search_history,
        inputs=[username_state, chat_id_state, search_box],
        outputs=[results_md],
    )

    return search_box, search_btn, results_md


def fuzzy_find_chats(user: str, query: str) -> str:
    """
    Fuzzy search through all chats for a user.

    Args:
        user: The username to search chats for
        query: The search query string

    Returns:
        Formatted string containing matching chat results
    """
    if not user or not query:
        return "Please login and enter a search query."
    chat_dir = os.path.join(os.getcwd(), "data", "chat_sessions", user)
    if not os.path.exists(chat_dir):
        return "No chats found."
    results = []
    for fname in os.listdir(chat_dir):
        if fname.endswith(".json"):
            with open(os.path.join(chat_dir, fname), "r") as f:
                try:
                    history = json.load(f)
                    all_text = " ".join([msg.get("content", "") for msg in history])
                    if query.lower() in all_text.lower() or get_close_matches(
                        query, [all_text], n=1, cutoff=0.6
                    ):
                        results.append(f"**{fname}**: {all_text[:100]}...")
                except Exception:
                    continue
    if not results:
        return "No matching chats found."
    return "\n\n".join(results)
