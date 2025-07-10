"""
Performance benchmarking script for NYP FYP CNC Chatbot.

This script runs and records benchmarks for LLM, database, file classification, and other core components.
"""

import time
import statistics
from pathlib import Path
from dotenv import load_dotenv

# Ensure /downloads exists
DOWNLOADS = Path("/downloads")
DOWNLOADS.mkdir(parents=True, exist_ok=True)
RESULT_MD = DOWNLOADS / "benchmark_results.md"

# Load .env variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=True)

BENCHMARKS = [
    {
        "name": "LLM Setup",
        "func": lambda: __import__("llm.chatModel").chatModel.initialize_llm_and_db(),
        "is_async": True,
    },
    {
        "name": "Database Initialization",
        "func": lambda: __import__(
            "llm.dataProcessing"
        ).dataProcessing.initialiseDatabase(),
        "is_async": False,
    },
    {
        "name": "File Classification",
        "func": lambda: __import__("backend").backend.data_classification("test text"),
        "is_async": False,
    },
    {
        "name": "Chatbot Response",
        "func": lambda: __import__("backend.chat").chat.get_chatbot_response(
            "Hello", [], "testuser", "testchat"
        ),
        "is_async": True,
    },
    {
        "name": "Audio Transcription",
        "func": lambda: __import__("backend").backend.transcribe_audio("test.wav"),
        "is_async": False,
    },
    {
        "name": "NLTK Stopwords Loading",
        "func": lambda: __import__("nltk.corpus").corpus.stopwords.words("english"),
        "is_async": False,
    },
    {
        "name": "LangChain Initialization",
        "func": lambda: __import__("langchain_openai").openai.OpenAIEmbeddings(
            model="text-embedding-3-small"
        ),
        "is_async": False,
    },
]

RUNS = 5
WARMUP = 1


def run_benchmark(bench):
    times = []
    # Warmup
    for _ in range(WARMUP):
        if bench["is_async"]:
            import asyncio

            asyncio.run(bench["func"]())
        else:
            bench["func"]()
    # Timed runs
    for _ in range(RUNS):
        start = time.perf_counter()
        if bench["is_async"]:
            import asyncio

            asyncio.run(bench["func"]())
        else:
            bench["func"]()
        end = time.perf_counter()
        times.append(end - start)
    return times


def summarize(times):
    return {
        "mean": statistics.mean(times),
        "stddev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "runs": len(times),
    }


def write_markdown(results):
    with open(RESULT_MD, "w") as f:
        f.write("# NYP FYP Chatbot Benchmark Results\n\n")
        for name, stats in results.items():
            f.write(f"## {name}\n\n")
            f.write("| Metric | Value (seconds) |\n")
            f.write("|--------|----------------|\n")
            f.write(f"| Mean   | {stats['mean']:.4f} |\n")
            f.write(f"| Stddev | {stats['stddev']:.4f} |\n")
            f.write(f"| Min    | {stats['min']:.4f} |\n")
            f.write(f"| Max    | {stats['max']:.4f} |\n")
            f.write(f"| Runs   | {stats['runs']} |\n\n")
    print(f"Benchmarks complete. All results written to {RESULT_MD}")


def main():
    results = {}
    for bench in BENCHMARKS:
        print(f"Benchmarking {bench['name']}...")
        try:
            times = run_benchmark(bench)
            stats = summarize(times)
            results[bench["name"]] = stats
        except Exception as e:
            results[bench["name"]] = {"error": str(e)}
    write_markdown(results)


if __name__ == "__main__":
    main()
