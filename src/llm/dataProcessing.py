"""
Data Processing utilities for the NYP FYP CNC Chatbot.

Handles text extraction, cleaning, and keyword processing. Loads configuration and API keys from environment variables using dotenv.
"""

#!/usr/bin/env python3
import logging
import os
import sys
import re
import tempfile
import shutil
import collections
import concurrent.futures
import warnings
import shelve
import subprocess
from pathlib import Path
from typing import Generator, Iterable, List, Optional  # Added Optional

# Alpine-friendly PDF processing
try:
    import fitz  # pymupdf

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available, using simple text extraction fallback")

from langchain_community.document_transformers.openai_functions import (
    create_metadata_tagger,
)
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database import DuckDBVectorStore

from glob import glob
import yake
from infra_utils import create_folders, get_chatbot_dir
from performance_utils import perf_monitor, cache_manager
from llm.keyword_cache import get_cached_response, set_cached_response


warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()


def get_data_paths() -> tuple[str, str, str, str]:
    """
    Get data paths with test environment awareness.

    :return: Tuple containing chat_data_path, classification_data_path, keywords_databank_path, and database_path.
    :rtype: tuple[str, str, str, str]
    """
    base_dir = get_chatbot_dir()

    is_test_env = os.getenv("TESTING", "").lower() == "true"

    if is_test_env:
        chat_data_path = os.path.join(base_dir, "test_uploads", "txt_files")
        classification_data_path = os.path.join(
            base_dir, "test_uploads", "classification_files"
        )
        keywords_databank_path = os.path.join(
            base_dir, "test_data", "keywords_databank"
        )
        database_path = os.path.join(base_dir, "test_data", "vector_store", "chroma_db")

        logging.info(f"🧪 Using test data paths: {chat_data_path}")
    else:
        chat_data_path = os.path.join(base_dir, "uploads", "txt_files")
        classification_data_path = os.path.join(
            base_dir, "uploads", "classification_files"
        )
        keywords_databank_path = os.path.join(base_dir, "data", "keywords_databank")
        database_path = os.path.join(base_dir, "data", "vector_store", "chroma_db")

        logging.info(f"Using production data paths: {chat_data_path}")

    os.makedirs(chat_data_path, exist_ok=True)
    os.makedirs(classification_data_path, exist_ok=True)
    os.makedirs(os.path.dirname(keywords_databank_path), exist_ok=True)
    os.makedirs(database_path, exist_ok=True)

    return (
        chat_data_path,
        classification_data_path,
        keywords_databank_path,
        database_path,
    )


def get_chat_data_path() -> str:
    """
    Get current chat data path.

    :return: The path to the chat data directory.
    :rtype: str
    """
    return get_data_paths()[0]


def get_classification_data_path() -> str:
    """
    Get current classification data path.

    :return: The path to the classification data directory.
    :rtype: str
    """
    return get_data_paths()[1]


def get_keywords_databank_path() -> str:
    """
    Get current keywords databank path.

    :return: The path to the keywords databank.
    :rtype: str
    """
    return get_data_paths()[2]


def get_database_path() -> str:
    """
    Get current database path.

    :return: The path to the database directory.
    :rtype: str
    """
    return get_data_paths()[3]


def get_current_paths() -> tuple[str, str, str, str]:
    """
    Get current paths (updates globals and returns them).

    :return: Tuple containing current paths.
    :rtype: tuple[str, str, str, str]
    """
    return (
        get_chat_data_path(),
        get_classification_data_path(),
        get_keywords_databank_path(),
        get_database_path(),
    )


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embedding = None
classification_db = None
chat_db = None

BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "20"))
MAX_MEMORY_MB = int(os.getenv("LLM_MAX_MEMORY_MB", "50"))
MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "8"))


