#!/usr/bin/env python3
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
import openai
import os
import sys
from glob import glob
from dotenv import load_dotenv
from keybert import KeyBERT
from keybert.llm import OpenAI
from keybert import KeyLLM
import warnings
import shelve
from utils import create_folders, get_chatbot_dir, rel2abspath
import logging

warnings.filterwarnings("ignore")

# load environment variables for secure configuration
load_dotenv()

# Test-aware path configuration
def get_data_paths():
    """Get data paths with test environment awareness."""
    base_dir = get_chatbot_dir()

    # Check if we're in a test environment (only explicit TESTING env var)
    is_test_env = os.getenv('TESTING', '').lower() == 'true'

    if is_test_env:
        # Use test-specific paths
        chat_data_path = os.path.join(base_dir, 'test_uploads', 'txt_files')
        classification_data_path = os.path.join(base_dir, 'test_uploads', 'classification_files')
        keywords_databank_path = os.path.join(base_dir, 'test_data', 'keywords_databank')
        database_path = os.path.join(base_dir, 'test_data', 'vector_store', 'chroma_db')

        # Ensure test directories exist
        os.makedirs(chat_data_path, exist_ok=True)
        os.makedirs(classification_data_path, exist_ok=True)
        os.makedirs(os.path.dirname(keywords_databank_path), exist_ok=True)
        os.makedirs(database_path, exist_ok=True)

        logging.info(f"🧪 Using test data paths: {chat_data_path}")
    else:
        # Use production paths from environment
        chat_data_path = os.path.join(base_dir, os.getenv("CHAT_DATA_PATH", 'data/modelling/data'))
        classification_data_path = rel2abspath(os.path.join(base_dir, os.getenv("CLASSIFICATION_DATA_PATH", 'data/modelling/CNC chatbot/data classification')))
        keywords_databank_path = rel2abspath(os.path.join(base_dir, os.getenv("KEYWORDS_DATABANK_PATH", 'data/keyword/keywords_databank')))
        database_path = rel2abspath(os.path.join(base_dir, os.getenv('DATABASE_PATH', 'data/vector_store/chroma_db')))

        logging.info(f"🏭 Using production data paths: {chat_data_path}")

    return chat_data_path, classification_data_path, keywords_databank_path, database_path

# Dynamic path getters (not cached at import time)
def get_chat_data_path():
    """Get current chat data path."""
    return get_data_paths()[0]

def get_classification_data_path():
    """Get current classification data path."""
    return get_data_paths()[1]

def get_keywords_databank_path():
    """Get current keywords databank path."""
    return get_data_paths()[2]

def get_database_path():
    """Get current database path."""
    return get_data_paths()[3]

# Legacy global variables for backward compatibility (use dynamic getters instead)
def _update_global_paths():
    """Update global path variables (for backward compatibility)."""
    global CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, KEYWORDS_DATABANK_PATH, DATABASE_PATH
    CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, KEYWORDS_DATABANK_PATH, DATABASE_PATH = get_data_paths()

# Initialize paths
_update_global_paths()
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')  # Default to a known model

# Expose current paths for external access
def get_current_paths():
    """Get current paths (updates globals and returns them)."""
    _update_global_paths()
    return CHAT_DATA_PATH, CLASSIFICATION_DATA_PATH, KEYWORDS_DATABANK_PATH, DATABASE_PATH

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.critical("OPENAI_API_KEY environment variable not set. LLM features will not work.")
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai.api_key = OPENAI_API_KEY

# Create necessary folders (parent directory of the keywords databank file)
create_folders(os.path.dirname(get_keywords_databank_path()))

# Initialize databases with proper error handling
try:
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    classification_db = Chroma(
        collection_name='classification',
        embedding_function=embedding,
        persist_directory=DATABASE_PATH
    )
    
    chat_db = Chroma(
        collection_name='chat',
        embedding_function=embedding,
        persist_directory=DATABASE_PATH
    )
    
    logging.info("Successfully initialized Chroma databases")
except Exception as e:
    logging.critical(f"Failed to initialize Chroma databases: {e}")
    raise

