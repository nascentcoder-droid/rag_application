import sys
from pathlib import Path

# Ensure project root is on sys.path so backend modules import cleanly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings, ConfigurationError
from backend.rag.document_loader import load_pdf_file
from backend.rag.vector_store import build_vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter


def run_ingestion() -> None:
    """Orchestrates loading, chunking, embedding, and indexing of company policy PDFs."""
    print("\n=======================================================")
    print("      Company Policy Knowledge Base Ingestion")
    print("=======================================================\n")

    # 1. Validate Embedding Configuration
    try:
        settings.validate_azure_embedding_config()
    except ConfigurationError as config_err:
        print(f"[ERROR] Configuration Error: {config_err}")
        print("Please edit your .env file with valid Azure OpenAI credentials and re-run.\n")
        sys.exit(1)

    kb_dir = settings.KNOWLEDGE_BASE_DIR
    if not kb_dir.exists():
        kb_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created knowledge base directory: {kb_dir}")

    # 2. Discover PDFs
    pdf_files = sorted(list(kb_dir.glob("*.pdf")))
    count = len(pdf_files)
    print(f"Found {count} PDF file{'s' if count != 1 else ''} in '{kb_dir.name}/'")

    if count == 0:
        print("[WARNING] No PDF files found in the knowledge_base/ directory.")
        print("Please place company policy PDF documents in knowledge_base/ and re-run this script.")
        print("Tip: Run 'python scripts/generate_sample_policies.py' to generate realistic sample policies.\n")
        sys.exit(0)

    # 3. Load PDFs
    all_pages = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", "; ", " ", ""],
        length_function=len,
    )

    for pdf_path in pdf_files:
        print(f"Loading: {pdf_path.name}")
        pages = load_pdf_file(pdf_path)
        if not pages:
            print(f"  [Notice] No readable text found in '{pdf_path.name}'. Skipping.")
            continue
        all_pages.extend(pages)

    if not all_pages:
        print("[ERROR] No readable text could be extracted from any PDF files.")
        sys.exit(1)

    # 4. Split into chunks
    chunks = text_splitter.split_documents(all_pages)
    print(f"\nCreated {len(chunks)} document chunks from {len(all_pages)} pages.")

    # 5. Embed and index into ChromaDB
    print("Generating embeddings...")
    print(f"Using Azure OpenAI Embedding Deployment: '{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}'")
    print("Storing vectors...")

    try:
        build_vector_store(documents=chunks)
        print(f"Persisted ChromaDB database under '{settings.CHROMA_PERSIST_DIR.name}/'")
        print("Ingestion completed successfully.\n")
    except Exception as e:
        print(f"[ERROR] Failed to store vectors in ChromaDB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_ingestion()
