import { defineConfig } from 'vite';

// Bundled assets must resolve relative to index.html in the desktop package.
export default defineConfig({ base: './' });
