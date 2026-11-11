import { useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import type { FeatureCollection, Point } from 'geojson'
import {
  getHeatmap,
  getInterventionPlan,
  getResources,
  getRiskAssessment,
  isMockMode,
  postRoute,
  simulateInterventions,
} from './api/client'
import type {
  BBox,
  HeatmapProperties,
  HeatmapResponse,
  InterventionPlan,
  Resource,
  ResourceType,
  ResourcesResponse,
  RiskAssessment,
  RouteResponse,
} from './api/types'
import './App.css'

function Brand() {
  return (
    <NavLink className="brand" to="/risk" aria-label="HeatShield home">
      <span className="brand-mark" aria-hidden="true">
        H
      </span>
      <span>
        <strong>heatshield</strong>
        <small>DELHI PILOT</small>
      </span>
    </NavLink>
  )
}

function AppHeader() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  }, [dark])

  return (
    <header className="topbar">
      <Brand />
      <nav className="primary-nav" aria-label="Choose workspace">
        <NavLink to="/risk" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Risk Card</NavLink>
        <NavLink to="/route" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Heat-Safe Route</NavLink>
        <NavLink to="/resources" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Resources Map</NavLink>
        <NavLink to="/city" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>City Heatmap</NavLink>
        <NavLink to="/optimizer" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Optimizer</NavLink>
        <NavLink to="/simulator" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Simulator</NavLink>
      </nav>
      <div className="topbar-actions">
        <span className={`mode-pill ${isMockMode ? 'mode-mock' : 'mode-live'}`}>
          <span />{isMockMode ? 'Mock data' : 'Live API'}
        </span>
        <button
          className="icon-button theme-toggle"
          type="button"
          onClick={() => setDark((value) => !value)}
          aria-label={`Switch to ${dark ? 'light' : 'dark'} mode`}
          title={`Switch to ${dark ? 'light' : 'dark'} mode`}
        >
          {dark ? '☼' : '◐'}
        </button>
        <span className="avatar" aria-label="Delhi pilot">D</span>
      </div>
    </header>
  )
}

function PageFrame({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <>
      <AppHeader />
      <main className={`page-content${className ? ` ${className}` : ''}`}>{children}</main>
      <footer className="site-footer">
        <span>HeatShield <span className="footer-dot">·</span> Built for hotter days</span>
        <span>Delhi <span aria-hidden="true">↗</span> Rohini</span>
      </footer>
    </>
  )
}

function Metric({ label, value, unit, tone = 'neutral' }: {
  label: string
  value: string
  unit?: string
  tone?: 'neutral' | 'warm' | 'hot'
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}<small>{unit}</small></strong>
    </div>
  )
}

function WorkerApp() {
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [requestNumber, setRequestNumber] = useState(0)

  useEffect(() => {
    let current = true
    getRiskAssessment()
      .then((result) => { if (current) setAssessment(result) })
      .catch((reason: Error) => { if (current) setError(reason.message) })
    return () => { current = false }
  }, [requestNumber])

  return (
    <PageFrame>
      <section className="worker-layout">
        <div className="worker-main">
          <div className="eyebrow"><span className="live-dot" /> YOUR SHIFT CHECK <span className="eyebrow-divider">/</span> DELHI, 1:30 PM</div>
          <div className="worker-heading">
            <div>
              <h1>Your shift, <em>safer.</em></h1>
              <p className="lede">A heat check for delivery workers in Rohini.</p>
            </div>
            <span className="weather-chip"><span aria-hidden="true">☀</span> Delhi <b>38°</b></span>
          </div>

          {error && (
            <ErrorBanner
              message={`today’s heat check: ${error}`}
              onRetry={() => {
                setAssessment(null)
                setError(null)
                setRequestNumber((value) => value + 1)
              }}
            />
          )}
          <section className="risk-card" aria-label="Your heat risk">
            <div className="risk-card-top">
              <div>
                <span className="card-kicker">DELIVERY WORKER <span className="muted-separator">·</span> ROHINI, DELHI</span>
                <h2>{assessment ? (assessment.level === 'extreme' ? 'Severe Heat Risk' : `${assessment.level[0].toUpperCase()}${assessment.level.slice(1)} Heat Risk`) : 'Loading your forecast'}</h2>
                <p>Today at 1:30 PM <span className="muted-separator">·</span> Updated just now</p>
              </div>
              <div className="risk-gauge" aria-label={assessment ? `Risk score ${assessment.risk_score} out of 100` : 'Risk score loading'}>
                <strong>{assessment ? assessment.risk_score : '—'}</strong><span>/ 100</span>
              </div>
            </div>
            <div className="risk-scale">
              <div className="scale-track"><span style={{ width: `${assessment?.risk_score ?? 0}%` }} /></div>
              <div className="scale-labels"><span>Low</span><span>Moderate</span><span>High</span><span>Extreme</span></div>
            </div>
            <div className="risk-facts">
              <Metric label="Heat stress" value={assessment ? `${assessment.wbgt_c}°` : '—'} unit=" WBGT" tone="hot" />
              <Metric label="Current time" value="1:30" unit=" PM" tone="warm" />
              <Metric label="Risk eases" value="3:30" unit=" PM" />
            </div>

            <div className="heat-alert">
              <span className="heat-alert-icon" aria-hidden="true">!</span>
              <div>
                <span className="card-kicker">DO THIS NOW</span>
                <strong>Avoid outdoor work 1:00–3:30 PM</strong>
                <p>Move deliveries to a cooler part of your shift if you can.</p>
              </div>
            </div>

            <div className="nearby-section">
              <div className="section-heading">
                <div><span className="card-kicker">CLOSE BY</span><h2>Places to cool down</h2></div>
                <NavLink className="text-link" to="/resources">See map <span aria-hidden="true">↗</span></NavLink>
              </div>
              <div className="nearby-grid" aria-label="Nearby heat-safety resources">
                <article className="nearby-card">
                  <span className="nearby-icon nearby-icon-shade" aria-hidden="true">◒</span>
                  <span className="nearby-label">Shaded rest</span>
                  <strong>450 <small>m</small></strong>
                </article>
                <article className="nearby-card">
                  <span className="nearby-icon nearby-icon-water" aria-hidden="true">↘</span>
                  <span className="nearby-label">Drinking water</span>
                  <strong>280 <small>m</small></strong>
                </article>
                <article className="nearby-card">
                  <span className="nearby-icon nearby-icon-cooling" aria-hidden="true">✳</span>
                  <span className="nearby-label">Cooling spot</span>
                  <strong>600 <small>m</small></strong>
                </article>
              </div>
            </div>

            <NavLink className="safer-route" to="/route">
              <span className="route-icon" aria-hidden="true">↗</span>
              <span className="route-copy">
                <span className="card-kicker">A COOLER WAY</span>
                <strong>Alternate route</strong>
                <small>38% lower heat exposure</small>
              </span>
              <span className="route-time">+6 <small>min</small></span>
              <span className="route-chevron" aria-hidden="true">→</span>
            </NavLink>
          </section>
          <section className="worker-reassurance" aria-label="Heat safety reminder">
            <span className="tip-icon" aria-hidden="true">✳</span>
            <p>Feeling dizzy or unusually tired? Stop work, move to shade, and tell someone nearby.</p>
          </section>
          <p className="disclaimer">HeatShield guidance supports—not replaces—local health advice.</p>
        </div>
      </section>
    </PageFrame>
  )
}

