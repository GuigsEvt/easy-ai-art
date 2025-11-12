import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables from .env files
  const env = loadEnv(mode, process.cwd(), '');
  
  // Use environment variable for API URL, fallback to localhost for development
  const apiUrl = env.VITE_API_BASE_URL || 'http://localhost:8082';
  // Use environment variable for port, fallback to 8080
  // Check VITE_PORT first, then PORT, then default to 8080
  const port = parseInt(env.VITE_PORT || env.PORT || '8080', 10);
  
  return {
    server: {
      host: "::",
      port: port,
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
