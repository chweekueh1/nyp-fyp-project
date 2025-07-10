#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import os
import logging
import tempfile
from datetime import datetime, timezone  # noqa: F401
from typing import Dict  # noqa: F401
from .rate_limiting import check_rate_limit
from .database import get_llm_functions
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


def _ensure_client_initialized() -> bool:
    """
    Ensure the OpenAI client is properly initialized.

    :return: True if client is initialized, False otherwise.
    """
    try:
        from . import config

        if config.client is not None:
            return True
        else:
            logger.warning("OpenAI client not available in config")
            return False
    except Exception as e:
        logger.error(f"Failed to check OpenAI client: {e}")
        return False


async def audio_to_text(ui_state: dict) -> dict:
    """
    Audio input interface: transcribes audio and gets a chatbot response.

    :param ui_state: Dictionary containing UI state with username, audio_file, history, and chat_id.
    :type ui_state: dict
    :return: Dictionary containing history, response, transcript, and debug information.
    :rtype: dict
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
        # Ensure client is initialized
        if not _ensure_client_initialized():
            return {
                "history": history,
                "response": "[Error] OpenAI client not initialized. Please ensure the backend is properly initialized and try again.",
                "debug": "OpenAI client not ready.",
            }

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
        from . import config

        with open(audio_file, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
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
        # Ensure client is initialized
        if not _ensure_client_initialized():
            return "Error transcribing audio: OpenAI client not initialized. Please ensure the backend is properly initialized and try again."

        # Check if audio file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return f"Error transcribing audio: File not found - {audio_file_path}"

        # Check if audio file is readable
        if not os.access(audio_file_path, os.R_OK):
            logger.error(f"Cannot read audio file: {audio_file_path}")
            return f"Error transcribing audio: Cannot read file - {audio_file_path}"

        # Check file size (OpenAI has limits)
        file_size = os.path.getsize(audio_file_path)
        max_size = 25 * 1024 * 1024  # 25MB limit
        if file_size > max_size:
            logger.error(f"Audio file too large: {file_size} bytes (max: {max_size})")
            return f"Error transcribing audio: File too large ({file_size / 1024 / 1024:.1f}MB, max 25MB)"

        from . import config

        with open(audio_file_path, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text
        return transcript

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return f"Error transcribing audio: {e}"


async def transcribe_audio_async(audio_file: bytes, username: str) -> dict:
    """Transcribe audio bytes asynchronously."""
    try:
        # Ensure client is initialized
        if not _ensure_client_initialized():
            return {
                "status": "error",
                "message": "OpenAI client not initialized. Please ensure the backend is properly initialized and try again.",
            }

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
            from . import config

            with open(temp_file_path, "rb") as f:
                transcript = config.client.audio.transcriptions.create(
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


async def transcribe_audio_file_async(audio_path: str) -> Dict[str, str]:
    """
    Transcribe an audio file asynchronously.

    :param audio_path: Path to the audio file to transcribe.
    :type audio_path: str
    :return: Dictionary containing transcription result or error.
    :rtype: Dict[str, str]
    """
    try:
        # Ensure client is initialized
        if not _ensure_client_initialized():
            return {
                "error": "OpenAI client not initialized. Please ensure the backend is properly initialized and try again."
            }

        if not os.path.exists(audio_path):
            return {"error": "Audio file not found"}

        from . import config

        with open(audio_path, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
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
