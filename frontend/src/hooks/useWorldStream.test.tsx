import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useWorldStream } from './useWorldStream'
import type { StreamEventEnvelope } from '../types/realtime'

class FakeWebSocket {
  static readonly OPEN = 1
  static instances: FakeWebSocket[] = []

  readyState = FakeWebSocket.OPEN
  onopen: (() => void) | null = null
  onmessage: ((message: MessageEvent<string>) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null
  send = vi.fn()
  close = vi.fn()
  readonly url: string

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }

  open(): void {
    this.onopen?.()
  }

  message(event: StreamEventEnvelope): void {
    this.onmessage?.({
      data: JSON.stringify(event),
    } as MessageEvent<string>)
  }
}

function streamEvent(sequence: number): StreamEventEnvelope {
  return {
    version: '1.0',
    sequence,
    world_id: 'world-1',
    tick: sequence,
    event_type: 'tick_committed',
    timestamp: '2026-07-29T10:00:00Z',
    payload: { current_tick: sequence },
  }
}

describe('useWorldStream', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    vi.stubGlobal('WebSocket', FakeWebSocket)
  })

  it('retains ordered events and ignores duplicate sequences', async () => {
    const { result } = renderHook(() => useWorldStream('world-1'))
    const socket = FakeWebSocket.instances[0]

    await act(async () => {
      socket.open()
      socket.message({
        version: '1.0',
        sequence: 0,
        world_id: 'world-1',
        tick: 0,
        event_type: 'stream_ready',
        timestamp: '2026-07-29T10:00:00Z',
        payload: { subscribed: true },
      })
      socket.message(streamEvent(1))
      socket.message(streamEvent(1))
      socket.message(streamEvent(2))
    })

    expect(result.current.status).toBe('connected')
    expect(result.current.connectionVersion).toBe(1)
    expect(result.current.latestTickSequence).toBe(2)
    expect(
      result.current.events.map((event) => event.sequence),
    ).toEqual([1, 2])
    expect(result.current.latestEvent?.sequence).toBe(2)
  })
})