def global_clean_text_for_classification(text: str) -> str:
    """
    Cleans text by removing excessive whitespace, newlines, and common non-alphanumeric characters,
    suitable for classification and keyword extraction.
    This function should be available globally or passed in.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r"[\n\r]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def dataProcessing(file: str, collection: Optional[DuckDBVectorStore] = None) -> None:
    """
    Ultra-optimized data processing with performance improvements,
    including text cleaning and top 10 keyword processing per document.
    - Uses thread pool for parallel keyword extraction and chunking if many documents.
    - Caches embedding and keyword extraction results for repeated content.
    - All major steps are performance monitored.
    - Batch size and thread pool are configurable via env vars.
    - Now includes cleaning of document content and extraction of top 10 words for metadata.

    :param file: The path to the file to be processed.
    :type file: str
    :param collection: The DuckDB vector store collection to insert documents into.
                       If None, documents are processed but not inserted into a database.
    :type collection: Optional[DuckDBVectorStore]
    """
    perf_monitor.start_timer("file_processing")
    keywords_bank: List[str] = []

    perf_monitor.start_timer("text_extraction")
    document_list_raw: List[Document] = ExtractText(file)
    perf_monitor.end_timer("text_extraction")

    perf_monitor.start_timer("content_cleaning")
    document_list_cleaned: List[Document] = []
    for doc in document_list_raw:
        cleaned_content = global_clean_text_for_classification(doc.page_content)
        document_list_cleaned.append(
            Document(page_content=cleaned_content, metadata=doc.metadata)
        )
    perf_monitor.end_timer("content_cleaning")

    perf_monitor.start_timer("keyword_extraction")

    def extract_and_process_keywords(doc: Document) -> Document:
        doc_hash = hash(doc.page_content)
        cache_key = str(doc_hash)
        cached_data_str = get_cached_response(cache_key)
        if cached_data_str:
            try:
                import json

                cached_data = json.loads(cached_data_str)
                doc.metadata["keywords"] = cached_data.get("keywords", [])
                doc.metadata["top_10_keywords"] = cached_data.get("top_10_keywords", "")
                return doc
            except Exception:
                pass
        doc_with_yake_keywords = FastYAKEMetadataTagger([doc])[0]
        doc.metadata["keywords"] = doc_with_yake_keywords.metadata.get("keywords", [])
        all_words_from_yake_keywords: List[str] = []
        for kw_phrase in doc.metadata.get("keywords", []):
            cleaned_kw_phrase = global_clean_text_for_classification(str(kw_phrase))
            all_words_from_yake_keywords.extend(
                [
                    w.lower()
                    for w in re.findall(r"\b\w+\b", cleaned_kw_phrase)
                    if len(w) > 2
                ]
            )
        word_counts = collections.Counter(all_words_from_yake_keywords)
        top_10_words_list = [w for w, _ in word_counts.most_common(10)]
        top_10_keywords_str = ", ".join(top_10_words_list)
        doc.metadata["top_10_keywords"] = top_10_keywords_str
        # Save to shared keyword cache
        import json

        set_cached_response(
            cache_key,
            json.dumps(
                {
                    "keywords": doc.metadata["keywords"],
                    "top_10_keywords": top_10_keywords_str,
                }
            ),
        )
        return doc

    if len(document_list_cleaned) > 8:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            document = list(
                executor.map(extract_and_process_keywords, document_list_cleaned)
            )
    else:
        document = [extract_and_process_keywords(doc) for doc in document_list_cleaned]
    perf_monitor.end_timer("keyword_extraction")

    for doc in document:
        if "keywords" in doc.metadata:
            keywords_bank.extend(doc.metadata["keywords"])
            doc.metadata["all_extracted_keywords_str"] = ", ".join(
                doc.metadata["keywords"]
            )

    perf_monitor.start_timer("chunking")
    chunk_cache = cache_manager.get_cache("chunking")
    doc_content_hash = hash(tuple(d.page_content for d in document))
    if doc_content_hash in chunk_cache:
        chunks = chunk_cache[doc_content_hash]
    else:
        if len(document) > 8:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:
                chunk_lists = list(
                    executor.map(lambda d: optimizedRecursiveChunker([d]), document)
                )
                chunks = [c for sublist in chunk_lists for c in sublist]
        else:
            chunks = optimizedRecursiveChunker(list(document))
        chunk_cache[doc_content_hash] = chunks
    perf_monitor.end_timer("chunking")

    perf_monitor.start_timer("batching")
    batches = list(
        optimized_batching(chunks, batch_size=BATCH_SIZE, max_memory_mb=MAX_MEMORY_MB)
    )
    perf_monitor.end_timer("batching")

    perf_monitor.start_timer("database_insertion")
    if collection is not None:
        parallelDatabaseInsertion(batches=batches, collection=collection)
    else:
        logging.warning("No DuckDB vector store provided for data processing.")
    perf_monitor.end_timer("database_insertion")

    perf_monitor.start_timer("keywords_update")
    updateKeywordsDatabank(keywords_bank)
    perf_monitor.end_timer("keywords_update")

    perf_monitor.end_timer("file_processing")
    total_time = perf_monitor.get_metrics().get("file_processing", 0)
    logging.info(f"⚡ File '{Path(file).name}' processed in {total_time:.2f}s.")


def strip_yaml_front_matter(md_path: str) -> str:
    """
    Remove YAML front matter from a markdown file and return the path to a temp file without it.

    :param md_path: The path to the markdown file.
    :type md_path: str
    :return: The path to a temporary file containing the markdown content without YAML front matter.
    :rtype: str
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    yaml_regex = r"^---\s*\n.*?\n---\s*\n"
    content_no_yaml = re.sub(yaml_regex, "", content, flags=re.DOTALL)
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".md", mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(content_no_yaml)
        return tmp.name


