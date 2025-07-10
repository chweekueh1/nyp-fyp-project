#!/usr/bin/env python3
"""
Database module for the NYP FYP CNC Chatbot backend.

This module provides database functionality including:

- DuckDB-based vector store implementation for document storage and retrieval
- LangChain-compatible retriever interface
- Lazy loading functions for database connections
- Document embedding and similarity search
- Keyword-based filtering capabilities
- Integration with OpenAI embeddings

The module supports both synchronous and asynchronous operations
and provides a scalable vector database solution for the chatbot.
"""

import os
import duckdb
import json
import numpy as np
from typing import List, Dict, Any, Optional  # noqa: F401
from performance_utils import lazy_loader
from .config import DATABASE_PATH, EMBEDDING_MODEL
from langchain_openai import OpenAIEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from infra_utils import create_folders

# --- DuckDB Vector Store Implementation ---


class DuckDBVectorStore:
    """DuckDB-based vector store for document storage and retrieval.

    This class provides a vector store implementation using DuckDB as the backend,
    compatible with LangChain's vector store interface.
    """

    def __init__(self, db_path: str, collection_name: str, embedding_model: str):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # Create collection-specific database file in subdirectory
        collection_dir = os.path.join(db_path, collection_name)
        create_folders(collection_dir)
        self.db_file = os.path.join(collection_dir, f"{collection_name}.db")

        self.conn = duckdb.connect(self.db_file)
        self._ensure_table()
        self.embedding = OpenAIEmbeddings(model=embedding_model)

    def _ensure_table(self):
        """Ensure the database table exists with the correct schema.

        Creates a table with columns for id, content, embedding (JSON),
        metadata (JSON), and 10 keyword columns for filtering.
        """
        # Table schema: id, content, embedding (JSON), metadata (JSON), keyword0...keyword9
        cols = ", ".join([f"keyword{i} VARCHAR" for i in range(10)])
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.collection_name} (
                id VARCHAR PRIMARY KEY,
                content TEXT,
                embedding JSON,
                metadata JSON,
                {cols}
            )
        """)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store.

        :param documents: List of document dictionaries with keys:
                         - id: Document identifier (optional, auto-generated if missing)
                         - content: Document text content
                         - metadata: Document metadata dictionary
                         - keywords: List of keywords for filtering (stored in metadata)
        :type documents: List[Dict[str, Any]]
        """
        # Each document: {id, content, metadata, keywords}
        to_insert = []
        for doc in documents:
            doc_id = doc.get("id") or str(hash(doc["content"]))
            content = doc["content"]
            metadata = doc.get("metadata", {})
            keywords = metadata.get("keywords", [])
            # Pad keywords to 10
            kw_cols = [keywords[i] if i < len(keywords) else None for i in range(10)]
            # Compute embedding
            embedding = self.embedding.embed_query(content)
            to_insert.append(
                (doc_id, content, json.dumps(embedding), json.dumps(metadata), *kw_cols)
            )
        cols = ", ".join([f"keyword{i}" for i in range(10)])
        placeholders = ", ".join(["?"] * (4 + 10))
        self.conn.executemany(
            f"INSERT OR REPLACE INTO {self.collection_name} (id, content, embedding, metadata, {cols}) VALUES ({placeholders})",
            to_insert,
        )

    def query(
        self, query_text: str, k: int = 5, keyword_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query the vector store for similar documents.

        :param query_text: The query text to search for.
        :type query_text: str
        :param k: Number of top results to return.
        :type k: int
        :param keyword_filter: Optional list of keywords to filter results.
        :type keyword_filter: Optional[List[str]]
        :return: List of document dictionaries with similarity scores.
        :rtype: List[Dict[str, Any]]
        """
        # Compute embedding for query
        query_emb = np.array(self.embedding.embed_query(query_text))
        # Build SQL filter for keywords
        where = ""
        params = []
        if keyword_filter:
            clauses = []
            for i in range(10):
                clauses.append(
                    f"keyword{i} IN ({', '.join(['?'] * len(keyword_filter))})"
                )
                params.extend(keyword_filter)
            where = "WHERE (" + " OR ".join(clauses) + ")"
        # Fetch all candidate docs
        sql = f"SELECT id, content, embedding, metadata FROM {self.collection_name} {where}"
        docs = self.conn.execute(sql, params).fetchall()
        # Compute cosine similarity
        results = []
        for doc_id, content, emb_json, metadata_json in docs:
            emb = np.array(json.loads(emb_json))
            sim = float(
                np.dot(query_emb, emb)
                / (np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-8)
            )
            results.append(
                {
                    "id": doc_id,
                    "content": content,
                    "metadata": json.loads(metadata_json),
                    "similarity": sim,
                }
            )
        # Return top-k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:k]

    def get(self, limit: int = 1) -> List[Dict[str, Any]]:
        """Get documents from the collection.

        :param limit: Maximum number of documents to return.
        :type limit: int
        :return: List of document dictionaries.
        :rtype: List[Dict[str, Any]]
        """
        sql = f"SELECT id, content, metadata FROM {self.collection_name} LIMIT {limit}"
        docs = self.conn.execute(sql).fetchall()
        return [
            {"id": doc[0], "content": doc[1], "metadata": json.loads(doc[2])}
            for doc in docs
        ]

    def as_retriever(
        self, search_kwargs: Optional[Dict[str, Any]] = None
    ) -> "DuckDBRetriever":
        """Return a retriever interface compatible with LangChain.

        :param search_kwargs: Optional search parameters for the retriever.
        :type search_kwargs: Optional[Dict[str, Any]]
        :return: DuckDBRetriever instance.
        :rtype: DuckDBRetriever
        """
        return DuckDBRetriever(self, search_kwargs or {})


class DuckDBRetriever(BaseRetriever):
    """Retriever interface for DuckDB vector store compatible with LangChain.

    This class provides a LangChain-compatible retriever interface for the
    DuckDB vector store, allowing integration with LangChain workflows.
    """

    @property
    def lc_namespace(self) -> list:
        """
        LangChain namespace for this retriever.

        :return: List of namespace components.
        :rtype: list
        """
        return ["backend", "database", "DuckDBRetriever"]

    @property
    def lc_id(self) -> str:
        """
        LangChain identifier for this retriever.

        :return: Unique identifier string.
        :rtype: str
        """
        return "duckdb_retriever"

    def __init__(self, vector_store: DuckDBVectorStore, search_kwargs: Dict[str, Any]):
        super().__init__()
        self._vector_store = vector_store
        self._search_kwargs = search_kwargs

    @property
    def vector_store(self) -> DuckDBVectorStore:
        """
        Get the underlying vector store instance.

        :return: The DuckDB vector store instance.
        :rtype: DuckDBVectorStore
        """
        return self._vector_store

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get relevant documents for a query using LangChain interface.

        :param query: The search query.
        :type query: str
        :param run_manager: LangChain callback manager for the retrieval run.
        :type run_manager: CallbackManagerForRetrieverRun
        :return: List of LangChain Document objects.
        :rtype: List[Document]
        """
        k = self._search_kwargs.get("k", 5)
        keyword_filter = self._search_kwargs.get("filter", {}).get("keywords", None)

        results = self.vector_store.query(query, k=k, keyword_filter=keyword_filter)
        return [
            Document(page_content=r["content"], metadata=r["metadata"]) for r in results
        ]

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents for a query (legacy compatibility method).

        :param query: The search query.
        :type query: str
        :return: List of LangChain Document objects.
        :rtype: List[Document]
        """
        k = self._search_kwargs.get("k", 5)
        keyword_filter = self._search_kwargs.get("filter", {}).get("keywords", None)

        results = self.vector_store.query(query, k=k, keyword_filter=keyword_filter)
        return [
            Document(page_content=r["content"], metadata=r["metadata"]) for r in results
        ]


# --- Lazy loading for collections ---
def get_duckdb_collection(collection_name: str) -> DuckDBVectorStore:
    """Lazy load DuckDB vector store collection.

    :param collection_name: Name of the collection to load.
    :type collection_name: str
    :return: DuckDBVectorStore instance for the specified collection.
    :rtype: DuckDBVectorStore
    """
    return lazy_loader.load_module(
        f"duckdb_{collection_name}",
        lambda: DuckDBVectorStore(DATABASE_PATH, collection_name, EMBEDDING_MODEL),
    )


def get_chat_db() -> DuckDBVectorStore:
    """
    Get DuckDB chat collection for conversation history.

    :return: DuckDBVectorStore instance for chat documents.
    :rtype: DuckDBVectorStore
    """
    return get_duckdb_collection("chat")


def get_classification_db() -> DuckDBVectorStore:
    """
    Get DuckDB classification collection for document classification.

    :return: DuckDBVectorStore instance for classification documents.
    :rtype: DuckDBVectorStore
    """
    return get_duckdb_collection("classification")


# --- Other lazy loading functions (unchanged) ---
def get_llm_functions() -> Dict[str, Any]:
    """
    Get LLM functions for chat operations.

    :return: Dictionary containing LLM function references.
    :rtype: Dict[str, Any]
    """
    from llm import chatModel

    # Return a dictionary of functions instead of the module
    return {
        "get_convo_hist_answer": chatModel.get_convo_hist_answer,
        "is_llm_ready": chatModel.is_llm_ready,
        "initialize_llm_and_db": chatModel.initialize_llm_and_db,
    }


def get_data_processing() -> Any:
    """
    Get data processing module.

    :return: Data processing module.
    :rtype: Any
    """
    from llm import dataProcessing

    return dataProcessing


def get_classification() -> Any:
    """
    Get classification module.

    :return: Classification module.
    :rtype: Any
    """
    from llm import classificationModel

    return classificationModel
