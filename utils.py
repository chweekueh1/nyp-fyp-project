import os

def rel2abspath(relative_path: str) -> str:
    return os.path.abspath(relative_path)

def create_folders(path: str):
    """
    Checks if a directory (and all its parent directories) exist.
    If not, it creates them. This function is idempotent, meaning it
    won't raise an error if the directories already exist.

    Args:
        path (str): The full path of the directory to ensure exists.
    """
    try:
        # os.makedirs creates all intermediate directories needed.
        # exist_ok=True prevents an error if the directory already exists.
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        # Catching OSError for file system related errors (e.g., permissions)
        # Re-raise the exception because if the directory can't be created,
        # subsequent operations relying on it will fail.
        raise

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
