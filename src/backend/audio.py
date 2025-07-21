#!/usr/bin/env python3
"""
Audio module for the backend.
Contains audio transcription and processing functions.
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional
from .rate_limiting import check_rate_limit
from .timezone_utils import get_utc_timestamp
from .consolidated_database import (
    get_performance_database,
    get_user_database,
)  # Import performance_db

# Set up logging
logger = logging.getLogger(__name__)

# Initialize database instances
perf_db = get_performance_database()
user_db = get_user_database()


def _get_username_from_id(user_id: int) -> Optional[str]:
    """Helper to retrieve username from user ID."""
    try:
        result = user_db.fetch_one(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        )
        return result[0] if result else None
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
    chat_id = ui_state.get("chat_id")
    user_id = ui_state.get("user_id")  # Assuming user_id is passed in ui_state

    # Get username from user_id if not directly available
    if not username and user_id:
        username = _get_username_from_id(user_id)

    if not username:
        return {"error": "Username or User ID is required."}

    if not await check_rate_limit(username, "audio"):
        return {
            "history": history,
            "response": "",
            "transcript": "",
            "debug_info": "Rate limit exceeded. Please try again later.",
        }

    if not audio_file:
        return {
            "history": history,
            "response": "",
            "transcript": "",
            "debug_info": "No audio file provided.",
        }

    # Extract audio content (assuming audio_file is base64 encoded or similar if from UI)
    # For now, let's assume audio_file is a path or bytes
    if isinstance(audio_file, str) and os.path.exists(audio_file):
        audio_content = audio_file
        filename = os.path.basename(audio_file)
    elif isinstance(audio_file, bytes):
        # Handle bytes: save to temp file for transcription
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_file)
            audio_content = temp_audio.name
            filename = f"audio_{get_utc_timestamp().replace(':', '-').replace('.', '-')}.mp3"  # Generate a filename
    else:
        return {
            "history": history,
            "response": "",
            "transcript": "",
            "debug_info": "Invalid audio file format.",
        }

    try:
        transcription_result = await transcribe_audio(audio_content, filename, username)
        transcript = transcription_result.get("transcript", "")
        duration_seconds = transcription_result.get(
            "duration_seconds", 0.0
        )  # Assume transcribe_audio_async returns duration
        model_used = transcription_result.get("model_used", "whisper-1")

        if "error" in transcription_result:
            logger.error(f"Audio transcription error: {transcription_result['error']}")
            return {
                "history": history,
                "response": "",
                "transcript": "",
                "debug_info": f"Audio transcription failed: {transcription_result['error']}",
            }

        if not transcript:
            return {
                "history": history,
                "response": "",
                "transcript": "",
                "debug_info": "No transcript obtained from audio.",
            }

        # Log transcription details to the performance database
        try:
            perf_db.execute_insert(
                "INSERT INTO audio_transcriptions (username, audio_file_name, duration_seconds, transcription_length_chars, transcription_timestamp, model_used) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    username,
                    filename,
                    duration_seconds,
                    len(transcript),
                    get_utc_timestamp(),
                    model_used,
                ),
            )
            logger.info(f"Logged audio transcription for {username}: {filename}")
        except Exception as db_e:
            logger.error(
                f"Failed to log audio transcription to DB for {username}: {db_e}"
            )

        # Integrate with chat model for response
        from chat import get_chatbot_response  # Import chat module's function

        _, updated_history, final_chat_id, _, debug_info = await get_chatbot_response(
            transcript,
            chat_id,
            user_id,  # Pass user_id for chat processing
        )

        return {
            "history": updated_history,
            "response": updated_history[-1]["content"]
            if updated_history
            else "",  # Last message is the LLM response
            "transcript": transcript,
            "chat_id": final_chat_id,
            "debug_info": debug_info,
        }

    except Exception as e:
        logger.error(f"Error in audio_to_text: {e}")
        return {
            "history": history,
            "response": "",
            "transcript": "",
            "debug_info": f"An unexpected error occurred: {e}",
        }
    finally:
        # Clean up temporary file if it was created
        if (
            isinstance(audio_content, str) and "temp" in audio_content
        ):  # Simple check for temp files
            try:
                os.unlink(audio_content)
            except Exception as e:
                logger.warning(
                    f"Failed to delete temporary audio file {audio_content}: {e}"
                )


async def transcribe_audio(
    audio_data: Any, filename: str, username: str
) -> Dict[str, Any]:
    """
    Transcribe audio data (file path or bytes) asynchronously.
    This function will now be responsible for getting the duration as well.
    :param audio_data: Path to the audio file or raw audio bytes.
    :type audio_data: Any
    :param filename: The filename to transcribe.
    :type filename: str
    :param username: The username to target.
    :type username: str
    :return: Dictionary containing transcription result, duration, model_used or error.
    :rtype: Dict[str, Any]
    """
    from . import config

    temp_file_path = None
    try:
        # Ensure client is initialized
        if not _ensure_client_initialized():
            return {
                "error": "OpenAI client not initialized. Please ensure the backend is properly initialized and try again."
            }

        file_to_transcribe_path = audio_data
        if isinstance(audio_data, bytes):
            # Save bytes to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                temp_audio.write(audio_data)
                temp_file_path = temp_audio.name
                file_to_transcribe_path = temp_file_path
        elif not os.path.exists(audio_data):
            return {"error": "Audio file not found"}

        # Get audio duration
        duration_seconds = 0.0
        try:
            # You might need a more robust audio metadata library like pydub, mutagen, or sox
            # This is a placeholder for getting duration
            # Example using a hypothetical `audio_metadata` module:
            # audio_info = audio_metadata.load(file_to_transcribe_path)
            # duration_seconds = audio_info.duration
            pass  # Replace with actual audio duration extraction
        except Exception as e:
            logger.warning(f"Could not get audio duration for {filename}: {e}")
            duration_seconds = 0.0  # Default to 0 if duration extraction fails

        with open(file_to_transcribe_path, "rb") as f:
            transcript = config.client.audio.transcriptions.create(
                model="whisper-1", file=f
            ).text

        return {
            "transcript": transcript,
            "file_path": file_to_transcribe_path,
            "processed_at": get_utc_timestamp(),
            "duration_seconds": duration_seconds,
            "model_used": "whisper-1",  # Hardcoded for now, can be dynamic
        }

    except Exception as e:
        logger.error(f"Error in transcribe_audio_async: {e}")
        return {"error": f"Error transcribing audio: {e}"}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
