"""
Enhanced Content Extraction Module for NYP FYP Chatbot

This module provides advanced file content extraction, cleaning, and keyword filtering utilities for the chatbot's file classification and search features. It supports parallel processing, integration with LLM keyword cache, and robust handling of various file types.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional  # noqa: F401
import logging
import shutil
import concurrent.futures
import re

# Import keyword filtering functionality
try:
    from llm.keyword_cache import filter_filler_words
except ImportError:
    # Fallback if keyword_cache is not available
    def filter_filler_words(text: str) -> str:
        """Remove filler/stop words from text using the keyword cache implementation."""
        try:
            from llm.keyword_cache import filter_filler_words as keyword_filter

            return keyword_filter(text)
        except ImportError:
            # Fallback if keyword_cache is not available
            return text


# Import the main implementation to avoid duplication
try:
    from llm.classificationModel import clean_text_for_classification
except ImportError:
    # Fallback implementation if the main module is not available
    def clean_text_for_classification(text: str) -> str:
        """
        Applies comprehensive cleaning to text to remove redundant symbols,
        markdown, and numerical prefixes, making it suitable for classification.
        """
        if not isinstance(text, str):
            text = str(text)  # Ensure it's a string

        # Remove common Markdown headings: e.g., "## Header", "# Title"
        text = re.sub(r"^\s*#+\s*.*$", "", text, flags=re.MULTILINE)
        # Remove horizontal rules: "---", "***"
        text = re.sub(r"^\s*[-*]+\s*$", "", text, flags=re.MULTILINE)
        # Remove list indicators: "1. ", "2. ", "- ", "* "
        text = re.sub(r"^\s*((\d+\.)|[-*])\s+", "", text, flags=re.MULTILINE)
        # Remove redundant spaces and newlines
        text = re.sub(r"\s+", " ", text).strip()
        # Remove any remaining leading/trailing punctuation that might occur after cleaning
        text = re.sub(r"^[.,!?;:()\"']+|[.,!?;:()\"']+$", "", text).strip()
        return text


# Set up logging
logger = logging.getLogger(__name__)

# CHUNK_CHAR_THRESHOLD now actively limits text file reads to the first 20000 characters.
CHUNK_CHAR_THRESHOLD = 20000  # characters
CLASSIFICATION_WORD_LIMIT = 10  # New constant for classification input word limit
MAX_WORKERS = 8


def escape_special_characters(text: str) -> str:
    """
    Escape special characters that might cause issues in text processing.

    This function removes control characters and extended ASCII characters
    that could cause problems in text processing while preserving normal
    text content, punctuation, and symbols.

    :param text: The text to escape special characters from.
    :type text: str
    :return: The text with problematic characters removed.
    :rtype: str
    """
    if not text:
        return text

    # Remove control characters (0x00-0x1F) except newlines and tabs
    # Remove extended ASCII characters (0x7F-0xFF) that might cause issues
    cleaned = ""
    for char in text:
        char_code = ord(char)
        # Keep printable ASCII (32-126), newlines (10, 13), and tabs (9)
        if (32 <= char_code <= 126) or char_code in [9, 10, 13]:
            cleaned += char
        # Keep Unicode characters above ASCII range
        elif char_code > 127:
            cleaned += char
        # Remove control characters and extended ASCII
        else:
            cleaned += " "

    return cleaned


def find_tool(tool_name: str) -> Optional[str]:
    """
    Find the path to a tool executable.

    :param tool_name: Name of the tool to find.
    :type tool_name: str
    :return: Path to the tool executable or None if not found.
    :rtype: Optional[str]
    """
    if os.getenv("IN_DOCKER", "false").lower() in ("1", "true"):
        path = shutil.which(tool_name)
        if path:
            return path
        return None
    home = os.path.expanduser("~")
    local_path = os.path.join(
        home, ".nypai-chatbot", "data", "dependencies", tool_name, "bin", tool_name
    )
    if os.path.exists(local_path):
        return local_path
    return shutil.which(tool_name)


def apply_text_processing(content: str, file_ext: str) -> str:
    """
    Applies text cleaning and filler word filtering to extracted content.

    :param content: The text content to process.
    :type content: str
    :param file_ext: File extension for logging purposes.
    :type file_ext: str
    :return: Processed text content with cleaning and filtering applied.
    :rtype: str
    """
    # This function should apply to any text content that has been extracted,
    # regardless of whether the original file was text-based or binary.

    # First, perform robust cleaning for redundant symbols
    cleaned_content = clean_text_for_classification(content)

    # Then, apply filler word filtering
    filtered_content = filter_filler_words(cleaned_content)

    logger.info(
        f"Applied text processing for '{file_ext}' file: special character cleaning and keyword filtering"
    )
    return filtered_content


def split_markdown_chunks(md_path: str) -> list:
    """
    Splits markdown file into chunks based on headers.

    :param md_path: Path to the markdown file.
    :type md_path: str
    :return: List of markdown chunks.
    :rtype: list
    """
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    chunks = []
    current_chunk = []
    for line in lines:
        if line.startswith("# "):
            if current_chunk:
                chunks.append("".join(current_chunk))
            current_chunk = []
        current_chunk.append(line)
    if current_chunk:
        chunks.append("".join(current_chunk))
    return chunks


def parallel_pandoc_chunks(md_path: str, input_format: str) -> str:
    """
    Processes markdown chunks in parallel using Pandoc.

    :param md_path: Path to the markdown file.
    :type md_path: str
    :param input_format: Input format for Pandoc.
    :type input_format: str
    :return: Processed text content.
    :rtype: str
    """
    chunks = split_markdown_chunks(md_path)
    results = [None] * len(chunks)

    def process_chunk(idx_chunk) -> tuple[int, str]:
        idx, chunk = idx_chunk
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".md", mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(chunk)
            tmp_path = tmp.name
        try:
            pandoc_path = find_tool("pandoc")
            cmd = [
                pandoc_path,
                "-f",
                input_format,
                "-t",
                "plain",
                "--wrap=none",
                tmp_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return (idx, result.stdout.strip())
            else:
                logger.warning(f"Pandoc chunk extraction failed: {result.stderr}")
                return (idx, "")
        finally:
            os.unlink(tmp_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for idx, content in executor.map(process_chunk, enumerate(chunks)):
            results[idx] = content
    return "\n\n".join(results)


def parallel_plaintext_chunks(md_path: str) -> str:
    """
    Processes markdown chunks in parallel as plain text.

    :param md_path: Path to the markdown file.
    :type md_path: str
    :return: Processed text content.
    :rtype: str
    """
    chunks = split_markdown_chunks(md_path)
    results = [None] * len(chunks)

    def process_chunk(idx_chunk) -> tuple[int, str]:
        idx, chunk = idx_chunk
        return (idx, chunk.strip())

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for idx, content in executor.map(process_chunk, enumerate(chunks)):
            results[idx] = content
    return "\n\n".join(results)


def extract_with_pandoc(
    file_path: str, pre_stripped_temp: Optional[str] = None
) -> Optional[str]:
    """
    Extracts content using Pandoc for various document types.

    :param file_path: Path to the file to extract content from.
    :type file_path: str
    :param pre_stripped_temp: Optional pre-stripped temporary file path.
    :type pre_stripped_temp: Optional[str]
    :return: Extracted text content or None if extraction fails.
    :rtype: Optional[str]
    """
    try:
        pandoc_path = find_tool("pandoc")
        if not pandoc_path:
            logger.warning("Pandoc is not installed or not in PATH.")
            return None
        file_ext = Path(file_path).suffix.lower()
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
            ".pdf": "pdf",
            ".txt": "markdown",
            ".csv": "markdown",
            ".log": "markdown",
        }
        if file_ext not in pandoc_formats:
            return None
        input_format = pandoc_formats[file_ext]
        temp_path = None
        file_to_use = file_path

        # For text-based files processed by Pandoc, read the full content,
        # apply initial text processing, then pass to Pandoc via a temp file.
        if file_ext in {".txt", ".md", ".markdown", ".csv", ".log", ".html", ".htm"}:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()  # Read full content here for Pandoc processing
            processed_content = apply_text_processing(content, file_ext)  # Apply here
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=file_ext, mode="w", encoding="utf-8"
            )
            tmp.write(processed_content)
            tmp.close()
            temp_path = tmp.name
            file_to_use = temp_path

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
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass  # Already logged warning if it fails in finally block
        if result.returncode == 0:
            content = result.stdout.strip()
            if content:
                logger.info(
                    f"Successfully extracted content using pandoc from {file_path}"
                )
                # Apply text processing again to the output of pandoc for consistency
                return apply_text_processing(content, file_ext)  # Apply again here
            else:
                logger.warning(f"Pandoc extracted empty content for {file_path}")
                return None
        else:
            logger.warning(f"Pandoc extraction failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Error extracting with pandoc: {e}")
        return None


def extract_with_tesseract(file_path: str) -> Optional[str]:
    """Extracts text from images using Tesseract OCR."""
    try:
        tesseract_path = find_tool("tesseract")
        if not tesseract_path:
            logger.warning("Tesseract is not installed or not in PATH.")
            return None
        file_ext = Path(file_path).suffix.lower()
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
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_output:
            output_path = tmp_output.name
        try:
            output_base = output_path[:-4]
            cmd = [tesseract_path, file_path, output_base, "-l", "eng"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                if os.path.exists(output_path):
                    with open(output_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        logger.info(
                            f"Successfully extracted text using tesseract from {file_path}"
                        )
                        return apply_text_processing(content, file_ext)
                    else:
                        logger.warning(
                            f"Tesseract extracted empty content for {file_path}"
                        )
                        return None
            else:
                logger.warning(f"Tesseract OCR failed for {file_path}: {result.stderr}")
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    except Exception as e:
        logger.error(f"Error in tesseract OCR for {file_path}: {e}")
    return None


def extract_pdf_content(file_path: str) -> Optional[str]:
    """Extracts content from PDF files, trying Pandoc first, then fallback."""
    try:
        content = extract_with_pandoc(file_path)
        if content:
            return content
        try:
            from llm.dataProcessing import ExtractText

            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    logger.info(
                        f"Successfully extracted PDF content using fallback method from {file_path}"
                    )
                    # DO NOT apply apply_text_processing for PDFs!
                    return content  # Just return the raw extracted content
        except Exception as e:
            logger.warning(f"Fallback PDF extraction failed for {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error in PDF content extraction for {file_path}: {e}")
    return None


def extract_text_file_content(
    file_path: str, pre_stripped_temp: Optional[str] = None
) -> Optional[str]:
    """
    Extracts content from text-based files, limited to the first CHUNK_CHAR_THRESHOLD characters.
    If the file is shorter than the threshold, the entire content is extracted.
    """
    try:
        file_ext = Path(file_path).suffix.lower()
        text_formats = {".txt", ".csv", ".log", ".md", ".markdown"}
        if file_ext not in text_formats:
            return None

        content_chars = []
        char_count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            while char_count < CHUNK_CHAR_THRESHOLD:  # Loop until 20000 chars or EOF
                next_line = f.readline()
                if not next_line:
                    break  # End of file

                remaining_chars = CHUNK_CHAR_THRESHOLD - char_count
                if len(next_line) > remaining_chars:
                    content_chars.append(next_line[:remaining_chars])
                    char_count += remaining_chars
                    break  # Reached limit within this line
                else:
                    content_chars.append(next_line)
                    char_count += len(next_line)

        content = "".join(content_chars)
        processed_content = apply_text_processing(content, file_ext)
        if len(content) < CHUNK_CHAR_THRESHOLD:
            logger.info(
                f"Successfully extracted full text content (less than {CHUNK_CHAR_THRESHOLD} chars) from {file_path}"
            )
        else:
            logger.info(
                f"Successfully extracted first {CHUNK_CHAR_THRESHOLD} characters from text file {file_path}"
            )
        return processed_content
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return None
    finally:
        pass


def enhanced_extract_file_content(file_path: str) -> Dict[str, Any]:
    """Main function to extract content from various file types."""
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
    extraction_methods = []

    try:
        # Prioritize specific extractors
        if file_ext == ".pdf":
            extraction_methods.append(("pdf_extraction", extract_pdf_content))
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
        elif file_ext in {
            ".docx",
            ".doc",
            ".odt",
            ".rtf",
            ".html",
            ".htm",
            ".epub",
            ".pptx",
            ".ppt",  # Added pptx/ppt here, as they're also handled by pandoc
        }:
            extraction_methods.append(("pandoc", extract_with_pandoc))
        elif file_ext in {".xlsx", ".xls"}:
            extraction_methods.append(
                ("excel_placeholder", lambda _: None)
            )  # Placeholder for Excel

        # Handle Markdown and direct text files: Prioritize extract_text_file_content
        # as it aligns with the user's explicit request for 20000 char limit for these.
        if file_ext in {".txt", ".csv", ".log", ".md", ".markdown"}:
            # Add at the beginning of the list to prioritize, then fallback to pandoc if applicable
            extraction_methods.insert(0, ("text_file", extract_text_file_content))
            # Also ensure pandoc is a fallback for markdown if the simple text read fails/is undesirable for some reason
            if file_ext in {".md", ".markdown"}:
                # Ensure pandoc is also available as a fallback for markdown, but after plain text
                extraction_methods.insert(1, ("pandoc", extract_with_pandoc))

        # General fallback: Try to read any file as a plain text file if no other method worked
        # This will also respect the 20000 character limit due to extract_text_file_content's current logic.
        extraction_methods.append(("generic_text_fallback", extract_text_file_content))

        for method_name, method_func in extraction_methods:
            result["extraction_methods_tried"].append(method_name)
            try:
                content = method_func(
                    file_path
                )  # No need for pre_stripped_temp here, handled internally.
                if content and content.strip():
                    result["content"] = content.strip()
                    result["method"] = method_name
                    break
            except Exception as e:
                logger.warning(
                    f"Extraction method {method_name} failed for {file_path}: {e}"
                )
                continue
    finally:
        pass  # No global temp file cleanup needed here due to internal handling

    # Existing fallback for non-PDF files using llm.dataProcessing.ExtractText (if no content yet)
    # Note: This fallback is *not* character limited by CHUNK_CHAR_THRESHOLD, as it uses ExtractText.
    if not result["content"] and file_ext != ".pdf":
        result["extraction_methods_tried"].append("fallback_original")
        try:
            from llm.dataProcessing import ExtractText

            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    result["content"] = apply_text_processing(content, file_ext).strip()
                    result["method"] = "fallback_original"
        except Exception as e:
            result["error"] = f"All extraction methods failed. Last error: {str(e)}"

    if not result["content"]:
        result["error"] = (
            result["error"] or "No content could be extracted from the file"
        )
    # Refine error messages if specific tools are missing
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
