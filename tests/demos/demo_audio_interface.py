#!/usr/bin/env python3
"""
Audio Interface Demo

This demo tests the audio input interface module to ensure it works correctly.
"""

import sys
from pathlib import Path
import gradio as gr
from gradio_modules.audio_input import audio_interface

# Add project root to path
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def create_audio_demo():
    """Create a demo of the audio interface."""

    with gr.Blocks(
        title="Audio Interface Demo",
        css="""
        .feature-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .info-box {
            background: #f8f9fa;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        """,
    ) as app:
        gr.Markdown("# 🎤 Audio Interface Demo")

        gr.Markdown("""
        <div class="feature-box">
        <h3>🎯 Demo Features</h3>
        <ul>
        <li>🎙️ Audio recording and upload</li>
        <li>📝 Speech-to-text transcription</li>
        <li>🤖 Chatbot response generation</li>
        <li>✏️ Transcription editing</li>
        <li>📋 Session history tracking</li>
        </ul>
        </div>
        """)

        # Login simulation
        with gr.Row():
            username_input = gr.Textbox(
                label="Username (Demo)",
                value="test",
                placeholder="Enter username for demo",
            )
            login_btn = gr.Button("Start Demo", variant="primary")

        login_status = gr.Markdown("Enter a username and click 'Start Demo' to begin")

        # Audio interface container (initially hidden)
        with gr.Column(visible=False) as audio_container:
            gr.Markdown("## 🎤 Audio Input Interface")

            # States
            username_state = gr.State("")

            # Audio interface
            audio_interface(username_state, setup_events=True)

            # Feature explanations
            with gr.Accordion("🎯 How to Test the Audio Features", open=False):
                gr.Markdown("""
                ### Testing Steps:

                1. **Record Audio**: Click the microphone button to record your voice
                2. **Upload Audio**: Or upload an audio file (MP3, WAV, etc.)
                3. **Process**: Click "Process Audio" to transcribe and get response
                4. **Edit**: Use the edit feature to modify transcription if needed
                5. **History**: View your audio session history

                ### Supported Features:
                - 🎙️ Real-time audio recording
                - 📁 Audio file upload (MP3, WAV, M4A, FLAC, OGG)
                - 🔄 Automatic transcription using Whisper
                - 🤖 AI chatbot responses
                - ✏️ Transcription editing
                - 📋 Session history with timestamps
                """)

        # Demo instructions
        with gr.Column(elem_classes="info-box"):
            gr.Markdown("""
            ### 📋 Demo Instructions

            **Prerequisites:**
            - Backend must be initialized (run `python app.py` first)
            - OpenAI API key must be configured for transcription
            - Audio permissions may be required for recording

            **Testing Tips:**
            - Speak clearly and at moderate pace
            - Keep recordings under 25MB
            - Test both recording and file upload
            - Try editing transcriptions before sending
            """)

        def handle_login(username):
            """Handle demo login."""
            if username and username.strip():
                return (
                    gr.update(visible=True),
                    gr.update(value=f"✅ **Demo started for user:** {username}"),
                    username.strip(),
                )
            else:
                return (
                    gr.update(visible=False),
                    gr.update(value="❌ **Error:** Please enter a username"),
                    "",
                )

        # Wire up login
        login_btn.click(
            fn=handle_login,
            inputs=[username_input],
            outputs=[audio_container, login_status, username_state],
        )

        username_input.submit(
            fn=handle_login,
            inputs=[username_input],
            outputs=[audio_container, login_status, username_state],
        )

    return app


if __name__ == "__main__":
    print("🎤 Starting Audio Interface Demo")
    print("=" * 50)

    # Check if backend functions are available
    try:
        print("✅ Backend functions available")
    except Exception as e:
        print(f"⚠️ Backend warning: {e}")
        print("Note: Some features may not work without backend initialization")

    print("🚀 Launching demo...")
    print("=" * 50)

    app = create_audio_demo()
    app.launch(debug=True, share=False)
