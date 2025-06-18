import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def main():
    from gradio_modules.main_app import main_app
    app = main_app()
    app.launch(debug=True, share=False)

if __name__ == "__main__":
    main()
