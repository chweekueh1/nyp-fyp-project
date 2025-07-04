#!/usr/bin/env python3
"""
Database module for the backend.
Contains lazy loading functions for DuckDB-based vector store and database-related utilities.
"""

import os
import duckdb
import json
import numpy as np
from typing import List, Dict, Any, Optional
from performance_utils import lazy_loader
from .config import DATABASE_PATH, EMBEDDING_MODEL
from langchain_openai import OpenAIEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from infra_utils import create_folders

# --- DuckDB Vector Store Implementation ---


class DuckDBVectorStore:
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
        """Get documents from the collection (for compatibility with ChromaDB)."""
        sql = f"SELECT id, content, metadata FROM {self.collection_name} LIMIT {limit}"
        docs = self.conn.execute(sql).fetchall()
        return [
            {"id": doc[0], "content": doc[1], "metadata": json.loads(doc[2])}
            for doc in docs
        ]

    def as_retriever(
        self, search_kwargs: Optional[Dict[str, Any]] = None
    ) -> "DuckDBRetriever":
        """Return a retriever interface (for compatibility with ChromaDB)."""
        return DuckDBRetriever(self, search_kwargs or {})


class DuckDBRetriever(BaseRetriever):
    @property
    def lc_namespace(self):
        return ["backend", "database", "DuckDBRetriever"]

    @property
    def lc_id(self):
        return "duckdb_retriever"

    """Retriever interface for DuckDB vector store (compatible with LangChain)."""

    def __init__(self, vector_store: DuckDBVectorStore, search_kwargs: Dict[str, Any]):
        super().__init__()
        self._vector_store = vector_store
        self.search_kwargs = search_kwargs

    @property
    def vector_store(self):
        return self._vector_store

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get relevant documents for a query."""
        k = self.search_kwargs.get("k", 5)
        keyword_filter = self.search_kwargs.get("filter", {}).get("keywords", None)

        results = self.vector_store.query(query, k=k, keyword_filter=keyword_filter)
        return [
            Document(page_content=r["content"], metadata=r["metadata"]) for r in results
        ]

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents for a query (legacy compatibility method)."""
        k = self.search_kwargs.get("k", 5)
        keyword_filter = self.search_kwargs.get("filter", {}).get("keywords", None)

        results = self.vector_store.query(query, k=k, keyword_filter=keyword_filter)
        return [
            Document(page_content=r["content"], metadata=r["metadata"]) for r in results
        ]


# --- Lazy loading for collections ---
def get_duckdb_collection(collection_name: str) -> DuckDBVectorStore:
    """Lazy load DuckDB vector store collection."""
    return lazy_loader.load_module(
        f"duckdb_{collection_name}",
        lambda: DuckDBVectorStore(DATABASE_PATH, collection_name, EMBEDDING_MODEL),
    )


# --- Compatibility shims for old API ---
def get_chroma_db():
    """Shim for old ChromaDB getter, returns DuckDB chat collection."""
    return get_duckdb_collection("chat")


def get_classification_db():
    """Shim for classification collection."""
    return get_duckdb_collection("classification")


# --- Other lazy loading functions (unchanged) ---
def get_llm_functions():
    return lazy_loader.load_module("llm_functions", lambda: _init_llm_functions())


def _init_llm_functions():
    from llm import chatModel

    # Return a dictionary of functions instead of the module
    return {
        "get_convo_hist_answer": chatModel.get_convo_hist_answer,
        "is_llm_ready": chatModel.is_llm_ready,
        "initialize_llm_and_db": chatModel.initialize_llm_and_db,
    }


def get_data_processing():
    return lazy_loader.load_module("data_processing", lambda: _init_data_processing())


def _init_data_processing():
    from llm import dataProcessing

    return dataProcessing


def get_classification():
    return lazy_loader.load_module("classification", lambda: _init_classification())


def _init_classification():
    from llm import classificationModel

    return classificationModel
