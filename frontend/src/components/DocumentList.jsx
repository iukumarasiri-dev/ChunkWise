// Lists uploaded documents with status (processing / ready / failed) and chunk
// count. Allows deleting a document.

const KIND_BADGE = {
  pdf: { label: "PDF", bg: "#e8effb", fg: "#3b6cb5" },
  docx: { label: "DOC", bg: "#e8effb", fg: "#3b6cb5" },
  doc: { label: "DOC", bg: "#e8effb", fg: "#3b6cb5" },
};

const STATUS = {
  ready: { label: "Ready", bg: "#e5f4e3", fg: "#3a7d34" },
  processing: { label: "Processing", bg: "#fbefd0", fg: "#8a6d1f" },
  failed: { label: "Failed", bg: "#fbe0e0", fg: "#b23b3b" },
};

function kindOf(filename) {
  const ext = filename.slice(filename.lastIndexOf(".") + 1).toLowerCase();
  return (
    KIND_BADGE[ext] || {
      label: (ext || "file").toUpperCase().slice(0, 4),
      bg: "#eee",
      fg: "#666",
    }
  );
}

function formatBytes(n) {
  if (n == null) return "";
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  if (n >= 1024) return `${Math.round(n / 1024)} KB`;
  return `${n} B`;
}

function relTime(iso) {
  if (!iso) return "";
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  const m = Math.round(s / 60);
  if (m < 60) return `${m} min ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h} hour${h === 1 ? "" : "s"} ago`;
  const d = Math.round(h / 24);
  return `${d} day${d === 1 ? "" : "s"} ago`;
}

function metaLine(doc) {
  const parts = [formatBytes(doc.size_bytes)];
  if (doc.status === "ready") {
    if (doc.chunk_count != null) parts.push(`${doc.chunk_count} chunks`);
    parts.push(`uploaded ${relTime(doc.uploaded_at)}`);
  } else if (doc.status === "processing") {
    parts.push("processing…");
  } else if (doc.status === "failed") {
    parts.push(doc.error || "failed to parse");
  }
  return parts.filter(Boolean).join(" · ");
}

function TrashIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

export default function DocumentList({ docs = [], loading = false, onDelete }) {
  if (loading && !docs.length) {
    return <div style={s.empty}>Loading documents…</div>;
  }
  if (!docs.length) {
    return (
      <div style={s.empty}>No documents yet. Upload one above to get started.</div>
    );
  }

  return (
    <div style={s.list}>
      {docs.map((doc) => {
        const badge = kindOf(doc.filename);
        const st = STATUS[doc.status] || STATUS.processing;
        return (
          <div key={doc.id} style={s.row}>
            <div style={{ ...s.badge, background: badge.bg, color: badge.fg }}>
              {badge.label}
            </div>
            <div style={s.info}>
              <div style={s.name} title={doc.filename}>
                {doc.filename}
              </div>
              <div style={s.meta}>{metaLine(doc)}</div>
            </div>
            <div style={{ ...s.pill, background: st.bg, color: st.fg }}>
              {st.label}
            </div>
            <button
              type="button"
              style={s.deleteBtn}
              title="Delete document"
              aria-label={`Delete ${doc.filename}`}
              onClick={() => onDelete?.(doc.id)}
            >
              <TrashIcon />
            </button>
          </div>
        );
      })}
    </div>
  );
}

const s = {
  list: { display: "flex", flexDirection: "column", gap: 12 },
  row: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    background: "#fff",
    border: "1px solid #ececec",
    borderRadius: 12,
    padding: "16px 18px",
  },
  badge: {
    width: 44,
    height: 44,
    borderRadius: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: 0.5,
    flexShrink: 0,
  },
  info: { flex: 1, minWidth: 0 },
  name: {
    fontSize: 15,
    fontWeight: 600,
    color: "#1c1c1c",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  meta: { fontSize: 13, color: "#8a8a82", marginTop: 3 },
  pill: {
    fontSize: 12,
    fontWeight: 600,
    padding: "5px 12px",
    borderRadius: 999,
    whiteSpace: "nowrap",
  },
  deleteBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: 34,
    height: 34,
    borderRadius: 8,
    border: "1px solid #ececec",
    background: "#fff",
    color: "#9a9a92",
    cursor: "pointer",
    flexShrink: 0,
  },
  empty: { color: "#8a8a82", fontSize: 14, padding: "24px 0" },
};