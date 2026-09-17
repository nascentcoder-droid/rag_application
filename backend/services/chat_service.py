import logging
from typing import Optional
from openai import APIError, AuthenticationError, RateLimitError

from backend.config import settings, ConfigurationError
from backend.models import ChatRequest, ChatResponse, SourceItem
from backend.rag.chain import (
    build_rag_prompt,
    extract_deduplicated_sources,
    format_context_documents,
    get_azure_chat_llm,
)
from backend.rag.retriever import get_retriever
from backend.rag.vector_store import VectorStoreNotFoundError

logger = logging.getLogger(__name__)


class ChatServiceError(Exception):
    """General domain error for ChatService operations."""
    pass


class ChatService:
    """Service handling retrieval and grounded response generation."""

    def __init__(self, top_k: Optional[int] = None):
        self.top_k = top_k or settings.TOP_K

    def answer_question(self, request: ChatRequest) -> ChatResponse:
        """
        Executes the RAG pipeline for a given user question:
        1. Validates configuration and loads the vector store retriever
        2. Retrieves the top_k relevant policy chunks
        3. Formats the context and queries Azure OpenAI
        4. Returns the grounded answer with deduplicated sources
        """
        question = request.question.strip()
        logger.info(f"Processing question: '{question[:80]}...'")

        # 1. Retrieve relevant policy chunks
        try:
            retriever = get_retriever(top_k=self.top_k)
            retrieved_docs = retriever.invoke(question)
        except (ConfigurationError, VectorStoreNotFoundError):
            raise
        except (AuthenticationError, APIError) as api_err:
            logger.error(f"Azure OpenAI embedding error during retrieval: {api_err}")
            raise ChatServiceError(f"Azure OpenAI embedding error during retrieval: {str(api_err)}")
        except Exception as e:
            logger.error(f"Vector store retrieval failed: {e}")
            raise ChatServiceError(f"Failed to retrieve policy documents: {str(e)}")

        if not retrieved_docs:
            logger.warning("No documents retrieved for question.")
            return ChatResponse(
                answer="I could not find information regarding that in the company policy knowledge base.",
                sources=[],
            )

        # 2. Extract sources and format context
        sources = extract_deduplicated_sources(retrieved_docs)
        formatted_context = format_context_documents(retrieved_docs)

        # 3. Query Azure OpenAI
        try:
            llm = get_azure_chat_llm()
            prompt = build_rag_prompt()
            messages = prompt.format_messages(
                context=formatted_context,
                question=question,
            )
            response = llm.invoke(messages)
            answer = response.content if hasattr(response, "content") else str(response)

            # Ensure answer is a string
            if isinstance(answer, list):
                answer = "".join(str(part) for part in answer)

            return ChatResponse(answer=answer.strip(), sources=sources)

        except (ConfigurationError, VectorStoreNotFoundError):
            raise
        except AuthenticationError as auth_err:
            logger.error("Azure OpenAI authentication failed. Check API key and endpoint.")
            raise ChatServiceError(
                "Authentication failed with Azure OpenAI. Please verify AZURE_OPENAI_API_KEY."
            )
        except RateLimitError as rate_err:
            logger.error(f"Azure OpenAI rate limit hit: {rate_err}")
            raise ChatServiceError(
                "Azure OpenAI rate limit exceeded. Please try again shortly."
            )
        except APIError as api_err:
            logger.error(f"Azure OpenAI API error: {api_err}")
            raise ChatServiceError(
                f"Azure OpenAI service error: {api_err.message if hasattr(api_err, 'message') else 'Request failed'}"
            )
        except Exception as gen_err:
            logger.error(f"Unexpected error during LLM generation: {gen_err}", exc_info=True)
            raise ChatServiceError(
                "An unexpected error occurred while generating the policy answer. Please contact support."
            )
