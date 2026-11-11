import mockData from './mock-data.json'
import type {
  HeatmapResponse,
  InterventionPlan,
  Resource,
  ResourcesResponse,
  RiskAssessment,
  RouteResponse,
  SimulateRequest,
} from './types'

export const mockRiskAssessment = mockData.risk as RiskAssessment
export const mockHeatmap = mockData.heatmap as HeatmapResponse
export const mockRoute = mockData.route as RouteResponse
export const mockInterventionPlan = mockData.optimize as InterventionPlan
const mockResources = mockData.resources as Resource[]

export function getMockHeatmapAtTime(timestamp: string): HeatmapResponse {
  const hour = Number(timestamp.slice(0, 2))
  const timeProgress = Math.max(0, Math.min(1, (hour - 10) / 3))
  const riskReduction = (1 - timeProgress) * 20
  const temperatureReduction = (1 - timeProgress) * 2.4
  const wbgtReduction = (1 - timeProgress) * 1.8

  return {
    ...mockHeatmap,
    features: mockHeatmap.features.map((feature) => ({
      ...feature,
      properties: {
        ...feature.properties,
        risk: Math.max(0, Math.round(feature.properties.risk - riskReduction)),
        temp_c: Number((feature.properties.temp_c - temperatureReduction).toFixed(1)),
        wbgt_c: Number((feature.properties.wbgt_c - wbgtReduction).toFixed(1)),
      },
    })),
  }
}

export function getMockInterventionPlan(budget: number): InterventionPlan {
  let remaining = budget
  const ranked_hotspots = mockInterventionPlan.ranked_hotspots.map((hotspot) => {
    const affordableInterventions = hotspot.interventions.filter((item) => item.cost_inr <= remaining)
    const selected = affordableInterventions.slice(0, 1)
    if (selected[0]) remaining -= selected[0].cost_inr
    return { ...hotspot, interventions: selected }
  })
  const selectedItems = ranked_hotspots.flatMap((hotspot) => hotspot.interventions)
  const summaries = new Map<string, { name: string; locations: number; cost_inr: number }>()
  const interventionNames = {
    shade: 'Temporary shade points',
    water: 'Water refill stations',
    cooling: 'Cooling centers',
  }
  for (const item of selectedItems) {
    const summary = summaries.get(item.intervention) ?? {
      name: interventionNames[item.intervention],
      locations: 0,
      cost_inr: 0,
    }
    summary.locations += item.units
    summary.cost_inr += item.cost_inr
    summaries.set(item.intervention, summary)
  }
  return {
    ...mockInterventionPlan,
    ranked_hotspots,
    budget_inr: budget,
    total_cost_inr: selectedItems.reduce((total, item) => total + item.cost_inr, 0),
    expected_risk_reduction: Number(selectedItems.reduce((total, item) => total + item.expected_risk_reduction, 0).toFixed(1)),
    people_reached: ranked_hotspots
      .filter((hotspot) => hotspot.interventions.length > 0)
      .reduce((total, hotspot) => total + hotspot.population_exposed, 0),
    interventions: [...summaries.values()],
  }
}

function distanceInMeters(from: { lat: number; lon: number }, to: { lat: number; lon: number }): number {
  const radians = (degrees: number) => (degrees * Math.PI) / 180
  const latDelta = radians(to.lat - from.lat)
  const lonDelta = radians(to.lon - from.lon)
  const arc =
    Math.sin(latDelta / 2) ** 2 +
    Math.cos(radians(from.lat)) * Math.cos(radians(to.lat)) * Math.sin(lonDelta / 2) ** 2
  return 6_371_000 * 2 * Math.atan2(Math.sqrt(arc), Math.sqrt(1 - arc))
}

export function getMockResources(
  type: Resource['type'],
  lat: number,
  lon: number,
  radius_m: number,
): ResourcesResponse {
  return {
    resources: mockResources
      .filter((resource) => resource.type === type)
      .map((resource) => ({
        ...resource,
        distance_m: Math.round(distanceInMeters({ lat, lon }, resource.location)),
      }))
      .filter((resource) => resource.distance_m <= radius_m),
  }
}

export function getMockSimulation({ interventions }: SimulateRequest): HeatmapResponse {
  const reductions = new Map<string, number>()
  const temperatureReductions = new Map<string, number>()
  const wbgtReductions = new Map<string, number>()
  for (const intervention of interventions) {
    const reduction = intervention.type === 'cooling' ? 14 : intervention.type === 'shade' ? 10 : 6
    const temperatureReduction = intervention.type === 'cooling' ? 2 : intervention.type === 'shade' ? 1.2 : 0.7
    const wbgtReduction = intervention.type === 'cooling' ? 1.5 : intervention.type === 'shade' ? 0.8 : 0.5
    reductions.set(
      intervention.cell_id,
      (reductions.get(intervention.cell_id) ?? 0) + reduction * intervention.units,
    )
    temperatureReductions.set(
      intervention.cell_id,
      (temperatureReductions.get(intervention.cell_id) ?? 0) + temperatureReduction * intervention.units,
    )
    wbgtReductions.set(
      intervention.cell_id,
      (wbgtReductions.get(intervention.cell_id) ?? 0) + wbgtReduction * intervention.units,
    )
  }

  return {
    ...mockHeatmap,
    features: mockHeatmap.features.map((feature) => {
      const reduction = reductions.get(feature.properties.cell_id) ?? 0
      const temperatureReduction = temperatureReductions.get(feature.properties.cell_id) ?? 0
      const wbgtReduction = wbgtReductions.get(feature.properties.cell_id) ?? 0
      const risk = Math.max(0, feature.properties.risk - reduction)
      return {
        ...feature,
        properties: {
          ...feature.properties,
          risk,
          temp_c: Number((feature.properties.temp_c - temperatureReduction).toFixed(1)),
          wbgt_c: Number((feature.properties.wbgt_c - wbgtReduction).toFixed(1)),
        },
      }
    }),
  }
}
