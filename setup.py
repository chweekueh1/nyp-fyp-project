#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import subprocess
import sys
import shutil
import argparse
import time

# Assuming utils.py exists and contains rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir, setup_logging
from infra_utils import rel2abspath, setup_logging

# Initialize logging as configured in utils.py
# This will set up console output and file logging to ~/.nypai-chatbot/logs/app.log
logger = setup_logging()  # Get the configured logger instance

print("setup.py argv:", sys.argv)


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


def docker_build():
    """
    Build the Docker image 'nyp-fyp-chatbot' with --no-cache, removing any existing one first.
    """
    ensure_docker_running()  # Ensures Docker daemon is running before attempting to build

    # --- THIS PART HANDLES OVERRIDING (REMOVING) THE EXISTING IMAGE ---
    print("🔄 Checking for existing Docker image 'nyp-fyp-chatbot'...")
    logger.info("Checking for existing Docker image 'nyp-fyp-chatbot'.")
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot"],
            capture_output=True,
            text=True,
            check=True,
        )
        image_id = result.stdout.strip()
        if image_id:
            print(
                f"🗑️  Removing existing Docker image 'nyp-fyp-chatbot' (ID: {image_id})..."
            )
            logger.info(f"Removing existing Docker image '{image_id}'.")
            # The '-f' flag forces removal even if container is using it (though --rm on run is better)
            subprocess.run(["docker", "rmi", "-f", "nyp-fyp-chatbot"], check=True)
            print("✅ Removed old Docker image.")
            logger.info("Old Docker image removed successfully.")
        else:
            print("No existing 'nyp-fyp-chatbot' image found.")
            logger.info("No existing 'nyp-fyp-chatbot' image found.")
    except Exception as e:
        print(f"⚠️  Could not check or remove existing image: {e}")
        logger.warning(f"Could not check or remove existing image: {e}")
    # --- END OF IMAGE OVERRIDE LOGIC ---

    print("🐳 Building Docker image 'nyp-fyp-chatbot' with clean build (no cache)...")
    logger.info("Building Docker image 'nyp-fyp-chatbot' with clean build.")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    try:
        # Force clean build with no cache and no layer caching
        subprocess.run(
            [
                "docker",
                "build",
                "--no-cache",  # Don't use any cached layers
                "--pull",  # Always pull latest base image
                "--progress=plain",  # Show detailed build output
                "-t",
                "nyp-fyp-chatbot",
                ".",
            ],
            check=True,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ Docker image built successfully with clean installation.")
        logger.info("Docker image built successfully with clean installation.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker build: {e}")
        logger.error(f"Unexpected error during Docker build: {e}", exc_info=True)
        sys.exit(1)


def docker_build_prod():
    """Builds the Docker image 'nyp-fyp-chatbot' using cache."""
    ensure_docker_running()  # Ensures Docker daemon is running before attempting to build

    # --- THIS PART HANDLES OVERRIDING (REMOVING) THE EXISTING IMAGE ---
    # (Optional: You might choose to skip this for prod builds if you always want to overwrite,
    # or keep it as it doesn't hurt and provides clear feedback)
    print(
        "🔄 Checking for existing Docker image 'nyp-fyp-chatbot' for production build..."
    )
    logger.info(
        "Checking for existing Docker image 'nyp-fyp-chatbot' for production build."
    )
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot"],
            capture_output=True,
            text=True,
            check=True,
        )
        image_id = result.stdout.strip()
        if image_id:
            print(
                f"🗑️  Removing existing Docker image 'nyp-fyp-chatbot' (ID: {image_id})..."
            )
            logger.info(f"Removing existing Docker image '{image_id}'.")
            subprocess.run(["docker", "rmi", "-f", "nyp-fyp-chatbot"], check=True)
            print("✅ Removed old Docker image.")
            logger.info("Old Docker image removed successfully for production build.")
        else:
            print("No existing 'nyp-fyp-chatbot' image found.")
            logger.info(
                "No existing 'nyp-fyp-chatbot' image found for production build."
            )
    except Exception as e:
        print(f"⚠️  Could not check or remove existing image for production build: {e}")
        logger.warning(
            f"Could not check or remove existing image for production build: {e}"
        )
    # --- END OF IMAGE OVERRIDE LOGIC ---

    print("🐳 Building Docker image 'nyp-fyp-chatbot' using cache for production...")
    logger.info("Building Docker image 'nyp-fyp-chatbot' using cache for production.")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    try:
        # Build using cache by default (no --no-cache flag)
        # --pull ensures base images are up-to-date
        subprocess.run(
            [
                "docker",
                "build",
                "--pull",  # Always pull latest base image
                "--progress=plain",  # Show detailed build output
                "-t",
                "nyp-fyp-chatbot",
                ".",
            ],
            check=True,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ Docker image built successfully using cache.")
        logger.info("Docker image built successfully using cache.")
        # --- Docker prune/cleanup ---
        print(
            "🧹 Pruning unused Docker containers, buildx, and volumes (keeping 'nyp-fyp-chatbot' image)..."
        )
        logger.info(
            "Pruning unused Docker containers, buildx, and volumes (keeping 'nyp-fyp-chatbot' image)..."
        )
        try:
            subprocess.run(
                ["docker", "system", "prune", "-af", "--volumes"], check=True
            )
            subprocess.run(["docker", "builder", "prune", "-af"], check=True)
            # Removed explicit Docker image deletion logic as requested
            subprocess.run(["docker", "volume", "prune", "-af"], check=True)
            print("✅ Docker cleanup complete.")
            logger.info("Docker cleanup complete.")
        except Exception as e:
            print(f"⚠️  Docker prune/cleanup failed: {e}")
            logger.warning(f"Docker prune/cleanup failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker image production build failed: {e}")
        logger.error(f"Docker image production build failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker production build: {e}")
        logger.error(
            f"Unexpected error during Docker production build: {e}", exc_info=True
        )
        sys.exit(1)


def ensure_docker_image():
    """Ensures the 'nyp-fyp-chatbot' Docker image exists, building it with --no-cache if necessary."""
    ensure_docker_running()
    # Check if the Docker image exists
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            print(
                "⚠️  Docker image 'nyp-fyp-chatbot' not found. Building it now with --no-cache..."
            )
            logger.info(
                "Docker image 'nyp-fyp-chatbot' not found. Initiating build with --no-cache."
            )
            # This calls docker_build() which includes the --no-cache logic
            docker_build()
        else:
            logger.info("Docker image 'nyp-fyp-chatbot' already exists.")
    except Exception as e:
        print(f"❌ Failed to check Docker images: {e}")
        logger.error(f"Failed to check Docker images: {e}", exc_info=True)
        sys.exit(1)


def docker_run():
    """Runs the Docker container for 'nyp-fyp-chatbot'."""
    ensure_docker_image()  # Ensures the image exists before running
    print("🐳 Running Docker container for 'nyp-fyp-chatbot'...")
    logger.info("Running Docker container for 'nyp-fyp-chatbot'.")
    cmd = [
        "docker",
        "run",
        "--rm",  # Add --rm to automatically remove container on exit
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "-p",
        "7860:7860",
        "nyp-fyp-chatbot",  # Map host port 7860 to container port 7860
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Docker container exited successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker container exited with an error: {e}")
        logger.error(f"Docker container exited with an error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running Docker container: {e}")
        logger.error(
            f"Unexpected error while running Docker container: {e}", exc_info=True
        )
        sys.exit(1)


def docker_test():
    """Runs tests inside the Docker container."""
    ensure_docker_image()
    print("🐳 Running tests in Docker container...")
    logger.info("Running tests inside Docker container.")
    # The --run-tests argument tells the entrypoint/command inside the Dockerfile to execute tests
    cmd = [
        "docker",
        "run",
        "--rm",  # Add --rm for temporary test container
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "-it",
        "nyp-fyp-chatbot",
        "--run-tests",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        print("✅ Docker tests completed successfully.")
        logger.info("Docker tests completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker test run failed: {e}")
        logger.error(f"Docker test run failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker test run: {e}")
        logger.error(f"Unexpected error during Docker test run: {e}", exc_info=True)
        sys.exit(1)


def docker_shell():
    """Opens a shell in the Docker container."""
    ensure_docker_image()
    print("🐳 Opening a shell in the Docker container...")
    logger.info("Opening a shell in Docker container.")
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",  # --rm and -it are good for interactive shells
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "nyp-fyp-chatbot",
        "/bin/bash",  # Explicitly specify bash as command
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Docker shell session exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker shell session exited with an error: {e}")
        logger.error(f"Docker shell session exited with an error: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker shell: {e}")
        logger.error(f"Unexpected error during Docker shell: {e}", exc_info=True)
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
            venv_path = "/opt/venv"
        else:
            venv_path = rel2abspath(".venv")

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
        pre_commit_config = rel2abspath(".pre-commit-config.yaml")
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


def run_test_file(test_file: str) -> None:
    """
    Run an individual test file using the current Python environment.

    :param test_file: Path to the test file to run.
    :type test_file: str
    :return: None
    :rtype: None
    """
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    print(f"🚀 Running test file: {test_file}")
    result = subprocess.run([sys.executable, test_file])
    sys.exit(result.returncode)


def main():
    """Main function to set up the environment and install dependencies."""
    if running_in_docker():
        logger.info(
            "Detected Docker environment. Skipping setup.py environment/venv/dependency logic."
        )
        logger.info(
            "All dependencies should be installed via Dockerfile. No further setup required."
        )

        # In Docker, ensure data directories exist in the mounted volume
        from infra_utils import ensure_chatbot_dir_exists

        ensure_chatbot_dir_exists()
        logger.info("Docker data directories ensured in mounted volume.")
        return

    logger.info("Starting environment setup script...")

    # Step 0: Ensure the base chatbot directory exists and logging is set up
    ensure_chatbot_dir_exists()
    logger.info("Base chatbot directories ensured in user home.")

    # Step 1: Add shebang to all Python files in the current project directory (and subdirectories)
    _add_shebang_to_python_files(os.getcwd())

    # Step 2: Define the path for the main virtual environment
    venv_path = rel2abspath(".venv")

    # Step 3: Remove existing main virtual environment if it exists
    if os.path.exists(venv_path):
        logger.info(f"Removing existing main virtual environment at: {venv_path}")
        try:
            shutil.rmtree(venv_path)
            logger.info("Existing main virtual environment removed successfully.")
        except OSError as e:
            logger.error(
                f"Error removing main virtual environment '{venv_path}': {e}",
                exc_info=True,
            )
            sys.exit(1)

    # Step 4: Create a new main Python virtual environment
    logger.info(f"Creating new main virtual environment at: {venv_path}")
    try:
        # sys.executable ensures the venv is created with the same Python interpreter running this script
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
            stdout=sys.stdout,  # Direct output of venv creation to console
            stderr=sys.stderr,  # Direct errors of venv creation to console
        )
        logger.info("Main virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create main virtual environment: {e}", exc_info=True)
        sys.exit(1)

    # Step 5: Determine pip executable path within the new main venv
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux, macOS, and other Unix-like systems
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Step 6: Install Python dependencies from requirements.txt into the main venv
    requirements_file = rel2abspath("requirements.txt")
    if os.path.exists(requirements_file):
        logger.info(
            f"Installing Python dependencies from '{requirements_file}' into main venv..."
        )
        try:
            subprocess.run(
                [pip_path, "install", "-r", requirements_file],
                check=True,
                stdout=sys.stdout,  # Direct output of pip install to console
                stderr=sys.stderr,  # Direct errors of pip install to console
            )
            logger.info("Dependencies from requirements.txt installed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to install dependencies from requirements.txt: {e}",
                exc_info=True,
            )
            sys.exit(1)
    else:
        logger.warning(
            f"requirements.txt not found at '{requirements_file}'. Skipping standard Python dependency installation."
        )

    # Placeholder for a PyTorch installation function if you add one later
    # call_pytorch_installation_function_here()

    logger.info("Environment setup complete.")
    # Provide activation instructions for the user for the main virtual environment
    if sys.platform == "win32":
        activate_command = f'call "{os.path.join(venv_path, "Scripts", "activate")}"'  # Added quotes for spaces in path
    else:
        activate_command = f'source "{os.path.join(venv_path, "bin", "activate")}"'  # Added quotes for spaces in path
    logger.info(
        f"To activate the main Python virtual environment, run: {activate_command}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Setup and Docker helper for NYP-FYP Chatbot."
    )
    parser.add_argument(
        "--docker-build",
        action="store_true",
        help="Build the Docker image with --no-cache.",
    )
    parser.add_argument(
        "--docker-run", action="store_true", help="Run the Docker container."
    )
    parser.add_argument(
        "--docker-test", action="store_true", help="Run the test suite in Docker."
    )
    parser.add_argument(
        "--docker-shell",
        action="store_true",
        help="Open a shell in the Docker container.",
    )
    parser.add_argument(
        "--docker-export",
        action="store_true",
        help="Export the Docker image to a tar file.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run the test suite inside the container.",
    )
    parser.add_argument(
        "--docker-test-file",
        type=str,
        help="Run a specific test file in Docker (provide the path to the test file)",
    )
    parser.add_argument(
        "--run-test-file",
        type=str,
        help="Run a specific test file inside the container (internal use)",
    )
    parser.add_argument(
        "--docker-prod",
        action="store_true",
        help="Build the Docker image with cache and run the app. Equivalent to --docker-build-prod and --docker-run.",
    )
    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Install pre-commit hooks with ruff for code quality checks.",
    )
    parser.add_argument(
        "--test-file",
        type=str,
        help="Run an individual test file (e.g., tests/frontend/test_login_ui.py)",
    )
    args = parser.parse_args()

    # Handle --run-tests and --run-test-file first to avoid interference
    # These are typically executed *inside* the Docker container or a local venv after setup
    if args.run_tests:
        print("🧪 Running test suite inside the container...")
        logger.info("Running test suite inside the container (internal call).")

        # Use the virtual environment Python for running tests
        # In Docker, the venv is at /opt/venv, locally it's at .venv
        if running_in_docker():
            venv_python_exec = "/opt/venv/bin/python"
        elif sys.platform == "win32":
            venv_python_exec = os.path.join(
                os.getcwd(), ".venv", "Scripts", "python.exe"
            )
        else:
            venv_python_exec = os.path.join(os.getcwd(), ".venv", "bin", "python")

        if os.path.exists(venv_python_exec):
            try:
                subprocess.run(
                    [venv_python_exec, "tests/run_all_tests.py"],
                    check=True,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
                print("✅ Test suite completed successfully.")
                logger.info("Test suite completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Test suite failed: {e}")
                logger.error(f"Test suite failed: {e}", exc_info=True)
                sys.exit(1)
            except Exception as e:
                print(f"❌ An unexpected error occurred during test run: {e}")
                logger.error(f"Unexpected error during test run: {e}", exc_info=True)
                sys.exit(1)
        else:
            print(
                f"❌ Cannot find Python executable at {venv_python_exec} to run tests. Ensure virtual environment is correctly set up."
            )
            logger.error(
                f"Virtual environment Python executable not found at {venv_python_exec} for running tests."
            )
            sys.exit(1)
        sys.exit(0)
    elif args.run_test_file:
        print(f"🧪 Running test file {args.run_test_file} inside the container...")
        logger.info(
            f"Running specific test file {args.run_test_file} inside the container (internal call)."
        )

        # Use the virtual environment Python for running tests
        # In Docker, the venv is at /opt/venv, locally it's at .venv
        if running_in_docker():
            venv_python_exec = "/opt/venv/bin/python"
        elif sys.platform == "win32":
            venv_python_exec = os.path.join(
                os.getcwd(), ".venv", "Scripts", "python.exe"
            )
        else:
            venv_python_exec = os.path.join(os.getcwd(), ".venv", "bin", "python")

        if os.path.exists(venv_python_exec):
            try:
                subprocess.run(
                    [venv_python_exec, args.run_test_file],
                    check=True,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
                print(f"✅ Test file {args.run_test_file} completed successfully.")
                logger.info(f"Test file {args.run_test_file} completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Test file {args.run_test_file} failed: {e}")
                logger.error(
                    f"Test file {args.run_test_file} failed: {e}", exc_info=True
                )
                sys.exit(1)
            except Exception as e:
                print(f"❌ An unexpected error occurred during test file run: {e}")
                logger.error(
                    f"Unexpected error during test file run: {e}", exc_info=True
                )
                sys.exit(1)
        else:
            print(
                f"❌ Cannot find Python executable at {venv_python_exec} to run the test file. Ensure virtual environment is correctly set up."
            )
            logger.error(
                f"Virtual environment Python executable not found at {venv_python_exec} for running specific test file."
            )
            sys.exit(1)
        sys.exit(0)

    # Handle Docker commands (these run the setup script itself with arguments)
    elif args.docker_build:
        docker_build()  # This calls the build with --no-cache
    elif args.docker_run:
        docker_run()
    elif args.docker_test:
        docker_test()
    elif args.docker_shell:
        docker_shell()
    elif args.docker_export:
        docker_export()
    elif args.docker_prod:
        print(
            "🚀 Running production deployment: Building Docker image (with cache) and then running the app..."
        )
        logger.info("Initiating Docker production deployment.")
        docker_build_prod()  # Build with cache
        docker_run()  # Then run the app
        print("✅ Docker production deployment complete.")
        logger.info("Docker production deployment completed.")
    elif args.pre_commit:
        setup_pre_commit()
    elif args.docker_test_file:
        ensure_docker_image()
        print(f"🐳 Running test file {args.docker_test_file} in Docker container...")
        logger.info(
            f"Running specific test file {args.docker_test_file} in Docker container (external call)."
        )
        cmd = [
            "docker",
            "run",
            "--rm",
            "-it",  # --rm for temporary container, -it for interactive if needed by test
            "--env-file",
            ".env",
            "-v",
            f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
            "nyp-fyp-chatbot",
            "--run-test-file",
            args.docker_test_file,  # Pass to the internal script
        ]
        try:
            subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
            print(
                f"✅ Docker test file {args.docker_test_file} completed successfully."
            )
            logger.info(
                f"Docker test file {args.docker_test_file} completed successfully."
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker test file {args.docker_test_file} failed: {e}")
            logger.error(
                f"Docker test file {args.docker_test_file} failed: {e}", exc_info=True
            )
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred during Docker test file run: {e}")
            logger.error(
                f"Unexpected error during Docker test file run: {e}", exc_info=True
            )
            sys.exit(1)
    elif args.test_file:
        run_test_file(args.test_file)
    # This block executes if no specific argparse argument matches
    elif running_in_docker():
        # This part assumes that if running in Docker and no other args, it should launch the app.
        # This implies that `app.py` is the main entrypoint when running the Docker container normally.
        print("🐳 Detected Docker environment. Using /opt/venv and launching app.py...")
        logger.info("Detected Docker environment. Attempting to launch app.py.")

        # In Docker, the virtual environment is at /opt/venv
        venv_python = "/opt/venv/bin/python"

        if not os.path.exists(venv_python):
            print(
                f"❌ Virtual environment Python executable not found at '{venv_python}'! Please check Dockerfile build process."
            )
            logger.error(
                f"Virtual environment Python executable not found at '{venv_python}' inside Docker."
            )
            sys.exit(1)

        # Use os.execv to replace the current process with the app.py process
        # This is more efficient than subprocess.run if this script's only job is to launch the app
        # after initial checks in Docker.
        try:
            logger.info(f"Executing '{venv_python} app.py'.")
            os.execv(venv_python, [venv_python, "app.py"])
        except Exception as e:
            print(f"❌ Failed to execute app.py: {e}")
            logger.error(f"Failed to execute app.py: {e}", exc_info=True)
            sys.exit(1)
    else:
        # If no specific Docker command and not in Docker, show usage and require flags
        print("❌ No command specified. This script requires CLI flags to run.")
        print("\nAvailable commands:")
        print("  --docker-build     Build Docker image with --no-cache")
        print("  --docker-run       Run Docker container")
        print("  --docker-test      Run test suite in Docker")
        print("  --docker-shell     Open shell in Docker container")
        print("  --docker-export    Export Docker image to tar file")
        print("  --docker-prod      Build with cache and run app")
        print("  --docker-test-file <path>  Run specific test file in Docker")
        print("  --pre-commit       Install pre-commit hooks with ruff")
        print("\nFor local development setup, use:")
        print("  python setup.py --help")
        print("\nFor Docker operations, use:")
        print("  python setup.py --docker-build")
        print("  python setup.py --docker-run")
        print("  python setup.py --docker-test")
        print("\nFor code quality setup, use:")
        print("  python setup.py --pre-commit")
        sys.exit(1)
