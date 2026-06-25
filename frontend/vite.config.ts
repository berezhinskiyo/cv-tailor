import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    // dev-сервер за nginx получает внешний Host — разрешаем любые хосты,
    // иначе Vite 5.4+ отвечает «Blocked request».
    allowedHosts: true,
  },
});
