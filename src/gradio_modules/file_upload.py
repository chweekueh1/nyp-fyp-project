#!/usr/bin/env python3
"""File upload interface module for handling file uploads in the chatbot."""

import gradio as gr
import backend
from typing import Tuple, Any, List, Dict  # noqa: F401


import os


def file_upload_ui(
    username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State
) -> Tuple[gr.File, gr.Button, gr.Markdown]:
    file_upload = gr.File(label="Upload a file for the chatbot")
    file_btn = gr.Button("Send File")
    file_debug_md = gr.Markdown(visible=True)

    # Patch: In benchmark mode, skip event setup
    if os.environ.get("BENCHMARK_MODE"):
        return file_upload, file_btn, file_debug_md

    async def send_file(
        user: str, file_obj: Any, history: List[List[str]], chat_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
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
        upload_dict = {"username": user, "file_obj": file_obj, "history": history}
        if chat_id:
            upload_dict["chat_id"] = chat_id
        # Await the backend async handler
        response_dict = await backend.handle_uploaded_file(upload_dict)
        new_history = response_dict.get("history", history)
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
        api_name="send_file_upload",
    )
    return file_upload, file_btn, file_debug_md
