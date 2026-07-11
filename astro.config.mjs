import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import vue from '@astrojs/vue';

export default defineConfig({
  site: 'https://hutba.islam.click',
  trailingSlash: 'never',
  build: {
    format: 'file',
  },
  integrations: [vue()],
  vite: {
    plugins: [tailwindcss()],
  },
});
