"""
Setup Script for NYP FYP Chatbot

This script manages environment setup, Docker image building, permissions, and test orchestration for the chatbot project.
It is the main entry point for developers and CI to prepare and manage the project environment.
"""
#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import sys
import subprocess
import shutil
import time
import signal
from typing import Optional, Any
from scripts.fix_permissions import fix_nypai_chatbot_permissions
from scripts.docker_utils import (
    docker_build,
    docker_build_test,
    docker_build_prod,
    docker_build_all,
    docker_build_docs,
    # save_build_time,  # Remove this import
)
from scripts.docker_build_tracker import DockerBuildTracker

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

# Only fix permissions on Unix-like systems, and only before logging is initialized
if os.name != "nt":
    # Skip permission fix for docs/Sphinx commands or if 'sphinx' is in the command
    if not any(arg in sys.argv for arg in ["--docs"]) and not any(
        "sphinx" in arg.lower() for arg in sys.argv
    ):
        # Ensure entrypoint.sh is executable before Docker build (use Python if possible)
        entrypoint_path = os.path.join(
            os.path.dirname(__file__), "scripts", "entrypoint.sh"
        )
        if os.path.exists(entrypoint_path):
            try:
                os.chmod(entrypoint_path, 0o755)
            except Exception as e:
                print(f"Warning: Could not chmod +x {entrypoint_path}: {e}")
        fix_nypai_chatbot_permissions()

# Now continue with the rest of the imports and logger setup
from infra_utils import setup_logging, get_docker_venv_python

# Initialize logging as configured in utils.py
# This will set up console output and file logging to ~/.nypai-chatbot/logs/app.log
logger = setup_logging()  # Get the configured logger instance

print("setup.py argv:", sys.argv)

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


def _add_shebang_to_python_files(directory: str) -> None:
    """
    Adds a shebang line '#!/usr/bin/env python3' to Python files
    in the given directory and its subdirectories, if one is not already present.
    Skips files in the .venv directory.

    :param directory: The directory to check for Python files.
    :type directory: str
    :return: None
    :rtype: None
    """
    logger.info(f"Checking Python files in '{directory}' for shebang lines...")
    for root, dirs, files in os.walk(directory):
        # Exclude .venv and __pycache__ directories from traversal
        if ".venv" in dirs:
            dirs.remove(".venv")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        first_line = f.readline()
                        # Reset file pointer to beginning
                        f.seek(0)
                        content = f.read()
                    if not first_line.startswith("#!"):
                        shebang_line = "#!/usr/bin/env python3\n"
                        new_content = shebang_line + content
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        logger.info(f"Added shebang to: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not process file {file_path}: {e}")
    logger.info("Shebang check complete.")


def running_in_docker() -> bool:
    """
    Detect if running inside a Docker container.

    :return: True if running in Docker, False otherwise.
    :rtype: bool
    """
    return os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"


