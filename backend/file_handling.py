#!/usr/bin/env python3
"""
File handling module for the backend.
Contains file upload, processing, and classification functions.
"""

import os
import logging
import filetype
import zipfile
import mimetypes
from datetime import datetime, timezone
from .config import CHAT_DATA_PATH
from .rate_limiting import check_rate_limit
from .database import get_classification
from .timezone_utils import get_utc_timestamp

# Set up logging
logger = logging.getLogger(__name__)


async def detectFileType_async(file_path: str) -> str | None:
    """Detect the file type asynchronously."""
    try:
        if not os.path.exists(file_path):
            return None

        # Try to detect file type using filetype library
        kind = filetype.guess(file_path)
        if kind:
            return kind.mime

        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type

        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() in [
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
        ]:
            return "text/plain"
        elif ext.lower() in [".pdf"]:
            return "application/pdf"
        elif ext.lower() in [".doc", ".docx"]:
            return "application/msword"
        elif ext.lower() in [".xls", ".xlsx"]:
            return "application/vnd.ms-excel"
        elif ext.lower() in [".ppt", ".pptx"]:
            return "application/vnd.ms-powerpoint"
        elif ext.lower() in [".zip", ".rar", ".7z"]:
            return "application/zip"
        elif ext.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            return "image/jpeg"
        elif ext.lower() in [".mp3", ".wav", ".flac", ".aac"]:
            return "audio/mpeg"
        elif ext.lower() in [".mp4", ".avi", ".mov", ".wmv"]:
            return "video/mp4"

        return None

    except Exception as e:
        logger.error(f"Error detecting file type for {file_path}: {e}")
        return None


async def handle_uploaded_file(ui_state: dict) -> dict:
    """
    File upload interface: processes the file and saves it permanently.
    """
    print(f"[DEBUG] backend.handle_uploaded_file called with ui_state: {ui_state}")
    username = ui_state.get("username")
    file_obj = ui_state.get("file_obj")

    if not file_obj:
        return {
            "status": "error",
            "message": "No file provided",
            "debug": "No file_obj in ui_state",
        }

    if not username:
        return {
            "status": "error",
            "message": "Username required for file processing",
            "debug": "No username provided",
        }

    # Check rate limit for file upload operations
    if not await check_rate_limit(username, "file_upload"):
        return {
            "status": "error",
            "message": "Rate limit exceeded for file uploads",
            "debug": "Rate limit exceeded",
        }

    try:
        # Get file information
        filename = file_obj.name
        file_content = file_obj.read()

        # Detect file type
        file_type = await detectFileType_async(filename)

        # Process file based on type
        if file_type and file_type.startswith("text/"):
            # Text file processing
            content = file_content.decode("utf-8", errors="ignore")
            result = await data_classification(content)
            return {
                "status": "success",
                "message": f"Text file '{filename}' processed successfully",
                "file_type": file_type,
                "classification": result,
                "debug": "Text file processed",
            }

        elif file_type and file_type == "application/pdf":
            # PDF processing
            result = await upload_file(file_content, filename, username)
            return {
                "status": "success",
                "message": f"PDF file '{filename}' uploaded successfully",
                "file_type": file_type,
                "upload_result": result,
                "debug": "PDF file uploaded",
            }

        elif file_type and file_type == "application/zip":
            # ZIP file processing
            result = await process_zip_file(file_content, filename, username)
            return {
                "status": "success",
                "message": f"ZIP file '{filename}' processed successfully",
                "file_type": file_type,
                "zip_result": result,
                "debug": "ZIP file processed",
            }

        else:
            # Generic file upload
            result = await upload_file(file_content, filename, username)
            return {
                "status": "success",
                "message": f"File '{filename}' uploaded successfully",
                "file_type": file_type or "unknown",
                "upload_result": result,
                "debug": "Generic file uploaded",
            }

    except Exception as e:
        logger.error(f"Error in handle_uploaded_file: {e}")
        return {
            "status": "error",
            "message": f"Error processing file: {str(e)}",
            "debug": f"Exception: {e}",
        }


async def upload_file(file_content: bytes, filename: str, username: str) -> dict:
    """Upload a file and save it to the user's directory."""
    try:
        # Create user directory
        user_dir = os.path.join(CHAT_DATA_PATH, username, "uploads")
        os.makedirs(user_dir, exist_ok=True)

        # Generate unique filename
        unique_filename = generateUniqueFilename(
            "upload", username, os.path.splitext(filename)[1]
        )
        file_path = os.path.join(user_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Get file info
        file_size = len(file_content)
        file_type = await detectFileType_async(file_path)

        logger.info(
            f"File uploaded: {filename} -> {unique_filename} ({file_size} bytes)"
        )

        return {
            "original_name": filename,
            "saved_name": unique_filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_type": file_type,
            "upload_time": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in upload_file: {e}")
        return {"error": str(e)}


async def data_classification(content: str) -> dict:
    """Classify the content of a text file."""
    try:
        # Get classification functions lazily
        classification_funcs = get_classification()
        if not classification_funcs:
            return {"error": "Classification functions not available"}

        # Perform classification
        result = classification_funcs.classify_text(content)

        return {
            "classification": result,
            "content_length": len(content),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in data_classification: {e}")
        return {"error": str(e)}


async def process_zip_file(file_content: bytes, filename: str, username: str) -> dict:
    """Process a ZIP file and extract its contents."""
    try:
        # Create temporary directory for extraction
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Save ZIP file temporarily
            zip_path = os.path.join(temp_dir, filename)
            with open(zip_path, "wb") as f:
                f.write(file_content)

            # Extract ZIP file
            extracted_files = []
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

                # Process extracted files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file != filename:  # Skip the original ZIP file
                            file_path = os.path.join(root, file)

                            # Read file content
                            try:
                                with open(file_path, "rb") as f:
                                    content = f.read()

                                # Try to decode as text
                                try:
                                    text_content = content.decode("utf-8")
                                    file_type = "text"
                                except UnicodeDecodeError:
                                    text_content = None
                                    file_type = "binary"

                                extracted_files.append(
                                    {
                                        "name": file,
                                        "path": file_path,
                                        "size": len(content),
                                        "type": file_type,
                                        "content": text_content,
                                    }
                                )

                            except Exception as e:
                                logger.error(
                                    f"Error reading extracted file {file}: {e}"
                                )
                                continue

            return {
                "original_zip": filename,
                "extracted_files": extracted_files,
                "total_files": len(extracted_files),
                "processed_at": get_utc_timestamp(),
            }

    except Exception as e:
        logger.error(f"Error in process_zip_file: {e}")
        return {"error": str(e)}


def generateUniqueFilename(prefix: str, username: str, extension: str) -> str:
    """Generate a unique filename for uploaded files."""
    try:
        # Use Singapore timezone for filename generation
        from .timezone_utils import now_singapore

        timestamp = now_singapore().strftime("%Y%m%d_%H%M%S")
        unique_id = f"{prefix}_{username}_{timestamp}"

        # Clean extension
        if not extension.startswith("."):
            extension = "." + extension

        return f"{unique_id}{extension}"

    except Exception as e:
        logger.error(f"Error in generateUniqueFilename: {e}")
        from .timezone_utils import now_singapore

        return f"{prefix}_{int(now_singapore().timestamp())}{extension}"
