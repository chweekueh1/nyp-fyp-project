import gradio as gr
import backend

def audio_input_ui(username_state, chat_history_state, chat_id_state):
    audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Speak to the chatbot")
    audio_btn = gr.Button("Send Audio")
    audio_debug_md = gr.Markdown(visible=True)

    def send_audio(user, audio_file, history, chat_id):
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
    """Test the audio input UI components."""
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
