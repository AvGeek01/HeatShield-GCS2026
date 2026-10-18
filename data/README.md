# Delhi pilot raw data

`data/raw/` is generated locally and is git-ignored. It is not included in Git.
From the repository root in PowerShell, activate the project environment,
install the geospatial dependencies, and run:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[geospatial,test]"
python .\data\download_pilot.py
python -m heatcore.data.verify
```

Landsat and Sentinel-2 imagery are downloaded from Microsoft Planetary
Computer's public STAC API using short-lived signed asset URLs; no Earth Engine
account, Google Cloud project, project ID, or credentials are needed. The
fallback was selected because Earth Engine initialization with the local
`EE_PROJECT` failed: the Earth Engine API is disabled for that project. The
Planetary Computer STAC collection metadata declares its license as
`proprietary`; the source Landsat and Sentinel datasets have their own
upstream terms. See [R's source and license notes](../docs/R_data_sources.md).

The script stores the Open-Meteo forecast, clipped WorldPop population raster,
OSM GeoJSON, Landsat LST GeoTIFF, Sentinel-2 NDVI GeoTIFF, and provenance
manifest in `data/raw/`. The pilot is a 5,000 m square centered on DTU in UTM
zone 43N. Satellite layers are median composites over the most recent 365 days;
weather is a seven-day hourly forecast at the pilot center. The WorldPop India
raster is downloaded to a temporary directory and clipped before that
temporary source is removed.

The downloader skips output files that already exist and never replaces them.
To refresh a particular layer, first move that specific file out of
`data/raw/`, then rerun the command. The OSMnx query uses public Overpass
infrastructure, so requests may be delayed or rejected during high load; rerun
later if that download fails. Weather and population files are cached before
the OSM query; the three files already cached in the pilot are reused. The
script resumes from existing successful outputs and rewrites the manifest
after a complete run with per-file source, dataset ID, bbox, date range, CRS,
resolution, license, SHA-256, and download time.

The verifier checks all five expected data files, their SHA-256 checksums,
their declared bbox, and coverage of the pilot bbox for each raster. A
successful run prints `PASS`; missing, altered, or out-of-bounds data prints
`FAIL` and exits nonzero.

All raw data stays local. Keep credentials, API keys, and any personal or
interview data out of this repository.
