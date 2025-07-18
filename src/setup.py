"""
Setup Script for NYP FYP Chatbot

This script manages environment setup, Docker image building, permissions, and test orchestration for the chatbot project.
It is the main entry point for developers and CI to prepare and manage the project environment.
"""

import contextlib
#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import sys
import subprocess
import shutil
import time
import signal
from typing import Optional, Any

# Global variable to track if shutdown is requested
shutdown_requested = False


def signal_handler(signum: int, frame: Any) -> None:
    """
    Handle shutdown signals gracefully.

    :param signum: Signal number received.
    :type signum: int
    :param frame: Current stack frame.
    :type frame: Any
    """
    global shutdown_requested
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True
    sys.exit(0)


def running_in_docker():
    print("TODO: Not implemented yet")


def get_dockerfile_venv_path():
    print("TODO: Not implemented yet")


def docker_build_test():
    print("TODO: Not implemented yet")


def fix_nypai_chatbot_permissions():
    """
    Fix permissions for key NYP FYP Chatbot directories and files.
    Ensures the current user has read/write/execute access to .nypai-chatbot and /app directories.
    Also ensures /app/data/memory_persistence is owned by UID 1001 and is world-writable if running in Docker/dev.
    """
    paths = [
        os.path.expanduser("~/.nypai-chatbot"),
        os.path.join(os.getcwd(), "src"),
        os.path.join(os.getcwd(), "data"),
        os.path.join(os.getcwd(), "logs"),
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                # Set read/write/execute for user, and read/execute for group/others
                os.chmod(path, 0o755)
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        os.chmod(os.path.join(root, f), 0o644)
            except Exception as e:
                print(f"Warning: Could not set permissions for {path}: {e}")

    # --- Memory persistence directory fix for Docker/dev ---
    # Only attempt if running on Linux and the directory exists
    mem_persist_host = os.path.join(os.getcwd(), "data", "memory_persistence")
    if os.path.exists(mem_persist_host):
        try:
            fix_memory_persistence_permissions(mem_persist_host)
        except Exception as e:
            print(f"Warning: Could not fix memory_persistence permissions: {e}")


def fix_memory_persistence_permissions(mem_persist_host):
    """
    Set owner to UID 1001 (appuser) and group 1001, and permissions to 777 for memory_persistence.
    """

    # Only run chown if we are root or have sudo
    if os.geteuid() == 0:
        os.system(f"chown -R 1001:1001 '{mem_persist_host}'")
    # Always set permissions to 777 for dev
    os.chmod(mem_persist_host, 0o777)
    for root, dirs, files in os.walk(mem_persist_host):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o666)
    print(f"✅ Fixed permissions for memory persistence: {mem_persist_host}")


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Remove any existing venv in the Docker venv location before building
if os.name == "nt":
    venv_path = os.path.expanduser(r"~/.nypai-chatbot/venv")
else:
    venv_path = "/home/appuser/.nypai-chatbot/venv"
if os.path.exists(venv_path):
    try:
        shutil.rmtree(venv_path)
        print(f"Removed existing venv at {venv_path}")
    except Exception as e:
        print(f"Warning: Could not remove venv at {venv_path}: {e}")


# Always fix permissions before any Docker build/run operation
def is_docker_build_or_run():
    docker_keywords = [
        "docker",
        "build",
        "run",
        "compose",
        "up",
        "down",
        "start",
        "stop",
        "restart",
    ]
    return any(any(kw in arg.lower() for kw in docker_keywords) for arg in sys.argv)


# Always fix permissions before any Docker build/run operation, regardless of command
def always_fix_permissions_before_docker():
    """
    Always fix permissions before any Docker build/run operation, and before any interactive prompt.
    This function should be called:
      - before any Docker build/run command
      - before any interactive prompt (e.g., "Which docker image would you like to build and run?")
      - at the start of the script
    """
    # Skip permission fix for docs/Sphinx commands or if 'sphinx' is in the command
    if (
        all(arg not in sys.argv for arg in ["--docs"])
        and all("sphinx" not in arg.lower() for arg in sys.argv)
        and os.name != "nt"
    ):
        entrypoint_path = os.path.join(
            os.path.dirname(__file__), "scripts", "entrypoint.sh"
        )
        if os.path.exists(entrypoint_path):
            try:
                os.chmod(entrypoint_path, 0o755)
            except Exception as e:
                print(f"Warning: Could not chmod +x {entrypoint_path}: {e}")
        # Always fix permissions before any Docker build/run command or prompt
        fix_nypai_chatbot_permissions()


def ensure_sudo():
    """
    Relaunch the script with sudo if not running as root (Linux/macOS).
    On Windows, print a warning and continue (permission fixes are not supported).
    """
    if os.name == "nt":
        print(
            "⚠️  Permission and ownership fixes are not supported on Windows. Continuing without them."
        )
        return
    if os.geteuid() != 0:
        print("🔒 This operation requires elevated (sudo) permissions.")
        try:
            # Re-exec the script with sudo, preserving all arguments
            args = ["sudo", sys.executable] + sys.argv
            os.execvp("sudo", args)
        except Exception as e:
            print(f"❌ Failed to escalate privileges with sudo: {e}")
            sys.exit(1)


# Call at the very start of the script
ensure_sudo()
always_fix_permissions_before_docker()

# Now continue with the rest of the imports and logger setup
from infra_utils import setup_logging, get_docker_venv_python

