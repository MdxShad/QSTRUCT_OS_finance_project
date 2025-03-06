import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite configuration for the Q‑Struct OS frontend.  The proxy forwards API calls
// beginning with `/api` to the local backend running on port 8000 during
// development.

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
