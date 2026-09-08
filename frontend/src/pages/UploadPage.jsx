// Upload page: drop a PDF/DOCX, then watch its ingestion status and chunk count
// in the document list.

import { useCallback, useEffect, useRef, useState } from "react";
import DocumentList from "../components/DocumentList.jsx";
import {
  listDocuments,
  uploadDocument,
  deleteDocument,
} from "../api/client.js";

const ACCEPT = ".pdf,.docx";
const ALLOWED_EXT = [".pdf", ".docx"];
const MAX_BYTES = 20 * 1024 * 1024;

export default function UploadPage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listDocuments();
      setDocs(list);
      setError(null);
    } catch (e) {
      setError(e.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while any document is still processing.
  useEffect(() => {
    if (!docs.some((d) => d.status === "processing")) return;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [docs, refresh]);

  const handleFiles = useCallback(
    async (fileList) => {
      const files = Array.from(fileList || []);
      if (!files.length) return;

      setUploading(true);
      setError(null);
      for (const file of files) {
        const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
        if (!ALLOWED_EXT.includes(ext)) {
          setError(`${file.name}: unsupported file type (PDF or DOCX only)`);
          continue;
        }
        if (file.size > MAX_BYTES) {
          setError(`${file.name}: exceeds the 20MB limit`);
          continue;
        }
        try {
          await uploadDocument(file);
        } catch (e) {
          setError(`${file.name}: ${e.message || "upload failed"}`);
        }
      }
      setUploading(false);
      refresh();
    },
    [refresh]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDelete = async (id) => {
    const prev = docs;
    setDocs((d) => d.filter((x) => x.id !== id)); // optimistic
    try {
      await deleteDocument(id);
    } catch (e) {
      setDocs(prev);
      setError(e.message || "Delete failed");
    }
  };

  const openPicker = () => inputRef.current?.click();

  return (
    <div style={S.page}>
      <div style={S.container}>
        <h1 style={S.title}>Documents</h1>
        <p style={S.subtitle}>Upload PDFs or Word docs to query against.</p>

        <div
          style={{ ...S.dropzone, ...(dragging ? S.dropzoneActive : null) }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={openPicker}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPicker();
            }
          }}
          role="button"
          tabIndex={0}
        >
          <div style={S.dropIcon} aria-hidden>
            ↑
          </div>
          <div style={S.dropText}>Drag and drop files here, or click to browse</div>
          <div style={S.dropHint}>PDF, DOCX up to 20MB</div>
          <button
            type="button"
            style={S.chooseBtn}
            disabled={uploading}
            onClick={(e) => {
              e.stopPropagation();
              openPicker();
            }}
          >
            {uploading ? "Uploading…" : "Choose files"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            multiple
            hidden
            onChange={(e) => {
              handleFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        {error && <div style={S.error}>{error}</div>}

        <div style={S.countRow}>
          {loading
            ? "Loading…"
            : `${docs.length} document${docs.length === 1 ? "" : "s"}`}
        </div>

        <DocumentList docs={docs} loading={loading} onDelete={onDelete} />
      </div>
    </div>
  );
}

const S = {
  page: {
    minHeight: "100vh",
    background: "#f5f5f3",
    padding: "40px 24px",
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
  },
  container: { maxWidth: 1100, margin: "0 auto" },
  title: {
    margin: 0,
    fontFamily: "Georgia, 'Times New Roman', serif",
    fontSize: 30,
    fontWeight: 600,
    color: "#1c1c1c",
  },
  subtitle: {
    color: "#6b6b6b",
    fontSize: 15,
    marginTop: 6,
    marginBottom: 28,
  },
  dropzone: {
    border: "1.5px dashed #cfcfc9",
    borderRadius: 14,
    background: "#fafafa",
    padding: "40px 24px",
    textAlign: "center",
    cursor: "pointer",
    transition: "border-color .15s, background .15s",
    outline: "none",
  },
  dropzoneActive: { borderColor: "#9a9a92", background: "#f0f0ec" },
  dropIcon: { fontSize: 22, color: "#8a8a82", marginBottom: 12 },
  dropText: { fontSize: 15, color: "#2a2a2a" },
  dropHint: { fontSize: 13, color: "#9a9a92", marginTop: 6, marginBottom: 16 },
  chooseBtn: {
    background: "#fff",
    border: "1px solid #d9d9d3",
    borderRadius: 8,
    padding: "8px 16px",
    fontSize: 14,
    color: "#2a2a2a",
    cursor: "pointer",
  },
  error: {
    background: "#fbe0e0",
    color: "#b23b3b",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    marginTop: 14,
  },
  countRow: { fontSize: 13, color: "#8a8a82", margin: "26px 0 12px" },
};