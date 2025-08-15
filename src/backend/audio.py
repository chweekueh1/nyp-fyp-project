#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import os
import logging
import os.path
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
    # Validate audio file type using magic number (simple check)
    import mimetypes
    import subprocess
    import shutil
    from tempfile import NamedTemporaryFile

    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type or not mime_type.startswith("audio"):
        logger.warning(f"Rejected non-audio file for user {username}: {filename}")
        return {
            "error": "Invalid file type. Only audio files are supported for transcription."
        }

    if not _ensure_client_initialized():
        return {"error": "OpenAI client not initialized. Cannot transcribe audio."}

    if not check_rate_limit("audio", username):
        logger.warning(f"Audio transcription rate limit hit for user: {username}")
        return {
            "error": "Rate limit exceeded for audio transcription. Please try again later."
        }

    if not audio_data_bytes or len(audio_data_bytes) == 0:
        logger.warning(
            f"Empty audio file received for transcription: {filename} by user: {username}"
        )
        return {"error": "Audio file is empty. Please provide a valid audio recording."}

    start_time = os.monotonic()
    temp_file = None
    norm_file = None
    wav_file = None
    try:
        from . import config

        # Write original audio to temp file
        _, ext = os.path.splitext(filename)
        temp_file = NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(audio_data_bytes)
        temp_file.close()
        input_path = temp_file.name

        # Convert to wav if not already wav
        if ext.lower() != ".wav":
            ffmpeg_path = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
            wav_file = NamedTemporaryFile(delete=False, suffix=".wav")
            wav_file.close()
            convert_cmd = [ffmpeg_path, "-y", "-i", input_path, wav_file.name]
            try:
                subprocess.run(
                    convert_cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                input_path = wav_file.name
            except Exception as e:
                logger.error(f"FFmpeg conversion failed: {e}")
                return {"error": "Failed to convert audio to WAV format."}

        # Normalize audio to at least -6 dB using ffmpeg
        norm_file = NamedTemporaryFile(delete=False, suffix=".wav")
        norm_file.close()
        ffmpeg_path = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
        norm_cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-filter:a",
            "volume=6dB",
            norm_file.name,
        ]
        try:
            subprocess.run(
                norm_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as e:
            logger.error(f"FFmpeg normalization failed: {e}")
            return {"error": "Failed to normalize audio volume."}

        file_to_transcribe_path = norm_file.name
        logger.info(
            f"Transcribing normalized audio file: {filename} (temp: {file_to_transcribe_path}) for user: {username}"
        )

        duration_seconds = 0.0  # Placeholder
        with open(file_to_transcribe_path, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text

        end_time = os.monotonic()
        duration_ms = int((end_time - start_time) * 1000)

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
            "file_path": filename,
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
        # Ensure all temp files are deleted
        for f in [temp_file, norm_file, wav_file]:
            if f and os.path.exists(f.name):
                try:
                    os.unlink(f.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {f.name}: {e}")


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

        if os.path.getsize(audio_file_path) == 0:
            logger.warning(f"Empty audio file detected at path: {audio_file_path}")
            return {
                "error": "Audio file is empty. Please provide a valid audio recording."
            }

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