def dataProcessing(file, collection=chat_db):
    """Ultra-optimized data processing with performance improvements."""
    import time
    from performance_utils import perf_monitor

    perf_monitor.start_timer("file_processing")
    keywords_bank = []

    # Step 1: Extract text (fast)
    perf_monitor.start_timer("text_extraction")
    document = ExtractText(file)
    perf_monitor.end_timer("text_extraction")

    # Step 2: Fast keyword extraction (no API calls)
    perf_monitor.start_timer("keyword_extraction")
    document = FastKeyBERTMetadataTagger(document)
    perf_monitor.end_timer("keyword_extraction")

    # Process keywords
    for doc in document:
        if "keywords" in doc.metadata:
            keywords_bank.extend(doc.metadata['keywords'])
            for i in range(len(doc.metadata['keywords'])):
                doc.metadata[f'keyword{i}'] = doc.metadata['keywords'][i]
            doc.metadata["keywords"] = ", ".join(doc.metadata["keywords"])

    # Step 3: Fast chunking (no API calls)
    perf_monitor.start_timer("chunking")
    chunks = optimizedRecursiveChunker(list(document))
    perf_monitor.end_timer("chunking")

    # Step 4: Advanced memory-conscious batching
    perf_monitor.start_timer("batching")
    batches = list(optimized_batching(chunks, batch_size=20, max_memory_mb=50))
    perf_monitor.end_timer("batching")

    # Step 5: Parallel database insertion
    perf_monitor.start_timer("database_insertion")
    parallelDatabaseInsertion(batches=batches, collection=collection)
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
                with shelve.open(KEYWORDS_DATABANK_PATH, 'r') as existing_db:
                    existing_keywords = existing_db.get('keywords', [])
            except Exception as read_e:
                logging.warning(f"Could not read existing keywords databank: {read_e}")

        # Merge and deduplicate keywords
        all_keywords = list(set(existing_keywords + keywords_bank))

        # Write to temporary file with explicit sync
        temp_db_path = f"{KEYWORDS_DATABANK_PATH}.tmp"
        temp_db = None
        try:
            temp_db = shelve.open(temp_db_path, 'c')
            temp_db['keywords'] = all_keywords
            temp_db.sync()  # Force write to disk
        finally:
            if temp_db:
                temp_db.close()

        # Atomic rename operation (only after file is completely closed)
        import time
        time.sleep(0.1)  # Small delay to ensure file handles are released

        # On Windows, shelve creates .dat and .dir files, not a single file
        # Find which files actually exist and rename them
        temp_extensions = ['.dat', '.dir', '.db', '']  # Check in order of likelihood

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
                    logging.warning(f"Failed to rename {temp_file} to {main_file}: {rename_e}")
                    raise

        logging.info(f"Successfully updated keywords databank with {len(keywords_bank)} new keywords")
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        # Clean up temporary files if they exist
        temp_base = f"{KEYWORDS_DATABANK_PATH}.tmp"
        temp_extensions = ['.dat', '.dir', '.db', '']

        for ext in temp_extensions:
            temp_file = temp_base + ext
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_e:
                    logging.warning(f"Failed to clean up {temp_file}: {cleanup_e}")

# Ultra-fast text extraction with fallback options
def ExtractText(path: str):
    """Ultra-fast text extraction with multiple fallback methods."""
    from performance_utils import perf_monitor

    perf_monitor.start_timer("text_extraction_method")

    # Try fast extraction methods first
    try:
        # Method 1: Direct file reading for text files (fastest)
        if path.lower().endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json')):
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

def FastTextExtraction(file_path: str):
    """Lightning-fast text extraction for plain text files."""
    from langchain.schema import Document

    try:
        # Read file directly with encoding detection
        import chardet

        # Detect encoding from first 10KB
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

        # Read full file with detected encoding
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()

        # Create document
        document = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "extraction_method": "fast_text",
                "encoding": encoding,
                "file_size": len(content)
            }
        )

        logging.debug(f"⚡ Fast text extraction: {len(content)} chars from {file_path}")
        return [document]

    except Exception as e:
        logging.warning(f"Fast text extraction failed for {file_path}: {e}")
        raise

