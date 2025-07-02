#!/usr/bin/env python3
"""Enhanced content extraction using pandoc and tesseract OCR for better file processing."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import shutil

# Set up logging
logger = logging.getLogger(__name__)


def find_tool(tool_name: str) -> Optional[str]:
    # Prefer system PATH in Docker
    if os.getenv("IN_DOCKER", "false").lower() in ("1", "true"):
        path = shutil.which(tool_name)
        if path:
            return path
    # Optionally, check local dependencies for non-Docker
    home = os.path.expanduser("~")
    local_path = os.path.join(
        home, ".nypai-chatbot", "data", "dependencies", tool_name, "bin", tool_name
    )
    if os.path.exists(local_path):
        return local_path
    # Fallback to PATH
    return shutil.which(tool_name)


def strip_yaml_front_matter(md_path: str) -> str:
    """Remove YAML front matter from a markdown file and return the path to a temp file without it.
    Strips the first YAML block (--- ... ---) found within the first 50 lines, even if not at the very top.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    in_yaml = False
    yaml_found = False
    for i, line in enumerate(lines):
        if not yaml_found and line.strip() == "---":
            in_yaml = True
            yaml_found = True
            continue
        if in_yaml and line.strip() == "---":
            in_yaml = False
            continue
        if not in_yaml:
            new_lines.append(line)
        # Only look for YAML in the first 50 lines
        if i > 50 and not yaml_found:
            new_lines = lines  # fallback: don't strip if not found early
            break
    content_no_yaml = "".join(new_lines)
    # Write to a temp file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".md", mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(content_no_yaml)
        return tmp.name


