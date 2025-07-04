#!/usr/bin/env python3
"""
Chatbot Interface Module

This module provides the main chatbot interface for the NYP FYP Chatbot application.
Users can send messages, manage chat sessions, search history, and rename chats.
"""

from typing import Tuple, Any, List, Dict

import gradio as gr
from llm.dataProcessing import YAKEMetadataTagger

from infra_utils import clear_chat_history


import backend


def load_all_chats(username: str) -> Dict[str, List[List[str]]]:
    """Load all chat histories for a user.

    Args:
        username: The username to load chats for

    Returns:
        Dictionary mapping chat_id to chat history (list of [user_msg, bot_msg] pairs)
    """
    if not username:
        return {}

    chat_ids = backend.list_user_chat_ids(username)
    all_histories = {}
    chat_names = {}
    for cid in chat_ids:
        try:
            hist = backend.get_chat_history(cid, username)
            # Try to get the chat name from metadata
            chat_name = None
            try:
                chat_name = backend.get_chat_name(cid, username)
            except Exception:
                pass
            all_histories[cid] = {
                "history": [list(pair) for pair in hist] if hist else [],
                "name": chat_name or cid,
            }
            chat_names[cid] = chat_name or cid
        except Exception as e:
            all_histories[cid] = {
                "history": [["[Error loading chat]", str(e)]],
                "name": cid,
            }
            chat_names[cid] = cid
    return all_histories


def handle_search(username: str, query: str) -> str:
    """
    Handle search query and return formatted results.

    Args:
        username: The username to search for
        query: The search query string

    Returns:
        Formatted string containing search results
    """
    if not username or not query.strip():
        return "Please enter a search query."

    try:
        # Get search results from backend
        results = backend.search_chat_history(query.strip(), username)

        if not results:
            return f"No results found for '{query}'."

        # Format results for display
        formatted_results = [f"# 🔍 Search Results for '{query}'\n"]
        formatted_results.append(
            f"Found {len(results)} chat(s) with matching content:\n"
        )

        for i, result in enumerate(results, 1):
            chat_name = result["chat_name"]
            match_count = result["match_count"]
            chat_preview = result["chat_preview"]

            formatted_results.append(f"## {i}. {chat_name}")
            formatted_results.append(
                f"**Matches:** {match_count} | **Preview:** {chat_preview}"
            )

            # Show first few matching messages
            for match in result["matching_messages"][:2]:  # Show max 2 matches per chat
                user_msg = match["user_message"]
                bot_msg = match["bot_message"]

                if match["user_match"]:
                    formatted_results.append(f"**User:** {user_msg}")
                if match["bot_match"]:
                    formatted_results.append(f"**Bot:** {bot_msg}")

            if len(result["matching_messages"]) > 2:
                remaining = len(result["matching_messages"]) - 2
                formatted_results.append(f"*... and {remaining} more matches*")

            formatted_results.append("---")

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Error searching: {str(e)}"


