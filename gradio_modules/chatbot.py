from typing import Tuple, Any, List, Dict
import gradio as gr
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
    for cid in chat_ids:
        try:
            hist = backend.get_chat_history(cid, username)
            all_histories[cid] = [list(pair) for pair in hist] if hist else []
        except Exception as e:
            all_histories[cid] = [["[Error loading chat]", str(e)]]
    return all_histories

def chatbot_ui(username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State, setup_events: bool = True) -> Tuple[gr.Dropdown, gr.Button, gr.Chatbot, gr.Textbox, gr.Button, gr.Markdown]:
    """
    Create the chatbot interface components with chat history loading.

    This function creates the chatbot UI components including:
    - Chat selector dropdown
    - New chat button
    - Chat history display
    - Message input
    - Send button
    - Debug markdown for status messages

    Args:
        username_state (gr.State): State component for the current username.
        chat_history_state (gr.State): State component for the chat history.
        chat_id_state (gr.State): State component for the current chat ID.

    Returns:
        Tuple[gr.Dropdown, gr.Button, gr.Chatbot, gr.Textbox, gr.Button, gr.Markdown]:
        Chat selector, new chat button, chatbot, message input, send button, and debug markdown.
    """
    # Chat management components
    chat_selector = gr.Dropdown(choices=[], label="Select Chat", scale=3)
    new_chat_btn = gr.Button("New Chat", variant="primary", scale=1)

    # Chat interface components
    chatbot = gr.Chatbot(label="Chat History", height=400)
    chat_input = gr.Textbox(label="Type your message", placeholder="Type your message here...")
    send_btn = gr.Button("Send", variant="primary")
    debug_md = gr.Markdown(visible=True)

    def load_chat_history(username: str, chat_id: str) -> List[List[str]]:
        """Load chat history for a specific chat ID."""
        if not username or not chat_id:
            return []
        try:
            hist = backend.get_chat_history(chat_id, username)
            return [list(pair) for pair in hist] if hist else []
        except Exception as e:
            return [["[Error loading chat]", str(e)]]

    def on_chat_select(username: str, selected_chat_id: str) -> Tuple[List[List[str]], str]:
        """Handle chat selection from dropdown."""
        if not username or not selected_chat_id:
            return [], ""
        history = load_chat_history(username, selected_chat_id)
        return history, selected_chat_id

    def create_new_chat(username: str) -> Tuple[Dict[str, Any], str, List[List[str]]]:
        """Create a new chat session."""
        if not username:
            return gr.update(), "", []

        # Create new chat and get its ID
        new_chat_id = backend.create_and_persist_new_chat(username)

        # Get updated list of chats
        all_chats = load_all_chats(username)
        chat_ids = list(all_chats.keys())

        return gr.update(choices=chat_ids, value=new_chat_id), new_chat_id, []

    def send_message(user: str, msg: str, history: List[List[str]], chat_id: str) -> Tuple[str, List[List[str]], str]:
        """
        Handle sending a message and updating the chat history.

        Args:
            user (str): Current username.
            msg (str): The message to send.
            history (List[List[str]]): Current chat history.
            chat_id (str): Current chat ID.

        Returns:
            Tuple[str, List[List[str]], str]: Empty input, updated chat history, debug message.
        """
        if not user:
            return msg, history, "Not logged in!"
        if not msg.strip():
            return msg, history, "Please enter a message."

        # Create new chat if none exists
        if not chat_id:
            chat_id = backend.create_and_persist_new_chat(user)

        # Get response from backend
        response_dict = backend.get_chatbot_response({
            'username': user,  # Changed from 'user' to 'username' to match backend expectation
            'message': msg,
            'history': history,
            'chat_id': chat_id
        })

        new_history = response_dict.get('history', history)
        response_val = response_dict.get('response', '')
        if not isinstance(response_val, str):
            response_val = str(response_val)

        return "", new_history, f"Message sent successfully"

    def initialize_chats(username: str) -> Tuple[Dict[str, Any], str, List[List[str]]]:
        """Initialize chat selector with user's existing chats."""
        if not username:
            return gr.update(choices=[], value=None), "", []

        all_chats = load_all_chats(username)
        chat_ids = list(all_chats.keys())
        selected = chat_ids[0] if chat_ids else None
        history = all_chats.get(selected, []) if selected else []

        return gr.update(choices=chat_ids, value=selected), selected or "", history

    # Event handlers (only set up if requested and in Blocks context)
    if setup_events:
        chat_selector.change(
            fn=on_chat_select,
            inputs=[username_state, chat_selector],
            outputs=[chatbot, chat_id_state]
        )

        new_chat_btn.click(
            fn=create_new_chat,
            inputs=[username_state],
            outputs=[chat_selector, chat_id_state, chatbot]
        )

        send_btn.click(
            fn=send_message,
            inputs=[username_state, chat_input, chatbot, chat_id_state],
            outputs=[chat_input, chatbot, debug_md]
        )

        # Initialize on username change
        username_state.change(
            fn=initialize_chats,
            inputs=[username_state],
            outputs=[chat_selector, chat_id_state, chatbot]
        )

    return chat_selector, new_chat_btn, chatbot, chat_input, send_btn, debug_md

def test_chatbot_ui():
    """
    Test the chatbot UI components.

    This function tests that all required components are created correctly.
    """
    try:
        # Create test states
        username = gr.State("test_user")
        chat_history = gr.State([])
        chat_id = gr.State("test_chat_id")

        # Test UI creation
        chat_selector, new_chat_btn, chatbot, chat_input, send_btn, debug_md = chatbot_ui(username, chat_history, chat_id)
        assert chat_selector is not None, "Chat selector should be created"
        assert new_chat_btn is not None, "New chat button should be created"
        assert chatbot is not None, "Chatbot component should be created"
        assert chat_input is not None, "Chat input component should be created"
        assert send_btn is not None, "Send button should be created"
        assert debug_md is not None, "Debug markdown should be created"

        print("test_chatbot_ui: PASSED")
    except Exception as e:
        print(f"test_chatbot_ui: FAILED - {e}")
        raise

if __name__ == "__main__":
    test_chatbot_ui()
