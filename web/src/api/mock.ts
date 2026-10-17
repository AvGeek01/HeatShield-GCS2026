import type { HeatmapResponse, InterventionPlan, RiskAssessment } from './types'

export const mockRiskAssessment: RiskAssessment = {
  risk_score: 78,
  level: 'high',
  wbgt_c: 32.4,
  factors: ['High afternoon temperature', 'Limited shade'],
  actions: [
    'Take a water break before your next shift.',
    'Plan the heaviest work before 11 AM.',
    'Rest in shade for 10 minutes every hour.',
  ],
}

export const mockHeatmap: HeatmapResponse = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.081, 28.743] }, properties: { risk: 88, temp_c: 39.1, wbgt_c: 33.2, population_exposed: 1480 } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.096, 28.752] }, properties: { risk: 72, temp_c: 38.4, wbgt_c: 31.8, population_exposed: 920 } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.067, 28.735] }, properties: { risk: 57, temp_c: 37.6, wbgt_c: 30.4, population_exposed: 640 } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.105, 28.728] }, properties: { risk: 81, temp_c: 39.0, wbgt_c: 32.7, population_exposed: 1140 } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.055, 28.756] }, properties: { risk: 44, temp_c: 36.8, wbgt_c: 29.6, population_exposed: 510 } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [77.088, 28.721] }, properties: { risk: 67, temp_c: 38.0, wbgt_c: 31.1, population_exposed: 780 } },
  ],
}

export const mockInterventionPlan: InterventionPlan = {
  budget_inr: 250000,
  people_reached: 4820,
  population_exposed: 12640,
  interventions: [
    { name: 'Temporary shade points', locations: 8, cost_inr: 92000 },
    { name: 'Water refill stations', locations: 5, cost_inr: 78500 },
    { name: 'Community heat alerts', locations: 12, cost_inr: 54000 },
  ],
}
