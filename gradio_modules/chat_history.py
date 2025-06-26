#!/usr/bin/env python3
import gradio as gr
import logging
import os
import sys
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from difflib import get_close_matches

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
    from utils import get_chatbot_dir
except ImportError as e:
    logger.error(f"Failed to import backend functions: {e}")
    raise

def chat_history_ui(username_state: gr.State, chat_id_state: gr.State, chat_history_state: gr.State) -> Tuple[gr.Textbox, gr.Button, gr.Markdown]:
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
        show_label=True
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
        outputs=[results_md]
    )
    
    return search_box, search_btn, results_md

def test_chat_history_ui():
    """Test the chat history UI components."""
    try:
        # Create test states
        username = gr.State("test_user")
        chat_id = gr.State("test_chat_id")
        chat_history = gr.State([])
        
        # Test UI creation
        search_box, search_btn, results_md = chat_history_ui(username, chat_id, chat_history)
        assert search_box is not None, "Search box component should be created"
        assert search_btn is not None, "Search button should be created"
        assert results_md is not None, "Results markdown should be created"
        
        print("test_chat_history_ui: PASSED")
    except Exception as e:
        print(f"test_chat_history_ui: FAILED - {e}")
        raise

def fuzzy_find_chats(user: str, query: str) -> str:
    """Fuzzy search through all chats for a user."""
    if not user or not query:
        return "Please login and enter a search query."
    chat_dir = os.path.join(get_chatbot_dir(), "data", "chat_sessions", user)
    if not os.path.exists(chat_dir):
        return "No chats found."
    results = []
    for fname in os.listdir(chat_dir):
        if fname.endswith(".json"):
            with open(os.path.join(chat_dir, fname), "r") as f:
                try:
                    history = json.load(f)
                    all_text = " ".join([msg.get("content", "") for msg in history])
                    if query.lower() in all_text.lower() or get_close_matches(query, [all_text], n=1, cutoff=0.6):
                        results.append(f"**{fname}**: {all_text[:100]}...")
                except Exception as e:
                    continue
    if not results:
        return "No matching chats found."
    return "\n\n".join(results)

if __name__ == "__main__":
    test_chat_history_ui()
