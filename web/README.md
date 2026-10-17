# HeatShield web

Mobile-first React, TypeScript, Tailwind CSS, and MapLibre application for the
Delhi heat-safety pilot. `/app` is the worker experience and `/city` is the
city operations dashboard.

## Run locally

```powershell
cd web
npm install
Copy-Item .env.example .env.local
npm run dev
```

The mock API is opt-in. Set `VITE_USE_MOCK_API=true` in `.env.local` to view
the demo forecast, hotspot data, and intervention plan. Set it to `false` and
configure `VITE_API_BASE_URL` to connect to the API.

## Checks

```powershell
npm run build
npm test
```
