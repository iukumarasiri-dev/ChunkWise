// Fetch-based backend client. All calls go through the Vite /api proxy.
//
//   uploadDocument(file)        -> POST   /api/documents  (multipart)
//   listDocuments()             -> GET    /api/documents
//   deleteDocument(id)          -> DELETE /api/documents/:id
//   query(question, documentId) -> POST   /api/query

export const API_BASE = "/api";

// Flip to false once the FastAPI backend is running.
const USE_MOCK = false;

// --- API key -----------------------------------------------------------
// Sent as X-API-Key on every request. Only needed if the backend has
// API_KEY set (required once the app is exposed beyond localhost). Stored
// so the user only has to enter it once per browser.
const API_KEY_STORAGE_KEY = "chunkwise_api_key";

function getApiKey() {
  try {
    return localStorage.getItem(API_KEY_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

function setApiKey(key) {
  try {
    if (key) localStorage.setItem(API_KEY_STORAGE_KEY, key);
    else localStorage.removeItem(API_KEY_STORAGE_KEY);
  } catch {
    /* private browsing / storage disabled - key just won't persist */
  }
}

function authHeaders() {
  const key = getApiKey();
  return key ? { "X-API-Key": key } : {};
}

// Fetch wrapper that attaches the stored API key and, on a 401 (missing or
// wrong key), prompts for one and retries once.
async function authorizedFetch(url, options = {}) {
  const withAuth = (opts) => ({
    ...opts,
    headers: { ...(opts.headers || {}), ...authHeaders() },
  });

  let res = await fetch(url, withAuth(options));
  if (res.status === 401) {
    const entered = window.prompt(
      "This ChunkWise server requires an API key.\nEnter it:"
    );
    if (entered && entered.trim()) {
      setApiKey(entered.trim());
      res = await fetch(url, withAuth(options));
    }
  }
  return res;
}

// --- mock data (mirrors the design mockup) --------------------------------
const daysAgo = (n) => new Date(Date.now() - n * 86_400_000).toISOString();

let mockDocs = [
  {
    id: "1",
    filename: "annual_report_2025.pdf",
    status: "ready",
    size_bytes: 4_200_000,
    chunk_count: 38,
    uploaded_at: daysAgo(2),
    error: null,
  },
  {
    id: "2",
    filename: "product_spec_v3.docx",
    status: "processing",
    size_bytes: 1_100_000,
    chunk_count: null,
    uploaded_at: daysAgo(0),
    error: null,
  },
  {
    id: "3",
    filename: "research_paper.pdf",
    status: "failed",
    size_bytes: 890_000,
    chunk_count: null,
    uploaded_at: daysAgo(0),
    error: "failed to parse",
  },
];

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function listDocuments() {
  if (USE_MOCK) {
    await delay(250);
    return mockDocs.map((d) => ({ ...d }));
  }
  return handle(await authorizedFetch(`${API_BASE}/documents`));
}

export async function uploadDocument(file) {
  if (USE_MOCK) {
    await delay(500);
    const doc = {
      id: String(Date.now() + Math.random()),
      filename: file.name,
      status: "processing",
      size_bytes: file.size,
      chunk_count: null,
      uploaded_at: new Date().toISOString(),
      error: null,
    };
    mockDocs = [doc, ...mockDocs];
    // simulate ingestion finishing a few seconds later
    setTimeout(() => {
      const d = mockDocs.find((x) => x.id === doc.id);
      if (d) {
        d.status = "ready";
        d.chunk_count = Math.floor(Math.random() * 40) + 5;
      }
    }, 4000);
    return { ...doc };
  }
  const form = new FormData();
  form.append("file", file);
  return handle(
    await authorizedFetch(`${API_BASE}/documents`, { method: "POST", body: form })
  );
}

export async function deleteDocument(id) {
  if (USE_MOCK) {
    await delay(150);
    mockDocs = mockDocs.filter((d) => d.id !== id);
    return { ok: true };
  }
  const res = await authorizedFetch(`${API_BASE}/documents/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Delete failed");
  return { ok: true };
}

export async function query(question, documentId) {
  if (USE_MOCK) {
    await delay(400);
    return {
      answer: "Mock answer. Turn USE_MOCK off and run the backend for real responses.",
      sources: [],
    };
  }
  return handle(
    await authorizedFetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, document_id: documentId ?? null }),
    })
  );
}