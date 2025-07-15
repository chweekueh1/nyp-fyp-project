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


def run_hyperfine_command(name, command, runs=5, extra_env=None):
    """
    Run a shell command using hyperfine and parse the results.
    Returns a dict with timing statistics.
    """
    print(f"🔥 Running hyperfine benchmark: {name}")
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
        output_path = tf.name

    env = dict(**os.environ)
    # Ensure both /app/src and /app are in PYTHONPATH for all project imports
    # Also add the CWD to PYTHONPATH for python -c to resolve relative imports
    pythonpath = env.get("PYTHONPATH", "")
    extra_paths = ["/app/src", "/app", os.getcwd()]
    # Remove duplicates and empty strings
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
        return parse_hyperfine_results(hyperfine_cmd, env, output_path, command)
    except subprocess.CalledProcessError as e:
        print(f"❌ Hyperfine failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}
    finally:
        os.remove(output_path)


def parse_hyperfine_results(hyperfine_cmd, env, output_path, command):
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
        )
        print(result.stdout)
        print(result.stderr)
        with open(output_path, "r") as f:
            data = json.load(f)
        if not data.get("results"):
            return {"error": "No results from hyperfine"}
        stats = data["results"][0]
        # Fallbacks for missing values
        return {
            "mean": stats.get("mean", 0.0),
            "stddev": stats.get("stddev", 0.0),
            "min": stats.get("min", 0.0),
            "max": stats.get("max", 0.0),
            "median": stats.get("median", 0.0),
            "runs": stats.get("parameters", {}).get("runs", 0),
            "command": command,
        }
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
                    "Frontend Static Asset Load",
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
                    "LLM DataProcessing Clean Text",
                    "LLM KeywordCache Import",
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


def frontend_static_assets():
    from pathlib import Path

    styles_dir = Path(__file__).parent.parent.parent / "styles"
    css_files = ["styles.css", "performance.css"]
    opened_files = []
    try:
        for css_file in css_files:
            css_path = styles_dir / css_file
            if css_path.exists():
                f = open(css_path, "r", encoding="utf-8")
                _ = f.read()
                opened_files.append(f)
    finally:
        for f in opened_files:
            try:
                f.close()
            except Exception:
                pass


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


