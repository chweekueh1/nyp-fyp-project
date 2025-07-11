import time
import statistics
import asyncio
import os
import sys
import sqlite3
import json
import tempfile
import concurrent.futures
import psutil
import gc
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from functools import wraps

# --- Constants and Configuration ---
# File paths
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(dotenv_path=BASE_DIR.parent / ".env", override=True)
os.environ["BENCHMARK_MODE"] = "1"

REPORT_FILE_PATH = Path("/app/data/benchmark_results.md")
DATABASE_FILE_PATH = Path("/app/data/performance.db")
APP_ROOT_DIR = Path("/app")
DATA_DIR = APP_ROOT_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Benchmark execution settings
NUM_WARMUP_RUNS = 1
NUM_MEASUREMENT_RUNS = 3
HYPERFINE_DEFAULT_RUNS = 3

# Display constants
LINE_SEPARATOR = "=" * 60
DOCKER_BUILD_MESSAGE = "🐳 Storing Docker build times..."

# Metric units
SECONDS_UNIT = "seconds"
MEGABYTES_UNIT = "MB"
GIGABYTES_UNIT = "GB"

# Dictionary keys (original minified names mapped to meaningful names)
# General
KEY_NAME = "name"
KEY_FUNC = "func"
KEY_IS_ASYNC = "is_async"
KEY_CATEGORY = "category"
KEY_DESCRIPTION = "description"
KEY_ERROR = "error"
KEY_RESULTS = "results"
KEY_TIMESTAMP = "timestamp"
KEY_DURATION = "duration"
KEY_IMAGE = "image"
KEY_TIMEZONE = "timezone"
KEY_SUCCESSFUL_RUNS = "successful_runs"
KEY_FAILED_RUNS = "failed_runs"
KEY_RUNS = "runs"
KEY_METADATA = "metadata"

# Statistics
KEY_MEAN = "mean"
KEY_STDDEV = "stddev"
KEY_MIN = "min"
KEY_MAX = "max"
KEY_MEDIAN = "median"

# System Info
KEY_CPU_COUNT = "cpu_count"
KEY_MEMORY_TOTAL_GB = "memory_total_gb"
KEY_MEMORY_AVAILABLE_GB = "memory_available_gb"
KEY_DISK_USAGE_PERCENT = "disk_usage_percent"
KEY_PYTHON_VERSION = "python_version"
KEY_PLATFORM = "platform"
KEY_IMAGE_SIZE_MB = "image_size_mb"
KEY_BUILD_HISTORY = "history"
KEY_STATISTICS = "statistics"

# Benchmark Categories
CAT_SYSTEM = "system"
CAT_SECURITY = "security"
CAT_FILE_PROCESSING = "file_processing"
CAT_SEARCH = "search"
CAT_CHAT = "chat"
CAT_NLP = "nlp"
CAT_LLM = "llm"
CAT_DATABASE = "database"
CAT_API = "api"
CAT_AUDIO = "audio"
CAT_CLASSIFICATION = "classification"

# Specific benchmark names (from original script)
BENCH_BACKEND_INIT = "Backend Initialization"
BENCH_APP_STARTUP = "App Startup"
BENCH_LLM_SETUP = "LLM Setup"
BENCH_DB_INIT = "Database Initialization"
BENCH_FILE_CLASSIFICATION = "File Classification"
BENCH_CHATBOT_RESPONSE = "Chatbot Response"
BENCH_TEXT_PROCESSING = "Text Processing"
BENCH_OPENAI_COMPLETION = "OpenAI Completion"
BENCH_KEYWORD_MATCHING = "Keyword Matching"
BENCH_FILE_TYPE_DETECTION = "File Type Detection"
BENCH_RATE_LIMITING = "Rate Limiting"
BENCH_PASSWORD_HASHING = "Password Hashing"
BENCH_STRING_OPERATIONS = "String Operations"
BENCH_JSON_OPERATIONS = "JSON Operations"
BENCH_FILE_OPERATIONS = "File Operations"
BENCH_MEMORY_ALLOCATION = "Memory Allocation"
BENCH_THREAD_POOL_OPERATIONS = "Thread Pool Operations"
BENCH_ASYNC_OPERATIONS = "Async Operations"
BENCH_DB_CONNECTION_POOL = "Database Connection Pool"
BENCH_NETWORK_LATENCY_SIM = "Network Latency Simulation"
BENCH_SIMPLE_SEARCH = "Search - Simple Queries"
BENCH_COMPLEX_SEARCH = "Search - Complex Queries"
BENCH_FUZZY_SEARCH = "Search - Fuzzy Matching"
BENCH_RATE_LIMITED = "rate_limited"
BENCH_LIMIT_INFO = "limit_info"
BENCH_CHAT_MESSAGE = "chat_message"
BENCH_QUERIES = "queries"
BENCH_TEST_USER = "testuser"
BENCH_TEST = "test"
BENCH_ALL_FAILED = "All benchmark runs failed"
BENCH_DOCKER_STORE_MESSAGE = "🐳 Storing Docker build times..."


# --- Utility Functions ---


def performance_timer(func_name: Optional[str] = None):
    """
    Decorator to measure execution time and memory usage of a function.
    Can be used for both sync and async functions.
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            try:
                return await func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                elapsed_time = end_time - start_time
                memory_diff = end_memory - start_memory
                print(
                    f"  📊 {func_name or func.__name__}: {elapsed_time:.4f}s, Memory: {memory_diff:+.2f}{MEGABYTES_UNIT}"
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                elapsed_time = end_time - start_time
                memory_diff = end_memory - start_memory
                print(
                    f"  📊 {func_name or func.__name__}: {elapsed_time:.4f}s, Memory: {memory_diff:+.2f}{MEGABYTES_UNIT}"
                )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    try:
        DATABASE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DATABASE_FILE_PATH))
        # Set a shorter timeout for connections that are not expected to block long
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Failed to use database path {DATABASE_FILE_PATH}: {e}")
        print("Warning: Using in-memory database for benchmarks")
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"An unexpected error occurred while connecting to the database: {e}")
        print("Warning: Using in-memory database for benchmarks as a fallback.")
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        return conn


def get_utc_timestamp() -> str:
    """Returns the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def get_docker_build_times() -> Optional[Dict[str, Any]]:
    """
    Retrieves Docker build history and statistics using docker_build_tracker.
    Returns None if the module is not found or an error occurs.
    """
    try:
        from docker_build_tracker import DockerBuildTracker

        tracker = DockerBuildTracker()
        history = tracker.get_build_history(limit=100)
        if history:
            formatted_history = [
                {
                    KEY_TIMESTAMP: entry["build_timestamp"],
                    KEY_IMAGE: entry["image_name"],
                    KEY_DURATION: entry["build_duration"],
                    KEY_IMAGE_SIZE_MB: entry["image_size_mb"],
                    KEY_TIMEZONE: entry[KEY_TIMEZONE],
                }
                for entry in history
            ]
            return {
                KEY_BUILD_HISTORY: formatted_history,
                KEY_STATISTICS: tracker.get_build_statistics(),
            }
        return None
    except ImportError:
        print(
            "Warning: 'docker_build_tracker' module not found. Docker build times will not be collected."
        )
        return None
    except Exception as e:
        print(f"Error loading Docker build times: {e}")
        return None


