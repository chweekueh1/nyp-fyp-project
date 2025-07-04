#!/usr/bin/env python3
"""
Keyword caching module for OpenAI responses with filler word filtering.
Caches responses based on cleaned keywords to avoid redundant API calls.
"""

import os
import shelve
import hashlib
from typing import Optional
import logging

# Use centralized NLTK configuration for stopwords
try:
    from infra_utils.nltk_config import get_stopwords

    stop_words = get_stopwords("english")
    logging.info(f"Loaded {len(stop_words)} stopwords for keyword filtering")
except ImportError:
    stop_words = set()
    logging.warning(
        "NLTK configuration not available, stopword filtering will be skipped."
    )

# Use BASE_CHATBOT_DIR and env var for cache path
BASE_CHATBOT_DIR = os.getenv("BASE_CHATBOT_DIR", os.getcwd())
default_cache_path = os.path.join("data", "keyword_cache", "keywords_cache.db")
CACHE_PATH = os.path.join(
    BASE_CHATBOT_DIR, os.getenv("KEYWORD_CACHE_PATH", default_cache_path)
)


# Ensure cache directory exists and create empty cache file if it doesn't exist
def _ensure_cache_exists():
    """Ensure the cache directory exists and create an empty cache file if it doesn't exist."""
    try:
        cache_dir = os.path.dirname(CACHE_PATH)
        os.makedirs(cache_dir, exist_ok=True)

        # Create empty cache file if it doesn't exist
        if not os.path.exists(CACHE_PATH):
            try:
                with shelve.open(CACHE_PATH):
                    # This will create the cache file
                    pass
                logging.info(f"Created empty keyword cache at {CACHE_PATH}")
            except Exception as e:
                logging.warning(f"Failed to create keyword cache file: {e}")
    except PermissionError as e:
        logging.warning(f"Permission denied creating cache directory: {e}")
    except Exception as e:
        logging.warning(f"Failed to ensure cache exists: {e}")


# Cache initialization flag
_cache_initialized = False


def filter_filler_words(text: str) -> str:
    """Remove filler/stop words from a string."""
    if not stop_words:
        return text
    words = text.split()
    filtered = [w for w in words if w.lower() not in stop_words]
    return " ".join(filtered)


def _keyword_hash(keyword: str) -> str:
    """Hash the cleaned keyword for use as a cache key."""
    return hashlib.sha256(keyword.encode("utf-8")).hexdigest()


def get_cached_response(keyword: str) -> Optional[str]:
    """Get a cached response for a keyword (after filtering filler words)."""
    global _cache_initialized
    if not _cache_initialized:
        _ensure_cache_exists()
        _cache_initialized = True

    cleaned = filter_filler_words(keyword)
    key = _keyword_hash(cleaned)
    try:
        with shelve.open(CACHE_PATH) as db:
            return db.get(key)
    except Exception as e:
        logging.warning(f"Error reading from keyword cache: {e}")
        return None


def set_cached_response(keyword: str, response: str) -> None:
    """Set a cached response for a keyword (after filtering filler words) only if it's unique."""
    global _cache_initialized
    if not _cache_initialized:
        _ensure_cache_exists()
        _cache_initialized = True

    cleaned = filter_filler_words(keyword)
    key = _keyword_hash(cleaned)

    try:
        with shelve.open(CACHE_PATH) as db:
            # Check if this keyword already exists in cache
            if key not in db:
                db[key] = response
                logging.info(f"Cached new unique keyword: {cleaned[:50]}...")
            else:
                logging.debug(f"Keyword already cached, skipping: {cleaned[:50]}...")
    except Exception as e:
        logging.error(f"Error writing to keyword cache: {e}")


def clear_cache() -> None:
    """Clear the entire keyword cache."""
    try:
        with shelve.open(CACHE_PATH) as db:
            db.clear()
        logging.info("Keyword cache cleared successfully")
    except Exception as e:
        logging.error(f"Error clearing keyword cache: {e}")


def get_cache_stats() -> dict:
    """Get statistics about the keyword cache."""
    try:
        with shelve.open(CACHE_PATH) as db:
            keys = list(db.keys())
            return {
                "total_entries": len(keys),
                "cache_path": CACHE_PATH,
                "cache_size_bytes": os.path.getsize(CACHE_PATH)
                if os.path.exists(CACHE_PATH)
                else 0,
            }
    except Exception as e:
        logging.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


# For CLI/manual testing
if __name__ == "__main__":
    print("Testing keyword cache...")
    set_cached_response("the quick brown fox and the lazy dog", "fox jumps dog")
    print(
        get_cached_response("quick brown fox lazy dog")
    )  # Should return 'fox jumps dog'
    print(
        get_cached_response("the quick brown fox and the lazy dog")
    )  # Should return 'fox jumps dog'
    print("Cache stats:", get_cache_stats())
    clear_cache()
    print(get_cached_response("quick brown fox lazy dog"))  # Should return None
