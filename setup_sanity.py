import os
import subprocess
import sys
import shutil
import venv


def setup_python_venv():
    """
    Sets up a Python virtual environment, installs necessary packages,
    and provides instructions for activation.
    """
    VENV_NAME = ".sanity-venv"

    print("Starting Python virtual environment setup...")

    # 1. Check if the virtual environment already exists and remove it
    if os.path.exists(VENV_NAME):
        print(
            f"Virtual environment '{VENV_NAME}' already exists. Deleting it to create a fresh one."
        )
        try:
            shutil.rmtree(VENV_NAME)
            print(f"Successfully deleted existing '{VENV_NAME}'.")
        except OSError as e:
            print(
                f"Error: Could not remove existing virtual environment '{VENV_NAME}': {e}"
            )
            sys.exit(1)

    # 2. Create the virtual environment
    print(f"Creating virtual environment '{VENV_NAME}'...")
    try:
        venv.create(VENV_NAME, with_pip=True, symlinks=True)
        print("Virtual environment created successfully.")
    except Exception as e:
        print(f"Error: Failed to create virtual environment: {e}")
        print("Please ensure Python 3 is installed and accessible in your PATH.")
        sys.exit(1)

    # 3. Determine the path to the pip executable within the new venv
    pip_executable = os.path.join(VENV_NAME, "bin", "pip")
    if sys.platform == "win32":
        pip_executable = os.path.join(VENV_NAME, "Scripts", "pip.exe")

    # Check if pip executable exists
    if not os.path.exists(pip_executable):
        print(
            f"Error: pip executable not found at {pip_executable}. Virtual environment might be corrupted."
        )
        sys.exit(1)

    # 4. Install required Python packages
    required_packages = ["openai", "python-dotenv"]
    print(f"Installing required packages: {', '.join(required_packages)}...")
    try:
        # Use subprocess.check_call to raise an exception for non-zero exit codes
        subprocess.check_call([pip_executable, "install"] + required_packages)
        print("All packages installed successfully. ✨")
    except subprocess.CalledProcessError as e:
        print(
            f"Error: Failed to install required packages. Command '{' '.join(e.cmd)}' returned non-zero exit status {e.returncode}."
        )
        print("Please check your internet connection and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during package installation: {e}")
        sys.exit(1)

    print("\nSetup complete. To use your virtual environment and run your script:")
    print("1. Activate the environment:")
    if sys.platform == "win32":
        print(f"   .\\{VENV_NAME}\\Scripts\\activate")
    else:
        print(f"   source ./{VENV_NAME}/bin/activate")
    print(
        "2. Then, run your sanity check script (e.g., 'python your_sanity_script_name.py')."
    )
    print("3. When you're done, run 'deactivate' to exit the virtual environment.")


if __name__ == "__main__":
    setup_python_venv()
