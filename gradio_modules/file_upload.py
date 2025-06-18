import gradio as gr
import backend

def file_upload_ui(username_state, chat_history_state, chat_id_state):
    file_upload = gr.File(label="Upload a file for the chatbot")
    file_btn = gr.Button("Send File")
    file_debug_md = gr.Markdown(visible=True)

    def send_file(user, file_obj, history, chat_id):
        if not user:
            return gr.update(value=history), gr.update(value="Not logged in!"), gr.update(value=history)
        if not file_obj:
            return gr.update(value=history), gr.update(value="No file uploaded."), gr.update(value=history)
        response_dict = backend.handle_uploaded_file({'user': user, 'file_obj': file_obj, 'history': history, 'chat_id': chat_id})
        new_history = response_dict.get('history', history)
        return gr.update(value=new_history), gr.update(value=f"Bot: {response_dict.get('response', '')}"), gr.update(value=new_history)

    file_btn.click(
        fn=send_file,
        inputs=[username_state, file_upload, chat_history_state, chat_id_state],
        outputs=[chat_history_state, file_debug_md, chat_history_state],
    )
    return file_upload, file_btn, file_debug_md

def test_file_upload_ui():
    """Test the file upload UI components."""
    try:
        # Create test states
        username = gr.State("test_user")
        chat_history = gr.State([])
        chat_id = gr.State("test_chat_id")
        
        # Test UI creation
        file_upload, file_btn, file_debug_md = file_upload_ui(username, chat_history, chat_id)
        assert file_upload is not None, "File upload component should be created"
        assert file_btn is not None, "File button should be created"
        assert file_debug_md is not None, "Debug markdown should be created"
        
        print("test_file_upload_ui: PASSED")
    except Exception as e:
        print(f"test_file_upload_ui: FAILED - {e}")
        raise

if __name__ == "__main__":
    test_file_upload_ui()
