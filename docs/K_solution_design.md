# HeatShield: solution design and feasibility

**Proposal scope:** a small, measurable heat-safety pilot around DTU/Rohini,
Delhi. This is a build-and-validation proposal, not a claim that the current
prototype is an operational warning service or a clinically validated risk
model.

## Executive summary

HeatShield joins two parts of the heat-response workflow that are usually
separate: (1) a worker-facing explanation of near-term outdoor heat risk and
feasible next steps, and (2) a city-facing view for finding priority places and
comparing candidate interventions under a stated budget. It is a decision
support layer around official forecasts, worker/employer controls, and city
heat-action plans—not a replacement for any of them.

The pilot should demonstrate:

1. A user can understand an activity- and exposure-aware risk card and choose
   an action they can actually take.
2. A small, quality-checked set of local observations and verified resources
   can add context to forecast and public geospatial data.
3. A city partner can inspect a transparent hotspot ranking and compare
   intervention scenarios within a fixed illustrative budget.
4. The team reports uncertainty, missing data, and limitations alongside
   every score and map.

**Build boundary:** the repository already has a web experience and a FastAPI
mock API, plus a heatcore screening estimate and pilot-data tooling. The
backend documentation says its API responses are synthetic and do not yet
persist readings or deliver live forecast-backed decisions. The pilot work
therefore includes connecting and validating data paths; do not present
existing mock values as observations, operational alerts, or measured
intervention effects. See [K_backend.md](./K_backend.md), [R systems map](./R_systems_map.md),
and [hardware BOM](./hardware_bom.md).

## 1. What we build

### User and workflow

**Primary pilot user:** an adult who regularly travels or works outdoors in
the DTU/Rohini area. Co-design the language and action choices with the people
who will use them; do not assume everyone has a smartphone, paid break,
employer permission, or access to a cool indoor space.

**City-side user:** a campus, municipal, public-health, or worker-support
partner who can verify candidate resources and decide whether a proposed
intervention is feasible and funded.

| Step | Product behavior | Evidence shown to user |
|---|---|---|
| 1. Establish context | Select or approximate an area, activity, and expected exposure window; avoid collecting exact continuous location by default. | Timestamp, source, spatial resolution, and whether values are forecast, observed, or illustrative. |
| 2. Estimate heat conditions | Combine a sourced forecast with air temperature, humidity, wind, and solar input to estimate WBGT where inputs are available. | WBGT estimate, data freshness, missing inputs, and uncertainty. |
| 3. Explain personal risk | Apply transparent activity, duration, and optional vulnerability assumptions to the heat estimate. | Risk band, the largest contributing factors, and a plain-language limitation. |
| 4. Offer feasible actions | Suggest timing, shade, water, rest, or a cooler route; show a resource only if its location and current status are adequately verified. | Action text distinguishes practical suggestions from guaranteed access. |
| 5. Prioritize a place | Show hotspot cells with data provenance and exposed-population estimates; allow an operator to set a budget and compare candidate intervention mixes. | Modelled ranking and assumptions, not a prediction of lives saved or guaranteed risk reduction. |
| 6. Learn and update | Record sensor health, resource verification, and intervention dates; compare before/after observations only with a suitable reference or comparison design. | Evaluation result is labelled observational or experimental as appropriate. |

### Differentiation against existing approaches

**Landscape-source note:** an S-authored landscape document was not present in
the repository. At the team's direction, this table is a concise desk-research
substitute, not a reconstruction of S's unpublished work. It compares
complementary solutions and service categories rather than claiming that
HeatShield replaces them. Validate the final competitor list with S before
external circulation.

