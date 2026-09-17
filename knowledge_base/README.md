# Company Policy Knowledge Base

Place your company policy PDF documents in this directory.

## Structure Example
```
knowledge_base/
├── leave_policy.pdf
├── remote_work_policy.pdf
├── travel_policy.pdf
├── expense_policy.pdf
├── security_policy.pdf
└── employee_handbook.pdf
```

## How It Works
- The ingestion script automatically scans this folder for any files ending in `.pdf`.
- Text is extracted page-by-page using PyPDF and split into chunks preserving metadata (document title, source filename, and page number).
- Embeddings are generated using Azure OpenAI and stored locally in `chroma_db/`.

## Adding or Updating Policies
1. Drop your new or updated PDF files into this directory.
2. Run the ingestion command from the project root:
   ```bash
   python scripts/ingest.py
   ```
3. The vector database in `chroma_db/` will be updated with the new policy chunks.
