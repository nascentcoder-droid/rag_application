import logging
from pathlib import Path
from typing import List, Tuple
import pypdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings

logger = logging.getLogger(__name__)


def load_pdf_file(pdf_path: Path) -> List[Document]:
    """
    Loads and extracts text page-by-page from a single PDF file using PyPDF.
    Handles empty pages and catches corruption errors gracefully.
    """
    documents: List[Document] = []
    file_name = pdf_path.name
    doc_title = pdf_path.stem.replace("_", " ").title()

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        num_pages = len(reader.pages)

        if num_pages == 0:
            logger.warning(f"Skipping '{file_name}': PDF contains 0 pages.")
            return []

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
                trimmed = page_text.strip()
                if trimmed:
                    documents.append(
                        Document(
                            page_content=trimmed,
                            metadata={
                                "source": file_name,
                                "document": doc_title,
                                "page": page_idx,
                                "total_pages": num_pages,
                            },
                        )
                    )
                else:
                    logger.debug(f"Page {page_idx} of '{file_name}' has no extractable text.")
            except Exception as page_err:
                logger.warning(
                    f"Error extracting text from page {page_idx} of '{file_name}': {page_err}"
                )

        if not documents:
            logger.warning(f"No extractable text found in '{file_name}'.")

    except Exception as e:
        logger.error(f"Failed to read PDF '{file_name}': {e}", exc_info=False)
        return []

    return documents


def load_and_chunk_knowledge_base(
    kb_dir: Path | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> Tuple[List[Path], List[Document]]:
    """
    Discovers all PDF files in knowledge_base/, loads their content,
    and splits them into semantically meaningful chunks while preserving metadata.

    Returns:
        Tuple of (list of discovered pdf paths, list of chunked Document objects)
    """
    directory = kb_dir or settings.KNOWLEDGE_BASE_DIR
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created knowledge base directory at: {directory}")

    pdf_files = sorted(list(directory.glob("*.pdf")))
    if not pdf_files:
        return [], []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", " ", ""],
        length_function=len,
    )

    all_chunks: List[Document] = []

    for pdf_path in pdf_files:
        doc_pages = load_pdf_file(pdf_path)
        if not doc_pages:
            continue

        file_chunks = text_splitter.split_documents(doc_pages)
        all_chunks.extend(file_chunks)

    return pdf_files, all_chunks
