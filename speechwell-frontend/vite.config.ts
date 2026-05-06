/*
File Logic Summary: TypeScript module for frontend runtime logic, routing, API integration, or UI behavior.
*/

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  server: {
    allowedHosts: ["strip-stamps-proceeding-regions.trycloudflare.com"],
  },
})

