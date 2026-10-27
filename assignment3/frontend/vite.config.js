import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Port 5174 so this runs side by side with Expedia Lite (5173).
// fs.allow ".." lets the app import ../shared/*.json (skill steps + crisis content).
export default defineConfig({
  plugins: [vue()],
  server: { host: "127.0.0.1", port: 5174, strictPort: true, fs: { allow: [".."] } },
});
