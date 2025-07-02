#!/usr/bin/env python3
"""Enhanced content extraction using pandoc and tesseract OCR for better file processing."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import shutil
import concurrent.futures
import re

# Set up logging
logger = logging.getLogger(__name__)

CHUNK_LINE_THRESHOLD = 100  # lines
CHUNK_CHAR_THRESHOLD = 1000  # characters
MAX_WORKERS = 4


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
    """Escape all lines that are exactly '---', '___', or '***' (optionally with whitespace) by prefixing them with a backslash, throughout the entire file. This prevents Pandoc from interpreting them as YAML delimiters or horizontal rules."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    escaped_lines = []
    pattern = re.compile(r"^\s*(---|___|\*\*\*)\s*$")
    num_escaped = 0
    for line in lines:
        if pattern.match(line):
            escaped_lines.append("\\" + line if not line.startswith("\\") else line)
            num_escaped += 1
        else:
            escaped_lines.append(line)
    if num_escaped > 0:
        logger.info(
            f"Escaped {num_escaped} horizontal rule/YAML delimiter lines in markdown for Pandoc safety: {md_path}"
        )
    # Write to a temp file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".md", mode="w", encoding="utf-8"
    ) as tmp:
        tmp.writelines(escaped_lines)
        return tmp.name


def split_markdown_chunks(md_path: str) -> list:
    """Split markdown file into chunks by top-level headings or by lines if not structured."""
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Try to split by top-level headings
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
    # If only one chunk, fallback to splitting by lines
    if len(chunks) == 1 and len(lines) > CHUNK_LINE_THRESHOLD:
        chunks = []
        for i in range(0, len(lines), CHUNK_LINE_THRESHOLD):
            chunks.append("".join(lines[i : i + CHUNK_LINE_THRESHOLD]))
    return chunks


def parallel_pandoc_chunks(md_path: str, input_format: str) -> str:
    """Process markdown chunks in parallel with pandoc and concatenate results."""
    chunks = split_markdown_chunks(md_path)
    results = [None] * len(chunks)

    def process_chunk(idx_chunk):
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
    """Process markdown chunks in parallel as plain text and concatenate results."""
    chunks = split_markdown_chunks(md_path)
    results = [None] * len(chunks)

    def process_chunk(idx_chunk):
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
    Extract text content using pandoc.

    :param file_path: Path to the file to extract content from
    :type file_path: str
    :param pre_stripped_temp: Optional path to a YAML-stripped temp file for markdown
    :type pre_stripped_temp: Optional[str]
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
        file_to_use = file_path
        if file_ext in {".md", ".markdown"}:
            # Always strip YAML before any extraction
            temp_path = strip_yaml_front_matter(file_path)
            file_to_use = temp_path
            # If large, chunk and parallelize
            with open(file_to_use, "r", encoding="utf-8") as f:
                content = f.read()
            if (
                len(content) > CHUNK_CHAR_THRESHOLD
                or content.count("\n") > CHUNK_LINE_THRESHOLD
            ):
                result = parallel_pandoc_chunks(file_to_use, input_format)
                os.unlink(temp_path)
                return result

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
                    f"Falling back to plain text extraction for markdown file: {file_path} (YAML stripped)"
                )
                return extract_text_file_content(
                    file_path, pre_stripped_temp=file_to_use
                )

    except Exception as e:
        logger.error(f"Error in pandoc extraction for {file_path}: {e}")
        # Fallback for markdown: try plain text extraction
        if Path(file_path).suffix.lower() in {".md", ".markdown"}:
            logger.info(
                f"Falling back to plain text extraction for markdown file: {file_path} (YAML stripped)"
            )
            return extract_text_file_content(file_path, pre_stripped_temp=file_to_use)

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


