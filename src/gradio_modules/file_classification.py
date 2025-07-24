#!/usr/bin/env python3
"""File Upload and Classification Interface.

This module provides a dedicated interface for uploading files and getting
classification results using the backend classification system.
"""

import gradio as gr
import os
import shutil
from pathlib import Path
from typing import Tuple, Any, List, Dict
from datetime import datetime
import asyncio
import logging

# Set up logging for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

from performance_utils import perf_monitor
from gradio_modules.enhanced_content_extraction import (
    enhanced_extract_file_content,
)
from infra_utils import get_chatbot_dir, clear_uploaded_files

# Import the enhanced classification formatter
from gradio_modules.classification_formatter import (
    format_classification_response,
)

from backend.file_handling import data_classification

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
    ".svg",  # Added SVG support
]

# Use a per-user request counter (consider if this is truly needed or if backend handles it)
classification_request_counts = {}


def get_uploads_dir(username: str) -> str:
    """Get the uploads directory for a specific user.

    :param username: The username to get uploads directory for
    :type username: str
    :return: Path to the user's uploads directory
    :rtype: str
    """
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
    logger.debug(f"Uploads directory for {username}: {uploads_dir}")
    return uploads_dir


def get_uploaded_files(username: str) -> List[str]:
    """Get list of uploaded files for the user.

    :param username: The username to get files for
    :type username: str
    :return: List of uploaded filenames
    :rtype: List[str]
    """
    if not username:
        logger.warning("Attempted to get uploaded files without a username.")
        return []

    try:
        uploads_dir = get_uploads_dir(username)
        if not os.path.exists(uploads_dir):
            logger.info(
                f"Uploads directory does not exist for {username}: {uploads_dir}"
            )
            return []

        files = []
        for file_path in Path(uploads_dir).glob("*"):
            if file_path.is_file() and is_file_allowed(file_path.name):
                files.append(file_path.name)

        # Sort by modification time, most recent first
        files_with_mtime = []
        for f_name in files:
            f_path = os.path.join(uploads_dir, f_name)
            if os.path.exists(f_path):
                files_with_mtime.append((f_name, os.path.getmtime(f_path)))

        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        sorted_files = [f[0] for f in files_with_mtime]

        logger.debug(f"Found {len(sorted_files)} uploaded files for {username}.")
        return sorted_files
    except Exception as e:
        logger.error(f"Error getting uploaded files for {username}: {e}")
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
        logger.warning("Missing username or filename for get_file_path.")
        return ""

    uploads_dir = get_uploads_dir(username)
    file_path = os.path.join(uploads_dir, filename)

    if not os.path.exists(file_path):
        logger.warning(f"File not found at expected path: {file_path}")
        return ""
    return file_path


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
    if not username:
        return "Please log in to view upload history."

    try:
        uploads_dir = get_uploads_dir(username)
        if not os.path.exists(uploads_dir):
            return "No files uploaded yet."

        files = get_uploaded_files(username)
        if not files:
            return "No files uploaded yet."

        history_lines = []
        for filename in files:
            file_path = get_file_path(username, filename)
            if os.path.exists(file_path):
                mod_time = os.path.getmtime(file_path)
                mod_datetime = datetime.fromtimestamp(mod_time)
                formatted_time = mod_datetime.strftime("%Y-%m-%d %H:%M:%S")
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size:,} bytes"
                history_lines.append(
                    f"- **{filename}** (uploaded: {formatted_time}, size: {size_str})"
                )
        return "\n".join(history_lines)
    except Exception as e:
        logger.error(f"Error loading upload history for {username}: {e}")
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
    logger.debug(f"Refreshing file dropdown for {username}. Found files: {files}")
    return gr.update(choices=files, value=None)


def show_loading() -> gr.update:
    """Show loading indicator."""
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
    """Hide loading indicator."""
    return gr.update(visible=False, value="")


