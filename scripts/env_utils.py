import os
import sys
from infra_utils import setup_logging

logger = setup_logging()

ENV_FILE_PATH = os.environ.get("DOCKER_ENV_FILE", ".env")

if os.name == "nt":
    LOCAL_VENV_PATH = os.path.expanduser(r"~/.nypai-chatbot/venv")
    LOCAL_VENV_PATH = os.path.expanduser(os.path.join("~", ".nypai-chatbot", "venv"))
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "Scripts", "python.exe")
else:
    LOCAL_VENV_PATH = os.path.expanduser("~/.nypai-chatbot/venv")
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "bin", "python")


def running_in_docker() -> bool:
    return os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"


def _add_shebang_to_python_files(directory: str) -> None:
    logger.info(f"Checking Python files in '{directory}' for shebang lines...")
    for root, dirs, files in os.walk(directory):
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


def check_env_file(env_file_path=ENV_FILE_PATH):
    # Always check relative to the project root
    if not os.path.exists(env_file_path):
        print(
            f"❌ Environment file '{env_file_path}' not found. Please create it from .env.dev or .env.example."
        )
        logger.error(f"Environment file '{env_file_path}' not found.")
        sys.exit(1)
    else:
        print(f"✅ Environment file '{env_file_path}' found.")
        logger.info(f"Environment file '{env_file_path}' found.")
