import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { mockHeatmap, mockInterventionPlan, mockRiskAssessment } from './api/mock'

vi.mock('./api/client', () => ({
  getHeatmap: vi.fn(() => Promise.resolve(mockHeatmap)),
  getInterventionPlan: vi.fn(() => Promise.resolve(mockInterventionPlan)),
  getRiskAssessment: vi.fn(() => Promise.resolve(mockRiskAssessment)),
  isMockMode: true,
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
  })

  it('renders the city dashboard at /city', async () => {
    window.history.replaceState({}, '', '/city')
    render(<App />)

    expect(screen.getByRole('heading', { name: /see where heat hits hardest/i })).toBeInTheDocument()
    expect(await screen.findByRole('img', { name: /map of heat risk hotspots/i })).toBeInTheDocument()
    expect(screen.getByText('Temporary shade points')).toBeInTheDocument()
  })
})
