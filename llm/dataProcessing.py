#!/usr/bin/env python3
import logging

# Optional unstructured import - fallback to simple text extraction if not available
try:
    from langchain_community.document_loaders.unstructured import UnstructuredFileLoader

    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    logging.warning("Unstructured not available, using simple text extraction fallback")
from langchain_community.document_transformers.openai_functions import (
    create_metadata_tagger,
)
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from backend.database import DuckDBVectorStore

import os
import sys
from glob import glob
from dotenv import load_dotenv

import yake
import warnings
import shelve
from infra_utils import create_folders, get_chatbot_dir
import logging
from typing import Generator, Iterable
from performance_utils import perf_monitor, cache_manager
import concurrent.futures
import re
import tempfile

warnings.filterwarnings("ignore")

# load environment variables for secure configuration
load_dotenv()


def get_data_paths() -> tuple[str, str, str, str]:
    """
    Get data paths with test environment awareness.

    :return: Tuple containing chat_data_path, classification_data_path, keywords_databank_path, and database_path.
    :rtype: tuple[str, str, str, str]
    """
    base_dir = get_chatbot_dir()

    # Check if we're in a test environment (only explicit TESTING env var)
    is_test_env = os.getenv("TESTING", "").lower() == "true"

    if is_test_env:
        # Use test-specific paths
        chat_data_path = os.path.join(base_dir, "test_uploads", "txt_files")
        classification_data_path = os.path.join(
            base_dir, "test_uploads", "classification_files"
        )
        keywords_databank_path = os.path.join(
            base_dir, "test_data", "keywords_databank"
        )
        database_path = os.path.join(base_dir, "test_data", "vector_store", "chroma_db")

        # Ensure test directories exist
        os.makedirs(chat_data_path, exist_ok=True)
        os.makedirs(classification_data_path, exist_ok=True)
        os.makedirs(os.path.dirname(keywords_databank_path), exist_ok=True)
        os.makedirs(database_path, exist_ok=True)

        logging.info(f"🧪 Using test data paths: {chat_data_path}")
    else:
        # Use production paths
        chat_data_path = os.path.join(base_dir, "uploads", "txt_files")
        classification_data_path = os.path.join(
            base_dir, "uploads", "classification_files"
        )
        keywords_databank_path = os.path.join(base_dir, "data", "keywords_databank")
        database_path = os.path.join(base_dir, "data", "vector_store", "chroma_db")

        # Ensure production directories exist
        os.makedirs(chat_data_path, exist_ok=True)
        os.makedirs(classification_data_path, exist_ok=True)
        os.makedirs(os.path.dirname(keywords_databank_path), exist_ok=True)
        os.makedirs(database_path, exist_ok=True)

        logging.info(f"Using production data paths: {chat_data_path}")

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


# Legacy global variables for backward compatibility (use dynamic getters instead)
def _update_global_paths() -> None:
    """
    Update global path variables (for backward compatibility).

    :return: None
    """
    global \
        CHAT_DATA_PATH, \
        CLASSIFICATION_DATA_PATH, \
        KEYWORDS_DATABANK_PATH, \
        DATABASE_PATH
    CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, KEYWORDS_DATABANK_PATH, DATABASE_PATH = (
        get_data_paths()
    )


# Initialize paths
_update_global_paths()
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)  # Default to a known model


# Expose current paths for external access
def get_current_paths() -> tuple[str, str, str, str]:
    """
    Get current paths (updates globals and returns them).

    :return: Tuple containing current paths.
    :rtype: tuple[str, str, str, str]
    """
    _update_global_paths()
    return (
        CHAT_DATA_PATH,
        CLASSIFICATION_DATA_PATH,
        KEYWORDS_DATABANK_PATH,
        DATABASE_PATH,
    )


# LLM, embedding, and DuckDB vector store will be initialized in app.py
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
embedding = None
classification_db = None
chat_db = None


# Add environment-configurable batch/thread settings
BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "20"))
MAX_MEMORY_MB = int(os.getenv("LLM_MAX_MEMORY_MB", "50"))
MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "4"))


