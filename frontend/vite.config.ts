import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Use environment variable for API URL, fallback to localhost for development
  const apiUrl = process.env.VITE_API_BASE_URL || 'http://localhost:8082';
  
  return {
    server: {
      host: "::",
      port: 8080,
      proxy: {
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/images': {
          target: apiUrl,
          changeOrigin: true,
        }
      }
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
