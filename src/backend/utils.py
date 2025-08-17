#!/usr/bin/env python3
"""
Utility functions module for the backend.
Contains helper functions and utilities.
"""

import os
import html
import re
import asyncio
from typing import Dict, Any, Union
from infra_utils import setup_logging, ensure_chatbot_dir_exists
from .config import CHAT_DATA_PATH, CHAT_SESSIONS_PATH
from .consolidated_database import get_consolidated_database  # Updated import

# Set up logging
logger = setup_logging()


def sanitize_input(input_text: str) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.

    :param input_text: The input text to sanitize.
    :type input_text: str
    :return: Sanitized input text with HTML tags removed and entities escaped.
    :rtype: str
    """
    if not input_text:
        return ""

    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", "", input_text)

    # Escape HTML entities
    cleaned = html.escape(cleaned)

    # Remove potentially dangerous characters
    cleaned = re.sub(r'[<>"\\\']', "", cleaned)

    # Handle arrow characters to prevent them from being interpreted as HTML entities
    # Use temporary placeholders to avoid conflicts with HTML entity escaping
    cleaned = cleaned.replace("-->", "ARROWLONGPLACEHOLDER")
    cleaned = cleaned.replace("-.->", "ARROWDOTTEDPLACEHOLDER")
    cleaned = cleaned.replace("==>", "ARROWTHICKPLACEHOLDER")
    cleaned = cleaned.replace("=>", "ARROWFATPLACEHOLDER")
    cleaned = cleaned.replace("<-", "ARROWLEFTPLACEHOLDER")
    cleaned = cleaned.replace("<->", "ARROWDOUBLEPLACEHOLDER")

    # Replace placeholders with desired rendering (e.g., Markdown compatible arrows)
    # This step is crucial if the output is later rendered as Markdown.
    cleaned = cleaned.replace("ARROWLONGPLACEHOLDER", "-->")
    cleaned = cleaned.replace("ARROWDOTTEDPLACEHOLDER", "-.->")
    cleaned = cleaned.replace("ARROWTHICKPLACEHOLDER", "==>")
    cleaned = cleaned.replace("ARROWFATPLACEHOLDER", "=>")
    cleaned = cleaned.replace("ARROWLEFTPLACEHOLDER", "<-")
    cleaned = cleaned.replace("ARROWDOUBLEPLACEHOLDER", "<->")

    return cleaned


async def _ensure_db_and_folders_async() -> None:
    """
    Asynchronously ensure that the database and necessary folders exist.
    """
    # Ensure base chatbot data directory exists
    await asyncio.to_thread(ensure_chatbot_dir_exists)
    logger.info("Chatbot base directory ensured.")

    # Ensure chat data and session paths exist
    os.makedirs(CHAT_DATA_PATH, exist_ok=True)
    os.makedirs(CHAT_SESSIONS_PATH, exist_ok=True)
    logger.info("Chat data and session directories ensured.")

    # Initialize the consolidated SQLite database
    try:
        db = get_consolidated_database()  # Use the consolidated database
        logger.info(f"Consolidated SQLite database initialized at {db.db_path}.")
    except Exception as e:
        logger.critical(
            f"Failed to initialize consolidated SQLite database: {e}", exc_info=True
        )
        raise  # Re-raise to halt startup if database cannot be initialized


def health_check() -> Dict[str, Any]:
    """
    Performs a health check on the backend components.

    :return: Dictionary containing the health status.
    :rtype: Dict[str, Any]
    """
    try:
        # Check file system health
        if not os.path.exists(CHAT_DATA_PATH) or not os.path.exists(CHAT_SESSIONS_PATH):
            return {"status": "error", "message": "File system paths missing"}

        # Check SQLite database connection
        try:
            db = get_consolidated_database()  # Use the consolidated database
            # Attempt a simple query to verify connection
            db.execute_query("SELECT 1")
        except Exception:
            return {
                "status": "error",
                "message": "SQLite database is not responding",
            }

        return {"status": "healthy", "message": "All systems operational"}

    except Exception as e:
        return {"status": "error", "message": f"Health check failed: {e}"}


def get_completion(
    prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 150,
    temperature: float = 0.8,
) -> Union[str, Dict[str, Any]]:
    """
    Get a completion from OpenAI.

    :param prompt: The prompt to send to the model
    :type prompt: str
    :param model: The model to use
    :type model: str
    :param max_tokens: Maximum tokens to generate
    :type max_tokens: int
    :param temperature: Temperature for generation
    :type temperature: float
    :return: The completion response
    :rtype: Union[str, Dict[str, Any]]
    """
    try:
        from .config import client

        if client is None:
            logger.error("OpenAI client is not initialized.")
            return {"error": "OpenAI client not available."}

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        else:
            return {"error": "No response from model"}

    except Exception as e:
        logger.error(f"Error getting completion from OpenAI: {e}")
        return {"error": f"Failed to get completion: {e}"}
