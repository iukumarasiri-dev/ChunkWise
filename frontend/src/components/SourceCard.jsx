// Shows one retrieved chunk behind an answer: filename, page number, excerpt,
// and similarity score.

export default function SourceCard({ filename, page, excerpt, score }) {
  return (
    <div style={s.card}>
      <div style={s.head}>
        <span style={s.link}>
          {filename}
          {page != null ? ` · page ${page}` : ""}
        </span>
        {score != null && (
          <span style={s.score}>{Math.round(score * 100)}% match</span>
        )}
      </div>
      {excerpt && <div style={s.excerpt}>&ldquo;{excerpt}&rdquo;</div>}
    </div>
  );
}

const s = {
  card: {
    background: "#f1f1ef",
    borderLeft: "3px solid #3b6cb5",
    borderRadius: "0 8px 8px 0",
    padding: "12px 14px",
  },
  head: {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: 12,
  },
  link: { color: "#2f5fa8", fontSize: 13, fontWeight: 600 },
  score: { color: "#9a9a92", fontSize: 12, flexShrink: 0 },
  excerpt: { color: "#6b6b6b", fontSize: 13, marginTop: 6, lineHeight: 1.5 },
};