type HeatmapDisplayProperties = HeatmapProperties & { hotspot_rank?: number; simulated?: boolean }

function getHeatmapDisplayData(data: FeatureCollection<Point, HeatmapProperties>, coolingCellId?: string) {
  const rankedIds = [...data.features]
    .sort((left, right) => right.properties.risk - left.properties.risk)
    .slice(0, 3)
    .map((feature) => feature.properties.cell_id)
  const ranks = new Map(rankedIds.map((id, index) => [id, index + 1]))

  return {
    ...data,
    features: data.features.map((feature) => ({
      ...feature,
      properties: {
        ...feature.properties,
        hotspot_rank: ranks.get(feature.properties.cell_id),
        simulated: feature.properties.cell_id === coolingCellId,
      },
    })),
  } satisfies FeatureCollection<Point, HeatmapDisplayProperties>
}

function streetMapStyle() {
  return {
    version: 8 as const,
    sources: {
      streets: {
        type: 'raster' as const,
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [
      { id: 'streets', type: 'raster' as const, source: 'streets', paint: { 'raster-saturation': -0.8, 'raster-opacity': 0.75 } },
    ],
  }
}

function HeatMap({ data, coolingCellId }: {
  data: FeatureCollection<Point, HeatmapProperties>
  coolingCellId?: string
}) {
  const [mapElement, setMapElement] = useState<HTMLDivElement | null>(null)
  const [mapError, setMapError] = useState<string | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const mapRef = useRef<import('maplibre-gl').Map | null>(null)
  const hotspotMarkers = useRef(new Map<string, HTMLSpanElement>())
  const displayData = useMemo(() => getHeatmapDisplayData(data, coolingCellId), [data, coolingCellId])
  const initialDisplayData = useRef(displayData)

  useEffect(() => {
    if (!mapElement) return

    let map: import('maplibre-gl').Map | undefined
    const markers: import('maplibre-gl').Marker[] = []
    const markerElements = hotspotMarkers.current
    let cancelled = false

    import('maplibre-gl')
      .then(({ Map: MapLibreMap, Marker }) => {
        if (cancelled) return
        map = new MapLibreMap({
          container: mapElement,
          center: [77.081, 28.743],
          zoom: 12,
          minZoom: 10,
          maxZoom: 15,
          attributionControl: { compact: true },
          style: streetMapStyle(),
        })
        mapRef.current = map

        map.on('load', () => {
          map?.addSource('heat-risk', { type: 'geojson', data: initialDisplayData.current })
          map?.addLayer({
            id: 'heat-risk-circles',
            type: 'circle',
            source: 'heat-risk',
            paint: {
              'circle-color': ['case', ['==', ['get', 'simulated'], true], '#4c9568', ['interpolate', ['linear'], ['get', 'risk'], 0, '#2f855a', 40, '#d69e2e', 65, '#e77931', 85, '#a82a2a']],
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 10, 15, 25],
              'circle-opacity': ['case', ['==', ['get', 'simulated'], true], 0.92, 0.72],
              'circle-stroke-width': ['case', ['==', ['get', 'simulated'], true], 4, 2],
              'circle-stroke-color': ['case', ['==', ['get', 'simulated'], true], '#e7f6df', '#fffdf8'],
            },
          })
          if (!map) return
          for (const feature of initialDisplayData.current.features) {
            const rank = feature.properties.hotspot_rank
            if (rank === undefined) continue
            const [longitude, latitude] = feature.geometry.coordinates
            if (longitude === undefined || latitude === undefined) continue
            const element = document.createElement('span')
            element.className = 'map-hotspot-badge'
            element.textContent = `#${rank}`
            markerElements.set(feature.properties.cell_id, element)
            markers.push(new Marker({ element }).setLngLat([longitude, latitude]).addTo(map))
          }
          setMapReady(true)
        })
      })
      .catch((reason: Error) => {
        if (!cancelled) setMapError(reason.message)
      })

    return () => {
      cancelled = true
      map?.remove()
      markers.forEach((marker) => marker.remove())
      markerElements.clear()
      mapRef.current = null
      setMapReady(false)
    }
  }, [mapElement])

  useEffect(() => {
    if (!mapReady) return
    const source = mapRef.current?.getSource('heat-risk') as import('maplibre-gl').GeoJSONSource | undefined
    source?.setData(displayData)
    for (const [cellId, element] of hotspotMarkers.current) {
      element.classList.toggle('is-cooled', cellId === coolingCellId)
    }
  }, [coolingCellId, displayData, mapReady])

  return (
    <div
      className="map-view"
      ref={setMapElement}
      role="img"
      aria-label={coolingCellId ? 'Map of heat risk hotspots with the simulated hotspot cooled' : 'Map of heat risk hotspots in Rohini, Delhi'}
    >
      {mapError && <span className="map-error">Map unavailable: {mapError}</span>}
    </div>
  )
}

function RouteMap({ route }: { route: RouteResponse }) {
  const [mapElement, setMapElement] = useState<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!mapElement) return

    let map: import('maplibre-gl').Map | undefined
    const markers: import('maplibre-gl').Marker[] = []
    let cancelled = false
    import('maplibre-gl')
      .then(({ Map: MapLibreMap, Marker }) => {
        if (cancelled) return
        map = new MapLibreMap({
          container: mapElement,
          center: [77.096, 28.745],
          zoom: 13,
          minZoom: 11,
          maxZoom: 16,
          attributionControl: { compact: true },
          style: streetMapStyle(),
        })
        map.on('load', () => {
          map?.addSource('route-options', {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: (['fastest', 'coolest'] as const).map((kind) => ({
                type: 'Feature' as const,
                geometry: route[kind].geometry,
                properties: { kind },
              })),
            },
          })
          map?.addLayer({
            id: 'fastest-route',
            type: 'line',
            source: 'route-options',
            filter: ['==', ['get', 'kind'], 'fastest'],
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': '#d76545', 'line-width': 7, 'line-opacity': 0.9 },
          })
          map?.addLayer({
            id: 'coolest-route',
            type: 'line',
            source: 'route-options',
            filter: ['==', ['get', 'kind'], 'coolest'],
            layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': '#377c59', 'line-width': 7, 'line-opacity': 0.95 },
          })
          const first = route.fastest.geometry.coordinates[0]
          const last = route.fastest.geometry.coordinates.at(-1)
          if (!first || !last) return
          const [firstLongitude, firstLatitude] = first
          const [lastLongitude, lastLatitude] = last
          if (firstLongitude === undefined || firstLatitude === undefined || lastLongitude === undefined || lastLatitude === undefined) return
          if (!map) return
          const firstPoint: [number, number] = [firstLongitude, firstLatitude]
          const lastPoint: [number, number] = [lastLongitude, lastLatitude]
          map?.addSource('route-stops', {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: [
                { type: 'Feature', geometry: { type: 'Point', coordinates: firstPoint }, properties: { label: 'DTU' } },
                { type: 'Feature', geometry: { type: 'Point', coordinates: lastPoint }, properties: { label: 'SECTOR 16' } },
              ],
            },
          })
          map?.addLayer({
            id: 'route-stop-circles',
            type: 'circle',
            source: 'route-stops',
            paint: { 'circle-radius': 8, 'circle-color': '#fffdf8', 'circle-stroke-color': '#234c3a', 'circle-stroke-width': 3 },
          })
          for (const stop of [
            { coordinates: firstPoint, label: 'DTU' },
            { coordinates: lastPoint, label: 'SECTOR 16' },
          ]) {
            const element = document.createElement('span')
            element.className = 'route-stop-label'
            element.textContent = stop.label
            markers.push(new Marker({ element, anchor: 'bottom' }).setLngLat(stop.coordinates).addTo(map))
          }
        })
      })
      .catch((reason: Error) => {
        if (!cancelled) console.error('HeatShield route map failed to load:', reason)
      })

    return () => {
      cancelled = true
      map?.remove()
      markers.forEach((marker) => marker.remove())
    }
  }, [mapElement, route])

  return <div className="route-map-view" ref={setMapElement} role="img" aria-label="Map comparing the fastest and coolest routes from DTU to Sector 16" />
}