def PandocTextExtraction(file_path: str) -> List[Document]:
    """Extracts plain text content from a file using Pandoc.

    This function leverages the Pandoc command-line tool to convert various
    document formats (e.g., Markdown, HTML, plain text) into clean, plain text.
    It includes basic error handling for Pandoc not being found or conversion
    failures.

    :param file_path: The path to the file from which to extract text.
    :type file_path: str
    :raises FileNotFoundError: If the Pandoc executable is not found in the system's PATH.
    :raises subprocess.CalledProcessError: If Pandoc encounters an error during conversion.
    :raises Exception: For any other unexpected errors during the extraction process.
    :return: A list containing a single Document object with the extracted text
             and relevant metadata.
    :rtype: list[Document]
    """
    try:
        file_extension = Path(file_path).suffix.lower()
        input_format = "plain"  # Default for general text files

        # Mapping common extensions to Pandoc input formats
        if file_extension in [".md", ".markdown"]:
            input_format = "markdown"
        elif file_extension == ".html":
            input_format = "html"
        elif file_extension == ".rst":
            input_format = "rst"
        # Add more mappings as needed for other formats Pandoc supports

        # Construct the Pandoc command
        # -f <input_format>: specifies the input format
        # -t plain: specifies the output format as plain text
        # --wrap=none: prevents line wrapping in the output
        # --strip-comments: removes comments from the input (e.g., HTML comments, Markdown comments)
        command = [
            "pandoc",
            "-f",
            input_format,
            "-t",
            "plain",
            "--wrap=none",
            "--strip-comments",
            file_path,
        ]

        # Execute the Pandoc command
        # stderr=subprocess.PIPE captures error messages
        # text=True and encoding='utf-8' ensure output is handled as text
        result = subprocess.check_output(
            command, stderr=subprocess.PIPE, text=True, encoding="utf-8"
        )
        content = result.strip()

        document = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "extraction_method": "pandoc_text",
                "original_format": input_format,
                "file_size": len(content),
            },
        )
        logging.debug(f"⚡ Pandoc extraction: {len(content)} chars from {file_path}")
        return [document]

    except FileNotFoundError:
        logging.error(
            "Pandoc executable not found. Please ensure Pandoc is installed and accessible in your system's PATH."
        )
        raise  # Re-raise to propagate the error
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Pandoc extraction failed for {file_path} (exit code: {e.returncode}): {e.stderr.strip()}"
        )
        raise  # Re-raise to propagate the error
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(
            f"An unexpected error occurred during Pandoc text extraction for {file_path}: {e}"
        )
        raise  # Re-raise to propagate the error


