import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { getRiskAssessment } from './api/client'
import {
  getMockSimulation,
  mockHeatmap,
  mockInterventionPlan,
  mockRiskAssessment,
  mockRoute,
} from './api/mock'

vi.mock('./api/client', () => ({
  getHeatmap: vi.fn(() => Promise.resolve(mockHeatmap)),
  getInterventionPlan: vi.fn(() => Promise.resolve(mockInterventionPlan)),
  getResources: vi.fn(() => Promise.resolve({
    resources: [{
      resource_id: 'water-rohini-01',
      type: 'water',
      name: 'Rohini Community Water Point',
      location: { lat: 28.751, lon: 77.116 },
      distance_m: 1200,
      availability: 'open',
    }],
  })),
  getRiskAssessment: vi.fn(() => Promise.resolve(mockRiskAssessment)),
  postRoute: vi.fn(() => Promise.resolve(mockRoute)),
  isMockMode: true,
  simulateInterventions: vi.fn(() => Promise.resolve(getMockSimulation({
    interventions: [{ cell_id: 'delhi:v1:0:0:77.02:28.69:77.13:28.79', type: 'shade', units: 1 }],
  }))),
}))

vi.mock('maplibre-gl', () => {
  class MockMap {
    on() { return this }
    addSource() {}
    addLayer() {}
    remove() {}
  }
  return { Map: MockMap }
})

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
})

describe('HeatShield routes', () => {
  it('renders the worker app at /app', async () => {
    window.history.replaceState({}, '', '/app')
    render(<App />)

    expect(screen.getByRole('heading', { name: /make today a safer day/i })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('High risk')).toBeInTheDocument())
    expect(screen.getByText('Take a water break before your next shift.')).toBeInTheDocument()
    expect(screen.getByText('Mock data')).toBeInTheDocument()
  })

  it('shows a visible API error and retries the request', async () => {
    window.history.replaceState({}, '', '/risk')
    vi.mocked(getRiskAssessment).mockRejectedValueOnce(new Error('API unavailable'))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('API unavailable')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('High risk')).toBeInTheDocument()
  })

  it('renders the city dashboard at /city', async () => {
    window.history.replaceState({}, '', '/city')
    render(<App />)

    expect(screen.getByRole('heading', { name: /see where heat hits hardest/i })).toBeInTheDocument()
    expect(await screen.findByRole('img', { name: /map of heat risk hotspots/i })).toBeInTheDocument()
    expect(screen.getByText('Temporary shade points')).toBeInTheDocument()
  })

  it('renders the heat-safe route page from mock route data', async () => {
    window.history.replaceState({}, '', '/route')
    render(<App />)

    expect(await screen.findByRole('heading', { name: /take the cooler way/i })).toBeInTheDocument()
    expect(screen.getByText('18.4')).toBeInTheDocument()
  })

  it('renders the resources map with local resources', async () => {
    window.history.replaceState({}, '', '/resources')
    render(<App />)

    expect(await screen.findByRole('heading', { name: /find a place to cool down/i })).toBeInTheDocument()
    expect(screen.getByText('Rohini Community Water Point')).toBeInTheDocument()
  })

  it('renders the optimizer with ranked hotspots', async () => {
    window.history.replaceState({}, '', '/optimizer')
    render(<App />)

    expect(await screen.findByRole('heading', { name: /put every rupee to work/i })).toBeInTheDocument()
    expect(await screen.findByText('delhi:v1:0:0:77.02:28.69:77.13:28.79')).toBeInTheDocument()
  })

  it('runs a simulation using the selected heatmap cell', async () => {
    window.history.replaceState({}, '', '/simulator')
    render(<App />)

    expect(await screen.findByRole('heading', { name: /test a cooler tomorrow/i })).toBeInTheDocument()
    screen.getByRole('button', { name: /run simulation/i }).click()
    expect(await screen.findByText(/estimated reduction: 10.0 risk points/i)).toBeInTheDocument()
  })

  it.each([
    ['Risk Card', /make today a safer day/i],
    ['Heat-Safe Route', /take the cooler way/i],
    ['Resources Map', /find a place to cool down/i],
    ['City Heatmap', /see where heat hits hardest/i],
    ['Optimizer', /put every rupee to work/i],
    ['Simulator', /test a cooler tomorrow/i],
  ])('opens the %s page when its nav tab is clicked', async (label, heading) => {
    window.history.replaceState({}, '', '/simulator')
    render(<App />)

    fireEvent.click(screen.getByRole('link', { name: label }))

    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
  })
})
