import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? "/resepifesbuk/" : "/",
  plugins: [react(), tailwindcss()],
  server: { host: "0.0.0.0", port: 5174 },
});