def ExtractText(path: str) -> List[Document]:
    """
    Ultra-fast text extraction with Alpine-friendly methods.
    Uses PyMuPDF for PDF processing and falls back to simpler methods for other file types.

    :param path: The path to the file to extract text from.
    :type path: str
    :return: A list of Document objects containing the extracted text and metadata.
    :rtype: List[Document]
    """
    perf_monitor.start_timer("text_extraction_method")

    try:
        # Define which text-based file types should be processed by Pandoc.
        # You can customize this list based on your needs.
        pandoc_supported_text_types = (
            ".md",
            ".markdown",
            ".txt",
            ".html",
            ".rst",
            ".tex",
            ".docx",
            ".odt",
            ".epub",
        )
        # Define file types that are better handled by simple text extraction
        # (e.g., code files where Pandoc might add unwanted formatting).
        fast_text_only_types = (".py", ".js", ".css", ".json")

        file_extension_lower = path.lower()

        if file_extension_lower.endswith(pandoc_supported_text_types):
            temp_path = None
            file_to_process = path  # Default to original path

            # Special handling for Markdown files to strip YAML front matter
            if file_extension_lower.endswith((".md", ".markdown")):
                temp_path = strip_yaml_front_matter(path)
                file_to_process = (
                    temp_path  # Use the temporary file for Pandoc processing
                )

            try:
                # Call the PandocTextExtraction function for these types
                result = PandocTextExtraction(file_to_process)
            finally:
                # Clean up the temporary file if it was created
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        elif file_extension_lower.endswith(fast_text_only_types):
            # Use FastTextExtraction for specific file types where Pandoc might be overkill
            # or introduce unwanted transformations (e.g., code files).
            result = FastTextExtraction(path)
        else:
            # Use Alpine-friendly PDF processing
            result = OptimizedUnstructuredExtraction(path)
        perf_monitor.end_timer("text_extraction_method")
        return result

    except Exception as e:
        logging.warning(
            f"Primary extraction methods failed for {path}: {e}. Falling back to fast text extraction."
        )
        # If any of the above methods fail, fall back to the fast text extraction approach.
        result = FastTextExtraction(path)
        perf_monitor.end_timer("text_extraction_method")
        return result


def FastTextExtraction(file_path: str) -> list[Document]:
    """
    Lightning-fast text extraction for plain text files.

    :param file_path: The path to the text file.
    :type file_path: str
    :return: List of Document objects containing extracted text and metadata.
    :rtype: list[Document]
    :raises Exception: If extraction fails.
    """
    import chardet

    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(50000)
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"

        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            content = f.read()

        document = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "extraction_method": "fast_text",
                "encoding": encoding,
                "file_size": len(content),
            },
        )

        logging.debug(f"⚡ Fast text extraction: {len(content)} chars from {file_path}")
        return [document]

    except Exception as e:
        logging.warning(f"Fast text extraction failed for {file_path}: {e}")
        raise


def OptimizedUnstructuredExtraction(file_path: str) -> list[Document]:
    import os

    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension != ".pdf":
        return FastTextExtraction(file_path)
    # Try poppler-utils (pdftotext) first
    try:
        result = subprocess.run(
            ["pdftotext", file_path, "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            text_content = result.stdout
            document = Document(
                page_content=text_content,
                metadata={
                    "source": file_path,
                    "extraction_method": "optimized_pdftotext",
                    "file_size": len(text_content),
                },
            )
            return [document]
    except Exception as e:
        logging.warning(f"pdftotext failed for {file_path}: {e}")

        # Fallback: pure Python with pypdf
    try:
        return _extracted_from_OptimizedUnstructuredExtraction_30(file_path)
    except Exception as e:
        logging.error(f"pypdf failed for {file_path}: {e}")
        return []


# TODO Rename this here and in `OptimizedUnstructuredExtraction`
def _extracted_from_OptimizedUnstructuredExtraction_30(file_path):
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    text_content = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_content += page_text
    document = Document(
        page_content=text_content,
        metadata={
            "source": file_path,
            "extraction_method": "optimized_pypdf",
            "file_size": len(text_content),
        },
    )
    return [document]


def StandardUnstructuredExtraction(file_path: str) -> list[Document]:
    """
    Standard extraction using Alpine-friendly methods (fallback method).
    Uses PyMuPDF for PDFs and falls back to fast text extraction for other files.

    :param file_path: Path to the file to extract text from.
    :type file_path: str
    :return: List of Document objects containing extracted text.
    :rtype: list[Document]
    """
    if not PYMUPDF_AVAILABLE:
        logging.warning("PyMuPDF not available, falling back to fast text extraction")
        return FastTextExtraction(file_path)

    try:
        file_extension = Path(file_path).suffix.lower()

        if file_extension == ".pdf":
            return _extracted_from_StandardUnstructuredExtraction_(file_path)
        else:
            # For non-PDF files, use fast text extraction
            return FastTextExtraction(file_path)

    except Exception as e:
        logging.warning(f"Standard extraction failed for {file_path}: {e}")
        return FastTextExtraction(file_path)


# TODO Rename this here and in `StandardUnstructuredExtraction`
def _extracted_from_StandardUnstructuredExtraction_(file_path):
    # Use PyMuPDF for PDF processing
    try:
        doc = fitz.open(file_path)
        text_content = "".join(page.get_text() for page in doc)
        doc.close()

        document = Document(
            page_content=text_content,
            metadata={
                "source": file_path,
                "extraction_method": "standard_pymupdf",
                "file_size": len(text_content),
            },
        )

        logging.debug(
            f"📄 Standard PDF extraction: {len(text_content)} chars from {file_path}"
        )
        return [document]
    except Exception as e:
        logging.warning(f"Standard extraction failed for {file_path}: {e}")
        return FastTextExtraction(file_path)


def OpenAIMetadataTagger(document: list[Document]) -> list[Document]:
    """
    Create metadata keyword tags for document and chunk using OpenAI.

    :param document: List of Document objects to tag.
    :type document: list[Document]
    :return: List of Document objects with added metadata.
    :rtype: list[Document]
    """
    schema = {
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The top 5–10 keywords that best represent the document's main topics or concepts.",
                "uniqueItems": True,
                "minItems": 10,
            },
        },
        "required": ["keywords"],
    }

    llm = ChatOpenAI(temperature=0.8, model="gpt-4o")

    document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)
    return document_transformer.transform_documents(document)


