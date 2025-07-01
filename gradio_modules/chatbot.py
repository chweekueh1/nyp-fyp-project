#!/usr/bin/env python3
from typing import Tuple, Any, List, Dict
import gradio as gr
# Backend import moved to function level to avoid early ChromaDB initialization


def load_all_chats(username: str) -> Dict[str, List[List[str]]]:
    """Load all chat histories for a user.

    Args:
        username: The username to load chats for

    Returns:
        Dictionary mapping chat_id to chat history (list of [user_msg, bot_msg] pairs)
    """
    if not username:
        return {}

    # Lazy import to avoid early ChromaDB initialization
    import backend

    chat_ids = backend.list_user_chat_ids(username)
    all_histories = {}
    for cid in chat_ids:
        try:
            hist = backend.get_chat_history(cid, username)
            all_histories[cid] = [list(pair) for pair in hist] if hist else []
        except Exception as e:
            all_histories[cid] = [["[Error loading chat]", str(e)]]
    return all_histories


def handle_search(username: str, query: str) -> str:
    """Handle search query and return formatted results."""
    if not username or not query.strip():
        return "Please enter a search query."

    try:
        # Lazy import to avoid early ChromaDB initialization
        import backend

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
    username_state: gr.State,
    chat_history_state: gr.State,
    chat_id_state: gr.State,
    setup_events: bool = True,
) -> Tuple[
    gr.Dropdown,
    gr.Button,
    gr.Chatbot,
    gr.Textbox,
    gr.Button,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
    gr.Textbox,
    gr.Button,
    gr.Markdown,
]:
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
        username_state (gr.State): State component for the current username.
        chat_history_state (gr.State): State component for the chat history.
        chat_id_state (gr.State): State component for the current chat ID.
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
            new_chat_btn = gr.Button("New Chat", variant="primary", size="sm")

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
        """Load chat history for a specific chat ID."""
        if not username or not chat_id:
            return []
        try:
            # Lazy import to avoid early ChromaDB initialization
            import backend

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
        """Handle chat selection from dropdown."""
        if not username or not selected_chat_id:
            return [], ""
        history = load_chat_history(username, selected_chat_id)
        return history, selected_chat_id

    def create_new_chat(
        username: str,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, str]]]:
        """Create a new chat session."""
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

        # Get response from backend (async function)
        import asyncio

        response_dict = asyncio.run(
            backend.get_chatbot_response(
                {
                    "username": user,  # Changed from 'user' to 'username' to match backend expectation
                    "message": msg,
                    "history": tuple_history,  # Backend expects tuples format
                    "chat_id": chat_id,
                }
            )
        )

        backend_history = response_dict.get("history", tuple_history)
        response_val = response_dict.get("response", "")
        if not isinstance(response_val, str):
            response_val = str(response_val)

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

        return (
            "",
            new_history,
            "Message sent successfully",
            chat_selector_update,
            chat_id,
        )

    def initialize_chats(
        username: str,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, str]]]:
        """Initialize chat selector with user's existing chats."""
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
        """Handle chat renaming and return updated UI state."""
        if not username or not current_chat_id or not new_name.strip():
            return "Please enter a new name for the chat.", gr.update(), current_chat_id

        try:
            # Lazy import to avoid early ChromaDB initialization
            import backend

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

    # Event handlers (only set up if requested and in Blocks context)
    if setup_events:
        chat_selector.change(
            fn=on_chat_select,
            inputs=[username_state, chat_selector],
            outputs=[chatbot, chat_id_state],
        )

        new_chat_btn.click(
            fn=create_new_chat,
            inputs=[username_state],
            outputs=[chat_selector, chat_id_state, chatbot],
        )

        send_btn.click(
            fn=send_message,
            inputs=[username_state, chat_input, chatbot, chat_id_state],
            outputs=[chat_input, chatbot, debug_md, chat_selector, chat_id_state],
        )

        # Search event handlers
        search_btn.click(
            fn=handle_search,
            inputs=[username_state, search_input],
            outputs=[search_results],
        )

        search_input.submit(
            fn=handle_search,
            inputs=[username_state, search_input],
            outputs=[search_results],
        )

        # Rename event handlers
        rename_btn.click(
            fn=handle_rename,
            inputs=[username_state, chat_id_state, rename_input],
            outputs=[debug_md, chat_selector, chat_id_state],
        )

        rename_input.submit(
            fn=handle_rename,
            inputs=[username_state, chat_id_state, rename_input],
            outputs=[debug_md, chat_selector, chat_id_state],
        )

        # Initialize on username change
        username_state.change(
            fn=initialize_chats,
            inputs=[username_state],
            outputs=[chat_selector, chat_id_state, chatbot],
        )

    return (
        chat_selector,
        new_chat_btn,
        chatbot,
        chat_input,
        send_btn,
        search_input,
        search_btn,
        search_results,
        rename_input,
        rename_btn,
        debug_md,
    )
