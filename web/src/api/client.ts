import {
  getMockInterventionPlan,
  getMockResources,
  getMockSimulation,
  mockHeatmap,
  mockRiskAssessment,
  mockRoute,
} from './mock'
import type {
  BBox,
  HeatmapResponse,
  InterventionPlan,
  OptimizeRequest,
  ResourceRequest,
  ResourcesResponse,
  RiskAssessment,
  RiskRequest,
  RouteRequest,
  RouteResponse,
  SimulateRequest,
} from './types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
export const isMockMode = import.meta.env.VITE_USE_MOCK_API === 'true'

const defaultRiskRequest: RiskRequest = {
  lat: 28.743,
  lon: 77.081,
  activity: 'outdoor_work',
  duration_min: 240,
  profile: 'outdoor_worker',
}
const defaultBounds: BBox = [77.02, 28.69, 77.13, 28.79]
const defaultRouteRequest: RouteRequest = {
  origin: { lat: 28.743, lon: 77.081 },
  dest: { lat: 28.747, lon: 77.112 },
  activity: 'walking',
}
const defaultResourcesRequest: ResourceRequest = {
  type: 'water',
  lat: 28.743,
  lon: 77.081,
  radius_m: 5_000,
}
const defaultOptimizeRequest: OptimizeRequest = { budget_inr: 250_000, bbox: defaultBounds }
const defaultSimulateRequest: SimulateRequest = {
  interventions: [{ cell_id: 'delhi:v1:0:0:77.02:28.69:77.13:28.79', type: 'shade', units: 1 }],
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(15_000),
    headers: { Accept: 'application/json', ...init?.headers },
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Request failed (${response.status} ${response.statusText})${detail ? `: ${detail}` : ''}`)
  }

  return response.json() as Promise<T>
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function getRiskAssessment(params: RiskRequest = defaultRiskRequest): Promise<RiskAssessment> {
  if (isMockMode) return Promise.resolve(mockRiskAssessment)
  const query = new URLSearchParams({
    lat: String(params.lat),
    lon: String(params.lon),
    activity: params.activity,
    duration_min: String(params.duration_min),
    profile: params.profile,
  })
  return request<RiskAssessment>(`/api/risk?${query}`)
}

export function getHeatmap(bbox: BBox = defaultBounds, ts = 'latest'): Promise<HeatmapResponse> {
  if (isMockMode) return Promise.resolve(mockHeatmap)
  const query = new URLSearchParams({ bbox: bbox.join(','), ts })
  return request<HeatmapResponse>(`/api/heatmap?${query}`)
}

export function postRoute(params: RouteRequest = defaultRouteRequest): Promise<RouteResponse> {
  if (isMockMode) return Promise.resolve(mockRoute)
  return postJson<RouteResponse>('/api/route', params)
}

export function getResources(params: ResourceRequest = defaultResourcesRequest): Promise<ResourcesResponse> {
  if (isMockMode) return Promise.resolve(getMockResources(params.type, params.lat, params.lon, params.radius_m))
  const query = new URLSearchParams({
    type: params.type,
    lat: String(params.lat),
    lon: String(params.lon),
    radius_m: String(params.radius_m),
  })
  return request<ResourcesResponse>(`/api/resources?${query}`)
}

export function getInterventionPlan(params: OptimizeRequest = defaultOptimizeRequest): Promise<InterventionPlan> {
  if (isMockMode) return Promise.resolve(getMockInterventionPlan(params.budget_inr))
  return postJson<InterventionPlan>('/api/optimize', params)
}

export function simulateInterventions(params: SimulateRequest = defaultSimulateRequest): Promise<HeatmapResponse> {
  if (isMockMode) return Promise.resolve(getMockSimulation(params))
  return postJson<HeatmapResponse>('/api/simulate', params)
}
