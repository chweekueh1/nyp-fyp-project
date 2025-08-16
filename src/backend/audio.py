#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import logging
import os
import time
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

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
    """
    import shutil
    import wave
    import subprocess

    start_time = time.monotonic()
    temp_file = None
    wav_file = None
    transcript = None
    audio_path_for_whisper = None
    duration_seconds = None
    try:
        # Write original audio to temp file
        _, ext = os.path.splitext(filename)
        temp_file = NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(audio_data_bytes)
        temp_file.close()
        input_path = temp_file.name

        # Always apply ffmpeg normalization and trim to 30s, regardless of input format
        ffmpeg_path = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
        wav_file = NamedTemporaryFile(delete=False, suffix=".wav")
        wav_file.close()
        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            input_path,
            "-af",
            "loudnorm",
            "-t",
            "30",
            wav_file.name,
        ]
        try:
            import subprocess

            subprocess.run(ffmpeg_cmd, check=True)
            audio_path_for_whisper = wav_file.name
        except Exception as ffmpeg_exc:
            logger.error(f"ffmpeg conversion failed: {ffmpeg_exc}")
            audio_path_for_whisper = input_path
            ffmpeg_cmd = [
                ffmpeg_path,
                "-y",
                "-i",
                input_path,
                "-af",
                "loudnorm",
                "-t",
                "30",
                wav_file.name,
            ]
            try:
                subprocess.run(ffmpeg_cmd, check=True)
                audio_path_for_whisper = wav_file.name
            except Exception as ffmpeg_exc:
                logger.error(f"ffmpeg conversion failed: {ffmpeg_exc}")
                audio_path_for_whisper = input_path

        # Check duration of input audio
        # Check duration of output audio (after ffmpeg conversion)
        import wave

        try:
            with wave.open(wav_file.name, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration_seconds = frames / float(rate)
        except wave.Error as e:
            logger.error(f"Failed to check audio duration: {e}")
            duration_seconds = None
        except Exception as e:
            logger.error(f"Unexpected error checking audio duration: {e}")
            duration_seconds = None

        if duration_seconds is not None and duration_seconds > 30.0:
            logger.warning(f"Audio file too long after trim: {duration_seconds:.2f}s")
            return {"error": "Audio file exceeds 30 seconds limit after trimming."}

        # --- Transcription using OpenAI Whisper ---
        from . import config

        transcript = None
        try:
            with open(audio_path_for_whisper, "rb") as audio_file:
                response = config.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                )
                transcript = response.strip() if response else ""
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            transcript = ""

        end_time = time.monotonic()
        duration_ms = int((end_time - start_time) * 1000)

        # Record audio request in the database (like other backend files)
        # Ensure audio_requests table exists before inserting
        try:
            db = _get_db()
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS audio_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    filename TEXT,
                    duration_ms INTEGER,
                    transcript TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            db.execute_query(
                "INSERT INTO audio_requests (username, filename, duration_ms, transcript, timestamp) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (username, filename, duration_ms, transcript),
            )
        except Exception as db_exc:
            logger.warning(f"Failed to record audio request: {db_exc}")

        return {"transcript": transcript, "duration_ms": duration_ms}

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return {"error": f"Error in transcribe_audio: {e}"}
    finally:
        # Ensure all temp files are deleted
        for f in [temp_file, wav_file]:
            try:
                if f is not None:
                    os.unlink(f.name)
            except Exception:
                pass


# Gradio-facing function
async def audio_to_text(ui_state: Dict[str, Any], file_obj: Any) -> Dict[str, Any]:
    """
    Gradio-facing function to handle audio transcription requests.
    Args:
        ui_state (Dict[str, Any]): The current UI state, including username.
        file_obj (Any): File-like object with .read() and .name attributes.
    Returns:
        Dict[str, Any]: A dictionary containing the transcript or an error message.
    """
    username = ui_state.get("username")
    if not username:
        return {"error": "Username not found in UI state. Cannot transcribe audio."}
    if not file_obj or not hasattr(file_obj, "read"):
        return {"error": "No audio file provided or file object is invalid."}
    try:
        # Get filename and bytes
        filename = getattr(file_obj, "name", None)
        if not filename:
            filename = "audio.wav"
        audio_data_bytes = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        if not audio_data_bytes or len(audio_data_bytes) == 0:
            logger.warning(f"Empty audio file detected: {filename}")
            return {
                "error": "Audio file is empty. Please provide a valid audio recording."
            }
        transcription_result = await transcribe_audio(
            audio_data_bytes, filename, username
        )
        return transcription_result
    except Exception as e:
        logger.error(f"Error in audio_to_text (calling transcribe_audio): {e}")
        return {"error": f"An unexpected error occurred: {e}"}
