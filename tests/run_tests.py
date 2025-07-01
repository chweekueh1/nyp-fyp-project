#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
import unittest
import importlib.util
import asyncio

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Initialize backend ONCE for all tests
from backend import init_backend


def setUpModule():
    print("Initializing backend for all tests...")
    asyncio.run(init_backend())
    print("Backend initialization complete.")


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - (%(filename)s) - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_module(module_path: str):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location("module", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestEnvironment(unittest.TestCase):
    """Test environment setup and configuration."""

    def test_environment_variables(self):
        """Test that required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "CHAT_DATA_PATH",
            "CLASSIFICATION_DATA_PATH",
            "KEYWORDS_DATABANK_PATH",
            "DATABASE_PATH",
            "EMBEDDING_MODEL",
        ]

        for var in required_vars:
            self.assertIsNotNone(
                os.getenv(var), f"Environment variable {var} is not set"
            )

    def test_required_directories(self):
        """Test that required directories exist."""
        required_dirs = ["data", "styles", "llm", "gradio_modules", "tests"]

        for dir_name in required_dirs:
            dir_path = parent_dir / dir_name
            self.assertTrue(
                dir_path.exists(), f"Required directory {dir_name} does not exist"
            )

    def test_required_files(self):
        """Test that required files exist."""
        required_files = [
            "app.py",
            "backend.py",
            "requirements.txt",
            "setup.py",
            "hashing.py",
        ]

        for file_name in required_files:
            file_path = parent_dir / file_name
            self.assertTrue(
                file_path.exists(), f"Required file {file_name} does not exist"
            )

    def test_module_imports(self):
        """Test that required modules can be imported."""
        required_modules = [
            "backend",
            "hashing",
            "llm.chatModel",
            "llm.classificationModel",
            "llm.dataProcessing",
            "gradio_modules.login_and_register",
            "gradio_modules.chatbot",
            "gradio_modules.file_classification",
            "gradio_modules.audio_input",
            # Legacy modules (used in tests only)
            "gradio_modules.chat_interface",
            "gradio_modules.search_interface",
            "gradio_modules.chat_history",
            "gradio_modules.file_upload",
        ]

        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_css_file(self):
        """Test that CSS file exists and is valid."""
        css_path = parent_dir / "styles" / "styles.css"
        self.assertTrue(css_path.exists(), "CSS file does not exist")

        # Try to read the file
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            self.assertTrue(len(css_content) > 0, "CSS file is empty")
        except Exception as e:
            self.fail(f"Failed to read CSS file: {e}")


def run_tests():
    """Run all tests and return True if all passed."""
    try:
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEnvironment)

        # Run tests
        result = unittest.TextTestRunner(verbosity=2).run(suite)

        # Return True if all tests passed
        return result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
