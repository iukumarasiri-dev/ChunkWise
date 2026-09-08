// Top-level app shell + routing between the Upload and Chat pages.

import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";

const linkStyle = ({ isActive }) => ({
  fontSize: 14,
  textDecoration: "none",
  color: isActive ? "#1c1c1c" : "#8a8a82",
  fontWeight: isActive ? 600 : 500,
});

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f3" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24,
          padding: "14px 24px",
          borderBottom: "1px solid #ececec",
          background: "#fff",
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        }}
      >
        <div
          style={{
            fontFamily: "Georgia, 'Times New Roman', serif",
            fontSize: 18,
            fontWeight: 600,
            color: "#1c1c1c",
          }}
        >
          ChunkWise
        </div>
        <nav style={{ display: "flex", gap: 18 }}>
          <NavLink to="/documents" style={linkStyle}>
            Documents
          </NavLink>
          <NavLink to="/chat" style={linkStyle}>
            Chat
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Navigate to="/documents" replace />} />
        <Route path="/documents" element={<UploadPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </div>
  );
}
