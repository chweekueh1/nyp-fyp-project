import os

def rel2abspath(relative_path: str) -> str:
    return os.path.abspath(relative_path)

def create_folders(path: str):
    if not path.endswith('\\'):
        folder_path = os.path.dirname(path)
    else:
        folder_path = path
    os.makedirs(folder_path, exist_ok=True)

def ensure_chatbot_dir_exists():
    # Creates a `.nypai-chatbot` folder for the user if it doesn't exist.
    user_folder = get_chatbot_dir()
    os.makedirs(user_folder, exist_ok=True)

def get_chatbot_dir():
    """
    Returns the absolute path to the current user's home directory.
    This method is robust and works across Windows, Linux, and macOS.
    """
    user_folder = f"{os.environ.get('USERPROFILE')}\\.nypai-chatbot\\"
    return user_folder
