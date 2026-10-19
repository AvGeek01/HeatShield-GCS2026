import { afterEach, describe, expect, it, vi } from 'vitest'
import type {
  BBox,
  OptimizeRequest,
  ResourceRequest,
  RiskRequest,
  RouteRequest,
  SimulateRequest,
} from './types'

const fetchMock = vi.fn()

async function loadClientWithFetch() {
  vi.stubEnv('VITE_USE_MOCK_API', 'false')
  vi.stubEnv('VITE_API_BASE_URL', 'https://heatshield.test')
  vi.stubGlobal('fetch', fetchMock)
  vi.resetModules()
  return import('./client')
}

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.resetModules()
  fetchMock.mockReset()
})

describe('typed API client', () => {
  it('requests risk with all documented query parameters', async () => {
    fetchMock.mockResolvedValue(new Response('{}'))
    const client = await loadClientWithFetch()
    const params: RiskRequest = {
      lat: 28.743,
      lon: 77.081,
      activity: 'walking',
      duration_min: 30,
      profile: 'general',
    }

    await client.getRiskAssessment(params)

    expect(fetchMock).toHaveBeenCalledWith(
      'https://heatshield.test/api/risk?lat=28.743&lon=77.081&activity=walking&duration_min=30&profile=general',
      expect.objectContaining({ headers: { Accept: 'application/json' } }),
    )
  })

  it('requests heatmap with a serialized bbox and timestamp', async () => {
    fetchMock.mockResolvedValue(new Response('{}'))
    const client = await loadClientWithFetch()
    const bbox: BBox = [77.02, 28.69, 77.13, 28.79]

    await client.getHeatmap(bbox, 'latest')

    expect(fetchMock).toHaveBeenCalledWith(
      'https://heatshield.test/api/heatmap?bbox=77.02%2C28.69%2C77.13%2C28.79&ts=latest',
      expect.any(Object),
    )
  })

  it('posts route and optimization requests to their documented paths', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response('{}'))
      .mockResolvedValueOnce(new Response('{}'))
    const client = await loadClientWithFetch()
    const route: RouteRequest = {
      origin: { lat: 28.743, lon: 77.081 },
      dest: { lat: 28.747, lon: 77.112 },
      activity: 'walking',
    }
    const optimize: OptimizeRequest = { budget_inr: 250_000, bbox: [77.02, 28.69, 77.13, 28.79] }

    await client.postRoute(route)
    await client.getInterventionPlan(optimize)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'https://heatshield.test/api/route',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(route) }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'https://heatshield.test/api/optimize',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(optimize) }),
    )
  })

  it('requests resources with the required type and coordinates', async () => {
    fetchMock.mockResolvedValue(new Response('{}'))
    const client = await loadClientWithFetch()
    const params: ResourceRequest = {
      type: 'shade',
      lat: 28.743,
      lon: 77.081,
      radius_m: 2_000,
    }

    await client.getResources(params)

    expect(fetchMock).toHaveBeenCalledWith(
      'https://heatshield.test/api/resources?type=shade&lat=28.743&lon=77.081&radius_m=2000',
      expect.any(Object),
    )
  })

  it('posts interventions to the simulation endpoint', async () => {
    fetchMock.mockResolvedValue(new Response('{}'))
    const client = await loadClientWithFetch()
    const params: SimulateRequest = {
      interventions: [{ cell_id: 'delhi:v1:0:0:77.02:28.69:77.13:28.79', type: 'shade', units: 1 }],
    }

    await client.simulateInterventions(params)

    expect(fetchMock).toHaveBeenCalledWith(
      'https://heatshield.test/api/simulate',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(params) }),
    )
  })
})
