import os
from dotenv import load_dotenv

# Assuming utils.py exists and contains rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir
from utils import rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir
import zipfile
import subprocess
import sys
import shutil
import logging

# Set up logging for this specific module
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO for general messages, use DEBUG for more verbosity
    format="%(asctime)s - %(levelname)s - (setup.py) - %(message)s",
)

# Load environment variables from .env file
load_dotenv()
PATH_TO_ADD = os.getenv("DEPENDENCIES_PATH", "")


def extractDependencies():
    """Extracts contents of dependencies.zip to the chatbot's dependencies directory."""
    zip_path = rel2abspath(".\\dependencies.zip")
    extract_to_dir = rel2abspath(os.path.join(get_chatbot_dir(), "dependencies"))

    if not os.path.exists(zip_path):
        logging.warning(
            f"Dependency zip file not found at: {zip_path}. Skipping extraction."
        )
        return

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to_dir)
        logging.info(f"Dependencies extracted to: {extract_to_dir}")
    except zipfile.BadZipFile:
        logging.error(
            f"Failed to extract '{zip_path}': It is a bad zip file.", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during dependency extraction: {e}",
            exc_info=True,
        )
        sys.exit(1)


def applyPath():
    """Adds specified dependency paths to the system's PATH environment variable."""
    if not PATH_TO_ADD:
        logging.info("DEPENDENCIES_PATH not set in .env. Skipping PATH modification.")
        return

    full_paths_to_add = []
    # Split by semicolon (common for Windows PATH)
    paths = PATH_TO_ADD.split(";")
    for path in paths:
        if path:  # Ensure path is not empty after splitting
            dependency_abs_path = rel2abspath(path.strip())
            full_paths_to_add.append(dependency_abs_path)
            logging.debug(f"Adding to PATH: {dependency_abs_path}")

    # Only modify PATH if there are actual paths to add
    if full_paths_to_add:
        # Use os.pathsep for cross-platform path separator (usually ':' on Unix, ';' on Windows)
        additional_path_str = os.pathsep + os.pathsep.join(full_paths_to_add)
        os.environ["PATH"] += additional_path_str
        logging.info(f"Added custom dependencies to PATH: {additional_path_str}")
    else:
        logging.info("No valid paths found in DEPENDENCIES_PATH to add to system PATH.")


def main():
    """Main function to set up the environment and install dependencies."""
    logging.info("Starting environment setup script...")

    ensure_chatbot_dir_exists()
    logging.info("Chatbot directories ensured.")

    extractDependencies()
    applyPath()

    venv_path = rel2abspath(".venv")
    if os.path.exists(venv_path):
        logging.info(f"Removing existing virtual environment at: {venv_path}")
        try:
            shutil.rmtree(venv_path)
            logging.info("Existing virtual environment removed successfully.")
        except OSError as e:
            logging.error(
                f"Error removing virtual environment '{venv_path}': {e}", exc_info=True
            )
            sys.exit(1)

    logging.info(f"Creating new virtual environment at: {venv_path}")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        logging.info("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create virtual environment: {e}", exc_info=True)
        sys.exit(1)

    # Determine pip executable path within the new venv
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux, macOS
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Install dependencies from requirements.txt
    requirements_file = rel2abspath("requirements.txt")
    if os.path.exists(requirements_file):
        logging.info(f"Installing dependencies from '{requirements_file}'...")
        try:
            subprocess.run(
                [pip_path, "install", "-r", requirements_file],
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            logging.info("Dependencies from requirements.txt installed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Failed to install dependencies from requirements.txt: {e}",
                exc_info=True,
            )
            sys.exit(1)
    else:
        logging.warning(
            f"requirements.txt not found at '{requirements_file}'. Skipping standard dependency installation."
        )

    # Call the integrated PyTorch installation function

    logging.info("Environment setup complete.")
    logging.info(
        f"To activate the environment: {'call ' if sys.platform == 'win32' else 'source '}{venv_path}{os.path.sep}{'Scripts' if sys.platform == 'win32' else 'bin'}{os.path.sep}activate"
    )


if __name__ == "__main__":
    main()