def chatbot_ui(
    username_state,
    chat_history_state,
    chat_id_state,
    setup_events: bool = True,
) -> Tuple:
    """
    Create the chatbot interface components with chat history loading, search, and renaming.

    This function creates the chatbot UI components including:
    - Chat selector dropdown
    - New chat button
    - Chat history display
    - Message input
    - Send button
    - Search functionality
    - Chat renaming functionality
    - Debug markdown for status messages

    Args:
        username_state (gr.State): State component for the current username (optional for testing).
        chat_history_state (gr.State): State component for the chat history (optional for testing).
        chat_id_state (gr.State): State component for the current chat ID (optional for testing).
        setup_events (bool): Whether to set up event handlers.

    Returns:
        Tuple containing all UI components:
        Chat selector, new chat button, chatbot, message input, send button,
        search input, search button, search results, rename input, rename button, and debug markdown.
    """

    # Chat management components with wider styling
    with gr.Group(elem_classes=["chat-interface-container"]):
        gr.Markdown("### 💬 Chat Management")
        with gr.Row():
            chat_selector = gr.Dropdown(choices=[], label="Select Chat")
            # new_chat_btn removed: chat creation is now automatic
            # new_chat_btn = gr.Button("New Chat", variant="primary", size="sm")

    # Chat controls
    with gr.Group():
        gr.Markdown("### 🔧 Chat Controls")

        # Chat renaming components
        with gr.Row():
            rename_input = gr.Textbox(
                label="Rename current chat",
                placeholder="Enter new name for current chat...",
            )
            rename_btn = gr.Button("🏷️ Rename", variant="secondary", size="sm")

        # Search components
        with gr.Row():
            search_input = gr.Textbox(
                label="Search chat history",
                placeholder="Search through all your chats...",
            )
            search_btn = gr.Button("🔍 Search", variant="secondary", size="sm")

        # Search results (initially visible but empty)
        search_results = gr.Markdown(value="", label="Search Results")

        # Add Clear Chat History button
        with gr.Row():
            clear_chat_btn = gr.Button(
                "🗑️ Clear Chat History", variant="stop", size="sm"
            )
            clear_chat_status = gr.Markdown(visible=False)

    # Main chat interface
    with gr.Group():
        gr.Markdown("### 💬 Chat Interface")
        chatbot = gr.Chatbot(label="Chat History", height=400, type="messages")

        with gr.Row():
            chat_input = gr.Textbox(
                label="Type your message",
                placeholder="Type your message here...",
                scale=4,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        debug_md = gr.Markdown(visible=True)

    def load_chat_history(username: str, chat_id: str) -> List[Dict[str, str]]:
        """
        Load chat history for a specific chat ID.

        Args:
            username: The username to load history for
            chat_id: The chat ID to load history for

        Returns:
            List of message dictionaries in chat format
        """
        if not username or not chat_id:
            return []

        try:
            hist = backend.get_chat_history(chat_id, username)
            # Convert tuples to messages format
            messages = []
            for user_msg, bot_msg in hist:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": bot_msg})
            return messages
        except Exception as e:
            return [{"role": "assistant", "content": f"[Error loading chat] {str(e)}"}]

    def on_chat_select(
        username: str, selected_chat_id: str
    ) -> Tuple[List[Dict[str, str]], str]:
        """
        Handle chat selection from dropdown.

        Args:
            username: The username
            selected_chat_id: The selected chat ID

        Returns:
            Tuple containing chat history and selected chat ID
        """
        if not username or not selected_chat_id:
            return [], ""
        history = load_chat_history(username, selected_chat_id)
        return history, selected_chat_id

    def create_new_chat(
        username: str,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, str]]]:
        """
        Create a new chat session.

        Args:
            username: The username to create chat for

        Returns:
            Tuple containing dropdown update, new chat ID, and empty chat history
        """
        if not username:
            return gr.update(), "", []

        # Create new chat and get its ID
        # Lazy import to avoid early ChromaDB initialization
        import backend

        new_chat_id = backend.create_and_persist_new_chat(username)

        # Get updated list of chats
        all_chats = load_all_chats(username)
        chat_ids = list(all_chats.keys())

        return gr.update(choices=chat_ids, value=new_chat_id), new_chat_id, []

    def send_message(
        user: str, msg: str, history: List[Dict[str, str]], chat_id: str
    ) -> Tuple[str, List[Dict[str, str]], str, Dict[str, Any], str]:
        """
        Handle sending a message and updating the chat history with smart naming.

        Args:
            user (str): Current username.
            msg (str): The message to send.
            history (List[Dict[str, str]]): Current chat history in messages format.
            chat_id (str): Current chat ID.

        Returns:
            Tuple[str, List[Dict[str, str]], str, Dict[str, Any], str]:
            Empty input, updated chat history, debug message, updated chat selector, new chat ID.
        """
        if not user:
            return msg, history, "Not logged in!", gr.update(), chat_id
        if not msg.strip():
            return msg, history, "Please enter a message.", gr.update(), chat_id

        # Lazy import to avoid early ChromaDB initialization
        import backend

        # Create new smart chat if none exists
        new_chat_created = False
        if not chat_id:
            chat_id = backend.create_and_persist_smart_chat(user, msg.strip())
            new_chat_created = True

        # Convert messages format to tuples for backend compatibility
        tuple_history = []
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                user_msg = history[i].get("content", "")
                bot_msg = history[i + 1].get("content", "")
                tuple_history.append([user_msg, bot_msg])

        # Extract keywords from the message using YAKE (top 20 words only, split by whitespace)
        keywords = YAKEMetadataTagger(msg)
        import collections

        all_words = []
        for kw in keywords:
            all_words.extend([w for w in kw.split() if len(w) > 2])
        word_counts = collections.Counter(all_words)
        top_20_words = [w for w, _ in word_counts.most_common(20)]
        filtered_keywords = ", ".join(top_20_words)

        # Get response from backend (async function)
        import asyncio

        # Pass filtered keywords to backend for classification
        response_dict = asyncio.run(
            backend.get_chatbot_response(
                {
                    "username": user,  # Changed from 'user' to 'username' to match backend expectation
                    "message": msg,
                    "history": tuple_history,  # Backend expects tuples format
                    "chat_id": chat_id,
                    "keywords": filtered_keywords,  # Pass keywords for classification
                }
            )
        )

        backend_history = response_dict.get("history", tuple_history)
        response_val = response_dict.get("response", "")
        # Always treat response as string for markdown rendering (avoid syntax errors)
        if not isinstance(response_val, str):
            response_val = str(response_val)

        # If the response contains a mermaid code block, ensure it is preserved and not parsed as JSON
        import re

        mermaid_match = re.search(r"```mermaid[\s\S]+?```", response_val)
        if mermaid_match:
            # Optionally, you could extract and display the diagram separately if needed
            pass  # For now, just ensure markdown rendering

        # Convert backend response back to messages format
        new_history = []
        for user_msg, bot_msg in backend_history:
            new_history.append({"role": "user", "content": user_msg})
            new_history.append({"role": "assistant", "content": bot_msg})

        # Update chat selector if new chat was created
        chat_selector_update = gr.update()
        if new_chat_created:
            try:
                all_chats = load_all_chats(user)
                chat_ids = list(all_chats.keys())
                chat_selector_update = gr.update(choices=chat_ids, value=chat_id)
            except Exception as e:
                print(f"Warning: Could not update chat selector: {e}")

        # Always return the response as markdown (for mermaid, code, etc.)
        return (
            "",
            new_history,
            response_val,
            chat_selector_update,
            chat_id,
        )

    def initialize_chats(
        username: str,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, str]]]:
        """
        Initialize chat selector with user's existing chats.

        Args:
            username: The username to initialize chats for

        Returns:
            Tuple containing dropdown update, selected chat ID, and chat history
        """
        if not username:
            return gr.update(choices=[], value=None), "", []

        all_chats = load_all_chats(username)
        chat_ids = list(all_chats.keys())
        selected = chat_ids[0] if chat_ids else None

        # Convert to messages format
        if selected:
            tuple_history = all_chats.get(selected, [])
            messages_history = []
            for user_msg, bot_msg in tuple_history:
                messages_history.append({"role": "user", "content": user_msg})
                messages_history.append({"role": "assistant", "content": bot_msg})
        else:
            messages_history = []

        return (
            gr.update(choices=chat_ids, value=selected),
            selected or "",
            messages_history,
        )

    def handle_rename(
        username: str, current_chat_id: str, new_name: str
    ) -> Tuple[str, Dict[str, Any], str]:
        """
        Handle chat renaming and return updated UI state.

        Args:
            username: The username
            current_chat_id: The current chat ID
            new_name: The new name for the chat

        Returns:
            Tuple containing status message, dropdown update, and new chat ID
        """
        if not username or not current_chat_id or not new_name.strip():
            return "Please enter a new name for the chat.", gr.update(), current_chat_id

        try:
            # Call backend rename function
            result = backend.rename_chat(current_chat_id, new_name.strip(), username)

            if result["success"]:
                new_chat_id = result["new_chat_id"]

                # Update chat selector with new list
                all_chats = load_all_chats(username)
                chat_ids = list(all_chats.keys())
                chat_selector_update = gr.update(choices=chat_ids, value=new_chat_id)

                return (
                    f"✅ Chat renamed to '{new_chat_id}'",
                    chat_selector_update,
                    new_chat_id,
                )
            else:
                return (
                    f"❌ Failed to rename chat: {result['error']}",
                    gr.update(),
                    current_chat_id,
                )

        except Exception as e:
            return f"❌ Error renaming chat: {str(e)}", gr.update(), current_chat_id

    def handle_clear_chat_history():
        try:
            clear_chat_history()
            return (gr.update(visible=True, value="✅ Chat history cleared!"),)
        except Exception as e:
            return (
                gr.update(visible=True, value=f"❌ Error clearing chat history: {e}"),
            )

    # In-memory chat list for UI (to keep dropdown and search in sync)
    chat_ids_memory = set()

    def update_chat_memory_and_dropdown(username: str):
        all_chats = load_all_chats(username)
        chat_ids = list(all_chats.keys())
        chat_ids_memory.clear()
        chat_ids_memory.update(chat_ids)
        # Build choices as list of tuples (label, value)
        choices = [(all_chats[cid]["name"], cid) for cid in chat_ids]
        selected = chat_ids[0] if chat_ids else None
        messages_history = []
        if selected:
            tuple_history = all_chats[selected]["history"]
            for user_msg, bot_msg in tuple_history:
                messages_history.append({"role": "user", "content": user_msg})
                messages_history.append({"role": "assistant", "content": bot_msg})
        return gr.update(choices=choices, value=selected), selected, messages_history

    # Patch create_new_chat to update memory
    def create_new_chat_and_update_memory(username: str):
        dropdown_update, new_chat_id, messages_history = create_new_chat(username)
        # Always update dropdown after chat creation
        dropdown_update, selected, _ = update_chat_memory_and_dropdown(username)
        return dropdown_update, new_chat_id, messages_history

    # Patch send_message to update memory if new chat is created
    def send_message_and_update_memory(user, msg, history, chat_id):
        result = send_message(user, msg, history, chat_id)
        # Always update dropdown after sending message (in case new chat is created)
        chat_selector_update, selected, _ = update_chat_memory_and_dropdown(user)
        # result: (input, new_history, debug, chat_selector_update, chat_id)
        # Replace chat_selector_update in result with the updated one
        result = list(result)
        if len(result) >= 4:
            result[3] = chat_selector_update
        return tuple(result)

    # Patch handle_rename to update memory
    def handle_rename_and_update_memory(username, current_chat_id, new_name):
        result = handle_rename(username, current_chat_id, new_name)
        # Always update dropdown after rename
        chat_selector_update, selected, _ = update_chat_memory_and_dropdown(username)
        # Replace chat_selector_update in result with the updated one
        result = list(result)
        if len(result) >= 2:
            result[1] = chat_selector_update
        return tuple(result)

    # Patch search to use in-memory chat_ids
    def handle_search_in_memory(username: str, query: str) -> str:
        if not username or not query.strip():
            return "Please enter a search query."
        all_chats = load_all_chats(username)
        chat_ids = list(chat_ids_memory)
        if not chat_ids:
            return "No chat history to search."
        filtered_chats = {cid: all_chats[cid] for cid in chat_ids if cid in all_chats}
        query_lower = query.strip().lower()
        results = []
        for cid, history in filtered_chats.items():
            chat_name = cid  # fallback if no name
            try:
                chat_name = backend.get_chat_name(cid, username)
            except Exception:
                pass
            matching_messages = []
            for pair in history:
                user_msg = pair[0] if len(pair) > 0 else ""
                bot_msg = pair[1] if len(pair) > 1 else ""
                user_match = query_lower in user_msg.lower()
                bot_match = query_lower in bot_msg.lower()
                if user_match or bot_match:
                    matching_messages.append(
                        {
                            "user_message": user_msg,
                            "bot_message": bot_msg,
                            "user_match": user_match,
                            "bot_match": bot_match,
                        }
                    )
            if matching_messages:
                results.append(
                    {
                        "chat_id": cid,
                        "chat_name": chat_name,
                        "match_count": len(matching_messages),
                        "chat_preview": matching_messages[0]["user_message"]
                        if matching_messages
                        else "",
                        "matching_messages": matching_messages,
                    }
                )
        if not results:
            return f"No results found for '{query}'."
        formatted_results = [f"# 🔍 Search Results for '{query}'\n"]
        formatted_results.append(
            f"Found {len(results)} chat(s) with matching content:\n"
        )
        for i, result in enumerate(results, 1):
            chat_name = result["chat_name"]
            match_count = result["match_count"]
            chat_preview = result["chat_preview"]
            formatted_results.append(f"## {i}. {chat_name}")
            formatted_results.append(
                f"**Matches:** {match_count} | **Preview:** {chat_preview}"
            )
            for match in result["matching_messages"][:2]:
                user_msg = match["user_message"]
                bot_msg = match["bot_message"]
                if match["user_match"]:
                    formatted_results.append(f"**User:** {user_msg}")
                if match["bot_match"]:
                    formatted_results.append(f"**Bot:** {bot_msg}")
            if len(result["matching_messages"]) > 2:
                remaining = len(result["matching_messages"]) - 2
                formatted_results.append(f"*... and {remaining} more matches*")
            formatted_results.append("---")
        return "\n".join(formatted_results)

    # Event handlers (only set up if requested and in Blocks context)
    if setup_events:
        chat_selector.change(
            fn=on_chat_select,
            inputs=[username_state, chat_selector],
            outputs=[chatbot, chat_id_state],
        )
        # new_chat_btn is removed, so no click event

        send_btn.click(
            fn=send_message_and_update_memory,
            inputs=[username_state, chat_input, chatbot, chat_id_state],
            outputs=[chat_input, chatbot, debug_md, chat_selector, chat_id_state],
        )

        # Search event handlers (use in-memory for instant UI update)
        search_btn.click(
            fn=handle_search_in_memory,
            inputs=[username_state, search_input],
            outputs=[search_results],
        )

        search_input.submit(
            fn=handle_search_in_memory,
            inputs=[username_state, search_input],
            outputs=[search_results],
        )

        # Rename event handlers (use in-memory for instant UI update)
        rename_btn.click(
            fn=handle_rename_and_update_memory,
            inputs=[username_state, chat_id_state, rename_input],
            outputs=[debug_md, chat_selector, chat_id_state],
        )

        rename_input.submit(
            fn=handle_rename_and_update_memory,
            inputs=[username_state, chat_id_state, rename_input],
            outputs=[debug_md, chat_selector, chat_id_state],
        )

        # Auto-create a new chat if none exists when user logs in or no chat is selected
        def ensure_chat_on_login(username: str):
            all_chats = load_all_chats(username)
            chat_ids = list(all_chats.keys())
            if not chat_ids:
                # No chats exist, create one
                dropdown_update, new_chat_id, messages_history = create_new_chat(
                    username
                )
                return dropdown_update, new_chat_id, messages_history
            else:
                # Chats exist, select the first one
                selected = chat_ids[0]
                tuple_history = all_chats.get(selected, [])
                messages_history = []
                for user_msg, bot_msg in tuple_history:
                    messages_history.append({"role": "user", "content": user_msg})
                    messages_history.append({"role": "assistant", "content": bot_msg})
                return (
                    gr.update(choices=chat_ids, value=selected),
                    selected,
                    messages_history,
                )

        # Patch ensure_chat_on_login to update memory
        def ensure_chat_on_login_and_update_memory(username: str):
            update_chat_memory_and_dropdown(username)
            return ensure_chat_on_login(username)

        # Replace username_state.change to use ensure_chat_on_login
        username_state.change(
            fn=ensure_chat_on_login_and_update_memory,
            inputs=[username_state],
            outputs=[chat_selector, chat_id_state, chatbot],
        )

        # Clear Chat History button
        clear_chat_btn.click(fn=handle_clear_chat_history, outputs=[clear_chat_status])

    return (
        chat_selector,
        # new_chat_btn removed from return tuple
        chatbot,
        chat_input,
        send_btn,
        search_input,
        search_btn,
        search_results,
        rename_input,
        rename_btn,
        debug_md,
        clear_chat_btn,
        clear_chat_status,
    )
