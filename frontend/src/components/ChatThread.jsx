// Renders the sequence of question/answer turns. Each answer is followed by its
// SourceCard list.

import SourceCard from "./SourceCard.jsx";

export default function ChatThread({ messages = [] }) {
  return (
    <div style={s.thread}>
      {messages.map((m) =>
        m.role === "user" ? (
          <div key={m.id} style={s.userRow}>
            <div style={s.userBubble}>{m.text}</div>
          </div>
        ) : (
          <div key={m.id} style={s.answerBlock}>
            <div
              style={{ ...s.answerCard, ...(m.error ? s.answerError : null) }}
            >
              {m.pending ? (
                <span style={s.pending}>Thinking…</span>
              ) : (
                m.text
              )}
            </div>

            {m.sources && m.sources.length > 0 && (
              <>
                <div style={s.sourcesLabel}>Sources</div>
                <div style={s.sourceList}>
                  {m.sources.map((src, i) => (
                    <SourceCard
                      key={i}
                      filename={src.filename}
                      page={src.page}
                      excerpt={src.excerpt}
                      score={src.score}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        )
      )}
    </div>
  );
}

const s = {
  thread: { display: "flex", flexDirection: "column", gap: 22 },
  userRow: { display: "flex", justifyContent: "flex-end" },
  userBubble: {
    background: "#edefea",
    color: "#2a2a2a",
    borderRadius: 14,
    padding: "12px 16px",
    fontSize: 14,
    maxWidth: "70%",
    lineHeight: 1.5,
  },
  answerBlock: { display: "flex", flexDirection: "column" },
  answerCard: {
    background: "#fff",
    border: "1px solid #ececec",
    borderRadius: 12,
    padding: "18px 20px",
    fontSize: 14,
    lineHeight: 1.6,
    color: "#2a2a2a",
    whiteSpace: "pre-wrap",
  },
  answerError: { borderColor: "#e6bcbc", color: "#b23b3b" },
  pending: { color: "#9a9a92" },
  sourcesLabel: { fontSize: 12, color: "#9a9a92", margin: "14px 0 8px" },
  sourceList: { display: "flex", flexDirection: "column", gap: 10 },
};
