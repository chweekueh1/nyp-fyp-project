#!/usr/bin/env python3
"""File upload interface module for handling file uploads in the chatbot."""

import gradio as gr
from typing import Tuple, Any, List
import os
import logging
from backend.file_handling import handle_uploaded_file  # Use consolidated backend!

logger = logging.getLogger(__name__)


def file_upload_ui(
    username_state: gr.State,
    all_chats_data_state: gr.State,  # align with app.py
    debug_info_state: gr.State,
    chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> gr.Blocks:
    """
    Constructs the file upload UI as a Gradio Blocks object.
    Inner headings *REMOVED* to avoid duplication at higher levels!
    """
    logger.info("[DEBUG] Initializing File Upload Interface (file_upload_ui)")
    with gr.Blocks() as file_upload_block:
        # NO heading/Markdown here!
        file_upload = gr.File(
            label="Upload a file for the chatbot", elem_id="file_upload_input"
        )
        file_btn = gr.Button("Send File", variant="primary", elem_id="file_send_btn")
        file_debug_md = gr.Markdown(visible=True, elem_id="file_debug_md")

        if os.environ.get("BENCHMARK_MODE"):
            return file_upload_block

        async def send_file(
            user: str, file_obj: Any, history: List[List[str]], chat_id: str
        ) -> Tuple[gr.update, gr.update, gr.update]:
            if not file_obj:
                return (
                    gr.update(value=history),
                    gr.update(value="No file selected."),
                    gr.update(value=history),
                )
            if not user:
                return (
                    gr.update(value=history),
                    gr.update(value="User not logged in."),
                    gr.update(value=history),
                )

            logger.info(f"Received file for processing: {file_obj.name}")
            try:
                result = await handle_uploaded_file(
                    {"username": user, "file_obj": file_obj}
                )
                msg = result.get("message", "")
                debug_str = str(result)
                new_history = history + [[file_obj.name, msg]]
                logger.info(
                    f"File processing successful for {user}. Response: {msg[:50]}..."
                )
                return (
                    gr.update(value=new_history),
                    gr.update(value=f"Bot: {msg}\n\n{debug_str}"),
                    gr.update(value=new_history),
                )
            except Exception as e:
                logger.error(f"Error during file upload processing: {e}", exc_info=True)
                return (
                    gr.update(value=history),
                    gr.update(value=f"Error processing file: {str(e)}"),
                    gr.update(value=history),
                )

        file_btn.click(
            fn=send_file,
            inputs=[username_state, file_upload, chat_history_state, chat_id_state],
            outputs=[
                chat_history_state,
                file_debug_md,
                chat_history_state,
            ],
            api_name="send_file_to_chatbot",
            queue=True,
        )

    return file_upload_block
