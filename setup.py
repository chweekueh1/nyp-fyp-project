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

# Assuming utils.py exists and contains rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir, setup_logging
from utils import rel2abspath, ensure_chatbot_dir_exists, get_chatbot_dir, setup_logging

# Initialize logging as configured in utils.py
# This will set up console output and file logging to ~/.nypai-chatbot/logs/app.log
logger = setup_logging() # Get the configured logger instance

# Global variable to hold the path to add, populated after temporary venv logic
PATH_TO_ADD = ""

def _get_dependencies_path_from_env():
    """
    Creates a temporary virtual environment, installs python-dotenv,
    loads the .env file within that temporary venv, captures the
    DEPENDENCIES_PATH value, and then cleans up the temporary venv.

    Returns:
        str: The value of DEPENDENCIES_PATH from the .env file, or an empty string.
    """
    temp_venv_dir = None
    try:
        # Create a temporary directory for the venv
        temp_venv_dir = tempfile.mkdtemp(prefix="temp_dotenv_venv_")
        # Ensure cleanup on exit, even if errors occur
        atexit.register(shutil.rmtree, temp_venv_dir, ignore_errors=True)

        logger.info(f"Creating temporary virtual environment at {temp_venv_dir} to load .env variables.")

        # Determine python executable path for the temporary venv
        temp_python_executable = os.path.join(temp_venv_dir, "bin", "python3")
        if sys.platform == "win32":
            temp_python_executable = os.path.join(temp_venv_dir, "Scripts", "python.exe")

        # Create the temporary virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", temp_venv_dir],
            check=True,
            stdout=subprocess.PIPE, # Capture stdout for venv creation
            stderr=subprocess.PIPE, # Capture stderr for venv creation
        )
        logger.debug("Temporary virtual environment created.")

        # Determine pip executable path for the temporary venv
        temp_pip_path = os.path.join(temp_venv_dir, "bin", "pip")
        if sys.platform == "win32":
            temp_pip_path = os.path.join(temp_venv_dir, "Scripts", "pip.exe")

        logger.info("Installing python-dotenv into temporary venv...")
        subprocess.run(
            [temp_pip_path, "install", "python-dotenv"],
            check=True,
            stdout=subprocess.PIPE, # Capture stdout for pip install
            stderr=subprocess.PIPE, # Capture stderr for pip install
        )
        logger.debug("python-dotenv installed in temporary venv.")

        # Script to be run in the temporary venv to load .env and print the variable
        # os.getcwd() is used to ensure .env is found relative to where setup.py is run
        get_env_script = f"""
import os
from dotenv import load_dotenv
import sys

# Load .env relative to the current working directory of the setup script
dotenv_path = os.path.join(os.getcwd(), '.env')
if not os.path.exists(dotenv_path):
    print("", end='') # Print empty string if .env not found
else:
    load_dotenv(dotenv_path=dotenv_path)
    print(os.getenv('DEPENDENCIES_PATH', ''))
"""
        logger.info("Loading DEPENDENCIES_PATH from .env via temporary venv...")
        result = subprocess.run(
            [temp_python_executable, "-c", get_env_script],
            capture_output=True,
            text=True, # Decode stdout/stderr as text
            check=True
        )
        loaded_path = result.stdout.strip()
        logger.info(f"Retrieved DEPENDENCIES_PATH: '{loaded_path}'")
        return loaded_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during temporary venv setup or env loading. Stderr: {e.stderr}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during temporary venv process: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup temporary virtual environment directory if it was created and still exists
        if temp_venv_dir and os.path.exists(temp_venv_dir):
            logger.info(f"Cleaning up temporary virtual environment at {temp_venv_dir}...")
            shutil.rmtree(temp_venv_dir, ignore_errors=True) # Use ignore_errors for atexit safety
            logger.info("Temporary virtual environment cleaned up.")


def _add_shebang_to_python_files(directory: str):
    """
    Adds a shebang line '#!/usr/bin/env python3' to Python files
    in the given directory and its subdirectories, if one is not already present.
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


def apply_path():
    """Adds specified dependency paths to the system's PATH environment variable for the current process."""
    global PATH_TO_ADD # Ensure we are modifying the global variable

    if not PATH_TO_ADD:
        logger.info("DEPENDENCIES_PATH not set in .env. Skipping PATH modification.")
        return

    full_paths_to_add = []
    # Split by semicolon, assuming the .env file uses ';' as a separator for multiple paths
    # This is important if the .env file originated from a Windows environment.
    paths = PATH_TO_ADD.split(";")
    for path_component in paths:
        if path_component:  # Ensure path is not empty after splitting
            # Use rel2abspath to get the absolute path, which also normalizes separators for the current OS
            dependency_abs_path = rel2abspath(path_component.strip())
            full_paths_to_add.append(dependency_abs_path)
            logger.debug(f"Resolved path to add: {dependency_abs_path}")

    # Only modify PATH if there are actual paths to add
    if full_paths_to_add:
        # Use os.pathsep for cross-platform path separator (':' on Unix, ';' on Windows)
        # os.environ.get('PATH', '') handles cases where PATH might not be set
        os.environ["PATH"] = os.environ.get('PATH', '') + os.pathsep + os.pathsep.join(full_paths_to_add)
        logger.info(f"Added custom dependencies to PATH for current process: {os.pathsep.join(full_paths_to_add)}")
    else:
        logger.info("No valid paths found in DEPENDENCIES_PATH to add to system PATH.")


def main():
    """Main function to set up the environment and install dependencies."""
    logger.info("Starting environment setup script...")

    # Step 0: Ensure the base chatbot directory exists and logging is set up
    ensure_chatbot_dir_exists()
    logger.info("Base chatbot directories ensured in user home.")

    # Step 1: Add shebang to all Python files in the current project directory (and subdirectories)
    _add_shebang_to_python_files(os.getcwd())

    # Step 2: Get PATH_TO_ADD using a temporary virtual environment for python-dotenv
    global PATH_TO_ADD # Declare intent to modify the global variable
    PATH_TO_ADD = _get_dependencies_path_from_env()

    # Step 3: Extract external dependencies
    extract_dependencies()

    # Step 4: Apply custom paths to the current process's PATH environment variable
    apply_path()

    # Step 5: Define the path for the main virtual environment
    venv_path = rel2abspath(".venv")

    # Step 6: Remove existing main virtual environment if it exists
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

    # Step 7: Create a new main Python virtual environment
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

    # Step 8: Determine pip executable path within the new main venv
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux, macOS, and other Unix-like systems
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Step 9: Install Python dependencies from requirements.txt into the main venv
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
    main()

