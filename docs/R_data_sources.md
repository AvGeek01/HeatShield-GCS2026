# R - Delhi pilot data sources and Earth Engine fallback

Checked on **19 October 2026**. The cached 5 km DTU/Rohini pilot bbox is
projected in UTM zone 43N and written in WGS84 order as west, south, east,
north in `data/raw/manifest.json`.

## Satellite fallback decision

Earth Engine was tested with the local `EE_PROJECT` setting using
`ee.Initialize(project=...)`. Initialization returned HTTP 403
`SERVICE_DISABLED`: the Earth Engine API is disabled for that project. Thus
the Earth Engine route could not be used in this environment. Rather than
guess about project eligibility, the downloader now uses the public Microsoft
Planetary Computer STAC API. The Landsat and Sentinel STAC searches for the
pilot bbox and 365-day interval returned matching scenes, and signed COG
assets for the required bands opened successfully without Earth Engine
credentials or a Google Cloud project.

Planetary Computer exposes:

- **Landsat Collection 2 Level-2:** collection `landsat-c2-l2`; `lwir11`
  surface-temperature and `qa_pixel` assets; COGs are 30 m pixels in this
  product (thermal sensor native resolution is 100 m). `lwir11` values are
  converted to Celsius using the USGS scale and offset. Fill, dilated cloud,
  cirrus, cloud, cloud-shadow, and snow QA bits are masked before calculating
  the annual median.
- **Sentinel-2 Level-2A:** collection `sentinel-2-l2a`; `B04` red and `B08`
  near-infrared bands at 10 m, and `SCL` scene classification at 20 m. The
  scene-classification band is resampled with nearest-neighbor to mask cloud,
  cloud-shadow, cirrus, and snow classes before computing NDVI and its annual
  median.
- The date window is the most recent 365 days at download time. The manifest
  records the query window, actual first/last scene dates, and scene IDs.

The public STAC search and COG download were tested; each collection returned
scenes intersecting this bbox, and the requested bands opened with CRS
`EPSG:32643` at the expected pixel sizes. The required three existing inputs
(Open-Meteo, WorldPop, and OSM) are used as-is by the downloader; existing
data files are skipped rather than overwritten.

### Licences and attribution

The Planetary Computer STAC collection metadata currently reports
`"license": "proprietary"` for both hosted collections. This is the catalogue
metadata value; it is not itself evidence that the upstream source data are
closed or that any separate Planetary Computer service rights can be
redistributed. The source providers state:

- USGS Landsat data are freely available and are generally U.S. government
  public-domain data. Acknowledge USGS and NASA. Review the specific product
  and service terms before redistributing Planetary Computer-hosted assets.
- Copernicus Sentinel data are available on a free, full, and open basis under
  the Copernicus Sentinel Data Legal Notice. Credit Copernicus Sentinel data
  and follow that notice. Review the hosting service terms separately.

The manifest records the upstream data source/licence and the STAC collection
IDs used to find the files. Do not treat the STAC service or its signed access
URLs as a permanent download API or as a licence grant.

### Verified access and documentation

- [Planetary Computer STAC API](https://planetarycomputer.microsoft.com/api/stac/v1)
- [Landsat C2 L2 collection metadata](https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2)
- [Sentinel-2 L2A collection metadata](https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a)
- [Planetary Computer SAS signing guidance](https://planetarycomputer.microsoft.com/docs/concepts/sas/)
- [USGS Landsat Collection 2 overview](https://www.usgs.gov/landsat-missions/landsat-collection-2)
- [Copernicus Data Space Terms and Conditions](https://dataspace.copernicus.eu/terms-and-conditions)
- [Earth Engine access requirements](https://developers.google.com/earth-engine/guides/access)
- [Open-Meteo access, pricing, API, and licence](https://open-meteo.com/en/pricing), [API documentation](https://open-meteo.com/en/docs), [CC BY 4.0 terms](https://open-meteo.com/en/licence)
- [OpenStreetMap ODbL and attribution](https://www.openstreetmap.org/copyright)
- [WorldPop India 2020 1 km raster archive](https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/IND/)

## Other cached pilot sources

- **Weather:** Open-Meteo Forecast API, hourly values at the pilot center,
  seven-day horizon. Its free endpoint is non-commercial and rate-limited;
  data are CC BY 4.0 and require attribution. The Open-Meteo model snaps the
  requested point to a model grid point, which may be outside the small pilot
  bbox; the manifest records both the requested center and returned grid
  point.
- **Population:** WorldPop India 2020 estimated population counts, 30
  arc-second (~1 km at the equator) GeoTIFF, clipped locally to the bbox.
  The archive index does not state a specific file-level licence; cite
  WorldPop and verify product terms before redistribution.
- **Street features:** OpenStreetMap queried via OSMnx and the public Overpass
  API. This is variable-detail vector data, not a fixed-resolution raster.
  OSM is licensed under ODbL 1.0; credit OpenStreetMap contributors and meet
  the attribution/share-alike requirements.

All pilot outputs and the manifest remain in the git-ignored `data/raw/`
directory.
