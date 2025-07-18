#!/usr/bin/env python3
"""
NLTK Configuration Module

This module provides centralized NLTK configuration for the NYP FYP Chatbot application.
It ensures NLTK data is stored in the .nypai-chatbot directory for consistency.
"""

import contextlib
import os
import logging
from typing import Set

# Set up logging
logger = logging.getLogger(__name__)


def setup_nltk_data_path() -> str:
    """
    Set up NLTK data path to use /home/appuser/.nypai-chatbot/data/nltk_data directory.

    :return: Path to NLTK data directory
    :rtype: str
    """
    try:
        # Hardcode the correct NLTK data path for all environments
        nltk_data_path = "/home/appuser/.nypai-chatbot/data/nltk_data"

        # Remove any reference to /root/.nypai-chatbot from NLTK data path
        import nltk

        # Remove /root/.nypai-chatbot and its subdirs from nltk.data.path
        nltk.data.path = [
            p for p in nltk.data.path if not p.startswith("/root/.nypai-chatbot")
        ]

        # Also ensure the directory and subdirectories exist and are writable
        if not os.environ.get("BENCHMARK_MODE"):
            os.makedirs(nltk_data_path, exist_ok=True)
            # Create required subdirectories for NLTK data
            for subdir in ["tokenizers", "corpora", "taggers"]:
                subdir_path = os.path.join(nltk_data_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                with contextlib.suppress(Exception):
                    os.chmod(subdir_path, 0o777)
            # Set permissions to ensure appuser can write
            with contextlib.suppress(Exception):
                os.chmod(nltk_data_path, 0o777)
        # Configure NLTK to use this path
        if nltk_data_path not in nltk.data.path:
            nltk.data.path.insert(0, nltk_data_path)

        return nltk_data_path

    except Exception as e:
        logger.warning(f"Failed to configure NLTK data path: {e}")
        return ""


def get_stopwords(language: str = "english") -> Set[str]:
    """
    Get stopwords for the specified language, downloading if necessary.

    :param language: Language for stopwords, defaults to "english"
    :type language: str
    :return: Set of stopwords
    :rtype: Set[str]
    """
    try:
        import nltk
        from nltk.corpus import stopwords

        # Ensure NLTK data path is configured
        nltk_data_path = setup_nltk_data_path()

        try:
            return set(stopwords.words(language))
        except LookupError:
            if nltk_data_path:
                nltk.download("stopwords", download_dir=nltk_data_path, quiet=True)
                return set(stopwords.words(language))
            else:
                logger.warning("Could not download stopwords - no valid data path")
                return _get_fallback_stopwords()

    except ImportError:
        logger.warning("NLTK not available, using fallback stopwords")
        return _get_fallback_stopwords()
    except Exception as e:
        logger.error(f"Error loading stopwords: {e}")
        return _get_fallback_stopwords()


def _get_fallback_stopwords() -> Set[str]:
    """
    Get fallback stopwords when NLTK is not available.

    :return: Set of common English stopwords
    :rtype: Set[str]
    """
    return {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "to",
        "was",
        "will",
        "with",
        "the",
        "this",
        "but",
        "they",
        "have",
        "had",
        "what",
        "said",
        "each",
        "which",
        "she",
        "do",
        "how",
        "their",
        "if",
        "up",
        "out",
        "many",
        "then",
        "them",
        "these",
        "so",
        "some",
        "her",
        "would",
        "make",
        "like",
        "into",
        "him",
        "time",
        "two",
        "more",
        "go",
        "no",
        "way",
        "could",
        "my",
        "than",
        "first",
        "been",
        "call",
        "who",
        "oil",
        "sit",
        "now",
        "find",
        "down",
        "day",
        "did",
        "get",
        "come",
        "made",
        "may",
        "part",
        "over",
        "new",
        "take",
        "only",
        "little",
        "work",
        "know",
        "place",
        "me",
        "back",
        "most",
        "very",
        "after",
        "thing",
        "our",
        "just",
        "name",
        "good",
        "sentence",
        "man",
        "think",
        "where",
        "help",
        "through",
        "much",
        "before",
        "right",
        "too",
        "mean",
        "any",
        "same",
        "follow",
        "came",
        "also",
        "around",
        "three",
        "put",
        "why",
        "again",
        "turn",
        "here",
        "off",
        "went",
        "old",
        "number",
        "great",
        "tell",
        "men",
        "say",
        "small",
        "every",
        "found",
        "still",
        "between",
        "mane",
        "should",
        "home",
        "big",
        "give",
        "air",
        "line",
        "set",
        "own",
        "under",
        "read",
        "last",
        "never",
        "us",
        "left",
        "end",
        "along",
        "while",
        "might",
        "next",
        "sound",
        "below",
        "saw",
        "something",
        "thought",
        "both",
        "few",
        "those",
        "always",
        "looked",
        "show",
        "large",
        "often",
        "together",
        "asked",
        "house",
        "don't",
        "world",
        "going",
        "want",
        "school",
        "important",
        "until",
        "form",
        "food",
        "keep",
        "children",
        "feet",
        "land",
        "side",
        "without",
        "boy",
        "animal",
        "life",
        "sometimes",
        "four",
        "head",
        "kind",
        "almost",
        "live",
        "page",
        "got",
        "earth",
        "need",
        "far",
        "hand",
        "high",
        "year",
        "mother",
        "light",
        "country",
        "father",
        "let",
        "night",
        "picture",
        "being",
        "study",
        "second",
        "book",
        "carry",
        "took",
        "science",
        "eat",
        "room",
        "friend",
        "began",
        "idea",
        "fish",
        "mountain",
        "north",
        "once",
        "base",
        "hear",
        "horse",
        "cut",
        "sure",
        "watch",
        "color",
        "face",
        "wood",
        "main",
        "enough",
        "plain",
        "girl",
        "usual",
        "young",
        "ready",
        "above",
        "ever",
        "red",
        "list",
        "though",
        "feel",
        "talk",
        "bird",
        "soon",
        "body",
        "dog",
        "family",
        "direct",
        "leave",
        "song",
        "measure",
        "door",
        "product",
        "black",
        "short",
        "numeral",
        "class",
        "wind",
        "question",
        "happen",
        "complete",
        "ship",
        "area",
        "half",
        "rock",
        "order",
        "fire",
        "south",
        "problem",
        "piece",
        "told",
        "knew",
        "pass",
        "since",
        "top",
        "whole",
        "king",
        "space",
        "heard",
        "best",
        "hour",
        "better",
        "during",
        "hundred",
        "five",
        "remember",
        "step",
        "early",
        "hold",
        "west",
        "ground",
        "interest",
        "reach",
        "fast",
        "verb",
        "sing",
        "listen",
        "six",
        "table",
        "travel",
        "less",
        "morning",
        "ten",
        "simple",
        "several",
        "vowel",
        "toward",
        "war",
        "lay",
        "against",
        "pattern",
        "slow",
        "center",
        "love",
        "person",
        "money",
        "serve",
        "appear",
        "road",
        "map",
        "rain",
        "rule",
        "govern",
        "pull",
        "cold",
        "notice",
        "voice",
        "unit",
        "power",
        "town",
        "fine",
        "certain",
        "fly",
        "fall",
        "lead",
        "cry",
        "dark",
        "machine",
        "note",
        "wait",
        "plan",
        "figure",
        "star",
        "box",
        "noun",
        "field",
        "rest",
        "correct",
        "able",
        "pound",
        "done",
        "beauty",
        "drive",
        "stood",
        "contain",
        "front",
        "teach",
        "week",
        "final",
        "gave",
        "green",
        "oh",
        "quick",
        "develop",
        "ocean",
        "warm",
        "free",
        "minute",
        "strong",
        "special",
        "mind",
        "behind",
        "clear",
        "tail",
        "produce",
        "fact",
        "street",
        "inch",
        "multiply",
        "nothing",
        "course",
        "stay",
        "wheel",
        "full",
        "force",
        "blue",
        "object",
        "decide",
        "surface",
        "deep",
        "moon",
        "island",
        "foot",
        "system",
        "busy",
        "test",
        "record",
        "boat",
        "common",
        "gold",
        "possible",
        "plane",
        "stead",
        "dry",
        "wonder",
        "laugh",
        "thousands",
        "ago",
        "ran",
        "check",
        "game",
        "shape",
        "equate",
        "hot",
        "miss",
        "brought",
        "heat",
        "snow",
        "tire",
        "bring",
        "yes",
        "distant",
        "fill",
        "east",
        "paint",
        "language",
        "among",
    }


def download_required_nltk_data() -> bool:
    """
    Download all required NLTK data to the configured directory.

    :return: True if successful, False otherwise
    :rtype: bool
    """
    try:
        import nltk

        nltk_data_path = setup_nltk_data_path()
        if not nltk_data_path:
            return False

        # List of required NLTK data
        required_data = ["stopwords", "punkt", "wordnet", "averaged_perceptron_tagger"]

        success = True
        for data_name in required_data:
            try:
                nltk.download(data_name, download_dir=nltk_data_path, quiet=True)
            except Exception as e:
                logger.warning(f"Failed to download {data_name}: {e}")
                success = False

        return success

    except ImportError:
        logger.warning("NLTK not available for data download")
        return False
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {e}")
        return False


# Initialize NLTK configuration on module import
try:
    setup_nltk_data_path()
except Exception as e:
    logger.warning(f"Failed to initialize NLTK configuration: {e}")
