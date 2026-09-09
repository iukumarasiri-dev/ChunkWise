# ChunkWise

A full-stack Retrieval-Augmented Generation (RAG) application that lets you upload
documents and ask questions grounded in their actual content. Every answer is
traceable back to the chunk it was generated from — filename, page number, and
excerpt included.

## Why this project

Most "chat with your docs" demos skip the part that actually makes RAG useful:
proving where an answer came from. ChunkWise is built around that — every response
is traceable back to the chunk it was generated from, so you can verify it instead
of trusting it blindly.

## Features

- **Document ingestion** — upload PDF or DOCX files, parsed and split into chunks automatically
- **Semantic search** — chunks are embedded and stored in a vector database for similarity-based retrieval
- **Grounded answers** — queries retrieve relevant chunks and generate answers using only that context
- **Source attribution** — every answer shows the document, page number, and exact excerpt it was drawn from
- **Document management** — track upload status (processing / ready / failed) and chunk counts per document
- **Scoped queries** — ask questions across all documents or narrow to a single one

## Tech stack

**Backend**

- FastAPI (async Python API)
- ChromaDB (vector store)
- sentence-transformers (embeddings)
- pdfplumber / python-docx (document parsing)
- SQLite (document metadata and status tracking)
- Ollama (answer generation — local or cloud), behind a pluggable provider interface

**Frontend**

- React + Vite
- Fetch-based API client

## Project structure

```
ChunkWise/
├── backend/
│   ├── app/
│   │   ├── api/       # upload, list, delete, query endpoints
│   │   ├── core/      # parsing, chunking, embedding, retrieval, RAG pipeline
│   │   ├── models/    # request/response schemas
│   │   └── db/        # document metadata storage
│   └── storage/       # uploaded files + vector DB persistence
└── frontend/
    └── src/
        ├── pages/       # Upload page, Chat/Query page
        ├── components/  # document list, chat thread, source cards
        └── api/         # backend client
```

## How it works

1. **Upload** — a document is parsed, split into overlapping text chunks, embedded, and stored in the vector database along with metadata (source file, page number).
2. **Query** — a question is embedded and used to retrieve the most relevant chunks via similarity search.
3. **Generate** — the retrieved chunks are passed to an LLM as context, which generates an answer grounded in that content.
4. **Cite** — the retrieved chunks are returned alongside the answer, so the UI can show exactly which passages support it.

## Getting started

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

The first document upload downloads the embedding model (~80 MB, one time).

Out of the box `LLM_PROVIDER=stub` in `.env` — answers just echo the top
retrieved passage, so the app runs with no LLM setup. For real synthesized
answers, configure Ollama (step 2).

### 2. LLM (optional — for synthesized answers)

Answer generation runs through [Ollama](https://ollama.com), either a local
server or Ollama Cloud.

**Local** — install Ollama from <https://ollama.com/download>, then:

```bash
ollama pull llama3.2:3b
```

and in `backend/.env`:

```
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
OLLAMA_HOST=http://localhost:11434
OLLAMA_API_KEY=
```

**Ollama Cloud** — no local model; create a key at
<https://ollama.com/settings/keys>, then in `backend/.env`:

```
LLM_PROVIDER=ollama
LLM_MODEL=gpt-oss:20b
OLLAMA_HOST=https://ollama.com
OLLAMA_API_KEY=your-key
```

Restart `uvicorn` after editing `.env`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The API will be available at http://localhost:8000 (interactive docs at `/docs`),
and the frontend at http://localhost:5173.

## Roadmap

- [ ] Hybrid search (vector + keyword/BM25) for better retrieval on exact terms
- [ ] Re-ranking retrieved chunks with a cross-encoder
- [ ] Retrieval evaluation harness
- [ ] Docker Compose setup for one-command startup
