import subprocess
import sys
import os

def bundle_app():
    # Ensure we're in the correct directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Define the save location
    save_location = os.path.join(app_dir, "dist", "chatbot.exe")

    # Create the directory if it does not exist
    save_dir = os.path.dirname(save_location)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Define the PyInstaller command
    command = f"""
    pyinstaller --onefile --windowed --clean \\
        --hidden-import=streamlit \\
        --hidden-import=streamlit.cli \\
        --hidden-import=streamlit.delta_generator \\
        --hidden-import=streamlit.elements \\
        --hidden-import=streamlit.proto \\
        --hidden-import=streamlit.runtime \\
        --hidden-import=streamlit.runtime.scriptrunner \\
        --hidden-import=streamlit.runtime.scriptrunner.script_runner \\
        --hidden-import=streamlit.web \\
        --hidden-import=streamlit.web.bootstrap \\
        --hidden-import=streamlit.web.server \\
        --add-data "streamlit_app.py;." \\
        --add-data "backend.py;." \\
        --distpath "{save_dir}" \\
        --name "chatbot" \\
        streamlit_app.py
    """

    # Execute the command
    try:
        print(command)
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to bundle the app: {e}")
        sys.exit(1)

    print(f"App bundled successfully and saved to {save_location}")

if __name__ == "__main__":
    bundle_app()