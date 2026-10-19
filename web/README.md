# HeatShield web

Mobile-first React, TypeScript, Tailwind CSS, and MapLibre application for the
Delhi heat-safety pilot. It includes the Risk Card (`/risk`), Heat-Safe Route
(`/route`), Resources Map (`/resources`), City Heatmap (`/city`), Optimizer
(`/optimizer`), and Simulator (`/simulator`).

## Run locally

```powershell
cd web
npm install
Copy-Item .env.example .env.local
npm run dev
```

The mock API is opt-in. Set `VITE_USE_MOCK_API=true` in `.env.local` to view
the demo forecast, hotspot data, and intervention plan. Development mode
defaults to mock data through `.env.development`; set
`VITE_USE_MOCK_API=false` in `.env.local` and configure `VITE_API_BASE_URL` to
connect to the API instead. API requests time out after 15 seconds, and the
city heatmap can be retried independently of the intervention optimizer.
Mock responses are loaded from local JSON fixtures in `src/api/mock-data.json`.
The API client supports `GET /api/risk`, `GET /api/heatmap`, `POST /api/route`,
`GET /api/resources`, `POST /api/optimize`, and `POST /api/simulate`, following
the backend Pydantic request and response models.

Production builds include a web app manifest and a service worker that caches
the application shell and same-origin static assets for offline launch. API
requests are deliberately not cached.

## Checks

```powershell
npm run build
npm test
```
