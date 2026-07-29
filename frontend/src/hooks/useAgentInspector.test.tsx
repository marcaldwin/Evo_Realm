import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useAgentInspector } from './useAgentInspector'
import type { AgentInspector } from '../types/agent'
import type { StreamEventEnvelope } from '../types/realtime'

const agent: AgentInspector = {
  id: 'elena',
  name: 'Elena',
  occupation: 'farmer',
  location_id: 'farm',
  status: 'working',
  hunger: 20,
  energy: 80,
  health: 100,
  money: 5,
  inventory: {},
  personality_traits: {},
  active_goal: null,
  recent_actions: [],
  selected_retrieved_memories: [],
}

const stateEvent: StreamEventEnvelope = {
  version: '1.0',
  sequence: 3,
  world_id: 'world-1',
  tick: 5,
  event_type: 'agent_state_changed',
  timestamp: '2026-07-29T00:00:00Z',
  payload: {
    agent_id: 'elena',
    changes: {},
  },
}

describe('useAgentInspector', () => {
  it('refreshes its values when the selected agent receives a state event', async () => {
    const updatedAgent: AgentInspector = {
      ...agent,
      hunger: 30,
      energy: 70,
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => agent,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => updatedAgent,
      })
    vi.stubGlobal('fetch', fetchMock)

    const { result, rerender } = renderHook(
      ({ latestEvent }) => useAgentInspector(
        'world-1',
        'elena',
        latestEvent,
      ),
      { initialProps: { latestEvent: null as StreamEventEnvelope | null } },
    )

    await waitFor(() => {
      expect(result.current.agent?.hunger).toBe(20)
    })

    rerender({ latestEvent: stateEvent })

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2)
      expect(result.current.agent?.hunger).toBe(30)
      expect(result.current.agent?.energy).toBe(70)
    })
  })

  it('reports a missing agent when the API returns 404', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useAgentInspector(
      'world-1',
      'missing-agent',
      null,
    ))

    await waitFor(() => {
      expect(result.current.notFound).toBe(true)
      expect(result.current.agent).toBeNull()
      expect(result.current.error).toBeNull()
    })
  })
})