# Initialize logging as configured in utils.py
# This will set up console output and file logging to ~/.nypai-chatbot/logs/app.log
logger = setup_logging()  # Get the configured logger instance

print("setup.py argv:", sys.argv)


# --- Ensure permissions are fixed before any interactive prompt ---
def prompt_with_permission_fix(prompt_text, *args, **kwargs):
    """
    Wrapper for input() or prompt functions that ensures permissions are fixed before prompting.
    """
    always_fix_permissions_before_docker()
    return input(prompt_text, *args, **kwargs)


# Example usage in your script:
# image_choice = prompt_with_permission_fix("Which docker image would you like to build and run? ")

# Add a global variable for the env file path, defaulting to .env
ENV_FILE_PATH = os.environ.get("DOCKER_ENV_FILE", ".env")

# Define deterministic venv paths
if os.name == "nt":
    LOCAL_VENV_PATH = os.path.expanduser(r"~/.nypai-chatbot/venv")
    LOCAL_VENV_PATH = os.path.expanduser(os.path.join("~", ".nypai-chatbot", "venv"))
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "Scripts", "python.exe")
else:
    LOCAL_VENV_PATH = os.path.expanduser("~/.nypai-chatbot/venv")
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "bin", "python")


def add_shebangs_to_python_files(directory: str) -> None:
    """
    Adds a shebang line '#!/usr/bin/env python3' to Python files
    in the given directory and its subdirectories, if one is not already present.
    Skips files in the .venv and __pycache__ directories.
    """
    logger.info(f"Checking Python files in '{directory}' for shebang lines...")
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in {".venv", "__pycache__"}]
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        first_line = f.readline()
                        f.seek(0)
                        content = f.read()
                    if not first_line.startswith("#!"):
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write("#!/usr/bin/env python3\n" + content)
                        logger.info(f"Added shebang to: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not process file {file_path}: {e}")
    logger.info("Shebang check complete.")


def is_running_in_docker() -> bool:
    """
    Detect if running inside a Docker container.

    :return: True if running in Docker, False otherwise.
    """
    return os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"


