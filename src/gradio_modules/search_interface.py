#!/usr/bin/env python3
"""
Search interface module for chat history search functionality.

This module provides a Gradio UI component specifically for searching
through a user's chat history and displaying the results.
Only the search_interface function is exported. All UI initialization is handled in app.py.
"""

import gradio as gr
import os
import difflib
from backend.consolidated_database import get_consolidated_database


def search_interface(
    username_state: gr.State,
    all_chats_data_state: gr.State,
    audio_history_state: gr.State,
) -> gr.Blocks:
    """
    Returns a Gradio Blocks UI for searching chat history and audio transcripts.
    """
    with gr.Blocks() as search_block:
        gr.Markdown("### Search Chat History")
        search_query = gr.Textbox(
            label="Search Query", placeholder="Type your search..."
        )
        search_btn = gr.Button("Search", variant="primary")
        search_results = gr.Markdown(visible=True)

        def run_search(query, username, audio_history, all_chats_data):
            query = query.strip()
            if not username or not query:
                return "❗ Please enter a search query and log in."
            db = get_consolidated_database()
            db.increment_user_stat(username, "search_queries", 1)
            all_matches = []
            debug_lines = [f"Result: '{query}' Username: '{username}'"]

            def append_debug_difflib(msg, query, session_id=None, session_name=None):
                content = msg.get("content", "")
                role = msg.get("role", "")
                score = difflib.SequenceMatcher(None, query, content).ratio()
                debug_lines.append(
                    f"[DIFFLIB] Session: {session_name or session_id} | Role: {role} | Content: '{content}' | Query: '{query}' | Score: {score:.3f}"
                )

            query_lower = query.lower()
            # Try in-memory chat data first if available
            if all_chats_data and isinstance(all_chats_data, dict):
                debug_lines.append(
                    f"\n[DEBUG][SEARCH] Using in-memory chat data with {len(all_chats_data)} sessions."
                )
                for session_id, messages in all_chats_data.items():
                    for msg in messages:
                        append_debug_difflib(msg, query, session_id=session_id)
                        content = msg.get("content", "")
                        if query_lower in content.lower():
                            all_matches.append(
                                {
                                    "session_id": session_id,
                                    "session_name": f"Session {session_id}",
                                    "role": msg.get("role", ""),
                                    "content": content,
                                    "timestamp": msg.get("timestamp", ""),
                                }
                            )
            else:
                debug_lines.append("\n[DEBUG][SEARCH] Using DB chat data.")
                sessions = db.get_chat_sessions_by_username(username)
                for session in sessions:
                    session_id = session["session_id"]
                    session_name = session.get("session_name", f"Session {session_id}")
                    messages = db.get_chat_messages(session_id)
                    for msg in messages:
                        append_debug_difflib(
                            msg, query, session_id=session_id, session_name=session_name
                        )
                        content = msg.get("content", "")
                        if query_lower in content.lower():
                            all_matches.append(
                                {
                                    "session_id": session_id,
                                    "session_name": session_name,
                                    "role": msg.get("role", ""),
                                    "content": content,
                                    "timestamp": msg.get("timestamp", ""),
                                }
                            )

            if not all_matches:
                debug_mode = bool(os.getenv("DEBUG_SEARCH_OUTPUT", ""))
                msg = "🔍 No matches found for your query."
                if debug_mode:
                    msg += "\n\n" + "\n".join(debug_lines)
                return msg
            results_md = "\n".join(
                [
                    f"#### Session: <code>{match['session_name']}</code> (ID <code>{match['session_id']}</code>)<br>"
                    f"<b>{match['role'].capitalize()}</b>: {match['content']}<br>"
                    f"<i>Time:</i> {match['timestamp']}<br>"
                    for match in all_matches
                ]
            )
            # Optionally, search audio transcript if provided
            audio_md = ""
            if audio_history and isinstance(audio_history, list):
                audio_matches = []
                for entry in audio_history:
                    transcript = entry.get("transcript", "")
                    if transcript and query_lower in transcript.lower():
                        highlight = transcript.replace(
                            query,
                            f'<mark style="background:yellow;font-weight:bold">{query}</mark>',
                        )
                        audio_matches.append(f"- **Transcript:** {highlight}")
                if audio_matches:
                    audio_md = "\n### Audio Transcript Matches\n" + "\n".join(
                        audio_matches
                    )
            return (
                results_md
                + ("\n" + audio_md if audio_md else "")
                + "\n\n"
                + "\n".join(debug_lines)
            )

        search_btn.click(
            fn=run_search,
            inputs=[
                search_query,
                username_state,
                audio_history_state,
                all_chats_data_state,
            ],
            outputs=[search_results],
            queue=True,
        )
    return search_block
