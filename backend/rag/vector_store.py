import logging
from pathlib import Path
from typing import List, Optional
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.config import settings
from backend.rag.embeddings import get_azure_embeddings

logger = logging.getLogger(__name__)

_cached_vector_store: Optional[Chroma] = None


class VectorStoreNotFoundError(RuntimeError):
    """Raised when the vector store database is not found or has no documents."""
    pass


def get_chroma_client() -> chromadb.PersistentClient:
    """Returns a PersistentClient for ChromaDB pointing to the local directory."""
    persist_dir = str(settings.CHROMA_PERSIST_DIR)
    return chromadb.PersistentClient(path=persist_dir)


def is_vector_store_populated() -> bool:
    """
    Checks if ChromaDB directory exists and contains a populated collection.
    """
    persist_dir = settings.CHROMA_PERSIST_DIR
    if not persist_dir.exists():
        return False

    try:
        client = get_chroma_client()
        collections = client.list_collections()
        # In newer Chroma, list_collections returns collection objects or names
        collection_names = [
            c.name if hasattr(c, "name") else str(c) for c in collections
        ]
        if settings.CHROMA_COLLECTION_NAME not in collection_names:
            return False

        col = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
        return col.count() > 0
    except Exception as e:
        logger.debug(f"Error checking vector store readiness: {e}")
        return False


def get_vector_store(create_if_missing: bool = False) -> Chroma:
    """
    Loads and returns the existing Chroma vector store.
    If create_if_missing is False and no populated vector store exists,
    raises VectorStoreNotFoundError instructing the user to run the ingestion script.
    """
    global _cached_vector_store
    if _cached_vector_store is not None and not create_if_missing:
        return _cached_vector_store

    if not create_if_missing:
        if not is_vector_store_populated():
            raise VectorStoreNotFoundError(
                "Knowledge base vector store not found or is empty in 'chroma_db/'. "
                "Please run 'python scripts/ingest.py' to process and index policy documents."
            )

    embeddings = get_azure_embeddings()
    client = get_chroma_client()

    store = Chroma(
        client=client,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
    )

    if not create_if_missing:
        _cached_vector_store = store

    return store


def build_vector_store(documents: List[Document], batch_size: int = 100) -> Chroma:
    """
    Builds or overwrites the Chroma vector store with the provided documents.
    Used by scripts/ingest.py.
    """
    embeddings = get_azure_embeddings()
    client = get_chroma_client()

    # Clear existing collection if present to avoid duplicate chunks on re-ingestion
    existing_collections = client.list_collections()
    existing_names = [
        c.name if hasattr(c, "name") else str(c) for c in existing_collections
    ]
    if settings.CHROMA_COLLECTION_NAME in existing_names:
        logger.info(f"Removing existing collection '{settings.CHROMA_COLLECTION_NAME}' for fresh ingestion.")
        client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)

    logger.info(f"Creating collection '{settings.CHROMA_COLLECTION_NAME}' in ChromaDB...")
    store = Chroma(
        client=client,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
    )

    # Ingest in batches to handle larger knowledge bases cleanly
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        store.add_documents(documents=batch)

    # Update cache
    global _cached_vector_store
    _cached_vector_store = store

    return store