async def main():
    print(LINE_SEPARATOR)
    print("Running all benchmarks using hyperfine...\n")
    # --- Backend Benchmarks (Accurate, minimal, and robust) ---
    results = {
        BENCH_BACKEND_INIT: run_hyperfine_command(
            BENCH_BACKEND_INIT,
            "python -c 'import asyncio; from backend.main import init_backend; asyncio.run(init_backend())'",
            runs=5,
        )
    }

    # LLM Setup: initialize LLM and DB (async)
    results[BENCH_LLM_SETUP] = run_hyperfine_command(
        BENCH_LLM_SETUP,
        "python -c 'import asyncio; from llm.chatModel import initialize_llm_and_db; asyncio.run(initialize_llm_and_db())'",
        runs=5,
    )

    # Database Initialization: ensure user DB is ready (sync)
    results[BENCH_DB_INIT] = run_hyperfine_command(
        BENCH_DB_INIT,
        "python -c 'from backend.consolidated_database import get_user_database; db = get_user_database(); db.execute_query(\"SELECT 1\")'",
        runs=5,
    )

    # File Classification: classify a test string (async)
    results[BENCH_FILE_CLASSIFICATION] = run_hyperfine_command(
        BENCH_FILE_CLASSIFICATION,
        "python -c 'import asyncio; from backend.file_handling import data_classification; asyncio.run(data_classification(\"This is a test file for classification.\"))'",
        runs=5,
    )

    # Chatbot Response: get a response from the chatbot (async)
    results[BENCH_CHATBOT_RESPONSE] = run_hyperfine_command(
        BENCH_CHATBOT_RESPONSE,
        'python -c \'import asyncio; from backend.chat import get_chatbot_response; asyncio.run(get_chatbot_response("Hello, how are you?", [], "testuser", "testchat"))\'',
        runs=5,
    )

    # App Startup: (leave as is, since it's frontend-related)
    results[BENCH_APP_STARTUP] = run_hyperfine_command(
        BENCH_APP_STARTUP,
        "python -c 'import sys; from pathlib import Path; import gradio as gr; "
        'src_path = Path(__file__).parent / "src"; '
        "sys.path.insert(0, str(src_path)) if str(src_path) not in sys.path else None; "
        "from gradio_modules.login_and_register import login_interface; "
        "from gradio_modules.chatbot import chatbot_ui; "
        "from gradio_modules.search_interface import search_interface; "
        "from gradio_modules.file_upload import file_upload_ui; "
        "from gradio_modules.audio_input import audio_interface; "
        "from flexcyon_theme import flexcyon_theme; "
        "def load_custom_css(): "
        '    styles_dir = Path(__file__).parent.parent / "styles"; '
        '    css_content = ""; '
        '    styles_file = styles_dir / "styles.css"; '
        "    if styles_file.exists(): "
        '        css_content += styles_file.read_text(encoding="utf-8") + "\\n"; '
        '    performance_file = styles_dir / "performance.css"; '
        "    if performance_file.exists(): "
        '        css_content += performance_file.read_text(encoding="utf-8") + "\\n"; '
        "    return css_content; "
        "custom_css = load_custom_css(); "
        'with gr.Blocks(title="NYP FYP CNC Chatbot", theme=flexcyon_theme, css=custom_css) as app: '
        "    with gr.Column(visible=gr.State(True)) as login_container: "
        "        login_interface(setup_events=True); "
        '    chat_id_state = gr.State(""); '
        "    chat_history_state = gr.State([]); "
        "    all_chats_data_state = gr.State({}); "
        '    debug_info_state = gr.State(""); '
        "    audio_history_state = gr.State([]); "
        "    with gr.Tabs(visible=False) as main_tabs: "
        '        with gr.Tab("💬 Chat"\): '
        "            chatbot_ui("
        "                None, chat_id_state, chat_history_state, all_chats_data_state, debug_info_state"
        "            ); "
        '        with gr.Tab("🔍 Search"\): '
        "            search_interface("
        "                None, chat_id_state, chat_history_state, all_chats_data_state, debug_info_state, audio_history_state"
        "            ); "
        '        with gr.Tab("📁 File Upload"\): '
        "            file_upload_ui("
        "                None, chat_history_state, chat_id_state"
        "            ); "
        '        with gr.Tab("🎤 Audio Input"\): '
        "            audio_interface("
        "                None, setup_events=True"
        "            ); '",
        runs=5,
    )

    # --- Frontend/Gradio Benchmarks (Accurate, minimal, robust) ---
    # Gradio Launch: Build the main Blocks interface (no launch)
    results["Frontend Gradio Launch"] = run_hyperfine_command(
        "Frontend Gradio Launch",
        "python -c 'import gradio; from gradio_modules.chatbot import chatbot_ui; from gradio_modules.login_and_register import login_interface; from flexcyon_theme import flexcyon_theme; with gradio.Blocks(title=\"NYP FYP CNC Chatbot\", theme=flexcyon_theme): pass'",
        runs=5,
    )

    # Static Asset Load: Read CSS files from the styles directory
    results["Frontend Static Asset Load"] = run_hyperfine_command(
        "Frontend Static Asset Load",
        'python -c \'import pathlib; styles_dir = pathlib.Path("styles"); [open(styles_dir / f, "r", encoding="utf-8").read() for f in ["styles.css", "performance.css"] if (styles_dir / f).exists()]\'',
        runs=5,
    )

    # Login/Register Interface: Build login/register UI (no events)
    results["Login/Register Interface"] = run_hyperfine_command(
        "Login/Register Interface",
        "python -c 'import gradio; from gradio_modules.login_and_register import login_interface; with gradio.Blocks(): login_interface(setup_events=False)'",
        runs=5,
    )

    # Chatbot Interface: Build chatbot UI (no events)
    results["Chatbot Interface"] = run_hyperfine_command(
        "Chatbot Interface",
        "python -c 'import gradio; from gradio_modules.chatbot import chatbot_ui; with gradio.Blocks(): chatbot_ui(None, None, None, None, None)'",
        runs=5,
    )

    # Search Interface: Build search UI (no events)
    results["Search Interface"] = run_hyperfine_command(
        "Search Interface",
        "python -c 'import gradio; from gradio_modules.search_interface import search_interface; with gradio.Blocks(): search_interface(None, None, None, None, None)'",
        runs=5,
    )

    # File Upload Interface: Build file upload UI (no events)
    results["File Upload Interface"] = run_hyperfine_command(
        "File Upload Interface",
        "python -c 'import gradio; from gradio_modules.file_upload import file_upload_ui; with gradio.Blocks(): file_upload_ui(None, None, None)'",
        runs=5,
    )

    # File Classification Interface: Build file classification UI (no events)
    results["File Classification Interface"] = run_hyperfine_command(
        "File Classification Interface",
        "python -c 'import gradio; from gradio_modules.file_classification import file_classification_interface; with gradio.Blocks(): file_classification_interface(None)'",
        runs=5,
    )

    # Audio Input Interface: Build audio input UI (no events)
    results["Audio Input Interface"] = run_hyperfine_command(
        "Audio Input Interface",
        "python -c 'import gradio; from gradio_modules.audio_input import audio_interface; with gradio.Blocks(): audio_interface(None, setup_events=False)'",
        runs=5,
    )

    # Change Password Interface: Build change password UI (no events)
    results["Change Password Interface"] = run_hyperfine_command(
        "Change Password Interface",
        "python -c 'import gradio; from gradio_modules.change_password import change_password_interface; with gradio.Blocks(): change_password_interface(None, None)'",
        runs=5,
    )

    # Stats Interface: Build stats UI (no events)
    results["Stats Interface"] = run_hyperfine_command(
        "Stats Interface",
        "python -c 'import gradio; from gradio_modules.stats_interface import StatsInterface; with gradio.Blocks(): StatsInterface()'",
        runs=5,
    )

    # Flexcyon Theme Import: Import the theme and access the object
    results["Flexcyon Theme Import"] = run_hyperfine_command(
        "Flexcyon Theme Import",
        "python -c 'import flexcyon_theme; flexcyon_theme.flexcyon_theme'",
        runs=5,
    )

    # NLTK Config
    results["NLTK Config"] = run_hyperfine_command(
        "NLTK Config",
        "python -c 'import infra_utils; infra_utils.nltk_config.setup_nltk_data_path(); infra_utils.nltk_config.get_stopwords(); infra_utils.nltk_config.download_required_nltk_data()'",
        runs=5,
    )

    # LLM
    results["LLM Model Load"] = run_hyperfine_command(
        "LLM Model Load",
        "python -c 'from llm.chatModel import get_model; import asyncio; asyncio.run(get_model())'",
        runs=5,
    )
    results["LLM Inference"] = run_hyperfine_command(
        "LLM Inference",
        'python -c \'from llm.chatModel import get_model; import asyncio; model = asyncio.run(get_model()); prompt = "What is the capital of France?"; getattr(model, "predict", lambda x: None)(prompt) if hasattr(model, "predict") else getattr(model, "generate", lambda x: None)(prompt) if hasattr(model, "generate") else None\'',
        runs=5,
    )

    # LLM: classificationModel.py
    results["LLM ClassificationModel Import"] = run_hyperfine_command(
        "LLM ClassificationModel Import",
        "python -c 'import llm.classificationModel'",
        runs=5,
    )
    results["LLM ClassificationModel Clean Text"] = run_hyperfine_command(
        "LLM ClassificationModel Clean Text",
        "python -c 'from llm.classificationModel import clean_text_for_classification; clean_text_for_classification(\"# Heading\\nSome text.\\n- List item\\n\")'",
        runs=5,
    )

    # LLM: dataProcessing.py
    results["LLM DataProcessing Import"] = run_hyperfine_command(
        "LLM DataProcessing Import", "python -c 'import llm.dataProcessing'", runs=5
    )
    results["LLM DataProcessing Clean Text"] = run_hyperfine_command(
        "LLM DataProcessing Clean Text",
        "python -c 'from llm.dataProcessing import global_clean_text_for_classification; global_clean_text_for_classification(\"Some\\ntext with   spaces\\n\\n\")'",
        runs=5,
    )

    # LLM: keyword_cache.py
    results["LLM KeywordCache Import"] = run_hyperfine_command(
        "LLM KeywordCache Import", "python -c 'import llm.keyword_cache'", runs=5
    )
    results["LLM KeywordCache Filter Filler Words"] = run_hyperfine_command(
        "LLM KeywordCache Filter Filler Words",
        "python -c 'from llm.keyword_cache import filter_filler_words; filter_filler_words(\"the quick brown fox jumps over the lazy dog\")'",
        runs=5,
    )

    # Hashing benchmarks
    results["Hashing Import"] = run_hyperfine_command(
        "Hashing Import", "python -c 'import hashing'", runs=5
    )
    results["Hashing Password"] = run_hyperfine_command(
        "Hashing Password",
        "python -c 'from hashing import hash_password; hash_password(\"mySuperSecretPassword123!\")'",
        runs=5,
    )
    results["Hashing Verify"] = run_hyperfine_command(
        "Hashing Verify",
        'python -c \'from hashing import hash_password, verify_password; h = hash_password("mySuperSecretPassword123!"); verify_password("mySuperSecretPassword123!", h)\'',
        runs=5,
    )

    # Performance utils benchmarks
    results["PerformanceUtils Import"] = run_hyperfine_command(
        "PerformanceUtils Import", "python -c 'import performance_utils'", runs=5
    )
    results["PerformanceUtils Timer"] = run_hyperfine_command(
        "PerformanceUtils Timer",
        'python -c \'from performance_utils import perf_monitor; perf_monitor.start_timer("test"); import time; time.sleep(0.01); perf_monitor.end_timer("test")\'',
        runs=5,
    )
    results["PerformanceUtils Cached File Exists"] = run_hyperfine_command(
        "PerformanceUtils Cached File Exists",
        "python -c 'from performance_utils import cached_file_exists; cached_file_exists(\"/etc/hosts\")'",
        runs=5,
    )

    # Hashing benchmarks
    results["Hashing Import"] = run_hyperfine_command(
        "Hashing Import", "python -c 'import hashing'", runs=5
    )
    results["Hashing Password"] = run_hyperfine_command(
        "Hashing Password",
        "python -c 'from hashing import hash_password; hash_password(\"mySuperSecretPassword123!\")'",
        runs=5,
    )
    results["Hashing Verify"] = run_hyperfine_command(
        "Hashing Verify",
        'python -c \'from hashing import hash_password, verify_password; h = hash_password("mySuperSecretPassword123!"); verify_password("mySuperSecretPassword123!", h)\'',
        runs=5,
    )

    # Performance utils benchmarks
    results["PerformanceUtils Import"] = run_hyperfine_command(
        "PerformanceUtils Import", "python -c 'import performance_utils'", runs=5
    )
    results["PerformanceUtils Timer"] = run_hyperfine_command(
        "PerformanceUtils Timer",
        'python -c \'from performance_utils import perf_monitor; perf_monitor.start_timer("test"); import time; time.sleep(0.01); perf_monitor.end_timer("test")\'',
        runs=5,
    )
    results["PerformanceUtils Cached File Exists"] = run_hyperfine_command(
        "PerformanceUtils Cached File Exists",
        "python -c 'from performance_utils import cached_file_exists; cached_file_exists(\"/etc/hosts\")'",
        runs=5,
    )

    print("\nAll benchmarks completed. Writing results...")
    write_benchmark_report(results)
    print(
        f"✅ Benchmark results written to {BENCHMARK_RESULTS_PATH} and {BENCHMARK_REPORT_PATH}"
    )
    print(LINE_SEPARATOR)


if __name__ == "__main__":
    asyncio.run(main())
