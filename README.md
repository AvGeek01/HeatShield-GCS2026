
# HeatShield

HeatShield is a heat-risk platform for Indian cities, piloting in Delhi around
the DTU/Rohini area. It turns weather forecasts into personal actions and
provides cities with hotspot maps and intervention planning.

## `heatcore` package

The `heatcore` package defines typed interfaces for the pilot's core
calculations. Its functions are scaffolding and currently raise
`NotImplementedError`; algorithms and forecast/model integrations are not yet
implemented.

- `heatcore.features.build_feature_vector` prepares features from a location,
	activity, duration, user profile, and forecast.
- `heatcore.wbgt.calculate_wbgt` accepts air temperature, relative humidity,
	wind speed, and solar radiation and returns WBGT in °C.
- `heatcore.model.predict_risk` defines the model boundary for a 0–100 score.
- `heatcore.risk.assess_risk` describes the response for
	`GET /api/risk?lat&lon&activity&duration_min&profile`:
	`{risk_score, level, wbgt_c, factors, actions}`.
- `heatcore.routing.find_heat_aware_route` defines a route lookup that can
	account for hotspot cells.
- `heatcore.optimizer.optimize_interventions` defines budget-constrained
	selection using heatmap cells.

`GET /api/heatmap?bbox&ts` is expected to return GeoJSON cells with
`risk`, `temp_c`, `wbgt_c`, and `population_exposed` properties.

## Folder ownership

| Owner | Folders |
| --- | --- |
| R | `/heatcore`, `/data` |
| S | `/web` |
| K | `/backend`, `/firmware`, `/docs` |

## How to run

### `/backend`

Run the backend setup from the repository root. Run backend\scripts\setup_backend.ps1; it creates backend\.env for you.

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\setup_backend.ps1
```

The setup creates the repository-root `.venv`, installs the backend dependencies, creates a local development password in `backend\.env` (which is git-ignored), and verifies the database migrations and tests. To skip Docker/PostGIS checks, add `-SkipDocker`.

To run the API locally after setup, activate the virtual environment from the repository root, then start Uvicorn from `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

To check the API endpoints, run this from the repository root in another PowerShell window:

```powershell
powershell -ExecutionPolicy Bypass -File backend\scripts\check_api.ps1
```

### `/heatcore`

Create and activate the Python 3.13 virtual environment, then install the
package and its test dependency:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "heatcore[test]"
python -m pytest
```

Install optional dependencies for the model, geospatial, and optimization
workflows as needed:

```powershell
python -m pip install -e "heatcore[ml,geospatial,optimization]"
```

### `/web`

### `/firmware`

### `/data`

### `/docs`