const CITY_TIMES = ['10:00', '11:00', '12:00', '13:00'] as const
type CityTime = typeof CITY_TIMES[number]

function formatCityTime(time: CityTime): string {
  const hour = Number(time.slice(0, 2))
  return `${hour > 12 ? hour - 12 : hour}:00 ${hour >= 12 ? 'PM' : 'AM'}`
}

function CityApp() {
  const [heatmap, setHeatmap] = useState<FeatureCollection<Point, HeatmapProperties> | null>(null)
  const [heatmapLoading, setHeatmapLoading] = useState(true)
  const [heatmapError, setHeatmapError] = useState<string | null>(null)
  const [plan, setPlan] = useState<InterventionPlan | null>(null)
  const [planError, setPlanError] = useState<string | null>(null)
  const [timeSlot, setTimeSlot] = useState<CityTime>('10:00')
  const [isPlaying, setIsPlaying] = useState(false)
  const [heatmapRequest, setHeatmapRequest] = useState(0)
  const [planRequest, setPlanRequest] = useState(0)

  useEffect(() => {
    let current = true
    getHeatmap(DEFAULT_BOUNDS, timeSlot)
      .then((result) => { if (current) setHeatmap(result) })
      .catch((reason: unknown) => {
        if (current) setHeatmapError(reason instanceof Error ? reason.message : 'Unexpected response from the heatmap service.')
      })
      .finally(() => { if (current) setHeatmapLoading(false) })
    return () => { current = false }
  }, [timeSlot, heatmapRequest])

  useEffect(() => {
    let current = true
    getInterventionPlan()
      .then((result) => { if (current) setPlan(result) })
      .catch((reason: unknown) => {
        if (current) setPlanError(reason instanceof Error ? reason.message : 'Unexpected response from the optimizer service.')
      })
    return () => { current = false }
  }, [planRequest])

  useEffect(() => {
    if (!isPlaying) return
    const timer = window.setTimeout(() => {
      if (timeSlot === CITY_TIMES[CITY_TIMES.length - 1]) {
        setIsPlaying(false)
        return
      }
      setHeatmapLoading(true)
      setTimeSlot((current) => CITY_TIMES[CITY_TIMES.indexOf(current) + 1])
    }, timeSlot === CITY_TIMES[CITY_TIMES.length - 1] ? 0 : 1_500)
    return () => window.clearTimeout(timer)
  }, [isPlaying, timeSlot])

  const priorityHotspots = [...(heatmap?.features ?? [])]
    .sort((left, right) => right.properties.risk - left.properties.risk)
    .slice(0, 3)

  return (
    <PageFrame>
      <section className="city-heading">
        <div>
          <div className="eyebrow"><span className="live-dot" /> CITY OPERATIONS <span className="eyebrow-divider">/</span> DELHI</div>
          <h1>See where heat <em>hits hardest.</em></h1>
          <p className="lede">A neighbourhood view to help put support where it matters.</p>
        </div>
        <button className="date-button" type="button"><span aria-hidden="true">▦</span> Today, 18 Oct <span aria-hidden="true">⌄</span></button>
      </section>
      {planError && (
        <ErrorBanner
          message={`intervention recommendations: ${planError}`}
          onRetry={() => {
            setPlan(null)
            setPlanError(null)
            setPlanRequest((request) => request + 1)
          }}
        />
      )}
      {heatmapError && heatmap && (
        <ErrorBanner
          message={`heatmap for ${formatCityTime(timeSlot)}: ${heatmapError}`}
          onRetry={() => {
            setHeatmapError(null)
            setHeatmapLoading(true)
            setHeatmapRequest((request) => request + 1)
          }}
        />
      )}
      <section className="city-metrics" aria-label="City heat metrics">
        <Metric label="People at high risk" value={plan ? plan.population_exposed.toLocaleString('en-IN') : '—'} tone="hot" />
        <Metric label="Priority hotspots" value={heatmap ? String(priorityHotspots.length).padStart(2, '0') : '—'} tone="warm" />
        <Metric label="Interventions ready" value={plan ? String(plan.interventions.length).padStart(2, '0') : '—'} />
        <div className="metric-note"><span className="live-dot" /><span>Forecast refreshed<br /><strong>Today, 9:40 AM</strong></span></div>
      </section>
      <section className="heat-timeline" aria-label="Heatmap time controls">
        <div className="timeline-heading">
          <div><span className="card-kicker">FORECAST PLAYBACK</span><strong>Heat through the day</strong></div>
          <span className="timeline-current">{formatCityTime(timeSlot)}</span>
        </div>
        <div className="timeline-controls">
          <button
            className="timeline-play"
            type="button"
            aria-pressed={isPlaying}
            onClick={() => {
              if (!isPlaying && timeSlot === CITY_TIMES[CITY_TIMES.length - 1]) setTimeSlot(CITY_TIMES[0])
              setHeatmapError(null)
              setIsPlaying((playing) => !playing)
            }}
          >
            <span aria-hidden="true">{isPlaying ? 'Ⅱ' : '▶'}</span>{isPlaying ? 'Pause' : 'Play'}
          </button>
          <div className="timeline-slots">
            {CITY_TIMES.map((time, index) => (
              <button
                key={time}
                type="button"
                aria-pressed={timeSlot === time}
                className={`timeline-slot${timeSlot === time ? ' selected' : ''}`}
                onClick={() => {
                  setIsPlaying(false)
                  setHeatmapError(null)
                  if (time !== timeSlot) {
                    setHeatmapLoading(true)
                    setTimeSlot(time)
                  }
                }}
              >
                <span className="timeline-dot" />
                <span>{formatCityTime(time)}</span>
                {index < CITY_TIMES.length - 1 && <span className="timeline-connector" aria-hidden="true" />}
              </button>
            ))}
          </div>
        </div>
      </section>
      <section className="city-grid">
        <article className="panel map-panel">
          <div className="panel-heading">
            <div><span className="card-kicker">NEIGHBOURHOOD VIEW</span><h2>Rohini heat map</h2></div>
            <span className="heatmap-time-chip">{formatCityTime(timeSlot)} forecast</span>
          </div>
          {heatmap
            ? <HeatMap data={heatmap} />
            : (
              <div className="map-placeholder" role={heatmapError ? 'alert' : 'status'}>
                {heatmapLoading
                  ? 'Loading hotspot map…'
                  : (
                    <div className="map-load-error">
                      <p>Could not load hotspot map: {heatmapError}</p>
                      <button
                        type="button"
                        className="map-retry-button"
                        onClick={() => {
                          setHeatmapError(null)
                          setPlanError(null)
                          setHeatmapLoading(true)
                          setHeatmapRequest((request) => request + 1)
                          setPlanRequest((request) => request + 1)
                        }}
                      >
                        Try again
                      </button>
                    </div>
                  )}
              </div>
            )}
          <div className="map-legend">
            <span>LOWER RISK</span><div className="legend-gradient" /><span>HIGHER RISK</span>
            <span className="legend-area">Showing <strong>Rohini · Ward 22</strong></span>
          </div>
          <div className="hotspot-callouts" role="group" aria-label="Three priority hotspots">
            {priorityHotspots.map((feature, index) => (
              <article className="hotspot-callout" key={feature.properties.cell_id}>
                <span className="hotspot-number">{String(index + 1).padStart(2, '0')}</span>
                <span className="hotspot-location">Hotspot {index + 1}<small>Rohini · {feature.geometry.coordinates[1].toFixed(3)}°N</small></span>
                <strong>{feature.properties.risk.toFixed(0)}<small> risk</small></strong>
              </article>
            ))}
          </div>
        </article>
        <article className="panel optimizer-panel">
          <div className="panel-heading">
            <div><span className="card-kicker">INTERVENTION OPTIMIZER</span><h2>Make every rupee count.</h2></div>
            <span className="spark-icon" aria-hidden="true">✳</span>
          </div>
          <p className="panel-description">A suggested mix to reach the most people at risk within your current budget.</p>
          <div className="budget-row"><span>Available budget</span><strong>{plan ? `₹${plan.budget_inr.toLocaleString('en-IN')}` : '—'}</strong></div>
          <div className="intervention-list">
            {(plan?.interventions ?? []).map((intervention) => (
              <div className="intervention-item" key={intervention.name}>
                <span className="intervention-dot" />
                <span className="intervention-name">{intervention.name}<small>{intervention.locations} locations</small></span>
                <strong>₹{intervention.cost_inr.toLocaleString('en-IN')}</strong>
              </div>
            ))}
            {!plan && <p className="loading-copy">Finding the highest-impact mix…</p>}
          </div>
          <div className="optimizer-summary"><span>Estimated people reached</span><strong>{plan ? plan.people_reached.toLocaleString('en-IN') : '—'}</strong></div>
          <NavLink className="primary-button" to="/optimizer">Review recommendations <span aria-hidden="true">→</span></NavLink>
          <p className="optimizer-footnote">Suggestions are planning support; confirm needs on the ground.</p>
        </article>
      </section>
      <p className="data-note">Risk estimates are indicative and may not reflect conditions at every location.</p>
    </PageFrame>
  )
}

