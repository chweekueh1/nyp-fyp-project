import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import shutil
import concurrent.futures
import re
import collections
import hashlib
import json

# Import keyword filtering functionality
try:
    from llm.keyword_cache import filter_filler_words
except ImportError:
    # Fallback if keyword_cache is not available
    def filter_filler_words(text: str) -> str:
        return text


# Set up logging
logger = logging.getLogger(__name__)

# CHUNK_CHAR_THRESHOLD now actively limits text file reads to the first 1000 characters.
CHUNK_CHAR_THRESHOLD = 1000  # characters
CLASSIFICATION_WORD_LIMIT = 20  # New constant for classification input word limit
MAX_WORKERS = 8


def find_tool(tool_name: str) -> Optional[str]:
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


def escape_special_characters(text: str) -> str:
    return re.sub(r"[^\w\s\n.,!?;:()\"'\-_+=<>[\]{}|\\/@#$%^&*~`]", " ", text)


def apply_text_processing(content: str, file_ext: str) -> str:
    """Applies text cleaning and filler word filtering to extracted content."""
    # This function should apply to any text content that has been extracted,
    # regardless of whether the original file was text-based or binary.
    cleaned_content = escape_special_characters(content)
    filtered_content = filter_filler_words(cleaned_content)
    logger.info(
        f"Applied text processing for '{file_ext}' file: special character cleaning and keyword filtering"
    )
    return filtered_content


def split_markdown_chunks(md_path: str) -> list:
    """Splits markdown file into chunks based on headers."""
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
    """Processes markdown chunks in parallel using Pandoc."""
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
    """Processes markdown chunks in parallel as plain text."""
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
    """Extracts content using Pandoc for various document types."""
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
            processed_content = apply_text_processing(content, file_ext)
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
                return apply_text_processing(content, file_ext)
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
                    return apply_text_processing(
                        content, Path(file_path).suffix.lower()
                    )
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
            while char_count < CHUNK_CHAR_THRESHOLD:  # Loop until 1000 chars or EOF
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
        # as it aligns with the user's explicit request for 1000 char limit for these.
        if file_ext in {".txt", ".csv", ".log", ".md", ".markdown"}:
            # Add at the beginning of the list to prioritize, then fallback to pandoc if applicable
            extraction_methods.insert(0, ("text_file", extract_text_file_content))
            # Also ensure pandoc is a fallback for markdown if the simple text read fails/is undesirable for some reason
            if file_ext in {".md", ".markdown"}:
                # Ensure pandoc is also available as a fallback for markdown, but after plain text
                extraction_methods.insert(1, ("pandoc", extract_with_pandoc))

        # General fallback: Try to read any file as a plain text file if no other method worked
        # This will also respect the 1000 character limit due to extract_text_file_content's current logic.
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


def classify_file_content(content: str, username: Optional[str]) -> Dict[str, Any]:
    """Classifies file content based on keywords and sends a concise summary to LLM."""
    from performance_utils import perf_monitor, cache_manager
    import yake

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
    if not isinstance(content, str):
        logger.warning(
            f"classify_file_content: expected string content, got {type(content)}: {content}"
        )
        content = str(content)

    # filter_filler_words should ideally already be applied during content extraction.
    # Keeping it here as a safeguard ensures it's always applied before YAKE/LLM.
    filtered_content = filter_filler_words(content)

    kw_extractor = yake.KeywordExtractor(
        lan="en",
        n=3,
        dedupLim=0.9,
        top=50,
        stopwords=None,
    )
    yake_output = kw_extractor.extract_keywords(filtered_content)

    all_relevant_terms = []
    for keyword, score in yake_output:
        all_relevant_terms.append(keyword.lower())
        for word in keyword.split():
            if len(word) > 2:
                all_relevant_terms.append(word.lower())

    word_counts = collections.Counter(all_relevant_terms)
    top_20_final_terms = [
        w for w, _ in word_counts.most_common(CLASSIFICATION_WORD_LIMIT)
    ]
    top_20_str = ", ".join(top_20_final_terms)

    # --- Create a concise text summary for classification based on word limit ---
    # This will be the primary text sent to the LLM for classification,
    # ensuring it adheres to a strict word count.
    words = filtered_content.split()
    concise_content_for_llm = " ".join(words[:CLASSIFICATION_WORD_LIMIT])

    # If filtered_content was very short, ensure concise_content_for_llm is not empty
    if not concise_content_for_llm and filtered_content.strip():
        concise_content_for_llm = filtered_content.strip()

    # Add a fallback to the raw top_20_str if concise_content_for_llm is empty after processing
    if not concise_content_for_llm and top_20_str:
        concise_content_for_llm = top_20_str
    # Ensure it's not completely empty, if all else fails, use a placeholder
    if not concise_content_for_llm:
        concise_content_for_llm = "No discernable content for classification"

    content_hash = hashlib.sha256(filtered_content.encode("utf-8")).hexdigest()
    cache = cache_manager.get_cache("classification_results")
    if content_hash in cache:
        result = cache[content_hash]
        result = result.copy()
        result["cached"] = True
        return result
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

        # Pass the newly created concise_content_for_llm as the main text
        result = classify_text(text=concise_content_for_llm, keywords=top_20_str)
        perf_monitor.end_timer("classification_llm_call")
        answer = result.get("answer", "{}")
        try:
            if isinstance(answer, str):
                classification_result = json.loads(answer)
            else:
                classification_result = answer
            if not isinstance(classification_result, dict):
                logger.warning(
                    f"classify_file_content: classification_result not dict: {classification_result}"
                )
                classification_result = {
                    "classification": "Unknown",
                    "sensitivity": "Unknown",
                    "reasoning": str(classification_result),
                    "confidence": 0.0,
                }
            if "classification" not in classification_result:
                classification_result["classification"] = "Official(Open)"
            if "sensitivity" not in classification_result or not isinstance(
                classification_result["sensitivity"], str
            ):
                logger.warning(
                    f"classify_file_content: sensitivity not string or missing: {classification_result.get('sensitivity')}"
                )
                classification_result["sensitivity"] = str(
                    classification_result.get("sensitivity", "Non-Sensitive")
                )
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
        cache[content_hash] = classification_result.copy()
        return classification_result
    except Exception as e:
        logger.error(f"classify_file_content: Exception during classification: {e}")
        return {
            "classification": "Error",
            "sensitivity": "Error",
            "reasoning": f"Classification failed: {str(e)}",
            "confidence": 0.0,
        }