def get_system_info() -> Dict[str, Any]:
    """Collects and returns system information."""
    try:
        return {
            KEY_CPU_COUNT: psutil.cpu_count(),
            KEY_MEMORY_TOTAL_GB: psutil.virtual_memory().total / (1024**3),
            KEY_MEMORY_AVAILABLE_GB: psutil.virtual_memory().available / (1024**3),
            KEY_DISK_USAGE_PERCENT: psutil.disk_usage("/").percent,
            KEY_PYTHON_VERSION: sys.version,
            KEY_PLATFORM: sys.platform,
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {}


# --- Benchmark Functions ---
# These functions will be decorated with @performance_timer


@performance_timer(BENCH_BACKEND_INIT)
async def run_backend_initialization_benchmark():
    """Benchmarks the initialization of the backend."""
    try:
        from backend.main import init_backend

        await init_backend()
        return "Backend initialized successfully"
    except Exception as e:
        raise Exception(f"Backend init benchmark failed: {e}")


@performance_timer(BENCH_APP_STARTUP)
async def run_app_startup_benchmark():
    """Benchmarks the application startup time."""
    try:
        from src.app import create_app

        create_app()
        return "App startup completed"
    except Exception as e:
        raise Exception(f"App startup benchmark failed: {e}")


@performance_timer(BENCH_LLM_SETUP)
async def run_llm_setup_benchmark():
    """Benchmarks the LLM and database initialization."""
    try:
        from llm.chatModel import initialize_llm_and_db

        return await initialize_llm_and_db()
    except Exception as e:
        raise Exception(f"LLM setup benchmark failed: {e}")


@performance_timer(BENCH_DB_INIT)
def run_database_initialization_benchmark():
    """Benchmarks the database initialization (vector store)."""
    try:
        from llm.dataProcessing import initialiseDatabase

        return initialiseDatabase()
    except Exception as e:
        raise Exception(f"Database init benchmark failed: {e}")


@performance_timer(BENCH_FILE_CLASSIFICATION)
async def run_file_classification_benchmark():
    """Benchmarks the text file classification."""
    try:
        from backend.file_handling import data_classification

        return await data_classification("test text")
    except Exception as e:
        raise Exception(f"File classification benchmark failed: {e}")


@performance_timer(BENCH_CHATBOT_RESPONSE)
async def run_chatbot_response_benchmark():
    """Benchmarks generating a chatbot response."""
    try:
        from backend.chat import get_chatbot_response

        return await get_chatbot_response("Hello", [], BENCH_TEST_USER, "testchat")
    except Exception as e:
        raise Exception(f"Chatbot response benchmark failed: {e}")


@performance_timer("NLTK Stopwords Loading")
def run_nltk_stopwords_benchmark():
    """Benchmarks loading NLTK stopwords."""
    try:
        import nltk

        # Ensure stopwords are downloaded if not present
        try:
            nltk.data.find("corpora/stopwords")
        except nltk.downloader.DownloadError:
            nltk.download("stopwords", quiet=True)
        return nltk.corpus.stopwords.words("english")
    except Exception as e:
        raise Exception(f"NLTK stopwords benchmark failed: {e}")


@performance_timer("LangChain Initialization")
def run_langchain_init_benchmark():
    """Benchmarks LangChain embeddings initialization."""
    try:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception as e:
        raise Exception(f"LangChain embeddings benchmark failed: {e}")


@performance_timer(BENCH_TEXT_PROCESSING)
def run_text_processing_benchmark():
    """Benchmarks text extraction from a dummy file."""
    try:
        # Create a dummy file for text processing
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is a test text file for processing.")
            temp_file_path = temp_file.name
        from llm.dataProcessing import ExtractText

        result = ExtractText(temp_file_path)
        os.unlink(temp_file_path)  # Clean up the dummy file
        return result
    except Exception as e:
        raise Exception(f"Text processing benchmark failed: {e}")


@performance_timer(BENCH_OPENAI_COMPLETION)
def run_openai_completion_benchmark():
    """Benchmarks an OpenAI completion API call."""
    try:
        from backend.utils import get_completion

        return get_completion("Hello, this is a test message.", max_tokens=50)
    except Exception as e:
        raise Exception(f"OpenAI completion benchmark failed: {e}")


@performance_timer("Audio Transcription")
def run_audio_transcription_benchmark():
    """Benchmarks audio transcription using a dummy WAV file."""
    try:
        # Create a dummy WAV file (minimal RIFF header + some silence)
        riff_header = (
            b"RIFF" + (40 * b"\x00") + b"WAVE" + (1000 * b"\x00")
        )  # Simplified for test
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_audio_file:
            temp_audio_file.write(riff_header)
            audio_file_path = temp_audio_file.name
        try:
            from backend.audio import transcribe_audio

            result = transcribe_audio(audio_file_path)
            return result
        finally:
            # Clean up the dummy file
            try:
                os.unlink(audio_file_path)
            except OSError as e:
                print(f"Error deleting temporary audio file {audio_file_path}: {e}")
    except Exception as e:
        raise Exception(f"Audio transcription benchmark failed: {e}")


@performance_timer(BENCH_KEYWORD_MATCHING)
def run_keyword_matching_benchmark():
    """Benchmarks keyword matching using OpenAI function calling."""
    try:
        from llm.chatModel import match_keywords

        return match_keywords("What is the weather like today?")
    except Exception as e:
        raise Exception(f"Keyword matching benchmark failed: {e}")


@performance_timer(BENCH_FILE_TYPE_DETECTION)
async def run_file_type_detection_benchmark():
    """Benchmarks file type detection for a dummy text file."""
    try:
        from backend.file_handling import detectFileType_async

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is a test file")
            file_path = temp_file.name
        try:
            result = await detectFileType_async(file_path)
            return result
        finally:
            try:
                os.unlink(file_path)
            except OSError as e:
                print(f"Error deleting temporary file {file_path}: {e}")
    except Exception as e:
        raise Exception(f"File type detection benchmark failed: {e}")


@performance_timer("Search Functionality (Basic)")
def run_search_functionality_benchmark():
    """Benchmarks basic chat history search."""
    try:
        from backend.chat import search_chat_history

        return search_chat_history(BENCH_TEST, BENCH_TEST_USER)
    except Exception as e:
        raise Exception(f"Search functionality benchmark failed: {e}")


@performance_timer(BENCH_RATE_LIMITING)
async def run_rate_limiting_benchmark():
    """Benchmarks rate limiting for a single user."""
    try:
        from backend.rate_limiting import check_rate_limit, get_rate_limit_info

        is_rate_limited = await check_rate_limit(BENCH_TEST_USER, BENCH_CHAT_MESSAGE)
        limit_info = get_rate_limit_info("chat")
        return {BENCH_RATE_LIMITED: is_rate_limited, BENCH_LIMIT_INFO: limit_info}
    except Exception as e:
        raise Exception(f"Rate limiting benchmark failed: {e}")


@performance_timer(BENCH_PASSWORD_HASHING)
def run_password_hashing_benchmark():
    """Benchmarks password hashing and verification."""
    try:
        from hashing import hash_password, verify_password

        test_password = "test_password_123"
        hashed_password = hash_password(test_password)
        is_verified = verify_password(test_password, hashed_password)
        return {"hashed": hashed_password, "verified": is_verified}
    except Exception as e:
        raise Exception(f"Password hashing benchmark failed: {e}")


@performance_timer("Simple Math Operations")
def run_simple_math_benchmark():
    """Benchmarks basic mathematical operations."""
    import math

    result = 0
    for i in range(1_000_000):
        result += math.sqrt(i)
    return result


@performance_timer(BENCH_STRING_OPERATIONS)
def run_string_operations_benchmark():
    """Benchmarks various string manipulation operations."""
    base_string = "Hello, this is a test string for benchmarking string operations."
    result_string = ""
    for _ in range(10_000):
        result_string += base_string.upper().lower().replace(BENCH_TEST, "replaced")
    return result_string


@performance_timer(BENCH_JSON_OPERATIONS)
def run_json_operations_benchmark():
    """Benchmarks JSON serialization and deserialization."""
    data = {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ],
        "settings": {"theme": "dark", "language": "en", "notifications": True},
    }
    parsed_data = None
    for _ in range(1000):
        json_string = json.dumps(data)
        parsed_data = json.loads(json_string)
    return parsed_data


