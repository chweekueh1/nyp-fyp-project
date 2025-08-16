import gradio as gr
from backend.chat import get_chatbot_response


async def transcribe_and_respond_wrapper(
    audio_input, username_state, audio_history_state
):
    """Transcribe audio and get chatbot response, and increment search stat if transcript triggers a search."""
    # Ensure audio_input is a file-like object (Gradio: type='file')
    # If not, try to convert if possible (e.g., from numpy array)
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
        from backend.audio import audio_to_text

        ui_state = {"username": username}

        file_obj = None
        # If audio_input is already a file-like object, use it
        if hasattr(audio_input, "read") and hasattr(audio_input, "name"):
            file_obj = audio_input
        # If audio_input is a tuple (e.g., (sample_rate, np.ndarray)), convert to file
        elif isinstance(audio_input, tuple) and len(audio_input) == 2:
            import numpy as np
            import tempfile
            import wave

            sample_rate, data = audio_input
            # Save as temp WAV file
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1 if len(data.shape) == 1 else data.shape[1])
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(sample_rate)
                # Ensure data is int16
                if data.dtype != np.int16:
                    data = (data * 32767).astype(np.int16)
                wf.writeframes(data.tobytes())
            temp_wav.flush()
            temp_wav.seek(0)
            file_obj = temp_wav
            file_obj.name = temp_wav.name
        # Otherwise, invalid
        if not file_obj or not hasattr(file_obj, "read"):
            return (
                "",
                "",
                "Error: No valid audio file object provided.",
                "",
                None,
                None,
                audio_history_state,
                "No audio interactions yet.",
            )

        transcription_result = await audio_to_text(ui_state, file_obj)
        transcript = transcription_result.get("transcript", "")
        error_msg = transcription_result.get("error", "")
        status = (
            "Transcription successful."
            if transcript
            else error_msg or "Transcription failed."
        )
        response = ""
        history = audio_history_state if isinstance(audio_history_state, list) else []
        audio_name = getattr(file_obj, "name", "unknown")
        history.append(
            {"audio": audio_name, "transcript": transcript, "response": response}
        )
        history_md = f"**Audio:** {audio_name}\n**Transcript:** {transcript}\n**Response:** {response}"
        if hasattr(file_obj, "close"):
            try:
                file_obj.close()
            except Exception:
                pass
        return response, transcript, status, error_msg, None, None, history, history_md
    except Exception as e:
        return (
            "",
            "",
            f"Error: {e}",
            f"Error: {e}",
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