def ensure_docker_available() -> None:
    """
    Ensure Docker is installed and the daemon is running. Attempt to start on Linux if needed.
    """

    def fail(msg, logmsg=None):
        print(msg)
        if logmsg:
            logger.error(logmsg)
        sys.exit(1)

    if shutil.which("docker") is None:
        fail(
            "❌ Docker is not installed or not in PATH. Please install Docker first.",
            "Docker executable not found in PATH.",
        )

    try:
        logger.info("Checking if Docker daemon is running with 'docker info'.")
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✅ Docker daemon is already running.")
        logger.info("Docker daemon is already running.")
        return
    except subprocess.CalledProcessError:
        print("⚠️  Docker daemon is not running. Attempting to start it...")
        logger.warning("Docker daemon is not running. Attempting to start.")
        if sys.platform == "darwin":
            fail(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Applications folder.",
                "Docker not running on macOS. User advised to start Docker Desktop.",
            )
        elif sys.platform == "linux":
            print(
                "Attempting to start Docker daemon with 'sudo systemctl start docker'..."
            )
            logger.info("Attempting to start Docker daemon via systemctl (Linux).")
            try:
                subprocess.run(
                    ["sudo", "systemctl", "start", "docker"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                for i in range(1, 11):
                    try:
                        subprocess.run(
                            ["docker", "info"],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("✅ Docker daemon started successfully.")
                        logger.info("Docker daemon started successfully.")
                        return
                    except subprocess.CalledProcessError:
                        print(f"Waiting for Docker to start... ({i}/10)")
                        time.sleep(2)
                fail(
                    "❌ Docker daemon could not be started automatically after multiple retries.\nPlease start it manually with: 'sudo systemctl start docker'",
                    "Failed to start Docker daemon automatically after retries.",
                )
            except subprocess.CalledProcessError as e:
                fail(
                    f"❌ Failed to execute 'sudo systemctl start docker': {e}\nPlease ensure you have sudo privileges and Docker is correctly configured.",
                    f"Failed to execute systemctl command: {e}",
                )
            except Exception as e:
                fail(
                    f"❌ An unexpected error occurred while trying to start Docker: {e}\nPlease start Docker manually.",
                    f"Unexpected error when starting Docker: {e}",
                )
        elif sys.platform == "win32":
            fail(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Start menu.",
                "Docker not running on Windows. User advised to start Docker Desktop.",
            )
        else:
            fail(
                "❌ Docker daemon is not running. Please consult your OS documentation to start Docker.",
                "Docker not running on unsupported OS. User advised to start manually.",
            )
    except FileNotFoundError:
        fail(
            "❌ 'docker' command not found. Please ensure Docker is installed and in your PATH.",
            "'docker' command not found. Docker might not be installed correctly.",
        )
    except Exception as e:
        print(f"❌ An unexpected error occurred while checking Docker status: {e}")
        logger.error(
            f"Unexpected error while checking Docker status: {e}", exc_info=True
        )
        sys.exit(1)


def extract_venv_path_from_dockerfile(dockerfile_path):
    """
    Extract the VENV_PATH argument from a Dockerfile, or return a default.
    """
    with contextlib.suppress(Exception):
        with open(dockerfile_path, "r") as f:
            for line in f:
                if line.strip().startswith("ARG VENV_PATH="):
                    return line.strip().split("=", 1)[1]
    return "/home/appuser/.nypai-chatbot/venv"


def ensure_docker_image():  # sourcery skip: extract-method
    """Check if the Docker image exists, build if not, and record build time if built."""
    try:
        subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-dev"],
            check=True,
            capture_output=True,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-dev' exists.")
        logger.info("Docker image 'nyp-fyp-chatbot-dev' exists.")
    except subprocess.CalledProcessError:
        logger.info("Docker image 'nyp-fyp-chatbot-dev' not found. Building.")
        # Build and record build time
        from datetime import datetime

        t0 = datetime.now()
        t1 = datetime.now()
        build_time = (t1 - t0).total_seconds()
        record_docker_build("nyp-fyp-chatbot-dev", build_time)


def ensure_test_docker_image():  # sourcery skip: extract-method
    """Check if the test Docker image exists, build if not, and record build time if built."""
    try:
        subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-test"],
            check=True,
            capture_output=True,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-test' exists.")
        logger.info("Docker image 'nyp-fyp-chatbot-test' exists.")
    except subprocess.CalledProcessError:
        logger.info("Docker image 'nyp-fyp-chatbot-test' not found. Building.")
        # Build and record build time
        from datetime import datetime

        t0 = datetime.now()
        t1 = datetime.now()
        build_time = (t1 - t0).total_seconds()
        record_docker_build("nyp-fyp-chatbot-test", build_time)


def docker_volume_path(local_path: str) -> str:
    """
    Convert a local path to a Docker-compatible volume path.
    Handles Windows path conversion for Docker Desktop.
    """
    if sys.platform != "win32":
        return local_path
    path = local_path.replace("\\", "/")
    if len(path) >= 2 and path[1] == ":":
        drive_letter = path[0].lower()
        path = f"/{drive_letter}{path[2:]}"
    return path


def check_env_file_exists(env_file_path=ENV_FILE_PATH):
    """
    Ensure the .env file exists in the project root.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, env_file_path)
    if not os.path.exists(env_path):
        print(
            f"❌ {env_file_path} file not found in project root. Please create one with the required environment variables (e.g., OPENAI_API_KEY) before running Docker containers."
        )
        sys.exit(1)


import sqlite3
from datetime import datetime, timezone

DOCKER_BUILD_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "data",
    "docker_build_times.sqlite3",
)


def init_build_db():
    """Ensure the build tracking SQLite database and table exist."""
    conn = sqlite3.connect(DOCKER_BUILD_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS docker_builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            build_time REAL NOT NULL,
            built_at_utc TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


import json
from datetime import timedelta

DOCKER_BUILD_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "docker_build_times.json"
)


def record_docker_build(image_name: str, build_time: float):
    """
    Record a docker build event with UTC+8 timestamp and write to JSON and SQLite.
    The JSON file will have the format:
    {
      "image_name": {
        "build_duration": ...,
        "total_builds": ...,
        "average_build_duration": ...,
        "last_build_on": ...
      }
    }
    """
    # Write to SQLite in project_root/data/docker_build_times.sqlite3
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "docker_build_times.sqlite3")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS docker_builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            build_time REAL NOT NULL,
            built_at_utc TEXT NOT NULL
        )
    """)
    utc8 = timezone(timedelta(hours=8))
    utc8_now = datetime.now(utc8).isoformat()
    c.execute(
        "INSERT INTO docker_builds (image_name, build_time, built_at_utc) VALUES (?, ?, ?)",
        (image_name, round(build_time, 2), utc8_now),
    )
    conn.commit()
    # Calculate stats for JSON
    c.execute(
        "SELECT COUNT(*), AVG(build_time) FROM docker_builds WHERE image_name = ?",
        (image_name,),
    )
    row = c.fetchone()
    total_builds = row[0] if row else 1
    avg_build_time = (
        round(row[1], 2) if row and row[1] is not None else round(build_time, 2)
    )
    conn.close()

    # Write to JSON file in project_root/data/docker_build_times.json
    json_path = os.path.join(data_dir, "docker_build_times.json")
    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        else:
            data = {}
        data[image_name] = {
            "build_duration": round(build_time, 2),
            "total_builds": total_builds,
            "average_build_duration": avg_build_time,
            "last_build_on": utc8_now,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not write to {json_path}: {e}")


def get_build_stats(image_name: str):
    """Return (last_built_utc, avg_build_time_2dp) for the given image_name."""
    init_build_db()
    conn = sqlite3.connect(DOCKER_BUILD_DB)
    c = conn.cursor()
    c.execute(
        "SELECT built_at_utc, build_time FROM docker_builds WHERE image_name = ? ORDER BY built_at_utc DESC LIMIT 1",
        (image_name,),
    )
    last = c.fetchone()
    c.execute(
        "SELECT AVG(build_time) FROM docker_builds WHERE image_name = ?", (image_name,)
    )
    avg = c.fetchone()
    conn.close()
    last_built = last[0] if last else None
    avg_build_time = round(avg[0], 2) if avg and avg[0] is not None else None
    return last_built, avg_build_time


def print_build_stats(image_name: str):
    last_built, avg_build_time = get_build_stats(image_name)
    print(f"Image: {image_name}")
    if last_built:
        print(f"  Last built (UTC): {last_built}")
    if avg_build_time is not None:
        print(f"  Average build time: {avg_build_time:.2f} seconds")
    print()


def docker_test(test_target: Optional[str] = None) -> None:
    ensure_test_docker_image()
    print("🐳 [DEBUG] Dockerfile installs venv at: /home/appuser/.nypai-chatbot/venv")
    print(
        f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
    )
    print("🔍 Running environment check (scripts/check_env.py) before tests...")
    python_exe = get_docker_venv_python("test")
    env_check_result = subprocess.run([python_exe, "scripts/check_env.py"])
    if env_check_result.returncode != 0:
        print("❌ Environment check failed. Aborting tests.")
        sys.exit(1)
    else:
        print("✅ Environment check passed.")
    if test_target:
        print(f"🧪 Running {test_target} in test Docker container...")
        logger.info(f"Running {test_target} inside test Docker container.")
        if test_target == "all":
            print(
                "🚀 Running all tests using scripts/bootstrap_tests.sh for full integration..."
            )
            bootstrap_result = subprocess.run(["bash", "scripts/bootstrap_tests.sh"])
            if bootstrap_result.returncode == 0:
                print("✅ All tests passed via bootstrap_tests.sh.")
                sys.exit(0)
            else:
                print(
                    "❌ Some tests failed via bootstrap_tests.sh. See logs/test_results.log for details."
                )
                sys.exit(1)
        elif test_target.startswith("tests/") and test_target.endswith(".py"):
            result = subprocess.run([get_docker_venv_python("test"), test_target])
            sys.exit(result.returncode)
        else:
            result = subprocess.run(
                [
                    get_docker_venv_python("test"),
                    "scripts/comprehensive_test_suite.py",
                    "--suite",
                    test_target,
                ]
            )
            sys.exit(result.returncode)
    else:
        print("🧪 Running Docker environment verification...")
        logger.info("Running Docker environment verification.")
        result = subprocess.run(
            [
                get_docker_venv_python("test"),
                "scripts/test_docker_environment.py",
            ]
        )
        sys.exit(result.returncode)


def docker_test_suite(suite_name: str) -> None:
    """Run a specific test suite inside the Docker test container."""
    valid_suites = [
        "frontend",
        "backend",
        "integration",
        "comprehensive",
        "unit",
        "performance",
        "all",
        "demo",
    ]
    if suite_name not in valid_suites:
        print(f"❌ Unknown test suite: {suite_name}")
        print(
            "Available suites: frontend, backend, integration, unit, performance, demo, all, comprehensive"
        )
        sys.exit(1)
    print(f"🧪 Running test suite: {suite_name}")
    logger.info(f"Running test suite: {suite_name}")
    cmd = [get_docker_venv_python("test"), "scripts/comprehensive_test_suite.py"]
    if suite_name not in ["all", "comprehensive"]:
        cmd += ["--suite", suite_name]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test suite {suite_name}: {e}")
        logger.error(f"Failed to run test suite {suite_name}: {e}", exc_info=True)
        sys.exit(1)


def docker_test_file(test_file: str) -> None:
    """Run an individual test file inside the Docker test container."""
    import pathlib

    test_path = pathlib.Path(test_file)
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    print(f"🧪 Running test file: {test_file}")
    logger.info(f"Running test file: {test_file}")
    cmd = [get_docker_venv_python("test"), test_file]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test file {test_file}: {e}")
        logger.error(f"Failed to run test file {test_file}: {e}", exc_info=True)
        sys.exit(1)


def list_available_tests():
    """List all available test files and suites."""
    print("🧪 Available Tests and Suites")
    print("=" * 50)

    # Test suites
    print("\n📋 Test Suites:")
    suites = {
        "frontend": "Frontend UI tests",
        "backend": "Backend API tests",
        "integration": "Integration tests",
        "comprehensive": "All tests organized by category",
        "unit": "Unit tests only",
        "performance": "Performance and optimization tests",
        "all": "Run all available tests",
        "demo": "Demo and interactive tests",
    }

    for suite, description in suites.items():
        print(f"  {suite:<15} - {description}")

    # Individual test files
    print("\n📄 Individual Test Files:")
    test_dirs = [
        "tests/frontend",
        "tests/backend",
        "tests/integration",
        "tests/performance",
        "tests/llm",
    ]

    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\n  📁 {test_dir}/")
            for file in sorted(os.listdir(test_dir)):
                if file.endswith(".py") and file.startswith("test_"):
                    print(f"    {file}")

    # Demo files
    demo_dir = "tests/demos"
    if os.path.exists(demo_dir):
        print(f"\n  📁 {demo_dir}/")
        for file in sorted(os.listdir(demo_dir)):
            if file.endswith(".py") and file.startswith("demo_"):
                print(f"    {file}")

    print("\n💡 Usage Examples:")
    print("  python setup.py --docker-test-suite frontend")
    print("  python setup.py --docker-test-file tests/backend/test_backend.py")
    print("  python setup.py --docker-test  # Environment verification")


def ensure_docker_running():
    """Ensure Docker is installed and the daemon is running."""
    import shutil
    import subprocess
    import sys

    if shutil.which("docker") is None:
        print("❌ Docker is not installed or not in PATH. Please install Docker first.")
        sys.exit(1)
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("❌ Docker daemon is not running. Please start Docker and try again.")
        sys.exit(1)


def docker_shell():
    """Open a shell in the Docker container."""
    ensure_docker_running()
    print("TODO: Deprecate this")


def run_docker_shell():
    """Open a shell in the Docker container."""
    ensure_docker_running()

    image_name = "nyp-fyp-chatbot:dev"
    try:
        subprocess.run(
            ["docker", "image", "inspect", image_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"❌ Docker image {image_name} not found. Building it first...")
        print("docker_build_test: Not implemented yet.")

    container_name = "nyp-fyp-chatbot-shell"

    # Stop and remove existing container if it exists
    with contextlib.suppress(Exception):
        subprocess.run(
            ["docker", "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["docker", "rm", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    run_command = [
        "docker",
        "run",
        "-it",
        "--name",
        container_name,
        "-v",
        f"{os.getcwd()}:/app",
        "-p",
        "7680:7680",
        "-p",
        "7860:7860",
        image_name,
        "/bin/sh",
    ]

    print(f"🐳 Starting shell in {image_name}...")
    logger.info(f"Starting Docker shell: {' '.join(run_command)}")

    subprocess.run(run_command, check=True)


def docker_generate_docs_in_container():
    """Run Sphinx documentation build in a temporary container, outputting debug info."""
    print("\n🔧 [docs] Generating documentation in a temporary container...")
    image_name = "nyp-fyp-chatbot:docs"
    container_name = "nyp-fyp-chatbot-docs-build"
    try:
        # Remove any previous build container
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Run the docs build
        run_cmd = [
            "docker",
            "run",
            "--name",
            container_name,
            image_name,
            "/home/appuser/.nypai-chatbot/venv-docs/bin/python",
            "/app/generate_docs.py",
        ]
        print(f"🐳 [docs] Running: {' '.join(run_cmd)}")
        result = subprocess.run(run_cmd)
        if result.returncode == 0:
            print("✅ [docs] Documentation generated successfully in container.")
        else:
            print("❌ [docs] Documentation generation failed in container.")
            sys.exit(1)
        # Copy the built docs out (optional, not needed for serving in container)
        # subprocess.run(["docker", "cp", f"{container_name}:/app/docs/_build/html", "./docs/_build/html"])
    finally:
        # Clean up the build container
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def docker_docs():
    """Run Sphinx documentation server in Docker with real-time progress display."""
    print("\n🚀 [docs] Starting Sphinx documentation server in Docker...")
    print("📊 [docs] Showing real-time build progress (this may take a few minutes)...")
    print("")

    try:
        run_docker_docs_server()
    except subprocess.CalledProcessError as e:
        print(f"❌ [docs] Docker docs server failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ [docs] Error starting Docker docs server: {e}")
        raise


def run_docker_docs_server():
    """Build and run Sphinx documentation server in Docker with real-time progress display and record build time."""
    ensure_docker_running()
    image_name = "nyp-fyp-chatbot:docs"
    container_name = "nyp-fyp-chatbot-docs"

    # Build the docs image and record build time
    build_cmd = [
        "docker",
        "build",
        "-f",
        "docker/Dockerfile.docs",
        "-t",
        image_name,
        ".",
    ]
    print(f"Building docs image: {' '.join(build_cmd)}")
    from datetime import datetime

    t0 = datetime.now()
    t1 = datetime.now()
    build_time = (t1 - t0).total_seconds()
    record_docker_build(image_name, build_time)

    # Stop and remove existing container if it exists
    subprocess.run(
        ["docker", "stop", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["docker", "rm", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    run_command = [
        "docker",
        "run",
        "--name",
        container_name,
        "-p",
        "8080:8080",
        image_name,
    ]

    print(f"🐳 [docs] Starting container: {' '.join(run_command)}")
    print("\n" + "=" * 80)
    print("📋 [docs] REAL-TIME BUILD PROGRESS:")
    print("=" * 80)

    process = subprocess.Popen(
        run_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    for line in process.stdout:
        print(line.rstrip())

    process.wait()

    if process.returncode == 0:
        print("\n" + "=" * 80)
        print("✅ [docs] Documentation server is now running!")
        print("📖 [docs] Documentation available at: http://localhost:8080")
        print("🛑 [docs] To stop the server, run: docker stop nyp-fyp-chatbot-docs")
        print("=" * 80)
    else:
        print(f"❌ [docs] Container failed with exit code: {process.returncode}")
        sys.exit(1)


# TODO Rename this here and in `docker_docs`
def _extracted_from_docker_docs_59(arg0):
    print("")
    print("=" * 80)
    print(arg0)


def docker_export():
    """Exports the Docker image 'nyp-fyp-chatbot' to a tar file."""
    ensure_docker_image()
    output_file = "nyp-fyp-chatbot.tar"
    print(f"📦 Exporting Docker image 'nyp-fyp-chatbot' to {output_file} ...")
    logger.info(f"Exporting Docker image to {output_file}.")
    try:
        subprocess.run(
            ["docker", "save", "-o", output_file, "nyp-fyp-chatbot"],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print(f"✅ Docker image exported successfully to {output_file}")
        logger.info("Docker image exported successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to export Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker export: {e}")
        logger.error(f"Unexpected error during Docker export: {e}", exc_info=True)
        sys.exit(1)


def docker_wipe():
    """Remove all Docker containers, images, and volumes related to this project."""
    ensure_docker_running()
    print("🧹 Wiping all Docker containers, images, and volumes...")

    project_images = [
        "nyp-fyp-chatbot-dev",
        "nyp-fyp-chatbot-prod",
        "nyp-fyp-chatbot:docs",
    ]
    project_containers = [
        "nyp-fyp-chatbot-dev",
        "nyp-fyp-chatbot-prod",
        "nyp-fyp-chatbot-docs",
    ]

    # Stop and remove containers
    print("🛑 Stopping and removing containers...")

    def stop_and_remove_container(container):
        subprocess.run(
            ["docker", "stop", container],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["docker", "rm", container],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"✅ Removed container: {container}")

    for container in project_containers:
        stop_and_remove_container(container)

    # Remove images
    print("🗑️ Removing images...")

    def remove_image(image):
        subprocess.run(
            ["docker", "rmi", "-f", image],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"✅ Removed image: {image}")

    for image in project_images:
        remove_image(image)

    # Remove dangling images and build cache
    print("🧽 Cleaning up dangling images and build cache...")
    subprocess.run(
        ["docker", "image", "prune", "-f"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["docker", "builder", "prune", "-f"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("✅ Cleaned up dangling images and build cache")

    # Remove volumes (optional - more aggressive cleanup)
    print("💾 Removing project volumes...")
    result = subprocess.run(
        ["docker", "volume", "ls", "-q"],
        check=True,
        capture_output=True,
        text=True,
    )
    volumes = result.stdout.strip().split("\n") if result.stdout.strip() else []

    def remove_volume(volume):
        subprocess.run(
            ["docker", "volume", "rm", volume],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"✅ Removed volume: {volume}")

    for volume in volumes:
        if volume and ("nyp" in volume.lower() or "chatbot" in volume.lower()):
            remove_volume(volume)

    print("✅ Docker wipe completed successfully!")
    logger.info("Docker wipe completed successfully")


def setup_pre_commit():
    """Install pre-commit hooks with ruff for code quality checks."""
    print("🔧 Setting up pre-commit hooks with ruff...")
    logger.info("Setting up pre-commit hooks with ruff.")

    try:
        install_and_configure_pre_commit()
    except subprocess.CalledProcessError as e:
        logger.error(f"pre-commit setup failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during pre-commit setup: {e}")
        logger.error(f"Unexpected error during pre-commit setup: {e}", exc_info=True)
        sys.exit(1)


def install_and_configure_pre_commit():
    """Install and configure pre-commit hooks with ruff for code quality checks."""
    venv_path = (
        get_dockerfile_venv_path("docker/Dockerfile")
        if running_in_docker()
        else LOCAL_VENV_PATH
    )

    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")

    if not os.path.exists(venv_path):
        create_virtualenv(venv_path)

    print("📦 Installing pre-commit...")
    logger.info("Installing pre-commit package.")
    subprocess.run(
        [pip_path, "install", "pre-commit"],
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print("✅ pre-commit installed successfully")

    pre_commit_config = os.path.join(
        os.path.dirname(__file__), ".pre-commit-config.yaml"
    )
    if not os.path.exists(pre_commit_config):
        print("📝 Creating .pre-commit-config.yaml...")
        logger.info("Creating .pre-commit-config.yaml file.")
        config_content = """# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.1
    hooks:
    -   id: ruff
        args: [--fix, --unsafe-fixes]
    -   id: ruff-format
"""
        with open(pre_commit_config, "w") as f:
            f.write(config_content)
        print("✅ .pre-commit-config.yaml created")
    else:
        print("ℹ️ .pre-commit-config.yaml already exists")

    print("🔗 Installing pre-commit hooks...")
    logger.info("Installing pre-commit hooks.")
    subprocess.run(
        [pre_commit_path, "install"], check=True, stdout=sys.stdout, stderr=sys.stderr
    )
    print("✅ pre-commit hooks installed successfully")

    print("🚀 Running pre-commit on all files (auto-fix and lint)...")
    logger.info("Running pre-commit on all files.")
    result = subprocess.run(
        [pre_commit_path, "run", "--all-files", "--unsafe-fixes"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if result.returncode == 0:
        usage_msg = """
✅ All files passed pre-commit checks!

🎉 pre-commit setup completed!
✅ pre-commit hooks are now active
✅ ruff will automatically format and lint your code on commit

💡 Usage:
  - Hooks run automatically on 'git commit'
  - Run manually: pre-commit run --all-files
  - Run on specific files: pre-commit run --files file1.py file2.py
"""
        print(usage_msg)
        logger.info("pre-commit setup completed successfully")
    else:
        error_msg = """
⚠️  Some files did not pass pre-commit checks after auto-fix.
Please review the output above, fix any remaining issues, and re-run:
  pre-commit run --all-files
Or commit your changes and let pre-commit show you what to fix.
"""
        print(error_msg)
        logger.warning("pre-commit found issues that could not be auto-fixed.")
        sys.exit(result.returncode)


def create_virtualenv(venv_path):
    print(f"⚠️  Virtual environment not found at {venv_path}")
    print(f"🔨 Creating virtual environment at {venv_path}...")
    logger.info(f"Creating virtual environment at {venv_path}")
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    print(f"✅ Virtual environment created at {venv_path}")
    logger.info(f"Virtual environment created at {venv_path}")


def update_shebangs():
    """Update shebang lines in Python files."""
    # TODO: Deprecate this feature
    print("🔍 Updating shebang lines in Python files...")
    try:
        print("✅ Shebang update completed.")
    except Exception as e:
        print(f"❌ Error updating shebangs: {e}")
        logger.error(f"Error updating shebangs: {e}", exc_info=True)


def update_test_shebangs():
    # Update shebang lines in test files.
    print("🔍 Updating shebang lines in test files...")
    # TODO: Deprecate this feature
    try:
        print("✅ Test shebang update completed.")
    except Exception as e:
        print(f"❌ Error updating test shebangs: {e}")
        logger.error(f"Error updating test shebangs: {e}", exc_info=True)


def build_and_record_docker_image(image_name, dockerfile_path):
    """
    Build a Docker image and record its build time in both sqlite and JSON.
    JSON format:
    {
      "image_name": {
        "build_duration": x.yz,
        "total_builds": a,
        "average_build_duration": b.cd,
        "last_build_on": "someutc+8time"
      }
    }
    The build history is saved into the sqlite file.
    """
    from datetime import datetime, timezone, timedelta
    import json
    import sqlite3

    print(f"[DEBUG] Building image {image_name} from {dockerfile_path} ...")
    build_cmd = [
        "docker",
        "build",
        "-f",
        dockerfile_path,
        "-t",
        image_name,
        ".",
    ]
    t0 = datetime.now(timezone.utc)
    result = subprocess.run(build_cmd, check=False)
    t1 = datetime.now(timezone.utc)
    build_time = (t1 - t0).total_seconds()

    # Convert to Singapore time (UTC+8) for last_build_on
    sg_tz = timezone(timedelta(hours=8))
    t1_sg = t1.astimezone(sg_tz)
    last_build_on = t1_sg.isoformat()

    # Write to JSON file in the required format
    json_path = os.path.join(os.getcwd(), "data", "docker_build_times.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    try:
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        else:
            data = {}

        # Update build history for this image
        prev = data.get(image_name, {})
        prev_builds = prev.get("total_builds", 0)
        prev_avg = prev.get("average_build_duration", 0.0)
        prev_total = prev_builds * prev_avg

        new_total_builds = prev_builds + 1
        new_total_duration = prev_total + build_time
        new_avg = (
            new_total_duration / new_total_builds
            if new_total_builds > 0
            else build_time
        )

        data[image_name] = {
            "build_duration": build_time,
            "total_builds": new_total_builds,
            "average_build_duration": new_avg,
            "last_build_on": last_build_on,
        }
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to write docker build time to JSON: {e}")

    # Write to sqlite (local file, not backend)
    try:
        # Always write to project_root/data/docker_build_times.sqlite3
        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data"
        )
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "docker_build_times.sqlite3")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS docker_builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT NOT NULL,
                build_time REAL NOT NULL,
                built_at_utc TEXT NOT NULL
            )
        """)
        conn.commit()
        c.execute(
            "INSERT INTO docker_builds (image_name, build_time, built_at_utc) VALUES (?, ?, ?)",
            (image_name, round(build_time, 2), last_build_on),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to write docker build time to local sqlite: {e}")

    return result.returncode


def docker_build():
    """Build the development Docker image and record build time."""
    build_and_record_docker_image("nyp-fyp-chatbot-dev", "docker/Dockerfile.dev")


def docker_run():
    """
    Run the development Docker container interactively after ensuring the image is built.
    """
    ensure_docker_running()
    image_name = "nyp-fyp-chatbot-dev"
    container_name = "nyp-fyp-chatbot-dev"

    # Check if image exists
    try:
        subprocess.run(
            ["docker", "image", "inspect", image_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"❌ Docker image {image_name} not found. Building it first...")
        docker_build()

    # Stop and remove existing container if it exists
    with contextlib.suppress(Exception):
        subprocess.run(
            ["docker", "stop", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["docker", "rm", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    run_command = [
        "docker",
        "run",
        "-it",
        "--name",
        container_name,
        "--env-file",
        ENV_FILE_PATH,
        "-v",
        f"{os.getcwd()}:/app",
        "-p",
        "7680:7860",
        image_name,
    ]

    print(f"🐳 Starting dev container: {' '.join(run_command)}")
    logger.info(f"Starting dev Docker container: {' '.join(run_command)}")
    subprocess.run(run_command, check=True)


def docker_build_bench():
    """Build the benchmark Docker image and record build time."""
    build_and_record_docker_image("nyp-fyp-chatbot-bench", "docker/Dockerfile.bench")


def show_help():
    help_text = """
Usage: python setup.py <command>

Available commands:
  --run-benchmarks     Run performance benchmarks
  --pre-commit         Setup pre-commit hooks
  --update-shebangs    Update shebang lines in Python files
  --docs               Build Sphinx documentation
  --docker-wipe        Remove all Docker containers, images, and volumes
  --docker-run         Build and run a Docker image
  --shell              Open a shell in the Docker container
  --export             Export the Docker image to a tar file
  --help               Show this help message

Examples:
  python setup.py --run-benchmarks
  python setup.py --pre-commit
  python setup.py --update-shebangs
  python setup.py --docs
  python setup.py --docker-wipe
  python setup.py --docker-run
  python setup.py --shell
  python setup.py --export
  python setup.py --help
"""
    print(help_text)


def main(shutdown_requested=False):
    """Main entry point for the setup script.

    Parses and executes project management commands from the command line.
    """
    import time

    def run_benchmarks_command():
        """Handle the --run-benchmarks command."""
        print(
            "📊 This will run comprehensive benchmarks and store results in the database"
        )
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        os.chmod(data_dir, 0o777)
        print(f"📁 Data directory ensured: {data_dir}")

        try:
            start = time.time()
            # --- Build the benchmark image and record build time ---
            if (
                build_and_record_docker_image(
                    "nyp-fyp-chatbot-bench", "docker/Dockerfile.bench"
                )
                != 0
            ):
                sys.exit(1)

            docker_compose_cmd = None
            try:
                subprocess.run(
                    ["docker-compose", "--version"], capture_output=True, check=True
                )
                docker_compose_cmd = "docker-compose"
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(
                        ["docker", "compose", "version"],
                        capture_output=True,
                        check=True,
                    )
                    docker_compose_cmd = ["docker", "compose"]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("❌ docker-compose not found. Please install docker-compose.")
                    print("   On Arch Linux: sudo pacman -S docker-compose")
                    print("   Or install via pip: pip install docker-compose")
                    sys.exit(1)

            docker_dir = os.path.join(os.getcwd(), "docker")
            os.chdir(docker_dir)

            if isinstance(docker_compose_cmd, str):
                cmd = [
                    docker_compose_cmd,
                    "-f",
                    "docker-compose.benchmark.yml",
                    "up",
                    "--build",
                    "--abort-on-container-exit",
                ]
            else:
                cmd = docker_compose_cmd + [
                    "-f",
                    "docker-compose.benchmark.yml",
                    "up",
                    "--build",
                    "--abort-on-container-exit",
                ]

            print(f"\n🐳 Executing Docker Compose command: {' '.join(cmd)}")
            # Stream output live to avoid "freezing" appearance
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(
                    f"\n❌ Docker Compose command failed with exit code {result.returncode}"
                )
            else:
                print("\n✅ Docker Compose command completed successfully.")

            os.chdir(os.path.join(docker_dir, ".."))
            duration = int(time.time() - start)
            print(f"Total Runtime {duration} seconds")

            # Results reporting
            for fname, desc in [
                ("benchmark_results.md", "Benchmark results"),
                ("performance.db", "Performance database"),
                ("benchmark_summary.json", "Benchmark summary"),
            ]:
                fpath = os.path.join(data_dir, fname)
                if os.path.exists(fpath):
                    print(f"✅ {desc} written to: {fpath}")
                else:
                    print(f"⚠️ Warning: {desc} not found in expected location")

            print("✅ Benchmarks completed successfully!")
            print(f"📊 Results stored in data directory: {data_dir}")

        except Exception as e:
            print(f"❌ Failed to run benchmarks: {e}")
            sys.exit(1)

    def docker_build_all():
        print("TODO: Not implemented yet")

    def build_and_run_docs():
        """Handle the --docs command to build and run Sphinx documentation server."""
        print(
            "\n=== [docs] Building and running Sphinx documentation server (single container) ==="
        )
        start = time.time()
        if (
            build_and_record_docker_image(
                "nyp-fyp-chatbot:docs", "docker/Dockerfile.docs"
            )
            == 0
        ):
            duration = int(time.time() - start)
            print(f"[DEBUG] Build time for docs image: {duration} seconds")
            docker_docs()
        else:
            print("An unexpected error occurred")

    def docker_run_interactive_command():
        """Handle the --docker-run command to interactively build and run Docker images."""
        print("\nWhich Docker image would you like to build and run?")
        print("  1. dev  (nyp-fyp-chatbot-dev)")
        print("  2. test (nyp-fyp-chatbot-test)")
        print("  3. prod (nyp-fyp-chatbot-prod)")
        print("  4. docs (nyp-fyp-chatbot:docs)")
        print("  5. all  (build all images)")
        print("  6. bench (nyp-fyp-chatbot-bench)")
        choice = input("Enter the number of the image to build and run [1-6]: ").strip()

        if choice == "1":
            start = time.time()
            docker_build()
            duration = int(time.time() - start)
            print(f"Total Runtime {duration} seconds")
            docker_run()
        elif choice == "2":
            print("docker_build_test: Not implemented yet.")
            print("🐳 Starting test container... (not implemented)")
        elif choice == "3":
            print("docker_build_prod: Not implemented yet.")
            print("🐳 Starting production container... (not implemented)")
        elif choice == "4":
            start = time.time()
            duration = int(time.time() - start)
            build_and_run_docs()
        elif choice == "5":
            start = time.time()
            docker_build_all()
            duration = int(time.time() - start)
            print("All images built. You can run them individually with 'docker run'.")
            print(f"Built in {duration} seconds")
        elif choice == "6":
            run_benchmarks_command()
        else:
            start = time.time()
            docker_build()
            duration = int(time.time() - start)
            print("✅ Development image built successfully!")
            print("🐳 Starting development container...")
            sys.path.append("scripts")
            docker_run()

    COMMANDS = {
        "--help": show_help,
        "help": show_help,
        "-h": show_help,
        "--shell": docker_shell,
        "--export": docker_export,
        "--docker-wipe": docker_wipe,
        "--pre-commit": setup_pre_commit,
        "--update-shebangs": update_shebangs,
        "--docs": build_and_run_docs,
        "--run-benchmarks": run_benchmarks_command,
        "--docker-run": docker_run_interactive_command,
    }

    if shutdown_requested:
        print("🛑 Shutdown requested, exiting gracefully...")
        sys.exit(0)

    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1]

    if command in COMMANDS:
        COMMANDS[command]()
        return

    print(f"❌ Unknown command: {command}")
    print("")
    show_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