def ensure_docker_running() -> None:
    """
    Check if Docker is installed and its daemon is running. If not running, attempt to start the daemon on Linux. Exit if Docker is not available or cannot be started.
    """
    # 1. Check if Docker is installed (executable in PATH)
    if shutil.which("docker") is None:
        print("❌ Docker is not installed or not in PATH. Please install Docker first.")
        logger.error("Docker executable not found in PATH.")
        sys.exit(1)
    # 2. Check if Docker daemon is running
    try:
        logger.info("Checking if Docker daemon is running with 'docker info'.")
        # Use subprocess.DEVNULL for stdout/stderr to suppress output unless there's an error
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✅ Docker daemon is already running.")
        logger.info("Docker daemon is already running.")
        return  # Docker is already running, so we're good to go
    except subprocess.CalledProcessError:
        # Docker is not running, proceed to attempt to start it
        print("⚠️  Docker daemon is not running. Attempting to start it...")
        logger.warning("Docker daemon is not running. Attempting to start.")
        # 3. Attempt to start Docker (Linux specific)
        if sys.platform == "linux":
            print(
                "Attempting to start Docker daemon with 'sudo systemctl start docker'..."
            )
            logger.info("Attempting to start Docker daemon via systemctl (Linux).")
            try:
                # Use sudo, as starting Docker service typically requires it
                subprocess.run(
                    ["sudo", "systemctl", "start", "docker"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )  # Keep this quiet unless error
                # Wait and check for Docker to start
                for i in range(1, 11):  # Increased retry attempts and wait time
                    try:
                        subprocess.run(
                            ["docker", "info"],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("✅ Docker daemon started successfully.")
                        logger.info("Docker daemon started successfully.")

                        return  # Docker started, return
                    except subprocess.CalledProcessError:
                        print(f"Waiting for Docker to start... ({i}/10)")
                        time.sleep(2)  # Wait 2 seconds between checks
                # If loop finishes, Docker did not start
                print(
                    "❌ Docker daemon could not be started automatically after multiple retries."
                )
                print("Please start it manually with: 'sudo systemctl start docker'")
                logger.error(
                    "Failed to start Docker daemon automatically after retries."
                )
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to execute 'sudo systemctl start docker': {e}")
                print(
                    "Please ensure you have sudo privileges and Docker is correctly configured."
                )
                logger.error(f"Failed to execute systemctl command: {e}", exc_info=True)
                sys.exit(1)
            except Exception as e:
                print(
                    f"❌ An unexpected error occurred while trying to start Docker: {e}"
                )
                print("Please start Docker manually.")
                logger.error(
                    f"Unexpected error when starting Docker: {e}", exc_info=True
                )
                sys.exit(1)
        elif sys.platform == "darwin":
            print(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Applications folder."
            )
            logger.error(
                "Docker not running on macOS. User advised to start Docker Desktop."
            )
            sys.exit(1)
        elif sys.platform == "win32":
            print(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Start menu."
            )
            logger.error(
                "Docker not running on Windows. User advised to start Docker Desktop."
            )
            sys.exit(1)
        else:
            print(
                "❌ Docker daemon is not running. Please consult your OS documentation to start Docker."
            )
            logger.error(
                "Docker not running on unsupported OS. User advised to start manually."
            )
            sys.exit(1)
    except FileNotFoundError:
        # This handles the unlikely case where 'docker' command itself is not found,
        # but shutil.which should have caught it earlier. Still good for robustness.
        print(
            "❌ 'docker' command not found. Please ensure Docker is installed and in your PATH."
        )
        logger.error(
            "'docker' command not found. Docker might not be installed correctly."
        )
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected errors during the initial 'docker info' check
        print(f"❌ An unexpected error occurred while checking Docker status: {e}")
        logger.error(
            f"Unexpected error while checking Docker status: {e}", exc_info=True
        )
        sys.exit(1)


def get_dockerfile_venv_path(dockerfile_path):
    try:
        with open(dockerfile_path, "r") as f:
            for line in f:
                if line.strip().startswith("ARG VENV_PATH="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return "/home/appuser/.nypai-chatbot/venv"  # fallback


def ensure_docker_image():
    """Check if the Docker image exists, build if not."""
    try:
        subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-dev"],
            check=True,
            capture_output=True,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-dev' exists.")
        logger.info("Docker image 'nyp-fyp-chatbot-dev' exists.")
    except subprocess.CalledProcessError:
        print("🔨 Docker image 'nyp-fyp-chatbot-dev' not found. Building...")
        logger.info("Docker image 'nyp-fyp-chatbot-dev' not found. Building.")
        docker_build()


def ensure_test_docker_image():
    """Check if the test Docker image exists, build if not."""
    try:
        subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-test"],
            check=True,
            capture_output=True,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-test' exists.")
        logger.info("Docker image 'nyp-fyp-chatbot-test' exists.")
    except subprocess.CalledProcessError:
        print("🔨 Docker image 'nyp-fyp-chatbot-test' not found. Building...")
        logger.info("Docker image 'nyp-fyp-chatbot-test' not found. Building.")
        docker_build_test()


def get_docker_volume_path(local_path: str) -> str:
    """
    Convert a local path to a Docker-compatible volume path.
    Handles Windows path conversion for Docker Desktop.

    :param local_path: Local file system path
    :type local_path: str
    :return: Docker-compatible volume path
    :rtype: str
    """
    if sys.platform == "win32":
        # Windows: Convert to Docker Desktop format
        # Replace backslashes with forward slashes
        path = local_path.replace("\\", "/")
        # Convert drive letter format (C:/path -> /c/path)
        if len(path) >= 2 and path[1] == ":":
            drive_letter = path[0].lower()
            path = f"/{drive_letter}{path[2:]}"
        return path
    else:
        # Unix-like systems: Use as-is
        return local_path


def check_env_file(env_file_path=ENV_FILE_PATH):
    # Always check relative to the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, env_file_path)
    if not os.path.exists(env_path):
        print(
            f"❌ {env_file_path} file not found in project root. Please create one with the required environment variables (e.g., OPENAI_API_KEY) before running Docker containers."
        )
        sys.exit(1)


# docker_run function moved to scripts/py


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
    if suite_name in ["all", "comprehensive"]:
        pass
    else:
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


def docker_shell():
    """Open a shell in the Docker container."""
    print("🔍 Opening shell in Docker container...")
    try:
        # Check if Docker is running
        ensure_docker_running()

        # Check if the image exists
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
            docker_build_test()

        # Run the container with shell
        container_name = "nyp-fyp-chatbot-shell"

        # Stop and remove existing container if it exists
        try:
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
        except Exception:
            pass

        # Start new container with shell
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

    except subprocess.CalledProcessError as e:
        print(f"❌ Docker shell failed: {e}")
        logger.error(f"Docker shell failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error opening Docker shell: {e}")
        logger.error(f"Error opening Docker shell: {e}", exc_info=True)
        raise


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
        ensure_docker_running()
        image_name = "nyp-fyp-chatbot:docs"
        container_name = "nyp-fyp-chatbot-docs"

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

        # Start new container and show real-time logs
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
        print("")
        print("=" * 80)
        print("📋 [docs] REAL-TIME BUILD PROGRESS:")
        print("=" * 80)

        # Run the container and show logs in real-time
        process = subprocess.Popen(
            run_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Show logs in real-time
        for line in process.stdout:
            print(line.rstrip())

        # Wait for the process to complete
        process.wait()

        if process.returncode == 0:
            print("")
            print("=" * 80)
            print("✅ [docs] Documentation server is now running!")
            print("📖 [docs] Documentation available at: http://localhost:8080")
            print("🛑 [docs] To stop the server, run: docker stop nyp-fyp-chatbot-docs")
            print("=" * 80)
        else:
            print(f"❌ [docs] Container failed with exit code: {process.returncode}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ [docs] Docker docs server failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ [docs] Error starting Docker docs server: {e}")
        raise


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
        print(f"❌ Failed to export Docker image: {e}")
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
    logger.info("Starting Docker wipe operation.")

    # List of project-related images to remove
    project_images = [
        "nyp-fyp-chatbot-dev",
        "nyp-fyp-chatbot-test",
        "nyp-fyp-chatbot-prod",
        "nyp-fyp-chatbot:docs",
    ]

    # List of project-related containers to remove
    project_containers = [
        "nyp-fyp-chatbot-dev",
        "nyp-fyp-chatbot-test",
        "nyp-fyp-chatbot-prod",
        "nyp-fyp-chatbot-docs",
    ]

    try:
        # Stop and remove containers
        print("🛑 Stopping and removing containers...")
        for container in project_containers:
            try:
                # Stop container if running
                subprocess.run(
                    ["docker", "stop", container],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                # Remove container
                subprocess.run(
                    ["docker", "rm", container],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"✅ Removed container: {container}")
            except Exception:
                pass  # Container might not exist

        # Remove images
        print("🗑️ Removing images...")
        for image in project_images:
            try:
                subprocess.run(
                    ["docker", "rmi", "-f", image],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"✅ Removed image: {image}")
            except Exception:
                pass  # Image might not exist

        # Remove dangling images and build cache
        print("🧽 Cleaning up dangling images and build cache...")
        try:
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
        except Exception:
            pass

        # Remove volumes (optional - more aggressive cleanup)
        print("💾 Removing project volumes...")
        try:
            # List and remove volumes that might be related to the project
            result = subprocess.run(
                ["docker", "volume", "ls", "-q"],
                check=True,
                capture_output=True,
                text=True,
            )
            volumes = result.stdout.strip().split("\n") if result.stdout.strip() else []

            for volume in volumes:
                if volume and ("nyp" in volume.lower() or "chatbot" in volume.lower()):
                    try:
                        subprocess.run(
                            ["docker", "volume", "rm", volume],
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print(f"✅ Removed volume: {volume}")
                    except Exception:
                        pass
        except Exception:
            pass

        print("✅ Docker wipe completed successfully!")
        logger.info("Docker wipe completed successfully")

    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker wipe: {e}")
        logger.error(f"Unexpected error during Docker wipe: {e}", exc_info=True)
        sys.exit(1)


def setup_pre_commit():
    """Install pre-commit hooks with ruff for code quality checks."""
    print("🔧 Setting up pre-commit hooks with ruff...")
    logger.info("Setting up pre-commit hooks with ruff.")

    try:
        # Determine the virtual environment path
        if running_in_docker():
            venv_path = get_dockerfile_venv_path("docker/Dockerfile")
        else:
            venv_path = LOCAL_VENV_PATH

        # Determine pip and pre-commit executable paths
        if sys.platform == "win32":
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            pre_commit_path = os.path.join(venv_path, "Scripts", "pre-commit.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            pre_commit_path = os.path.join(venv_path, "bin", "pre-commit")

        # Check if virtual environment exists, create if not
        if not os.path.exists(venv_path):
            print(f"⚠️  Virtual environment not found at {venv_path}")
            print(f"🔨 Creating virtual environment at {venv_path}...")
            logger.info(f"Creating virtual environment at {venv_path}")
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            print(f"✅ Virtual environment created at {venv_path}")
            logger.info(f"Virtual environment created at {venv_path}")

        # Install pre-commit
        print("📦 Installing pre-commit...")
        logger.info("Installing pre-commit package.")
        subprocess.run(
            [
                "pre-commit",
                "install",
                "--hook-type",
                "commit-msg",
                "--hook-type",
                "pre-push",
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        subprocess.run(
            [pip_path, "install", "pre-commit"],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ pre-commit installed successfully")

        # Create .pre-commit-config.yaml if it doesn't exist
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

        # Always (re-)install pre-commit hooks
        print("🔗 Installing pre-commit hooks...")
        logger.info("Installing pre-commit hooks.")
        subprocess.run(
            [pre_commit_path, "install"],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ pre-commit hooks installed successfully")

        # Always run pre-commit on all files to auto-fix and lint
        print("🚀 Running pre-commit on all files (auto-fix and lint)...")
        logger.info("Running pre-commit on all files.")
        result = subprocess.run(
            [pre_commit_path, "run", "--all-files", "--unsafe-fixes"],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if result.returncode == 0:
            print("✅ All files passed pre-commit checks!")
            print("\n🎉 pre-commit setup completed!")
            print("✅ pre-commit hooks are now active")
            print("✅ ruff will automatically format and lint your code on commit")
            print("\n💡 Usage:")
            print("  - Hooks run automatically on 'git commit'")
            print("  - Run manually: pre-commit run --all-files")
            print("  - Run on specific files: pre-commit run --files file1.py file2.py")
            logger.info("pre-commit setup completed successfully")
        else:
            print("⚠️  Some files did not pass pre-commit checks after auto-fix.")
            print(
                "Please review the output above, fix any remaining issues, and re-run:"
            )
            print("  pre-commit run --all-files")
            print("Or commit your changes and let pre-commit show you what to fix.")
            logger.warning("pre-commit found issues that could not be auto-fixed.")
            sys.exit(result.returncode)

    except subprocess.CalledProcessError as e:
        print(f"❌ pre-commit setup failed: {e}")
        logger.error(f"pre-commit setup failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during pre-commit setup: {e}")
        logger.error(f"Unexpected error during pre-commit setup: {e}", exc_info=True)
        sys.exit(1)


def update_shebangs():
    """Update shebang lines in Python files."""
    print("🔍 Updating shebang lines in Python files...")
    try:
        _add_shebang_to_python_files(".")
        print("✅ Shebang update completed.")
    except Exception as e:
        print(f"❌ Error updating shebangs: {e}")
        logger.error(f"Error updating shebangs: {e}", exc_info=True)


def update_test_shebangs():
    # Update shebang lines in test files.
    print("🔍 Updating shebang lines in test files...")
    try:
        _add_shebang_to_python_files("tests")
        print("✅ Test shebang update completed.")
    except Exception as e:
        print(f"❌ Error updating test shebangs: {e}")
        logger.error(f"Error updating test shebangs: {e}", exc_info=True)


def docker_build_bench():
    """Build the benchmark Docker image."""
    import subprocess

    print("[DEBUG] Building benchmark image from docker/Dockerfile.bench...")
    subprocess.run(
        [
            "docker",
            "build",
            "-f",
            "docker/Dockerfile.bench",
            "-t",
            "nyp-fyp-chatbot-bench",
            ".",
        ],
        check=True,
    )
    print("✅ Benchmark image 'nyp-fyp-chatbot-bench' built successfully.")


def show_help():
    # Display help information for setup.py commands.
    print("Usage: python setup.py <command>")
    print("")
    print("Available commands:")
    print("  --build/--docker-build              Build Docker image")
    print("  --build-test/--docker-build-test    Build test Docker image")
    print("  --build-prod/--docker-build-prod    Build production Docker image")
    print("  --build-all/--docker-build-all      Build all Docker images")
    print("  --test               Run tests in Docker")
    print("  --test-suite <suite> Run specific test suite")
    print("  --test-file <file>   Run specific test file")
    print("  --list-tests         List available tests")
    print("  --shell              Open shell in Docker container")
    print("  --export             Export Docker image")
    print("  --run-benchmarks     Run performance benchmarks using docker-compose")
    print("  --docker-wipe        Remove all Docker containers, images, and volumes")
    print("  --pre-commit         Setup pre-commit hooks")
    print("  --update-shebangs    Update shebang lines in Python files")
    print("  --update-test-shebangs Update shebang lines in test files")
    print(
        "  --docs               Build and run Sphinx documentation server (single container)"
    )
    print(
        "  --docker-run         Build and run a Docker image of your choice (interactive)"
    )
    print("  --help               Show this help message")
    print("")
    print("Examples:")
    print("  python setup.py --docker-build")
    print("  python setup.py --docker-run")
    print("  python setup.py --test")
    print(
        "  python setup.py --run-benchmarks  # Uses docker-compose with volume mounting"
    )
    print("  python setup.py --docs")
    print("  python setup.py --help")


def main():
    # Main function to handle command line arguments.
    global shutdown_requested

    # Show help if no arguments provided
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    # Check for shutdown request
    if shutdown_requested:
        print("🛑 Shutdown requested, exiting gracefully...")
        sys.exit(0)

    command = sys.argv[1]

    # Show help for help commands
    if command == "--help" or command == "help" or command == "-h":
        show_help()
        sys.exit(0)
    elif command == "--build" or command == "--docker-build":
        import time

        start = time.time()
        docker_build()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-dev", duration)
        print(
            f"[DEBUG] Build time for dev image: {duration} seconds (recorded in SQLite)"
        )
    elif command == "--build-test" or command == "--docker-build-test":
        import time

        start = time.time()
        docker_build_test()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-test", duration)
        print(
            f"[DEBUG] Build time for test image: {duration} seconds (recorded in SQLite)"
        )
    elif command == "--build-prod" or command == "--docker-build-prod":
        import time

        start = time.time()
        docker_build_prod()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-prod", duration)
        print(
            f"[DEBUG] Build time for prod image: {duration} seconds (recorded in SQLite)"
        )
    elif command == "--build-all" or command == "--docker-build-all":
        import time

        start = time.time()
        docker_build_all()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-all", duration)
        print(
            f"[DEBUG] Build time for all images: {duration} seconds (recorded in SQLite)"
        )
    elif command == "--test":
        test_target = sys.argv[2] if len(sys.argv) > 2 else None
        docker_test(test_target)
    elif command == "--test-suite":
        if len(sys.argv) < 3:
            print("Usage: python setup.py --test-suite <suite_name>")
            sys.exit(1)
        suite_name = sys.argv[2]
        docker_test_suite(suite_name)
    elif command == "--test-file":
        if len(sys.argv) < 3:
            print("Usage: python setup.py --test-file <test_file>")
            sys.exit(1)
        test_file = sys.argv[2]
        docker_test_file(test_file)
    elif command == "--list-tests":
        list_available_tests()
    elif command == "--shell":
        import time

        start = time.time()
        docker_shell()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-shell", duration)
    elif command == "--export":
        import time

        start = time.time()
        docker_export()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-export", duration)
    elif command == "--docker-wipe":
        import time

        start = time.time()
        docker_wipe()
        duration = int(time.time() - start)
        # Do not call save_build_time for wipe
    elif command == "--pre-commit":
        setup_pre_commit()
    elif command == "--update-shebangs":
        update_shebangs()
    elif command == "--update-test-shebangs":
        update_test_shebangs()
    elif command == "--run-benchmarks":
        print("🚀 Running performance benchmarks...")
        print(
            "📊 This will run comprehensive benchmarks and store results in the database"
        )

        # Ensure data directory exists
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        os.chmod(data_dir, 0o777)
        print(f"📁 Data directory ensured: {data_dir}")

        # Run benchmarks using docker-compose
        try:
            import time

            start = time.time()

            # Check if docker-compose is available
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

            # Change to docker directory and run docker-compose
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
            # --- MODIFICATION FOR DEBUGGING: Capture and print output ---
            result = subprocess.run(
                cmd, capture_output=True, text=True
            )  # Capture stdout and stderr

            if result.returncode != 0:
                print(
                    f"\n❌ Docker Compose command failed with exit code {result.returncode}"
                )
                print("\n--- STDOUT from Docker Compose ---")
                print(result.stdout)
                print("\n--- STDERR from Docker Compose ---")
                print(result.stderr)
                raise Exception("Docker Compose failed. See detailed output above.")
            else:
                print("\n✅ Docker Compose command completed successfully.")
                print("\n--- STDOUT from Docker Compose ---")
                print(result.stdout)  # Also print successful output for context
            # --- END MODIFICATION FOR DEBUGGING ---

            # Change back to project root
            os.chdir(os.path.join(docker_dir, ".."))

            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-bench", duration)

            # Check if results were written
            if os.path.exists(os.path.join(data_dir, "benchmark_results.md")):
                print(
                    f"✅ Benchmark results written to: {os.path.join(data_dir, 'benchmark_results.md')}"
                )
            else:
                print("⚠️ Warning: Benchmark results not found in expected location")

            if os.path.exists(os.path.join(data_dir, "performance.db")):
                print(
                    f"✅ Performance database written to: {os.path.join(data_dir, 'performance.db')}"
                )
            else:
                print("⚠️ Warning: Performance database not found in expected location")

            if os.path.exists(os.path.join(data_dir, "benchmark_summary.json")):
                print(
                    f"✅ Benchmark summary written to: {os.path.join(data_dir, 'benchmark_summary.json')}"
                )
            else:
                print("⚠️ Warning: Benchmark summary not found in expected location")

            print("✅ Benchmarks completed successfully!")
            print(f"📊 Results stored in data directory: {data_dir}")

        except Exception as e:
            print(f"❌ Failed to run benchmarks: {e}")
            sys.exit(1)
    elif command == "--docs":
        import time

        print(
            "\n=== [docs] Building and running Sphinx documentation server (single container) ==="
        )
        start = time.time()
        docker_build_docs()
        duration = int(time.time() - start)
        DockerBuildTracker().record_build("nyp-fyp-chatbot-docs", duration)
        print(
            f"[DEBUG] Build time for docs image: {duration} seconds (recorded in SQLite)"
        )
        docker_docs()
    elif command == "--docker-run":
        print("\nWhich Docker image would you like to build and run?")
        print("  1. dev  (nyp-fyp-chatbot-dev)")
        print("  2. test (nyp-fyp-chatbot-test)")
        print("  3. prod (nyp-fyp-chatbot-prod)")
        print("  4. docs (nyp-fyp-chatbot:docs)")
        print("  5. all  (build all images)")
        print("  6. bench (nyp-fyp-chatbot-bench)")
        choice = input("Enter the number of the image to build and run [1-6]: ").strip()
        import time

        if choice == "1":
            start = time.time()
            docker_build()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-dev", duration)
            print("✅ Development image built successfully!")
            print("🐳 Starting development container...")
            sys.path.append("scripts")
            from scripts.docker_utils import docker_run

            docker_run(mode="dev", prompt_for_mode=False)
        elif choice == "2":
            start = time.time()
            docker_build_test()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-test", duration)
            print("✅ Test image built successfully!")
            print("🐳 Starting test container...")
            sys.path.append("scripts")
            from scripts.docker_utils import docker_run

            docker_run(mode="test", prompt_for_mode=False)
        elif choice == "3":
            start = time.time()
            docker_build_prod()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-prod", duration)
            print("✅ Production image built successfully!")
            print("🐳 Starting production container...")
            sys.path.append("scripts")
            from scripts.docker_utils import docker_run

            docker_run(mode="prod", prompt_for_mode=False)
        elif choice == "4":
            start = time.time()
            docker_build_docs()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-docs", duration)
            docker_docs()
        elif choice == "5":
            start = time.time()
            docker_build_all()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-all", duration)
            print("All images built. You can run them individually with 'docker run'.")
        elif choice == "6":
            print("🚀 Running performance benchmarks...")
            print(
                "📊 This will run comprehensive benchmarks and store results in the database"
            )

            # Ensure data directory exists
            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)
            print(f"📁 Data directory ensured: {data_dir}")

            # Run benchmarks using docker-compose
            try:
                start = time.time()

                # Check if docker-compose is available
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
                        print(
                            "❌ docker-compose not found. Please install docker-compose."
                        )
                        print("   On Arch Linux: sudo pacman -S docker-compose")
                        print("   Or install via pip: pip install docker-compose")
                        sys.exit(1)

                # Change to docker directory and run docker-compose
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

                subprocess.run(cmd, check=True)

                # Change back to project root
                os.chdir(os.path.join(docker_dir, ".."))

                duration = int(time.time() - start)
                DockerBuildTracker().record_build("nyp-fyp-chatbot-bench", duration)

                # Check if results were written
                if os.path.exists(os.path.join(data_dir, "benchmark_results.md")):
                    print(
                        f"✅ Benchmark results written to: {os.path.join(data_dir, 'benchmark_results.md')}"
                    )
                else:
                    print("⚠️ Warning: Benchmark results not found in expected location")

                if os.path.exists(os.path.join(data_dir, "performance.db")):
                    print(
                        f"✅ Performance database written to: {os.path.join(data_dir, 'performance.db')}"
                    )
                else:
                    print(
                        "⚠️ Warning: Performance database not found in expected location"
                    )

                if os.path.exists(os.path.join(data_dir, "benchmark_summary.json")):
                    print(
                        f"✅ Benchmark summary written to: {os.path.join(data_dir, 'benchmark_summary.json')}"
                    )
                else:
                    print("⚠️ Warning: Benchmark summary not found in expected location")

                print("✅ Benchmarks completed successfully!")
                print(f"📊 Results stored in data directory: {data_dir}")

            except Exception as e:
                print(f"❌ Failed to run benchmarks: {e}")
                sys.exit(1)
        else:
            start = time.time()
            docker_build()
            duration = int(time.time() - start)
            DockerBuildTracker().record_build("nyp-fyp-chatbot-dev", duration)
            print("✅ Development image built successfully!")
            print("🐳 Starting development container...")
            sys.path.append("scripts")
            from scripts.docker_utils import docker_run

            docker_run(mode="dev", prompt_for_mode=False)
    else:
        print(f"❌ Unknown command: {command}")
        print("")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
