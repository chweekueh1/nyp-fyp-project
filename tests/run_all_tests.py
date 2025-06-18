#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
import unittest
import importlib.util
import json
from datetime import datetime

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Set up logging
log_dir = parent_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - (%(filename)s) - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
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

def discover_tests():
    """Discover all test modules in the tests directory."""
    test_loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent)
    suite = test_loader.discover(start_dir, pattern="test_*.py")
    return suite

def run_tests():
    """Run all tests and return True if all passed."""
    try:
        # Discover and run tests
        suite = discover_tests()
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        # Log results
        if result.wasSuccessful():
            logger.info("All tests passed successfully!")
        else:
            logger.error("Some tests failed!")
            for error in result.errors:
                logger.error(f"Error: {error[0]}\n{error[1]}")
            for failure in result.failures:
                logger.error(f"Failure: {failure[0]}\n{failure[1]}")
        
        return result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting test run...")
    success = run_tests()
    sys.exit(0 if success else 1) 