const DEFAULT_BOUNDS: BBox = [77.02, 28.69, 77.13, 28.79]
const RESOURCE_TYPES: ResourceType[] = ['water', 'shade', 'cooling']

function RoutePage() {
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [requestNumber, setRequestNumber] = useState(0)

  useEffect(() => {
    let current = true
    postRoute()
      .then((result) => { if (current) setRoute(result) })
      .catch((reason: unknown) => {
        if (current) setError(reason instanceof Error ? reason.message : 'Unexpected response from the route service.')
      })
    return () => { current = false }
  }, [requestNumber])

  return (
    <PageFrame className="route-page-content">
      <PageIntro eyebrow="PERSONAL SAFETY / ROHINI" title={<>Take the <em>cooler way.</em></>} description="Compare the quickest trip with a lower-heat route for your journey." />
      {error && (
        <ErrorBanner
          message={error}
          onRetry={() => {
            setRoute(null)
            setError(null)
            setRequestNumber((value) => value + 1)
          }}
        />
      )}
      <section className="route-cards" aria-label="Route comparisons">
        {(['fastest', 'coolest'] as const).map((kind) => {
          const option = route?.[kind]
          return (
            <article className={`panel route-card route-${kind}`} key={kind}>
              <span className="card-kicker">{kind === 'fastest' ? 'QUICKEST OPTION' : 'LOWER HEAT OPTION'}</span>
              <h2>{kind === 'fastest' ? 'Fastest route' : 'Coolest route'}</h2>
              <div className="route-metrics">
                <Metric label="Travel time" value={option ? option.duration_min.toFixed(1) : '—'} unit=" min" />
                <Metric label="Heat exposure" value={option ? option.exposure.toFixed(0) : '—'} unit=" / 100" tone={kind === 'fastest' ? 'hot' : 'neutral'} />
              </div>
              <p className="route-description">
                {option
                  ? `${option.geometry.coordinates.length} waypoints · ${kind === 'coolest' ? 'Lower estimated exposure, with a small detour.' : 'Direct path to your destination.'}`
                  : 'Loading route options…'}
              </p>
            </article>
          )
        })}
      </section>
      {route && (
        <article className="panel route-map-panel">
          <div className="panel-heading">
            <div><span className="card-kicker">ROUTE COMPARISON / ROHINI</span><h2>Choose your way to Sector 16</h2></div>
            <span className="heatmap-time-chip">DTU · ROHINI</span>
          </div>
          <RouteMap route={route} />
          <div className="route-map-legend" aria-label="Route map legend">
            <span><i className="route-legend-fastest" /> Fastest · {route.fastest.duration_min.toFixed(1)} min</span>
            <span><i className="route-legend-coolest" /> Coolest · {route.coolest.duration_min.toFixed(1)} min</span>
            <span className="route-exposure-note">{route.coolest.exposure.toFixed(0)}% heat exposure on cooler route</span>
          </div>
        </article>
      )}
      <section className="panel route-note">
        <span className="route-start">DTU · ROHINI</span><span className="route-line" aria-hidden="true" /><span className="route-end">SECTOR 16</span>
        <p>Route estimates use the Delhi pilot forecast. Choose the cooler option when conditions feel unsafe.</p>
      </section>
      <button className="primary-button page-action" type="button" onClick={() => { setError(null); setRequestNumber((value) => value + 1) }}>
        Refresh route options <span aria-hidden="true">↻</span>
      </button>
    </PageFrame>
  )
}

