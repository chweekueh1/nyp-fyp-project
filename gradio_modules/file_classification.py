#!/usr/bin/env python3
"""File Upload and Classification Interface.

This module provides a dedicated interface for uploading files and getting
classification results using the backend classification system.
"""

import gradio as gr
import os
import shutil
from pathlib import Path
from typing import Tuple, Any, List
from datetime import datetime
from performance_utils import perf_monitor
from gradio_modules.enhanced_content_extraction import (
    enhanced_extract_file_content,
    classify_file_content,
)
from infra_utils import get_chatbot_dir, clear_uploaded_files

# Backend and LLM imports moved to function level to avoid early ChromaDB initialization
# from infra_utils import get_chatbot_dir
# from llm.dataProcessing import ExtractText  # Moved to function level
# from llm.classificationModel import classify_text  # Moved to function level

# Hardcoded list of allowed file extensions
ALLOWED_EXTENSIONS = [
    ".txt",
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".pptx",
    ".ppt",
    ".md",
    ".rtf",
    ".csv",
]

# Use a per-user request counter
classification_request_counts = {}


def get_uploads_dir(username: str) -> str:
    """Get the uploads directory for a specific user.

    :param username: The username to get uploads directory for
    :type username: str
    :return: Path to the user's uploads directory
    :rtype: str
    """
    import os
    # from infra_utils import get_chatbot_dir

    is_test_env = os.getenv("TESTING", "").lower() == "true"

    if is_test_env:
        # Use test upload directory
        uploads_dir = os.path.join(
            get_chatbot_dir(), "test_uploads", "txt_files", username
        )
    else:
        # Use production upload directory under ~/.nypai-chatbot/uploads/{username}
        uploads_dir = os.path.join(get_chatbot_dir(), "uploads", username)

    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir


def get_uploaded_files(username: str) -> List[str]:
    """Get list of uploaded files for the user.

    :param username: The username to get files for
    :type username: str
    :return: List of uploaded filenames
    :rtype: List[str]
    """
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
    """Get full path to an uploaded file.

    :param username: The username who owns the file
    :type username: str
    :param filename: The filename to get path for
    :type filename: str
    :return: Full path to the file if it exists, empty string otherwise
    :rtype: str
    """
    if not username or not filename:
        return ""

    uploads_dir = get_uploads_dir(username)
    file_path = os.path.join(uploads_dir, filename)

    if os.path.exists(file_path):
        return file_path
    return ""


def is_file_allowed(filename: str) -> bool:
    """Check if the file extension is allowed.

    :param filename: The filename to check
    :type filename: str
    :return: True if file extension is allowed, False otherwise
    :rtype: bool
    """
    if not filename:
        return False
    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS


def get_upload_history(username: str) -> str:
    """Get the upload history for the user.

    :param username: The username to get history for
    :type username: str
    :return: Formatted upload history string
    :rtype: str
    """
    try:
        uploads_dir = get_uploads_dir(username)
        if not os.path.exists(uploads_dir):
            return "No files uploaded yet."

        files = get_uploaded_files(username)
        if not files:
            return "No files uploaded yet."

        history_lines = ["### 📋 Upload History\n"]
        for filename in files:
            file_path = get_file_path(username, filename)
            if os.path.exists(file_path):
                # Get file modification time
                mod_time = os.path.getmtime(file_path)
                mod_datetime = datetime.fromtimestamp(mod_time)
                formatted_time = mod_datetime.strftime("%Y-%m-%d %H:%M:%S")

                # Get file size
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size:,} bytes"

                history_lines.append(
                    f"- **{filename}** (uploaded: {formatted_time}, size: {size_str})"
                )

        return "\n".join(history_lines)

    except Exception as e:
        return f"Error loading history: {str(e)}"


def refresh_file_dropdown(username: str) -> gr.update:
    """Refresh the file dropdown with uploaded files.

    :param username: The username to get files for
    :type username: str
    :return: Updated dropdown choices
    :rtype: gr.update
    """
    if not username:
        return gr.update(choices=[], value=None)

    files = get_uploaded_files(username)
    return gr.update(choices=files, value=None)


def show_loading() -> gr.update:
    """Show loading indicator.

    :return: Loading indicator update
    :rtype: gr.update
    """
    return gr.update(
        visible=True,
        value="""
        <div style="text-align: center; padding: 20px;">
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .spinner {
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 2s linear infinite;
                    margin: 0 auto;
                }
            </style>
            <div class="spinner"></div>
            <p>Processing...</p>
        </div>
        """,
    )


