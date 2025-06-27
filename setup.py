#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import zipfile
import subprocess
import sys
import shutil
import logging
import tempfile
import atexit # For reliable cleanup of temporary directory
import platform
import argparse
import time

# Assuming utils.py exists and contains rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir, setup_logging
from utils import rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir, setup_logging

# Initialize logging as configured in utils.py
# This will set up console output and file logging to ~/.nypai-chatbot/logs/app.log
logger = setup_logging() # Get the configured logger instance

print('setup.py argv:', sys.argv)

def _add_shebang_to_python_files(directory: str):
    """
    Adds a shebang line '#!/usr/bin/env python3' to Python files
    in the given directory and sits subdirectories, if one is not already present.
    Skips files in the .venv directory.
    """
    logger.info(f"Checking Python files in '{directory}' for shebang lines...")
    for root, dirs, files in os.walk(directory):
        # Exclude .venv directory from traversal
        if '.venv' in dirs:
            dirs.remove('.venv')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        first_line = f.readline()
                        # Reset file pointer to beginning
                        f.seek(0)
                        content = f.read()

                    if not first_line.startswith("#!"):
                        shebang_line = "#!/usr/bin/env python3\n"
                        new_content = shebang_line + content
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        logger.info(f"Added shebang to: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not process file {file_path}: {e}")
    logger.info("Shebang check complete.")