def dataProcessing(file: str, collection: "DuckDBVectorStore" = None) -> None:
    """
    Ultra-optimized data processing with performance improvements.
    - Uses thread pool for parallel keyword extraction and chunking if many documents.
    - Caches embedding and keyword extraction results for repeated content.
    - All major steps are performance monitored.
    - Batch size and thread pool are configurable via env vars.
    """
    import time

    perf_monitor.start_timer("file_processing")
    keywords_bank = []

    # Step 1: Extract text (fast)
    perf_monitor.start_timer("text_extraction")
    document = ExtractText(file)
    perf_monitor.end_timer("text_extraction")

    # Step 2: Fast keyword extraction (parallel if many docs)
    perf_monitor.start_timer("keyword_extraction")
    cache = cache_manager.get_cache("keyword_extraction")

    def extract_keywords(doc):
        doc_hash = hash(doc.page_content)
        if doc_hash in cache:
            doc.metadata["keywords"] = cache[doc_hash]
        else:
            doc = FastYAKEMetadataTagger([doc])[0]
            cache[doc_hash] = doc.metadata.get("keywords", [])
        return doc

    if len(document) > 8:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            document = list(executor.map(extract_keywords, document))
    else:
        document = [extract_keywords(doc) for doc in document]
    perf_monitor.end_timer("keyword_extraction")

    # Process keywords
    for doc in document:
        if "keywords" in doc.metadata:
            keywords_bank.extend(doc.metadata["keywords"])
            for i in range(len(doc.metadata["keywords"])):
                doc.metadata[f"keyword{i}"] = doc.metadata["keywords"][i]
            doc.metadata["keywords"] = ", ".join(doc.metadata["keywords"])

    # Step 3: Fast chunking (parallel if many docs)
    perf_monitor.start_timer("chunking")
    chunk_cache = cache_manager.get_cache("chunking")
    doc_hash = hash(tuple(d.page_content for d in document))
    if doc_hash in chunk_cache:
        chunks = chunk_cache[doc_hash]
    else:
        if len(document) > 8:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:
                # Split docs in parallel, then flatten
                chunk_lists = list(
                    executor.map(lambda d: optimizedRecursiveChunker([d]), document)
                )
                chunks = [c for sublist in chunk_lists for c in sublist]
        else:
            chunks = optimizedRecursiveChunker(list(document))
        chunk_cache[doc_hash] = chunks
    perf_monitor.end_timer("chunking")

    # Step 4: Advanced memory-conscious batching
    perf_monitor.start_timer("batching")
    batches = list(
        optimized_batching(chunks, batch_size=BATCH_SIZE, max_memory_mb=MAX_MEMORY_MB)
    )
    perf_monitor.end_timer("batching")

    # Step 5: Parallel database insertion
    perf_monitor.start_timer("database_insertion")
    if collection is not None:
        parallelDatabaseInsertion(batches=batches, collection=collection)
    else:
        logging.warning("No DuckDB vector store provided for data processing.")
    perf_monitor.end_timer("database_insertion")

    # Update keywords databank
    perf_monitor.start_timer("keywords_update")
    updateKeywordsDatabank(keywords_bank)
    perf_monitor.end_timer("keywords_update")

    perf_monitor.end_timer("file_processing")
    total_time = perf_monitor.get_metrics().get("file_processing", 0)
    logging.info(f"⚡ File processed in {total_time:.2f}s: {file}")

    # Update keywords databank with atomic file operations
    try:
        # Ensure the parent directory exists before creating files
        create_folders(os.path.dirname(KEYWORDS_DATABANK_PATH))

        # Load existing keywords first
        existing_keywords = []
        if os.path.exists(KEYWORDS_DATABANK_PATH):
            try:
                with shelve.open(KEYWORDS_DATABANK_PATH, "r") as existing_db:
                    existing_keywords = existing_db.get("keywords", [])
            except Exception as read_e:
                logging.warning(f"Could not read existing keywords databank: {read_e}")

        # Merge and deduplicate keywords
        all_keywords = list(set(existing_keywords + keywords_bank))

        # Write to temporary file with explicit sync
        temp_db_path = f"{KEYWORDS_DATABANK_PATH}.tmp"
        temp_db = None
        try:
            temp_db = shelve.open(temp_db_path, "c")
            temp_db["keywords"] = all_keywords
            temp_db.sync()  # Force write to disk
        finally:
            if temp_db:
                temp_db.close()

        # Atomic rename operation (only after file is completely closed)
        import time

        time.sleep(0.1)  # Small delay to ensure file handles are released

        # On Windows, shelve creates .dat and .dir files, not a single file
        # Find which files actually exist and rename them
        temp_extensions = [".dat", ".dir", ".db", ""]  # Check in order of likelihood

        for ext in temp_extensions:
            temp_file = temp_db_path + ext
            main_file = KEYWORDS_DATABANK_PATH + ext

            if os.path.exists(temp_file):
                try:
                    if os.path.exists(main_file):
                        os.replace(temp_file, main_file)
                    else:
                        os.rename(temp_file, main_file)
                    logging.debug(f"Successfully renamed {temp_file} to {main_file}")
                except Exception as rename_e:
                    logging.warning(
                        f"Failed to rename {temp_file} to {main_file}: {rename_e}"
                    )
                    raise

        logging.info(
            f"Successfully updated keywords databank with {len(keywords_bank)} new keywords"
        )
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        # Clean up temporary files if they exist
        temp_base = f"{KEYWORDS_DATABANK_PATH}.tmp"
        temp_extensions = [".dat", ".dir", ".db", ""]

        for ext in temp_extensions:
            temp_file = temp_base + ext
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_e:
                    logging.warning(f"Failed to clean up {temp_file}: {cleanup_e}")


