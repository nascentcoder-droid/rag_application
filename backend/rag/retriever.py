from typing import Optional
from langchain_core.vectorstores import VectorStoreRetriever

from backend.config import settings
from backend.rag.vector_store import get_vector_store


def get_retriever(top_k: Optional[int] = None) -> VectorStoreRetriever:
    """
    Returns a VectorStoreRetriever configured for similarity search
    with the specified or default top_k chunks.
    """
    k = top_k if top_k is not None else settings.TOP_K
    store = get_vector_store(create_if_missing=False)
    return store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )
