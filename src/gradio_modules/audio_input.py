import os
import asyncio
from backend.audio import transcribe_audio
from backend.chat import get_chatbot_response


def transcribe_and_respond_wrapper(audio_input, username_state, audio_history_state):
    """Transcribe audio and get chatbot response."""
    if not audio_input or not username_state:
        return (
            "No audio provided.",
            "",
            "Please provide audio input.",
            "",
            None,
            None,
            audio_history_state,
            "No audio interactions yet.",
        )

    username = username_state
    # Read audio file
    try:
        with open(audio_input, "rb") as f:
            audio_bytes = f.read()
        filename = os.path.basename(audio_input)
        loop = asyncio.get_event_loop()
        transcription_result = loop.run_until_complete(
            transcribe_audio(audio_bytes, filename, username)
        )
        transcript = transcription_result.get("transcript", "")
        status = "Transcription successful." if transcript else "Transcription failed."
        # Get chatbot response
        response = ""
        if transcript:
            response_gen = get_chatbot_response(username, "audio_chat", transcript)
            response = ""
            for chunk in response_gen:
                response += chunk
        # Update audio history
        history = audio_history_state if isinstance(audio_history_state, list) else []
        history.append(
            {"audio": filename, "transcript": transcript, "response": response}
        )
        history_md = f"**Audio:** {filename}\n**Transcript:** {transcript}\n**Response:** {response}"
        return transcript, response, status, "", None, None, history, history_md
    except Exception as e:
        return (
            "",
            "",
            f"Error: {e}",
            "",
            None,
            None,
            audio_history_state,
            "No audio interactions yet.",
        )


def toggle_edit_mode(transcription_output):
    """Enable edit mode for transcription."""
    return transcription_output, gr.update(visible=False), gr.update(visible=True)


def send_edited_transcription_wrapper(
    edit_transcription, username_state, audio_history_state
):
    """Send edited transcription to chatbot and update history."""
    username = username_state
    transcript = edit_transcription
    response = ""
    if transcript:
        response_gen = get_chatbot_response(username, "audio_chat", transcript)
        for chunk in response_gen:
            response += chunk
    history = audio_history_state if isinstance(audio_history_state, list) else []
    history.append({"audio": "edited", "transcript": transcript, "response": response})
    history_md = (
        f"**Audio:** edited\n**Transcript:** {transcript}\n**Response:** {response}"
    )
    status = "Edited transcription sent to chatbot."
    return response, status, history, history_md


def clear_audio_history(audio_history_state):
    """Clear audio history."""
    return [], "No audio interactions yet."


#!/usr/bin/env python3
"""
Audio Input Interface Module

This module provides the audio input interface for the NYP FYP Chatbot application.
Users can record audio or upload audio files for transcription and chatbot interaction.
"""

import gradio as gr
import logging

logger = logging.getLogger(__name__)


def audio_interface(
    username_state: gr.State, audio_history_state: gr.State, debug_info_state: gr.State
) -> gr.Blocks:
    """
    Constructs the audio input UI as a Gradio Blocks object.
    All UI logic is scoped inside this function.
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

            status_message = gr.Markdown(visible=True, elem_id="audio_status_message")
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
            gr.Markdown("### 🤖 Chatbot Response")
            response_output = gr.Markdown(
                label="Chatbot Response",
                value="Waiting for transcription...",
                elem_id="audio_chatbot_response",
            )
            gr.Markdown("### 📜 Audio History")
            history_output = gr.Markdown(
                label="History",
                value="No audio interactions yet.",
                elem_id="audio_history_output",
            )
            clear_history_btn = gr.Button(
                "🗑️ Clear Audio History", elem_id="audio_clear_history_btn"
            )
        # Wire events to components that need them
        audio_input.change(
            fn=transcribe_and_respond_wrapper,
            inputs=[audio_input, username_state, audio_history_state],
            outputs=[
                transcription_output,
                response_output,
                status_message,
                edit_transcription,
                edit_btn,
                send_edited_btn,
                audio_history_state,
                history_output,
            ],
            queue=True,
        )
        edit_btn.click(
            fn=toggle_edit_mode,
            inputs=[transcription_output],
            outputs=[edit_transcription, edit_btn, send_edited_btn],
        )
        send_edited_btn.click(
            fn=send_edited_transcription_wrapper,
            inputs=[edit_transcription, username_state, audio_history_state],
            outputs=[
                response_output,
                status_message,
                audio_history_state,
                history_output,
            ],
            queue=True,
        )
        clear_history_btn.click(
            fn=clear_audio_history,
            inputs=[audio_history_state],
            outputs=[audio_history_state, history_output],
        )
    return audio_block
