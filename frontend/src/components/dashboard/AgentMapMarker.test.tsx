import {
  act,
  fireEvent,
  render,
  screen,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type {
  AgentSummary,
  LocationSummary,
} from '../../types/world'
import {
  AgentMapMarker,
  DESYNC_SNAP_DELAY_MS,
} from './AgentMapMarker'
import {
  buildTilePath,
  collectLatestConfirmedMoves,
  getMovementDirection,
  type ConfirmedAgentMove,
} from './agentMovement'
import type { StreamEventEnvelope } from '../../types/realtime'

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

const market: LocationSummary = {
  ...farm,
  id: 'market',
  name: 'Central Market',
  location_type: 'market',
  x: 4,
  y: 3,
}

const confirmedMove: ConfirmedAgentMove = {
  sequence: 12,
  agentId: agent.id,
  fromLocationId: farm.id,
  toLocationId: market.id,
  destination: { x: market.x, y: market.y },
}

afterEach(() => {
  vi.useRealTimers()
})

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

describe('collectLatestConfirmedMoves', () => {
  it('extracts the latest valid backend movement for each agent', () => {
    const movementEvent: StreamEventEnvelope = {
      version: '1.0',
      sequence: confirmedMove.sequence,
      world_id: 'world-1',
      tick: 3,
      event_type: 'agent_moved',
      timestamp: '2026-08-05T08:00:00Z',
      payload: {
        agent_id: agent.id,
        from_location_id: farm.id,
        to_location_id: market.id,
      },
    }

    expect(
      collectLatestConfirmedMoves(
        [movementEvent],
        [farm, market],
      ).get(agent.id),
    ).toEqual(confirmedMove)
  })
})

describe('AgentMapMarker', () => {
  it('walks only after a confirmed backend movement event', async () => {
    vi.useFakeTimers()
    const { rerender } = render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        confirmedMove={null}
        syncVersion={0}
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
          agent={agent}
          location={farm}
          confirmedMove={confirmedMove}
          syncVersion={0}
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

    await act(async () => {
      rerender(
        <AgentMapMarker
          agent={{ ...agent, location_id: market.id }}
          location={market}
          confirmedMove={confirmedMove}
          syncVersion={0}
          selected={false}
          stackIndex={0}
          stackCount={1}
          onSelect={vi.fn()}
        />,
      )
    })

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
  })

  it('snaps a desynchronized snapshot without walking', async () => {
    vi.useFakeTimers()
    const { rerender } = render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        confirmedMove={null}
        syncVersion={0}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={vi.fn()}
      />,
    )
    const marker = screen.getByRole('button', { name: /elena/i })

    rerender(
      <AgentMapMarker
        agent={{ ...agent, location_id: market.id }}
        location={market}
        confirmedMove={null}
        syncVersion={0}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={vi.fn()}
      />,
    )

    expect(marker.style.left).toBe('15%')

    await act(async () => {
      vi.advanceTimersByTime(DESYNC_SNAP_DELAY_MS)
    })

    expect(marker.style.left).toBe('45%')
    expect(marker.style.top).toBe('35%')
    expect(
      marker.querySelector('.agent-sprite')
        ?.getAttribute('data-walking'),
    ).toBe('false')
  })

  it('snaps on reconnect without replaying an old movement', async () => {
    vi.useFakeTimers()
    const { rerender } = render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        confirmedMove={confirmedMove}
        syncVersion={0}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={vi.fn()}
      />,
    )
    const marker = screen.getByRole('button', { name: /elena/i })

    rerender(
      <AgentMapMarker
        agent={{ ...agent, location_id: market.id }}
        location={market}
        confirmedMove={confirmedMove}
        syncVersion={1}
        selected={false}
        stackIndex={0}
        stackCount={1}
        onSelect={vi.fn()}
      />,
    )

    await act(async () => {
      vi.runOnlyPendingTimers()
    })

    expect(marker.style.left).toBe('45%')
    expect(marker.style.top).toBe('35%')
    expect(
      marker.querySelector('.agent-sprite')
        ?.getAttribute('data-walking'),
    ).toBe('false')
  })

  it('keeps agent selection interactive', () => {
    const onSelect = vi.fn()

    render(
      <AgentMapMarker
        agent={agent}
        location={farm}
        confirmedMove={null}
        syncVersion={0}
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
