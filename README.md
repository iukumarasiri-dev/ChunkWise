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

### 4. Docker (alternative to steps 1–3)

```bash
cp backend/.env.example backend/.env   # optional — only needed to customize settings or enable Ollama
docker compose up --build
```

The frontend will be available at http://localhost:3000 (nginx proxies `/api` to
the backend), and the backend directly at http://localhost:8000. Uploaded
documents, the vector DB, and the SQLite metadata all persist in a named volume
across restarts. `backend/.env` is optional — the app runs with built-in
defaults (`LLM_PROVIDER=stub`) if it's absent; copy it only to point at Ollama
or change other settings.

## Exposing beyond localhost

Every endpoint except `/health` is unauthenticated by default — fine for
local use, not fine once the app is reachable from outside your machine
(e.g. via a Cloudflare Tunnel, ngrok, or a public deploy). Before doing
that, set `API_KEY` in `backend/.env`:

```
API_KEY=<generate one>
```

Generate a value with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Restart the backend (or `docker compose up --build -d`) after setting it.
Once set, the frontend will prompt once for the key on first use and
remember it in the browser (`localStorage`); the API rejects any request
without a matching `X-API-Key` header. Leaving `API_KEY` blank keeps auth
disabled, which the server logs a warning about on startup.

## CI/CD

GitHub Actions runs on every push and pull request to `main` ([.github/workflows/ci.yml](.github/workflows/ci.yml)):

1. **backend-tests** — installs `backend/requirements-dev.txt` and runs `pytest`.
2. **frontend-build** — installs frontend deps with `npm ci` and runs `npm run build`.
3. **deploy** — runs only after both jobs above pass, and only on a direct push to `main` (not on pull requests). Executes on a **self-hosted runner**: checks out the code and runs `docker compose up -d --build` to rebuild and restart the app in place.

Requirements for the self-hosted runner:

- Docker (with the Compose plugin) installed and the runner user able to run it.
- `backend/.env` already present on the runner — it's git-ignored and not checked out by CI, so it must be created/maintained directly on the deploy host (see [Getting started](#3-frontend) above for its contents).

To add automated tests as a merge gate, keep pushing to feature branches and opening PRs into `main` — the `backend-tests` and `frontend-build` jobs run on PRs too, `deploy` does not.

## Roadmap

- [ ] Hybrid search (vector + keyword/BM25) for better retrieval on exact terms
- [x] Re-ranking retrieved chunks with a cross-encoder
- [ ] Retrieval evaluation harness
- [x] Docker Compose setup for one-command startup
- [x] CI/CD pipeline (GitHub Actions: test, build, self-hosted deploy)