function ResourcesPage() {
  const [type, setType] = useState<ResourceType>('water')
  const [result, setResult] = useState<ResourcesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [requestNumber, setRequestNumber] = useState(0)

  useEffect(() => {
    let current = true
    getResources({ type, lat: 28.743, lon: 77.081, radius_m: 5_000 })
      .then((response) => { if (current) setResult(response) })
      .catch((reason: unknown) => {
        if (current) setError(reason instanceof Error ? reason.message : 'Unexpected response from the resources service.')
      })
    return () => { current = false }
  }, [type, requestNumber])

  const resources = result?.resources ?? []

  return (
    <PageFrame>
      <PageIntro eyebrow="LOCAL SUPPORT / ROHINI" title={<>Find a place to <em>cool down.</em></>} description="Nearby water, shade, and cooling resources around the DTU and Rohini pilot area." />
      {error && (
        <ErrorBanner
          message={error}
          onRetry={() => {
            setResult(null)
            setError(null)
            setRequestNumber((value) => value + 1)
          }}
        />
      )}
      <section className="resource-toolbar" aria-label="Filter resources">
        <div className="resource-tabs">
          {RESOURCE_TYPES.map((item) => (
            <button key={item} className={`resource-tab${type === item ? ' selected' : ''}`} type="button" onClick={() => { setError(null); setResult(null); setType(item) }}>
              {resourceLabel(item)}
            </button>
          ))}
        </div>
        <span className="radius-label">Within 5 km of DTU</span>
      </section>
      <section className="resource-layout">
        <article className="panel resource-map-panel">
          <div className="resource-map-art" role="img" aria-label={`Map preview of ${resourceLabel(type).toLowerCase()} resources in Rohini`}>
            <span className="map-road map-road-one" /><span className="map-road map-road-two" /><span className="map-road map-road-three" />
            <span className="map-area-label">ROHINI · DELHI</span>
            <span className="map-origin" title="DTU pilot area">DTU</span>
            {resources.map((resource, index) => <span key={resource.resource_id} className={`resource-pin pin-${index % 4}`} title={resource.name}>●</span>)}
          </div>
          <p className="map-caption">Illustrative pilot-area map · resource availability can change</p>
        </article>
        <section className="resource-list" aria-label="Nearby resources">
          <div className="section-heading"><div><span className="card-kicker">NEAR YOU</span><h2>{result ? resources.length : '…'} {resourceLabel(type).toLowerCase()} points</h2></div></div>
          {result && resources.length === 0 && <p className="empty-state">No {resourceLabel(type).toLowerCase()} resources were found within this radius.</p>}
          {resources.map((resource) => <ResourceCard key={resource.resource_id} resource={resource} />)}
          {!result && !error && <p className="loading-copy">Loading nearby resources…</p>}
        </section>
      </section>
    </PageFrame>
  )
}

