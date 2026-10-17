import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import type { FeatureCollection, Point } from 'geojson'
import {
  getHeatmap,
  getInterventionPlan,
  getRiskAssessment,
  isMockMode,
} from './api/client'
import type { HeatmapProperties, InterventionPlan, RiskAssessment } from './api/types'
import './App.css'

function Brand() {
  return (
    <NavLink className="brand" to="/app" aria-label="HeatShield home">
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
        <NavLink to="/app" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
          For workers
        </NavLink>
        <NavLink to="/city" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
          For cities
        </NavLink>
      </nav>
      <div className="topbar-actions">
        {isMockMode && <span className="mode-pill"><span /> Demo data</span>}
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

function PageFrame({ children }: { children: ReactNode }) {
  return (
    <>
      <AppHeader />
      <main className="page-content">{children}</main>
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

  useEffect(() => {
    let current = true
    getRiskAssessment()
      .then((result) => { if (current) setAssessment(result) })
      .catch((reason: Error) => { if (current) setError(reason.message) })
    return () => { current = false }
  }, [])

  return (
    <PageFrame>
      <section className="worker-layout">
        <div className="worker-main">
          <div className="eyebrow"><span className="live-dot" /> YOUR HEAT CHECK <span className="eyebrow-divider">/</span> TODAY, 18 OCT</div>
          <div className="worker-heading">
            <div>
              <h1>Make today a <em>safer</em> day.</h1>
              <p className="lede">A little planning goes a long way in the heat.</p>
            </div>
            <span className="weather-chip"><span aria-hidden="true">☀</span> Mostly sunny <b>38°</b></span>
          </div>

          {error && <p className="error-banner" role="alert">Could not load today’s heat check: {error}</p>}
          <section className="risk-card" aria-label="Your heat risk">
            <div className="risk-card-top">
              <div>
                <span className="card-kicker">YOUR HEAT RISK</span>
                <h2>{assessment ? `${assessment.level[0].toUpperCase()}${assessment.level.slice(1)} risk` : 'Loading your forecast'}</h2>
                <p>Rohini, Delhi <span className="muted-separator">·</span> Updated just now</p>
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
              <Metric label="Feels like" value={assessment ? `${assessment.wbgt_c}°` : '—'} unit=" WBGT" tone="hot" />
              <Metric label="Peak heat" value="1–4" unit=" PM" tone="warm" />
              <Metric label="Best break" value="12:30" unit=" PM" />
            </div>
          </section>

          <section className="actions-section">
            <div className="section-heading">
              <div><span className="card-kicker">A PLAN THAT HELPS</span><h2>Your next steps</h2></div>
              <span className="action-count">{assessment?.actions.length ?? 3} actions</span>
            </div>
            <div className="action-list">
              {(assessment?.actions ?? [
                'Take a water break before your next shift.',
                'Plan the heaviest work before 11 AM.',
                'Rest in shade for 10 minutes every hour.',
              ]).map((action, index) => (
                <article className="action-item" key={action}>
                  <span className={`action-number action-${index + 1}`}>0{index + 1}</span>
                  <p>{action}</p>
                  <span className="action-arrow" aria-hidden="true">↗</span>
                </article>
              ))}
            </div>
          </section>
        </div>

        <aside className="worker-aside">
          <div className="aside-label">HEAT, IN CONTEXT</div>
          <div className="shade-card">
            <div className="shade-graphic" aria-hidden="true">
              <span className="sun-orb" />
              <span className="shade-line shade-line-one" />
              <span className="shade-line shade-line-two" />
              <span className="shade-line shade-line-three" />
            </div>
            <div className="shade-copy">
              <span className="card-kicker">A MOMENT TO RESET</span>
              <h3>Find a cooler<br />place to pause.</h3>
              <p>Water and shade can make a real difference. Check in with yourself and your team.</p>
            </div>
          </div>
          <div className="tip-card">
            <span className="tip-icon" aria-hidden="true">✳</span>
            <div><span className="card-kicker">HEAT SMART</span><p>Feeling dizzy or unusually tired? Stop work, move to shade, and tell someone nearby.</p></div>
          </div>
          <p className="disclaimer">HeatShield guidance supports—not replaces—local health advice.</p>
        </aside>
      </section>
    </PageFrame>
  )
}

function HeatMap({ data }: { data: FeatureCollection<Point, HeatmapProperties> }) {
  const [mapElement, setMapElement] = useState<HTMLDivElement | null>(null)
  const [mapError, setMapError] = useState<string | null>(null)

  useEffect(() => {
    if (!mapElement) return

    let map: import('maplibre-gl').Map | undefined
    let cancelled = false

    import('maplibre-gl')
      .then(({ Map: MapLibreMap }) => {
        if (cancelled) return
        map = new MapLibreMap({
          container: mapElement,
          center: [77.081, 28.743],
          zoom: 12,
          minZoom: 10,
          maxZoom: 15,
          attributionControl: { compact: true },
          style: {
            version: 8,
            sources: {
              streets: {
                type: 'raster',
                tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                tileSize: 256,
                attribution: '© OpenStreetMap contributors',
              },
            },
            layers: [
              { id: 'streets', type: 'raster', source: 'streets', paint: { 'raster-saturation': -0.8, 'raster-opacity': 0.75 } },
            ],
          },
        })

        map.on('load', () => {
          map?.addSource('heat-risk', { type: 'geojson', data })
          map?.addLayer({
            id: 'heat-risk-circles',
            type: 'circle',
            source: 'heat-risk',
            paint: {
              'circle-color': ['interpolate', ['linear'], ['get', 'risk'], 0, '#2f855a', 40, '#d69e2e', 65, '#e77931', 85, '#a82a2a'],
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 10, 15, 25],
              'circle-opacity': 0.72,
              'circle-stroke-width': 2,
              'circle-stroke-color': '#fffdf8',
            },
          })
        })
      })
      .catch((reason: Error) => {
        if (!cancelled) setMapError(reason.message)
      })

    return () => {
      cancelled = true
      map?.remove()
    }
  }, [data, mapElement])

  return (
    <div className="map-view" ref={setMapElement} role="img" aria-label="Map of heat risk hotspots in Rohini, Delhi">
      {mapError && <span className="map-error">Map unavailable: {mapError}</span>}
    </div>
  )
}

function CityApp() {
  const [heatmap, setHeatmap] = useState<FeatureCollection<Point, HeatmapProperties> | null>(null)
  const [heatmapLoading, setHeatmapLoading] = useState(true)
  const [heatmapError, setHeatmapError] = useState<string | null>(null)
  const [plan, setPlan] = useState<InterventionPlan | null>(null)
  const [planError, setPlanError] = useState<string | null>(null)
  const [heatmapRequest, setHeatmapRequest] = useState(0)

  useEffect(() => {
    let current = true
    getHeatmap()
      .then((result) => { if (current) setHeatmap(result) })
      .catch((reason: unknown) => {
        if (current) setHeatmapError(reason instanceof Error ? reason.message : 'Unexpected response from the heatmap service.')
      })
      .finally(() => { if (current) setHeatmapLoading(false) })

    getInterventionPlan()
      .then((result) => { if (current) setPlan(result) })
      .catch((reason: unknown) => {
        if (current) setPlanError(reason instanceof Error ? reason.message : 'Unexpected response from the optimizer service.')
      })

    return () => { current = false }
  }, [heatmapRequest])

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
      {planError && <p className="error-banner" role="alert">Could not load intervention recommendations: {planError}</p>}
      <section className="city-metrics" aria-label="City heat metrics">
        <Metric label="People at high risk" value={plan ? plan.population_exposed.toLocaleString('en-IN') : '—'} tone="hot" />
        <Metric label="Priority hotspots" value={heatmap ? String(heatmap.features.filter((feature) => feature.properties.risk >= 65).length).padStart(2, '0') : '—'} tone="warm" />
        <Metric label="Interventions ready" value={plan ? String(plan.interventions.length).padStart(2, '0') : '—'} />
        <div className="metric-note"><span className="live-dot" /><span>Forecast refreshed<br /><strong>Today, 9:40 AM</strong></span></div>
      </section>
      <section className="city-grid">
        <article className="panel map-panel">
          <div className="panel-heading">
            <div><span className="card-kicker">NEIGHBOURHOOD VIEW</span><h2>Rohini heat map</h2></div>
            <button className="small-select" type="button">Heat risk <span aria-hidden="true">⌄</span></button>
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
                          setHeatmapLoading(true)
                          setHeatmapRequest((request) => request + 1)
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
          <button className="primary-button" type="button">Review recommendations <span aria-hidden="true">→</span></button>
          <p className="optimizer-footnote">Suggestions are planning support; confirm needs on the ground.</p>
        </article>
      </section>
      <p className="data-note">Risk estimates are indicative and may not reflect conditions at every location.</p>
    </PageFrame>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<WorkerApp />} />
      <Route path="/city" element={<CityApp />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  )
}

function App() {
  return <BrowserRouter><AppRoutes /></BrowserRouter>
}

export default App
