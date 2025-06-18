import gradio as gr
import backend

def chatbot_ui(username_state, chat_history_state, chat_id_state):
    chatbot = gr.Chatbot()
    chat_input = gr.Textbox(label="Type your message")
    send_btn = gr.Button("Send")
    debug_md = gr.Markdown(visible=True)

    def send_message(user, msg, history, chat_id):
        if not user:
            return gr.update(value=history), gr.update(value="Not logged in!"), gr.update(value=history)
        if not msg:
            return gr.update(value=history), gr.update(value="Please enter a message."), gr.update(value=history)
        response_dict = backend.get_chatbot_response({'user': user, 'message': msg, 'history': history, 'chat_id': chat_id})
        new_history = response_dict.get('history', history)
        return gr.update(value=new_history), gr.update(value=f"Bot: {response_dict.get('response', '')}"), gr.update(value=new_history)

    send_btn.click(
        fn=send_message,
        inputs=[username_state, chat_input, chat_history_state, chat_id_state],
        outputs=[chatbot, debug_md, chat_history_state],
    )
    return chatbot, chat_input, send_btn, debug_md

def test_chatbot_ui():
    """Test the chatbot UI components."""
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
