import type { FeatureCollection, Point } from 'geojson'

export type RiskLevel = 'low' | 'moderate' | 'high' | 'extreme'

export interface RiskAssessment {
  risk_score: number
  level: RiskLevel
  wbgt_c: number
  factors: string[]
  actions: string[]
}

export interface HeatmapProperties {
  risk: number
  temp_c: number
  wbgt_c: number
  population_exposed: number
}

export type HeatmapResponse = FeatureCollection<Point, HeatmapProperties>

export interface Intervention {
  name: string
  locations: number
  cost_inr: number
}

export interface InterventionPlan {
  budget_inr: number
  people_reached: number
  population_exposed: number
  interventions: Intervention[]
}
