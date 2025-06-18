import gradio as gr
import backend
from typing import Tuple, List, Dict, Any

def audio_input_ui(username_state: gr.State, chat_history_state: gr.State, chat_id_state: gr.State) -> Tuple[gr.Audio, gr.Button, gr.Markdown, None]:
    """
    Create the audio input interface components.
    
    This function creates the audio input UI components including:
    - Audio input for microphone recording
    - Send button
    - Debug markdown for status messages
    
    Args:
        username_state (gr.State): State component for the current username.
        chat_history_state (gr.State): State component for the chat history.
        chat_id_state (gr.State): State component for the current chat ID.
        
    Returns:
        Tuple[gr.Audio, gr.Button, gr.Markdown, None]: Audio input, send button, debug markdown, and None.
    """
    audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Speak to the chatbot")
    audio_btn = gr.Button("Send Audio")
    audio_debug_md = gr.Markdown(visible=True)

    def send_audio(user: str, audio_file: str, history: List[List[str]], chat_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Handle sending an audio message and updating the chat history.
        
        Args:
            user (str): Current username.
            audio_file (str): Path to the recorded audio file.
            history (List[List[str]]): Current chat history.
            chat_id (str): Current chat ID.
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]: Updated chat history, debug message, and chat history state.
        """
        if not user:
            return gr.update(value=history), gr.update(value="Not logged in!"), gr.update(value=history)
        if not audio_file:
            return gr.update(value=history), gr.update(value="No audio file provided."), gr.update(value=history)
        response_dict = backend.audio_to_text({'user': user, 'audio_file': audio_file, 'history': history, 'chat_id': chat_id})
        new_history = response_dict.get('history', history)
        return gr.update(value=new_history), gr.update(value=f"Bot: {response_dict.get('response', '')}"), gr.update(value=new_history)

    audio_btn.click(
        fn=send_audio,
        inputs=[username_state, audio_input, chat_history_state, chat_id_state],
        outputs=[chat_history_state, audio_debug_md, chat_history_state],
    )
    return audio_input, audio_btn, audio_debug_md, None

def test_audio_input_ui():
    """
    Test the audio input UI components.
    
    This function tests that all required components are created correctly.
    """
    try:
        # Create test states
        username = gr.State("test_user")
        chat_history = gr.State([])
        chat_id = gr.State("test_chat_id")
        
        # Test UI creation
        audio_input, audio_btn, audio_debug_md, _ = audio_input_ui(username, chat_history, chat_id)
        assert audio_input is not None, "Audio input component should be created"
        assert audio_btn is not None, "Audio button should be created"
        assert audio_debug_md is not None, "Debug markdown should be created"
        
        print("test_audio_input_ui: PASSED")
    except Exception as e:
        print(f"test_audio_input_ui: FAILED - {e}")
        raise

if __name__ == "__main__":
    test_audio_input_ui()
