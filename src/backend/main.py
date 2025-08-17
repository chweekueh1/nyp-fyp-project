#!/usr/bin/env python3
"""Main module for the NYP FYP CNC Chatbot backend.

This module contains the core initialization functions and main entry points
for the backend system. It handles:

- Backend system initialization
- LLM and database setup
- Performance monitoring integration
- System status reporting

The module provides both synchronous and asynchronous initialization
functions to support different deployment scenarios.
"""

import logging
import os
from .utils import _ensure_db_and_folders_async
from .database import (
    get_llm_functions,
    get_chat_db,
    get_data_processing,
    get_classification,
    get_classification_db,  # Added to ensure classification_db from database.py is checked
)
from performance_utils import perf_monitor
from . import (
    timezone_utils,
)  # Import timezone_utils to ensure it's loaded and initialized
from typing import Dict, Any
from .consolidated_database import (
    get_consolidated_database,
)  # New: Import consolidated database

# Set up logging
logger = logging.getLogger(__name__)


async def init_backend() -> None:
    """
    Initialize the backend system.

    This function initializes all backend components including:
    - Database and folder structure
    - LLM functions and database connections
    - DuckDB vector store
    - Data processing module
    - Classification module
    - Timezone utilities (by importing)

    Raises:
        Exception: If any component fails to initialize
    """
    try:
        logger.info("🚀 Initializing backend...")
        perf_monitor.start_timer("backend_init_total")

        # Ensure database and folders exist
        perf_monitor.start_timer("db_and_folders_init")
        await _ensure_db_and_folders_async()
        perf_monitor.end_timer("db_and_folders_init")
        logger.info("✅ Database and folders ensured.")

        # Initialize LLM functions and LLM/DB directly (no lazy loading)
        try:
            perf_monitor.start_timer("llm_functions_init")
            llm_funcs = get_llm_functions()
            if llm_funcs:
                logger.info("✅ LLM functions initialized")
                # Explicitly call LLM initialization if it has such a method
                if "initialize_llm_and_db" in llm_funcs:
                    await llm_funcs["initialize_llm_and_db"]()
                    logger.info("✅ LLM model and associated DB initialized.")
                else:
                    logger.warning("LLM initialization function not found.")
            else:
                logger.warning("LLM functions could not be initialized.")
            perf_monitor.end_timer("llm_functions_init")
        except Exception as e:
            logger.error(f"Error initializing LLM functions: {e}")
            raise

        # Initialize OpenAI Whisper client for audio transcription
        try:
            perf_monitor.start_timer("openai_whisper_client_init")
            from backend import config

            if config.client is None:
                import openai

                openai_api_key = os.getenv("OPENAI_API_KEY")
                if openai_api_key:
                    config.client = openai.OpenAI(api_key=openai_api_key)
                    logger.info(
                        "✅ OpenAI Whisper client initialized for audio transcription."
                    )
                else:
                    logger.warning(
                        "OPENAI_API_KEY not set. Whisper client not initialized."
                    )
            perf_monitor.end_timer("openai_whisper_client_init")
        except Exception as e:
            logger.error(f"Error initializing OpenAI Whisper client: {e}")

        # Initialize DuckDB chat vector store
        try:
            perf_monitor.start_timer("duckdb_chat_init")
            chat_duck_db = get_chat_db()
            if chat_duck_db:
                logger.info("✅ DuckDB chat vector database initialized.")
            perf_monitor.end_timer("duckdb_chat_init")
        except Exception as e:
            logger.error(f"Error initializing DuckDB chat vector database: {e}")
            raise

        # Initialize DuckDB classification vector store
        try:
            perf_monitor.start_timer("duckdb_classification_init")
            classification_duck_db = get_classification_db()
            if classification_duck_db:
                logger.info("✅ DuckDB classification vector database initialized.")
            perf_monitor.end_timer("duckdb_classification_init")
        except Exception as e:
            logger.error(
                f"Error initializing DuckDB classification vector database: {e}"
            )
            raise

        # Initialize consolidated SQLite database
        try:
            perf_monitor.start_timer("consolidated_sqlite_db_init")
            consolidated_sqlite_db = get_consolidated_database()
            if consolidated_sqlite_db:
                logger.info("✅ Consolidated SQLite database initialized.")
            perf_monitor.end_timer("consolidated_sqlite_db_init")
        except Exception as e:
            logger.error(f"Error initializing consolidated SQLite database: {e}")
            raise

        # Initialize data processing module
        try:
            perf_monitor.start_timer("data_processing_init")
            data_proc = get_data_processing()
            if data_proc:
                logger.info("✅ Data processing module initialized.")
            perf_monitor.end_timer("data_processing_init")
        except Exception as e:
            logger.error(f"Error initializing data processing module: {e}")
            raise

        # Initialize classification module (separate from classification_db if it's just the module)
        try:
            perf_monitor.start_timer("classification_module_init")
            classification_module = get_classification()
            if classification_module:
                logger.info("✅ Classification module initialized.")
                # Ensure classification workflow is initialized
                try:
                    from llm.classificationModel import (
                        initialize_classification_workflow,
                    )

                    initialize_classification_workflow()
                    logger.info("✅ Classification workflow initialized.")
                except Exception as e:
                    logger.error(f"Error initializing classification workflow: {e}")
            perf_monitor.end_timer("classification_module_init")
        except Exception as e:
            logger.error(f"Error initializing classification module: {e}")
            raise

        # Timezone utilities are implicitly initialized by import.
        # Add a quick check to ensure they are accessible.
        try:
            perf_monitor.start_timer("timezone_utils_check")
            _ = timezone_utils.get_app_timezone()
            logger.info("✅ Timezone utilities available.")
            perf_monitor.end_timer("timezone_utils_check")
        except Exception as e:
            logger.error(f"Error checking timezone utilities: {e}")
            raise

        perf_monitor.end_timer("backend_init_total")
        logger.info("🚀 Backend initialization complete.")
    except Exception as e:
        logger.critical(f"🔥 Backend initialization failed: {e}", exc_info=True)
        raise


