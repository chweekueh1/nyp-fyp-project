#!/usr/bin/env python3
"""
Database module for the backend.
Contains lazy loading functions for ChromaDB and database-related utilities.
"""

from performance_utils import lazy_loader
from .config import DATABASE_PATH, EMBEDDING_MODEL


# Lazy imports for performance
def get_chroma_db():
    """Lazy load ChromaDB."""
    return lazy_loader.load_module("chroma", lambda: _init_chroma_db())


def _init_chroma_db():
    """Initialize ChromaDB with lazy imports."""
    from langchain_chroma import Chroma
    from langchain_openai.embeddings import OpenAIEmbeddings

    return Chroma(
        collection_name="classification",
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=DATABASE_PATH,
    )


# Lazy loading functions for performance
def get_llm_functions():
    """Lazy load LLM functions."""
    return lazy_loader.load_module("llm_functions", lambda: _init_llm_functions())


def _init_llm_functions():
    """Initialize LLM functions with lazy imports."""
    from llm import chatModel

    return chatModel


def get_data_processing():
    """Lazy load data processing functions."""
    return lazy_loader.load_module("data_processing", lambda: _init_data_processing())


def _init_data_processing():
    """Initialize data processing with lazy imports."""
    from llm import dataProcessing

    return dataProcessing


def get_classification():
    """Lazy load classification functions."""
    return lazy_loader.load_module("classification", lambda: _init_classification())


def _init_classification():
    """Initialize classification with lazy imports."""
    from llm import classificationModel

    return classificationModel
