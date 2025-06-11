import os
import sys
import subprocess
from pathlib import Path
from streamlit.web import cli as stcli
import time # For a brief pause before launching Streamlit

# --- Configuration ---
# Determine the project root directory (where this setup.py script resides)
PROJECT_DIR = Path(os.path.dirname(__file__))

# Define the name of your virtual environment directory
# Based on your previous output, it seems to be '.venv_build'
VENV_NAME = ".venv"
VENV_DIR = PROJECT_DIR / VENV_NAME

# Path to your secondary Python application (e.g., a backend service)
# Assuming 'app.py' is in the root of your project
SECONDARY_APP_PATH = PROJECT_DIR / "backend.py"

# Path to your main Streamlit application file
# Assuming 'streamlit_app.py' is in the root of your project
STREAMLIT_APP_PATH = PROJECT_DIR / "streamlit_app.py"

# --- Helper Function ---
def get_venv_python_executable(venv_path: Path) -> Path:
    """
    Determines the path to the Python executable within the specified virtual environment.
    Handles differences between Windows and Unix-like systems.
    """
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

# --- Main Execution Block ---
if __name__ == "__main__":
    # Change the current working directory to the project root.
    # This is crucial so that relative paths (like "app.py" or "streamlit_app.py")
    # are resolved correctly by both subprocesses and Streamlit.
    os.chdir(PROJECT_DIR)
    print(f"Changed current working directory to: {os.getcwd()}")

    # Get the Python executable path from the virtual environment
    venv_python_executable = get_venv_python_executable(VENV_DIR)

    # --- Pre-flight checks ---
    if not venv_python_executable.exists():
        print(f"Error: Python executable not found in virtual environment: {venv_python_executable}")
        print("Please ensure your virtual environment ('{VENV_NAME}') is activated or set up correctly.")
        sys.exit(1)

    if not SECONDARY_APP_PATH.exists():
        print(f"Error: Secondary application script '{SECONDARY_APP_PATH}' not found.")
        sys.exit(1)

    if not STREAMLIT_APP_PATH.exists():
        print(f"Error: Streamlit application script '{STREAMLIT_APP_PATH}' not found.")
        sys.exit(1)

    # --- 1. Launch the secondary 'app.py' subprocess ---
    print(f"\n--- Launching secondary process: {SECONDARY_APP_PATH} ---")
    secondary_process = None # Initialize to None
    try:
        # Use subprocess.Popen to run 'app.py' in the background (non-blocking).
        # We redirect stdout/stderr to subprocess.PIPE to prevent its output from
        # interfering with the main console, but you could also redirect to DEVNULL
        # if you don't care about its output, or to a log file.
        secondary_process = subprocess.Popen(
            [str(venv_python_executable), str(SECONDARY_APP_PATH)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Decode stdout/stderr as text
            bufsize=1 # Line-buffered output
        )
        print(f"Secondary app.py process started with PID: {secondary_process.pid}")
        print("Note: Output from app.py will be buffered internally. Check logs if needed.")
        # Optional: Give secondary process a moment to initialize if it's a backend service
        time.sleep(2)

    except Exception as e:
        print(f"Failed to launch secondary app.py process: {e}")
        # If the secondary process fails to start, it's often critical, so exit.
        sys.exit(1)

    # --- 2. Launch the Streamlit application ---
    print(f"\n--- Launching Streamlit application: {STREAMLIT_APP_PATH} ---")
    try:
        # Streamlit's CLI expects arguments to be set in sys.argv.
        # The first element "streamlit" is a convention for the command itself.
        sys.argv = [
            "streamlit",
            "run",
            str(STREAMLIT_APP_PATH), 
            "--server.port=8501",
            "--global.developmentMode=false"
        ]
        
        # Call Streamlit's main function. This will typically block until Streamlit exits.
        stcli.main()

    except Exception as e:
        print(f"Streamlit application crashed: {e}")
    finally:
        # --- 3. Clean up the secondary subprocess when Streamlit exits ---
        if secondary_process and secondary_process.poll() is None:
            print("\n--- Streamlit app exited. Attempting to terminate secondary app.py process ---")
            try:
                secondary_process.terminate() # Request graceful termination
                secondary_process.wait(timeout=5) # Wait up to 5 seconds for it to exit
                if secondary_process.poll() is None:
                    print("Secondary app.py process did not terminate gracefully. Forcing kill.")
                    secondary_process.kill() # Force kill if still running
                print("Secondary app.py process terminated.")
            except Exception as e:
                print(f"Error terminating secondary app.py process: {e}")
        elif secondary_process:
            print("\nSecondary app.py process was already terminated or finished.")
        else:
            print("\nSecondary app.py process was not launched or process object is null.")