def extract_text_file_content(
    file_path: str, pre_stripped_temp: Optional[str] = None
) -> Optional[str]:
    """
    Extract content from plain text files.

    :param file_path: Path to the text file to extract content from
    :type file_path: str
    :param pre_stripped_temp: Optional path to a YAML-stripped temp file for markdown
    :type pre_stripped_temp: Optional[str]
    :return: Extracted text content or None if extraction failed
    :rtype: Optional[str]
    """
    try:
        file_ext = Path(file_path).suffix.lower()
        text_formats = {".txt", ".csv", ".log", ".md", ".markdown"}

        if file_ext not in text_formats:
            return None

        target_path = (
            pre_stripped_temp
            if pre_stripped_temp and file_ext in {".md", ".markdown"}
            else file_path
        )
        # Read up to 100 lines or 1000 characters, whichever is more
        max_lines = CHUNK_LINE_THRESHOLD
        min_chars = CHUNK_CHAR_THRESHOLD
        content_lines = []
        char_count = 0
        with open(target_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                content_lines.append(line)
                char_count += len(line)
                # If we've reached both thresholds, break
                if i + 1 >= max_lines and char_count >= min_chars:
                    break
            # If we hit 100 lines but not 1000 chars, keep reading until 1000 chars
            while char_count < min_chars:
                next_line = f.readline()
                if not next_line:
                    break
                content_lines.append(next_line)
                char_count += len(next_line)
            # If we hit 1000 chars but not 100 lines, keep reading until 100 lines
            while len(content_lines) < max_lines:
                next_line = f.readline()
                if not next_line:
                    break
                content_lines.append(next_line)
                char_count += len(next_line)
        content = "".join(content_lines)
        return content
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
    finally:
        # Clean up temp file if used
        if (
            pre_stripped_temp
            and pre_stripped_temp != file_path
            and file_ext in {".md", ".markdown"}
        ):
            try:
                os.unlink(pre_stripped_temp)
            except Exception:
                pass
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
    pre_stripped_temp = None
    try:
        # For markdown, pre-strip YAML and use temp file for all extraction attempts
        if file_ext in {".md", ".markdown"}:
            pre_stripped_temp = strip_yaml_front_matter(file_path)

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
            extraction_methods.append(
                (
                    "pandoc",
                    lambda fp: extract_with_pandoc(
                        fp, pre_stripped_temp=pre_stripped_temp
                    ),
                )
            )
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
                if file_ext in {".md", ".markdown"} and method_name != "pandoc":
                    content = extract_text_file_content(
                        file_path, pre_stripped_temp=pre_stripped_temp
                    )
                else:
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
    finally:
        # Clean up temp file if used
        if pre_stripped_temp and os.path.exists(pre_stripped_temp):
            try:
                os.unlink(pre_stripped_temp)
            except Exception:
                pass

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


def classify_file_content(content: str, username: Optional[str]) -> Dict[str, Any]:
    """
    Classify the extracted file content with enhanced error handling, request counting, and caching.
    Shared utility for file classification.

    :param content: The text content to classify
    :type content: str
    :param username: Optional username for per-user request counting
    :type username: Optional[str]
    :return: Dictionary containing classification results
    :rtype: Dict[str, Any]
    """
    from performance_utils import perf_monitor, cache_manager
    import json
    import hashlib

    # Use a per-user request counter
    if not hasattr(classify_file_content, "classification_request_counts"):
        classify_file_content.classification_request_counts = {}
    classification_request_counts = classify_file_content.classification_request_counts
    if not content or not content.strip():
        return {
            "classification": "Unknown",
            "sensitivity": "Unknown",
            "reasoning": "No content available for classification",
            "confidence": 0.0,
        }
    # Hash the content for caching
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    cache = cache_manager.get_cache("classification_results")
    if content_hash in cache:
        result = cache[content_hash]
        result = result.copy()  # Avoid mutating cached result
        result["cached"] = True
        return result
    # Per-user request counting
    user_key = username or "__global__"
    if user_key not in classification_request_counts:
        classification_request_counts[user_key] = 0
    classification_request_counts[user_key] += 1
    print(
        f"[INFO] File classification requests for '{user_key}': {classification_request_counts[user_key]}"
    )
    try:
        perf_monitor.start_timer("classification_llm_call")
        from llm.classificationModel import classify_text

        result = classify_text(content)
        perf_monitor.end_timer("classification_llm_call")
        # Extract the answer which should be JSON
        answer = result.get("answer", "{}")
        try:
            if isinstance(answer, str):
                classification_result = json.loads(answer)
            else:
                classification_result = answer
            if "classification" not in classification_result:
                classification_result["classification"] = "Official(Open)"
            if "sensitivity" not in classification_result:
                classification_result["sensitivity"] = "Non-Sensitive"
            if "reasoning" not in classification_result:
                classification_result["reasoning"] = (
                    "Classification completed successfully"
                )
            if "confidence" not in classification_result:
                classification_result["confidence"] = 0.8
        except json.JSONDecodeError:
            classification_result = {
                "classification": "Official(Open)",
                "sensitivity": "Non-Sensitive",
                "reasoning": f"Classification completed. Raw response: {answer}",
                "confidence": 0.5,
            }
        # Cache the result
        cache[content_hash] = classification_result.copy()
        return classification_result
    except Exception as e:
        return {
            "classification": "Error",
            "sensitivity": "Error",
            "reasoning": f"Classification failed: {str(e)}",
            "confidence": 0.0,
        }
