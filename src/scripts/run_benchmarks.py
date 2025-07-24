import contextlib
import time
import os
import sys
import json
import logging
import subprocess
import tempfile
from pathlib import Path

# --- Setup paths and environment ---
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if os.environ.get("IN_DOCKER") == "1":
    DATA_DIR = Path("/app/data")
    os.environ["BASE_CHATBOT_DIR"] = "/app"
    os.environ["KEYWORD_CACHE_PATH"] = "data/keyword_cache/keywords_cache.db"
    os.environ["DATABASE_PATH"] = "data/vector_store/chroma_db"
    os.environ["KEYWORDS_DATABANK_PATH"] = "data/keywords_databank"
    os.environ["LANGCHAIN_CHECKPOINT_PATH"] = (
        "data/memory_persistence/checkpoint.sqlite"
    )
    for fname in ["benchmark_results.md", "benchmark_results.json", "app.log"]:
        fpath = DATA_DIR / fname
        if fpath.exists():
            try:
                fpath.unlink()
            except Exception as e:
                print(f"Warning: Could not remove {fname}: {e}")
else:
    DATA_DIR = Path(__file__).parent.parent / "data"
BENCHMARK_LOG_PATH = DATA_DIR / "app.log"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_RESULTS_PATH = DATA_DIR / "benchmark_results.json"
BENCHMARK_REPORT_PATH = DATA_DIR / "benchmark_results.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(BENCHMARK_LOG_PATH, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)

LINE_SEPARATOR = "=" * 60


def run_hyperfine_command(name, command, runs=5, extra_env=None, timeout=60):
    """
    Run a shell command using hyperfine and parse the results.
    Returns a dict with timing statistics, or None if failed/timed out/non-empty STDERR.
    """
    logging.info(f"🔥 Running hyperfine benchmark: {name}")
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
        output_path = tf.name

    env = dict(os.environ)
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
        "--show-output",
        command,
    ]
    try:
        result = subprocess.run(
            hyperfine_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        stderr_content = result.stderr.strip()
        if stderr_content:
            return None
        with open(output_path, "r") as f:
            data = json.load(f)
        if not data.get("results"):
            return None
        stats = data["results"][0]
        runs_val = len(stats["times"]) if "times" in stats else 0
        with open(BENCHMARK_LOG_PATH, "a") as logf:
            logf.write(f"\n[Benchmark Command]: {' '.join(hyperfine_cmd)}\n")
            logf.write("[STDOUT]\n")
            logf.write(result.stdout)
            logf.write("\n[STDERR]\n")
            logf.write(result.stderr)
            logf.write("\n" + "=" * 80 + "\n")
        return {
            "mean": stats.get("mean", 0.0),
            "stddev": stats.get("stddev", 0.0),
            "min": stats.get("min", 0.0),
            "max": stats.get("max", 0.0),
            "median": stats.get("median", 0.0),
            "runs": runs_val,
            "command": command,
        }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception):
        return None
    finally:
        os.remove(output_path)


import platform
import psutil


