import os
import asyncio
import gradio as gr
from backend.audio import transcribe_audio
from backend.chat import get_chatbot_response
from backend.consolidated_database import get_consolidated_database


def transcribe_and_respond_wrapper(audio_input, username_state, audio_history_state):
    """Transcribe audio and get chatbot response, and increment search stat if transcript triggers a search."""
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
        response = ""
        if transcript:
            db = get_consolidated_database()
            try:
                db.increment_user_stat(username, "audio_transcriptions", 1)
            except Exception:
                pass
            response_gen = get_chatbot_response(username, "audio_chat", transcript)
            response = ""
            for chunk in response_gen:
                response += chunk
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
Only the audio_interface function is exported. All UI initialization is handled in app.py.
"""