def FastYAKEMetadataTagger(documents: list[Document]) -> list[Document]:
    """
    Lightning-fast keyword extraction using YAKE (no ML models, fast and Alpine compatible).

    :param documents: List of Document objects to extract keywords from.
    :type documents: list[Document]
    :return: List of Document objects with keywords added to metadata.
    :rtype: list[Document]
    """
    enhanced_documents = []
    for doc in documents:
        if len(doc.page_content.strip()) < 50:
            doc.metadata["keywords"] = []
            enhanced_documents.append(doc)
            continue
        kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=5)
        keywords = kw_extractor.extract_keywords(doc.page_content)
        keyword_list = [kw for kw, score in sorted(keywords, key=lambda x: x[1])]
        doc.metadata["keywords"] = keyword_list
        enhanced_documents.append(doc)
    total_keywords = sum(
        len(doc.metadata.get("keywords", [])) for doc in enhanced_documents
    )
    logging.info(
        f"⚡ Extracted {total_keywords} keywords from {len(documents)} documents (YAKE fast)"
    )
    return enhanced_documents


def optimizedRecursiveChunker(documents: list[Document]) -> list[Document]:
    """
    Optimized chunker with better performance and reduced memory usage.

    :param documents: List of Document objects to chunk.
    :type documents: list[Document]
    :return: List of chunked Document objects.
    :rtype: list[Document]
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )

    chunks = text_splitter.split_documents(documents)

    logging.info(f"⚡ Split {len(documents)} documents into {len(chunks)} chunks.")

    if chunks:
        logging.debug(f"Sample chunk: {chunks[0].page_content[:100]}...")

    return chunks


def optimized_batching(
    chunks: list[Document], batch_size: int = 25, max_memory_mb: int = 100
) -> Generator[list[Document], None, None]:
    """
    Advanced batching with memory monitoring and optimization.

    :param chunks: List of chunks to batch.
    :type chunks: list[Document]
    :param batch_size: Number of chunks per batch.
    :type batch_size: int
    :param max_memory_mb: Maximum memory usage per batch in MB.
    :type max_memory_mb: int
    :yields list[Document]: A batch of chunks.
    :rtype: Generator[list[Document], None, None]
    """
    perf_monitor.start_timer("advanced_batching")

    current_batch: List[Document] = []
    current_size = 0
    max_size = max_memory_mb * 1024 * 1024

    for chunk in chunks:
        chunk_size = sys.getsizeof(chunk.page_content) + sys.getsizeof(
            str(chunk.metadata)
        )

        if current_batch and current_size + chunk_size > max_size:
            yield current_batch
            current_batch = [chunk]
            current_size = chunk_size
        else:
            current_batch.append(chunk)
            current_size += chunk_size

        if current_batch and len(current_batch) >= batch_size:
            yield current_batch
            current_batch = []
            current_size = 0

    if current_batch:
        yield current_batch

    perf_monitor.end_timer("advanced_batching")
    logging.debug(f"⚡ Advanced batching complete with memory limit {max_memory_mb}MB")


def parallelDatabaseInsertion(
    batches: Iterable[list[Document]], collection: DuckDBVectorStore
) -> None:
    """
    Optimized database insertion with error handling and performance monitoring.

    :param batches: Iterable of batches of Document objects.
    :type batches: Iterable[list[Document]]
    :param collection: The DuckDB vector store collection to insert documents into.
    :type collection: DuckDBVectorStore
    """
    import threading

    insertion_lock = threading.Lock()
    successful_insertions = 0
    failed_insertions = 0

    batches_list = list(batches)
    total_batches = len(batches_list)

    if total_batches == 0:
        logging.info("No batches to insert into the database.")
        return

    def insert_batch(batch_data: tuple[int, list[Document]]):
        batch_idx, batch = batch_data
        try:
            with insertion_lock:
                docs_for_duckdb = []
                for doc in batch:
                    docs_for_duckdb.append(
                        {
                            "id": doc.metadata.get("id", str(hash(doc.page_content))),
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                        }
                    )
                collection.add_documents(docs_for_duckdb)
            return f"✅ Batch {batch_idx}: {len(batch)} docs inserted."
        except Exception as e:
            logging.error(f"❌ Batch {batch_idx} failed: {e}")
            return f"❌ Batch {batch_idx} failed: {str(e)}"

    max_workers_for_db = min(MAX_WORKERS, total_batches, 3)
    logging.debug(f"Using {max_workers_for_db} workers for database insertion.")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers_for_db
    ) as executor:
        batch_data_tuples = list(enumerate(batches_list))
        future_to_batch = {
            executor.submit(insert_batch, data): data for data in batch_data_tuples
        }

        for future in concurrent.futures.as_completed(future_to_batch):
            result = future.result()
            if "✅" in result:
                successful_insertions += 1
            else:
                failed_insertions += 1
            logging.debug(result)

    total_docs = sum(len(batch) for batch in batches_list)
    logging.info(
        f"⚡ Database insertion complete: {successful_insertions} batches successful, {failed_insertions} failed ({total_docs} total docs)."
    )


def updateKeywordsDatabank(keywords_bank: list[str]) -> None:
    """
    Optimized keywords databank update with atomic file handling for shelve files.

    :param keywords_bank: List of keywords to add to the databank.
    :type keywords_bank: list[str]
    :raises Exception: If updating the databank fails.
    """
    if not keywords_bank:
        logging.debug("No new keywords to add to the databank.")
        return

    try:
        keywords_path = get_keywords_databank_path()
        create_folders(os.path.dirname(keywords_path))

        existing_keywords = []
        if os.path.exists(f"{keywords_path}.dat"):
            try:
                with shelve.open(keywords_path, "r") as existing_db:
                    existing_keywords = existing_db.get("keywords", [])
            except Exception as read_e:
                logging.warning(
                    f"Could not read existing keywords databank at {keywords_path}: {read_e}"
                )
                existing_keywords = []

        all_keywords = list(set(existing_keywords + keywords_bank))
        logging.debug(
            f"Merged {len(existing_keywords)} existing with {len(keywords_bank)} new keywords. Total unique: {len(all_keywords)}"
        )

        temp_db_path = f"{keywords_path}.tmp"
        temp_db = None
        try:
            temp_db = shelve.open(temp_db_path, "c")
            temp_db["keywords"] = all_keywords
            temp_db.sync()
            logging.debug(f"Temporary keywords databank written to {temp_db_path}.*")
        finally:
            if temp_db:
                temp_db.close()

        shelve_extensions = [".dat", ".dir", ".bak", ".db", ""]

        for ext in shelve_extensions:
            src_file = temp_db_path + ext
            dest_file = keywords_path + ext

            if os.path.exists(src_file):
                try:
                    if os.path.exists(dest_file):
                        os.replace(src_file, dest_file)
                        logging.debug(
                            f"Atomically replaced '{dest_file}' with '{src_file}'"
                        )
                    else:
                        os.rename(src_file, dest_file)
                        logging.debug(f"Renamed '{src_file}' to '{dest_file}'")
                except Exception as rename_e:
                    logging.warning(
                        f"Failed to replace/rename {src_file} to {dest_file}: {rename_e}"
                    )
                    raise

        logging.info(
            f"Successfully updated keywords databank with {len(keywords_bank)} new keywords. Total keywords: {len(all_keywords)}"
        )
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        temp_base = f"{keywords_path}.tmp"
        shelve_extensions = [".dat", ".dir", ".bak", ".db", ""]

        for ext in shelve_extensions:
            temp_file = temp_base + ext
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug(f"Cleaned up residual temporary file: {temp_file}")
                except Exception as cleanup_e:
                    logging.warning(
                        f"Failed to clean up residual {temp_file}: {cleanup_e}"
                    )
        raise


def initialiseDatabase():
    """
    Optimized database initialization with parallel processing.

    :return: None
    """
    perf_monitor.start_timer("database_initialization")

    chat_files = glob(os.path.join(get_chat_data_path(), "**", "*.*"), recursive=True)
    classification_files = glob(
        os.path.join(get_classification_data_path(), "**", "*.*"), recursive=True
    )

    total_files = len(chat_files) + len(classification_files)
    logging.info(f"🗄️ Initializing database with {total_files} files...")

    if total_files == 0:
        logging.info("No files found for database initialization.")
        perf_monitor.end_timer("database_initialization")
        return

    max_workers_for_init = min(MAX_WORKERS, total_files, 4)
    logging.debug(f"Using {max_workers_for_init} workers for database initialization.")

    def process_file_with_collection(
        file_and_collection: tuple[str, DuckDBVectorStore],
    ):
        file_path, collection = file_and_collection
        try:
            dataProcessing(file_path, collection=collection)
            return f"✅ Processed: {os.path.basename(file_path)}"
        except Exception as e:
            logging.error(f"❌ Failed to process {file_path}: {e}")
            return f"❌ Failed: {os.path.basename(file_path)} - {str(e)}"

    file_collection_pairs: List[tuple[str, DuckDBVectorStore]] = []
    if chat_db:
        file_collection_pairs.extend([(f, chat_db) for f in chat_files])
    else:
        logging.warning("Chat database (chat_db) not initialized for file processing.")

    if classification_db:
        file_collection_pairs.extend(
            [(f, classification_db) for f in classification_files]
        )
    else:
        logging.warning(
            "Classification database (classification_db) not initialized for file processing."
        )

    if not file_collection_pairs:
        logging.warning(
            "No database collections available for file processing during initialization."
        )
        perf_monitor.end_timer("database_initialization")
        return

    successful_files = 0
    failed_files = 0

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers_for_init
    ) as executor:
        future_to_file = {
            executor.submit(process_file_with_collection, pair): pair
            for pair in file_collection_pairs
        }

        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()
            if "✅" in result:
                successful_files += 1
            else:
                failed_files += 1
            logging.debug(result)

    perf_monitor.end_timer("database_initialization")
    total_time = perf_monitor.get_metrics().get("database_initialization", 0)
    logging.info(
        f"🗄️ Database initialization complete in {total_time:.2f}s: {successful_files} successful, {failed_files} failed."
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Running dataProcessing.py as main...")

    class MockDuckDBVectorStore:
        def __init__(self, name="mock_db"):
            self.name = name
            logging.info(f"MockDuckDBVectorStore '{self.name}' initialized.")

        def add_documents(self, docs):
            logging.info(f"MockDB '{self.name}': Added {len(docs)} documents.")

        def get_all_documents(self):
            return [{"content": "mock doc"}]

    temp_dir = tempfile.mkdtemp()
    test_chat_file = os.path.join(temp_dir, "test_chat_doc.txt")
    test_classification_file = os.path.join(temp_dir, "test_classification_doc.md")

    with open(test_chat_file, "w") as f:
        f.write(
            "This is a test document for chat data. It contains information about data processing and pipelines."
        )
    with open(test_classification_file, "w") as f:
        f.write(
            "---\ntitle: Confidential Report\nauthor: John Doe\n---\nThis document contains highly sensitive financial information. Do not share."
        )

    os.environ["TESTING"] = "true"
    chat_db = MockDuckDBVectorStore("chat_collection")
    classification_db = MockDuckDBVectorStore("classification_collection")

    initialiseDatabase()

    shutil.rmtree(temp_dir)
    logging.info("Cleaned up temporary test files and directory.")

    del os.environ["TESTING"]