def get_backend_status() -> Dict[str, Any]:
    """
    Check the status of various backend components.

    :return: A dictionary containing the status of each component.
    :rtype: Dict[str, Any]
    """
    logger.info("Checking backend status...")
    status = {"backend_initialized": True, "components": {}}

    try:
        # Check LLM functions
        try:
            llm_funcs = get_llm_functions()
            status["components"]["llm_functions"] = {"available": llm_funcs is not None}
        except Exception as e:
            status["components"]["llm_functions"] = {
                "available": False,
                "error": str(e),
            }

        # Check Consolidated SQLite Database
        try:
            consolidated_db = get_consolidated_database()
            status["components"]["consolidated_sqlite_db"] = {
                "available": consolidated_db is not None
            }
        except Exception as e:
            status["components"]["consolidated_sqlite_db"] = {
                "available": False,
                "error": str(e),
            }

        # Check DuckDB chat database
        try:
            chat_duck_db = get_chat_db()
            status["components"]["duckdb_chat_db"] = {
                "available": chat_duck_db is not None
            }
        except Exception as e:
            status["components"]["duckdb_chat_db"] = {
                "available": False,
                "error": str(e),
            }

        # Check DuckDB classification database
        try:
            classification_duck_db = get_classification_db()
            status["components"]["duckdb_classification_db"] = {
                "available": classification_duck_db is not None
            }
        except Exception as e:
            status["components"]["duckdb_classification_db"] = {
                "available": False,
                "error": str(e),
            }

        # Check data processing
        try:
            data_processing = get_data_processing()
            status["components"]["data_processing"] = {
                "available": data_processing is not None
            }
        except Exception as e:
            status["components"]["data_processing"] = {
                "available": False,
                "error": str(e),
            }

        # Check classification module
        try:
            classification = get_classification()
            status["components"]["classification_module"] = {
                "available": classification is not None
            }
        except Exception as e:
            status["components"]["classification_module"] = {
                "available": False,
                "error": str(e),
            }

        # Check timezone utilities
        try:
            # Simply checking if the module can be accessed
            _ = timezone_utils.get_app_timezone()
            status["components"]["timezone_utils"] = {"available": True}
        except Exception as e:
            status["components"]["timezone_utils"] = {
                "available": False,
                "error": str(e),
            }

        return status

    except Exception as e:
        logger.error(f"Error getting backend status: {e}")
        return {"backend_initialized": False, "error": str(e)}
