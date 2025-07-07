# search_interface.py
#!/usr/bin/env python3
"""
Search interface module for chat history search functionality.

This module provides a Gradio UI component specifically for searching
through a user's chat history and displaying the results.
"""

from typing import Dict, Any, List, Tuple
import gradio as gr
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from backend.chat import search_chat_history, get_chat_history  # DO NOT RENAME

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> Tuple[gr.Column, gr.Textbox, gr.Button, gr.Dropdown]:
    """
    Create the search interface components.

    This function creates the search UI components including:
    - Search input box.
    - Search button to trigger the search.
    - Search results dropdown to display and select results.
    - A container column to hold these components.

    :param logged_in_state: State for tracking user login status.
    :type logged_in_state: gr.State
    :param username_state: State for storing the current username.
    :type username_state: gr.State
    :param current_chat_id_state: State for storing the current chat ID.
    :type current_chat_id_state: gr.State
    :param chat_history_state: State for storing the current chat history.
    :type chat_history_state: gr.State
    :return: A tuple containing the search container (gr.Column), search query textbox,
              search button, and search results dropdown.
    :rtype: Tuple[gr.Column, gr.Textbox, gr.Button, gr.Dropdown]
    """
    with gr.Column(visible=False) as search_container:  # Container for search UI
        with gr.Row():
            search_query = gr.Textbox(
                label="Search chats", placeholder="Enter search query...", scale=4
            )
            search_btn = gr.Button("Search", scale=1)

        search_results_dropdown = gr.Dropdown(
            label="Search Results",
            choices=[],
            interactive=True,
            allow_custom_value=False,  # Users should pick from results, not type
        )

    # Make the handler async to support potential async backend calls
    async def _handle_search_query(
        query: str, username: str
    ) -> Dict[str, Any]:  # <--- MODIFIED TO ASYNC
        """
        Handle a search query from the UI and return matching results for dropdown.

        This function calls the backend's `search_chat_history` and formats
        the results for display in a Gradio Dropdown component.

        :param query: The search query string.
        :type query: str
        :param username: The current username.
        :type username: str
        :return: A dictionary suitable for updating a Gradio Dropdown,
                  containing 'choices' and 'value'.
        :rtype: Dict[str, Any]
        """
        if not query.strip() or not username:
            return gr.update(choices=[], value=None)

        try:
            # Get search results from backend
            # search_chat_history returns list of dicts with chat_name, chat_id, etc.
            results = await search_chat_history(
                query.strip(), username
            )  # <--- ADDED AWAIT

            # Format results for dropdown: (display_name, value_to_pass)
            # Display name will include chat name and a preview
            # Value to pass will be the chat_id
            dropdown_choices = []
            if results:
                for result in results:
                    chat_name = result.get(
                        "chat_name", result.get("chat_id", "Unknown Chat")
                    )
                    chat_preview = result.get("chat_preview", "No preview available.")
                    chat_id = result.get("chat_id")
                    display_text = f"{chat_name}: {chat_preview}"
                    dropdown_choices.append((display_text, chat_id))

            return gr.update(choices=dropdown_choices, value=None)
        except Exception as e:
            logger.error(f"Error handling search: {e}")
            return gr.update(choices=[], value=None)

    # Make the handler async to support potential async backend calls
    async def _handle_search_result_selection(  # <--- MODIFIED TO ASYNC
        selected_chat_id: str, username: str
    ) -> Tuple[str, List[List[str]]]:
        """
        Handle selection of a search result and return the corresponding chat history.

        This function is triggered when a user selects an item from the search results dropdown.
        It retrieves the full chat history for the selected chat ID from the backend.

        :param selected_chat_id: The ID of the selected chat result.
        :type selected_chat_id: str
        :param username: The current username.
        :type username: str
        :return: A tuple containing the selected chat ID and its history
                  (list of [user_msg, bot_msg] pairs) for display in a chatbot component.
        :rtype: Tuple[str, List[List[str]]]
        """
        if not selected_chat_id or not username:
            return "", []

        try:
            # Get chat history for selected result
            history = await get_chat_history(
                selected_chat_id, username
            )  # <--- ADDED AWAIT
            # Convert tuples to lists to match the expected return type for Gradio Chatbot
            if history:
                return selected_chat_id, [[str(msg[0]), str(msg[1])] for msg in history]
            else:
                return selected_chat_id, []
        except Exception as e:
            logger.error(f"Error handling search result selection: {e}")
            return selected_chat_id, []

    # Bind events
    search_query.submit(
        fn=_handle_search_query,
        inputs=[search_query, username_state],
        outputs=[search_results_dropdown],
    )
    search_btn.click(
        fn=_handle_search_query,
        inputs=[search_query, username_state],
        outputs=[search_results_dropdown],
    )

    search_results_dropdown.change(
        fn=_handle_search_result_selection,
        inputs=[search_results_dropdown, username_state],
        outputs=[current_chat_id_state, chat_history_state],
    )

    return search_container, search_query, search_btn, search_results_dropdown
