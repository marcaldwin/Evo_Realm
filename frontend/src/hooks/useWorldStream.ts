import { useEffect, useState } from 'react'

import { getWorldSnapshotTick } from '../api/worlds'
import { environment } from '../config/environment'
import type { ConnectionStatus } from '../types/connection'
import type {
  SnapshotLoadedMessage,
  StreamEventEnvelope,
} from '../types/realtime'

interface WorldStreamState {
  status: ConnectionStatus
  latestEvent: StreamEventEnvelope | null
}

export function useWorldStream(
  worldId: string | null,
): WorldStreamState {
  const [state, setState] = useState<WorldStreamState>({
    status: 'disconnected',
    latestEvent: null,
  })

  useEffect(() => {
    if (worldId === null) {
      return
    }

    const selectedWorldId = worldId
    let active = true

    const socket = new WebSocket(
      `${environment.websocketBaseUrl}/api/worlds/${encodeURIComponent(selectedWorldId)}/stream`,
    )

    async function handleMessage(message: MessageEvent<string>) {
      const envelope =
        JSON.parse(message.data) as StreamEventEnvelope

      if (
        envelope.event_type === 'stream_ready'
        && envelope.payload.snapshot_required === true
      ) {
        const snapshotTick =
          await getWorldSnapshotTick(selectedWorldId)

        const acknowledgement: SnapshotLoadedMessage = {
          type: 'snapshot_loaded',
          snapshot_tick: snapshotTick,
        }

        if (
          active
          && socket.readyState === WebSocket.OPEN
        ) {
          socket.send(JSON.stringify(acknowledgement))
        }

        return
      }

      if (
        envelope.event_type === 'stream_ready'
        && envelope.payload.subscribed === true
      ) {
        if (active) {
          setState((current) => ({
            ...current,
            status: 'connected',
          }))
        }

        return
      }

      if (active) {
        setState({
          status: 'connected',
          latestEvent: envelope,
        })
      }
    }

    socket.onopen = () => {
      if (active) {
        setState({
          status: 'connecting',
          latestEvent: null,
        })
      }
    }

    socket.onmessage = (message) => {
      void handleMessage(message)
    }

    socket.onerror = () => {
      if (active) {
        setState((current) => ({
          ...current,
          status: 'disconnected',
        }))
      }
    }

    socket.onclose = () => {
      if (active) {
        setState((current) => ({
          ...current,
          status: 'disconnected',
        }))
      }
    }

    return () => {
      active = false
      socket.close()
    }
  }, [worldId])

  if (worldId === null) {
    return {
      status: 'disconnected',
      latestEvent: null,
    }
  }

  return state
}
