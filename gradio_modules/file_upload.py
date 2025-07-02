#!/usr/bin/env python3
"""File upload interface module for handling file uploads in the chatbot."""

import gradio as gr
import backend
from typing import Tuple, Any, List, Dict


def file_upload_ui(
    username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State
) -> Tuple[gr.File, gr.Button, gr.Markdown]:
    """Create the file upload interface components.

    This function creates the file upload UI components including:
    - File upload input
    - Send button
    - Debug markdown for status messages

    :param username_state: State component for the current username
    :type username_state: gr.State
    :param chat_history_state: State component for the chat history
    :type chat_history_state: gr.State
    :param chat_id_state: State component for the current chat ID
    :type chat_id_state: gr.State
    :return: File upload, send button, and debug markdown
    :rtype: Tuple[gr.File, gr.Button, gr.Markdown]
    """
    file_upload = gr.File(label="Upload a file for the chatbot")
    file_btn = gr.Button("Send File")
    file_debug_md = gr.Markdown(visible=True)

    def send_file(
        user: str, file_obj: Any, history: List[List[str]], chat_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Handle sending a file and updating the chat history.

        :param user: Current username
        :type user: str
        :param file_obj: The uploaded file object
        :type file_obj: Any
        :param history: Current chat history
        :type history: List[List[str]]
        :param chat_id: Current chat ID
        :type chat_id: str
        :return: Updated chat history, debug message, and chat history state
        :rtype: Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]
        """
        if not user:
            return (
                gr.update(value=history),
                gr.update(value="Not logged in!"),
                gr.update(value=history),
            )
        if not file_obj:
            return (
                gr.update(value=history),
                gr.update(value="No file uploaded."),
                gr.update(value=history),
            )
        # Remove chat_id from upload context, only include if present and not empty
        upload_dict = {"user": user, "file_obj": file_obj, "history": history}
        if chat_id:
            upload_dict["chat_id"] = chat_id
        response_dict = backend.handle_uploaded_file(upload_dict)
        new_history = response_dict.get("history", history)
        # Always ensure the debug message is a string
        response_val = response_dict.get("response", "")
        if not isinstance(response_val, str):
            response_val = str(response_val)
        return (
            gr.update(value=new_history),
            gr.update(value=f"Bot: {response_val}"),
            gr.update(value=new_history),
        )

    file_btn.click(
        fn=send_file,
        inputs=[username_state, file_upload, chat_history_state, chat_id_state],
        outputs=[chat_history_state, file_debug_md, chat_history_state],
    )
    return file_upload, file_btn, file_debug_md