def strip_yaml_front_matter(md_path: str) -> str:
    """Remove YAML front matter from a markdown file and return the path to a temp file without it."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Regex to match YAML front matter
    yaml_regex = r"^---\s*\n.*?\n---\s*\n"
    content_no_yaml = re.sub(yaml_regex, "", content, flags=re.DOTALL)
    # Write to a temp file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".md", mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(content_no_yaml)
        return tmp.name


def ExtractText(path: str):
    """
    Ultra-fast text extraction with multiple fallback methods.
    If the file is markdown, strip YAML front matter before passing to pandoc or other processors.
    """
    from performance_utils import perf_monitor

    perf_monitor.start_timer("text_extraction_method")

    # Try fast extraction methods first
    try:
        # Method 1: Direct file reading for text files (fastest)
        if path.lower().endswith(
            (".txt", ".md", ".py", ".js", ".html", ".css", ".json")
        ):
            # For markdown, strip YAML before further processing
            if path.lower().endswith((".md", ".markdown")):
                temp_path = strip_yaml_front_matter(path)
                result = FastTextExtraction(temp_path)
                os.unlink(temp_path)
            else:
                result = FastTextExtraction(path)
            perf_monitor.end_timer("text_extraction_method")
            return result

        # Method 2: Optimized UnstructuredFileLoader (medium speed)
        result = OptimizedUnstructuredExtraction(path)
        perf_monitor.end_timer("text_extraction_method")
        return result

    except Exception as e:
        logging.warning(f"Fast extraction failed: {e}, falling back to standard method")
        # Method 3: Standard UnstructuredFileLoader (slower but reliable)
        result = StandardUnstructuredExtraction(path)
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
    from langchain.schema import Document

    try:
        # Read file directly with encoding detection
        import chardet

        # Detect encoding from first 10KB
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"

        # Read full file with detected encoding
        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            content = f.read()

        # Create document
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
    """
    Optimized UnstructuredFileLoader with performance tweaks.

    :param file_path: The path to the file to extract.
    :type file_path: str
    :return: List of Document objects containing extracted text and metadata.
    :rtype: list[Document]
    :raises Exception: If extraction fails.
    """
    if not UNSTRUCTURED_AVAILABLE:
        logging.warning(
            "Unstructured not available, falling back to fast text extraction"
        )
        return FastTextExtraction(file_path)

    try:
        # Use UnstructuredFileLoader with optimized settings
        loader = UnstructuredFileLoader(
            file_path,
            mode="single",  # Single document mode for speed
            encoding="utf-8",
        )

        documents = loader.load()

        # Add extraction method to metadata
        for doc in documents:
            doc.metadata["extraction_method"] = "optimized_unstructured"
            doc.metadata["file_size"] = len(doc.page_content)

        logging.debug(
            f"⚡ Optimized extraction: {len(documents)} docs from {file_path}"
        )
        return documents

    except Exception as e:
        logging.warning(f"Optimized extraction failed for {file_path}: {e}")
        raise


def StandardUnstructuredExtraction(file_path: str):
    """
    Standard UnstructuredFileLoader (fallback method).

    :param file_path: The path to the file to extract.
    :type file_path: str
    :return: List of Document objects containing extracted text and metadata.
    :rtype: list[Document]
    """
    if not UNSTRUCTURED_AVAILABLE:
        logging.warning(
            "Unstructured not available, falling back to fast text extraction"
        )
        return FastTextExtraction(file_path)

    try:
        loader = UnstructuredFileLoader(file_path, encoding="utf-8")
        documents = loader.load()

        # Add extraction method to metadata
        for doc in documents:
            doc.metadata["extraction_method"] = "standard_unstructured"
            doc.metadata["file_size"] = len(doc.page_content)

        logging.debug(f"📄 Standard extraction: {len(documents)} docs from {file_path}")
        return documents

    except Exception as e:
        logging.error(f"All extraction methods failed for {file_path}: {e}")
        # Create empty document as last resort
        from langchain.schema import Document

        return [
            Document(
                page_content=f"[Extraction failed: {str(e)}]",
                metadata={
                    "source": file_path,
                    "extraction_method": "failed",
                    "error": str(e),
                },
            )
        ]


# function to create metadata keyword tags for document and chunk using OpenAI
def OpenAIMetadataTagger(document: list[Document]):
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

    llm = ChatOpenAI(
        temperature=0.8, model="gpt-4o"
    )  # Changed to gpt-4o for data processing

    document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)
    enhanced_documents = document_transformer.transform_documents(document)
    return enhanced_documents


# function to create metadata keyword tags for document and chunk using YAKE library
def YAKEMetadataTagger(document: str | list[Document]) -> list[str]:
    """
    Create metadata keyword tags for document and chunk using YAKE library.

    :param document: The document or text to extract keywords from.
    :type document: str | list[Document]
    :return: List of extracted keywords.
    :rtype: list[str]
    """
    if isinstance(document, str):
        text = document
    elif isinstance(document, list) and len(document) > 0:
        text = " ".join([doc.page_content for doc in document])
    else:
        return []

    kw_extractor = yake.KeywordExtractor(lan="en", n=1, top=5)
    keywords = kw_extractor.extract_keywords(text)
    # Return only the keyword strings, sorted by score (lowest is best)
    return [kw for kw, score in sorted(keywords, key=lambda x: x[1])]


# Lightning-fast keyword extractor using simple text analysis (no ML models)


# Lightning-fast keyword extractor using YAKE (no ML models, fast and Alpine compatible)
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


def HighQualityYAKEMetadataTagger(documents: list[Document]) -> list[Document]:
    """
    High-quality YAKE-based metadata tagger (slower but better quality).

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
        kw_extractor = yake.KeywordExtractor(lan="en", n=2, top=5)
        keywords = kw_extractor.extract_keywords(doc.page_content)
        keyword_list = [kw for kw, score in sorted(keywords, key=lambda x: x[1])]
        doc.metadata["keywords"] = keyword_list
        enhanced_documents.append(doc)
    total_keywords = sum(
        len(doc.metadata.get("keywords", [])) for doc in enhanced_documents
    )
    logging.info(
        f"⚡ Extracted {total_keywords} keywords from {len(documents)} documents (YAKE high-quality)"
    )
    return enhanced_documents


