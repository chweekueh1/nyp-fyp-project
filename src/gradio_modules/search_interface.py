#!/usr/bin/env python3
"""
Search interface module for chat history search functionality.

This module provides a Gradio UI component specifically for searching
through a user's chat history and displaying the results.
Only the search_interface function is exported. All UI initialization is handled in app.py.
"""

import gradio as gr
from backend.consolidated_database import get_consolidated_database


def search_interface(
    username_state: gr.State,
    all_chats_data_state: gr.State,
    audio_history_state: gr.State,
) -> gr.Blocks:
    """
    Returns a Gradio Blocks UI for searching chat history and audio transcripts.
    """
    from backend.chat import search_chat_history

    with gr.Blocks() as search_block:
        gr.Markdown("### Search Chat History")
        search_query = gr.Textbox(
            label="Search Query", placeholder="Type your search..."
        )
        search_btn = gr.Button("Search", variant="primary")
        search_results = gr.Markdown(visible=True)

        async def run_search(query, username, audio_history, all_chats_data):
            query = query.strip()
            if not username or not query:
                return "❗ Please enter a search query and log in."
            db = get_consolidated_database()
            db.increment_user_stat(username, "search_queries", 1)
            debug_lines = [f"Result: '{query}' Username: '{username}'"]

            # Use backend chat search for chat history
            try:
                chat_results = await search_chat_history(username, query)
            except Exception as e:
                return f"Error searching chat history: {e}"

            if not chat_results:
                return "🔍 No matches found for your query."

            # For each result, show fuzzy score and debug info
            for r in chat_results:
                content = r.get("content", "")
                role = r.get("role", "")
                session_id = r.get("session_id", "")
                session_name = r.get("session_name", "")
                score = r.get("fuzzy_score", 0)
                debug_lines.append(
                    f"[DIFFLIB] Session: {session_name or session_id} | Role: {role} | Content: '{content}' | Query: '{query}' | Score: {score:.3f}"
                )

            results_md = "\n".join(
                [
                    f"#### Session: <code>{r.get('session_name', '')}</code> (ID <code>{r.get('session_id', '')}</code>)<br>"
                    f"<b>{r.get('role', '').capitalize()}</b>: {r.get('content', '')}<br>"
                    f"<i>Time:</i> {r.get('timestamp', '')}<br>"
                    for r in chat_results
                ]
            )

            # Only return chat search results and debug info
            return results_md + "\n\n" + "\n".join(debug_lines)

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
