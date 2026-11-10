import { defineConfig } from 'vite'
import { heyApiPlugin } from '@hey-api/vite-plugin';
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    heyApiPlugin({
      config: {
        input: 'http://localhost:9000/openapi.json',
        output: 'src/api',
        plugins: [
          {
            name: '@hey-api/client-fetch',
            runtimeConfigPath: './src/hey-api.runtime.ts',
          },
          '@hey-api/schemas',
          {
            enums: 'javascript',
            name: '@hey-api/typescript',
          },
          '@tanstack/react-query',
          'zod'
        ]
      },
    }),
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:9000',
      }
    }
  }
})
