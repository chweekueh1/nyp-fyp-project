"""
File Upload and Classification Interface

This module provides a dedicated interface for uploading files and getting 
classification results using the backend classification system.
"""

import gradio as gr
import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any, List
from datetime import datetime
# Backend and LLM imports moved to function level to avoid early ChromaDB initialization
from utils import get_chatbot_dir
# from llm.dataProcessing import ExtractText  # Moved to function level
# from llm.classificationModel import classify_text  # Moved to function level

# Hardcoded list of allowed file extensions
ALLOWED_EXTENSIONS = [
    '.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls', 
    '.pptx', '.ppt', '.md', '.rtf', '.csv'
]

def get_uploads_dir(username: str) -> str:
    """Get the uploads directory for a specific user."""
    # Check if we're in test mode
    import os
    is_test_env = os.getenv('TESTING', '').lower() == 'true'

    if is_test_env:
        # Use test upload directory
        uploads_dir = os.path.join(get_chatbot_dir(), 'test_uploads', 'txt_files', username)
    else:
        # Use production upload directory - align with backend structure
        uploads_dir = os.path.join(get_chatbot_dir(), 'uploads', username)

    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir

def get_uploaded_files(username: str) -> List[str]:
    """Get list of uploaded files for the user."""
    if not username:
        return []

    try:
        uploads_dir = get_uploads_dir(username)
        if not os.path.exists(uploads_dir):
            return []

        files = []
        for file_path in Path(uploads_dir).glob("*"):
            if file_path.is_file() and is_file_allowed(file_path.name):
                files.append(file_path.name)

        return sorted(files, reverse=True)  # Most recent first
    except Exception as e:
        print(f"Error getting uploaded files: {e}")
        return []

def get_file_path(username: str, filename: str) -> str:
    """Get full path to an uploaded file."""
    if not username or not filename:
        return ""

    uploads_dir = get_uploads_dir(username)
    file_path = os.path.join(uploads_dir, filename)

    if os.path.exists(file_path):
        return file_path
    return ""

def is_file_allowed(filename: str) -> bool:
    """Check if the file extension is allowed."""
    if not filename:
        return False
    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS

def save_uploaded_file(file_obj, username: str) -> Tuple[str, str]:
    """
    Save uploaded file to user's uploads directory.
    
    Returns:
        Tuple[str, str]: (saved_file_path, original_filename)
    """
    if not file_obj or not username:
        raise ValueError("File object and username are required")
    
    # Get original filename
    original_filename = getattr(file_obj, 'name', 'unknown_file')
    if not original_filename:
        original_filename = 'unknown_file'
    
    # Check file extension
    if not is_file_allowed(original_filename):
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Create uploads directory
    uploads_dir = get_uploads_dir(username)
    
    # Generate unique filename to avoid conflicts
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(original_filename).suffix
    base_name = Path(original_filename).stem
    unique_filename = f"{base_name}_{timestamp}{file_ext}"
    
    # Save file
    saved_path = os.path.join(uploads_dir, unique_filename)
    
    # Copy file content
    if hasattr(file_obj, 'name') and os.path.exists(file_obj.name):
        # File object with path
        shutil.copy2(file_obj.name, saved_path)
    else:
        # File object without path (uploaded content)
        with open(saved_path, 'wb') as f:
            if hasattr(file_obj, 'read'):
                f.write(file_obj.read())
            else:
                # Assume it's a path string
                with open(file_obj, 'rb') as src:
                    shutil.copyfileobj(src, f)
    
    return saved_path, original_filename

def extract_file_content(file_path: str) -> str:
    """Extract text content from uploaded file."""
    try:
        # Lazy import to avoid early ChromaDB initialization
        from llm.dataProcessing import ExtractText

        documents = ExtractText(file_path)
        if documents:
            # Combine all document content
            content = "\n\n".join([doc.page_content for doc in documents])
            return content
        else:
            return "No content could be extracted from the file."
    except Exception as e:
        raise Exception(f"Error extracting content: {str(e)}")

def classify_file_content(content: str) -> Dict[str, Any]:
    """Classify the extracted file content."""
    try:
        if not content or not content.strip():
            return {
                "classification": "Unknown",
                "sensitivity": "Unknown",
                "reasoning": "No content available for classification"
            }

        # Lazy import to avoid early ChromaDB initialization
        from llm.classificationModel import classify_text

        # Use the classification model
        result = classify_text(content)
        
        # Extract the answer which should be JSON
        answer = result.get('answer', '{}')
        
        # Try to parse JSON response
        try:
            if isinstance(answer, str):
                classification_result = json.loads(answer)
            else:
                classification_result = answer
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            classification_result = {
                "classification": "Official(Open)",
                "sensitivity": "Non-Sensitive",
                "reasoning": f"Classification completed. Raw response: {answer}"
            }
        
        return classification_result
        
    except Exception as e:
        return {
            "classification": "Error",
            "sensitivity": "Error",
            "reasoning": f"Classification failed: {str(e)}"
        }