# KeyBERTOpenAIMetadataTagger and all KeyBERT-based taggers are deprecated and removed. Use YAKE-based taggers instead.


# function to split documents into set smaller chunks for better retrieval processing
# includes overlap to maintain context between chunks
def recursiveChunker(documents: list[Document]):
    """
    Split documents into set smaller chunks for better retrieval processing, with overlap to maintain context.

    :param documents: List of Document objects to chunk.
    :type documents: list[Document]
    :return: List of chunked Document objects.
    :rtype: list[Document]
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=400, length_function=len, add_start_index=True
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    print("Example Chunks:")
    print(chunks[0])
    print("=" * 100)
    print(chunks[1])
    print("=" * 100)
    print(chunks[2])

    return chunks


# Optimized recursive chunker with performance improvements
def optimizedRecursiveChunker(documents: list[Document]):
    """
    Optimized chunker with better performance and reduced memory usage.

    :param documents: List of Document objects to chunk.
    :type documents: list[Document]
    :return: List of chunked Document objects.
    :rtype: list[Document]
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Smaller chunks for faster processing
        chunk_overlap=200,  # Reduced overlap for speed
        length_function=len,
        add_start_index=True,
    )

    chunks = text_splitter.split_documents(documents)

    logging.info(f"⚡ Split {len(documents)} documents into {len(chunks)} chunks")

    # Only log first chunk for verification (reduce console spam)
    if chunks:
        logging.debug(f"Sample chunk: {chunks[0].page_content[:100]}...")

    return chunks