def handle_clear_uploaded_files() -> Tuple[gr.update, gr.update, gr.update]:
    """Handle clearing uploaded files.

    :return: Tuple of UI updates for status, file dropdown, and history.
    :rtype: Tuple[gr.update, gr.update, gr.update]
    """
    try:
        clear_uploaded_files()
        logger.info("Uploaded files cleared successfully.")
        return (
            gr.update(visible=True, value="✅ Uploaded files cleared!"),
            gr.update(choices=[], value=None),  # Clear dropdown
            gr.update(value="No files uploaded yet."),  # Clear history
        )
    except Exception as e:
        logger.error(f"Error clearing files: {e}")
        return (
            gr.update(visible=True, value=f"❌ Error clearing files: {str(e)}"),
            gr.no_change(),  # Don't change dropdown on error
            gr.no_change(),  # Don't change history on error
        )


def call_backend_data_classification(content_text: str) -> Dict[str, Any]:
    """
    Call the backend data classification function.

    :param content_text: Text content to classify.
    :type content_text: str
    :return: Classification result dictionary.
    :rtype: Dict[str, Any]
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    logger.info("Calling backend data classification.")
    result = loop.run_until_complete(data_classification(content_text))
    logger.debug(f"Backend classification result: {result}")
    return result


def _get_error_return_state(
    error_message: str, username: str
) -> Tuple[gr.update, gr.update, str, str, str, str, str, gr.update, gr.update, str]:
    """Helper to return a consistent error state for UI updates."""
    return (
        gr.update(visible=True, value=f"❌ **Error:** {error_message}"),
        gr.update(visible=False),  # Hide results box on error
        "",  # Clear classification
        "",  # Clear sensitivity
        "",  # Clear file_info
        "",  # Clear reasoning
        "",  # Clear summary
        hide_loading(),
        refresh_file_dropdown(username),
        get_upload_history(username),
    )


def _perform_classification_logic(
    file_path: str, original_filename: str, username: str
) -> Tuple[gr.update, gr.update, str, str, str, str, str, gr.update, gr.update, str]:
    """
    Performs the core logic of file content extraction, classification, and formatting.
    This function is called by both handle_upload_click and handle_classify_existing.
    """
    perf_monitor.start_timer("file_classification_total")
    logger.info(f"Starting classification logic for {original_filename}")

    perf_monitor.start_timer("extraction")
    extraction_result = enhanced_extract_file_content(file_path)
    perf_monitor.end_timer("extraction")
    content_text = extraction_result.get("content", "")
    logger.info(f"Extracted {len(content_text)} characters from {original_filename}.")

    perf_monitor.start_timer("classification")
    classification = call_backend_data_classification(content_text)
    perf_monitor.end_timer("classification")

    perf_monitor.start_timer("formatting")
    formatted_results = format_classification_response(
        classification, extraction_result, original_filename
    )
    perf_monitor.end_timer("formatting")

    perf_monitor.end_timer("file_classification_total")
    logger.info(f"File classification for {original_filename} completed.")

    return (
        gr.update(
            visible=True,
            value="✅ **File uploaded and classified successfully!**",
        ),
        gr.update(visible=True),  # Make results box visible
        formatted_results["classification"],
        formatted_results["sensitivity"],
        formatted_results["file_info"],
        formatted_results["reasoning"],
        formatted_results["summary"],  # This will directly contain markdown
        hide_loading(),
        gr.no_change(),  # Dropdown is refreshed by handle_upload_click/handle_classify_existing
        get_upload_history(username),
    )


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
    logger.info(f"Handling file upload for user: {username}")

    if not username:
        return _get_error_return_state("Please log in first", username)

    if not file_obj:
        return _get_error_return_state("Please select a file to upload", username)

    try:
        saved_path, original_filename = save_uploaded_file(file_obj, username)
        # Update dropdown immediately after saving
        dropdown_update = refresh_file_dropdown(username)

        # Perform classification logic
        (
            status_update,
            results_box_update,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            loading_update,
            _,
            history_md_update,
        ) = _perform_classification_logic(  # Use _ for the dropdown_no_change
            saved_path, original_filename, username
        )

        # Combine the updates, ensuring file_dropdown is updated
        return (
            status_update,
            results_box_update,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            loading_update,
            dropdown_update,  # Explicitly pass the dropdown update
            history_md_update,
        )

    except ValueError as ve:
        logger.error(f"File upload validation error: {ve}")
        return _get_error_return_state(str(ve), username)
    except Exception as e:
        perf_monitor.end_timer("file_classification_total")
        logger.error(f"Error during file upload and classification: {e}", exc_info=True)
        return _get_error_return_state(f"System error: {e}", username)


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
    logger.info(
        f"Handling classification of existing file: {selected_file} for user: {username}"
    )

    if not username:
        return _get_error_return_state("Please log in first", username)

    if not selected_file:
        return _get_error_return_state("Please select a file to classify", username)

    file_path = get_file_path(username, selected_file)
    if not file_path:
        return _get_error_return_state("File not found in your uploads.", username)

    try:
        # Perform classification logic
        (
            status_update,
            results_box_update,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            loading_update,
            _,
            history_md_update,
        ) = _perform_classification_logic(  # Use _ for the dropdown_no_change
            file_path, selected_file, username
        )

        # Combine the updates, no dropdown update needed here
        return (
            status_update,
            results_box_update,
            classification_result,
            sensitivity_result,
            file_info,
            reasoning_result,
            summary_result,
            loading_update,
            history_md_update,  # Only history is updated, dropdown is not affected here
        )
    except Exception as e:
        perf_monitor.end_timer("file_classification_total")
        logger.error(f"Error during existing file classification: {e}", exc_info=True)
        return _get_error_return_state(f"System error: {e}", username)


def save_uploaded_file(file_obj: Any, username: str) -> Tuple[str, str]:
    """Save uploaded file to user's uploads directory.

    :param file_obj: The file object to save
    :type file_obj: Any
    :param username: The username to save the file for
    :type username: str
    :return: Tuple of (saved_file_path, original_filename)
    :rtype: Tuple[str, str]
    :raises ValueError: If file object or username is missing, or file type not allowed
    :raises IOError: If there's an error saving the file.
    """
    if not file_obj or not username:
        logger.error("Attempted to save file with missing file_obj or username.")
        raise ValueError("File object and username are required")

    original_filename = (
        Path(file_obj.name).name if hasattr(file_obj, "name") else "unknown_file"
    )

    if not is_file_allowed(original_filename):
        logger.warning(f"Attempted to upload disallowed file type: {original_filename}")
        raise ValueError(
            f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    uploads_dir = get_uploads_dir(username)
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )  # Added microseconds for more uniqueness
    file_ext = Path(original_filename).suffix
    base_name = Path(original_filename).stem
    unique_filename = f"{base_name}_{timestamp}{file_ext}"
    saved_path = os.path.join(uploads_dir, unique_filename)

    try:
        shutil.copy2(file_obj.name, saved_path)
        logger.info(f"File '{original_filename}' saved to '{saved_path}'")
    except Exception as e:
        logger.error(
            f"Failed to save file '{original_filename}' to '{saved_path}': {e}",
            exc_info=True,
        )
        raise IOError(f"Failed to save file: {e}")

    return saved_path, original_filename


def file_classification_interface(
    username_state: gr.State,
    logged_in_state: gr.State,  # Added this
    debug_info_state: gr.State,  # Added this
) -> gr.Blocks:
    """
    Creates the Gradio UI components for the file classification interface,
    encapsulated within a gr.Blocks object.
    """
    with gr.Blocks() as classification_block:  # The main Blocks for this interface
        with gr.Column(elem_classes=["file-classification-container"]):
            gr.Markdown("## 📁 File Upload & Classification")
            gr.Markdown(
                "Upload files for automatic security classification and sensitivity analysis."
            )
            gr.Markdown(
                "For the sake of performance, only the first 20,000 characters are extracted for text-based files. Non-text-based files are handled normally."
            )

            with gr.Group():
                gr.Markdown("### 📤 Upload New File")
                allowed_types_text = (
                    f"**Allowed file types:** {', '.join(ALLOWED_EXTENSIONS)}"
                )
                gr.Markdown(allowed_types_text)
                file_upload = gr.File(
                    label="Choose a file to upload",
                    file_types=ALLOWED_EXTENSIONS,
                    file_count="single",
                    elem_id="classification_file_upload",
                )
                upload_btn = gr.Button(
                    "Upload & Classify",
                    variant="primary",
                    size="lg",
                    elem_id="classification_upload_btn",
                )
                clear_files_btn = gr.Button(
                    "🗑️ Clear Uploaded Files",
                    variant="stop",
                    size="sm",
                    elem_id="classification_clear_files_btn",
                )
                clear_files_status = gr.Markdown(
                    visible=False, elem_id="classification_clear_status"
                )

            with gr.Group():
                gr.Markdown("### 📂 Classify Existing Files")
                gr.Markdown("Select from previously uploaded files to classify:")
                file_dropdown = gr.Dropdown(
                    label="Select uploaded file",
                    choices=[],
                    value=None,
                    interactive=True,
                    allow_custom_value=False,
                    elem_id="classification_file_dropdown",
                )
                refresh_files_btn = gr.Button(
                    "🔄 Refresh Files",
                    variant="secondary",
                    size="sm",
                    elem_id="classification_refresh_btn",
                )
                classify_existing_btn = gr.Button(
                    "Classify Selected File",
                    variant="primary",
                    size="lg",
                    elem_id="classification_classify_existing_btn",
                )

            loading_indicator = gr.HTML(
                value="",
                visible=False,
                elem_classes=["loading-indicator"],
                elem_id="classification_loading_indicator",
            )
            status_md = gr.Markdown(visible=False, elem_id="classification_status_md")

            gr.Markdown("### 🔍 Classification Results")
            with gr.Group(
                visible=False, elem_id="classification_results_box"
            ) as results_box:
                classification_result = gr.Markdown(
                    label="Security Classification",
                    value="",
                    elem_id="classification_security_result",
                )
                sensitivity_result = gr.Markdown(
                    label="Sensitivity Level",
                    value="",
                    elem_id="classification_sensitivity_result",
                )
                file_info = gr.Markdown(
                    label="File Information",
                    value="",
                    elem_id="classification_file_info",
                )
                reasoning_result = gr.Markdown(
                    label="Classification Reasoning",
                    value="",
                    elem_id="classification_reasoning_result",
                )
                summary_result = gr.Markdown(
                    value="",
                    label="Classification Summary",
                    elem_id="classification_summary_result",
                )

            gr.Markdown("### 📋 Upload History")
            history_md = gr.Markdown(
                "No files uploaded yet.", elem_id="classification_history_md"
            )
            refresh_history_btn = gr.Button(
                "Refresh History",
                variant="secondary",
                elem_id="classification_refresh_history_btn",
            )

        # --- Event Handlers (wired directly within this Blocks) ---
        logger.info("Setting up file classification event handlers within Blocks.")

        upload_btn.click(
            fn=show_loading, outputs=[loading_indicator], queue=False
        ).then(
            fn=handle_upload_click,
            inputs=[file_upload, username_state],
            outputs=[
                status_md,
                results_box,
                classification_result,
                sensitivity_result,
                file_info,
                reasoning_result,
                summary_result,
                loading_indicator,
                file_dropdown,  # Update dropdown after upload
                history_md,  # Update history after upload
            ],
            api_name="upload_and_classify_file",
            queue=True,
        )

        classify_existing_btn.click(
            fn=show_loading, outputs=[loading_indicator], queue=False
        ).then(
            fn=handle_classify_existing,
            inputs=[file_dropdown, username_state],
            outputs=[
                status_md,
                results_box,
                classification_result,
                sensitivity_result,
                file_info,
                reasoning_result,
                summary_result,
                loading_indicator,
                history_md,  # Update history after classification
            ],
            api_name="classify_existing_file",
            queue=True,
        )

        refresh_files_btn.click(
            fn=refresh_file_dropdown,
            inputs=[username_state],
            outputs=[file_dropdown],
            queue=False,
        )

        refresh_history_btn.click(
            fn=get_upload_history,
            inputs=[username_state],
            outputs=[history_md],
            queue=False,
        )

        clear_files_btn.click(
            fn=handle_clear_uploaded_files,
            outputs=[
                clear_files_status,
                file_dropdown,
                history_md,
            ],  # Clear dropdown and history as well
            queue=False,
        )

        # Initialize file dropdown and history on interface load (when this Blocks becomes visible)
        classification_block.load(
            fn=lambda username: (
                refresh_file_dropdown(username),
                get_upload_history(username),
            ),
            inputs=[username_state],
            outputs=[file_dropdown, history_md],
            queue=False,
        )

    return classification_block  # Return the entire Blocks object
