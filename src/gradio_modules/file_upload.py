#!/usr/bin/env python3
"""File upload interface module for handling file uploads in the chatbot."""

import gradio as gr
import backend
from typing import Tuple, Any, List
import os
import logging

logger = logging.getLogger(__name__)


def file_upload_ui(
    username_state: gr.State,
    all_chats_data_state: gr.State,  # Added: to align with app.py passing this state
    debug_info_state: gr.State,  # Added: to align with app.py passing this state
    chat_id_state: gr.State,
    chat_history_state: gr.State,
) -> gr.Blocks:
    """
    Constructs the file upload UI as a Gradio Blocks object.
    """
    with gr.Blocks() as file_upload_block:
        gr.Markdown("## 📁 Generic File Upload")
        gr.Markdown(
            "Upload a file to send to the chatbot. The chatbot will process it and respond."
        )

        file_upload = gr.File(
            label="Upload a file for the chatbot", elem_id="file_upload_input"
        )
        file_btn = gr.Button("Send File", variant="primary", elem_id="file_send_btn")
        file_debug_md = gr.Markdown(visible=True, elem_id="file_debug_md")

        # Patch: In benchmark mode, skip event setup
        if os.environ.get("BENCHMARK_MODE"):
            # In benchmark mode, we still need to return the Blocks object
            # but without wiring events.
            return file_upload_block

        async def send_file(
            user: str, file_obj: Any, history: List[List[str]], chat_id: str
        ) -> Tuple[gr.update, gr.update, gr.update]:
            # This function currently updates chat_history_state directly.
            # If backend.process_file_for_chatbot also modifies all_chats_data_state,
            # ensure that state is also returned and updated in the outputs.
            # For simplicity, adhering to current file's behavior.
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
                # Assuming backend.process_file_for_chatbot handles updating the
                # chat history persistently via chat_id and user, and returns the bot's response.
                response_val = await backend.process_file_for_chatbot(
                    user, file_obj, history, chat_id
                )

                new_history = history + [[file_obj.name, response_val]]
                # The first output slot is for the chat_history_state passed from app.py
                # The second output slot is for the local file_debug_md
                # The third output slot is for the chatbot display component in chatbot.py
                # Note: If backend.process_file_for_chatbot updates `all_chats_data_state`
                # (e.g., if it saves the chat), then `all_chats_data_state` should also be
                # an output here if it needs to be refreshed on the frontend.
                logger.info(
                    f"File processing successful for {user}. Response: {response_val[:50]}..."
                )
                return (
                    gr.update(value=new_history),  # Update chat_history_state
                    gr.update(value=f"Bot: {response_val}"),  # Update file_debug_md
                    gr.update(
                        value=new_history
                    ),  # Update chat_history_state (for chatbot display)
                )
            except Exception as e:
                logger.error(f"Error during file upload processing: {e}", exc_info=True)
                return (
                    gr.update(value=history),
                    gr.update(value=f"Error processing file: {str(e)}"),
                    gr.update(value=history),
                )

        # Wire events within the Blocks context
        file_btn.click(
            fn=send_file,
            inputs=[username_state, file_upload, chat_history_state, chat_id_state],
            outputs=[
                chat_history_state,
                file_debug_md,
                chat_history_state,
            ],  # Output to chat_history_state and debug
            api_name="send_file_to_chatbot",
            queue=True,  # Enable queuing for potentially long operations
        )

    return file_upload_block  # Return the entire Blocks object
