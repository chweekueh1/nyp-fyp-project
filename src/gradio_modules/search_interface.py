def _handle_search_query(search_query, username_state, audio_history_state):
    """Handle search query submission: fuzzy search across all user chats and audio history."""
    import difflib
    from backend.chat import search_chat_history

    results_md = ""
    stats_md = ""
    username = username_state
    query = search_query.strip()
    if not username or not query:
        return "Please enter a search query and log in.", "No results."

    # Search chat history using backend
    try:
        chat_results = search_chat_history(username, query)
        # Optionally, search audio history if provided
        audio_results = []
        if audio_history_state and isinstance(audio_history_state, list):
            for entry in audio_history_state:
                transcript = entry.get("transcript", "")
                if transcript:
                    score = difflib.SequenceMatcher(None, transcript, query).ratio()
                    if score > 0.3:
                        audio_results.append(
                            (transcript, score, entry.get("audio", ""))
                        )
        # Format results
        results_md = "### Chat Results\n"
        if chat_results:
            for msg in chat_results:
                results_md += f"- **Chat:** {msg.get('chat_id', 'N/A')}<br>**Message:** {msg.get('content', '')}<br>**Score:** {msg.get('score', 0):.2f}\n"
        else:
            results_md += "No chat results found.\n"
        if audio_results:
            results_md += "\n### Audio Results\n"
            for transcript, score, audio_file in audio_results:
                results_md += f"- **Audio:** {audio_file}<br>**Transcript:** {transcript}<br>**Score:** {score:.2f}\n"
        stats_md = f"Found {len(chat_results)} chat results, {len(audio_results)} audio results."
        return results_md, stats_md
    except Exception as e:
        return f"Error during search: {e}", "No results."


def _clear_search_results():
    """Clear search results display."""
    return "", "Results cleared."


def _refresh_search_results_on_data_change(
    search_query, username_state, all_chats_data_state, audio_history_state
):
    """Refresh search results when chat data changes."""
    # Just re-run the search query
    return _handle_search_query(search_query, username_state, audio_history_state)


# search_interface.py
#!/usr/bin/env python3
"""
Search interface module for chat history search functionality.

This module provides a Gradio UI component specifically for searching
through a user's chat history and displaying the results.

State Management:
- search_container: Main container that is shown/hidden based on login status
- search_results_md: Displays search results as formatted text

Integration:
- Integrated with main app.py through _enable_chat_inputs_on_login
- Connected to backend.chat.search_chat_history for fuzzy search
- Search input can also send messages to the chatbot
- Automatically refreshes search results when chat data changes

Features:
- Fuzzy search using difflib.SequenceMatcher
- Search across all user chats
- Real-time search results with similarity scores
- Clear search functionality
- Automatic visibility management based on login status
- Search input can also function as a chat input
- Automatic refresh when new messages are added
"""

import gradio as gr
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def search_interface(
    username_state: gr.State,
    all_chats_data_state: gr.State,
    audio_history_state: gr.State,
    debug_info_state: gr.State,  # ADDED: To reflect state passed from app.py
) -> gr.Blocks:
    """
    Constructs the search UI as a Gradio Blocks object.
    All UI logic is scoped inside this function.
    """
    logger.info("🔍 [SEARCH_UI] Initializing search interface...")

    with gr.Blocks() as search_block:
        with gr.Column(elem_classes=["search-interface-container"]):
            gr.Markdown("## 🔍 Chat History Search")
            gr.Markdown(
                "Search through your past chat messages and audio transcriptions."
            )

            search_query = gr.Textbox(
                label="Search Query",
                placeholder="Enter keywords to search chat history...",
                elem_id="search_query_input",
            )
            with gr.Row():
                search_btn = gr.Button(
                    "Search", variant="primary", elem_id="search_btn"
                )
                clear_search_btn = gr.Button(
                    "Clear Search", variant="secondary", elem_id="clear_search_btn"
                )
            search_stats = gr.Markdown(
                "Enter a query and click 'Search' or press Enter to find results.",
                elem_id="search_stats_md",
            )
            search_results_md = gr.Markdown(
                "",
                elem_id="search_results_md",
            )
        # Wire events to components that need them
        search_query.submit(
            fn=_handle_search_query,
            inputs=[search_query, username_state, audio_history_state],
            outputs=[search_results_md, search_stats],
            queue=True,
        )
        search_btn.click(
            fn=_handle_search_query,
            inputs=[search_query, username_state, audio_history_state],
            outputs=[search_results_md, search_stats],
            queue=True,
        )
        clear_search_btn.click(
            fn=_clear_search_results,
            outputs=[search_results_md, search_stats],
            queue=False,
        )
        all_chats_data_state.change(
            fn=_refresh_search_results_on_data_change,
            inputs=[
                search_query,
                username_state,
                all_chats_data_state,
                audio_history_state,
            ],
            outputs=[search_results_md, search_stats],
            queue=False,
        )
    return search_block