@performance_timer(BENCH_FILE_OPERATIONS)
def run_file_operations_benchmark():
    """Benchmarks file creation, writing, reading, and deletion."""
    temp_files = []
    try:
        for i in range(10):
            # Create a temporary file, write to it, and close it
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(f"Test content for file {i}".encode())
            temp_file.close()
            temp_files.append(temp_file.name)

        total_content = ""
        for file_path in temp_files:
            with open(file_path, "r") as f:
                total_content += f.read()
        return len(total_content)
    except Exception as e:
        raise Exception(f"File operations benchmark failed: {e}")
    finally:
        for file_path in temp_files:
            try:
                os.unlink(file_path)
            except OSError as e:
                print(f"Error deleting temporary file {file_path}: {e}")


@performance_timer(BENCH_MEMORY_ALLOCATION)
def run_memory_allocation_benchmark():
    """Benchmarks large memory allocation and garbage collection."""
    try:
        large_list = []
        for _ in range(100):
            large_list.append([f"item_{i}" for i in range(10000)])
        gc.collect()  # Trigger garbage collection
        return len(large_list)
    except Exception as e:
        raise Exception(f"Memory allocation benchmark failed: {e}")


@performance_timer(BENCH_THREAD_POOL_OPERATIONS)
def run_thread_pool_benchmark():
    """Benchmarks operations using a thread pool executor."""
    try:

        def cpu_bound_task(x):
            return x * x

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(cpu_bound_task, i) for i in range(1000)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
        return len(results)
    except Exception as e:
        raise Exception(f"Thread pool benchmark failed: {e}")


