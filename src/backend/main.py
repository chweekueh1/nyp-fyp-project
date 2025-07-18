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
from .utils import _ensure_db_and_folders_async
from .database import get_llm_functions, get_chat_db
from performance_utils import perf_monitor

# Set up logging
logger = logging.getLogger(__name__)


async def init_backend() -> None:
    """
    Initialize the backend system.

    This function initializes all backend components including:
    - Database and folder structure
    - LLM functions and database connections
    - DuckDB vector store

    Raises:
        Exception: If any component fails to initialize
    """
    try:
        logger.info("🚀 Initializing backend...")

        # Ensure database and folders exist
        await _ensure_db_and_folders_async()

        # Initialize LLM functions and LLM/DB directly (no lazy loading)
        try:
            llm_funcs = get_llm_functions()
            if llm_funcs:
                logger.info("✅ LLM functions initialized")
                # Explicitly initialize LLM and DB
                await llm_funcs["initialize_llm_and_db"]()
                logger.info("✅ LLM and DB initialized after backend startup")
            else:
                logger.warning("⚠️ LLM functions not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM and DB: {e}")

        # Initialize DuckDB vector store
        try:
            db = get_chat_db()  # Use DuckDB chat collection directly
            if db:
                logger.info("✅ DuckDB vector store initialized")
            else:
                logger.warning("⚠️ DuckDB vector store not available")
        except Exception as e:
            logger.error(f"❌ Error initializing DuckDB vector store: {e}")

        logger.info("✅ Backend initialization completed")

    except Exception as e:
        logger.error(f"❌ Backend initialization failed: {e}")
        raise


async def init_backend_async_internal() -> None:
    """
    Internal async initialization function.

    Performs comprehensive backend initialization with performance monitoring.
    This function is called internally and includes detailed logging and
    performance tracking for each component.

    Raises:
        Exception: If any component fails to initialize
    """
    try:
        logger.info("🔄 Starting internal backend initialization...")

        # Ensure database and folders exist
        await _ensure_db_and_folders_async()

        # Initialize LLM functions with performance monitoring
        with perf_monitor("llm_initialization"):
            llm_funcs = get_llm_functions()
            if llm_funcs:
                logger.info("✅ LLM functions initialized successfully")
            else:
                logger.warning("⚠️ LLM functions initialization failed")

        # Initialize DuckDB vector store with performance monitoring
        with perf_monitor("duckdb_initialization"):
            try:
                db = get_chat_db()  # Use DuckDB chat collection directly
                if db:
                    logger.info("✅ DuckDB vector store initialized successfully")
                else:
                    logger.warning("⚠️ DuckDB vector store initialization failed")
            except Exception as e:
                logger.error(f"❌ DuckDB vector store initialization error: {e}")

        # Initialize data processing functions
        with perf_monitor("data_processing_initialization"):
            try:
                from .database import get_data_processing

                data_processing = get_data_processing()
                if data_processing:
                    logger.info("✅ Data processing functions initialized")
                else:
                    logger.warning("⚠️ Data processing functions not available")
            except Exception as e:
                logger.error(f"❌ Data processing initialization error: {e}")

        # Initialize classification functions
        with perf_monitor("classification_initialization"):
            try:
                from .database import get_classification

                classification = get_classification()
                if classification:
                    logger.info("✅ Classification functions initialized")
                else:
                    logger.warning("⚠️ Classification functions not available")
            except Exception as e:
                logger.error(f"❌ Classification initialization error: {e}")

        logger.info("✅ Internal backend initialization completed successfully")

    except Exception as e:
        logger.error(f"❌ Internal backend initialization failed: {e}")
        raise


def get_backend_status() -> dict:
    """
    Get the current status of the backend components.

    :return: Dictionary containing backend status information.
    :rtype: dict
    """
    try:
        status = {"backend_initialized": True, "components": {}}

        # Check LLM functions
        try:
            llm_funcs = get_llm_functions()
            status["components"]["llm_functions"] = {
                "available": llm_funcs is not None,
                "ready": llm_funcs["is_llm_ready"]() if llm_funcs else False,
            }
        except Exception as e:
            status["components"]["llm_functions"] = {
                "available": False,
                "error": str(e),
            }

        # Check DuckDB vector store
        try:
            db = get_chat_db()  # Use DuckDB chat collection directly
            status["components"]["duckdb_vectorstore"] = {"available": db is not None}
        except Exception as e:
            status["components"]["duckdb_vectorstore"] = {
                "available": False,
                "error": str(e),
            }

        # Check data processing
        try:
            from .database import get_data_processing

            data_processing = get_data_processing()
            status["components"]["data_processing"] = {
                "available": data_processing is not None
            }
        except Exception as e:
            status["components"]["data_processing"] = {
                "available": False,
                "error": str(e),
            }

        # Check classification
        try:
            from .database import get_classification

            classification = get_classification()
            status["components"]["classification"] = {
                "available": classification is not None
            }
        except Exception as e:
            status["components"]["classification"] = {
                "available": False,
                "error": str(e),
            }

        return status

    except Exception as e:
        logger.error(f"Error getting backend status: {e}")
        return {"backend_initialized": False, "error": str(e)}