| Existing solution / example | What it already provides | HeatShield's proposed distinction | Relationship and limitation |
|---|---|---|---|
| India Meteorological Department (IMD) warnings and heat guidance | Official weather observations, forecasts, and warning products; the IMD portal exposes district/subdivision warnings and nowcasts. | Convert a sourced forecast into an activity- and exposure-specific explanation, then connect it to verified nearby resources and a city prioritization view. | Complement, never compete with or override official warnings. HeatShield must show the IMD source and issue time, and must not imply finer forecast precision than the input supports. [IMD portal](https://mausam.imd.gov.in/) |
| City Heat Action Plans (HAPs), including Ahmedabad's plan | A public-health and city coordination framework for heat preparedness, communication, and response. The Ahmedabad plan is an established example of a city HAP. | Provide a repeatable, local data and workflow layer that can help partners identify where to review resources and compare proposed investments. | Operationalize and support a partner's plan; do not replace emergency protocols, authority, funding, public communication, or city accountability. The Ahmedabad example is not evidence that the same governance or results transfer to Delhi. [Ahmedabad Heat Action Plan (PDF)](https://www.nrdc.org/sites/default/files/ahmedabad-heat-action-plan-2019.pdf) |
| General weather forecasts and weather apps/APIs, such as Open-Meteo as a pilot data source | Weather forecasts and weather variables useful for planning. Open-Meteo is a forecast source in the pilot data notes, not a validated personal occupational-risk service. | Interpret available environmental variables with activity, duration, local resource context, and explicit confidence/provenance; provide an action and a municipal planning workflow. | Use reliable, licensed, attributed data sources. Forecast resolution, latency, terms, and service availability constrain the product. A forecast alone is not a measurement of a worksite microclimate or individual heat strain. [Open-Meteo docs](https://open-meteo.com/en/docs); [pilot data-source notes](./R_data_sources.md) |
| Earth-observation and GIS analysis platforms, e.g. Google Earth Engine | Large satellite and geospatial data catalogues and analysis tools for detecting land-surface patterns and change. | Package selected layers into an operationally legible hotspot review and intervention-planning workflow for local partners, with field checks and source metadata. | A data/analysis platform is an input, not a competing worker advice service. Satellite land-surface temperature (LST) is not air temperature, WBGT, or personal exposure; validate spatial and time support. [Google Earth Engine](https://earthengine.google.com/); [R data notes](./R_data_sources.md) |
| Occupational heat-protection guidance and employer controls (e.g. NIOSH guidance) | Evidence-based controls such as water, rest, shade, acclimatization, and work/rest planning. | Make the forecast and local conditions easier to interpret, and help identify where protective resources may be missing. | HeatShield cannot provide paid breaks, enforce controls, diagnose illness, or shift responsibility from employers and authorities. Guidance developed outside India needs local occupational-health review. [NIOSH recommendations](https://www.cdc.gov/niosh/heat-stress/recommendations/index.html); [R source register](./R_systems_sources.md) |

**Defensible claim:** the proposed differentiation is in the integration and
explainability of existing forecast, exposure, resource, and budget-planning
inputs. Do not claim that HeatShield is the first heat-alert system, has
superior forecast accuracy, or has demonstrated health or economic impact.

## 2. Theory of change

| Stage | HeatShield proposal | Assumptions / conditions |
|---|---|---|
| **Inputs** | Official or licensed forecast data; pilot-grade temperature/humidity/light (and optional globe) nodes; public geospatial and population layers; verified resource locations; web/API/database; a capped pilot budget; worker and partner time. | Data remain available and lawful to use; device placements are permitted; people with authority can provide or act on resource information. |
| **Activities** | Co-design risk language and actions; configure and QA data; test sensors against a reference; build forecast-to-risk and hotspot-to-optimizer workflows; verify resources; train partner users; run usability and field tests. | Participation is voluntary and safe; local expertise reviews assumptions; advice remains subordinate to official guidance and workplace controls. |
| **Outputs** | Timestamped risk cards with factors/actions; sourced hotspot map; verified-resource records; a ranked, budget-constrained intervention scenario; sensor/data-quality and usability reports. | Outputs expose provenance, uncertainty, missingness, and model limits; an operator does not mistake a mock/demo layer for live data. |
| **Short-term outcomes** | Users better understand when heat conditions merit attention and can identify a feasible protective option; partners can review where data indicate potential service gaps and compare options consistently. | Comprehension leads to action only when the user has agency and the proposed resource is real, accessible, and available. |
| **Medium-term outcomes** | Partners improve siting, verification, or scheduling of protective resources; field measurements and feedback lead to more locally appropriate risk communication. | A partner acts on the evidence, maintains interventions, and allocates recurring resources; evaluation includes appropriate comparison data. |
| **Impact sought** | Lower preventable heat exposure and more equitable access to protection for outdoor populations; better-targeted, accountable city investment. | Not attributable to software alone. Requires public-health/employer/city action, sustained funding, worker agency, and validated evidence over multiple heat seasons. |

The causal pathways and their conditional income/work-control feedbacks are
described in [R's systems map](./R_systems_map.md). Heat risk is not a
diagnosis, and a score or map is not evidence that a health outcome has been
prevented.

### Pilot KPIs

There is **no measured pilot baseline yet**. Record baseline values during the
first two weeks; never substitute a model default, mock API response, student
survey, or unverified resource list for a worker or field baseline. Targets
below are proposed go/no-go thresholds for a small prototype, not population
impact claims.

| Domain | KPI | Baseline | Pilot target | Measurement method |
|---|---|---|---|---|
| Human | Risk-card comprehension | Unknown; establish before task testing. | At least 8 of 10 adult usability participants correctly explain the shown risk band and one recommended action; none interpret it as a medical diagnosis. | Moderated, task-based test with voluntary adult participants; record anonymized counts and misunderstandings only. |
| Human | Action feasibility | Unknown; establish by asking what action is realistically available. | At least 7 of 10 participants can identify one action they could take in the shown scenario; report constraints and “no feasible action” responses rather than hiding them. | Scenario walkthrough and non-identifying structured feedback; no health disclosure required. |
| Human | Advice safety and comprehension | No locally reviewed language baseline. | 100% of tested screens show source/freshness and a concise limitation; all high-risk copy reviewed by a qualified local heat-health/occupational advisor before field use. | Content checklist and sign-off record; test the rendered copy on target devices/languages. |
| Infrastructure | Sensor data completeness | Unknown until bench and field deployment. | At least 90% of expected hourly records received per node over a 14-day test, with every gap and outage visible. | Expected-versus-received timestamp audit; report per-node and aggregate completeness. |
| Infrastructure | Sensor comparison | No reference comparison established. | At least 90% of paired temperature and RH readings within the team-agreed pilot tolerance of a checked reference (initial proposal: ±1.5°C and ±10 percentage points RH). | Co-locate devices with a traceable/checkable reference across relevant conditions; document instrument, placement, calibration, and exclusions. These are engineering acceptance targets, not certification. |
| Infrastructure | Resource/map traceability | Current backend demo uses synthetic resources; verified field count is zero until audited. | Every displayed real resource has a source, verification date, status or “unknown” label, and partner/field-check evidence; do not present stale entries as open. | Audit sample on the ground with partner permission; log verification time and status without collecting personal-location data. |
| Economic | Hardware cost per deployed node | Existing BOM estimate: approximately ₹2,256–₹3,106 per node with the optional DIY globe channel; estimate only. | Keep six-node hardware purchase at or below ₹18,636, subject to current quotes and availability. | Dated itemized invoices/quotes compared with [hardware BOM](./hardware_bom.md); record substitutes and tax/shipping separately. |
| Economic | Optimizer budget feasibility and modeled coverage | No field-validated intervention-effect baseline. | Every generated plan remains within the entered budget; across at least 10 fixed test scenarios, report exposed-population/risk proxy per rupee against a simple documented baseline allocator. A ≥10% modeled improvement is a stretch target, not a real-world benefit claim. | Reproducible scenarios and saved assumptions; compare algorithms on the same input snapshot. Separately report simulated values and do not call them people actually protected. |
| Economic | Recurring service cost | Unknown before service/data choices. | Measure monthly connectivity, hosting, replacement, and maintenance; present a per-node/month figure before scale-up rather than assume zero-cost operations. | Invoices and usage logs over the pilot; separate in-kind labor and one-time equipment from recurring costs. |

**Do not use as short-pilot success KPIs:** heat-related deaths,
hospitalizations, diagnosed illness, or “income saved.” These outcomes need
appropriate ethical review, longer observation, suitable comparison designs,
and data that this pilot does not currently have.

## 3. Risk register

Likelihood and impact are qualitative pre-mitigation planning judgements:
**L** = low, **M** = medium, **H** = high. Re-score at kickoff and after each
field test. Owners are proposed team assignments, not evidence that mitigation
is already complete.

| Risk | Likelihood | Impact | Mitigation / trigger | Owner |
|---|:---:|:---:|---|---|
| **Sensor failure or drift** | M | H | Bench-test before installation; maintain node IDs, calibration and placement logs; compare against a reference; show stale/missing data and fall back to sourced forecast values without disguising the fallback. Pause any sensor-driven inference when QA fails. | K with R |
| **Bad, biased, stale, or spatially mismatched data** | H | H | Track source, timestamp, CRS/resolution, units, licence, missingness, and quality flags; distinguish air temperature, LST, WBGT, and population estimates; ground-check locations; do not interpolate or aggregate beyond defensible resolution. | R with K |
| **Low adoption or no ability to act** | M | H | Co-design with intended users; test language, phone access, trust, and action feasibility; include offline/partner-mediated options; do not count impressions/downloads as protective action. If users cannot act, redesign the workflow and engage employers/partners instead of escalating alerts. | S with R |
| **Wrong, overconfident, or misunderstood advice** | M | H | Label estimates and freshness; use official warnings as authority; safety-review thresholds and translations; test alert comprehension; give conservative fallback guidance and escalation to local health services. Do not diagnose, promise safety, or prescribe work/rest limits from an unvalidated score. | R with K |
| **Privacy or re-identification** | M | H | Minimize data; avoid default continuous GPS, names, phone numbers, health details, and raw interview text; use coarse aggregation, short retention, role-based access, consent, and private storage; review every public export. Stop collection on any unauthorized access or accidental disclosure. | K with S |
| **Connectivity/power outage** | H | M | Batch and buffer sensor records; expose last-seen timestamps; use low-power duty cycles and test several cloudy days; design user actions to degrade gracefully to official warnings/local guidance; test offline operation before deployment. | K |
| **Partner/site access or permissions delayed** | M | H | Secure written site and data permissions before procurement; identify alternate test sites and a no-install demo; do not install public devices or represent a partner as endorsing the work without authorization. Escalate if access is not confirmed by W−5. | K with team |
| **Costs exceed estimate or procurement is unavailable** | M | M | Obtain current quotes, check stock/taxes/shipping, cap purchases, keep optional globe channel and cloud spend as gated items, reserve contingency, document donated/in-kind inputs, and stop procurement if total exceeds approved cap. | K with team |

**Cross-cutting stop conditions:** no live advice until a named reviewer signs
off; no real user data without consent and an approved handling plan; no
installation without site permission; no external claim of measured benefits
from mock, simulated, or unvalidated data.

## 4. Budget and delivery plan

### Indicative pilot budget (INR)

The target is a **₹40,000–₹75,000 cash envelope** for an eight-week,
six-node prototype. It is a planning range, not a quote. The node estimate is
from the team's [hardware BOM](./hardware_bom.md), checked 19 October 2026;
prices and availability must be refreshed before purchase. Hardware vendor
prices, data terms, taxes, shipping, permissions, and institutional hosting
may change. Staff/student time, permanent city infrastructure, medical
services, and city intervention construction are excluded.

| Cost line | Low (₹) | High (₹) | Basis / gate |
|---|---:|---:|---|
| Six pilot nodes, including optional DIY globe channels | 13,536 | 18,636 | Existing BOM range; confirm stock and quote before ordering. |
| Reference instrument / calibration and QA allowance | 4,000 | 8,000 | Planning allowance; borrow a suitable reference if available; obtain quote if purchase is needed. |
| Site mounting, fasteners, installation materials | 3,000 | 6,000 | Planning allowance; only after site permissions and placement review. |
| Local travel and field visits | 4,000 | 8,000 | Planning allowance for setup, verification, and return visits. |
| Connectivity / data allowance | 2,000 | 5,000 | Prefer approved existing Wi-Fi where appropriate; avoid assuming continuous cellular coverage. |
| Hosting, domain, monitoring | 0 | 5,000 | Use approved institutional/free-tier resources if available; validate privacy, terms, and availability. |
| Accessible print / user-testing materials | 2,000 | 4,000 | Short, multilingual materials; no personal data in public handouts. |
| Spares and maintenance | 2,000 | 4,000 | Battery, wiring, connector, and enclosure contingency; reuse only tested parts. |
| Subtotal | **30,536** | **58,636** | Sum of above estimates. |
| Contingency (approximately 20%) | 6,107 | 11,727 | Held by team; requires approval to spend. |
| **Planning total** | **36,643** | **70,363** | Round planning envelope to **₹40,000–₹75,000**; release funds in stages. |

The total excludes any city-funded shade, water, or cooling installation;
HeatShield can rank proposals but cannot fund or deliver them. Keep procurement
receipts, quotes, and participant activity free of identifying/personal data
in public Git.

### Relative week-by-week timeline to regional finals

The official GSC page currently displays a **past 2025–26** cycle and does not
provide a verified upcoming regional-finals date. The schedule below is
therefore a relative eight-week countdown, **not an asserted event date**.
Replace W−8 … W0 with the organizer's confirmed dates and submission rules
before committing spend. [Official GSC page](https://makerbhavanfoundation.org/gsc/)
(checked 21 November 2026).

| Week | Deliverable and gate |
|---|---|
| **W−8** | Confirm organizer date, eligibility, deliverables, and mentor/judge expectations; reconcile S's original landscape with the cited comparison; choose pilot users and an authorized site. **Gate:** no public pitch with unverified rules or unapproved site access. |
| **W−7** | Worker/user co-design and risk-language review; document tasks, constraints, consent, and data-minimization plan; agree KPIs and baseline protocol. **Gate:** no personal/health data collection without approval and safe handling. |
| **W−6** | Refresh procurement quotes and data licences; complete sensor bench plan and API/data-flow design; label mock versus live sources in UI. **Gate:** cap total commitments to budget; postpone hardware if site permission is pending. |
| **W−5** | Build data QA and provenance checks; test sensors against a reference; connect forecast/API paths in a non-public test environment; draft partner resource-verification checklist. **Gate:** stop operational risk display if inputs fail QA. |
| **W−4** | Conduct privacy-safe usability test; validate Hindi/English action copy and accessibility; run optimizer against documented scenarios and a simple baseline. **Gate:** safety reviewer signs off on any advice presented as pilot guidance. |
| **W−3** | If permitted, deploy up to six nodes; verify location, power, connectivity, time sync, and data receipt; audit a small set of real resources with partner permission. Otherwise, run a clearly labelled tabletop demo. |
| **W−2** | Collect reliability and comprehension KPIs; fix high-severity issues; compare forecasts, nodes, and references without conflating LST/air/globe temperature; freeze demo scenario and fallback. |
| **W−1** | Rehearse end-to-end live and offline demos; test failure modes; prepare evidence-backed claim sheet, risk register, budget actuals, and scale-up conditions. **Gate:** demo remains safe if network or sensors fail. |
| **W0: regional finals** | Demonstrate one user workflow and one city workflow; present measured pilot metrics with sample sizes, provenance, uncertainty, and limitations; distinguish prototype, simulation, and field evidence; propose next-season validation. |

If fewer than eight weeks remain, preserve the safety, permission, and
evidence gates; reduce deployment scope instead of compressing them. If more
time is available, extend field testing and comparison measurement rather
than inflating impact claims.

## 5. Team roles and decision rights

| Role | Lead responsibility | Shared interfaces / decisions |
|---|---|---|
| **R — heat science and data** | Own WBGT/risk assumptions, activity/exposure interpretation, forecast and geospatial feature provenance, uncertainty, model tests, and scientific/health-source review. | Co-define data contracts with K and action language with S; approve scientific limits and claims. |
| **S — web experience and landscape** | Own worker/city user journeys, accessible interface, localization, user testing, and the original competitor/landscape inventory. | Confirm and supply the missing landscape source; coordinate with R on understandable evidence and with K on API behavior. |
| **K — backend, devices, and delivery** | Own FastAPI/PostGIS, migrations, data ingestion interfaces, sensor-node firmware/integration, deployment/reliability, privacy/security operations, budget tracking, and this solution-design document. | Coordinate site/partner permissions with all; preserve source/licence metadata and operational audit trail. |
| **All three** | Agree on pilot scope, consent and data handling, reviewer sign-off, risk severity, go/no-go gates, and final claims. | No single owner may turn synthetic, incomplete, or unvalidated data into a public health or impact claim. |

## Feasibility decision

**Feasible as a scoped prototype and evidence-gathering pilot** if the team
can secure an authorized test site, refresh quotes, recruit voluntary adult
users safely, and obtain local scientific/health review. A six-node field
deployment is a stretch goal, not a prerequisite to demonstrate the software
workflow.

**Not yet feasible to claim** citywide forecasting, clinically validated
individual risk, real-time resource availability, causal reductions in
illness/productivity loss, or cost-effectiveness of interventions. Those
claims require better ground truth, partner operations, longer observation,
and evaluation beyond a student prototype.

## References and evidence limits

Sources checked **21 November 2026**, except the repository BOM, whose
price-check date is stated as 19 October 2026. A web page being accessible is
not proof that its approach or effect size transfers to Delhi.

1. HeatShield, [R's systems map](./R_systems_map.md) and [R's source register](./R_systems_sources.md): local causal hypotheses, mechanisms, and model limits.
2. HeatShield, [R's pilot data-source notes](./R_data_sources.md): data provenance, resolution, licensing, and current access constraints.
3. HeatShield, [K backend description](./K_backend.md): mock API behavior, database boundary, and migration implementation.
4. HeatShield, [sensor node BOM](./hardware_bom.md): six-node scope and dated cost estimates.
5. India Meteorological Department, [official portal](https://mausam.imd.gov.in/): public warnings, nowcasts, observations, and heatwave guidance entry points.
6. Ahmedabad, [Heat Action Plan 2019 (PDF)](https://www.nrdc.org/sites/default/files/ahmedabad-heat-action-plan-2019.pdf): example city heat-action framework; cited as an example, not Delhi validation.
7. Open-Meteo, [API documentation](https://open-meteo.com/en/docs): forecast-source reference; check live terms, attribution, availability, and spatial/temporal fit before use.
8. Google, [Earth Engine](https://earthengine.google.com/): geospatial analysis platform description; satellite-derived surface temperature is not personal exposure.
9. World Health Organization, [Heat and health](https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health), updated 31 July 2026: general health and occupational context, not a Delhi-specific risk model.
10. International Labour Organization, [Working on a warmer planet](https://www.ilo.org/publications/working-warmer-planet-impact-heat-stress-labour-productivity-and-decent): global occupational productivity context, not a local causal estimate.
11. U.S. NIOSH, [worker heat-stress recommendations](https://www.cdc.gov/niosh/heat-stress/recommendations/index.html): general protection controls; local occupational-health review is still required.
12. Maker Bhavan Foundation, [Global Sustainability Challenge](https://makerbhavanfoundation.org/gsc/): the published page describes an old 2025–26 schedule; confirm the current regional-finals date and rules with organizers.
