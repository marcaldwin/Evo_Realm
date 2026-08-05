import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { StreamEventEnvelope } from '../types/realtime'
import type { AgentRelationship } from '../types/relationship'
import { useWorldRelationships } from './useWorldRelationships'

const baselineRelationship: AgentRelationship = {
  relationship_id: 'relationship-1',
  world_id: 'world-1',
  source_agent_id: 'elena',
  target_agent_id: 'marco',
  trust: 5,
  affection: 2,
  respect: 3,
  interaction_count: 1,
}

const relationshipEvent: StreamEventEnvelope = {
  version: '1.0',
  sequence: 3,
  world_id: 'world-1',
  tick: 8,
  event_type: 'relationship_changed',
  timestamp: '2026-08-05T10:00:00Z',
  payload: {
    relationship_id: 'relationship-1',
    source_agent_id: 'elena',
    target_agent_id: 'marco',
    changes: {
      trust: { before: 5, after: 12 },
      interaction_count: { before: 1, after: 2 },
    },
  },
}

function relationshipResponse(
  relationship: AgentRelationship,
) {
  return {
    ok: true,
    status: 200,
    json: async () => [relationship],
  }
}

describe('useWorldRelationships', () => {
  it('projects live changes and refreshes its baseline on reconnect', async () => {
    const reconnectedRelationship = {
      ...baselineRelationship,
      trust: 20,
      interaction_count: 4,
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        relationshipResponse(baselineRelationship),
      )
      .mockResolvedValueOnce(
        relationshipResponse(reconnectedRelationship),
      )
    vi.stubGlobal('fetch', fetchMock)

    const { result, rerender } = renderHook(
      ({ events, connectionVersion }) => useWorldRelationships(
        'world-1',
        events,
        connectionVersion,
      ),
      {
        initialProps: {
          events: [] as StreamEventEnvelope[],
          connectionVersion: 1,
        },
      },
    )

    await waitFor(() => {
      expect(result.current.relationships[0]?.trust).toBe(5)
    })

    rerender({
      events: [relationshipEvent],
      connectionVersion: 1,
    })

    expect(result.current.relationships[0]).toMatchObject({
      trust: 12,
      interaction_count: 2,
    })

    rerender({
      events: [relationshipEvent],
      connectionVersion: 2,
    })

    await waitFor(() => {
      expect(result.current.relationships[0]).toMatchObject({
        trust: 20,
        interaction_count: 4,
      })
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('ignores malformed relationship updates', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      relationshipResponse(baselineRelationship),
    ))
    const malformedEvent: StreamEventEnvelope = {
      ...relationshipEvent,
      sequence: 4,
      payload: {
        relationship_id: 'relationship-1',
        source_agent_id: 'elena',
        target_agent_id: 'marco',
        changes: { trust: { after: 500 } },
      },
    }
    const { result, rerender } = renderHook(
      ({ events }) => useWorldRelationships('world-1', events, 1),
      { initialProps: { events: [] as StreamEventEnvelope[] } },
    )

    await waitFor(() => {
      expect(result.current.relationships[0]?.trust).toBe(5)
    })
    rerender({ events: [malformedEvent] })

    expect(result.current.relationships[0]?.trust).toBe(5)
  })
})