# function to split documents into semantic smaller chunks for better retrieval processing
def semanticChunker(documents: list[Document]):
    """
    Split documents into semantic smaller chunks for better retrieval processing.

    :param documents: List of Document objects to chunk.
    :type documents: list[Document]
    :return: List of chunked Document objects.
    :rtype: list[Document]
    """
    text_splitter = SemanticChunker(OpenAIEmbeddings())

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    # print('Example Chunks:')
    # print(chunks[0])
    # print('='*100)
    # print(chunks[1])
    # print('='*100)
    # print(chunks[2])

    return chunks


# Ultra-efficient memory-conscious batching
def batching(chunks: list, batch_size: int) -> Generator[list, None, None]:
    """
    Memory-efficient batching with generator pattern.

    :param chunks: List of chunks to batch.
    :type chunks: list
    :param batch_size: Number of chunks per batch.
    :type batch_size: int
    :yields list: A batch of chunks.
    :rtype: Generator[list, None, None]
    """
    for i in range(0, len(chunks), batch_size):
        yield chunks[i : i + batch_size]


# Advanced batching with memory optimization
def optimized_batching(
    chunks: list, batch_size: int = 25, max_memory_mb: int = 100
) -> Generator[list, None, None]:
    """
    Advanced batching with memory monitoring and optimization.

    :param chunks: List of chunks to batch.
    :type chunks: list
    :param batch_size: Number of chunks per batch.
    :type batch_size: int
    :param max_memory_mb: Maximum memory usage per batch in MB.
    :type max_memory_mb: int
    :yields list: A batch of chunks.
    :rtype: Generator[list, None, None]
    """
    from performance_utils import perf_monitor

    perf_monitor.start_timer("advanced_batching")

    current_batch = []
    current_size = 0
    max_size = max_memory_mb * 1024 * 1024  # Convert MB to bytes

    for chunk in chunks:
        # Estimate memory usage of chunk
        chunk_size = sys.getsizeof(chunk.page_content) + sys.getsizeof(
            str(chunk.metadata)
        )

        # Check if adding this chunk would exceed memory limit
        if current_size + chunk_size > max_size and current_batch:
            # Yield current batch and start new one
            yield current_batch
            current_batch = [chunk]
            current_size = chunk_size
        else:
            # Add chunk to current batch
            current_batch.append(chunk)
            current_size += chunk_size

        # Also check batch size limit
        if len(current_batch) >= batch_size:
            yield current_batch
            current_batch = []
            current_size = 0

    # Yield remaining chunks
    if current_batch:
        yield current_batch

    perf_monitor.end_timer("advanced_batching")
    logging.debug(f"⚡ Advanced batching complete with memory limit {max_memory_mb}MB")


# Adding documents to the appropriate collection
def databaseInsertion(
    batches: Iterable[list[Document]], collection: DuckDBVectorStore
) -> None:
    """
    Add documents to the appropriate collection.

    :param batches: Iterable of batches of Document objects.
    :type batches: Iterable[list[Document]]
    :param collection: The DuckDB vector store collection to insert documents into.
    :type collection: DuckDBVectorStore
    """
    for chunk in batches:
        # Convert LangChain Document objects to DuckDB format
        docs_for_duckdb = []
        for doc in chunk:
            docs_for_duckdb.append(
                {
                    "id": doc.metadata.get("id", str(hash(doc.page_content))),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
            )
        collection.add_documents(docs_for_duckdb)


# Optimized parallel database insertion
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
    import concurrent.futures
    import threading

    # Thread-safe insertion with connection pooling
    insertion_lock = threading.Lock()
    successful_insertions = 0
    failed_insertions = 0

    def insert_batch(batch_data):
        """Insert a single batch with error handling."""
        batch_idx, batch = batch_data
        try:
            with insertion_lock:  # Ensure thread-safe database access
                # Convert LangChain Document objects to DuckDB format
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
            return f"✅ Batch {batch_idx}: {len(batch)} docs"
        except Exception as e:
            logging.error(f"❌ Batch {batch_idx} failed: {e}")
            return f"❌ Batch {batch_idx}: {str(e)}"

    # Process batches with limited parallelism to avoid overwhelming the database
    max_workers = min(3, len(batches))  # Limit concurrent database operations

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch insertion tasks
        batch_data = [(i, batch) for i, batch in enumerate(batches)]
        future_to_batch = {
            executor.submit(insert_batch, data): data for data in batch_data
        }

        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_batch):
            result = future.result()
            if "✅" in result:
                successful_insertions += 1
            else:
                failed_insertions += 1
            logging.debug(result)

    total_docs = sum(len(batch) for batch in batches)
    logging.info(
        f"⚡ Database insertion complete: {successful_insertions} successful, {failed_insertions} failed, {total_docs} total docs"
    )