def hide_loading() -> gr.update:
    """Hide loading indicator.

    :return: Loading indicator update
    :rtype: gr.update
    """
    return gr.update(visible=False, value="")


def handle_clear_uploaded_files() -> tuple:
    """Handle clearing uploaded files.

    :return: Status message tuple
    :rtype: tuple
    """
    try:
        clear_uploaded_files()
        return (gr.update(visible=True, value="✅ Uploaded files cleared!"),)
    except Exception as e:
        return (gr.update(visible=True, value=f"❌ Error clearing files: {str(e)}"),)


def handle_upload_click(file_obj: Any, username: str) -> tuple:
    """Handle file upload and classification.

    :param file_obj: The uploaded file object
    :type file_obj: Any
    :param username: The username
    :type username: str
    :return: Tuple of UI updates
    :rtype: tuple
    """
    perf_monitor.start_timer("file_classification_total")
    if not username:
        return (
            gr.update(visible=True, value="❌ **Error:** Please log in first"),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            "",
            hide_loading(),
            refresh_file_dropdown(username),
        )

    if not file_obj:
        return (
            gr.update(
                visible=True, value="❌ **Error:** Please select a file to upload"
            ),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            get_upload_history(username),
            hide_loading(),
            refresh_file_dropdown(username),
        )

    try:
        # Save the uploaded file
        saved_path, original_filename = save_uploaded_file(file_obj, username)
        perf_monitor.start_timer("extraction")
        extraction_result = enhanced_extract_file_content(saved_path)
        perf_monitor.end_timer("extraction")
        content_text = extraction_result.get("content", "")
        perf_monitor.start_timer("classification")
        classification = classify_file_content(content_text, username)
        perf_monitor.end_timer("classification")
        perf_monitor.start_timer("formatting")
        # Format results using enhanced formatter
        try:
            from gradio_modules.classification_formatter import (
                format_classification_response,
            )

            formatted_results = format_classification_response(
                classification, extraction_result, original_filename
            )
            perf_monitor.end_timer("formatting")
            perf_monitor.end_timer("file_classification_total")

            return (
                gr.update(
                    visible=True,
                    value="✅ **File uploaded and classified successfully!**",
                ),
                gr.update(visible=True),
                formatted_results["classification"],
                formatted_results["sensitivity"],
                formatted_results["file_info"],
                formatted_results["reasoning"],
                formatted_results["summary"],
                get_upload_history(username),
                hide_loading(),
                refresh_file_dropdown(username),
            )
        except ImportError:
            # Fallback to basic formatting if formatter not available
            perf_monitor.end_timer("formatting")
            perf_monitor.end_timer("file_classification_total")
            return (
                gr.update(
                    visible=True,
                    value="✅ **File uploaded and classified successfully!**",
                ),
                gr.update(visible=True),
                f"**Classification:** {classification.get('classification', 'Unknown')}",
                f"**Sensitivity:** {classification.get('sensitivity', 'Unknown')}",
                f"**File:** {original_filename}",
                f"**Reasoning:** {classification.get('reasoning', 'No reasoning provided')}",
                "**Summary:** Content extracted and classified",
                get_upload_history(username),
                hide_loading(),
                refresh_file_dropdown(username),
            )

    except Exception as e:
        perf_monitor.end_timer("file_classification_total")
        error_msg = f"❌ **Error processing file:** {str(e)}"
        return (
            gr.update(visible=True, value=error_msg),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            get_upload_history(username),
            hide_loading(),
            refresh_file_dropdown(username),
        )


