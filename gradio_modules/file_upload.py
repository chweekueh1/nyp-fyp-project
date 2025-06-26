#!/usr/bin/env python3
import gradio as gr
import backend
from typing import Tuple, Any, List, Dict

def file_upload_ui(username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State) -> Tuple[gr.File, gr.Button, gr.Markdown]:
    """
    Create the file upload interface components.
    
    This function creates the file upload UI components including:
    - File upload input
    - Send button
    - Debug markdown for status messages
    
    Args:
        username_state (gr.State): State component for the current username.
        chat_history_state (gr.State): State component for the chat history.
        chat_id_state (gr.State): State component for the current chat ID.
        
    Returns:
        Tuple[gr.File, gr.Button, gr.Markdown]: File upload, send button, and debug markdown.
    """
    file_upload = gr.File(label="Upload a file for the chatbot")
    file_btn = gr.Button("Send File")
    file_debug_md = gr.Markdown(visible=True)

    def send_file(user: str, file_obj: Any, history: List[List[str]], chat_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Handle sending a file and updating the chat history.
        
        Args:
            user (str): Current username.
            file_obj (Any): The uploaded file object.
            history (List[List[str]]): Current chat history.
            chat_id (str): Current chat ID.
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]: Updated chat history, debug message, and chat history state.
        """
        if not user:
            return gr.update(value=history), gr.update(value="Not logged in!"), gr.update(value=history)
        if not file_obj:
            return gr.update(value=history), gr.update(value="No file uploaded."), gr.update(value=history)
        # Remove chat_id from upload context, only include if present and not empty
        upload_dict = {'user': user, 'file_obj': file_obj, 'history': history}
        if chat_id:
            upload_dict['chat_id'] = chat_id
        response_dict = backend.handle_uploaded_file(upload_dict)
        new_history = response_dict.get('history', history)
        # Always ensure the debug message is a string
        response_val = response_dict.get('response', '')
        if not isinstance(response_val, str):
            response_val = str(response_val)
        return gr.update(value=new_history), gr.update(value=f"Bot: {response_val}"), gr.update(value=new_history)

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
