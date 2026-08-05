import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useWorldEvents } from './useWorldEvents'
import type { StreamEventEnvelope } from '../types/realtime'

const duplicateAction: StreamEventEnvelope = {
  version: '1.0',
  sequence: 1,
  world_id: 'world-1',
  tick: 3,
  event_type: 'action_rejected',
  timestamp: '2026-07-29T10:00:00Z',
  payload: {
    source_event_type: 'food_purchase_rejected',
    summary: 'Marco lacked money.',
  },
}

const stateEvent: StreamEventEnvelope = {
  version: '1.0',
  sequence: 2,
  world_id: 'world-1',
  tick: 3,
  event_type: 'agent_state_changed',
  timestamp: '2026-07-29T10:00:01Z',
  payload: {
    agent_id: 'marco',
    changes: {},
  },
}

describe('useWorldEvents', () => {
  it('orders and deduplicates REST and WebSocket events', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [
        {
          tick: 3,
          event_type: 'food_purchase_rejected',
          agent_id: 'marco',
          location_id: 'market',
          summary: 'Marco lacked money.',
        },
      ],
    })
    vi.stubGlobal('fetch', fetchMock)

    const { result, rerender } = renderHook(
      ({ commandVersion }) => useWorldEvents(
        'world-1',
        [duplicateAction, stateEvent],
        1,
        commandVersion,
      ),
      { initialProps: { commandVersion: 0 } },
    )

    await waitFor(() => {
      expect(result.current.events).toHaveLength(2)
    })

    expect(result.current.events[0].event_type).toBe(
      'agent_state_changed',
    )
    expect(result.current.events[1].event_type).toBe(
      'food_purchase_rejected',
    )

    rerender({ commandVersion: 1 })

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2)
    })
  })
})