def handle_classify_existing(selected_file: str, username: str) -> tuple:
    """Handle classification of existing uploaded file.

    :param selected_file: The selected filename
    :type selected_file: str
    :param username: The username
    :type username: str
    :return: Tuple of UI updates
    :rtype: tuple
    """
    perf_monitor.start_timer("file_classification_total")
    if not username:
        return (
            gr.update(visible=True, value="❌ **Error:** Please log in first"),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            get_upload_history(username),
            hide_loading(),
        )

    if not selected_file:
        return (
            gr.update(
                visible=True, value="❌ **Error:** Please select a file to classify"
            ),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            get_upload_history(username),
            hide_loading(),
        )

    try:
        file_path = get_file_path(username, selected_file)
        if not file_path:
            return (
                gr.update(visible=True, value="❌ **Error:** File not found"),
                gr.update(visible=False),
                "",
                "",
                "",
                "",
                gr.update(visible=False, value=""),
                get_upload_history(username),
                hide_loading(),
            )

        perf_monitor.start_timer("extraction")
        extraction_result = enhanced_extract_file_content(file_path)
        perf_monitor.end_timer("extraction")
        content_text = extraction_result.get("content", "")
        perf_monitor.start_timer("classification")
        classification = classify_file_content(content_text, username)
        perf_monitor.end_timer("classification")
        perf_monitor.start_timer("formatting")

        # Format results using enhanced formatter
        try:
            from gradio_modules.classification_formatter import (
                format_classification_response,
            )

            formatted_results = format_classification_response(
                classification, extraction_result, selected_file
            )
            perf_monitor.end_timer("formatting")
            perf_monitor.end_timer("file_classification_total")

            return (
                gr.update(visible=True, value="✅ **File classified successfully!**"),
                gr.update(visible=True),
                formatted_results["classification"],
                formatted_results["sensitivity"],
                formatted_results["file_info"],
                formatted_results["reasoning"],
                formatted_results["summary"],
                get_upload_history(username),
                hide_loading(),
            )
        except ImportError:
            # Fallback to basic formatting if formatter not available
            perf_monitor.end_timer("formatting")
            perf_monitor.end_timer("file_classification_total")
            return (
                gr.update(visible=True, value="✅ **File classified successfully!**"),
                gr.update(visible=True),
                f"**Classification:** {classification.get('classification', 'Unknown')}",
                f"**Sensitivity:** {classification.get('sensitivity', 'Unknown')}",
                f"**File:** {selected_file}",
                f"**Reasoning:** {classification.get('reasoning', 'No reasoning provided')}",
                "**Summary:** Content extracted and classified",
                get_upload_history(username),
                hide_loading(),
            )

    except Exception as e:
        perf_monitor.end_timer("file_classification_total")
        error_msg = f"❌ **Error classifying file:** {str(e)}"
        return (
            gr.update(visible=True, value=error_msg),
            gr.update(visible=False),
            "",
            "",
            "",
            "",
            gr.update(visible=False, value=""),
            get_upload_history(username),
            hide_loading(),
        )


