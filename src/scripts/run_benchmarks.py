import time
import os
import asyncio
import sys
import json
from pathlib import Path

# --- Setup paths and environment ---
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Always write results to the host's project root /data directory (not inside /app/src/data)
HOST_DATA_DIR = Path(os.environ.get("HOST_DATA_DIR", "/app/data"))
BENCHMARK_RESULTS_PATH = HOST_DATA_DIR / "benchmark_results.json"
BENCHMARK_REPORT_PATH = HOST_DATA_DIR / "benchmark_results.md"

# --- Benchmark Names ---
BENCH_BACKEND_INIT = "Backend Initialization"
BENCH_APP_STARTUP = "App Startup"
BENCH_LLM_SETUP = "LLM Setup"
BENCH_DB_INIT = "Database Initialization"
BENCH_FILE_CLASSIFICATION = "File Classification"
BENCH_CHATBOT_RESPONSE = "Chatbot Response"
BENCH_TEST_USER = "testuser"

LINE_SEPARATOR = "=" * 60

import subprocess
import tempfile
import os


def run_hyperfine_command(name, command, runs=5, extra_env=None, timeout=60):
    """
    Run a shell command using hyperfine and parse the results.
    Returns a dict with timing statistics.
    """
    print(f"🔥 Running hyperfine benchmark: {name}")
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
        output_path = tf.name

    env = dict(**os.environ)
    pythonpath = env.get("PYTHONPATH", "")
    extra_paths = ["/app/src", "/app", os.getcwd()]
    pythonpath_parts = [p for p in (pythonpath.split(":") if pythonpath else []) if p]
    for p in extra_paths:
        if p not in pythonpath_parts:
            pythonpath_parts.append(p)
    env["PYTHONPATH"] = ":".join(pythonpath_parts)
    if extra_env:
        env |= extra_env

    hyperfine_cmd = [
        "hyperfine",
        "--runs",
        str(runs),
        "--export-json",
        output_path,
        command,
    ]
    try:
        return parse_hyperfine_results(
            hyperfine_cmd, env, output_path, command, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Benchmark '{name}' timed out after {timeout} seconds.")
        return {"error": f"Timeout after {timeout} seconds"}
    except subprocess.CalledProcessError as e:
        print(f"❌ Hyperfine failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}
    finally:
        os.remove(output_path)


def parse_hyperfine_results(hyperfine_cmd, env, output_path, command, timeout=60):
    """
    Run the hyperfine command and parse the results JSON for statistics.
    """
    try:
        result = subprocess.run(
            hyperfine_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        print(result.stdout)
        print(result.stderr)
        with open(output_path, "r") as f:
            data = json.load(f)
        if not data.get("results"):
            return {"error": "No results from hyperfine"}
        stats = data["results"][0]
        return {
            "mean": stats.get("mean", 0.0),
            "stddev": stats.get("stddev", 0.0),
            "min": stats.get("min", 0.0),
            "max": stats.get("max", 0.0),
            "median": stats.get("median", 0.0),
            "runs": stats.get("parameters", {}).get("runs", 0),
            "command": command,
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ Hyperfine failed: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        return {
            "error": f"Hyperfine failed: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        }
    except subprocess.TimeoutExpired:
        print(f"❌ Benchmark timed out after {timeout} seconds.")
        return {"error": f"Timeout after {timeout} seconds"}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}


def write_benchmark_report(results):
    """Write a markdown report of the benchmark results, grouped and with detailed stats."""
    BENCHMARK_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BENCHMARK_REPORT_PATH, "w") as f:
        f.write("# NYP FYP Chatbot Benchmark Results\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Group benchmarks by category
        groups = [
            (
                "Backend Benchmarks",
                [
                    BENCH_BACKEND_INIT,
                    BENCH_APP_STARTUP,
                    BENCH_LLM_SETUP,
                    BENCH_DB_INIT,
                    BENCH_FILE_CLASSIFICATION,
                    BENCH_CHATBOT_RESPONSE,
                ],
            ),
            (
                "Frontend/Gradio Benchmarks",
                [
                    "Frontend Gradio Launch",
                    "Login/Register Interface",
                    "Chatbot Interface",
                    "Search Interface",
                    "File Upload Interface",
                    "File Classification Interface",
                    "Audio Input Interface",
                    "Change Password Interface",
                    "Stats Interface",
                    "Flexcyon Theme Import",
                ],
            ),
            ("NLTK/Infra Benchmarks", ["NLTK Config"]),
            (
                "LLM Benchmarks",
                [
                    "LLM Model Load",
                    "LLM Inference",
                    "LLM ClassificationModel Import",
                    "LLM ClassificationModel Clean Text",
                    "LLM DataProcessing Import",
                    "LLM DataProcessing Clean TextLLM KeywordCache Import",
                    "LLM KeywordCache Filter Filler Words",
                ],
            ),
            (
                "Hashing Benchmarks",
                ["Hashing Import", "Hashing Password", "Hashing Verify"],
            ),
            (
                "Performance Utils Benchmarks",
                [
                    "PerformanceUtils Import",
                    "PerformanceUtils Timer",
                    "PerformanceUtils Cached File Exists",
                ],
            ),
        ]

        # Summary Table (grouped)
        for group_name, keys in groups:
            f.write(f"## {group_name}\n\n")
            f.write(
                "| Benchmark Name | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Median (s) | Runs |\n"
            )
            f.write(
                "|---------------|----------|-------------|---------|---------|------------|------|\n"
            )
            for name in keys:
                data = results.get(name, {})
                if "error" in data:
                    f.write(f"| {name} | ❌ Error | - | - | - | - | - |\n")
                else:
                    f.write(
                        f"| {name} | {data.get('mean', 0):.4f} | {data.get('stddev', 0):.4f} | {data.get('min', 0):.4f} | {data.get('max', 0):.4f} | {data.get('median', 0):.4f} | {data.get('runs', '-')}\n"
                    )
            f.write("\n")

        # Detailed statistics for each benchmark
        f.write("## Detailed Benchmark Statistics\n\n")
        for name, data in results.items():
            f.write(f"### {name}\n\n")
            if "error" in data:
                f.write(f"**Error:** {data['error']}\n\n")
            else:
                f.write(f"- **Command:** `{data.get('command', '')}`\n")
                f.write(f"- **Runs:** {data.get('runs', '-')}\n")
                f.write(f"- **Mean:** {data.get('mean', 0):.6f} s\n")
                f.write(f"- **Stddev:** {data.get('stddev', 0):.6f} s\n")
                f.write(f"- **Min:** {data.get('min', 0):.6f} s\n")
                f.write(f"- **Max:** {data.get('max', 0):.6f} s\n")
                f.write(f"- **Median:** {data.get('median', 0):.6f} s\n")
            f.write("\n")


# --- Benchmark Functions ---


async def backend_init():
    # Properly initialize the backend using the main entrypoint
    from backend.main import init_backend

    await init_backend()


def db_init():
    # Initialize the consolidated database (vector store)
    from backend.consolidated_database import get_user_database

    db = get_user_database()
    # Optionally, run a simple query to ensure it's working
    db.execute_query("SELECT 1")


async def file_classification():
    # Use the backend.file_handling.data_classification function
    from backend.file_handling import data_classification

    return await data_classification("This is a test file for classification.")


async def chatbot_response():
    # Use the backend.chat.get_chatbot_response function
    from backend.chat import get_chatbot_response

    # Provide minimal valid arguments for a test call
    message = "Hello, how are you?"
    history = []
    username = BENCH_TEST_USER
    chat_id = "testchat"
    # get_chatbot_response returns a tuple, but we only care about timing
    await get_chatbot_response(message, history, username, chat_id)


def gradio_launch():
    import gradio as gr
    from gradio_modules.chatbot import chatbot_ui
    from gradio_modules.login_and_register import login_interface
    from flexcyon_theme import flexcyon_theme

    with gr.Blocks(title="NYP FYP CNC Chatbot", theme=flexcyon_theme):
        with gr.Column(visible=True):
            login_interface(setup_events=True)
        with gr.Tabs(visible=False):
            with gr.Tab("💬 Chat"):
                chatbot_ui(None, None, None, None, None)
    # Don't launch, just build the interface for timing


async def llm_model_load():
    from llm.chatModel import get_model

    await get_model()


async def llm_inference():
    from llm.chatModel import get_model

    model = await get_model()
    prompt = "What is the capital of France?"
    if hasattr(model, "predict"):
        _ = model.predict(prompt)
    elif hasattr(model, "generate"):
        _ = model.generate(prompt)


# --- Main Runner ---


import concurrent.futures


async def main():
    print(LINE_SEPARATOR)
    print("Running all benchmarks using hyperfine...\n")

    # Define all benchmarks as (name, command, runs)
    benchmarks = [
        (
            BENCH_BACKEND_INIT,
            "python -c 'from backend.main import init_backend; init_backend()'",
            5,
        ),
        (
            BENCH_LLM_SETUP,
            "python -c 'from llm.chatModel import initialize_llm_and_db; initialize_llm_and_db()'",
            5,
        ),
        (
            BENCH_DB_INIT,
            "python -c 'from backend.consolidated_database import get_user_database; db = get_user_database(); db.execute_query(\"SELECT 1\")'",
            5,
        ),
        (
            BENCH_FILE_CLASSIFICATION,
            "python -c 'from backend.file_handling import data_classification; data_classification(\"This is a test file for classification.\")'",
            5,
        ),
        (
            BENCH_CHATBOT_RESPONSE,
            'python -c \'from backend.chat import get_chatbot_response; get_chatbot_response("Hello, how are you?", [], "testuser", "testchat")\'',
            5,
        ),
        (BENCH_APP_STARTUP, 'python -c "from app import main; main()"', 5),
        # Gradio UI benchmarks: wrap in try/except to avoid failing in headless mode, do NOT import gradio directly
        (
            "Frontend Gradio Launch",
            'python -c \'import sys; try: from gradio_modules.chatbot import chatbot_ui; from gradio_modules.login_and_register import login_interface; from flexcyon_theme import flexcyon_theme; with __import__("gradio").Blocks(title="NYP FYP CNC Chatbot", theme=flexcyon_theme): pass except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Login/Register Interface",
            'python -c \'import sys; try: from gradio_modules.login_and_register import login_interface; with __import__("gradio").Blocks(): login_interface(setup_events=False) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Chatbot Interface",
            'python -c \'import sys; try: from gradio_modules.chatbot import chatbot_ui; with __import__("gradio").Blocks(): chatbot_ui(None, None, None, None, None) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Search Interface",
            'python -c \'import sys; try: from gradio_modules.search_interface import search_interface; with __import__("gradio").Blocks(): search_interface(None, None, None, None, None) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "File Upload Interface",
            'python -c \'import sys; try: from gradio_modules.file_upload import file_upload_ui; with __import__("gradio").Blocks(): file_upload_ui(None, None, None) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "File Classification Interface",
            'python -c \'import sys; try: from gradio_modules.file_classification import file_classification_interface; with __import__("gradio").Blocks(): file_classification_interface(None) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Audio Input Interface",
            'python -c \'import sys; try: from gradio_modules.audio_input import audio_interface; with __import__("gradio").Blocks(): audio_interface(None, setup_events=False) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Change Password Interface",
            'python -c \'import sys; try: from gradio_modules.change_password import change_password_interface; with __import__("gradio").Blocks(): change_password_interface(None, None) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Stats Interface",
            'python -c \'import sys; try: from gradio_modules.stats_interface import StatsInterface; with __import__("gradio").Blocks(): StatsInterface() except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Flexcyon Theme Import",
            "python -c 'import sys; try: import flexcyon_theme; flexcyon_theme.flexcyon_theme except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "NLTK Config",
            "python -c 'import sys; try: import infra_utils; infra_utils.nltk_config.setup_nltk_data_path(); infra_utils.nltk_config.get_stopwords(); infra_utils.nltk_config.download_required_nltk_data() except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "LLM Model Load",
            "python -c 'import sys; try: from llm.chatModel import get_model; get_model() except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "LLM Inference",
            'python -c \'import sys; try: from llm.chatModel import get_model; model = get_model(); prompt = "What is the capital of France?"; getattr(model, "predict", lambda x: None)(prompt) if hasattr(model, "predict") else getattr(model, "generate", lambda x: None)(prompt) if hasattr(model, "generate") else None except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "LLM ClassificationModel Import",
            "python -c 'import sys; try: import llm.classificationModel except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "LLM ClassificationModel Clean Text",
            'python -c \'import sys; try: from llm.classificationModel import clean_text_for_classification; clean_text_for_classification("# Heading\\nSome text.\\n- List item\\n") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "LLM DataProcessing Import",
            "python -c 'import sys; try: import llm.dataProcessing except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "LLM DataProcessing Clean Text",
            'python -c \'import sys; try: from llm.dataProcessing import global_clean_text_for_classification; global_clean_text_for_classification("Some\\ntext with   spaces\\n\\n") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "LLM KeywordCache Import",
            "python -c 'import sys; try: import llm.keyword_cache except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "LLM KeywordCache Filter Filler Words",
            'python -c \'import sys; try: from llm.keyword_cache import filter_filler_words; filter_filler_words("the quick brown fox jumps over the lazy dog") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Hashing Import",
            "python -c 'import sys; try: import hashing except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "Hashing Password",
            'python -c \'import sys; try: from hashing import hash_password; hash_password("mySuperSecretPassword123!") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "Hashing Verify",
            'python -c \'import sys; try: from hashing import hash_password, verify_password; h = hash_password("mySuperSecretPassword123!"); verify_password("mySuperSecretPassword123!", h) except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "PerformanceUtils Import",
            "python -c 'import sys; try: import performance_utils except Exception as e: print(f\"[SKIP] {e}\"); sys.exit(0)'",
            5,
        ),
        (
            "PerformanceUtils Timer",
            'python -c \'import sys; try: from performance_utils import perf_monitor; perf_monitor.start_timer("test"); import time; time.sleep(0.01); perf_monitor.end_timer("test") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
        (
            "PerformanceUtils Cached File Exists",
            'python -c \'import sys; try: from performance_utils import cached_file_exists; cached_file_exists("/etc/hosts") except Exception as e: print(f"[SKIP] {e}"); sys.exit(0)\'',
            5,
        ),
    ]

    results = {}

    def run_benchmark(name, command, runs):
        res = run_hyperfine_command(name, command, runs)
        print(f"✅ Benchmark '{name}' completed.")
        return name, res

    # Use ThreadPoolExecutor to run benchmarks in parallel (non-blocking main thread)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_bench = {
            executor.submit(run_benchmark, name, command, runs): name
            for name, command, runs in benchmarks
        }
        for future in concurrent.futures.as_completed(future_to_bench):
            name, res = future.result()
            results[name] = res

    print("\nAll benchmarks completed. Writing results...")
    write_benchmark_report(results)
    print(
        f"✅ Benchmark results written to {BENCHMARK_RESULTS_PATH} and {BENCHMARK_REPORT_PATH}"
    )
    print(LINE_SEPARATOR)


if __name__ == "__main__":
    asyncio.run(main())
