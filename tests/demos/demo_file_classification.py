#!/usr/bin/env python3
"""
Demo for File Classification Interface

This demo showcases the file upload and classification functionality.
"""

import sys
from pathlib import Path
import gradio as gr
from gradio_modules.file_classification import file_classification_interface

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def create_demo():
    """Create the file classification demo interface."""

    print("🎯 File Classification Demo")
    print("=" * 50)
    print("Features:")
    print("  📁 File upload with extension validation")
    print("  🔍 Automatic security classification")
    print("  📊 Sensitivity level analysis")
    print("  💾 File storage in user uploads directory")
    print("  📋 Upload history tracking")
    print("=" * 50)

    # Custom CSS for the demo
    demo_css = """
    .demo-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .feature-box {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-result {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 8px;
        padding: 15px;
    }
    .error-result {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 8px;
        padding: 15px;
    }
    """

    with gr.Blocks(title="File Classification Demo", css=demo_css) as demo:
        # Demo header
        with gr.Column(elem_classes="demo-header"):
            gr.Markdown("# 📄 File Classification Demo")
            gr.Markdown(
                "Upload files for automatic security classification and sensitivity analysis"
            )

        # Demo features info
        with gr.Column(elem_classes="feature-box"):
            gr.Markdown("""
            ### 🎯 Demo Features
            
            **Supported File Types:** `.txt`, `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.ppt`, `.md`, `.rtf`, `.csv`
            
            **Classification Categories:**
            - **Security:** Official(Open), Official(Closed), Restricted, Confidential, Secret, Top Secret
            - **Sensitivity:** Non-Sensitive, Sensitive Normal, Sensitive High
            
            **Demo Workflow:**
            1. 📁 Upload a supported file type
            2. 🔍 System extracts text content
            3. 🤖 AI classifies security level and sensitivity
            4. 📊 Results displayed with reasoning
            5. 💾 File stored in uploads directory
            """)

        # Login simulation for demo
        with gr.Row():
            with gr.Column(scale=2):
                demo_username = gr.Textbox(
                    label="Demo Username",
                    value="test",
                    placeholder="Enter username for demo",
                )
            with gr.Column(scale=1):
                login_btn = gr.Button("Set User", variant="primary")

        # User state
        username_state = gr.State("")
        login_status = gr.Markdown("Please set a username to begin the demo.")

        # File classification interface (initially hidden)
        with gr.Column(visible=False) as classification_interface:
            # Use the actual file classification interface
            file_classification_interface(username_state)

        # Demo instructions
        with gr.Column(elem_classes="feature-box"):
            gr.Markdown("""
            ### 📝 Demo Instructions
            
            1. **Set Username:** Enter a demo username above and click "Set User"
            2. **Upload File:** Choose a file from the supported types
            3. **Classify:** Click "Upload & Classify" to process the file
            4. **Review Results:** Check the classification, sensitivity, and reasoning
            5. **View History:** See your uploaded files in the history section
            
            **Sample Files to Try:**
            - Create a `.txt` file with confidential business information
            - Upload a document with personal data
            - Try different content types to see classification differences
            """)

        # Demo event handlers
        def handle_demo_login(username):
            """Handle demo login."""
            if not username or not username.strip():
                return (
                    "",
                    gr.update(value="❌ Please enter a username"),
                    gr.update(visible=False),
                )

            username = username.strip()
            return (
                username,
                gr.update(
                    value=f"✅ **Demo user set:** {username}\n\nYou can now upload files for classification!"
                ),
                gr.update(visible=True),
            )

        login_btn.click(
            fn=handle_demo_login,
            inputs=[demo_username],
            outputs=[username_state, login_status, classification_interface],
        )

        # Auto-login on Enter
        demo_username.submit(
            fn=handle_demo_login,
            inputs=[demo_username],
            outputs=[username_state, login_status, classification_interface],
        )

    return demo


def main():
    """Launch the file classification demo."""

    # Check if backend is available
    try:
        from utils import get_chatbot_dir

        print(f"✅ Backend available - uploads will be saved to: {get_chatbot_dir()}")
    except Exception as e:
        print(f"⚠️ Backend warning: {e}")

    # Check if classification model is available
    try:
        print("✅ Classification model available")
    except Exception as e:
        print(f"⚠️ Classification model warning: {e}")
        print("   Classification will use fallback responses")

    print("\n🚀 Starting File Classification Demo...")

    demo = create_demo()

    # Launch demo
    demo.launch(
        server_name="127.0.0.1",
        server_port=7867,
        share=False,
        show_error=True,
        quiet=False,
    )


if __name__ == "__main__":
    main()