def save_uploaded_file(file_obj: Any, username: str) -> Tuple[str, str]:
    """Save uploaded file to user's uploads directory.

    :param file_obj: The file object to save
    :type file_obj: Any
    :param username: The username to save the file for
    :type username: str
    :return: Tuple of (saved_file_path, original_filename)
    :rtype: Tuple[str, str]
    :raises ValueError: If file object or username is missing, or file type not allowed
    """
    if not file_obj or not username:
        raise ValueError("File object and username are required")

    # Get original filename
    original_filename = getattr(file_obj, "name", "unknown_file")
    if not original_filename:
        original_filename = "unknown_file"

    # Check file extension
    if not is_file_allowed(original_filename):
        raise ValueError(
            f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

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
    if hasattr(file_obj, "name") and os.path.exists(file_obj.name):
        # File object with path
        shutil.copy2(file_obj.name, saved_path)
    else:
        # File object without path (uploaded content)
        with open(saved_path, "wb") as f:
            if hasattr(file_obj, "read"):
                f.write(file_obj.read())
            else:
                # Assume it's a path string
                with open(file_obj, "rb") as src:
                    shutil.copyfileobj(src, f)

    return saved_path, original_filename


def file_classification_interface(username_state: gr.State) -> tuple:
    """Create the file upload and classification interface.

    :param username_state: Gradio state containing the current username
    :type username_state: gr.State
    :return: Tuple of Gradio components for the interface
    :rtype: tuple
    """

    # Removed Column context manager to avoid Gradio 5.34.0 compatibility issues
    # Header
    gr.Markdown("## 📁 File Upload & Classification")
    gr.Markdown(
        "Upload files for automatic security classification and sensitivity analysis."
    )

    # File upload section - removed Group context manager
    gr.Markdown("### 📤 Upload New File")

    # Show allowed file types
    allowed_types_text = f"**Allowed file types:** {', '.join(ALLOWED_EXTENSIONS)}"
    gr.Markdown(allowed_types_text)

    file_upload = gr.File(
        label="Choose a file to upload",
        file_types=ALLOWED_EXTENSIONS,
        file_count="single",
    )

    upload_btn = gr.Button("Upload & Classify", variant="primary", size="lg")

    # Add Clear Uploaded Files button
    clear_files_btn = gr.Button("🗑️ Clear Uploaded Files", variant="stop", size="sm")
    clear_files_status = gr.Markdown(visible=False)

    # File selection section for already uploaded files
    gr.Markdown("### 📂 Classify Existing Files")
    gr.Markdown("Select from previously uploaded files to classify:")

    # Create dropdown without any context managers to avoid Gradio compatibility issue
    file_dropdown = gr.Dropdown(
        label="Select uploaded file",
        choices=[],
        value=None,
        interactive=True,
        allow_custom_value=False,
    )

    # Buttons without Row context manager
    refresh_files_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")
    classify_existing_btn = gr.Button(
        "Classify Selected File", variant="primary", size="lg"
    )

    # Loading indicator
    loading_indicator = gr.HTML(
        value="", visible=False, elem_classes=["loading-indicator"]
    )

    # Status and results section - removed all context managers
    status_md = gr.Markdown(visible=False)

    # Classification results - simplified without nested context managers
    results_section = gr.Column(visible=False)
    gr.Markdown("### 🔍 Classification Results")

    classification_result = gr.Textbox(
        label="Security Classification",
        interactive=False,
        placeholder="Classification will appear here...",
    )
    sensitivity_result = gr.Textbox(
        label="Sensitivity Level",
        interactive=False,
        placeholder="Sensitivity will appear here...",
    )

    file_info = gr.Textbox(
        label="File Information",
        interactive=False,
        placeholder="File details will appear here...",
        lines=3,
    )

    reasoning_result = gr.Textbox(
        label="Classification Reasoning",
        interactive=False,
        placeholder="Reasoning will appear here...",
        lines=4,
    )

    # Enhanced summary section
    summary_result = gr.Markdown(
        value="", label="Classification Summary", visible=False
    )

    # Upload history section - removed Group context manager
    gr.Markdown("### 📋 Upload History")
    history_md = gr.Markdown("No files uploaded yet.")
    refresh_history_btn = gr.Button("Refresh History", variant="secondary")

    # Functions are now defined at module level

    # Note: Event handlers should be set up in the calling context (app.py)
    # to ensure they are within a proper Gradio Blocks context
    # The following functions are available for event handling:
    # - handle_upload_click
    # - handle_classify_existing
    # - refresh_file_dropdown
    # - get_upload_history
    # - handle_clear_uploaded_files
    # - show_loading

    return (
        file_upload,
        upload_btn,
        status_md,
        results_section,
        classification_result,
        sensitivity_result,
        file_info,
        reasoning_result,
        summary_result,
        history_md,
        refresh_history_btn,
        file_dropdown,
        refresh_files_btn,
        classify_existing_btn,
        loading_indicator,
        clear_files_btn,
        clear_files_status,
    )


def setup_file_classification_events(
    components: tuple, username_state: gr.State
) -> None:
    """Set up event handlers for file classification interface.

    This function should be called within a Gradio Blocks context to properly
    set up all the event handlers for the file classification interface.

    :param components: Tuple of components returned by file_classification_interface
    :type components: tuple
    :param username_state: The username state component
    :type username_state: gr.State
    :return: None
    :rtype: None
    """
    (
        file_upload,
        upload_btn,
        status_md,
        results_section,
        classification_result,
        sensitivity_result,
        file_info,
        reasoning_result,
        summary_result,
        history_md,
        refresh_history_btn,
        file_dropdown,
        refresh_files_btn,
        classify_existing_btn,
        loading_indicator,
        clear_files_btn,
        clear_files_status,
    ) = components

    # Handler functions are defined in the same module scope

    # Event handlers with loading indicators
    upload_btn.click(fn=show_loading, outputs=[loading_indicator]).then(
        fn=handle_upload_click,
        inputs=[file_upload, username_state],
        outputs=[
            status_md,
            results_section,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            history_md,
            loading_indicator,
            file_dropdown,
        ],
    )

    classify_existing_btn.click(fn=show_loading, outputs=[loading_indicator]).then(
        fn=handle_classify_existing,
        inputs=[file_dropdown, username_state],
        outputs=[
            status_md,
            results_section,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            history_md,
            loading_indicator,
        ],
    )

    refresh_files_btn.click(
        fn=refresh_file_dropdown, inputs=[username_state], outputs=[file_dropdown]
    )

    refresh_history_btn.click(
        fn=get_upload_history, inputs=[username_state], outputs=[history_md]
    )

    clear_files_btn.click(fn=handle_clear_uploaded_files, outputs=[clear_files_status])

    # Initialize file dropdown on interface load
    def initialize_interface(username: str):
        """Initialize the interface with user's uploaded files."""
        return refresh_file_dropdown(username)

    # Set up initial state
    username_state.change(
        fn=initialize_interface, inputs=[username_state], outputs=[file_dropdown]
    )