# Optimized keywords databank update
def updateKeywordsDatabank(keywords_bank: list[str]) -> None:
    """
    Optimized keywords databank update with the fixed file handling.

    :param keywords_bank: List of keywords to add to the databank.
    :type keywords_bank: list[str]
    :raises Exception: If updating the databank fails.
    """
    if not keywords_bank:
        return

    # Update keywords databank with atomic file operations
    try:
        # Get current keywords databank path
        keywords_path = get_keywords_databank_path()

        # Ensure the parent directory exists before creating files
        create_folders(os.path.dirname(keywords_path))

        # Load existing keywords first
        existing_keywords = []
        if os.path.exists(keywords_path):
            try:
                with shelve.open(keywords_path, "r") as existing_db:
                    existing_keywords = existing_db.get("keywords", [])
            except Exception as read_e:
                logging.warning(f"Could not read existing keywords databank: {read_e}")

        # Merge and deduplicate keywords
        all_keywords = list(set(existing_keywords + keywords_bank))

        # Write to temporary file with explicit sync
        temp_db_path = f"{keywords_path}.tmp"
        temp_db = None
        try:
            temp_db = shelve.open(temp_db_path, "c")
            temp_db["keywords"] = all_keywords
            temp_db.sync()  # Force write to disk
        finally:
            if temp_db:
                temp_db.close()

        # Atomic rename operation (only after file is completely closed)
        import time

        time.sleep(0.1)  # Small delay to ensure file handles are released

        # On Windows, shelve creates .dat and .dir files, not a single file
        # Find which files actually exist and rename them
        temp_extensions = [".dat", ".dir", ".db", ""]  # Check in order of likelihood

        for ext in temp_extensions:
            temp_file = temp_db_path + ext
            main_file = keywords_path + ext

            if os.path.exists(temp_file):
                try:
                    if os.path.exists(main_file):
                        os.replace(temp_file, main_file)
                    else:
                        os.rename(temp_file, main_file)
                    logging.debug(f"Successfully renamed {temp_file} to {main_file}")
                except Exception as rename_e:
                    logging.warning(
                        f"Failed to rename {temp_file} to {main_file}: {rename_e}"
                    )
                    raise

        logging.info(
            f"Successfully updated keywords databank with {len(keywords_bank)} new keywords"
        )
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        # Clean up temporary files if they exist
        temp_base = f"{keywords_path}.tmp"
        temp_extensions = [".dat", ".dir", ".db", ""]

        for ext in temp_extensions:
            temp_file = temp_base + ext
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_e:
                    logging.warning(f"Failed to clean up {temp_file}: {cleanup_e}")


def initialiseDatabase():
    """
    Optimized database initialization with parallel processing.

    :return: None
    """
    import concurrent.futures
    from performance_utils import perf_monitor

    perf_monitor.start_timer("database_initialization")

    # Get all files to process (using dynamic paths)
    chat_files = glob(get_chat_data_path() + "/**/*.*", recursive=True)
    classification_files = glob(
        get_classification_data_path() + "/**/*.*", recursive=True
    )

    total_files = len(chat_files) + len(classification_files)
    logging.info(f"🗄️ Initializing database with {total_files} files...")

    if total_files == 0:
        logging.info("No files found for database initialization")
        perf_monitor.end_timer("database_initialization")
        return

    # Process files in parallel with limited workers to avoid overwhelming the system
    max_workers = min(2, total_files)  # Limit concurrent file processing

    def process_file_with_collection(file_and_collection):
        """Process a single file with its designated collection."""
        file_path, collection = file_and_collection
        try:
            dataProcessing(file_path, collection=collection)
            return f"✅ Processed: {os.path.basename(file_path)}"
        except Exception as e:
            logging.error(f"❌ Failed to process {file_path}: {e}")
            return f"❌ Failed: {os.path.basename(file_path)} - {str(e)}"

    # Prepare file and collection pairs
    file_collection_pairs = []
    file_collection_pairs.extend([(f, chat_db) for f in chat_files])
    file_collection_pairs.extend([(f, classification_db) for f in classification_files])

    # Process files in parallel
    successful_files = 0
    failed_files = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
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
        f"🗄️ Database initialization complete in {total_time:.2f}s: {successful_files} successful, {failed_files} failed"
    )


if __name__ == "__main__":
    pass
