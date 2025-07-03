#!/usr/bin/env python3
# This shebang line ensures the script is executable directly on Linux systems.

import os
import subprocess
import sys
import shutil
import argparse
import time
from typing import Optional

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
    Build the development Docker image 'nyp-fyp-chatbot-dev'.
    """
    ensure_docker_running()  # Ensures Docker daemon is running before attempting to build

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

    # --- BUILD THE NEW IMAGE ---
    print("🔨 Building Docker image 'nyp-fyp-chatbot-dev'...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-dev'.")

    try:
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile.dev",
                "-t",
                "nyp-fyp-chatbot-dev",
                ".",
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-dev' built successfully.")
        logger.info("Docker image 'nyp-fyp-chatbot-dev' built successfully.")
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
    Build the test Docker image 'nyp-fyp-chatbot-test'.
    """
    ensure_docker_running()

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

    print("🔨 Building Docker image 'nyp-fyp-chatbot-test'...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-test'.")

    # Temporarily rename .dockerignore to allow test files
    dockerignore_backup = None
    if os.path.exists(".dockerignore"):
        dockerignore_backup = ".dockerignore.backup"
        os.rename(".dockerignore", dockerignore_backup)

    try:
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile.test",
                "-t",
                "nyp-fyp-chatbot-test",
                ".",
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-test' built successfully.")
        logger.info("Docker image 'nyp-fyp-chatbot-test' built successfully.")
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
    Build the production Docker image 'nyp-fyp-chatbot-prod'.
    """
    ensure_docker_running()

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

    print("🔨 Building Docker image 'nyp-fyp-chatbot-prod'...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-prod'.")

    try:
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "Dockerfile",
                "-t",
                "nyp-fyp-chatbot-prod",
                ".",
            ],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("✅ Docker image 'nyp-fyp-chatbot-prod' built successfully.")
        logger.info("Docker image 'nyp-fyp-chatbot-prod' built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker build: {e}")
        logger.error(f"Unexpected error during Docker build: {e}", exc_info=True)
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


def docker_run():
    """Run the development Docker container."""
    ensure_docker_image()
    print("🚀 Running development Docker container...")
    logger.info("Running development Docker container.")
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
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
    """
    Runs tests inside the test Docker container.

    Args:
        test_target: Optional specific test suite or file to run. If None, runs environment verification.
    """
    ensure_test_docker_image()

    if test_target:
        print(f"🧪 Running {test_target} in test Docker container...")
        logger.info(f"Running {test_target} inside test Docker container.")
    else:
        print("🧪 Running Docker environment verification...")
        logger.info("Running Docker environment verification.")

    # Build the Docker command
    cmd = [
        "docker",
        "run",
        "--rm",
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
    ]

    # Add test target as environment variable if specified
    if test_target:
        cmd.extend(["-e", f"TEST_TARGET={test_target}"])

    # Add the container name
    cmd.extend(["nyp-fyp-chatbot-test"])

    # If a specific test target is provided, override the default command
    if test_target:
        # Check if it's an individual test file (starts with "tests/" and ends with ".py")
        if test_target.startswith("tests/") and test_target.endswith(".py"):
            # Individual test file
            cmd.extend(["/opt/venv/bin/python", test_target])
        else:
            # Any suite name: run comprehensive test suite with --suite argument
            cmd.extend(
                [
                    "/opt/venv/bin/python",
                    "tests/comprehensive_test_suite.py",
                    "--suite",
                    test_target,
                ]
            )
    else:
        # Default: run environment verification
        cmd.extend(["/opt/venv/bin/python", "tests/test_docker_environment.py"])

    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        if test_target:
            print(f"✅ {test_target} completed successfully.")
            logger.info(f"{test_target} completed successfully.")
        else:
            print("✅ Docker environment verification completed successfully.")
            logger.info("Docker environment verification completed successfully.")
    except subprocess.CalledProcessError as e:
        if test_target:
            print(f"❌ {test_target} failed: {e}")
            logger.error(f"{test_target} failed: {e}", exc_info=True)
        else:
            print(f"❌ Docker environment verification failed: {e}")
            logger.error("Docker environment verification failed: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        if test_target:
            print(f"❌ An unexpected error occurred during {test_target}: {e}")
            logger.error(f"Unexpected error during {test_target}: {e}", exc_info=True)
        else:
            print(
                f"❌ An unexpected error occurred during Docker environment verification: {e}"
            )
            logger.error(
                f"Unexpected error during Docker environment verification: {e}",
                exc_info=True,
            )
        sys.exit(1)


def docker_shell():
    """Opens a shell in the development Docker container."""
    ensure_docker_image()
    print("🐳 Opening a shell in the development Docker container...")
    logger.info("Opening a shell in development Docker container.")
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ".env",
        "-v",
        f"{os.path.expanduser('~')}/.nypai-chatbot:/root/.nypai-chatbot",
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


def docker_test_suite(suite_name: str) -> None:
    """
    Run a specific test suite inside the Docker container.

    :param suite_name: Name of the test suite to run (e.g., frontend, backend, integration, comprehensive, unit, performance).
    :type suite_name: str
    :return: None
    :rtype: None
    """
    # Map suite names to test suite identifiers
    suite_mapping = {
        "frontend": "frontend",
        "backend": "backend",
        "integration": "integration",
        "comprehensive": "comprehensive",
        "unit": "unit",
        "performance": "performance",
        "all": "all",
        "demo": "demo",
    }

    if suite_name not in suite_mapping:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_mapping.keys())}")
        print("\nSuite descriptions:")
        print("  frontend      - Frontend UI tests")
        print("  backend       - Backend API tests")
        print("  integration   - Integration tests")
        print("  comprehensive - All tests organized by category")
        print("  unit          - Unit tests only")
        print("  performance   - Performance and optimization tests")
        print("  all           - Run all available tests")
        print("  demo          - Demo and interactive tests")
        sys.exit(1)

    # Use the docker_test abstraction with the specific test suite
    docker_test(suite_mapping[suite_name])


def docker_test_file(test_file: str) -> None:
    """
    Run an individual test file inside the Docker container.

    :param test_file: Path to the test file to run.
    :type test_file: str
    :return: None
    :rtype: None
    """
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)

    # Use the docker_test abstraction with the specific test file
    docker_test(test_file)


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


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="NYP FYP Chatbot Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build different Docker containers (Python 3.12 Alpine)
  python setup.py --docker-build          # Build development container
  python setup.py --docker-build-test     # Build test container
  python setup.py --docker-build-prod     # Build production container

  # Run development container
  python setup.py --docker-run

  # Run tests in test container
  python setup.py --docker-test                                    # Run environment verification
  python setup.py --docker-test-suite frontend                     # Run frontend test suite
  python setup.py --docker-test-suite backend                      # Run backend test suite
  python setup.py --docker-test-suite integration                  # Run integration test suite
  python setup.py --docker-test-suite performance                  # Run performance test suite
  python setup.py --docker-test-suite comprehensive                # Run comprehensive test suite
  python setup.py --docker-test-suite all                          # Run all test suites
  python setup.py --docker-test-file tests/backend/test_backend_fixes_and_rename.py
  python setup.py --list-tests                                    # List all available tests

  # Development tools
  python setup.py --docker-shell
  python setup.py --setup-pre-commit
        """,
    )

    # Docker commands
    parser.add_argument(
        "--docker-build",
        action="store_true",
        help="Build the development Docker image 'nyp-fyp-chatbot-dev'",
    )
    parser.add_argument(
        "--docker-build-test",
        action="store_true",
        help="Build the test Docker image 'nyp-fyp-chatbot-test'",
    )
    parser.add_argument(
        "--docker-build-prod",
        action="store_true",
        help="Build the production Docker image 'nyp-fyp-chatbot-prod'",
    )
    parser.add_argument(
        "--docker-run",
        action="store_true",
        help="Run the development Docker container 'nyp-fyp-chatbot-dev'",
    )
    parser.add_argument(
        "--docker-test",
        action="store_true",
        help="Run all tests in test Docker container",
    )
    parser.add_argument(
        "--docker-test-suite",
        type=str,
        choices=[
            "frontend",
            "backend",
            "integration",
            "comprehensive",
            "unit",
            "performance",
            "all",
            "demo",
        ],
        help="Run a specific test suite in test Docker container",
    )
    parser.add_argument(
        "--docker-test-file",
        type=str,
        help="Run an individual test file in test Docker container",
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all available test files and suites",
    )
    parser.add_argument(
        "--docker-shell",
        action="store_true",
        help="Open a shell in the development Docker container",
    )
    parser.add_argument(
        "--docker-export",
        action="store_true",
        help="Export the Docker image to a tar file",
    )

    # Development tools
    parser.add_argument(
        "--setup-pre-commit",
        action="store_true",
        help="Install pre-commit hooks with ruff for code quality checks.",
    )

    # Internal Docker container arguments
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests inside Docker container (internal use)",
    )

    args = parser.parse_args()

    # Handle Docker commands
    if args.docker_build:
        docker_build()
        return
    elif args.docker_build_test:
        docker_build_test()
        return
    elif args.docker_build_prod:
        docker_build_prod()
        return
    elif args.docker_run:
        docker_run()
        return
    elif args.docker_test:
        docker_test()
        return
    elif args.docker_test_suite:
        docker_test_suite(args.docker_test_suite)
        return
    elif args.docker_test_file:
        docker_test_file(args.docker_test_file)
        return
    elif args.list_tests:
        list_available_tests()
        return
    elif args.docker_shell:
        docker_shell()
        return
    elif args.docker_export:
        docker_export()
        return

    # Handle development tools
    elif args.setup_pre_commit:
        setup_pre_commit()
        return

    # Handle internal Docker container arguments
    elif args.run_tests:
        print("🧪 Running test suite inside the container...")
        logger.info("Running test suite inside the container (internal call).")

        # Always run the comprehensive test suite, which will handle TEST_TARGET environment variable
        try:
            subprocess.run(
                [sys.executable, "tests/comprehensive_test_suite.py"],
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            print("✅ Tests completed successfully.")
            logger.info("Tests completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")
            logger.error(f"Tests failed: {e}", exc_info=True)
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred during tests: {e}")
            logger.error(f"Unexpected error during tests: {e}", exc_info=True)
            sys.exit(1)
        return

    # This block executes if no specific argparse argument matches
    elif running_in_docker():
        print("🐳 Running inside Docker container...")
        logger.info("Running inside Docker container.")
        # Default behavior: run the main application
        print("🚀 Starting main application...")
        logger.info("Starting main application.")
        try:
            subprocess.run(
                [sys.executable, "app.py"],
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Application failed to start: {e}")
            logger.error(f"Application failed to start: {e}", exc_info=True)
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            sys.exit(1)
    else:
        # When no arguments are provided, show help instead of starting the app
        parser.print_help()
        print(
            "\n❌ No command specified. Please use one of the available options above."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
