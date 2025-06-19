from typing import Tuple, Any, List, Dict
import gradio as gr
import backend

def chatbot_ui(username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State) -> Tuple[gr.Chatbot, gr.Textbox, gr.Button, gr.Markdown]:
    """
    Create the chatbot interface components.
    
    This function creates the chatbot UI components including:
    - Chat history display
    - Message input
    - Send button
    - Debug markdown for status messages
    
    Args:
        username_state (gr.State): State component for the current username.
        chat_history_state (gr.State): State component for the chat history.
        chat_id_state (gr.State): State component for the current chat ID.
        
    Returns:
        Tuple[gr.Chatbot, gr.Textbox, gr.Button, gr.Markdown]: Chatbot, message input, send button, and debug markdown.
    """
    chatbot = gr.Chatbot()
    chat_input = gr.Textbox(label="Type your message")
    send_btn = gr.Button("Send")
    debug_md = gr.Markdown(visible=True)

    def send_message(user: str, msg: str, history: List[List[str]], chat_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Handle sending a message and updating the chat history.
        
        Args:
            user (str): Current username.
            msg (str): The message to send.
            history (List[List[str]]): Current chat history.
            chat_id (str): Current chat ID.
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]: Updated chat history, debug message, and chat history state.
        """
        if not user:
            return gr.update(value=history), gr.update(value="Not logged in!"), gr.update(value=history)
        if not msg:
            return gr.update(value=history), gr.update(value="Please enter a message."), gr.update(value=history)
        response_dict = backend.get_chatbot_response({'user': user, 'message': msg, 'history': history, 'chat_id': chat_id})
        new_history = response_dict.get('history', history)
        # Always ensure the debug message is a string
        response_val = response_dict.get('response', '')
        if not isinstance(response_val, str):
            response_val = str(response_val)
        return gr.update(value=new_history), gr.update(value=f"Bot: {response_val}"), gr.update(value=new_history)

    send_btn.click(
        fn=send_message,
        inputs=[username_state, chat_input, chat_history_state, chat_id_state],
        outputs=[chatbot, debug_md, chat_history_state],
    )
    return chatbot, chat_input, send_btn, debug_md

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
        chatbot, chat_input, send_btn, debug_md = chatbot_ui(username, chat_history, chat_id)
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
