import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path"; // Optional: for path aliases

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    // Optional: for cleaner imports like @/components/...
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist", // Output directory for built assets
    assetsDir: "assets", // Subdirectory for assets within outDir
  },
});
