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
    """Create the search interface components and add them to app_data."""
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

def _handle_search(query: str, username: str) -> List[str]:
    """Handle search query.
    
    Args:
        query: The search query
        username: The username to search for
        
    Returns:
        List of search results
    """
    if not query or not username:
        return []
    
    try:
        # Get search results from backend
        results = search_chat_history(query, username)
        return [str(r) for r in results] if results else []
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return []

def _handle_search_result(chat_id: str, username: str) -> List[tuple[str, str]]:
    """Handle search result selection.
    
    Args:
        chat_id: The selected chat ID
        username: The username to get chat history for
        
    Returns:
        List of chat messages
    """
    if not chat_id or not username:
        return []
    
    try:
        # Get chat history from backend
        history = get_chat_history(chat_id, username)
        return [(msg[0], msg[1]) for msg in history] if history else []
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return [] 