function OptimizerPage() {
  const [budget, setBudget] = useState(250_000)
  const [plan, setPlan] = useState<InterventionPlan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [runNumber, setRunNumber] = useState(0)

  useEffect(() => {
    let current = true
    getInterventionPlan({ budget_inr: budget, bbox: DEFAULT_BOUNDS })
      .then((result) => { if (current) setPlan(result) })
      .catch((reason: unknown) => {
        if (current) setError(reason instanceof Error ? reason.message : 'Unexpected response from the optimizer service.')
      })
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [budget, runNumber])

  return (
    <PageFrame>
      <PageIntro eyebrow="CITY OPERATIONS / BUDGET PLANNING" title={<>Put every rupee <em>to work.</em></>} description="Rank heat hotspots and explore an intervention mix for the available budget." />
      {error && (
        <ErrorBanner
          message={error}
          onRetry={() => {
            setPlan(null)
            setError(null)
            setLoading(true)
            setRunNumber((value) => value + 1)
          }}
        />
      )}
      <section className="optimizer-page-grid">
        <article className="panel budget-panel">
          <span className="card-kicker">PLANNING INPUT</span>
          <label htmlFor="budget-inr">Available budget (INR)</label>
          <input id="budget-inr" type="number" min="1" max="1000000000" step="10000" value={budget} onChange={(event) => { setError(null); setLoading(true); setBudget(Math.max(1, Number(event.target.value))) }} />
          <input aria-label="Budget slider" type="range" min="50000" max="1000000" step="10000" value={Math.min(1_000_000, Math.max(50_000, budget))} onChange={(event) => { setError(null); setLoading(true); setBudget(Number(event.target.value)) }} />
          <p>Recommendations prioritize population exposure and estimated heat-risk reduction across Rohini.</p>
          <button className="primary-button" type="button" onClick={() => { setError(null); setLoading(true); setRunNumber((value) => value + 1) }} disabled={loading}>
            {loading ? 'Optimizing…' : 'Recalculate plan'} <span aria-hidden="true">→</span>
          </button>
        </article>
        <article className="panel optimizer-results">
          <div className="panel-heading"><div><span className="card-kicker">RECOMMENDED MIX</span><h2>Interventions with impact</h2></div><span className="spark-icon" aria-hidden="true">✳</span></div>
          {plan ? (
            <>
              <div className="optimizer-summary"><span>Estimated people reached</span><strong>{plan.people_reached.toLocaleString('en-IN')}</strong></div>
              <div className="optimizer-summary"><span>Expected risk reduction</span><strong>{plan.expected_risk_reduction.toFixed(1)} pts</strong></div>
              <div className="intervention-list">
                {plan.interventions.map((item) => (
                  <div className="intervention-item" key={item.name}>
                    <span className="intervention-dot" /><span className="intervention-name">{item.name}<small>{item.locations} locations</small></span>
                    <strong>₹{item.cost_inr.toLocaleString('en-IN')}</strong>
                  </div>
                ))}
              </div>
              <p className="optimizer-footnote">Planned spend: ₹{plan.total_cost_inr.toLocaleString('en-IN')} of ₹{plan.budget_inr.toLocaleString('en-IN')}</p>
            </>
          ) : <p className="loading-copy">{loading ? 'Finding the highest-impact mix…' : 'No recommendations available.'}</p>}
        </article>
      </section>
      <section className="panel hotspot-table">
        <div className="panel-heading"><div><span className="card-kicker">RANKED HOTSPOTS</span><h2>Priority locations</h2></div></div>
        {plan?.ranked_hotspots.map((hotspot) => (
          <div className="hotspot-row" key={hotspot.cell_id}>
            <span className="hotspot-rank">#{hotspot.rank}</span><strong>{hotspot.cell_id}</strong>
            <span>Risk {hotspot.risk.toFixed(0)}</span><span>{hotspot.population_exposed.toLocaleString('en-IN')} exposed</span>
            <span>{hotspot.interventions.map((item) => `${item.units} × ${resourceLabel(item.intervention)}`).join(', ') || 'No action within budget'}</span>
          </div>
        ))}
      </section>
    </PageFrame>
  )
}

function SimulatorPage() {
  const [baseline, setBaseline] = useState<HeatmapResponse | null>(null)
  const [simulation, setSimulation] = useState<HeatmapResponse | null>(null)
  const [cellId, setCellId] = useState('cell-0-0')
  const [type, setType] = useState<ResourceType>('shade')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [baselineRequest, setBaselineRequest] = useState(0)

  useEffect(() => {
    let current = true
    getHeatmap(DEFAULT_BOUNDS)
      .then((result) => {
        if (current) {
          setBaseline(result)
          setCellId(result.features[0]?.properties.cell_id ?? '')
        }
      })
      .catch((reason: unknown) => {
        if (current) setError(reason instanceof Error ? reason.message : 'Unexpected response from the heatmap service.')
      })
      .finally(() => { if (current) setLoading(false) })
    return () => { current = false }
  }, [baselineRequest])

  async function runSimulation() {
    setError(null)
    setLoading(true)
    try {
      const result = await simulateInterventions({ interventions: [{ cell_id: cellId, type, units: 1 }] })
      setSimulation(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unexpected response from the simulation service.')
    } finally {
      setLoading(false)
    }
  }

  function retry() {
    setError(null)
    if (baseline) {
      setSimulation(null)
      void runSimulation()
      return
    }
    setLoading(true)
    setBaselineRequest((value) => value + 1)
  }

  const selectedBaseline = baseline?.features.find((feature) => feature.properties.cell_id === cellId)
  const selectedSimulation = simulation?.features.find((feature) => feature.properties.cell_id === cellId)

  return (
    <PageFrame>
      <PageIntro eyebrow="CITY OPERATIONS / WHAT-IF" title={<>Test a cooler <em>tomorrow.</em></>} description="Preview how a proposed intervention could change heat-risk estimates at a priority hotspot." />
      {error && <ErrorBanner message={error} onRetry={retry} />}
      <section className="simulator-grid">
        <article className="panel simulation-controls">
          <span className="card-kicker">SCENARIO INPUT</span>
          <label htmlFor="sim-cell">Hotspot</label>
          <select id="sim-cell" value={cellId} onChange={(event) => { setCellId(event.target.value); setSimulation(null) }}>
            {(baseline?.features ?? []).map((feature) => (
              <option key={feature.properties.cell_id} value={feature.properties.cell_id}>{feature.properties.cell_id} · risk {feature.properties.risk}</option>
            ))}
          </select>
          <label htmlFor="sim-type">Intervention</label>
          <select id="sim-type" value={type} onChange={(event) => { setType(event.target.value as ResourceType); setSimulation(null) }}>
            {RESOURCE_TYPES.map((item) => <option key={item} value={item}>{resourceLabel(item)}</option>)}
          </select>
          <button className="primary-button" type="button" onClick={runSimulation} disabled={loading || !cellId}>
            {loading ? 'Cooling hotspot…' : 'Simulate intervention'} <span className={loading ? 'simulation-button-icon is-spinning' : 'simulation-button-icon'} aria-hidden="true">✳</span>
          </button>
        </article>
        <article className="panel simulation-results">
          <div className="panel-heading"><div><span className="card-kicker">RISK SCORE COMPARISON</span><h2>{simulation ? 'Scenario outcome' : 'Baseline conditions'}</h2></div></div>
          <div className="simulation-score-row">
            <Metric label="Before" value={selectedBaseline ? selectedBaseline.properties.risk.toFixed(0) : loading ? '…' : '—'} unit=" / 100" tone="hot" />
            <span className="simulation-arrow" aria-hidden="true">→</span>
            <Metric label="After" value={selectedSimulation ? selectedSimulation.properties.risk.toFixed(0) : '—'} unit=" / 100" tone="neutral" />
          </div>
          {selectedSimulation && selectedBaseline && (
            <p className="simulation-change">Estimated reduction: {(selectedBaseline.properties.risk - selectedSimulation.properties.risk).toFixed(1)} risk points · WBGT {selectedBaseline.properties.wbgt_c}°C → {selectedSimulation.properties.wbgt_c}°C</p>
          )}
          {baseline && <HeatMap data={simulation ?? baseline} coolingCellId={simulation ? cellId : undefined} />}
        </article>
      </section>
    </PageFrame>
  )
}

function PageIntro({ eyebrow, title, description }: { eyebrow: string; title: ReactNode; description: string }) {
  return (
    <section className="page-intro">
      <div className="eyebrow"><span className="live-dot" /> {eyebrow}</div>
      <h1>{title}</h1>
      <p className="lede">{description}</p>
    </section>
  )
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-banner" role="alert">
      <span>Could not load data: {message}</span>
      <button className="error-retry" type="button" onClick={onRetry}>Try again</button>
    </div>
  )
}

function resourceLabel(type: ResourceType): string {
  return type === 'water' ? 'Water' : type === 'shade' ? 'Shade' : 'Cooling'
}

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <article className="resource-card panel">
      <span className={`resource-symbol resource-${resource.type}`} aria-hidden="true">{resource.type === 'water' ? '↟' : resource.type === 'shade' ? '⌂' : '✳'}</span>
      <div><h3>{resource.name}</h3><p>{(resource.distance_m / 1000).toFixed(1)} km away <span>·</span> {resource.availability}</p></div>
      <span className={`availability availability-${resource.availability}`}>{resource.availability}</span>
    </article>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/risk" replace />} />
      <Route path="/risk" element={<WorkerApp />} />
      <Route path="/app" element={<WorkerApp />} />
      <Route path="/route" element={<RoutePage />} />
      <Route path="/resources" element={<ResourcesPage />} />
      <Route path="/city" element={<CityApp />} />
      <Route path="/optimizer" element={<OptimizerPage />} />
      <Route path="/simulator" element={<SimulatorPage />} />
      <Route path="*" element={<Navigate to="/risk" replace />} />
    </Routes>
  )
}

function App() {
  return <BrowserRouter><AppRoutes /></BrowserRouter>
}

export default App
