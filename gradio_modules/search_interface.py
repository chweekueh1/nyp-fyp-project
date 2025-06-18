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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import backend functions
try:
    from backend import search_chat_history, get_chat_history
except ImportError as e:
    logger.error(f"Failed to import backend functions: {e}")
    raise

def search_interface(app_data: Dict[str, Any]) -> None:
    """
    Create the search interface components and add them to app_data.
    
    This function creates the search UI components including:
    - Search input
    - Search button
    - Search results dropdown
    - Search container
    
    Args:
        app_data (Dict[str, Any]): Dictionary containing Gradio components and states.
    """
    with gr.Column(visible=False) as search_container:
        with gr.Row():
            app_data['search_query'] = gr.Textbox(
                label="Search",
                placeholder="Search your chat history...",
                show_label=False,
                container=False
            )
            app_data['search_button'] = gr.Button("Search")
        app_data['search_results'] = gr.Dropdown(
            label="Search Results",
            choices=[],
            show_label=True,
            interactive=True
        )
        app_data['search_container'] = search_container
        # Add search button click event
        app_data['search_button'].click(
            fn=_handle_search,
            inputs=[
                app_data['search_query'],
                app_data['username_state']
            ],
            outputs=[app_data['search_results']]
        )
        # Add search result selection event
        app_data['search_results'].select(
            fn=_handle_search_result,
            inputs=[
                app_data['search_results'],
                app_data['username_state']
            ],
            outputs=[app_data['chat_history_state']]
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
        return [[str(msg[0]), str(msg[1])] for msg in history] if history else []
    except Exception as e:
        logger.error(f"Error handling search result: {e}")
        return [] 