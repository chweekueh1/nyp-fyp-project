#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import os
import logging
import tempfile
from datetime import datetime, timezone
from .config import client
from .rate_limiting import check_rate_limit
from .database import get_llm_functions
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


async def audio_to_text(ui_state: dict) -> dict:
    """
    Audio input interface: transcribes audio and gets a chatbot response.
    """
    print(f"[DEBUG] backend.audio_to_text called with ui_state: {ui_state}")
    username = ui_state.get("username")
    audio_file = ui_state.get("audio_file")
    history = ui_state.get("history", [])
    chat_id = ui_state.get("chat_id", "default")

    if not audio_file:
        return {
            "history": history,
            "response": "[No audio file provided]",
            "debug": "No audio.",
        }

    if not username:
        return {
            "history": history,
            "response": "[Error] Username required for audio processing",
            "debug": "No username provided.",
        }

    # Check rate limit for audio operations
    if not await check_rate_limit(username, "audio"):
        return {
            "history": history,
            "response": "[Error] Rate limit exceeded for audio processing",
            "debug": "Rate limit exceeded.",
        }

    try:
        # Get LLM functions lazily
        llm_funcs = get_llm_functions()
        if not llm_funcs or not llm_funcs["is_llm_ready"]():
            logging.error(
                "LLM/DB not ready in audio_to_text. Backend may not be fully initialized."
            )
            return {
                "history": history,
                "response": "[Error] AI assistant is not fully initialized. Please try again later.",
                "debug": "LLM/DB not ready.",
            }

        # Transcribe audio
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text

        # Now get chatbot response
        result = llm_funcs["get_convo_hist_answer"](transcript, chat_id)
        response = result["answer"]
        history = history + [[f"[Audio: {audio_file}]", response]]

        response_dict = {
            "history": history,
            "response": response,
            "transcript": transcript,
            "debug": "Audio transcribed and response generated.",
        }
        print(f"[DEBUG] backend.audio_to_text returning: {response_dict}")
        return response_dict

    except Exception as e:
        print(f"[ERROR] backend.audio_to_text exception: {e}")
        return {
            "history": history,
            "response": f"[Error] {e}",
            "debug": f"Exception: {e}",
        }


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe an audio file to text."""
    try:
        with open(audio_file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text
        return transcript

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return f"Error transcribing audio: {e}"


async def transcribe_audio_async(audio_file: bytes, username: str) -> dict:
    """Transcribe audio bytes asynchronously."""
    try:
        # Check rate limit
        if not await check_rate_limit(username, "audio"):
            return {
                "status": "error",
                "message": "Rate limit exceeded for audio processing",
            }

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_file)
            temp_file_path = temp_file.name

        try:
            # Transcribe audio
            with open(temp_file_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=f
                ).text

            return {
                "status": "success",
                "transcript": transcript,
                "processed_at": get_utc_timestamp(),
            }

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

    except Exception as e:
        logger.error(f"Error in transcribe_audio_async: {e}")
        return {"status": "error", "message": f"Error transcribing audio: {e}"}


async def transcribe_audio_file_async(audio_path):
    """Transcribe an audio file asynchronously."""
    try:
        if not os.path.exists(audio_path):
            return {"error": "Audio file not found"}

        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text

        return {
            "transcript": transcript,
            "file_path": audio_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in transcribe_audio_file_async: {e}")
        return {"error": str(e)}
