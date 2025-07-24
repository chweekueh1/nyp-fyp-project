#!/usr/bin/env python3
"""
Audio Input Interface Module

This module provides the audio input interface for the NYP FYP Chatbot application.
Users can record audio or upload audio files for transcription and chatbot interaction.
"""

from typing import List, Dict, Any, Tuple
import gradio as gr
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

from backend.audio import transcribe_audio
from backend.chat import (
    get_chatbot_response,
)  # Assuming this is the correct import for chatbot response


def audio_interface(
    username_state: gr.State, audio_history_state: gr.State, debug_info_state: gr.State
) -> gr.Blocks:
    """
    Constructs the audio input UI as a Gradio Blocks object.
    """
    with gr.Blocks() as audio_block:
        with gr.Column(elem_classes=["audio-interface-container"]):
            gr.Markdown("## 🎤 Audio Input & Transcription")
            gr.Markdown(
                "Record audio or upload an audio file for transcription and chatbot interaction."
            )
            with gr.Group():
                gr.Markdown("### 🎙️ Audio Input")
                audio_input = gr.Audio(
                    label="Record or Upload Audio",
                    type="filepath",
                    elem_id="audio_input",
                )
                gr.Markdown("""
                **Supported Audio Formats:** MP3, WAV, M4A, FLAC, OGG

                **Recording Tips:**
                - Speak clearly and at a moderate pace
                - Minimize background noise
                - Keep recordings under 30 seconds for best performance
                """)

            # Debug and Status Messages
            status_message = gr.Markdown(visible=True, elem_id="audio_status_message")

            # Transcription Display
            gr.Markdown("### 📝 Transcription")
            transcription_output = gr.Textbox(
                label="Transcribed Text",
                placeholder="Your transcribed text will appear here...",
                interactive=False,
                elem_id="audio_transcription_output",
            )
            with gr.Row():
                edit_btn = gr.Button("✏️ Edit Transcription", elem_id="audio_edit_btn")
                send_edited_btn = gr.Button(
                    "✅ Send Edited Text",
                    visible=False,
                    elem_id="audio_send_edited_btn",
                )

            edit_transcription = gr.Textbox(
                label="Edit and Send",
                placeholder="Make changes here...",
                visible=False,
                elem_id="audio_edit_transcription",
            )

            # Chatbot Response
            gr.Markdown("### 🤖 Chatbot Response")
            response_output = gr.Markdown(
                label="Chatbot Response",
                value="Waiting for transcription...",
                elem_id="audio_chatbot_response",
            )

            # Audio History Display
            gr.Markdown("### 📜 Audio History")
            history_output = gr.Markdown(
                label="History",
                value="No audio interactions yet.",
                elem_id="audio_history_output",
            )
            clear_history_btn = gr.Button(
                "🗑️ Clear Audio History", elem_id="audio_clear_history_btn"
            )

        # --- Helper Functions (defined inside to access Gradio components directly) ---

        def _format_audio_history(history: List[Dict[str, Any]]) -> str:
            """Formats the audio history for display in Markdown."""
            if not history:
                return "No audio interactions yet."
            formatted_items = []
            for i, item in enumerate(history):
                timestamp = item.get(
                    "timestamp", "Unknown time"
                )  # Assuming timestamp is already formatted or ISO string
                formatted_items.append(f"**Interaction {i + 1} ({timestamp}):**")
                formatted_items.append(
                    f"- **User (Transcription):** {item.get('transcription', 'N/A')}"
                )
                formatted_items.append(
                    f"- **Chatbot Response:** {item.get('response', 'N/A')}\n"
                )
            return "\n".join(formatted_items)

        async def transcribe_and_respond_wrapper(
            audio_filepath: str,
            username: str,
            current_audio_history: List[Dict[str, Any]],
        ) -> Tuple[
            str, str, str, gr.update, gr.update, gr.update, List[Dict[str, Any]], str
        ]:
            """
            Handles audio transcription and gets a chatbot response.
            """
            if not audio_filepath:
                yield (
                    "",
                    "",
                    "Please upload or record audio.",
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding

            if not username:
                yield (
                    "",
                    "",
                    "Please log in first!",
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding

            status_message_text = "Transcribing audio..."
            yield (
                "",
                "",
                status_message_text,
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                current_audio_history,
                _format_audio_history(current_audio_history),
            )

            try:
                # Read audio data from the file path
                with open(audio_filepath, "rb") as f:
                    audio_data_bytes = f.read()
                filename = os.path.basename(audio_filepath)

                transcription_result = await transcribe_audio(
                    audio_data_bytes, filename, username
                )
                transcription_text = transcription_result.get(
                    "transcription", "Could not transcribe."
                )

                status_message_text = "Getting chatbot response..."
                yield (
                    transcription_text,
                    "",
                    status_message_text,
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )

                # Simulate getting chatbot response (replace with actual backend call)
                # The get_chatbot_response function from backend.chat now uses streaming.
                # Create a dummy chat_history and chat_id for the call
                dummy_chat_history = []
                dummy_chat_id = (
                    "audio_chat_session"  # A temporary ID for audio-based interactions
                )

                full_response = ""
                response_generator = get_chatbot_response(
                    transcription_text, dummy_chat_history, username, dummy_chat_id
                )
                async for chunk in response_generator:
                    # Assuming chunk is (msg_input, history_output_list, debug_info, all_chats_data)
                    # and history_output_list's last element is the bot's latest message
                    if len(chunk[1]) > 0 and len(chunk[1][-1]) > 1:
                        full_response += chunk[1][-1][1]
                    yield (
                        transcription_text,
                        full_response,
                        status_message_text,
                        gr.update(visible=True),
                        gr.update(visible=True),
                        gr.update(visible=False),
                        current_audio_history,
                        _format_audio_history(current_audio_history),
                    )

                new_history_item = {
                    "timestamp": datetime.now().isoformat(),
                    "transcription": transcription_text,
                    "response": full_response,
                }
                current_audio_history.append(new_history_item)

                yield (
                    transcription_text,
                    full_response,
                    "Done!",
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )

            except Exception as e:
                logger.error(f"Error in audio processing: {e}", exc_info=True)
                yield (
                    "",
                    "",
                    f"Error: {str(e)}",
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding
            finally:
                # Clean up the temporary audio file
                if os.path.exists(audio_filepath):
                    os.remove(audio_filepath)

        def toggle_edit_mode(
            current_transcription: str,
        ) -> Tuple[gr.update, gr.update, gr.update]:
            """Toggles the visibility of the edit textbox and buttons."""
            return (
                gr.update(
                    value=current_transcription, visible=True
                ),  # Show edit box with current text
                gr.update(visible=False),  # Hide edit button
                gr.update(visible=True),  # Show send edited button
            )

        async def send_edited_transcription_wrapper(
            edited_text: str, username: str, current_audio_history: List[Dict[str, Any]]
        ) -> Tuple[str, str, List[Dict[str, Any]], str]:
            """Sends the edited transcription to the chatbot."""
            if not edited_text:
                yield (
                    "",
                    "Edited text cannot be empty.",
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding

            if not username:
                yield (
                    "",
                    "Please log in first!",
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding

            status_message_text = "Sending edited text to chatbot..."
            yield (
                "",
                status_message_text,
                current_audio_history,
                _format_audio_history(current_audio_history),
            )

            try:
                # Simulate getting chatbot response for edited text
                dummy_chat_history = []
                dummy_chat_id = "audio_chat_session"

                full_response = ""
                response_generator = get_chatbot_response(
                    edited_text, dummy_chat_history, username, dummy_chat_id
                )
                async for chunk in response_generator:
                    if len(chunk[1]) > 0 and len(chunk[1][-1]) > 1:
                        full_response += chunk[1][-1][1]
                    yield (
                        full_response,
                        status_message_text,
                        current_audio_history,
                        _format_audio_history(current_audio_history),
                    )

                new_history_item = {
                    "timestamp": datetime.now().isoformat(),
                    "transcription": edited_text,
                    "response": full_response,
                }
                current_audio_history.append(new_history_item)

                yield (
                    full_response,
                    "Done!",
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
            except Exception as e:
                logger.error(f"Error sending edited transcription: {e}", exc_info=True)
                yield (
                    "",
                    f"Error: {str(e)}",
                    current_audio_history,
                    _format_audio_history(current_audio_history),
                )
                return  # Exit the generator after yielding

        def clear_audio_history(
            current_audio_history: List[Dict[str, Any]],
        ) -> Tuple[List[Dict[str, Any]], str]:
            """Clears the audio interaction history."""
            current_audio_history.clear()
            return current_audio_history, "No audio interactions yet."

        # --- Event Wiring ---

        audio_input.change(
            fn=transcribe_and_respond_wrapper,
            inputs=[
                audio_input,
                username_state,
                audio_history_state,
            ],  # Correctly reference audio_history_state
            outputs=[
                transcription_output,
                response_output,
                status_message,
                edit_transcription,
                edit_btn,
                send_edited_btn,
                audio_history_state,  # Update the state
                history_output,  # Update the markdown display
            ],
            queue=True,
        )

        edit_btn.click(
            fn=toggle_edit_mode,
            inputs=[
                transcription_output
            ],  # Pass current transcription to pre-fill edit box
            outputs=[edit_transcription, edit_btn, send_edited_btn],
        )

        send_edited_btn.click(
            fn=send_edited_transcription_wrapper,
            inputs=[
                edit_transcription,
                username_state,
                audio_history_state,
            ],  # Correctly reference audio_history_state
            outputs=[
                response_output,
                status_message,
                audio_history_state,
                history_output,
            ],  # Correctly reference audio_history_state
            queue=True,
        )

        clear_history_btn.click(
            fn=clear_audio_history,
            inputs=[audio_history_state],  # Correctly reference audio_history_state
            outputs=[
                audio_history_state,
                history_output,
            ],  # Correctly reference audio_history_state
        )

    return audio_block
