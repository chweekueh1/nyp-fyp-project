#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import os
import logging
import os.path
import tempfile
from typing import Dict, Any, Optional
from .rate_limiting import (
    check_rate_limit,
)
from .timezone_utils import get_utc_timestamp
from .consolidated_database import (
    get_consolidated_database,  # Unified import
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize consolidated database instance
_db_instance = None


def _get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = get_consolidated_database()
    return _db_instance


def _get_username_from_id(user_id: int) -> Optional[str]:
    """Helper to retrieve username from user ID."""
    try:
        db = _get_db()
        # ConsolidatedDatabase.execute_query returns a list of sqlite3.Row objects
        result = db.execute_query("SELECT username FROM users WHERE id = ?", (user_id,))
        return result[0]["username"] if result else None
    except Exception as e:
        logger.error(f"Error fetching username for user ID {user_id}: {e}")
        return None


def _ensure_client_initialized() -> bool:
    """
    Ensure the OpenAI client is properly initialized.

    :return: True if client is initialized, False otherwise.
    """
    try:
        from . import config

        if config.client is not None:
            return True
        logger.warning("OpenAI client not available in config")
        return False
    except Exception as e:
        logger.error(f"Failed to check OpenAI client: {e}")
        return False


async def transcribe_audio(
    audio_data_bytes: bytes, filename: str, username: str
) -> Dict[str, Any]:
    """
    Transcribes audio data (bytes) to text using OpenAI's Whisper model.

    Args:
        audio_data_bytes (bytes): The raw audio data as bytes.
        filename (str): The original filename, used for logging and tracking.
        username (str): The username for rate limiting and performance tracking.

    Returns:
        Dict[str, Any]: A dictionary containing the transcript or an error message.
    """
    if not _ensure_client_initialized():
        return {"error": "OpenAI client not initialized. Cannot transcribe audio."}

    if not check_rate_limit("audio", username):
        logger.warning(f"Audio transcription rate limit hit for user: {username}")
        return {
            "error": "Rate limit exceeded for audio transcription. Please try again later."
        }

    start_time = os.monotonic()
    temp_file = None
    try:
        from . import config

        # Determine file extension from original filename or default to .mp3
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = ".mp3"

        # Create a temporary file to write the audio bytes
        # delete=False means we manually delete it in the finally block
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(audio_data_bytes)
        temp_file.close()  # Close the file handle so config.client can open it

        file_to_transcribe_path = temp_file.name
        logger.info(
            f"Transcribing audio file: {filename} (temp: {file_to_transcribe_path}) for user: {username}"
        )

        # Placeholder for duration calculation
        duration_seconds = 0.0
        # In a production system, a library like pydub or soundfile would be used
        # to get the actual duration of the audio file.

        with open(file_to_transcribe_path, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text

        end_time = os.monotonic()
        duration_ms = int((end_time - start_time) * 1000)

        # Record API call
        db = _get_db()
        db.add_api_call_record(
            username=username,
            endpoint="/audio_to_text",
            method="POST",
            duration_ms=duration_ms,
            status_code=200,
            error_message=None,
        )

        return {
            "transcript": transcript,
            "file_path": filename,  # Return original filename
            "processed_at": get_utc_timestamp(),
            "duration_seconds": duration_seconds,
            "model_used": "whisper-1",
        }

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        end_time = os.monotonic()
        duration_ms = int((end_time - start_time) * 1000)
        db = _get_db()
        db.add_api_call_record(
            username=username,
            endpoint="/audio_to_text",
            method="POST",
            duration_ms=duration_ms,
            status_code=500,
            error_message=str(e),
        )
        return {"error": f"Error transcribing audio: {e}"}
    finally:
        # Ensure the temporary file is deleted
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file.name}: {e}")


async def audio_to_text(
    ui_state: Dict[str, Any], audio_file_path: str
) -> Dict[str, Any]:
    """
    Transcribes an audio file to text using OpenAI's Whisper model.
    This is the Gradio-facing function, which now calls transcribe_audio.

    Args:
        ui_state (Dict[str, Any]): The current UI state, including username.
        audio_file_path (str): Path to the uploaded audio file.

    Returns:
        Dict[str, Any]: A dictionary containing the transcript or an error message.
    """
    username = ui_state.get("username")
    if not username:
        return {"error": "Username not found in UI state. Cannot transcribe audio."}

    if not audio_file_path or not os.path.exists(audio_file_path):
        return {"error": "No audio file provided or file does not exist."}

    try:
        with open(audio_file_path, "rb") as f:
            audio_data_bytes = f.read()

        filename = os.path.basename(audio_file_path)

        # Call the new transcribe_audio function with raw bytes
        transcription_result = await transcribe_audio(
            audio_data_bytes, filename, username
        )
        return transcription_result

    except Exception as e:
        logger.error(f"Error in audio_to_text (calling transcribe_audio): {e}")
        return {"error": f"An unexpected error occurred: {e}"}