def write_benchmark_report(results, total_runtime=None):
    """
    Write a markdown report of the benchmark results, grouped and with detailed stats.
    """
    from datetime import datetime, timedelta, timezone

    def is_valid_benchmark(data):
        """Return True if the benchmark data is valid and should be included in the report."""
        if not data or "error" in data:
            return False
        if isinstance(data, dict) and data.get("stderr", "").strip():
            return False
        return not isinstance(data, dict) or any(
            data.get(k, 0) != 0 for k in ["mean", "stddev", "min", "max", "median"]
        )

    def render_group_table(group_name, keys, results):
        """Render a markdown table for a group of benchmarks."""
        rows = []
        for name in keys:
            data = results.get(name)
            if not is_valid_benchmark(data):
                continue
            runs_val = data.get("runs", "-")
            runs_str = (
                str(runs_val) if isinstance(runs_val, int) and runs_val > 0 else "-"
            )
            rows.append(
                f"| {name} | {data.get('mean', 0):.4f} | {data.get('stddev', 0):.4f} | {data.get('min', 0):.4f} | {data.get('max', 0):.4f} | {data.get('median', 0):.4f} | {runs_str} |"
            )
        if not rows:
            return ""
        header = (
            f"## {group_name}\n\n"
            "| Benchmark Name | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Median (s) | Runs |\n"
            "|---------------|----------|-------------|---------|---------|------------|------|\n"
        )
        return header + "\n".join(rows) + "\n\n"

    def render_detailed_stats(results):
        """Render detailed statistics for each valid benchmark."""
        output = ["## Detailed Benchmark Statistics\n"]
        for name, data in results.items():
            if not is_valid_benchmark(data):
                continue
            output.append(f"### {name}\n")
            output.append(f"- **Command:** `{data.get('command', '')}`")
            output.append(f"- **Runs:** {data.get('runs', '-')}")
            output.append(f"- **Mean:** {data.get('mean', 0):.6f} s")
            output.append(f"- **Stddev:** {data.get('stddev', 0):.6f} s")
            output.append(f"- **Min:** {data.get('min', 0):.6f} s")
            output.append(f"- **Max:** {data.get('max', 0):.6f} s")
            output.append(f"- **Median:** {data.get('median', 0):.6f} s\n")
        return "\n".join(output)

    BENCHMARK_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if BENCHMARK_REPORT_PATH.exists():
        BENCHMARK_REPORT_PATH.unlink()

    with open(BENCHMARK_REPORT_PATH, "w") as f:
        f.write("# NYP FYP Chatbot Benchmark Results\n\n")
        utc8 = timezone(timedelta(hours=8))
        now_utc8 = datetime.now(utc8)
        f.write(f"**Generated:** {now_utc8.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)\n\n")
        if total_runtime is not None:
            f.write(f"**Total Benchmark Runtime:** {total_runtime:.2f} seconds\n\n")
        f.write("## System Information\n\n")
        f.write(
            f"- **OS:** {platform.system()} {platform.release()} ({platform.version()})\n"
        )
        f.write(
            f"- **Python version:** {platform.python_version()} ({platform.python_implementation()})\n"
        )
        f.write(f"- **Machine:** {platform.machine()}\n")
        f.write(f"- **Processor:** {platform.processor()}\n")
        with contextlib.suppress(Exception):
            f.write(f"- **CPU cores:** {psutil.cpu_count(logical=True)}\n")
            mem = psutil.virtual_memory()
            f.write(f"- **RAM:** {round(mem.total / (1024**3), 2)} GB\n")
        f.write(
            f"- **Docker:** {'Yes' if os.environ.get('IN_DOCKER') == '1' else 'No'}\n"
        )
        f.write(f"- **Working Directory:** {os.getcwd()}\n")
        f.write(f"- **PYTHONPATH:** {os.environ.get('PYTHONPATH', '')}\n\n")

        groups = [
            ("NLTK/Infra Benchmarks", ["NLTK Config"]),
            (
                "LLM Benchmarks",
                [
                    "LLM ClassificationModel Import",
                    "LLM ClassificationModel Clean Text",
                    "LLM DataProcessing Import",
                    "LLM DataProcessing Clean Text",
                    "LLM KeywordCache Filter Filler Words",
                ],
            ),
            (
                "Hashing Benchmarks",
                ["Hashing Import", "Hashing Password"],
            ),
            (
                "Performance Utils Benchmarks",
                [
                    "PerformanceUtils Timer",
                    "PerformanceUtils Cached File Exists",
                ],
            ),
            (
                "Database Benchmarks",
                [
                    "Database Initialization",
                ],
            ),
        ]

        for group_name, keys in groups:
            table = render_group_table(group_name, keys, results)
            if table:
                f.write(table)

        f.write(render_detailed_stats(results))


