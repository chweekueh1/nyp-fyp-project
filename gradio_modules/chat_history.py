# chat_history.py
#!/usr/bin/env python3
"""
Chat History Interface Module

This module provides the chat history interface for the NYP FYP Chatbot application.
Users can search through their chat history and view previous conversations.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple

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
    # Correctly import fuzzy_search_chats from backend.chat as requested
    from backend.chat import fuzzy_search_chats as backend_fuzzy_search_chats
except ImportError as e:
    logger.error(f"Failed to import backend functions: {e}")
    raise


def chat_history_ui(
    username_state: gr.State, chat_id_state: gr.State, chat_history_state: gr.State
) -> Tuple[gr.Textbox, gr.Button, gr.Markdown]:
    """
    Create the chat history UI components.

    This function sets up the Gradio components for searching chat history,
    including a search box, a search button, and a markdown component
    to display results. It also defines the search logic.

    :param username_state: Gradio State component containing the current username.
    :type username_state: gr.State
    :param chat_id_state: Gradio State component containing the current chat ID.
    :type chat_id_state: gr.State
    :param chat_history_state: Gradio State component containing the current chat history.
    :type chat_history_state: gr.State
    :return: A tuple containing the search box, search button, and results markdown components.
    :rtype: Tuple[gr.Textbox, gr.Button, gr.Markdown]
    """
    search_box = gr.Textbox(
        label="Search chat history",
        placeholder="Enter search query...",
        show_label=True,
    )
    search_btn = gr.Button("Search Chat History")
    results_md = gr.Markdown("Search results will appear here.")

    def search_history(username: str, chat_id: str, search_query: str) -> str:
        """
        Search chat history for the given user and query.

        This function uses the backend's fuzzy search capability to find
        matching chat sessions and formats the results for display.

        :param username: The username of the user performing the search.
        :type username: str
        :param chat_id: The ID of the current chat (not directly used by fuzzy search, but passed for context).
        :type chat_id: str
        :param search_query: The query string to search for.
        :type search_query: str
        :return: A formatted string containing the search results or an error message.
        :rtype: str
        """
        if not username:
            return "Please login to search chat history."
        if not search_query:
            return "Please enter a search query."
        try:
            # Use the imported fuzzy_search_chats from backend
            # Assuming backend_fuzzy_search_chats expects (query, username)
            results = backend_fuzzy_search_chats(search_query, username)
            return (
                results  # backend_fuzzy_search_chats already returns a formatted string
            )
        except Exception as e:
            logger.error(f"Error searching chat history: {e}")
            return f"Error searching chat history: {e}"

    search_btn.click(
        fn=search_history,
        inputs=[username_state, chat_id_state, search_box],
        outputs=[results_md],
    )

    return search_box, search_btn, results_md
