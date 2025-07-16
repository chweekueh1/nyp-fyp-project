#!/usr/bin/env python3
"""
Audio Input Interface Module

This module provides the audio input interface for the NYP FYP Chatbot application.
Users can record audio or upload audio files for transcription and chatbot interaction.
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple, Optional  # noqa: F401

import gradio as gr

from backend import transcribe_audio
from backend.chat import get_chatbot_response

from infra_utils import setup_logging

logger = setup_logging()


import os


def audio_interface(username_state: str, setup_events: bool = True) -> Tuple:
    with gr.Column(elem_classes=["audio-interface-container"]):
        gr.Markdown("## 🎤 Audio Input & Transcription")
        gr.Markdown(
            "Record audio or upload an audio file for transcription and chatbot interaction."
        )
        with gr.Group():
            gr.Markdown("### 🎙️ Audio Input")
            audio_input = gr.Audio(
                label="Record or Upload Audio", type="filepath", elem_id="audio_input"
            )
            gr.Markdown("""
            **Supported Audio Formats:** MP3, WAV, M4A, FLAC, OGG

            **Recording Tips:**
            - Speak clearly and at a moderate pace
            - Minimize background noise
            - Keep recordings under 25MB for best results
            """)
            process_audio_btn = gr.Button(
                "🎯 Process Audio", variant="primary", size="lg"
            )
        with gr.Group():
            gr.Markdown("### 📝 Transcription & Response")
            status_message = gr.Markdown(visible=False)
            transcription_output = gr.Textbox(
                label="📄 Audio Transcription",
                placeholder="Audio transcription will appear here...",
                interactive=False,
                lines=4,
                max_lines=20,
            )
            with gr.Row():
                edit_transcription = gr.Textbox(
                    label="✏️ Edit Transcription (Optional)",
                    placeholder="You can edit the transcription here before sending to chatbot...",
                    lines=2,
                    max_lines=20,
                    visible=False,
                )
                edit_btn = gr.Button("✏️ Edit", size="sm", visible=False)
                send_edited_btn = gr.Button(
                    "📤 Send Edited", variant="primary", size="sm", visible=False
                )
            response_output = gr.Textbox(
                label="🤖 Chatbot Response",
                placeholder="Chatbot response will appear here...",
                interactive=False,
                lines=6,
                max_lines=30,
            )
        with gr.Group():
            gr.Markdown("### 📋 Audio Session History")
            history_output = gr.Markdown("No audio processed yet in this session.")
            clear_history_btn = gr.Button("🗑️ Clear History", variant="secondary")
    audio_history = gr.State([])

    # Patch: In benchmark mode, skip event setup
    if os.environ.get("BENCHMARK_MODE") or not setup_events:
        return (
            audio_input,
            process_audio_btn,
            transcription_output,
            response_output,
            status_message,
            edit_transcription,
            edit_btn,
            send_edited_btn,
            history_output,
            clear_history_btn,
            audio_history,
        )

    def process_audio_file_wrapper(
        audio_file: Optional[str],
        username: Optional[str],
        history: List[Dict[str, Any]],
    ) -> Tuple[
        str, str, gr.update, gr.update, gr.update, gr.update, List[Dict[str, Any]], str
    ]:
        """Wrapper function to handle async process_audio_file."""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new event loop if none exists or is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute the async function
        return loop.run_until_complete(
            process_audio_file_async(audio_file, username, history)
        )

    async def process_audio_file_async(
        audio_file: Optional[str],
        username: Optional[str],
        history: List[Dict[str, Any]],
    ) -> Tuple[
        str,
        str,
        gr.update,
        gr.update,
        gr.update,
        gr.update,
        List[Dict[str, Any]],
        str,
    ]:
        # Process audio file and get chatbot response.
        #
        # :param audio_file: Path to the audio file to process
        # :type audio_file: Optional[str]
        # :param username: Current username for authentication
        # :type username: Optional[str]
        # :param history: List of previous audio processing history
        # :type history: List[Dict[str, Any]]
        # :return: Tuple containing transcription, response, status update, edit update, edit button update, send edited update, updated history, and formatted history.
        # :rtype: Tuple[str, str, gr.update, gr.update, gr.update, gr.update, List[Dict[str, Any]], str]
        if not audio_file:
            return (
                "",
                "",
                gr.update(
                    visible=True,
                    value="❌ **Error:** Please record or upload an audio file.",
                ),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                history,
                format_history(history),
            )

        if not username:
            return (
                "",
                "",
                gr.update(visible=True, value="❌ **Error:** Please log in first."),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                history,
                format_history(history),
            )

        try:
            # Step 1: Transcribe audio using the simple transcribe_audio function
            transcription = transcribe_audio(audio_file)

            # Check if transcription failed
            if transcription.startswith("Error"):
                return (
                    transcription,
                    "",
                    gr.update(
                        visible=True,
                        value="❌ **Transcription failed.** Please try again with a clearer audio file.",
                    ),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    history,
                    format_history(history),
                )

            # Step 2: Get chatbot response using get_chatbot_response
            # Use "new_chat_id" to let the backend create a proper chat
            chat_id = "new_chat_id"

            # Get chatbot response
            response_result = await get_chatbot_response(
                transcription, [], username, chat_id
            )

            # Extract response from result
            # get_chatbot_response returns (empty_message, updated_history, chat_id, all_chats_data, debug_info)
            if len(response_result) >= 2:
                updated_history = response_result[1]
                if updated_history and len(updated_history) > 0:
                    # Get the last bot response from the updated history
                    response = (
                        updated_history[-1][1]
                        if len(updated_history[-1]) > 1
                        else "No response received"
                    )
                else:
                    response = "No response received"
            else:
                response = "Error: Invalid response format"

            # Add to history
            history.append(
                {
                    "transcription": transcription,
                    "response": response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            # Success
            return (
                transcription,
                response,
                gr.update(
                    visible=True,
                    value="✅ **Audio processed successfully!** Transcription and response ready.",
                ),
                gr.update(visible=True, value=transcription),
                gr.update(visible=True),
                gr.update(visible=True),
                history,
                format_history(history),
            )

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return (
                "",
                "",
                gr.update(
                    visible=True, value=f"❌ **Error processing audio:** {str(e)}"
                ),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                history,
                format_history(history),
            )

    def send_edited_transcription_wrapper(
        edited_text: str, username: Optional[str], history: List[Dict[str, Any]]
    ) -> Tuple[str, gr.update, List[Dict[str, Any]], str]:
        """Wrapper function to handle async send_edited_transcription."""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new event loop if none exists or is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute the async function
        return loop.run_until_complete(
            send_edited_transcription_async(edited_text, username, history)
        )

    async def send_edited_transcription_async(
        edited_text: str, username: Optional[str], history: List[Dict[str, Any]]
    ) -> Tuple[str, gr.update, List[Dict[str, Any]], str]:
        # Send edited transcription to chatbot.
        #
        # :param edited_text: The edited transcription text
        # :type edited_text: str
        # :param username: Current username for authentication
        # :type username: Optional[str]
        # :param history: List of previous audio processing history
        # :type history: List[Dict[str, Any]]
        # :return: Tuple containing:
        #          - response: Chatbot response
        #          - status_update: Status message update
        #          - updated_history: Updated history list
        #          - formatted_history: Formatted history for display
        # :rtype: Tuple[str, gr.update, List[Dict[str, Any]], str]
        if not edited_text or not edited_text.strip():
            return (
                "",
                gr.update(
                    visible=True, value="❌ **Error:** Please enter some text to send."
                ),
                history,
                format_history(history),
            )

        if not username:
            return (
                "",
                gr.update(visible=True, value="❌ **Error:** Please log in first."),
                history,
                format_history(history),
            )

        try:
            # Use "new_chat_id" to let the backend create a proper chat
            chat_id = "new_chat_id"

            # Get chatbot response
            response_result = await get_chatbot_response(
                edited_text.strip(), [], username, chat_id
            )

            # Extract response from result
            # get_chatbot_response returns (empty_message, updated_history, chat_id, all_chats_data, debug_info)
            if len(response_result) >= 2:
                updated_history = response_result[1]
                if updated_history and len(updated_history) > 0:
                    # Get the last bot response from the updated history
                    response = (
                        updated_history[-1][1]
                        if len(updated_history[-1]) > 1
                        else "No response received"
                    )
                else:
                    response = "No response received"
            else:
                response = "Error: Invalid response format"

            # Add to history
            history.append(
                {
                    "transcription": f"{edited_text.strip()} (edited)",
                    "response": response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            return (
                response,
                gr.update(
                    visible=True, value="✅ **Edited message sent successfully!**"
                ),
                history,
                format_history(history),
            )

        except Exception as e:
            logger.error(f"Error sending edited transcription: {e}")
            return (
                "",
                gr.update(visible=True, value=f"❌ **Error:** {str(e)}"),
                history,
                format_history(history),
            )

    def toggle_edit_mode() -> Tuple[gr.update, gr.update, gr.update]:
        # Toggle edit mode for transcription.
        #
        # :return: Tuple containing visibility updates for edit components
        # :rtype: Tuple[gr.update, gr.update, gr.update]
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def clear_audio_history() -> Tuple[List[Dict[str, Any]], str]:
        # Clear the audio session history.
        #
        # :return: Tuple containing empty history list and success message
        # :rtype: Tuple[List[Dict[str, Any]], str]
        return [], "Audio history cleared."

    def format_history(history: List[Dict[str, Any]]) -> str:
        """
        Format history for display.

        :param history: List of audio processing history items
        :type history: List[Dict[str, Any]]
        :return: Formatted string representation of history
        :rtype: str
        """
        if not history:
            return "No audio processed yet in this session."

        formatted = []
        for i, item in enumerate(history[-5:], 1):  # Show last 5 items
            transcription = item.get("transcription", "")
            response = item.get("response", "")
            timestamp = item.get("timestamp", "Unknown time")

            formatted.append(f"""
**Session {i}** _{timestamp}_
- **Input:** {transcription[:100]}{"..." if len(transcription) > 100 else ""}
- **Response:** {response[:100]}{"..." if len(response) > 100 else ""}
""")

        return "\n".join(formatted)

    # Event handlers
    process_audio_btn.click(
        fn=process_audio_file_wrapper,
        inputs=[audio_input, username_state, audio_history],
        outputs=[
            transcription_output,
            response_output,
            status_message,
            edit_transcription,
            edit_btn,
            send_edited_btn,
            audio_history,
            history_output,
        ],
    )

    edit_btn.click(
        fn=toggle_edit_mode, outputs=[edit_transcription, edit_btn, send_edited_btn]
    )

    send_edited_btn.click(
        fn=send_edited_transcription_wrapper,
        inputs=[edit_transcription, username_state, audio_history],
        outputs=[response_output, status_message, audio_history, history_output],
    )

    clear_history_btn.click(
        fn=clear_audio_history, outputs=[audio_history, history_output]
    )

    return (
        audio_input,
        process_audio_btn,
        transcription_output,
        response_output,
        status_message,
        edit_transcription,
        edit_btn,
        send_edited_btn,
        history_output,
        clear_history_btn,
        audio_history,
    )