import concurrent.futures


def main():
    print(LINE_SEPARATOR)
    print("Running all benchmarks using hyperfine...\n")

    benchmarks = [
        (
            "NLTK Config",
            "python -c 'from infra_utils import nltk_config; nltk_config.setup_nltk_data_path(); nltk_config.get_stopwords(); nltk_config.download_required_nltk_data()'",
            5,
        ),
        (
            "LLM ClassificationModel Import",
            "python -c 'import llm.classificationModel'",
            5,
        ),
        (
            "Database Initialization",
            "python -c 'from backend.consolidated_database import get_user_database; db = get_conslidated_database(); db.execute_query(\"SELECT 1\")'",
            5,
        ),
        (
            "LLM ClassificationModel Clean Text",
            "python -c 'from llm.classificationModel import clean_text_for_classification; clean_text_for_classification(\"# Heading\\nSome text.\\n- List item\\n\")'",
            5,
        ),
        (
            "Hashing Import",
            "python -c 'import hashing'",
            5,
        ),
        (
            "Hashing Password",
            "python -c 'from hashing import hash_password; hash_password(\"mySuperSecretPassword123!\")'",
            5,
        ),
        (
            "PerformanceUtils Timer",
            'python -c \'from performance_utils import perf_monitor; perf_monitor.start_timer("test"); import time; time.sleep(0.01); perf_monitor.end_timer("test")\'',
            5,
        ),
        (
            "PerformanceUtils Cached File Exists",
            "python -c 'from performance_utils import cached_file_exists; cached_file_exists(\"/etc/hosts\")'",
            5,
        ),
        (
            "LLM KeywordCache Filter Filler Words",
            "python -c 'from llm.keyword_cache import filter_filler_words; filter_filler_words(\"the quick brown fox jumps over the lazy dog\")'",
            5,
        ),
        (
            "LLM DataProcessing Import",
            "python -c 'import llm.dataProcessing'",
            5,
        ),
        (
            "LLM DataProcessing Clean Text",
            "python -c 'from llm.dataProcessing import global_clean_text_for_classification; global_clean_text_for_classification(\"Some\\ntext with   spaces\\n\\n\")'",
            5,
        ),
    ]

    results = {}

    def run_benchmark(name, command, runs):
        res = run_hyperfine_command(name, command, runs)
        if res is not None:
            print(f"✅ Benchmark '{name}' completed.")
            return name, res
        else:
            print(f"❌ Benchmark '{name}' failed or had non-empty STDERR. Skipping.")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_bench = {
            executor.submit(run_benchmark, name, command, runs): name
            for name, command, runs in benchmarks
        }
        for future in concurrent.futures.as_completed(future_to_bench):
            result = future.result()
            if result is not None:
                name, res = result
                results[name] = res

    print("\nAll benchmarks completed. Writing results...")
    total_runtime = (
        time.time() - BENCHMARK_START_TIME
        if "BENCHMARK_START_TIME" in globals()
        else None
    )
    write_benchmark_report(results, total_runtime=total_runtime)
    with open(BENCHMARK_LOG_PATH, "a") as logf:
        logf.write("\n[INFO] All benchmarks completed successfully.\n")
        logf.write(
            f"[INFO] Benchmark results written to {BENCHMARK_RESULTS_PATH} and {BENCHMARK_REPORT_PATH}\n"
        )
        if total_runtime is not None:
            logf.write(f"[INFO] Total Benchmark Runtime: {total_runtime:.2f} seconds\n")
        logf.write("=" * 80 + "\n")
    print(
        f"✅ Benchmark results written to {BENCHMARK_RESULTS_PATH} and {BENCHMARK_REPORT_PATH} and logs to {BENCHMARK_LOG_PATH}"
    )
    print(LINE_SEPARATOR)


if __name__ == "__main__":
    global BENCHMARK_START_TIME
    BENCHMARK_START_TIME = time.time()
    main()
