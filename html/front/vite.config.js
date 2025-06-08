import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  base: './', // 使用相对路径
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: '../',
    assetsDir: 'js',
    sourcemap: true,
    rollupOptions: {
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(css)$/.test(assetInfo.name)) {
            return `css/[name]-[hash].css`;
          }
          return `assets/[name]-[hash].${ext}`;
        },
      },
    },
    emptyOutDir: false,
  },
});
