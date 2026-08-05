import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useWorldControls } from './useWorldControls'
import type { WorldSnapshot } from '../types/world'

const snapshot: WorldSnapshot = {
  id: 'world-1',
  name: 'Control World',
  current_tick: 0,
  seed: 42,
  status: 'running',
  locations: [],
  agents: [],
  events: [],
}

describe('useWorldControls', () => {
  it('adopts the world returned by a successful command', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => snapshot,
    })
    const onWorldUpdated = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useWorldControls(
      'world-1',
      onWorldUpdated,
    ))

    await act(async () => {
      await result.current.execute('start')
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/worlds/world-1/start',
      { method: 'POST' },
    )
    expect(onWorldUpdated).toHaveBeenCalledWith(snapshot)
    expect(result.current.completionVersion).toBe(1)
  })

  it('keeps the confirmed state and exposes a conflict error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        detail: 'Cannot pause world while status is created.',
      }),
    }))

    const { result } = renderHook(() => useWorldControls(
      'world-1',
      vi.fn(),
    ))

    await act(async () => {
      await result.current.execute('pause')
    })

    await waitFor(() => {
      expect(result.current.error).toBe(
        'Cannot pause world while status is created.',
      )
    })
    expect(result.current.completionVersion).toBe(0)
  })
})
