# K Backend

The FastAPI service exposes mock data for the Delhi pilot. All risk, heatmap,
route, resource, optimization, simulation, and reading responses are synthetic;
they are not live forecasts, verified facilities, or medical advice. The API
validates request and response payloads with Pydantic and publishes Swagger UI
at `/docs` and its OpenAPI schema at `/openapi.json`.

## Run locally

From the repository root in PowerShell:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`; Swagger UI is at
`http://127.0.0.1:8000/docs`. Edit `backend/.env` for local settings and never
commit it.

## Run with PostGIS

After copying the example environment file and setting a local
`POSTGRES_PASSWORD`, start the database and API from the repository root:

```powershell
docker compose --env-file backend\.env -f backend\docker-compose.yml up --build
```

The PostGIS database is provisioned for the next persistence step. Current API
endpoints deliberately return deterministic mock data and do not write readings
to the database.

## Tests

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

The heatmap query `bbox` is `min_lon,min_lat,max_lon,max_lat`; optimizer body
`bbox` uses the corresponding four-number array. CORS defaults to the local Vite
origins and can be overridden with `CORS_ORIGINS`.