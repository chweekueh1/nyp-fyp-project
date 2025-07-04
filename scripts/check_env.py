#!/usr/bin/env python3
import os
import sys

# Add the parent directory to the path to find infra_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- VENV PATH CHECK & DEBUG INFO ---
from infra_utils import get_docker_venv_path

print(f"🐍 Python executable: {sys.executable}")
print(f"🔗 sys.prefix (venv): {sys.prefix}")
if os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1":
    print(f"ℹ️  Dockerfiles install the venv at: {get_docker_venv_path('test')}")
    # In Docker, ensure we are running from the correct venv
    expected_prefix = get_docker_venv_path("test")
    actual_prefix = sys.prefix
    if not actual_prefix.startswith(expected_prefix):
        print(
            f"❌ Not running from the correct venv!\nExpected: {expected_prefix}\nActual:   {actual_prefix}\nPlease ensure you are using the Docker-created venv."
        )
        sys.exit(1)

# Add this block to load .env if not running in Docker
if not (os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"):
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "❌ python-dotenv is required for local environment checks. Please install it with 'pip install python-dotenv'."
        )
        sys.exit(1)
    # Find project root (parent of scripts/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.environ.get("DOCKER_ENV_FILE", ".env")
    env_path = os.path.join(project_root, env_file)
    load_dotenv(env_path)

# Add project root to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import subprocess
from infra_utils import get_chatbot_dir


def check_env():
    # Check OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY is not set!")
        sys.exit(1)
    else:
        print("✅ OPENAI_API_KEY is set.")

    # Determine chatbot base directory using backend logic
    chatbot_dir = get_chatbot_dir()
    print(f"🔍 Using chatbot base directory: {chatbot_dir}")

    # Directories to check under chatbot_dir
    required_dirs = [
        os.path.join(chatbot_dir, "data"),
        os.path.join(chatbot_dir, "data", "vector_store"),
        os.path.join(chatbot_dir, "data", "user_info"),
        os.path.join(chatbot_dir, "data", "chat_sessions"),
    ]
    for d in required_dirs:
        print(f"Checking: {d}")
        if not os.path.exists(d):
            print(f"⚠️  Directory {d} does not exist. Creating...")
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                print(f"❌ Failed to create directory {d}: {e}")
                sys.exit(1)
        if not os.access(d, os.W_OK):
            print(f"❌ Directory {d} is not writable!")
            sys.exit(1)
        else:
            print(f"✅ Directory {d} exists and is writable.")

    # Optionally check /app for legacy/test compatibility
    app_dir = "/app"
    if os.path.exists(app_dir):
        if not os.access(app_dir, os.W_OK):
            print(
                f"⚠️  Directory {app_dir} exists but is not writable. Some tests may fail if they expect to write here."
            )
        else:
            print(f"✅ Directory {app_dir} exists and is writable.")
    else:
        print(
            f"ℹ️  Directory {app_dir} does not exist. This is usually fine unless tests expect it."
        )

    # Check dependencies
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "check"])
        print("✅ All dependencies are installed and compatible.")
    except subprocess.CalledProcessError:
        print(
            "❌ Some dependencies are missing or incompatible. Run 'pip install -r requirements.txt'."
        )
        sys.exit(1)

    print("\n🎉 Environment check passed. Ready to run tests!")
    sys.exit(0)


if __name__ == "__main__":
    check_env()
