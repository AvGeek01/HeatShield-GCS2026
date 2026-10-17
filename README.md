
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

### `/heatcore`

### `/web`

### `/firmware`

### `/data`

### `/docs`

<!-- Run commands will be added as each component becomes runnable. -->

