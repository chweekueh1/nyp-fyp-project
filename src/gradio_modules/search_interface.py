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

from typing import Tuple, Dict, Any, List
import gradio as gr
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import from parent directory
from backend.chat import search_chat_history, format_search_results  # DO NOT RENAME

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
    """
    logger.info("🔍 [SEARCH_UI] Initializing search interface...")

    with gr.Blocks() as search_block:
        # The visibility of this top-level container will be controlled by app.py
        # based on login status and tab selection.
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
                "Search results will appear here.", elem_id="search_results_md"
            )

            # --- Helper Functions for Search Interface ---

            async def _handle_search_query(
                query: str, username: str, audio_history: List[List[str]]
            ) -> Tuple[str, str]:
                logger.info(
                    f"🔍 [SEARCH_HANDLER] Search query received: '{query}' by user: {username}"
                )
                if not query:
                    return gr.update(
                        value="Please enter a search query.", visible=True
                    ), gr.update(value="", visible=True)

                try:
                    results = []
                    async for result in search_chat_history(
                        username, query, audio_history
                    ):
                        results.append(result)

                    if not results:
                        return "No matching chats found.", ""

                    formatted_results = format_search_results(results)

                    if not formatted_results:
                        return gr.update(
                            value="No matching results found.", visible=True
                        ), gr.update(value="0 results", visible=True)

                    num_results = len(results)
                    return gr.update(value=formatted_results, visible=True), gr.update(
                        value=f"{num_results} results found", visible=True
                    )
                except Exception as e:
                    logger.error(
                        f"🔍 [SEARCH_HANDLER] Error during search for '{username}': {e}",
                        exc_info=True,
                    )
                    return gr.update(
                        value=f"An error occurred during search: {str(e)}", visible=True
                    ), gr.update(value="", visible=True)

            async def _clear_search_results() -> Tuple[str, str]:
                logger.info("🔍 [SEARCH_HANDLER] Clearing search results.")
                return gr.update(
                    value="Search results will appear here.", visible=True
                ), gr.update(
                    value="Enter a query and click 'Search' or press Enter to find results.",
                    visible=True,
                )

            async def _refresh_search_results_on_data_change(
                current_query: str,
                username: str,
                all_chats_data: Dict[str, Dict[str, Any]],  # Use the gr.State directly
                audio_history: List[List[str]],  # Use the gr.State directly
            ) -> Tuple[gr.update, gr.update]:
                """Refreshes search results if the chat data or audio history changes and a query exists."""
                logger.info(
                    f"🔍 [SEARCH_HANDLER] Data change detected. Refreshing search for user: {username}"
                )
                if current_query:
                    # Re-run the search if there's an active query
                    return await _handle_search_query(
                        current_query, username, audio_history
                    )
                return gr.update(), gr.update()  # No change if no query

            # --- Event Wiring ---
            logger.info("🔍 [SEARCH_UI] Binding search events...")

            search_query.submit(
                fn=_handle_search_query,
                inputs=[
                    search_query,
                    username_state,
                    audio_history_state,
                ],  # Pass the gr.State directly
                outputs=[search_results_md, search_stats],
                queue=True,
            )
            search_btn.click(
                fn=_handle_search_query,
                inputs=[
                    search_query,
                    username_state,
                    audio_history_state,
                ],  # Pass the gr.State directly
                outputs=[search_results_md, search_stats],
                queue=True,
            )
            logger.info("🔍 [SEARCH_UI] Search events bound successfully")

            # Add clear search functionality
            clear_search_btn.click(
                fn=_clear_search_results,
                outputs=[search_results_md, search_stats],
                queue=False,
            )

            # Add automatic refresh when chat data changes
            # This ensures search results are updated when new messages are added
            logger.info(
                "🔍 [SEARCH_UI] Setting up automatic refresh on all_chats_data_state.change"
            )
            all_chats_data_state.change(
                fn=_refresh_search_results_on_data_change,
                inputs=[
                    search_query,
                    username_state,
                    all_chats_data_state,
                    audio_history_state,
                ],  # Pass the gr.State directly
                outputs=[search_results_md, search_stats],
                queue=False,  # Don't queue this to avoid delays
            )

            # Note: Message sending functionality is handled by the main chat input in chatbot_ui
            # The search interface focuses only on search functionality

            logger.info(
                "🔍 [SEARCH_UI] Returning search components: container, query, btn, results_md, stats"
            )
    return search_block  # Return the entire Blocks object