def OptimizedUnstructuredExtraction(file_path: str):
    """Optimized UnstructuredFileLoader with performance tweaks."""
    try:
        # Use UnstructuredFileLoader with optimized settings
        loader = UnstructuredFileLoader(
            file_path,
            mode="single",  # Single document mode for speed
            encoding='utf-8'
        )

        documents = loader.load()

        # Add extraction method to metadata
        for doc in documents:
            doc.metadata["extraction_method"] = "optimized_unstructured"
            doc.metadata["file_size"] = len(doc.page_content)

        logging.debug(f"⚡ Optimized extraction: {len(documents)} docs from {file_path}")
        return documents

    except Exception as e:
        logging.warning(f"Optimized extraction failed for {file_path}: {e}")
        raise

def StandardUnstructuredExtraction(file_path: str):
    """Standard UnstructuredFileLoader (fallback method)."""
    try:
        loader = UnstructuredFileLoader(file_path, encoding='utf-8')
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
        return [Document(
            page_content=f"[Extraction failed: {str(e)}]",
            metadata={"source": file_path, "extraction_method": "failed", "error": str(e)}
        )]

# function to create metadata keyword tags for document and chunk using OpenAI
def OpenAIMetadataTagger(document: list[Document]):
    
    schema = { 
        "properties": {
            "keywords": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The top 5–10 keywords that best represent the document's main topics or concepts.",
                "uniqueItems": True,
                "minItems": 10
            },
        },
        "required": ["keywords"]
    }

    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")  # Changed to gpt-4o-mini for consistency

    document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)
    enhanced_documents = document_transformer.transform_documents(document)
    return enhanced_documents

# function to create metadata keyword tags for document and chunk using keyBERT library
def KeyBERTMetadataTagger(document):

    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(document, keyphrase_ngram_range=(1, 2), use_maxsum=True, nr_candidates=20, top_n=5, stop_words='english')
    return keywords

# Lightning-fast keyword extractor using simple text analysis (no ML models)
def FastKeyBERTMetadataTagger(documents: list[Document]):
    """Lightning-fast keyword extraction using simple text analysis instead of ML models."""
    import re
    from collections import Counter

    def extract_keywords_simple(text):
        """Extract keywords using simple text analysis - extremely fast."""
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'its', 'our', 'their', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'now', 'here', 'there', 'when', 'where', 'why', 'how'
        }

        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter out stop words and get word frequencies
        filtered_words = [word for word in words if word not in stop_words]
        word_counts = Counter(filtered_words)

        # Get top 5 most frequent words as keywords
        keywords = [word for word, count in word_counts.most_common(5) if count > 1]

        return keywords[:3]  # Return top 3 keywords

    try:
        enhanced_documents = []

        for doc in documents:
            # Skip very short documents
            if len(doc.page_content.strip()) < 50:
                doc.metadata["keywords"] = []
            else:
                # Extract keywords using simple text analysis
                keywords = extract_keywords_simple(doc.page_content)
                doc.metadata["keywords"] = keywords

            enhanced_documents.append(doc)

        total_keywords = sum(len(doc.metadata.get("keywords", [])) for doc in enhanced_documents)
        logging.info(f"⚡ Extracted {total_keywords} keywords from {len(documents)} documents (simple analysis)")

        return enhanced_documents

    except Exception as e:
        logging.warning(f"Simple keyword extraction failed: {e}, falling back to no keywords")
        # Fallback: return documents without keywords
        for doc in documents:
            doc.metadata["keywords"] = []
        return documents

