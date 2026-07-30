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
  latestTickSequence: number | null
  events: StreamEventEnvelope[]
  connectionVersion: number
}

interface StoredWorldStreamState extends WorldStreamState {
  worldId: string | null
}

const MAX_STREAM_EVENTS = 200

export function useWorldStream(
  worldId: string | null,
): WorldStreamState {
  const [state, setState] = useState<StoredWorldStreamState>({
    worldId: null,
    status: 'disconnected',
    latestEvent: null,
    latestTickSequence: null,
    events: [],
    connectionVersion: 0,
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
            worldId: selectedWorldId,
            status: 'connected',
            latestEvent: current.worldId === selectedWorldId
              ? current.latestEvent
              : null,
            latestTickSequence:
              current.worldId === selectedWorldId
                ? current.latestTickSequence
                : null,
            events: current.worldId === selectedWorldId
              ? current.events
              : [],
            connectionVersion: (
              current.worldId === selectedWorldId
                ? current.connectionVersion
                : 0
            ) + 1,
          }))
        }

        return
      }

      if (active) {
        setState((current) => {
          const currentEvents = current.worldId === selectedWorldId
            ? current.events
            : []
          const alreadyReceived = currentEvents.some(
            (event) => event.sequence === envelope.sequence,
          )

          return {
            worldId: selectedWorldId,
            status: 'connected',
            latestEvent: envelope,
            latestTickSequence:
              envelope.event_type === 'tick_committed'
                ? envelope.sequence
                : current.worldId === selectedWorldId
                  ? current.latestTickSequence
                  : null,
            events: alreadyReceived
              ? currentEvents
              : [...currentEvents, envelope].slice(
                -MAX_STREAM_EVENTS,
              ),
            connectionVersion: current.worldId === selectedWorldId
              ? current.connectionVersion
              : 0,
          }
        })
      }
    }

    socket.onopen = () => {
      if (active) {
        setState((current) => ({
          worldId: selectedWorldId,
          status: 'connecting',
          latestEvent: null,
          latestTickSequence:
            current.worldId === selectedWorldId
              ? current.latestTickSequence
              : null,
          events: current.worldId === selectedWorldId
            ? current.events
            : [],
          connectionVersion: current.worldId === selectedWorldId
            ? current.connectionVersion
            : 0,
        }))
      }
    }

    socket.onmessage = (message) => {
      void handleMessage(message)
    }

    socket.onerror = () => {
      if (active) {
        setState((current) => ({
          ...current,
          worldId: selectedWorldId,
          status: 'disconnected',
        }))
      }
    }

    socket.onclose = () => {
      if (active) {
        setState((current) => ({
          ...current,
          worldId: selectedWorldId,
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
      latestTickSequence: null,
      events: [],
      connectionVersion: 0,
    }
  }

  if (state.worldId !== worldId) {
    return {
      status: 'connecting',
      latestEvent: null,
      latestTickSequence: null,
      events: [],
      connectionVersion: 0,
    }
  }

  return {
    status: state.status,
    latestEvent: state.latestEvent,
    latestTickSequence: state.latestTickSequence,
    events: state.events,
    connectionVersion: state.connectionVersion,
  }
}
