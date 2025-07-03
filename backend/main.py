#!/usr/bin/env python3
"""
Main module for the backend.
Contains initialization functions and main entry points.
"""

import logging
from .utils import _ensure_db_and_folders_async
from .database import get_llm_functions, get_chroma_db
from performance_utils import perf_monitor

# Set up logging
logger = logging.getLogger(__name__)


async def init_backend():
    """Initialize the backend system."""
    try:
        logger.info("🚀 Initializing backend...")

        # Ensure database and folders exist
        await _ensure_db_and_folders_async()

        # Initialize LLM functions
        llm_funcs = get_llm_functions()
        if llm_funcs:
            logger.info("✅ LLM functions initialized")
        else:
            logger.warning("⚠️ LLM functions not available")

        # Initialize ChromaDB
        try:
            db = get_chroma_db()
            if db:
                logger.info("✅ ChromaDB initialized")
            else:
                logger.warning("⚠️ ChromaDB not available")
        except Exception as e:
            logger.error(f"❌ Error initializing ChromaDB: {e}")

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

        # Initialize ChromaDB with performance monitoring
        with perf_monitor("chromadb_initialization"):
            try:
                db = get_chroma_db()
                if db:
                    logger.info("✅ ChromaDB initialized successfully")
                else:
                    logger.warning("⚠️ ChromaDB initialization failed")
            except Exception as e:
                logger.error(f"❌ ChromaDB initialization error: {e}")

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

        # Check ChromaDB
        try:
            db = get_chroma_db()
            status["components"]["chromadb"] = {"available": db is not None}
        except Exception as e:
            status["components"]["chromadb"] = {"available": False, "error": str(e)}

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
