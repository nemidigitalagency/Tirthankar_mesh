import { defineConfig } from 'vite';

export default defineConfig({
  // Relative asset paths make the app work at both localhost:4173 and
  // https://USERNAME.github.io/REPOSITORY_NAME/.
  base: './',
  server: {
    host: '0.0.0.0',
    allowedHosts: true,
  },
});
