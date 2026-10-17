import { mockHeatmap, mockInterventionPlan, mockRiskAssessment } from './mock'
import type { HeatmapResponse, InterventionPlan, RiskAssessment } from './types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
export const isMockMode = import.meta.env.VITE_USE_MOCK_API === 'true'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(15000),
    headers: { Accept: 'application/json', ...init?.headers },
  })

  if (!response.ok) {
    throw new Error(`Request failed (${response.status} ${response.statusText})`)
  }

  return response.json() as Promise<T>
}

export function getRiskAssessment(): Promise<RiskAssessment> {
  if (isMockMode) return Promise.resolve(mockRiskAssessment)
  return request<RiskAssessment>('/api/risk?lat=28.743&lon=77.081&activity=outdoor_work&duration_min=240&profile=worker')
}

export function getHeatmap(): Promise<HeatmapResponse> {
  if (isMockMode) return Promise.resolve(mockHeatmap)
  return request<HeatmapResponse>('/api/heatmap?bbox=77.02,28.69,77.13,28.79&ts=latest')
}

export function getInterventionPlan(): Promise<InterventionPlan> {
  if (isMockMode) return Promise.resolve(mockInterventionPlan)
  return request<InterventionPlan>('/api/interventions/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bbox: '77.02,28.69,77.13,28.79', budget_inr: 250000 }),
  })
}