@performance_timer(BENCH_ASYNC_OPERATIONS)
async def run_async_operations_benchmark():
    """Benchmarks asynchronous operations with asyncio.gather."""
    try:

        async def async_task(x):
            await asyncio.sleep(0.001)  # Simulate some async I/O
            return x * x

        tasks = [async_task(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        return len(results)
    except Exception as e:
        raise Exception(f"Async operations benchmark failed: {e}")


@performance_timer(BENCH_DB_CONNECTION_POOL)
def run_database_connection_pool_benchmark():
    """Benchmarks opening and closing multiple database connections."""
    try:
        connections = []
        for i in range(10):
            conn = sqlite3.connect(":memory:")  # Use in-memory DB for speed
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            cursor.execute("INSERT INTO test VALUES (?, ?)", (i, f"test_{i}"))
            connections.append(conn)

        total_rows = 0
        for conn in connections:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test")
            total_rows += cursor.fetchone()[0]
            conn.close()  # Close connection explicitly
        return total_rows
    except Exception as e:
        raise Exception(f"Database connection pool benchmark failed: {e}")


@performance_timer(BENCH_NETWORK_LATENCY_SIM)
async def run_network_latency_benchmark():
    """Benchmarks simulated network latency."""
    try:

        async def simulate_network_call():
            await asyncio.sleep(0.01)  # Simulate network delay
            return "response"

        tasks = [simulate_network_call() for _ in range(50)]
        responses = await asyncio.gather(*tasks)
        return len(responses)
    except Exception as e:
        raise Exception(f"Network latency benchmark failed: {e}")


@performance_timer("File Classification - Text Files")
async def run_file_classification_text_benchmark():
    """Benchmarks text file classification on multiple text samples."""
    try:
        from backend.file_handling import data_classification

        text_samples = [
            "This is a simple test document for classification.",
            "CONFIDENTIAL: This document contains sensitive financial information about Q4 earnings and strategic plans.",
            "Public announcement: The company will be hosting an open house event next month.",
            "Technical specification document with detailed engineering diagrams and specifications.",
            "Personal data including names, addresses, and contact information for employees.",
        ]
        results = []
        for i, text in enumerate(text_samples):
            classification = await data_classification(text)
            results.append(classification)
        return {KEY_RESULTS: results, "processed_count": len(results)}
    except Exception as e:
        raise Exception(f"Text file classification benchmark failed: {e}")


@performance_timer("File Classification - PDF Files")
async def run_file_classification_pdf_benchmark():
    """Benchmarks PDF file classification using a dummy PDF."""
    try:
        from backend.file_handling import upload_file

        # Minimal valid PDF content for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf_file:
            temp_pdf_file.write(pdf_content)
            pdf_file_path = temp_pdf_file.name
        try:
            # Assuming upload_file also handles classification
            result = await upload_file(
                pdf_content, "test_document.pdf", BENCH_TEST_USER
            )
            return result
        finally:
            try:
                os.unlink(pdf_file_path)
            except OSError as e:
                print(f"Error deleting temporary PDF file {pdf_file_path}: {e}")
    except Exception as e:
        raise Exception(f"PDF file classification benchmark failed: {e}")


@performance_timer("File Classification - Office Documents")
async def run_file_classification_office_benchmark():
    """Benchmarks classification of a simulated Office document (as text)."""
    try:
        from backend.file_handling import upload_file

        # Simulate an Office document content (e.g., meeting minutes)
        doc_content = """Meeting Minutes

Date: 2024-01-15
Attendees: John Doe, Jane Smith

Agenda:
1. Q4 Review
2. Budget Planning
3. Strategic Initiatives

Notes:
- Revenue increased by 15%
- New product launch scheduled for Q2
- Hiring freeze implemented"""
        # Assuming upload_file also handles classification for text content
        result = await upload_file(
            doc_content.encode(), "meeting_minutes.txt", BENCH_TEST_USER
        )
        return result
    except Exception as e:
        raise Exception(f"Office document classification benchmark failed: {e}")


@performance_timer("Audio Transcription - Short Audio")
async def run_audio_transcription_short_benchmark():
    """Benchmarks transcription of a short dummy audio file."""
    try:
        from backend.audio import transcribe_audio_file_async

        # Create a short dummy WAV file
        short_riff_header = b"RIFF" + (40 * b"\x00") + b"WAVE" + (1000 * b"\x00")
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_audio_file:
            temp_audio_file.write(short_riff_header)
            audio_file_path = temp_audio_file.name
        try:
            result = await transcribe_audio_file_async(audio_file_path)
            return result
        finally:
            try:
                os.unlink(audio_file_path)
            except OSError as e:
                print(f"Error deleting temporary audio file {audio_file_path}: {e}")
    except Exception as e:
        raise Exception(f"Short audio transcription benchmark failed: {e}")


@performance_timer("Audio Transcription - Long Audio")
async def run_audio_transcription_long_benchmark():
    """Benchmarks transcription of a long dummy audio file."""
    try:
        from backend.audio import transcribe_audio_file_async

        # Create a longer dummy WAV file
        long_riff_header = b"RIFF" + (40 * b"\x00") + b"WAVE" + (5000 * b"\x00")
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_audio_file:
            temp_audio_file.write(long_riff_header)
            audio_file_path = temp_audio_file.name
        try:
            result = await transcribe_audio_file_async(audio_file_path)
            return result
        finally:
            try:
                os.unlink(audio_file_path)
            except OSError as e:
                print(f"Error deleting temporary audio file {audio_file_path}: {e}")
    except Exception as e:
        raise Exception(f"Long audio transcription benchmark failed: {e}")


@performance_timer(BENCH_SIMPLE_SEARCH)
async def run_simple_search_benchmark():
    """Benchmarks simple chat history search queries."""
    try:
        from backend.chat import search_chat_history

        queries = ["hello", BENCH_TEST, "help", "what", "how"]
        results = []
        for query in queries:
            search_result = search_chat_history(query, BENCH_TEST_USER)
            results.append(search_result)
        return {BENCH_QUERIES: len(queries), KEY_RESULTS: results}
    except Exception as e:
        raise Exception(f"Simple search benchmark failed: {e}")


@performance_timer(BENCH_COMPLEX_SEARCH)
async def run_complex_search_benchmark():
    """Benchmarks complex chat history search queries."""
    try:
        from backend.chat import search_chat_history

        queries = [
            "machine learning algorithms",
            "database optimization techniques",
            "security best practices",
            "performance monitoring tools",
            "deployment strategies",
        ]
        results = []
        for query in queries:
            search_result = search_chat_history(query, BENCH_TEST_USER)
            results.append(search_result)
        return {BENCH_QUERIES: len(queries), KEY_RESULTS: results}
    except Exception as e:
        raise Exception(f"Complex search benchmark failed: {e}")


@performance_timer(BENCH_FUZZY_SEARCH)
async def run_fuzzy_search_benchmark():
    """Benchmarks fuzzy chat history search queries."""
    try:
        from backend.chat import search_chat_history

        queries = [
            "machin lernin",
            "databse optimizashun",
            "securty best practises",
            "performence monitering",
            "deploymint strategys",
        ]
        results = []
        for query in queries:
            search_result = search_chat_history(query, BENCH_TEST_USER)
            results.append(search_result)
        return {BENCH_QUERIES: len(queries), KEY_RESULTS: results}
    except Exception as e:
        raise Exception(f"Fuzzy search benchmark failed: {e}")


@performance_timer("Rate Limiting - Multiple Users")
async def run_multiple_user_rate_limiting_benchmark():
    """Benchmarks rate limiting across multiple users."""
    try:
        from backend.rate_limiting import check_rate_limit, get_rate_limit_info

        users = ["user1", "user2", "user3", "user4", "user5"]
        results = []
        for user in users:
            is_rate_limited = await check_rate_limit(user, BENCH_CHAT_MESSAGE)
            limit_info = get_rate_limit_info("chat")
            results.append(
                {
                    "user": user,
                    BENCH_RATE_LIMITED: is_rate_limited,
                    BENCH_LIMIT_INFO: limit_info,
                }
            )
        return {"users_count": len(users), KEY_RESULTS: results}
    except Exception as e:
        raise Exception(f"Multiple user rate limiting benchmark failed: {e}")


@performance_timer("Database Operations - Batch")
def run_database_batch_operations_benchmark():
    """Benchmarks batch insert, update, and delete operations in a database."""
    temp_db_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db_file:
            temp_db_path = temp_db_file.name
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE benchmark_data (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL,
                timestamp TEXT
            )
        """)

        # Batch insert
        data_to_insert = [
            (i, f"item_{i}", i * 1.5, get_utc_timestamp()) for i in range(1000)
        ]
        cursor.executemany(
            "INSERT INTO benchmark_data VALUES (?, ?, ?, ?)", data_to_insert
        )

        # Count after insert
        cursor.execute("SELECT COUNT(*) FROM benchmark_data")

        # Batch update
        cursor.execute("UPDATE benchmark_data SET value = value * 2 WHERE id % 2 = 0")

        # Batch delete
        cursor.execute("DELETE FROM benchmark_data WHERE id > 500")

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM benchmark_data")
        final_count = cursor.fetchone()[0]
        conn.close()
        return {"inserted_count": len(data_to_insert), "final_count": final_count}
    except Exception as e:
        raise Exception(f"Database batch operations benchmark failed: {e}")
    finally:
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                os.unlink(temp_db_path)
            except OSError as e:
                print(f"Error deleting temporary database file {temp_db_path}: {e}")


@performance_timer("File Processing - Multiple Formats")
async def run_file_processing_multiple_formats_benchmark():
    """Benchmarks file type detection across various file formats."""
    # Dummy content for different file types (minimal valid headers/content)
    file_contents = [
        (".txt", b"This is a text file"),
        (".pdf", b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"),
        (
            ".docx",
            b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        ),  # Minimal DOCX header
        (
            ".xlsx",
            b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        ),  # Minimal XLSX header
        (
            ".jpg",
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\x0b\x0b\t\x08\x0b\x0f\x0c\x0c\x0e\x0e\x0f\x12\x11\x0b\x11\x13\x18\x19\x18\x12\x16\x16\x17\x16\x12\x1b\x1c\x1a\x1b\x19\x17\x19\x1d!\x1c\x1e\x1e\x1d\x1b\x1c\x1c #\x1f"$!f\x14\x1f\x1f%)-0-0))%)(\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x00\x00\x01\x7f\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf5\x9f\x04\xbe\xff\xd9',
        ),  # Minimal JPG header (tiny 1x1 image)
        (
            ".png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82",
        ),  # Minimal PNG header (tiny 1x1 image)
    ]
    temp_files = []
    results = []
    try:
        from backend.file_handling import detectFileType_async

        for suffix, content in file_contents:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(content)
                temp_file.flush()  # Ensure content is written
                temp_files.append(temp_file.name)
            detected_type = await detectFileType_async(temp_file.name)
            results.append({"format": suffix, "detected": detected_type})
        return {"formats_count": len(file_contents), KEY_RESULTS: results}
    except Exception as e:
        raise Exception(f"Multiple file format processing benchmark failed: {e}")
    finally:
        for file_path in temp_files:
            try:
                os.unlink(file_path)
            except OSError as e:
                print(f"Error deleting temporary file {file_path}: {e}")


# --- Benchmark Definitions ---
# Each benchmark is a dictionary with:
# - name: Display name of the benchmark
# - func: The function to be executed
# - is_async: True if the function is an async function, False otherwise
# - category: A category for grouping (e.g., 'system', 'security', 'file_processing')
# - description: A brief description of what the benchmark measures

BENCHMARKS: List[Dict[str, Any]] = [
    {
        KEY_NAME: "Simple Math Operations",
        KEY_FUNC: run_simple_math_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Basic mathematical operations",
    },
    {
        KEY_NAME: BENCH_STRING_OPERATIONS,
        KEY_FUNC: run_string_operations_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "String manipulation operations",
    },
    {
        KEY_NAME: BENCH_JSON_OPERATIONS,
        KEY_FUNC: run_json_operations_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "JSON serialization and deserialization",
    },
    {
        KEY_NAME: BENCH_FILE_OPERATIONS,
        KEY_FUNC: run_file_operations_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "File creation, reading, and deletion",
    },
    {
        KEY_NAME: BENCH_MEMORY_ALLOCATION,
        KEY_FUNC: run_memory_allocation_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Memory allocation and garbage collection",
    },
    {
        KEY_NAME: BENCH_THREAD_POOL_OPERATIONS,
        KEY_FUNC: run_thread_pool_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Thread pool executor operations",
    },
    {
        KEY_NAME: BENCH_ASYNC_OPERATIONS,
        KEY_FUNC: run_async_operations_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Async/await operations",
    },
    {
        KEY_NAME: BENCH_DB_CONNECTION_POOL,
        KEY_FUNC: run_database_connection_pool_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Database connection pool operations",
    },
    {
        KEY_NAME: "Database Batch Operations",
        KEY_FUNC: run_database_batch_operations_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Batch database operations",
    },
    {
        KEY_NAME: BENCH_NETWORK_LATENCY_SIM,
        KEY_FUNC: run_network_latency_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Simulated network latency operations",
    },
    {
        KEY_NAME: BENCH_PASSWORD_HASHING,
        KEY_FUNC: run_password_hashing_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_SECURITY,
        KEY_DESCRIPTION: "Password hashing and verification",
    },
    {
        KEY_NAME: BENCH_RATE_LIMITING,
        KEY_FUNC: run_rate_limiting_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SECURITY,
        KEY_DESCRIPTION: "Rate limiting functionality",
    },
    {
        KEY_NAME: "Rate Limiting Multiple Users",
        KEY_FUNC: run_multiple_user_rate_limiting_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SECURITY,
        KEY_DESCRIPTION: "Rate limiting with multiple users",
    },
    {
        KEY_NAME: BENCH_FILE_TYPE_DETECTION,
        KEY_FUNC: run_file_type_detection_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_FILE_PROCESSING,
        KEY_DESCRIPTION: "File type detection using filetype library",
    },
    {
        KEY_NAME: "File Processing Multiple Formats",
        KEY_FUNC: run_file_processing_multiple_formats_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_FILE_PROCESSING,
        KEY_DESCRIPTION: "File processing for multiple formats",
    },
    {
        KEY_NAME: "File Classification - Text",
        KEY_FUNC: run_file_classification_text_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_CLASSIFICATION,
        KEY_DESCRIPTION: "Text file classification",
    },
    {
        KEY_NAME: "File Classification - PDF",
        KEY_FUNC: run_file_classification_pdf_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_CLASSIFICATION,
        KEY_DESCRIPTION: "PDF file classification",
    },
    {
        KEY_NAME: "File Classification - Office",
        KEY_FUNC: run_file_classification_office_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_CLASSIFICATION,
        KEY_DESCRIPTION: "Office document classification",
    },
    {
        KEY_NAME: "NLTK Stopwords Loading",
        KEY_FUNC: run_nltk_stopwords_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_NLP,
        KEY_DESCRIPTION: "Load NLTK stopwords",
    },
    {
        KEY_NAME: "LangChain Initialization",
        KEY_FUNC: run_langchain_init_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_LLM,
        KEY_DESCRIPTION: "Initialize LangChain embeddings",
    },
    {
        KEY_NAME: BENCH_KEYWORD_MATCHING,
        KEY_FUNC: run_keyword_matching_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_NLP,
        KEY_DESCRIPTION: "Keyword matching using OpenAI function calling",
    },
    {
        KEY_NAME: BENCH_SIMPLE_SEARCH,
        KEY_FUNC: run_simple_search_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SEARCH,
        KEY_DESCRIPTION: "Simple search queries",
    },
    {
        KEY_NAME: BENCH_COMPLEX_SEARCH,
        KEY_FUNC: run_complex_search_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SEARCH,
        KEY_DESCRIPTION: "Complex search queries",
    },
    {
        KEY_NAME: BENCH_FUZZY_SEARCH,
        KEY_FUNC: run_fuzzy_search_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SEARCH,
        KEY_DESCRIPTION: "Fuzzy search matching",
    },
    {
        KEY_NAME: BENCH_OPENAI_COMPLETION,
        KEY_FUNC: run_openai_completion_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_API,
        KEY_DESCRIPTION: "OpenAI completion API call",
    },
    {
        KEY_NAME: "Audio Transcription - Short",
        KEY_FUNC: run_audio_transcription_short_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_AUDIO,
        KEY_DESCRIPTION: "Short audio transcription",
    },
    {
        KEY_NAME: "Audio Transcription - Long",
        KEY_FUNC: run_audio_transcription_long_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_AUDIO,
        KEY_DESCRIPTION: "Long audio transcription",
    },
    {
        KEY_NAME: BENCH_TEXT_PROCESSING,
        KEY_FUNC: run_text_processing_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_FILE_PROCESSING,
        KEY_DESCRIPTION: "Process text files",
    },
    {
        KEY_NAME: BENCH_FILE_CLASSIFICATION,
        KEY_FUNC: run_file_classification_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_CLASSIFICATION,
        KEY_DESCRIPTION: "Classify text content",
    },
    {
        KEY_NAME: BENCH_LLM_SETUP,
        KEY_FUNC: run_llm_setup_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_LLM,
        KEY_DESCRIPTION: "Initialize LLM and database connections",
    },
    {
        KEY_NAME: BENCH_DB_INIT,
        KEY_FUNC: run_database_initialization_benchmark,
        KEY_IS_ASYNC: False,
        KEY_CATEGORY: CAT_DATABASE,
        KEY_DESCRIPTION: "Initialize database and vector store",
    },
    {
        KEY_NAME: BENCH_CHATBOT_RESPONSE,
        KEY_FUNC: run_chatbot_response_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_CHAT,
        KEY_DESCRIPTION: "Generate chatbot response",
    },
    {
        KEY_NAME: BENCH_BACKEND_INIT,
        KEY_FUNC: run_backend_initialization_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Complete backend initialization",
    },
    {
        KEY_NAME: BENCH_APP_STARTUP,
        KEY_FUNC: run_app_startup_benchmark,
        KEY_IS_ASYNC: True,
        KEY_CATEGORY: CAT_SYSTEM,
        KEY_DESCRIPTION: "Application startup time",
    },
]


# --- BenchmarkRunner Class ---


class BenchmarkRunner:
    """
    Manages the execution, storage, and reporting of various performance benchmarks.
    """

    def __init__(self, username: str = "system"):
        self.username = username
        self.perf_db_connection = get_db_connection()
        self.results: Dict[str, Any] = {}
        self.docker_build_times = get_docker_build_times()
        self.system_info = get_system_info()

    async def run_single_benchmark_async(
        self, benchmark: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs a single asynchronous benchmark, including warmup and measurement runs.
        """
        print(f"🔥 Running benchmark: {benchmark[KEY_NAME]}")
        run_times = []

        # Warmup runs
        for i in range(NUM_WARMUP_RUNS):
            try:
                if benchmark[KEY_IS_ASYNC]:
                    await benchmark[KEY_FUNC]()
                else:
                    # Run synchronous function in a thread pool to avoid blocking the event loop
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, benchmark[KEY_FUNC])
                print(f"  🔄 Warmup {i + 1}/{NUM_WARMUP_RUNS}")
            except Exception as e:
                print(f"  ⚠️ Warmup {i + 1} failed: {e}")

        # Measurement runs
        for i in range(NUM_MEASUREMENT_RUNS):
            try:
                start_time = time.perf_counter()
                if benchmark[KEY_IS_ASYNC]:
                    await benchmark[KEY_FUNC]()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, benchmark[KEY_FUNC])
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                run_times.append(elapsed_time)
                print(f"  ⏱️ Run {i + 1}/{NUM_MEASUREMENT_RUNS}: {elapsed_time:.4f}s")
            except Exception as e:
                print(f"  ❌ Run {i + 1} failed: {e}")
                # Continue with other runs even if one fails
                continue

        if not run_times:
            return {KEY_ERROR: BENCH_ALL_FAILED}

        return self._calculate_stats(run_times, benchmark)

    def run_single_benchmark_sync(self, benchmark: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a single synchronous benchmark, including warmup and measurement runs.
        Handles async functions by running them in the current event loop.
        """
        print(f"🔥 Running benchmark: {benchmark[KEY_NAME]}")
        run_times = []

        # Warmup runs
        for i in range(NUM_WARMUP_RUNS):
            try:
                if benchmark[KEY_IS_ASYNC]:
                    asyncio.run(benchmark[KEY_FUNC]())
                else:
                    benchmark[KEY_FUNC]()
                print(f"  🔄 Warmup {i + 1}/{NUM_WARMUP_RUNS}")
            except Exception as e:
                print(f"  ⚠️ Warmup {i + 1} failed: {e}")

        # Measurement runs
        for i in range(NUM_MEASUREMENT_RUNS):
            try:
                start_time = time.perf_counter()
                if benchmark[KEY_IS_ASYNC]:
                    asyncio.run(benchmark[KEY_FUNC]())
                else:
                    benchmark[KEY_FUNC]()
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                run_times.append(elapsed_time)
                print(f"  ⏱️ Run {i + 1}/{NUM_MEASUREMENT_RUNS}: {elapsed_time:.4f}s")
            except Exception as e:
                print(f"  ❌ Run {i + 1} failed: {e}")
                continue

        if not run_times:
            return {KEY_ERROR: BENCH_ALL_FAILED}

        return self._calculate_stats(run_times, benchmark)

    def _calculate_stats(
        self, times: List[float], benchmark_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculates statistics from a list of run times."""
        stats = {
            KEY_MEAN: statistics.mean(times),
            KEY_STDDEV: statistics.stdev(times) if len(times) > 1 else 0.0,
            KEY_MIN: min(times),
            KEY_MAX: max(times),
            KEY_MEDIAN: statistics.median(times),
            KEY_RUNS: len(times),
            KEY_SUCCESSFUL_RUNS: len(times),
            KEY_FAILED_RUNS: NUM_MEASUREMENT_RUNS - len(times),
        }
        self._store_benchmark_result(benchmark_info, stats)
        return stats

    def _store_benchmark_result(
        self, benchmark_info: Dict[str, Any], stats: Dict[str, Any]
    ):
        """Stores benchmark results in the performance database."""
        try:
            # Create table if not exists
            self.perf_db_connection.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.perf_db_connection.commit()

            insert_sql = """
                INSERT INTO performance_metrics
                (username, metric_type, metric_name, metric_value, metric_unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            # Store main statistics
            metadata_json = json.dumps(
                {
                    KEY_CATEGORY: benchmark_info[KEY_CATEGORY],
                    KEY_DESCRIPTION: benchmark_info[KEY_DESCRIPTION],
                    KEY_RUNS: stats[KEY_RUNS],
                    KEY_SUCCESSFUL_RUNS: stats[KEY_SUCCESSFUL_RUNS],
                    KEY_FAILED_RUNS: stats[KEY_FAILED_RUNS],
                }
            )

            metrics_to_store = [
                (
                    self.username,
                    "benchmark",
                    f"{benchmark_info[KEY_NAME]}_mean",
                    stats[KEY_MEAN],
                    SECONDS_UNIT,
                    get_utc_timestamp(),
                    metadata_json,
                ),
                (
                    self.username,
                    "benchmark",
                    f"{benchmark_info[KEY_NAME]}_stddev",
                    stats[KEY_STDDEV],
                    SECONDS_UNIT,
                    get_utc_timestamp(),
                    metadata_json,
                ),
                (
                    self.username,
                    "benchmark",
                    f"{benchmark_info[KEY_NAME]}_min",
                    stats[KEY_MIN],
                    SECONDS_UNIT,
                    get_utc_timestamp(),
                    metadata_json,
                ),
                (
                    self.username,
                    "benchmark",
                    f"{benchmark_info[KEY_NAME]}_max",
                    stats[KEY_MAX],
                    SECONDS_UNIT,
                    get_utc_timestamp(),
                    metadata_json,
                ),
                (
                    self.username,
                    "benchmark",
                    f"{benchmark_info[KEY_NAME]}_median",
                    stats[KEY_MEDIAN],
                    SECONDS_UNIT,
                    get_utc_timestamp(),
                    metadata_json,
                ),
            ]

            cursor = self.perf_db_connection.cursor()
            for metric in metrics_to_store:
                cursor.execute(insert_sql, metric)
            self.perf_db_connection.commit()
            print(
                f"  💾 Stored {len(metrics_to_store)} metrics in database for {benchmark_info[KEY_NAME]}"
            )

        except sqlite3.Error as e:
            print(f"  ❌ Failed to store benchmark result in database: {e}")
        except Exception as e:
            print(
                f"  ❌ An unexpected error occurred while storing benchmark result: {e}"
            )

    def store_docker_build_times(self):
        """Stores Docker build history and statistics in the performance database."""
        if not self.docker_build_times:
            print("  ⚠️ No Docker build times available or failed to load.")
            return

        try:
            insert_sql = """
                INSERT INTO performance_metrics
                (username, metric_type, metric_name, metric_value, metric_unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor = self.perf_db_connection.cursor()

            # Store individual build history
            for build in self.docker_build_times.get(KEY_BUILD_HISTORY, []):
                metadata_json = json.dumps(
                    {
                        KEY_IMAGE: build[KEY_IMAGE],
                        "type": "individual_build",
                        KEY_IMAGE_SIZE_MB: build.get(KEY_IMAGE_SIZE_MB, 0),
                        KEY_TIMEZONE: build.get(KEY_TIMEZONE, "UTC"),
                    }
                )
                cursor.execute(
                    insert_sql,
                    (
                        self.username,
                        "docker_build",
                        f"build_{build[KEY_IMAGE]}",
                        build[KEY_DURATION],
                        SECONDS_UNIT,
                        build[KEY_TIMESTAMP],
                        metadata_json,
                    ),
                )

            # Store build statistics (averages)
            build_stats = self.docker_build_times.get(KEY_STATISTICS, {})
            for image_name, stats in build_stats.items():
                metadata_json = json.dumps(
                    {
                        KEY_IMAGE: image_name,
                        "type": "build_statistics",
                        "avg_size_mb": stats.get("avg_size_mb", 0),
                        "total_builds": stats.get("total_builds", 0),
                        KEY_TIMEZONE: stats.get(KEY_TIMEZONE, "UTC"),
                    }
                )
                cursor.execute(
                    insert_sql,
                    (
                        self.username,
                        "docker_build",
                        f"stats_{image_name}_avg_duration",  # Specific metric name for clarity
                        stats["avg_duration"],
                        SECONDS_UNIT,
                        get_utc_timestamp(),
                        metadata_json,
                    ),
                )
            self.perf_db_connection.commit()
            print("  💾 Stored Docker build times and statistics in database")
        except sqlite3.Error as e:
            print(f"  ❌ Failed to store Docker build times in database: {e}")
        except Exception as e:
            print(
                f"  ❌ An unexpected error occurred while storing Docker build times: {e}"
            )

    async def run_all_benchmarks_async(self) -> Dict[str, Any]:
        """
        Runs all defined benchmarks asynchronously, grouped by category.
        """
        print("🚀 Starting comprehensive async benchmark suite...")
        print(
            f"📊 Running {len(BENCHMARKS)} benchmarks with {NUM_MEASUREMENT_RUNS} runs each"
        )
        print(f"👤 Username: {self.username}")
        print(
            f"🔧 System: {self.system_info.get(KEY_CPU_COUNT, 'Unknown')} CPUs, "
            f"{self.system_info.get(KEY_MEMORY_TOTAL_GB, 0):.1f}{GIGABYTES_UNIT} RAM"
        )
        print(LINE_SEPARATOR)

        total_start_time = time.time()
        print(BENCH_DOCKER_STORE_MESSAGE)
        self.store_docker_build_times()

        results: Dict[str, Any] = {}
        benchmarks_by_category: Dict[str, List[Dict[str, Any]]] = {}
        for bench in BENCHMARKS:
            benchmarks_by_category.setdefault(bench[KEY_CATEGORY], []).append(bench)

        for category, category_benchmarks in benchmarks_by_category.items():
            print(f"\n📂 Running {category.capitalize()} benchmarks...")
            tasks = [self.run_single_benchmark_async(b) for b in category_benchmarks]
            category_results = await asyncio.gather(*tasks, return_exceptions=True)

            for benchmark_info, result in zip(category_benchmarks, category_results):
                benchmark_name = benchmark_info[KEY_NAME]
                if isinstance(result, Exception):
                    print(f"❌ {benchmark_name} failed: {result}")
                    results[benchmark_name] = {KEY_ERROR: str(result)}
                else:
                    results[benchmark_name] = result
                    if KEY_ERROR not in result:
                        print(
                            f"✅ {benchmark_name}: {result.get(KEY_MEAN, 'N/A'):.4f}s ± {result.get(KEY_STDDEV, 'N/A'):.4f}s"
                        )
                    else:
                        print(f"❌ {benchmark_name}: {result[KEY_ERROR]}")

        total_elapsed_time = time.time() - total_start_time
        print(f"\n🎯 Total benchmark time: {total_elapsed_time:.2f}s")
        print(LINE_SEPARATOR)
        return results

    def run_all_benchmarks_sync(self) -> Dict[str, Any]:
        """
        Runs all defined benchmarks synchronously.
        """
        print("🚀 Starting comprehensive synchronous benchmark suite...")
        print(
            f"📊 Running {len(BENCHMARKS)} benchmarks with {NUM_MEASUREMENT_RUNS} runs each"
        )
        print(f"👤 Username: {self.username}")
        print(LINE_SEPARATOR)

        total_start_time = time.time()
        print(BENCH_DOCKER_STORE_MESSAGE)
        self.store_docker_build_times()

        results: Dict[str, Any] = {}
        for benchmark_info in BENCHMARKS:
            try:
                benchmark_result = self.run_single_benchmark_sync(benchmark_info)
                results[benchmark_info[KEY_NAME]] = benchmark_result
                if KEY_ERROR not in benchmark_result:
                    print(
                        f"✅ {benchmark_info[KEY_NAME]}: {benchmark_result.get(KEY_MEAN, 'N/A'):.4f}s ± {benchmark_result.get(KEY_STDDEV, 'N/A'):.4f}s"
                    )
                else:
                    print(
                        f"❌ {benchmark_info[KEY_NAME]}: {benchmark_result[KEY_ERROR]}"
                    )
            except Exception as e:
                print(f"❌ {benchmark_info[KEY_NAME]} failed: {e}")
                results[benchmark_info[KEY_NAME]] = {KEY_ERROR: str(e)}

        total_elapsed_time = time.time() - total_start_time
        print(f"\n🎯 Total benchmark time: {total_elapsed_time:.2f}s")
        print(LINE_SEPARATOR)
        return results

    def write_markdown_report(self, results: Dict[str, Any]):
        """Generates a detailed markdown report of the benchmark results."""
        with open(REPORT_FILE_PATH, "w") as f:
            f.write("# NYP FYP Chatbot Benchmark Results\n\n")
            f.write(f"**Generated:** {get_utc_timestamp()}\n")
            f.write(f"**Username:** {self.username}\n")
            f.write(f"**Total Benchmarks Run:** {len(results)}\n")
            f.write(
                f"**System Info:** CPU Cores: {self.system_info.get(KEY_CPU_COUNT, 'N/A')}, "
                f"Total RAM: {self.system_info.get(KEY_MEMORY_TOTAL_GB, 0):.1f}{GIGABYTES_UNIT}, "
                f"Python Version: {self.system_info.get(KEY_PYTHON_VERSION, 'N/A')}, "
                f"Platform: {self.system_info.get(KEY_PLATFORM, 'N/A')}\n\n"
            )

            f.write("## Summary\n\n")
            f.write(
                "| Benchmark Name | Category | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Median (s) | Runs | Successful | Failed |\n"
            )
            f.write(
                "|----------------|----------|----------|-------------|---------|---------|------------|------|------------|--------|\n"
            )

            # Sort benchmarks by category then name for better readability in the report
            sorted_benchmark_names = sorted(results.keys())
            sorted_benchmarks_with_categories = []
            for name in sorted_benchmark_names:
                # Find the corresponding benchmark definition to get its category
                for bench_def in BENCHMARKS:
                    if bench_def[KEY_NAME] == name:
                        sorted_benchmarks_with_categories.append(
                            (name, bench_def[KEY_CATEGORY], results[name])
                        )
                        break

            # Sort by category first, then by name
            sorted_benchmarks_with_categories.sort(key=lambda x: (x[1], x[0]))

            for name, category, data in sorted_benchmarks_with_categories:
                if KEY_ERROR in data:
                    f.write(
                        f"| {name} | {category.capitalize()} | ❌ Error | - | - | - | - | - | - | - |\n"
                    )
                else:
                    f.write(
                        f"| {name} | {category.capitalize()} | {data.get(KEY_MEAN, 'N/A'):.4f} | {data.get(KEY_STDDEV, 'N/A'):.4f} | {data.get(KEY_MIN, 'N/A'):.4f} | {data.get(KEY_MAX, 'N/A'):.4f} | {data.get(KEY_MEDIAN, 'N/A'):.4f} | {data.get(KEY_RUNS, 'N/A')} | {data.get(KEY_SUCCESSFUL_RUNS, 'N/A')} | {data.get(KEY_FAILED_RUNS, 'N/A')} |\n"
                    )

            f.write("\n## Detailed Results\n\n")
            for name, category, data in sorted_benchmarks_with_categories:
                f.write(f"### {name} ({category.capitalize()})\n\n")

                # Find the description for the benchmark
                description = "N/A"
                for bench_def in BENCHMARKS:
                    if bench_def[KEY_NAME] == name:
                        description = bench_def[KEY_DESCRIPTION]
                        break
                f.write(f"**Description:** {description}\n\n")

                if KEY_ERROR in data:
                    f.write(f"**Error:** {data[KEY_ERROR]}\n\n")
                else:
                    f.write("| Metric | Value |\n")
                    f.write("|--------|-------|\n")
                    f.write(
                        f"| Mean | {data.get(KEY_MEAN, 'N/A'):.4f} {SECONDS_UNIT} |\n"
                    )
                    f.write(
                        f"| Stddev | {data.get(KEY_STDDEV, 'N/A'):.4f} {SECONDS_UNIT} |\n"
                    )
                    f.write(
                        f"| Min | {data.get(KEY_MIN, 'N/A'):.4f} {SECONDS_UNIT} |\n"
                    )
                    f.write(
                        f"| Max | {data.get(KEY_MAX, 'N/A'):.4f} {SECONDS_UNIT} |\n"
                    )
                    f.write(
                        f"| Median | {data.get(KEY_MEDIAN, 'N/A'):.4f} {SECONDS_UNIT} |\n"
                    )
                    f.write(f"| Total Runs | {data.get(KEY_RUNS, 'N/A')} |\n")
                    f.write(
                        f"| Successful Runs | {data.get(KEY_SUCCESSFUL_RUNS, 'N/A')} |\n"
                    )
                    f.write(f"| Failed Runs | {data.get(KEY_FAILED_RUNS, 'N/A')} |\n\n")

            # Add Docker Build Times Summary
            if self.docker_build_times:
                f.write("\n## Docker Build Times Summary\n\n")
                f.write(
                    "This section provides insights into Docker image build performance.\n\n"
                )

                build_stats = self.docker_build_times.get(KEY_STATISTICS, {})
                if build_stats:
                    f.write("### Average Build Times by Image\n\n")
                    f.write(
                        "| Image Name | Average Duration (s) | Average Size (MB) | Total Builds | Timezone |\n"
                    )
                    f.write(
                        "|------------|----------------------|-------------------|--------------|----------|\n"
                    )
                    for image_name, stats in build_stats.items():
                        f.write(
                            f"| {image_name} | {stats.get('avg_duration', 'N/A'):.2f} | {stats.get('avg_size_mb', 'N/A'):.2f} | {stats.get('total_builds', 'N/A')} | {stats.get(KEY_TIMEZONE, 'N/A')} |\n"
                        )
                    f.write("\n")

                build_history = self.docker_build_times.get(KEY_BUILD_HISTORY, [])
                if build_history:
                    f.write("### Recent Docker Builds (Last 5)\n\n")
                    f.write(
                        "| Timestamp (UTC) | Image Name | Duration (s) | Size (MB) | Timezone |\n"
                    )
                    f.write(
                        "|-----------------|------------|--------------|-----------|----------|\n"
                    )
                    # Sort history by timestamp descending to show most recent first
                    sorted_history = sorted(
                        build_history, key=lambda x: x[KEY_TIMESTAMP], reverse=True
                    )
                    for build in sorted_history[:5]:
                        f.write(
                            f"| {build.get(KEY_TIMESTAMP, 'N/A')} | {build.get(KEY_IMAGE, 'N/A')} | {build.get(KEY_DURATION, 'N/A'):.2f} | {build.get(KEY_IMAGE_SIZE_MB, 'N/A'):.2f} | {build.get(KEY_TIMEZONE, 'N/A')} |\n"
                        )
                    f.write("\n")

        print(f"📄 Detailed report written to {REPORT_FILE_PATH}")


def run_hyperfine_style_benchmark(
    benchmark_name: str, command: str, runs: int = HYPERFINE_DEFAULT_RUNS
) -> Dict[str, Any]:
    """
    Runs an external command using subprocess, similar to hyperfine,
    and collects timing statistics.
    """
    import subprocess

    print(f"🔥 Running system command benchmark: {benchmark_name}")
    print(f"📝 Command: `{command}`")
    run_times = []
    for i in range(runs):
        try:
            start_time = time.perf_counter()
            # Use shell=True for complex commands (e.g., pipes, redirects)
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            run_times.append(elapsed_time)
            print(f"  ⏱️ Run {i + 1}/{runs}: {elapsed_time:.4f}s")
        except process.TimeoutExpired:
            print(f"  ⏰ Run {i + 1} timed out after 60 seconds.")
            # Optionally print stdout/stderr even on timeout
            # print(f"  Stdout: {ex.stdout}\n  Stderr: {ex.stderr}")
        except process.CalledProcessError as e:
            print(f"  ❌ Run {i + 1} failed with return code {e.returncode}")
            print(f"  Stdout: {e.stdout}\n  Stderr: {e.stderr}")
        except Exception as e:
            print(f"  ❌ Run {i + 1} failed: {e}")

    if not run_times:
        return {KEY_ERROR: BENCH_ALL_FAILED}

    return {
        KEY_MEAN: statistics.mean(run_times),
        KEY_STDDEV: statistics.stdev(run_times) if len(run_times) > 1 else 0.0,
        KEY_MIN: min(run_times),
        KEY_MAX: max(run_times),
        KEY_MEDIAN: statistics.median(run_times),
        KEY_RUNS: len(run_times),
        KEY_SUCCESSFUL_RUNS: len(run_times),
        KEY_FAILED_RUNS: runs - len(run_times),
    }


async def main():
    """Main function to run the benchmark suite."""
    username = os.getenv("BENCHMARK_USER", "system")
    runner = BenchmarkRunner(username)

    if runner.docker_build_times:
        print("🐳 Docker Build Times Summary:")
        print(LINE_SEPARATOR)
        build_stats = runner.docker_build_times.get(KEY_STATISTICS, {})
        if build_stats:
            print("📊 Average Build Times:")
            for image, stats in build_stats.items():
                print(
                    f"  {image}: {stats['avg_duration']:.2f}s (Avg Size: {stats.get('avg_size_mb', 0):.2f}MB, Total Builds: {stats.get('total_builds', 0)})"
                )
        build_history = runner.docker_build_times.get(KEY_BUILD_HISTORY, [])
        if build_history:
            print(f"\n📈 Recent Builds ({len(build_history)} total):")
            # Show the 5 most recent builds
            for build in sorted(
                build_history, key=lambda x: x[KEY_TIMESTAMP], reverse=True
            )[:5]:
                print(
                    f"  {build[KEY_IMAGE]}: {build[KEY_DURATION]:.2f}s ({build[KEY_TIMESTAMP]}, {build.get(KEY_IMAGE_SIZE_MB, 0):.2f}MB)"
                )
        print(LINE_SEPARATOR)

    all_benchmark_results = await runner.run_all_benchmarks_async()
    runner.write_markdown_report(all_benchmark_results)

    print("\n🔧 Running system command benchmarks...")
    system_commands = [
        (
            "Python Import Time",
            "python -c 'import gradio; import pandas; import numpy'",
        ),  # More comprehensive import
        (
            "File System Read (Large)",
            "find /app -type f -print0 | xargs -0 du -b | awk '{total += $1} END {print total}'",
        ),  # Measure total size of files found
        (
            "Database Query (External SQLite)",
            'sqlite3 :memory: "CREATE TABLE test (id INTEGER); INSERT INTO test VALUES (1),(2),(3); SELECT COUNT(*) FROM test;"',
        ),
    ]

    for name, command in system_commands:
        try:
            cmd_result = run_hyperfine_style_benchmark(
                name, command, runs=HYPERFINE_DEFAULT_RUNS
            )
            all_benchmark_results[f"System_{name}"] = (
                cmd_result  # Add to main results for report
            )
            if KEY_ERROR not in cmd_result:
                print(
                    f"✅ {name}: {cmd_result.get(KEY_MEAN, 'N/A'):.4f}s ± {cmd_result.get(KEY_STDDEV, 'N/A'):.4f}s"
                )
            else:
                print(f"❌ {name}: {cmd_result[KEY_ERROR]}")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            all_benchmark_results[f"System_{name}"] = {KEY_ERROR: str(e)}

    # Rewrite the report to include system command benchmarks
    runner.write_markdown_report(all_benchmark_results)

    successful_count = sum(
        1 for res in all_benchmark_results.values() if KEY_ERROR not in res
    )
    total_count = len(all_benchmark_results)

    print(
        f"\n🎉 All benchmarks complete! Results stored in database and {REPORT_FILE_PATH}"
    )
    print("📊 View results in the stats interface or check the markdown report.")
    print(f"\n📈 Benchmark Summary: {successful_count}/{total_count} successful.")
    if runner.docker_build_times:
        print("🐳 Docker build times have been stored in the performance database.")


def run_main_sync_wrapper():
    """Synchronous wrapper to run the main async function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user.")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()  # Print full traceback for debugging


if __name__ == "__main__":
    run_main_sync_wrapper()