def extract_with_pandoc(file_path: str) -> Optional[str]:
    """Extract text content using pandoc.

    :param file_path: Path to the file to extract content from
    :type file_path: str
    :return: Extracted text content or None if extraction failed
    :rtype: Optional[str]
    """
    try:
        pandoc_path = find_tool("pandoc")
        if not pandoc_path:
            logger.warning("Pandoc is not installed or not in PATH.")
            return None
        file_ext = Path(file_path).suffix.lower()

        # Pandoc supported formats
        pandoc_formats = {
            ".docx": "docx",
            ".doc": "doc",
            ".odt": "odt",
            ".rtf": "rtf",
            ".html": "html",
            ".htm": "html",
            ".epub": "epub",
            ".md": "markdown",
            ".markdown": "markdown",
        }

        if file_ext not in pandoc_formats:
            return None

        input_format = pandoc_formats[file_ext]

        # For markdown, strip YAML front matter to avoid pandoc YAML parse errors
        temp_path = None
        if file_ext in {".md", ".markdown"}:
            temp_path = strip_yaml_front_matter(file_path)
            file_to_use = temp_path
        else:
            file_to_use = file_path

        # Use pandoc to convert to plain text
        cmd = [
            pandoc_path,
            "-f",
            input_format,
            "-t",
            "plain",
            "--wrap=none",
            file_to_use,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Clean up temp file if used
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

        if result.returncode == 0:
            content = result.stdout.strip()
            if content:
                logger.info(
                    f"Successfully extracted content using pandoc from {file_path}"
                )
                return content
        else:
            logger.warning(f"Pandoc extraction failed for {file_path}: {result.stderr}")
            # Fallback for markdown: try plain text extraction
            if file_ext in {".md", ".markdown"}:
                logger.info(
                    f"Falling back to plain text extraction for markdown file: {file_path}"
                )
                return extract_text_file_content(file_path)

    except Exception as e:
        logger.error(f"Error in pandoc extraction for {file_path}: {e}")
        # Fallback for markdown: try plain text extraction
        if Path(file_path).suffix.lower() in {".md", ".markdown"}:
            logger.info(
                f"Falling back to plain text extraction for markdown file: {file_path}"
            )
            return extract_text_file_content(file_path)

    return None


def extract_with_tesseract(file_path: str) -> Optional[str]:
    """Extract text from images using tesseract OCR.

    :param file_path: Path to the image file to extract text from
    :type file_path: str
    :return: Extracted text content or None if extraction failed
    :rtype: Optional[str]
    """
    try:
        tesseract_path = find_tool("tesseract")
        if not tesseract_path:
            logger.warning("Tesseract is not installed or not in PATH.")
            return None
        file_ext = Path(file_path).suffix.lower()

        # Image formats supported by tesseract
        image_formats = {
            ".png",
            ".jpg",
            ".jpeg",
            ".tiff",
            ".tif",
            ".bmp",
            ".gif",
            ".webp",
        }

        if file_ext not in image_formats:
            return None

        # Use tesseract to extract text
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_output:
            output_path = tmp_output.name

        try:
            # Remove the .txt extension as tesseract adds it automatically
            output_base = output_path[:-4]

            cmd = [tesseract_path, file_path, output_base, "-l", "eng"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # Read the output file
                if os.path.exists(output_path):
                    with open(output_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()

                    if content:
                        logger.info(
                            f"Successfully extracted text using tesseract from {file_path}"
                        )
                        return content
            else:
                logger.warning(f"Tesseract OCR failed for {file_path}: {result.stderr}")

        finally:
            # Clean up temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)

    except Exception as e:
        logger.error(f"Error in tesseract OCR for {file_path}: {e}")

    return None


def extract_pdf_content(file_path: str) -> Optional[str]:
    """Extract content from PDF files using multiple methods.

    :param file_path: Path to the PDF file to extract content from
    :type file_path: str
    :return: Extracted text content or None if extraction failed
    :rtype: Optional[str]
    """
    try:
        # Try pandoc first for PDF
        content = extract_with_pandoc(file_path)
        if content:
            return content

        # Fallback to existing PDF extraction methods
        try:
            from llm.dataProcessing import ExtractText

            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    logger.info(
                        f"Successfully extracted PDF content using fallback method from {file_path}"
                    )
                    return content
        except Exception as e:
            logger.warning(f"Fallback PDF extraction failed for {file_path}: {e}")

    except Exception as e:
        logger.error(f"Error in PDF content extraction for {file_path}: {e}")

    return None


def extract_text_file_content(file_path: str) -> Optional[str]:
    """Extract content from plain text files.

    :param file_path: Path to the text file to extract content from
    :type file_path: str
    :return: Extracted text content or None if extraction failed
    :rtype: Optional[str]
    """
    try:
        file_ext = Path(file_path).suffix.lower()
        text_formats = {".txt", ".csv", ".log", ".md", ".markdown"}

        if file_ext not in text_formats:
            return None

        # Try different encodings
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read().strip()
                if content:
                    logger.info(
                        f"Successfully read text file {file_path} with encoding {encoding}"
                    )
                    return content
            except UnicodeDecodeError:
                continue

        logger.warning(
            f"Could not decode text file {file_path} with any supported encoding"
        )

    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")

    return None


def enhanced_extract_file_content(file_path: str) -> Dict[str, Any]:
    """Enhanced file content extraction with multiple methods and detailed results.

    :param file_path: Path to the file to extract content from
    :type file_path: str
    :return: Dictionary containing extracted content, method used, and metadata
    :rtype: Dict[str, Any]
    """
    if not os.path.exists(file_path):
        return {
            "content": "",
            "method": "error",
            "error": f"File not found: {file_path}",
            "file_size": 0,
            "file_type": "unknown",
        }

    file_ext = Path(file_path).suffix.lower()
    file_size = os.path.getsize(file_path)

    result = {
        "content": "",
        "method": "none",
        "error": None,
        "file_size": file_size,
        "file_type": file_ext,
        "extraction_methods_tried": [],
    }

    # Try different extraction methods based on file type
    extraction_methods = []

    # PDF files
    if file_ext == ".pdf":
        extraction_methods.append(("pdf_extraction", extract_pdf_content))

    # Image files (OCR)
    elif file_ext in {
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".tif",
        ".bmp",
        ".gif",
        ".webp",
    }:
        extraction_methods.append(("tesseract_ocr", extract_with_tesseract))

    # Document files
    elif file_ext in {
        ".docx",
        ".doc",
        ".odt",
        ".rtf",
        ".html",
        ".htm",
        ".epub",
        ".md",
        ".markdown",
    }:
        extraction_methods.append(("pandoc", extract_with_pandoc))

    # Text files
    elif file_ext in {".txt", ".csv", ".log"}:
        extraction_methods.append(("text_file", extract_text_file_content))

    # Excel files
    elif file_ext in {".xlsx", ".xls"}:
        extraction_methods.append(("excel_fallback", lambda _: None))  # Placeholder

    # PowerPoint files
    elif file_ext in {".pptx", ".ppt"}:
        extraction_methods.append(("pandoc", extract_with_pandoc))

    # Try extraction methods
    for method_name, method_func in extraction_methods:
        result["extraction_methods_tried"].append(method_name)
        try:
            content = method_func(file_path)
            if content and content.strip():
                result["content"] = content.strip()
                result["method"] = method_name
                break
        except Exception as e:
            logger.warning(
                f"Extraction method {method_name} failed for {file_path}: {e}"
            )
            continue

    # Fallback to original method if nothing worked
    if not result["content"] and file_ext != ".pdf":  # Avoid double PDF processing
        result["extraction_methods_tried"].append("fallback_original")
        try:
            from llm.dataProcessing import ExtractText

            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    result["content"] = content.strip()
                    result["method"] = "fallback_original"
        except Exception as e:
            result["error"] = f"All extraction methods failed. Last error: {str(e)}"

    if not result["content"]:
        result["error"] = (
            result["error"] or "No content could be extracted from the file"
        )

    # After all extraction attempts, if a required tool was missing, set error
    if not result["content"]:
        if result["method"] == "pandoc" and shutil.which("pandoc") is None:
            result["error"] = (
                "Pandoc is not installed or not in PATH. Please install pandoc for document conversion."
            )
        elif result["method"] == "tesseract_ocr" and shutil.which("tesseract") is None:
            result["error"] = (
                "Tesseract is not installed or not in PATH. Please install tesseract-ocr for OCR."
            )

    return result
