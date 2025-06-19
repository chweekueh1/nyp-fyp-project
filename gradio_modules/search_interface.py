from typing import Dict, Any, List
import gradio as gr
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from backend import search_chat_history, get_chat_history

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_interface(
    logged_in_state: gr.State,
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State
) -> None:
    """
    Create the search interface components.
    
    This function creates the search UI components including:
    - Search input
    - Search button
    - Search results dropdown
    - Search container
    
    Args:
        logged_in_state (gr.State): State for tracking login status
        username_state (gr.State): State for storing current username
        current_chat_id_state (gr.State): State for storing current chat ID
        chat_history_state (gr.State): State for storing chat history
    """
    with gr.Column(visible=False) as search_container:
        with gr.Row():
            search_query = gr.Textbox(
                label="Search",
                placeholder="Search your chat history...",
                show_label=False,
                container=False
            )
            search_button = gr.Button("Search")
        search_results = gr.Dropdown(
            label="Search Results",
            choices=[],
            show_label=True,
            interactive=True
        )
        
        # Add search button click event
        search_button.click(
            fn=_handle_search,
            inputs=[
                search_query,
                username_state
            ],
            outputs=[search_results]
        )
        
        # Add search result selection event
        search_results.select(
            fn=_handle_search_result,
            inputs=[
                search_results,
                username_state
            ],
            outputs=[chat_history_state]
        )

def _handle_search(query: str, username: str) -> Dict[str, Any]:
    """
    Handle search query and return matching results.
    
    Args:
        query (str): The search query.
        username (str): Current username.
        
    Returns:
        Dict[str, Any]: Updated search results dropdown.
    """
    if not query:
        return {"choices": [], "value": None}
        
    try:
        # Get search results from backend
        results = search_chat_history(query, username)
        # Always ensure results are strings for dropdown
        results = [str(r) for r in results]
        return {"choices": results, "value": None}
    except Exception as e:
        logger.error(f"Error handling search: {e}")
        return {"choices": [], "value": None}

def _handle_search_result(selected: str, username: str) -> List[List[str]]:
    """
    Handle search result selection and return the corresponding chat history.
    
    Args:
        selected (str): The selected search result.
        username (str): Current username.
        
    Returns:
        List[List[str]]: Chat history for the selected result.
    """
    if not selected:
        return []
        
    try:
        # Get chat history for selected result
        history = get_chat_history(username, selected)
        # Convert tuples to lists to match the expected return type
        if history:
            return [[str(msg[0]), str(msg[1])] for msg in history]
        else:
            return []
    except Exception as e:
        logger.error(f"Error handling search result: {e}")
        return []