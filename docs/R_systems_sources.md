# R - Delhi outdoor-worker heat-risk systems map sources

Sources were checked on **19 October 2026**. The notes below state what each
reference supports and the limits on applying it to the DTU/Rohini pilot.
General occupational mechanisms are not presented as Delhi-specific effect
sizes. See the [systems map](./R_systems_map.md) for citations in context.

## Primary sources

### S1 - NIOSH criteria for occupational exposure to heat

Jacklitsch, B., Williams, W. J., Musolin, K., Coca, A., Kim, J.-H., & Turner,
N. (2016). *Criteria for a Recommended Standard: Occupational Exposure to
Heat and Hot Environments*. DHHS (NIOSH) Publication No. 2016-106.
[NIOSH publication page](https://www.cdc.gov/niosh/publications/numbered/2016-106.html).

Supports the occupational heat-stress framework, combining environmental and
metabolic heat, risk factors, and controls. NIOSH lists high temperature and
humidity, direct sun, dehydration, exertion, age, pregnancy, health problems,
medication, and lack of acclimatization among relevant factors. This is
general occupational guidance, not a Delhi-specific threshold or validation.

### S2 - NIOSH heat-stress overview

National Institute for Occupational Safety and Health (NIOSH). *Heat Stress*.
[Overview and risk factors](https://www.cdc.gov/niosh/heat-stress/about/index.html).

Confirms that occupational heat stress combines metabolic heat, environmental
heat, and clothing/PPE, and describes resulting heat illness and injury. The
page identifies outdoor work, humidity, direct sun, limited air movement,
dehydration, exertion, health conditions, medication, age, pregnancy, prior
heat illness, and acclimatization as relevant risk considerations.

### S3 - NIOSH worker protection recommendations

NIOSH. *Recommendations for employers: heat stress*.
[Controls, hydration, work-rest, and acclimatization](https://www.cdc.gov/niosh/heat-stress/recommendations/index.html).

Supports work/rest schedules, recovery in a cool area, potable water near the
work area, heat alerts, acclimatization, and reducing strenuous work. These
recommendations assume employers can provide and workers can use the controls;
HeatShield cannot ensure either condition.

### S4 - Landsat Collection 2 surface-temperature product

U.S. Geological Survey (USGS) / Google Earth Engine data catalogue. *Landsat
8 Collection 2 Tier 1 Level 2*.
[Dataset description and surface-temperature product notes](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).

The catalogue identifies the thermal infrared band as an orthorectified
surface-temperature product derived from Landsat 8 TIRS data and documents
processing and missing-data limitations. This supports treating LST as
surface temperature, not ambient air temperature or an individual heat-dose
measurement. The local pilot data note records daytime scenes, native thermal
resolution/resampling, and cloud/clear-sky limitations:
[R_data_sources.md](./R_data_sources.md).

### S5 - National Weather Service heat index and WBGT

U.S. National Weather Service. *Heat Safety: Heat Index and Wet Bulb Globe
Temperature*.
[NWS heat tools](https://www.weather.gov/safety/heat-index).

The page defines heat index as air temperature interpreted with relative
humidity, notes that full sunshine can increase heat-index values, and
describes WBGT as using temperature, humidity, wind, solar radiation, and
other weather parameters. It identifies WBGT as useful for active populations
including outdoor workers. These are US public-weather guidance materials;
their thresholds should not be transplanted as India-specific clinical or
workplace cut-offs without local review.

### S6 - International Labour Organization productivity assessment

Kjellstrom, T., Maître, N., Saget, C., Otto, M., & Karimova, T. (2019).
*Working on a warmer planet: The impact of heat stress on labour productivity
and decent work*. International Labour Organization.
[Publication page and report](https://www.ilo.org/publications/working-warmer-planet-impact-heat-stress-labour-productivity-and-decent).

Supports the relationship between occupational heat stress, labour
productivity, and decent work, including the importance of outdoor work and
work organization. It provides global/national assessment, not a measured
causal loop for individual outdoor workers in Rohini. Income-pressure loops
in the map are explicitly hypotheses requiring worker and employer input.

### S7 - World Health Organization heat and health

World Health Organization (WHO). *Climate change, heat and health*.
[Fact sheet](https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health).

Identifies heat as an environmental and occupational health hazard and
describes serious health effects, including aggravation of underlying
conditions. Supports the climate-warming-to-heat-health pathway and the
importance of susceptibility. It is global guidance, not a pilot-area
vulnerability model or an individual prediction method.

### S8 - U.S. Environmental Protection Agency urban vegetation guidance

U.S. Environmental Protection Agency (EPA). *Using Trees and Vegetation to
Reduce Heat Islands*.
[EPA heat-island resource](https://www.epa.gov/heatislands/using-trees-and-vegetation-reduce-heat-islands).

The official resource describes urban trees and vegetation as heat-island
reduction strategies. It supports the urban greening intervention pathway;
local cooling depends on placement, canopy, water, maintenance, street form,
and whether workers can actually reach/use the shade. The page is not Delhi
effect-size evidence.

### S9 - National Weather Service humidity and direct-sun mechanism

U.S. National Weather Service, Amarillo Weather Forecast Office. *Heat Index*.
[NWS heat-index explanation](https://www.weather.gov/ama/heatindex).

Explains that sweat evaporation cools the body, high atmospheric moisture
reduces evaporation, and direct sunlight can raise heat-index-equivalent
conditions compared with the shade-based heat-index chart. This explains the
direction of the humidity and shade pathways; heat-index values are not WBGT
and should not be used as work-rest thresholds for the Delhi pilot.

### S10 - U.S. Environmental Protection Agency heat-island overview

U.S. Environmental Protection Agency (EPA). *What Are Heat Islands?*
[EPA overview](https://www.epa.gov/heatislands/what-are-heat-islands).

Provides the urban heat-island context for the map's urban-form pathway.
Together with S8, it supports considering urban surface cover and vegetation
as city-scale heat drivers and intervention areas. It does not quantify the
DTU/Rohini effect or establish which individual worker is exposed.

## Claim-to-source verification notes

| Claim used in the map | Evidence basis | Boundary |
|---|---|---|
| Heat exposure can lead to occupational heat illness and injury. | NIOSH S1-S2 and WHO S7. | Do not interpret a predicted risk score as a diagnosis. |
| Humidity, direct sun, and workload alter heat stress; WBGT accounts for multiple environmental variables. | NIOSH S1-S2, NWS S5 and S9. | The combination and thresholds need local exposure data and validation. |
| Water, shade, recovery, schedule adjustment, and acclimatization are protective controls. | NIOSH S1-S3 and NWS S5. | Warnings do not substitute for employer-provided controls. |
| Heat stress can affect productivity and decent work. | ILO S6. | Lost income is conditional on pay, time off, and job security; the causal income feedback is a local hypothesis. |
| Climate change contributes to rising heat-health risk. | WHO S7. | The map does not quantify the climate-change contribution in Delhi. |
| Vegetation can be a city heat-island intervention. | EPA S8. | The map does not assert site-specific cooling magnitude or that canopy is accessible to workers. |
| Urban heat islands are affected by city surface cover and form. | EPA S8-S10. | The map does not quantify local contributions from tree cover or impervious surfaces. |
| Satellite LST is a surface-temperature retrieval, not a worker or air-temperature observation. | Landsat product definition and limitations, S4; local product/resolution notes in `R_data_sources.md`. | Do not substitute a daytime satellite retrieval for time-specific air, globe, WBGT, or personal measurements. |

## Verification status

Links and source descriptions were checked on the date above. The causal loop
diagram is a synthesis, not a published causal model for Delhi. In particular,
the links among informal work, constrained access to protections, reduced
income, and subsequent exposure are marked as conditional hypotheses. The
team must review those links with local workers and partners before treating
them as established facts or using them to make operational decisions.
