import os
import sys
from pathlib import Path
import gradio as gr
from utils import setup_logging

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
logger = setup_logging()

from gradio_modules.main_app import main_app

if __name__ == "__main__":
    app = main_app()
    app.launch(debug=True, share=False)
