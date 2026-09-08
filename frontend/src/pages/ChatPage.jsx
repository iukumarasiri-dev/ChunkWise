// Chat page: ask a question (optionally scoped to one document) and see the
// grounded answer with its source chunks.

import { useEffect, useMemo, useRef, useState } from "react";
import ChatThread from "../components/ChatThread.jsx";
import { listDocuments, query } from "../api/client.js";

let nextId = 1;
const uid = () => String(nextId++);

export default function ChatPage() {
  const [docs, setDocs] = useState([]);
  const [scope, setScope] = useState(""); // "" = all documents
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const threadEndRef = useRef(null);

  useEffect(() => {
    listDocuments()
      .then((list) => setDocs(list.filter((d) => d.status === "ready")))
      .catch(() => setDocs([]));
  }, []);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const canSend = input.trim().length > 0 && !sending;

  const scopeLabel = useMemo(() => {
    if (!scope) return "All documents";
    return docs.find((d) => d.id === scope)?.filename || "All documents";
  }, [scope, docs]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!canSend) return;

    const question = input.trim();
    const userMsg = { id: uid(), role: "user", text: question };
    const pendingMsg = { id: uid(), role: "assistant", text: "", pending: true };
    setMessages((m) => [...m, userMsg, pendingMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await query(question, scope || null);
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingMsg.id
            ? {
                ...msg,
                pending: false,
                text: res.answer,
                sources: res.sources || [],
              }
            : msg
        )
      );
    } catch (err) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingMsg.id
            ? {
                ...msg,
                pending: false,
                error: true,
                text: err.message || "Something went wrong. Try again.",
              }
            : msg
        )
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={S.page}>
      <div style={S.container}>
        <h1 style={S.title}>Ask your documents</h1>

        <div style={S.scopeRow}>
          <span style={S.scopeLabel}>Scope</span>
          <select
            style={S.select}
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            aria-label="Document scope"
          >
            <option value="">All documents</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>

        <div style={S.threadArea}>
          {messages.length === 0 ? (
            <div style={S.empty}>
              Ask a question about {scopeLabel.toLowerCase()} to get a grounded
              answer with sources.
            </div>
          ) : (
            <ChatThread messages={messages} />
          )}
          <div ref={threadEndRef} />
        </div>

        <form style={S.inputBar} onSubmit={onSubmit}>
          <input
            style={S.input}
            placeholder="Ask a question about your documents"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button
            type="submit"
            style={{ ...S.sendBtn, opacity: canSend ? 1 : 0.5 }}
            disabled={!canSend}
            aria-label="Send question"
          >
            →
          </button>
        </form>
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
  container: {
    maxWidth: 1100,
    margin: "0 auto",
    display: "flex",
    flexDirection: "column",
    minHeight: "calc(100vh - 80px)",
  },
  title: {
    margin: 0,
    fontFamily: "Georgia, 'Times New Roman', serif",
    fontSize: 28,
    fontWeight: 600,
    color: "#1c1c1c",
  },
  scopeRow: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    margin: "22px 0 8px",
  },
  scopeLabel: { fontSize: 13, color: "#8a8a82" },
  select: {
    appearance: "auto",
    background: "#fff",
    border: "1px solid #d9d9d3",
    borderRadius: 10,
    padding: "8px 12px",
    fontSize: 14,
    color: "#2a2a2a",
    minWidth: 200,
  },
  threadArea: {
    flex: 1,
    overflowY: "auto",
    padding: "24px 0",
  },
  empty: {
    color: "#9a9a92",
    fontSize: 14,
    padding: "40px 0",
  },
  inputBar: {
    display: "flex",
    gap: 10,
    borderTop: "1px solid #ececec",
    paddingTop: 20,
    marginTop: 12,
  },
  input: {
    flex: 1,
    padding: "12px 14px",
    borderRadius: 10,
    border: "1px solid #d9d9d3",
    fontSize: 14,
    color: "#2a2a2a",
    outline: "none",
    background: "#fff",
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 10,
    background: "#1c1c1c",
    color: "#fff",
    border: "none",
    fontSize: 18,
    cursor: "pointer",
    flexShrink: 0,
  },
};
