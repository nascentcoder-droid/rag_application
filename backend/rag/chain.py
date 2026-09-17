import logging
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from backend.config import settings
from backend.models import SourceItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional, helpful company policy assistant.

Answer the user's question using ONLY the information contained in the provided policy context below.
Follow these strict rules:
1. Do not invent, assume, extrapolate, or fabricate company policies.
2. If the answer cannot be found in the provided context, clearly and politely state:
   "I could not find information regarding that in the company policy knowledge base."
3. If the policy specifies conditions, exceptions, eligibility requirements, numerical limits, waiting periods, or mandatory approvals, preserve and state those details accurately.
4. When possible, cite the source document and page number where the relevant rule is located.
5. Clearly distinguish between what is explicitly stated in the policies and what is not mentioned.

Context:
{context}"""

USER_PROMPT = """Question:
{question}"""


def get_azure_chat_llm() -> AzureChatOpenAI:
    """
    Instantiates and returns the AzureChatOpenAI model client
    using verified Azure OpenAI credentials from settings.
    """
    settings.validate_azure_chat_config()

    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
        max_tokens=4096,
        temperature=0.0,
    )


def format_context_documents(docs: List[Document]) -> str:
    """
    Formats retrieved document chunks into a structured context string
    with clearly identifiable document titles, filenames, and page numbers.
    """
    if not docs:
        return "No relevant policy documents were retrieved."

    formatted_pieces = []
    for idx, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "Unknown Document")
        page = doc.metadata.get("page", "N/A")
        formatted_pieces.append(
            f"--- Policy Excerpt {idx} [Document: {source} | Page: {page}] ---\n"
            f"{doc.page_content.strip()}"
        )

    return "\n\n".join(formatted_pieces)


def extract_deduplicated_sources(docs: List[Document]) -> List[SourceItem]:
    """
    Extracts and deduplicates source references from retrieved chunks,
    preserving document name and page number.
    """
    seen = set()
    sources: List[SourceItem] = []

    for doc in docs:
        source_name = doc.metadata.get("source", "Unknown Document")
        try:
            page_num = int(doc.metadata.get("page", 1))
        except (ValueError, TypeError):
            page_num = 1

        key = (source_name, page_num)
        if key not in seen:
            seen.add(key)
            sources.append(SourceItem(document=source_name, page=page_num))

    return sources


def build_rag_prompt() -> ChatPromptTemplate:
    """Creates the standard ChatPromptTemplate for policy answering."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    )
