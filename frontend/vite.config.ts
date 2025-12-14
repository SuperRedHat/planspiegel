import { defineConfig } from "vite";
import * as path from "node:path";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  server: {
    port: 3000,
  },
  resolve: {
    alias: [
      { find: "@app/", replacement: path.resolve(process.cwd(), "./src") },
      {
        find: "@utils/",
        replacement: path.resolve(process.cwd(), "./src/utils"),
      },
      {
        find: "@components/",
        replacement: path.resolve(process.cwd(), "./src/components"),
      },
      {
        find: "@pages/",
        replacement: path.resolve(process.cwd(), "./src/pages"),
      },
      {
        find: "@assets/",
        replacement: path.resolve(process.cwd(), "./src/assets"),
      },
      {
        find: "@interfaces/",
        replacement: path.resolve(process.cwd(), "./src/interfaces"),
      },
    ],
  },
});
