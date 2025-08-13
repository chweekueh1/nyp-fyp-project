#!/usr/bin/env python3
"""
Search interface module for chat history search functionality.

This module provides a Gradio UI component specifically for searching
through a user's chat history and displaying the results.
Only the search_interface function is exported. All UI initialization is handled in app.py.
"""

import gradio as gr
from backend.consolidated_database import get_consolidated_database


async def _handle_search_query(search_query, username_state, audio_history_state=None):
    """Async handler: search this user's chats and return markdown results. Also increments the user's 'search_queries' statistic."""
    username = username_state
    query = search_query.strip()
    if not username or not query:
        return "Please enter a search query and log in."
    import logging

    logger = logging.getLogger("gradio_modules.search_interface")
    try:
        db = get_consolidated_database()
        db.increment_user_stat(username, "search_queries", 1)
        all_matches = []
        import inspect

        frame = inspect.currentframe()
        all_chats_data_state = None
        if frame is not None:
            args = frame.f_back.f_locals
            all_chats_data_state = args.get("all_chats_data_state", None)
        debug_lines = [f"Result: '{query}' Username: '{username}'"]
        if all_chats_data_state and isinstance(all_chats_data_state, dict):
            debug_lines.append(
                f"\n\n[DEBUG][SEARCH] Using in-memory chat data with {len(all_chats_data_state)} sessions."
            )
            for session_id, messages in all_chats_data_state.items():
                for i, msg in enumerate(messages):
                    debug_lines.append(f"\n\”[DEBUG][SEARCH] Checking message: {msg}")
                    if query.lower() in msg.get("content", "").lower():
                        all_matches.append(
                            {
                                "session_id": session_id,
                                "session_name": session_id,
                                "role": msg.get("role", ""),
                                "content": msg.get("content", ""),
                                "timestamp": msg.get("timestamp", ""),
                                "index": i,
                            }
                        )
        else:
            debug_lines.append("\n\n[DEBUG][SEARCH] Using DB chat data.")
            sessions = db.get_chat_sessions_by_username(username)
            for session in sessions:
                session_id = session["session_id"]
                messages = db.get_chat_messages(session_id)
                for i, msg in enumerate(messages):
                    debug_lines.append(f"[DEBUG][SEARCH] Checking message: {msg}")
                    if query.lower() in msg["content"].lower():
                        all_matches.append(
                            {
                                "session_id": session_id,
                                "session_name": session["session_name"],
                                "role": msg["role"],
                                "content": msg["content"],
                                "timestamp": msg["timestamp"],
                                "index": i,
                            }
                        )
        logger.debug("\n".join(debug_lines))
        if not all_matches and not debug_lines:
            return "No matches found.\n\n" + "\n".join(debug_lines)
        results_md = "\n".join(
            [
                f"### Session `{match['session_name']}` (ID `{match['session_id']}`)\n- **{match['role']}**: {match['content']}\n- Time: {match['timestamp']}\n"
                for match in all_matches
            ]
        )
        # Optionally, search audio transcript if provided (unchanged)
        audio_md = ""
        if audio_history_state and isinstance(audio_history_state, list):
            audio_matches = []
            for entry in audio_history_state:
                transcript = entry.get("transcript", "")
                if transcript and query.lower() in transcript.lower():
                    highlight = transcript.replace(
                        query,
                        f'<mark style="background:yellow;font-weight:bold">{query}</mark>',
                    )
                    audio_matches.append(f"- **Transcript:** {highlight}")
            if audio_matches:
                audio_md = "\n### Audio Transcript Matches\n" + "\n".join(audio_matches)
        return (
            results_md
            + ("\n" + audio_md if audio_md else "")
            + "\n\n"
            + "\n".join(debug_lines)
        )
    except Exception as e:
        return f"Error during search: {e}"


def _clear_search_results():
    return ""


def search_interface(
    username_state: gr.State,
    all_chats_data_state: gr.State = None,
    audio_history_state: gr.State = None,
    debug_info_state: gr.State = None,
) -> gr.Blocks:
    """
    Constructs the search UI as a Gradio Blocks object. All UI logic is scoped inside this function.
    """
    with gr.Blocks() as search_block:
        with gr.Column(elem_classes=["search-interface-container"]):
            gr.Markdown("## 🔍 Chat History Search")
            gr.Markdown("Search through your past chat messages.")
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
            search_results_md = gr.Markdown("", elem_id="search_results_md")
        search_query.submit(
            fn=_handle_search_query,
            inputs=[search_query, username_state, audio_history_state],
            outputs=[search_results_md],
            queue=True,
        )
        search_btn.click(
            fn=_handle_search_query,
            inputs=[search_query, username_state, audio_history_state],
            outputs=[search_results_md],
            queue=True,
        )
        clear_search_btn.click(
            fn=_clear_search_results,
            outputs=[search_results_md],
            queue=False,
        )

    return search_block
