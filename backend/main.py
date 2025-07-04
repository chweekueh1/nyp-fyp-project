#!/usr/bin/env python3
"""
Main module for the backend.
Contains initialization functions and main entry points.
"""

import logging
from .utils import _ensure_db_and_folders_async
from .database import get_llm_functions, get_chat_db
from performance_utils import perf_monitor

# Set up logging
logger = logging.getLogger(__name__)


async def init_backend():
    """Initialize the backend system."""
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
                llm_funcs["initialize_llm_and_db"]()
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


async def init_backend_async_internal():
    """Internal async initialization function."""
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
    """Get the current status of the backend components."""
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