# Optional: Keep KeyBERT version for high-quality extraction when performance is not critical
def HighQualityKeyBERTMetadataTagger(documents: list[Document]):
    """High-quality KeyBERT-based metadata tagger (slower but better quality)."""
    try:
        from functools import lru_cache

        # Cache KeyBERT model to avoid re-initialization
        @lru_cache(maxsize=1)
        def get_keybert_model():
            return KeyBERT()

        kw_model = get_keybert_model()
        enhanced_documents = []

        for doc in documents:
            # Skip very short documents
            if len(doc.page_content.strip()) < 50:
                doc.metadata["keywords"] = []
                enhanced_documents.append(doc)
                continue

            # Extract keywords with KeyBERT
            keywords = kw_model.extract_keywords(
                doc.page_content,
                keyphrase_ngram_range=(1, 2),
                use_maxsum=True,
                nr_candidates=8,
                top_n=3,
                stop_words='english'
            )

            # Convert to list of keyword strings
            keyword_list = []
            for kw in keywords:
                if isinstance(kw, tuple) and len(kw) >= 2:
                    keyword_list.append(str(kw[0]))
                else:
                    keyword_list.append(str(kw))

            doc.metadata["keywords"] = keyword_list
            enhanced_documents.append(doc)

        total_keywords = sum(len(doc.metadata.get("keywords", [])) for doc in enhanced_documents)
        logging.info(f"⚡ Extracted {total_keywords} keywords from {len(documents)} documents (KeyBERT)")

        return enhanced_documents

    except Exception as e:
        logging.warning(f"KeyBERT tagging failed: {e}, falling back to simple extraction")
        return FastKeyBERTMetadataTagger(documents)

# function to create metadata keyword tags for document and chunk using keyBERT library extended with openAI through langchain
# This function outputs the same results as OpenAIMetadataTagger except it seems to have an issue of counting punctuation as a keyword
# This is likely due to the how the KeyLLM is implemented in the keyBERT library
# This function is kept here as an archive and for future reference but will not be used in the final implementation
client = openai.OpenAI(api_key=openai.api_key)
def KeyBERTOpenAIMetadataTagger(document):

    # Create your LLM
    llm = OpenAI(client)
    kw_model = KeyLLM(llm)

    # Load it in KeyLLM
    kw_model = KeyLLM(llm)

    # Extract keywords
    keywords = kw_model.extract_keywords(document,check_vocab=True)

    return keywords

# function to split documents into set smaller chunks for better retrieval processing
# includes overlap to maintain context between chunks
def recursiveChunker(documents: list[Document]):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400,
        length_function=len,
        add_start_index=True
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    print('Example Chunks:')
    print(chunks[0])
    print('='*100)
    print(chunks[1])
    print('='*100)
    print(chunks[2])

    return chunks

