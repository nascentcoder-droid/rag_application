# Company Policy Knowledge Base RAG Assistant

A production-grade, modular Retrieval-Augmented Generation (RAG) application enabling employees to query company policies stored as PDF documents through a clean **FastAPI** REST backend and an interactive **Streamlit** chat interface.

Powered by **LangChain**, **Azure OpenAI**, **ChromaDB**, and **PyPDF**.

---

## Architecture Overview

```
 ┌──────────────────────┐
 │  Company Policy PDFs │ (knowledge_base/)
 └──────────┬───────────┘
            │
            ▼ (scripts/ingest.py)
 ┌──────────────────────┐
 │  PyPDF Chunk Loader  │ (chunk_size: 1000, overlap: 150)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │   Azure Embeddings   │ (AzureOpenAIEmbeddings)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │  ChromaDB (Local)    │ (chroma_db/)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐      Question      ┌──────────────────────┐
 │   FastAPI Backend    │ ◄───────────────── │  Streamlit Chat UI   │
 │   (/api/chat)        │ ─────────────────► │  (frontend/app.py)   │
 └──────────┬───────────┘   Answer + Sources └──────────────────────┘
            │
            ▼
 ┌──────────────────────┐
 │ LangChain Retriever  │ (Top-K similarity search)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │   Azure OpenAI LLM   │ (gpt-5.1 / AzureChatOpenAI)
 └──────────────────────┘
```

---

## Features

- **Automated PDF Ingestion**: Dynamically discovers all `.pdf` documents in `knowledge_base/`, extracts text page-by-page, and preserves document name and page numbers in chunk metadata.
- **Persistent Vector Store**: Local vector index managed via ChromaDB (`chroma_db/`), eliminating index recreation on server startup.
- **Production Guardrails & Grounding**: Strict system prompt instructing the model to rely only on policy context, preserve limits/eligibility conditions, and cite exact documents and page numbers.
- **Modular Azure OpenAI Integration**: Decoupled chat model deployment (`AZURE_OPENAI_DEPLOYMENT`) and embedding model deployment (`AZURE_OPENAI_EMBEDDING_DEPLOYMENT`).
- **RESTful FastAPI Service**: Standardized schemas with Pydantic validation, CORS middleware for Streamlit, and explicit error handlers preventing credential leaks.
- **Interactive Streamlit UI**: Chat interface with session history, backend connectivity monitor, sample questions, and collapsible source citations.

---

## 1. Prerequisites

- **Python**: Version `3.11` or higher (tested on Python 3.11 - 3.14).
- **Azure OpenAI Resource**:
  - Chat Model Deployment (e.g., `gpt-5.1` or `gpt-4o`).
  - Embedding Model Deployment (e.g., `text-embedding-3-small` or `text-embedding-ada-002`).
  - API endpoint and secret API key.

---

## 2. Installation & Virtual Environment

Clone the repository and set up the Python virtual environment:

### Windows
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Configuration

1. Copy the sample environment file to create `.env`:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt: `copy .env.example .env`)*

2. Open `.env` and fill in your Azure OpenAI parameters:
   ```env
   # Azure OpenAI Credentials
   AZURE_OPENAI_API_KEY=your-actual-azure-key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   AZURE_OPENAI_DEPLOYMENT=gpt-5.1
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

   # Retrieval Settings
   TOP_K=5

   # Application URL
   BACKEND_URL=http://localhost:8000
   ```

> [!IMPORTANT]
> Never commit `.env` to version control. The repository includes `.gitignore` to prevent accidental credential exposure.

---

## 4. Add Policy Documents

Place your company policy PDF documents inside the `knowledge_base/` directory:

```
knowledge_base/
├── leave_policy.pdf
├── remote_work_policy.pdf
├── travel_policy.pdf
├── expense_policy.pdf
├── security_policy.pdf
└── employee_handbook.pdf
```

### Generating Sample Policies
If you do not have policy PDFs on hand, generate 6 sample corporate policies by running:
```bash
python scripts/generate_sample_policies.py
```

---

## 5. Ingest Documents into Vector Store

Run the ingestion script to parse, chunk, embed, and index documents into ChromaDB:

```bash
python scripts/ingest.py
```

### Expected Output:
```
=======================================================
      Company Policy Knowledge Base Ingestion
=======================================================

Found 6 PDF files in 'knowledge_base/'
Loading: employee_handbook.pdf
Loading: expense_policy.pdf
Loading: leave_policy.pdf
Loading: remote_work_policy.pdf
Loading: security_policy.pdf
Loading: travel_policy.pdf

Created 26 document chunks from 14 pages.
Generating embeddings...
Using Azure OpenAI Embedding Deployment: 'text-embedding-3-small'
Storing vectors...
Persisted ChromaDB database under 'chroma_db/'
Ingestion completed successfully.
```

---

## 6. Start the FastAPI Backend

From the root of the project:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## 7. Start the Streamlit Frontend

In a separate terminal window (with `venv` activated):

```bash
streamlit run frontend/app.py
```

Open your browser at `http://localhost:8501`.

---

## 8. Test the API

### PowerShell Test
```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8000/api/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"question":"How many annual leave days do employees receive?"}'
```

### curl Test
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question":"How many annual leave days do employees receive?"}'
```

### Expected JSON Response:
```json
{
  "answer": "Full-time permanent employees are entitled to 20 business days of paid annual leave per calendar year. Leave accrues monthly at a rate of 1.67 days per completed month of active service.",
  "sources": [
    {
      "document": "leave_policy.pdf",
      "page": 1
    }
  ]
}
```

---

## 9. Quick Launcher for Windows (`run.bat`)

For convenience on Windows, double-click `run.bat` or run:
```cmd
run.bat
```
This script will activate `venv` and prompt you to start either the FastAPI backend, Streamlit frontend, ingestion pipeline, or sample policy generator.

---

## Project Structure

```
rag_application/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application & route definitions
│   ├── config.py                # Pydantic Settings & environment validation
│   ├── models.py                # Request / Response Pydantic models
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_loader.py   # PyPDF extraction & chunking
│   │   ├── embeddings.py        # AzureOpenAIEmbeddings factory
│   │   ├── vector_store.py      # ChromaDB client & persistence
│   │   ├── retriever.py         # VectorStoreRetriever builder
│   │   └── chain.py             # Prompt template & AzureChatOpenAI pipeline
│   │
│   └── services/
│       ├── __init__.py
│       └── chat_service.py      # RAG orchestration service
│
├── frontend/
│   └── app.py                   # Streamlit interactive chat UI
│
├── knowledge_base/              # Directory for raw policy PDFs
│   └── README.md
│
├── chroma_db/                   # Local ChromaDB persistent storage
│
├── scripts/
│   ├── ingest.py                # Knowledge base ingestion CLI
│   └── generate_sample_policies.py # Sample PDF creator
│
├── .env                         # Local secrets (git-ignored)
├── .env.example                 # Example configuration template
├── .gitignore                   # Version control ignore rules
├── requirements.txt             # Production dependency pins
├── README.md                    # System documentation
└── run.bat                      # Windows launcher script
```