def file_classification_interface(username_state):
    """
    Create the file upload and classification interface.
    
    Args:
        username_state: Gradio state containing the current username
        
    Returns:
        Tuple of Gradio components for the interface
    """
    
    with gr.Column(elem_classes=["file-classification-container"]):
        # Header
        gr.Markdown("## 📁 File Upload & Classification")
        gr.Markdown("Upload files for automatic security classification and sensitivity analysis.")
        
        # File upload section
        with gr.Group():
            gr.Markdown("### 📤 Upload New File")

            # Show allowed file types
            allowed_types_text = f"**Allowed file types:** {', '.join(ALLOWED_EXTENSIONS)}"
            gr.Markdown(allowed_types_text)

            file_upload = gr.File(
                label="Choose a file to upload",
                file_types=ALLOWED_EXTENSIONS,
                file_count="single"
            )

            upload_btn = gr.Button("Upload & Classify", variant="primary", size="lg")

        # File selection section for already uploaded files
        with gr.Group():
            gr.Markdown("### 📂 Classify Existing Files")
            gr.Markdown("Select from previously uploaded files to classify:")

            with gr.Row():
                file_dropdown = gr.Dropdown(
                    label="Select uploaded file",
                    choices=[],
                    value=None,
                    interactive=True,
                    allow_custom_value=False
                )
                refresh_files_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")

            classify_existing_btn = gr.Button("Classify Selected File", variant="primary", size="lg")

        # Loading indicator
        loading_indicator = gr.HTML(
            value="",
            visible=False,
            elem_classes=["loading-indicator"]
        )
        
        # Status and results section
        with gr.Group():
            status_md = gr.Markdown(visible=False)
            
            # Classification results
            with gr.Column(visible=False) as results_section:
                gr.Markdown("### 🔍 Classification Results")
                
                with gr.Row():
                    with gr.Column():
                        classification_result = gr.Textbox(
                            label="Security Classification",
                            interactive=False,
                            placeholder="Classification will appear here..."
                        )
                        sensitivity_result = gr.Textbox(
                            label="Sensitivity Level", 
                            interactive=False,
                            placeholder="Sensitivity will appear here..."
                        )
                    
                    with gr.Column():
                        file_info = gr.Textbox(
                            label="File Information",
                            interactive=False,
                            placeholder="File details will appear here...",
                            lines=3
                        )
                
                reasoning_result = gr.Textbox(
                    label="Classification Reasoning",
                    interactive=False,
                    placeholder="Reasoning will appear here...",
                    lines=4
                )
        
        # Upload history section
        with gr.Group():
            gr.Markdown("### 📋 Upload History")
            history_md = gr.Markdown("No files uploaded yet.")
            refresh_history_btn = gr.Button("Refresh History", variant="secondary")
    

    
    def get_upload_history(username):
        """Get the upload history for the user."""
        if not username:
            return "Please log in to view upload history."
        
        try:
            uploads_dir = get_uploads_dir(username)
            
            if not os.path.exists(uploads_dir):
                return "No uploads directory found."
            
            files = []
            for file_path in Path(uploads_dir).glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    files.append(f"📄 **{file_path.name}** ({size:,} bytes) - {modified}")
            
            if not files:
                return "No files uploaded yet."
            
            return "\n\n".join(files)
            
        except Exception as e:
            return f"Error loading history: {str(e)}"
    
    # Helper functions for file operations
    def refresh_file_dropdown(username):
        """Refresh the file dropdown with uploaded files."""
        if not username:
            return gr.update(choices=[], value=None)

        files = get_uploaded_files(username)
        return gr.update(choices=files, value=None)

    def show_loading():
        """Show loading indicator."""
        return gr.update(
            visible=True,
            value="""
            <div style="text-align: center; padding: 20px;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <p style="margin-top: 10px; color: #666;">🔄 Processing file classification...</p>
                <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                </style>
            </div>
            """
        )

    def hide_loading():
        """Hide loading indicator."""
        return gr.update(visible=False, value="")

    # Event handlers - simplified for better compatibility
    def handle_upload_click(file_obj, username):
        """Simplified upload handler with loading indicator."""
        if not username:
            return (
                gr.update(visible=True, value="❌ **Error:** Please log in first"),
                gr.update(visible=False),
                "", "", "", "", "Please log in to view upload history.",
                hide_loading(),
                refresh_file_dropdown(username)
            )

        if not file_obj:
            return (
                gr.update(visible=True, value="❌ **Error:** Please select a file to upload"),
                gr.update(visible=False),
                "", "", "", "", get_upload_history(username),
                hide_loading(),
                refresh_file_dropdown(username)
            )

        try:
            # Save the uploaded file
            saved_path, original_filename = save_uploaded_file(file_obj, username)

            # Extract and classify content
            content = extract_file_content(saved_path)
            classification = classify_file_content(content)

            # Prepare results
            file_size = os.path.getsize(saved_path)
            file_info_text = f"**Filename:** {original_filename}\n**Size:** {file_size:,} bytes\n**Saved:** {os.path.basename(saved_path)}"
            success_msg = f"✅ **Success:** {original_filename} uploaded and classified!"

            return (
                gr.update(visible=True, value=success_msg),
                gr.update(visible=True),
                classification.get('classification', 'Unknown'),
                classification.get('sensitivity', 'Unknown'),
                file_info_text,
                classification.get('reasoning', 'No reasoning provided'),
                get_upload_history(username),
                hide_loading(),
                refresh_file_dropdown(username)
            )

        except Exception as e:
            error_msg = f"❌ **Error:** {str(e)}"
            return (
                gr.update(visible=True, value=error_msg),
                gr.update(visible=False),
                "", "", "", "", get_upload_history(username),
                hide_loading(),
                refresh_file_dropdown(username)
            )

    def handle_classify_existing(selected_file, username):
        """Handle classification of existing uploaded file."""
        if not username:
            return (
                gr.update(visible=True, value="❌ **Error:** Please log in first"),
                gr.update(visible=False),
                "", "", "", "", "Please log in to view upload history.",
                hide_loading()
            )

        if not selected_file:
            return (
                gr.update(visible=True, value="❌ **Error:** Please select a file to classify"),
                gr.update(visible=False),
                "", "", "", "", get_upload_history(username),
                hide_loading()
            )

        try:
            # Get file path
            file_path = get_file_path(username, selected_file)
            if not file_path:
                raise Exception(f"File not found: {selected_file}")

            # Extract and classify content
            content = extract_file_content(file_path)
            classification = classify_file_content(content)

            # Prepare results
            file_size = os.path.getsize(file_path)
            file_info_text = f"**Filename:** {selected_file}\n**Size:** {file_size:,} bytes\n**Path:** {os.path.basename(file_path)}"
            success_msg = f"✅ **Success:** {selected_file} classified!"

            return (
                gr.update(visible=True, value=success_msg),
                gr.update(visible=True),
                classification.get('classification', 'Unknown'),
                classification.get('sensitivity', 'Unknown'),
                file_info_text,
                classification.get('reasoning', 'No reasoning provided'),
                get_upload_history(username),
                hide_loading()
            )

        except Exception as e:
            error_msg = f"❌ **Error:** {str(e)}"
            return (
                gr.update(visible=True, value=error_msg),
                gr.update(visible=False),
                "", "", "", "", get_upload_history(username),
                hide_loading()
            )

    # Event handlers with loading indicators
    upload_btn.click(
        fn=show_loading,
        outputs=[loading_indicator]
    ).then(
        fn=handle_upload_click,
        inputs=[file_upload, username_state],
        outputs=[
            status_md,
            results_section,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            history_md,
            loading_indicator,
            file_dropdown
        ]
    )

    classify_existing_btn.click(
        fn=show_loading,
        outputs=[loading_indicator]
    ).then(
        fn=handle_classify_existing,
        inputs=[file_dropdown, username_state],
        outputs=[
            status_md,
            results_section,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            history_md,
            loading_indicator
        ]
    )

    refresh_files_btn.click(
        fn=refresh_file_dropdown,
        inputs=[username_state],
        outputs=[file_dropdown]
    )

    refresh_history_btn.click(
        fn=get_upload_history,
        inputs=[username_state],
        outputs=[history_md]
    )
    
    # Initialize file dropdown on interface load
    def initialize_interface(username):
        """Initialize the interface with user's uploaded files."""
        return refresh_file_dropdown(username)

    # Set up initial state
    username_state.change(
        fn=initialize_interface,
        inputs=[username_state],
        outputs=[file_dropdown]
    )

    return (
        file_upload, upload_btn, status_md, results_section,
        classification_result, sensitivity_result, file_info,
        reasoning_result, history_md, refresh_history_btn,
        file_dropdown, refresh_files_btn, classify_existing_btn, loading_indicator
    )