# Optimized recursive chunker with performance improvements
def optimizedRecursiveChunker(documents: list[Document]):
    """Optimized chunker with better performance and reduced memory usage."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Smaller chunks for faster processing
        chunk_overlap=200,  # Reduced overlap for speed
        length_function=len,
        add_start_index=True
    )

    chunks = text_splitter.split_documents(documents)

    logging.info(f"⚡ Split {len(documents)} documents into {len(chunks)} chunks")

    # Only log first chunk for verification (reduce console spam)
    if chunks:
        logging.debug(f"Sample chunk: {chunks[0].page_content[:100]}...")

    return chunks

# function to split documents into semantic smaller chunks for better retrieval processing
def semanticChunker(documents: list[Document]):

    text_splitter = SemanticChunker(OpenAIEmbeddings())

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    #print('Example Chunks:')
    #print(chunks[0])
    #print('='*100)
    #print(chunks[1])
    #print('='*100)
    #print(chunks[2])

    return chunks

# Ultra-efficient memory-conscious batching
def batching(chunks, batch_size):
    """Memory-efficient batching with generator pattern."""
    for i in range(0, len(chunks), batch_size):
        yield chunks[i:i + batch_size]

# Advanced batching with memory optimization
def optimized_batching(chunks, batch_size=25, max_memory_mb=100):
    """Advanced batching with memory monitoring and optimization."""
    import sys
    from performance_utils import perf_monitor

    perf_monitor.start_timer("advanced_batching")

    current_batch = []
    current_size = 0
    max_size = max_memory_mb * 1024 * 1024  # Convert MB to bytes

    for chunk in chunks:
        # Estimate memory usage of chunk
        chunk_size = sys.getsizeof(chunk.page_content) + sys.getsizeof(str(chunk.metadata))

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

#Adding documents to the appropriate collection
def databaseInsertion(batches, collection: Chroma):

    for chunk in batches:
        collection.add_documents(documents=chunk)

# Optimized parallel database insertion
def parallelDatabaseInsertion(batches, collection: Chroma):
    """Optimized database insertion with error handling and performance monitoring."""
    import concurrent.futures
    import threading
    from performance_utils import perf_monitor

    # Thread-safe insertion with connection pooling
    insertion_lock = threading.Lock()
    successful_insertions = 0
    failed_insertions = 0

    def insert_batch(batch_data):
        """Insert a single batch with error handling."""
        batch_idx, batch = batch_data
        try:
            with insertion_lock:  # Ensure thread-safe database access
                collection.add_documents(documents=batch)
            return f"✅ Batch {batch_idx}: {len(batch)} docs"
        except Exception as e:
            logging.error(f"❌ Batch {batch_idx} failed: {e}")
            return f"❌ Batch {batch_idx}: {str(e)}"

    # Process batches with limited parallelism to avoid overwhelming the database
    max_workers = min(3, len(batches))  # Limit concurrent database operations

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch insertion tasks
        batch_data = [(i, batch) for i, batch in enumerate(batches)]
        future_to_batch = {executor.submit(insert_batch, data): data for data in batch_data}

        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_batch):
            result = future.result()
            if "✅" in result:
                successful_insertions += 1
            else:
                failed_insertions += 1
            logging.debug(result)

    total_docs = sum(len(batch) for batch in batches)
    logging.info(f"⚡ Database insertion complete: {successful_insertions} successful, {failed_insertions} failed, {total_docs} total docs")

# Optimized keywords databank update
def updateKeywordsDatabank(keywords_bank):
    """Optimized keywords databank update with the fixed file handling."""
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
                with shelve.open(keywords_path, 'r') as existing_db:
                    existing_keywords = existing_db.get('keywords', [])
            except Exception as read_e:
                logging.warning(f"Could not read existing keywords databank: {read_e}")

        # Merge and deduplicate keywords
        all_keywords = list(set(existing_keywords + keywords_bank))

        # Write to temporary file with explicit sync
        temp_db_path = f"{keywords_path}.tmp"
        temp_db = None
        try:
            temp_db = shelve.open(temp_db_path, 'c')
            temp_db['keywords'] = all_keywords
            temp_db.sync()  # Force write to disk
        finally:
            if temp_db:
                temp_db.close()

        # Atomic rename operation (only after file is completely closed)
        import time
        time.sleep(0.1)  # Small delay to ensure file handles are released

        # On Windows, shelve creates .dat and .dir files, not a single file
        # Find which files actually exist and rename them
        temp_extensions = ['.dat', '.dir', '.db', '']  # Check in order of likelihood

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
                    logging.warning(f"Failed to rename {temp_file} to {main_file}: {rename_e}")
                    raise

        logging.info(f"Successfully updated keywords databank with {len(keywords_bank)} new keywords")
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        # Clean up temporary files if they exist
        temp_base = f"{keywords_path}.tmp"
        temp_extensions = ['.dat', '.dir', '.db', '']

        for ext in temp_extensions:
            temp_file = temp_base + ext
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as cleanup_e:
                    logging.warning(f"Failed to clean up {temp_file}: {cleanup_e}")

def initialiseDatabase():
    """Optimized database initialization with parallel processing."""
    import concurrent.futures
    from performance_utils import perf_monitor

    perf_monitor.start_timer("database_initialization")

    # Get all files to process (using dynamic paths)
    chat_files = glob(get_chat_data_path() + '/**/*.*', recursive=True)
    classification_files = glob(get_classification_data_path() + '/**/*.*', recursive=True)

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
        future_to_file = {executor.submit(process_file_with_collection, pair): pair for pair in file_collection_pairs}

        for future in concurrent.futures.as_completed(future_to_file):
            result = future.result()
            if "✅" in result:
                successful_files += 1
            else:
                failed_files += 1
            logging.debug(result)

    perf_monitor.end_timer("database_initialization")
    total_time = perf_monitor.get_metrics().get("database_initialization", 0)
    logging.info(f"🗄️ Database initialization complete in {total_time:.2f}s: {successful_files} successful, {failed_files} failed")

if __name__ == "__main__":
    pass
