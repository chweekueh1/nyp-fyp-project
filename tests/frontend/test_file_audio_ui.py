import gradio as gr
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backend functions directly
from backend import upload_file, data_classification, transcribe_audio

def test_file_upload_interface():
    """Test the file upload interface."""
    async def handle_file_upload(file, username):
        if not file:
            return "❌ Please select a file to upload"
        file_dict = {"name": file.name, "file": file.read(), "username": username}
        try:
            result = await upload_file(file_dict)
            if result.get('code') == '200':
                return f"✅ File uploaded successfully: {file.name}"
            else:
                return f"❌ File upload failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"❌ File upload error: {str(e)}"

    async def handle_file_classification(file):
        if not file:
            return "❌ Please select a file to classify"
        file_dict = {"name": file.name, "file": file.read(), "type": file.type or "application/octet-stream"}
        try:
            result = await data_classification(file_dict)
            if result.get('code') == '200':
                return f"✅ File classified successfully: {result.get('message', 'Classification complete')}"
            else:
                return f"❌ File classification failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"❌ File classification error: {str(e)}"

    with gr.Blocks(title="File Upload Interface Test") as app:
        # Initialize states
        logged_in_state = gr.State(True)  # Start logged in for testing
        username_state = gr.State("test")
        chat_history_state = gr.State([])
        chat_id_state = gr.State("test_chat_id")
        
        # Header
        gr.Markdown("# File Upload Interface Test")
        
        # File inputs
        file_input = gr.File(label="Upload File", file_types=["txt", "pdf", "docx", "pptx", "xlsx"])
        upload_button = gr.Button("Upload File", variant="primary")
        classify_button = gr.Button("Classify File", variant="secondary")
        
        # Output
        upload_result = gr.Markdown("File upload results will appear here...")
        
        # Event handlers
        upload_button.click(
            fn=handle_file_upload,
            inputs=[file_input, username_state],
            outputs=[upload_result],
            api_name="upload_file"
        )
        
        classify_button.click(
            fn=handle_file_classification,
            inputs=[file_input],
            outputs=[upload_result],
            api_name="classify_file"
        )
        
        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **File Upload:** Upload a file using the file input
        2. **Upload File:** Click the Upload File button
        3. **Classify File:** Click the Classify File button
        4. **File Processing:** Check that the file is processed by backend
        
        **Expected Behavior:**
        - File upload should work
        - Upload File button should be responsive
        - Classify File button should be responsive
        - Backend functions should be called directly
        - File processing results should be displayed
        """)
    
    return app

def test_audio_input_interface():
    """Test the audio input interface."""
    async def handle_audio_transcription(audio, username):
        if not audio:
            return "❌ Please record or upload audio"
        try:
            result = await transcribe_audio(audio, username)
            if result.get('code') == '200':
                return f"✅ Audio transcribed successfully: {result.get('message', 'Transcription complete')}"
            else:
                return f"❌ Audio transcription failed: {result.get('message', 'Unknown error')}"
        except Exception as e:
            return f"❌ Audio transcription error: {str(e)}"
    with gr.Blocks(title="Audio Input Interface Test") as app:
        # Initialize states
        logged_in_state = gr.State(True)
        username_state = gr.State("test")
        chat_history_state = gr.State([])
        chat_id_state = gr.State("test_chat_id")
        
        # Header
        gr.Markdown("# Audio Input Interface Test")
        
        # Audio inputs
        audio_input = gr.Audio(label="Record Audio", type="filepath")
        transcribe_button = gr.Button("Transcribe Audio", variant="primary")
        
        # Output
        audio_result = gr.Markdown("Audio transcription results will appear here...")
        
        # Event handler
        transcribe_button.click(
            fn=handle_audio_transcription,
            inputs=[audio_input, username_state],
            outputs=[audio_result],
            api_name="transcribe_audio"
        )
        
        # Status display
        gr.Markdown("## Test Instructions")
        gr.Markdown("""
        **Test the following:**
        1. **Audio Recording:** Record audio using the microphone
        2. **Transcribe Audio:** Click the Transcribe Audio button
        3. **Audio Processing:** Check that the audio is processed by backend
        4. **Transcription Results:** Verify transcription results are displayed
        
        **Expected Behavior:**
        - Audio recording should work
        - Transcribe Audio button should be responsive
        - Backend function should be called directly
        - Audio transcription results should be displayed
        """)
    
    return app

if __name__ == "__main__":
    print("Creating file upload interface test...")
    app = test_file_upload_interface()
    print("Launching file upload interface test...")
    app.launch(debug=True, share=False)