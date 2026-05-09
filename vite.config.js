import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'style.css') {
            return 'assets/static/style.css';
          }
          return 'assets/static/[name].[hash][extname]';
        },
      },
    },
  },
});