def extract_dependencies():
    """Extracts contents of dependencies.zip to the chatbot's dependencies directory."""
    # Use os.path.join for cross-platform path construction for literals
    zip_path = rel2abspath(os.path.join(".", "dependencies.zip"))
    extract_to_dir = rel2abspath(os.path.join(get_chatbot_dir(), "dependencies"))

    if not os.path.exists(zip_path):
        logger.warning(
            f"Dependency zip file not found at: {zip_path}. Skipping extraction."
        )
        return

    logger.info(f"Attempting to extract dependencies from {zip_path} to {extract_to_dir}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # zipfile.extractall handles path separators correctly internally based on OS
            zip_ref.extractall(extract_to_dir)
        logger.info(f"Dependencies extracted successfully to: {extract_to_dir}")
    except zipfile.BadZipFile:
        logger.error(
            f"Failed to extract '{zip_path}': It is a bad zip file. Please check the zip file integrity.", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during dependency extraction: {e}",
            exc_info=True,
        )
        sys.exit(1)


def running_in_docker():
    """Detect if running inside a Docker container."""
    return os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER') == '1'


def ensure_docker_running():
    # Check if Docker is available
    if shutil.which('docker') is None:
        print("❌ Docker is not installed or not in PATH. Please install Docker first.")
        sys.exit(1)
    # Try 'docker info' to see if daemon is running
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return  # Docker is running
    except subprocess.CalledProcessError:
        pass
    # If not running, try to start it (Linux only)
    if platform.system() == "Linux":
        print("⚠️  Docker daemon is not running. Attempting to start it with 'sudo systemctl start docker'...")
        try:
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
            # Wait a moment for Docker to start
            for _ in range(5):
                try:
                    subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("✅ Docker daemon started successfully.")
                    return
                except subprocess.CalledProcessError:
                    time.sleep(1)
            print("❌ Docker daemon could not be started automatically. Please start it manually with:")
            print("  sudo systemctl start docker")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to start Docker daemon: {e}\nPlease start Docker manually with:\n  sudo systemctl start docker")
            sys.exit(1)
    elif platform.system() == "Darwin":
        print("❌ Docker daemon is not running. Please start Docker Desktop from your Applications folder.")
        sys.exit(1)
    elif platform.system() == "Windows":
        print("❌ Docker daemon is not running. Please start Docker Desktop from your Start menu.")
        sys.exit(1)
    else:
        print("❌ Docker daemon is not running. Please consult your OS documentation to start Docker.")
        sys.exit(1)


def docker_build():
    ensure_docker_running()
    # Remove any existing nyp-fyp-chatbot image before building
    print("🔄 Checking for existing Docker image 'nyp-fyp-chatbot'...")
    try:
        result = subprocess.run(["docker", "images", "-q", "nyp-fyp-chatbot"], capture_output=True, text=True, check=True)
        image_id = result.stdout.strip()
        if image_id:
            print(f"🗑️  Removing existing Docker image 'nyp-fyp-chatbot' (ID: {image_id})...")
            subprocess.run(["docker", "rmi", "-f", "nyp-fyp-chatbot"], check=True)
            print("✅ Removed old Docker image.")
        else:
            print("No existing 'nyp-fyp-chatbot' image found.")
    except Exception as e:
        print(f"⚠️  Could not check or remove existing image: {e}")
    print("🐳 Building Docker image 'nyp-fyp-chatbot' with BuildKit...")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    subprocess.run(["docker", "build", "-t", "nyp-fyp-chatbot", "."], check=True, env=env)

def ensure_docker_image():
    ensure_docker_running()
    # Check if the Docker image exists
    try:
        result = subprocess.run([
            "docker", "images", "-q", "nyp-fyp-chatbot"
        ], capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("⚠️  Docker image 'nyp-fyp-chatbot' not found. Building it now...")
            docker_build()
    except Exception as e:
        print(f"❌ Failed to check Docker images: {e}")
        sys.exit(1)

def docker_run():
    ensure_docker_image()
    print("🐳 Running Docker container for 'nyp-fyp-chatbot'...")
    cmd = [
        "docker", "run", "--env-file", ".env",
        "-v", f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "-p", "7860:7860", "nyp-fyp-chatbot"
    ]
    subprocess.run(cmd, check=True)

def docker_test():
    ensure_docker_image()
    print("🐳 Running tests in Docker container...")
    cmd = [
        "docker", "run", "--env-file", ".env",
        "-v", f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "-it", "nyp-fyp-chatbot", "--run-tests"
    ]
    subprocess.run(cmd, check=True)

def docker_shell():
    ensure_docker_image()
    print("🐳 Opening a shell in the Docker container...")
    cmd = [
        "docker", "run", "--env-file", ".env",
        "-v", f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
        "-it", "nyp-fyp-chatbot", "/bin/bash"
    ]
    subprocess.run(cmd, check=True)

def docker_export():
    ensure_docker_image()
    output_file = "nyp-fyp-chatbot.tar"
    print(f"📦 Exporting Docker image 'nyp-fyp-chatbot' to {output_file} ...")
    try:
        subprocess.run(["docker", "save", "-o", output_file, "nyp-fyp-chatbot"], check=True)
        print(f"✅ Docker image exported successfully to {output_file}")
    except Exception as e:
        print(f"❌ Failed to export Docker image: {e}")
        sys.exit(1)

def main():
    """Main function to set up the environment and install dependencies."""
    if running_in_docker():
        logger.info("Detected Docker environment. Skipping setup.py environment/venv/dependency logic.")
        logger.info("All dependencies should be installed via Dockerfile. No further setup required.")
        return
    logger.info("Starting environment setup script...")

    # Step 0: Ensure the base chatbot directory exists and logging is set up
    ensure_chatbot_dir_exists()
    logger.info("Base chatbot directories ensured in user home.")

    # Step 1: Add shebang to all Python files in the current project directory (and subdirectories)
    _add_shebang_to_python_files(os.getcwd())

    # Step 2: Extract external dependencies
    extract_dependencies()

    # Step 3: Define the path for the main virtual environment
    venv_path = rel2abspath(".venv")

    # Step 4: Remove existing main virtual environment if it exists
    if os.path.exists(venv_path):
        logger.info(f"Removing existing main virtual environment at: {venv_path}")
        try:
            shutil.rmtree(venv_path)
            logger.info("Existing main virtual environment removed successfully.")
        except OSError as e:
            logger.error(
                f"Error removing main virtual environment '{venv_path}': {e}", exc_info=True
            )
            sys.exit(1)

    # Step 5: Create a new main Python virtual environment
    logger.info(f"Creating new main virtual environment at: {venv_path}")
    try:
        # sys.executable ensures the venv is created with the same Python interpreter running this script
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
            stdout=sys.stdout, # Direct output of venv creation to console
            stderr=sys.stderr, # Direct errors of venv creation to console
        )
        logger.info("Main virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create main virtual environment: {e}", exc_info=True)
        sys.exit(1)

    # Step 6: Determine pip executable path within the new main venv
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux, macOS, and other Unix-like systems
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Step 7: Install Python dependencies from requirements.txt into the main venv
    requirements_file = rel2abspath("requirements.txt")
    if os.path.exists(requirements_file):
        logger.info(f"Installing Python dependencies from '{requirements_file}' into main venv...")
        try:
            subprocess.run(
                [pip_path, "install", "-r", requirements_file],
                check=True,
                stdout=sys.stdout, # Direct output of pip install to console
                stderr=sys.stderr, # Direct errors of pip install to console
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
        activate_command = f"call {os.path.join(venv_path, 'Scripts', 'activate')}"
    else:
        activate_command = f"source {os.path.join(venv_path, 'bin', 'activate')}"
    logger.info(f"To activate the main Python virtual environment, run: {activate_command}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup and Docker helper for NYP-FYP Chatbot.")
    parser.add_argument("--docker-build", action="store_true", help="Build the Docker image.")
    parser.add_argument("--docker-run", action="store_true", help="Run the Docker container.")
    parser.add_argument("--docker-test", action="store_true", help="Run the test suite in Docker.")
    parser.add_argument("--docker-shell", action="store_true", help="Open a shell in the Docker container.")
    parser.add_argument("--docker-export", action="store_true", help="Export the Docker image to a tar file.")
    parser.add_argument("--run-tests", action="store_true", help="Run the test suite inside the container.")
    parser.add_argument("--docker-test-file", type=str, help="Run a specific test file in Docker (provide the path to the test file)")
    parser.add_argument("--run-test-file", type=str, help="Run a specific test file inside the container (internal use)")
    args = parser.parse_args()

    # Handle --run-tests and --run-test-file first to avoid interference
    if args.run_tests:
        print("🧪 Running test suite inside the container...")
        venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
        subprocess.run([venv_python, "tests/run_all_tests.py"], check=True)
        sys.exit(0)
    if args.run_test_file:
        print(f"🧪 Running test file {args.run_test_file} inside the container...")
        venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
        subprocess.run([venv_python, args.run_test_file], check=True)
        sys.exit(0)
    if args.docker_build:
        docker_build()
    elif args.docker_run:
        docker_run()
    elif args.docker_test:
        docker_test()
    elif args.docker_shell:
        docker_shell()
    elif args.docker_export:
        docker_export()
    elif args.docker_test_file:
        ensure_docker_image()
        print(f"🐳 Running test file {args.docker_test_file} in Docker container...")
        cmd = [
            "docker", "run", "--env-file", ".env",
            "-v", f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
            "-it", "nyp-fyp-chatbot", "--run-test-file", args.docker_test_file
        ]
        subprocess.run(cmd, check=True)
    elif running_in_docker():
        print("🐳 Detected Docker environment. Activating .venv and launching app.py...")
        venv_python = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
        if not os.path.exists(venv_python):
            print("❌ .venv not found! Please check Docker build.")
            sys.exit(1)
        os.execv(venv_python, [venv_python, 'app.py'])
    else:
        main()

