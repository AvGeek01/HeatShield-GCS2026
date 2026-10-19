import type { FeatureCollection, LineString, Point } from 'geojson'

export type RiskLevel = 'low' | 'moderate' | 'high' | 'extreme'
export type Activity = 'walking' | 'commuting' | 'cycling' | 'running' | 'outdoor_work' | 'resting'
export type RiskProfile = 'general' | 'child' | 'older_adult' | 'outdoor_worker' | 'chronic_condition' | 'worker'
export type ResourceType = 'water' | 'shade' | 'cooling'
export type BBox = [number, number, number, number]

export interface RiskRequest {
  lat: number
  lon: number
  activity: Activity
  duration_min: number
  profile: RiskProfile
}

export interface RiskAssessment {
  risk_score: number
  level: RiskLevel
  wbgt_c: number
  factors: string[]
  actions: string[]
}

export interface HeatmapProperties {
  cell_id: string
  risk: number
  temp_c: number
  wbgt_c: number
  population_exposed: number
}

export type HeatmapResponse = FeatureCollection<Point, HeatmapProperties>

export interface Location {
  lat: number
  lon: number
}

export interface RouteRequest {
  origin: Location
  dest: Location
  activity: Activity
}

export interface RouteOption {
  geometry: LineString
  duration_min: number
  exposure: number
}

export interface RouteResponse {
  fastest: RouteOption
  coolest: RouteOption
}

export interface Resource {
  resource_id: string
  type: ResourceType
  name: string
  location: Location
  distance_m: number
  availability: 'open' | 'limited' | 'unknown'
}

export interface ResourcesResponse {
  resources: Resource[]
}

export interface ResourceRequest {
  type: ResourceType
  lat: number
  lon: number
  radius_m: number
}

export interface Intervention {
  cell_id: string
  type: ResourceType
  units: number
}

export interface InterventionPlanItem {
  intervention: ResourceType
  units: number
  cost_inr: number
  expected_risk_reduction: number
}

export interface RankedHotspot {
  rank: number
  cell_id: string
  risk: number
  population_exposed: number
  interventions: InterventionPlanItem[]
}

export interface InterventionSummary {
  name: string
  locations: number
  cost_inr: number
}

export interface InterventionPlan {
  ranked_hotspots: RankedHotspot[]
  total_cost_inr: number
  expected_risk_reduction: number
  budget_inr: number
  people_reached: number
  population_exposed: number
  interventions: InterventionSummary[]
}

export interface OptimizeRequest {
  budget_inr: number
  bbox: BBox
}

export interface SimulateRequest {
  interventions: Intervention[]
}
