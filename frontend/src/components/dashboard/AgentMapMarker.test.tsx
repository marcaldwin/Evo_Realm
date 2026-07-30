import {
  act,
  fireEvent,
  render,
  screen,
} from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type {
  AgentSummary,
  LocationSummary,
} from '../../types/world'
import { AgentMapMarker } from './AgentMapMarker'
import {
  buildTilePath,
  getMovementDirection,
} from './agentMovement'

const agent: AgentSummary = {
  id: 'elena',
  name: 'Elena',
  occupation: 'farmer',
  location_id: 'farm',
  status: 'idle',
  hunger: 20,
  energy: 80,
  health: 100,
  money: 5,
  inventory: {},
}

const farm: LocationSummary = {
  id: 'farm',
  name: 'North Farm',
  location_type: 'farm',
  x: 1,
  y: 1,
  capacity: 10,
  inventory: {},
}

describe('getMovementDirection', () => {
  it('uses the dominant coordinate change', () => {
    expect(getMovementDirection(
      { x: 1, y: 1 },
      { x: 4, y: 2 },
    )).toBe('right')
    expect(getMovementDirection(
      { x: 4, y: 3 },
      { x: 4, y: 1 },
    )).toBe('up')
  })
})

describe('buildTilePath', () => {
  it('creates cardinal one-tile steps to the destination', () => {
    expect(buildTilePath(
      { x: 1, y: 1 },
      { x: 4, y: 3 },
    )).toEqual([
      { x: 2, y: 1 },
      { x: 3, y: 1 },
      { x: 4, y: 1 },
      { x: 4, y: 2 },
      { x: 4, y: 3 },
    ])
  })
})

describe('AgentMapMarker', () => {
  it('walks through every tile before reaching a committed location', async () => {
    vi.useFakeTimers()
    const market: LocationSummary = {
      ...farm,
      id: 'market',
      name: 'Central Market',
      location_type: 'market',
      x: 4,
      y: 3,
    }
    const { rerender } = render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={vi.fn()}
      />,
    )

    const marker = screen.getByRole('button', { name: /elena/i })

    expect(marker.style.left).toBe('15%')
    expect(marker.style.top).toBe('15%')

    await act(async () => {
      rerender(
        <AgentMapMarker
          agent={{ ...agent, location_id: 'market' }}
          location={market}
          selected={false}
          stackIndex={0}
          stackCount={1}
          onSelect={vi.fn()}
        />,
      )
    })

    const runNextTimer = async () => {
      await act(async () => {
        vi.runOnlyPendingTimers()
      })
    }

    await runNextTimer()
    await runNextTimer()

    const sprite = marker.querySelector('.agent-sprite')

    expect(marker.style.left).toBe('25%')
    expect(marker.style.top).toBe('15%')
    expect(sprite?.getAttribute('data-direction')).toBe('right')
    expect(sprite?.getAttribute('data-walking')).toBe('true')

    const remainingCoordinates = [
      ['35%', '15%'],
      ['45%', '15%'],
      ['45%', '25%'],
      ['45%', '35%'],
    ]

    for (const [left, top] of remainingCoordinates) {
      await runNextTimer()
      await runNextTimer()

      expect(marker.style.left).toBe(left)
      expect(marker.style.top).toBe(top)
    }

    await runNextTimer()

    expect(sprite?.getAttribute('data-walking')).toBe('false')
    vi.useRealTimers()
  })

  it('keeps agent selection interactive', () => {
    const onSelect = vi.fn()

    render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={onSelect}
      />,
    )

    fireEvent.click(
      screen.getByRole('button', { name: /elena/i }),
    )

    expect(onSelect).toHaveBeenCalledWith('elena')
  })
})
