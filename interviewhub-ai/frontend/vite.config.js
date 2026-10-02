import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const apiBaseUrl = loadEnv(mode, process.cwd(), '').VITE_API_BASE_URL || process.env.VITE_API_BASE_URL;
  if (mode === 'production' && apiBaseUrl?.startsWith('http://')) {
    throw new Error('Production VITE_API_BASE_URL must use HTTPS or a same-origin relative path.');
  }
  return { plugins: [react()] };
});
