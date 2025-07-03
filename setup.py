#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import sys
import subprocess
import shutil
import time
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from fix_permissions import fix_nypai_chatbot_permissions
from main import main

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


def docker_build():
    """
    Build the development Docker image 'nyp-fyp-chatbot-dev' with optimized CPU utilization.
    """
    ensure_docker_running()  # Ensures Docker daemon is running before attempting to build

    # Determine venv_path for debug print based on build type
    venv_path = get_dockerfile_venv_path("Dockerfile")
    if "--docker-build-test" in sys.argv:
        venv_path = get_dockerfile_venv_path("Dockerfile.test")
    elif "--docker-build-dev" in sys.argv:
        venv_path = get_dockerfile_venv_path("Dockerfile.dev")
    elif "--docker-build-all" in sys.argv:
        venv_path = (
            get_dockerfile_venv_path("Dockerfile"),
            get_dockerfile_venv_path("Dockerfile.dev"),
            get_dockerfile_venv_path("Dockerfile.test"),
        )
    print(f"🐳 [DEBUG] Dockerfile will install venv at: {venv_path}")
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )

    # --- REMOVE OLD IMAGE IF EXISTS ---
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-dev' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-dev"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # Ignore errors

    # --- BUILD THE NEW IMAGE WITH OPTIMIZATIONS ---
    print("🔨 Building Docker image 'nyp-fyp-chatbot-dev' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-dev' with optimizations.")

    # Set BuildKit environment variables for parallel builds
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"

    # Get CPU core count for parallelization
    try:
        import multiprocessing

        cpu_cores = multiprocessing.cpu_count()
    except (ImportError, OSError):
        cpu_cores = 4  # Fallback

    print(f"🚀 Using {cpu_cores} CPU cores for parallel build")
    logger.info(f"Using {cpu_cores} CPU cores for parallel build")

    start_time = time.time()

    try:
        # Build command with optimizations
        build_cmd = [
            "docker",
            "build",
            "-f",
            "Dockerfile.dev",
            "-t",
            "nyp-fyp-chatbot-dev",
            "--build-arg",
            f"PARALLEL_JOBS={cpu_cores}",
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            "--progress=plain",
            ".",
        ]

        subprocess.run(
            build_cmd,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env,
        )

        end_time = time.time()
        build_duration = int(end_time - start_time)

        print(
            f"✅ Docker image 'nyp-fyp-chatbot-dev' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-dev' built successfully in {build_duration} seconds."
        )

        # Show build cache statistics
        try:
            print("📊 Build cache statistics:")
            subprocess.run(
                [
                    "docker",
                    "system",
                    "df",
                    "--format",
                    "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}",
                ],
                check=True,
                stdout=sys.stdout,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass  # Ignore cache stats errors

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker build: {e}")
        logger.error(f"Unexpected error during Docker build: {e}", exc_info=True)
        sys.exit(1)


def docker_build_test():
    """
    Build the test Docker image 'nyp-fyp-chatbot-test' with optimized CPU utilization.
    """
    ensure_docker_running()

    print(
        f"🐳 [DEBUG] Dockerfile will install venv at: /home/appuser/.nypai-chatbot/{venv_path}"
    )
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )

    # --- REMOVE OLD IMAGE IF EXISTS ---
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-test' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-test"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # Ignore errors

    print("🔨 Building Docker image 'nyp-fyp-chatbot-test' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-test' with optimizations.")

    # Set BuildKit environment variables for parallel builds
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"

    # Get CPU core count for parallelization
    try:
        import multiprocessing

        cpu_cores = multiprocessing.cpu_count()
    except (ImportError, OSError):
        cpu_cores = 4  # Fallback

    print(f"🚀 Using {cpu_cores} CPU cores for parallel build")
    logger.info(f"Using {cpu_cores} CPU cores for parallel build")

    # Temporarily rename .dockerignore to allow test files
    dockerignore_backup = None
    if os.path.exists(".dockerignore"):
        dockerignore_backup = ".dockerignore.backup"
        os.rename(".dockerignore", dockerignore_backup)

    start_time = time.time()

    try:
        # Build command with optimizations
        build_cmd = [
            "docker",
            "build",
            "-f",
            "Dockerfile.test",
            "-t",
            "nyp-fyp-chatbot-test",
            "--build-arg",
            f"PARALLEL_JOBS={cpu_cores}",
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            "--progress=plain",
            ".",
        ]

        subprocess.run(
            build_cmd,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env,
        )

        end_time = time.time()
        build_duration = int(end_time - start_time)

        print(
            f"✅ Docker image 'nyp-fyp-chatbot-test' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-test' built successfully in {build_duration} seconds."
        )

        # Show build cache statistics
        try:
            print("📊 Build cache statistics:")
            subprocess.run(
                [
                    "docker",
                    "system",
                    "df",
                    "--format",
                    "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}",
                ],
                check=True,
                stdout=sys.stdout,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass  # Ignore cache stats errors

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker build: {e}")
        logger.error(f"Unexpected error during Docker build: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Restore .dockerignore
        if dockerignore_backup and os.path.exists(dockerignore_backup):
            os.rename(dockerignore_backup, ".dockerignore")


def docker_build_prod():
    """
    Build the production Docker image 'nyp-fyp-chatbot-prod' with optimized CPU utilization.
    """
    ensure_docker_running()

    print(
        f"🐳 [DEBUG] Dockerfile will install venv at: /home/appuser/.nypai-chatbot/{venv_path}"
    )
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )

    # --- REMOVE OLD IMAGE IF EXISTS ---
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-prod' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-prod"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # Ignore errors

    print("🔨 Building Docker image 'nyp-fyp-chatbot-prod' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-prod' with optimizations.")

    # Set BuildKit environment variables for parallel builds
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"

    # Get CPU core count for parallelization
    try:
        import multiprocessing

        cpu_cores = multiprocessing.cpu_count()
    except (ImportError, OSError):
        cpu_cores = 4  # Fallback

    print(f"🚀 Using {cpu_cores} CPU cores for parallel build")
    logger.info(f"Using {cpu_cores} CPU cores for parallel build")

    start_time = time.time()

    try:
        # Build command with optimizations
        build_cmd = [
            "docker",
            "build",
            "-f",
            "Dockerfile",
            "-t",
            "nyp-fyp-chatbot-prod",
            "--build-arg",
            f"PARALLEL_JOBS={cpu_cores}",
            "--build-arg",
            "BUILDKIT_INLINE_CACHE=1",
            "--progress=plain",
            ".",
        ]

        subprocess.run(
            build_cmd,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env,
        )

        end_time = time.time()
        build_duration = int(end_time - start_time)

        print(
            f"✅ Docker image 'nyp-fyp-chatbot-prod' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-prod' built successfully in {build_duration} seconds."
        )

        # Show build cache statistics
        try:
            print("📊 Build cache statistics:")
            subprocess.run(
                [
                    "docker",
                    "system",
                    "df",
                    "--format",
                    "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}",
                ],
                check=True,
                stdout=sys.stdout,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass  # Ignore cache stats errors

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker build: {e}")
        logger.error(f"Unexpected error during Docker build: {e}", exc_info=True)
        sys.exit(1)


def docker_build_all():
    """
    Build all Docker images (dev, test, prod) with optimized CPU utilization.
    """
    print("🚀 Building all Docker images with CPU optimizations...")
    logger.info("Building all Docker images with optimizations.")

    start_time = time.time()

    try:
        # Build development image
        print("\n🔨 Building development image...")
        docker_build()

        # Build test image
        print("\n🔨 Building test image...")
        docker_build_test()

        # Build production image
        print("\n🔨 Building production image...")
        docker_build_prod()

        end_time = time.time()
        total_duration = int(end_time - start_time)

        print(f"\n✅ All Docker images built successfully in {total_duration} seconds.")
        logger.info(
            f"All Docker images built successfully in {total_duration} seconds."
        )

        # Show all images
        print("\n📋 Built images:")
        subprocess.run(
            [
                "docker",
                "images",
                "nyp-fyp-chatbot-*",
                "--format",
                "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}",
            ],
            check=True,
            stdout=sys.stdout,
            stderr=subprocess.DEVNULL,
        )

    except Exception as e:
        print(f"❌ Failed to build all Docker images: {e}")
        logger.error(f"Failed to build all Docker images: {e}", exc_info=True)
        sys.exit(1)


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

    Args:
        local_path: Local file system path

    Returns:
        Docker-compatible volume path
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


def docker_run():
    check_env_file(ENV_FILE_PATH)
    ensure_docker_image()
    print("🐳 [DEBUG] Dockerfile installs venv at: /home/appuser/.nypai-chatbot/venv")
    print(
        f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
    )
    print("🐳 Starting development Docker container...")
    logger.info("Starting development Docker container.")
    chatbot_dir = os.path.expanduser("~/.nypai-chatbot")
    docker_volume_path = get_docker_volume_path(chatbot_dir)
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        "-v",
        f"{docker_volume_path}:/home/appuser/.nypai-chatbot",
        "-p",
        "7860:7860",
        "nyp-fyp-chatbot-dev",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Development Docker container exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Development Docker container exited with an error: {e}")
        logger.error(
            f"Development Docker container exited with an error: {e}", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during development Docker run: {e}")
        logger.error(
            f"Unexpected error during development Docker run: {e}", exc_info=True
        )
        sys.exit(1)


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
                    "tests/comprehensive_test_suite.py",
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
                "tests/test_docker_environment.py",
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
    cmd = [get_docker_venv_python("test"), "tests/comprehensive_test_suite.py"]
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
    check_env_file(ENV_FILE_PATH)
    ensure_docker_image()
    print("🐳 Opening a shell in the development Docker container...")
    logger.info("Opening a shell in development Docker container.")
    chatbot_dir = os.path.expanduser("~/.nypai-chatbot")
    docker_volume_path = get_docker_volume_path(chatbot_dir)
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        "-v",
        f"{docker_volume_path}:/home/appuser/.nypai-chatbot",
        "nyp-fyp-chatbot-dev",
        "/bin/bash",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Development Docker shell session exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Development Docker shell session exited with an error: {e}")
        logger.error(
            f"Development Docker shell session exited with an error: {e}", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during development Docker shell: {e}")
        logger.error(
            f"Unexpected error during development Docker shell: {e}", exc_info=True
        )
        sys.exit(1)


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


def setup_pre_commit():
    """Install pre-commit hooks with ruff for code quality checks."""
    print("🔧 Setting up pre-commit hooks with ruff...")
    logger.info("Setting up pre-commit hooks with ruff.")

    try:
        # Determine the virtual environment path
        if running_in_docker():
            venv_path = get_dockerfile_venv_path("Dockerfile")
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


def update_test_shebangs():
    """
    Update all test files to use a dynamic shell shebang that uses VENV_PATH.
    """
    import glob
    import re

    test_files = glob.glob("tests/**/*.py", recursive=True)
    dynamic_shebang = "#!/bin/sh\n'''exec' \"${VENV_PATH:-/home/appuser/.nypai-chatbot/venv-test}/bin/python\" \"$0\" \"$@\"\n' '''\n"
    for file_path in test_files:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Always print the shebang line, even if not a python shebang
        if lines:
            print(f"[setup.py] {file_path} shebang: {lines[0].strip()}")
        # Replace only if the first line is a python shebang
        if lines and re.match(r"^#!.*python", lines[0]):
            if lines[0] != dynamic_shebang:
                print(f"[setup.py] Updating shebang in {file_path}")
                lines[0] = dynamic_shebang
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)


if __name__ == "__main__":
    main()
