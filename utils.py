import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

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

def setup_logging():
    """Set up centralized logging configuration.
    
    This function configures logging to:
    1. Write to app.log in the project root
    2. Rotate logs when they reach 5MB
    3. Keep 3 backup files
    4. Log all levels (DEBUG and above)
    5. Format logs with timestamp, level, module, and message
    """
    # Get the project root directory
    root_dir = Path(__file__).parent
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler
    log_file = root_dir / 'app.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handler to root logger
    logger.addHandler(file_handler)
    
    # Also log to console with INFO level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Clear the log file
    with open(log_file, 'w') as f:
        f.write('')
    
    return logger
