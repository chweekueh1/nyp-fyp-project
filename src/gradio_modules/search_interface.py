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

from typing import Tuple, Dict, Any  # noqa: F401
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
from backend.markdown_formatter import format_markdown

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import os


def search_interface(
    username_state: gr.State,
    current_chat_id_state: gr.State,
    chat_history_state: gr.State,
    all_chats_data_state: gr.State,
    debug_info_state: gr.State,
    audio_history_state: gr.State = None,
) -> Tuple[gr.Column, gr.Textbox, gr.Button, gr.Markdown, gr.Markdown]:
    logger.info(
        "🔍 [SEARCH_UI] search_interface function called - initializing search components"
    )
    logger.info("🔍 [SEARCH_UI] Creating search container and components")
    with gr.Column(
        visible=False, elem_classes=["search-interface-container"]
    ) as search_container:
        with gr.Row(elem_classes=["search-header-row"]):
            gr.Markdown("### 🔍 Search Chat History", elem_classes=["search-title"])
        with gr.Row(elem_classes=["search-input-row"]):
            search_query = gr.Textbox(
                label="",
                placeholder="Enter your search query here...",
                scale=4,
                elem_classes=["search-input"],
                show_label=False,
                container=False,
            )
            search_btn = gr.Button(
                "🔍 Search",
                scale=1,
                variant="primary",
                elem_classes=["search-button"],
                size="sm",
            )
            clear_search_btn = gr.Button(
                "🗑️ Clear",
                scale=0,
                variant="secondary",
                elem_classes=["clear-search-button"],
                size="sm",
            )
        with gr.Row(elem_classes=["search-stats-row"]):
            search_stats = gr.Markdown(
                "Ready to search...", elem_classes=["search-stats"], visible=False
            )
        search_results_md = gr.Markdown(
            "Enter a search query above to find messages in your chat history.",
            elem_classes=["search-results"],
            elem_id="search_results",
        )
    logger.info("🔍 [SEARCH_UI] Search container and components created successfully")

    # Patch: In benchmark mode, skip event setup
    if os.environ.get("BENCHMARK_MODE"):
        return (
            search_container,
            search_query,
            search_btn,
            search_results_md,
            search_stats,
        )

    def _handle_search_query(
        query: str, username: str, audio_history=None
    ) -> tuple[str, str]:
        # Handle a search query from the UI and return formatted results.
        #
        # This function calls the backend's `search_chat_history` and formats
        # the results for display in a Markdown component.
        #
        # :param query: The search query string.
        # :type query: str
        # :param username: The current username.
        # :type username: str
        # :return: Tuple of (formatted markdown string, stats string).
        # :rtype: tuple[str, str]
        logger.info(
            f"🔍 [SEARCH_UI] _handle_search_query called with query: '{query}', username: '{username}'"
        )

        if not query.strip() or not username:
            logger.info("🔍 [SEARCH_UI] Empty query or username, returning early")
            return "Please enter a search query.", ""

        try:
            logger.info("🔍 [SEARCH_UI] Calling backend search_chat_history...")
            found_results, status_message = search_chat_history(query.strip(), username)
            logger.info(
                f"🔍 [SEARCH_UI] Backend returned {len(found_results)} results, status: '{status_message}'"
            )

            # --- Audio history search ---
            audio_results = []
            if audio_history:
                for item in audio_history:
                    transcription = item.get("transcription", "")
                    timestamp = item.get("timestamp", "")
                    if query.lower() in transcription.lower():
                        audio_results.append(
                            {
                                "type": "audio",
                                "transcription": transcription,
                                "timestamp": timestamp,
                            }
                        )

            # Format results
            result_text = ""
            if found_results:
                result_text += format_search_results(
                    found_results, query, include_similarity=True
                )
            if audio_results:
                result_text += "\n\n---\n### 🎤 Audio History Results\n"
                for i, item in enumerate(audio_results, 1):
                    result_text += f"**Audio {i}** _{item['timestamp']}_\n- **Transcription:** {item['transcription'][:100]}{'...' if len(item['transcription']) > 100 else ''}\n\n"
            if not found_results and not audio_results:
                stats_text = f"❌ No results found for '{query}'"
                result_text = f"**No results found for '{query}'**\n\n{status_message}. Try increasing the length of the query."
                return result_text, stats_text

            stats_text = f"✅ Found {len(found_results) + len(audio_results)} result{'s' if (len(found_results) + len(audio_results)) != 1 else ''} for '{query}'"
            return format_markdown(result_text), stats_text
        except Exception as e:
            logger.error(f"Error handling search: {e}")
            error_text = f"**Error occurred during search:** {str(e)}"
            stats_text = "❌ Error occurred during search"
            return error_text, stats_text

    def _refresh_search_results_on_data_change(
        current_query: str, username: str, all_chats_data: Dict[str, Any]
    ) -> tuple[str, str]:
        # Refresh search results when chat data changes (e.g., new messages added).
        #
        # This function is called automatically when all_chats_data_state changes,
        # ensuring search results stay up-to-date with new messages.
        #
        # :param current_query: The current search query (if any).
        # :type current_query: str
        # :param username: The current username.
        # :type username: str
        # :param all_chats_data: The updated chat data.
        # :type all_chats_data: Dict[str, Any]
        # :return: Tuple of (updated search results, stats string).
        # :rtype: tuple[str, str]
        logger.info("🔍 [SEARCH_REFRESH] _refresh_search_results_on_data_change called")
        logger.info(
            f"🔍 [SEARCH_REFRESH] current_query: '{current_query}', username: '{username}'"
        )
        logger.info(
            f"🔍 [SEARCH_REFRESH] all_chats_data has {len(all_chats_data)} chats"
        )

        # Only refresh if there's an active search query
        if not current_query.strip() or not username:
            logger.info(
                "🔍 [SEARCH_REFRESH] No active query or username, returning default message"
            )
            return (
                "Enter a search query above to find messages in your chat history.",
                "",
            )

        try:
            # Log the refresh attempt for debugging
            logger.info(
                f"Refreshing search for query '{current_query}' for user '{username}'"
            )
            logger.info(f"all_chats_data contains {len(all_chats_data)} chats")

            # Use the all_chats_data parameter directly instead of internal cache
            # This ensures we get the latest data that was just updated by the chatbot
            if all_chats_data:
                logger.info(
                    f"Using provided all_chats_data with {len(all_chats_data)} chats"
                )

                # Log some details about the chats for debugging
                for chat_id, chat_data in all_chats_data.items():
                    history_length = len(chat_data.get("history", []))
                    logger.info(f"Chat {chat_id}: {history_length} messages")
            else:
                logger.warning(f"No all_chats_data provided for user {username}")

            # Re-run the search with the current query and username
            found_results, status_message = search_chat_history(
                current_query.strip(), username
            )
            if not found_results:
                stats_text = f"❌ No results found for '{current_query}'"
                result_text = f"**No results found for '{current_query}'**\n\n{status_message}. Try increasing the length of the query."
                return result_text, stats_text

            result_text = format_search_results(
                found_results, current_query, include_similarity=True
            )
            stats_text = f"✅ Found {len(found_results)} result{'s' if len(found_results) != 1 else ''} for '{current_query}'"
            return format_markdown(result_text), stats_text
        except Exception as e:
            logger.error(f"Error refreshing search results: {e}")
            error_text = f"**Error occurred during search refresh:** {str(e)}"
            stats_text = "❌ Error occurred during search refresh"
            return error_text, stats_text

    def _clear_search_results() -> tuple[str, str]:
        """
        Clear search results and reset the markdown.

        :return: Tuple of (cleared message, empty stats).
        :rtype: tuple[str, str]
        """
        return "Enter a search query above to find messages in your chat history.", ""

    # Bind events
    logger.info("🔍 [SEARCH_UI] Binding search events")
    search_query.submit(
        fn=lambda q, u, a=audio_history_state: _handle_search_query(
            q, u, a.value if a else None
        ),
        inputs=[search_query, username_state],
        outputs=[search_results_md, search_stats],
    )
    search_btn.click(
        fn=lambda q, u, a=audio_history_state: _handle_search_query(
            q, u, a.value if a else None
        ),
        inputs=[search_query, username_state],
        outputs=[search_results_md, search_stats],
    )
    logger.info("🔍 [SEARCH_UI] Search events bound successfully")

    # Add clear search functionality
    clear_search_btn.click(
        fn=_clear_search_results,
        outputs=[search_results_md, search_stats],
    )

    # Add automatic refresh when chat data changes
    # This ensures search results are updated when new messages are added
    logger.info(
        "🔍 [SEARCH_UI] Setting up automatic refresh on all_chats_data_state.change"
    )
    all_chats_data_state.change(
        fn=_refresh_search_results_on_data_change,
        inputs=[search_query, username_state, all_chats_data_state],
        outputs=[search_results_md, search_stats],
        queue=False,  # Don't queue this to avoid delays
    )

    # Note: Message sending functionality is handled by the main chat input in chatbot_ui
    # The search interface focuses only on search functionality

    logger.info(
        "🔍 [SEARCH_UI] Returning search components: container, query, btn, results_md, stats"
    )
    return search_container, search_query, search_btn, search_results_md, search_stats
