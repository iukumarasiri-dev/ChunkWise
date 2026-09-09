import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api to the FastAPI backend during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
        proxy: {
      "/api": {
        // 127.0.0.1, not "localhost": Node resolves localhost to IPv6 ::1 first,
        // but uvicorn binds IPv4 127.0.0.1 — the mismatch causes intermittent
        // ECONNREFUSED on Windows, especially during --reload restarts.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
