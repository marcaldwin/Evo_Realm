import { useEffect, useMemo, useRef, useState } from 'react'

import { listWorldEvents } from '../api/events'
import type {
  DashboardEvent,
  SimulationEvent,
} from '../types/dashboard'
import type { StreamEventEnvelope } from '../types/realtime'

const MAX_DASHBOARD_EVENTS = 200

export interface WorldEventsState {
  events: DashboardEvent[]
  loading: boolean
  error: string | null
}

interface StoredEventHistory {
  worldId: string | null
  events: SimulationEvent[]
  loading: boolean
  error: string | null
}

function payloadText(
  payload: Record<string, unknown>,
  key: string,
  fallback: string,
): string {
  return typeof payload[key] === 'string'
    ? payload[key]
    : fallback
}

export function describeStreamEvent(
  event: StreamEventEnvelope,
): string {
  const summary = event.payload.summary
  if (typeof summary === 'string') {
    return summary
  }

  switch (event.event_type) {
    case 'tick_committed':
      return `Tick ${event.tick} committed.`
    case 'agent_state_changed':
      return `${payloadText(event.payload, 'agent_id', 'Agent')} state changed.`
    case 'agent_moved':
      return `${payloadText(event.payload, 'agent_id', 'Agent')} moved from ${payloadText(event.payload, 'from_location_id', 'an unknown location')} to ${payloadText(event.payload, 'to_location_id', 'an unknown location')}.`
    case 'conversation_message':
      return `${payloadText(event.payload, 'speaker_agent_id', 'Agent')}: ${payloadText(event.payload, 'message', 'Conversation message')}`
    case 'relationship_changed':
      return `Relationship from ${payloadText(event.payload, 'source_agent_id', 'an agent')} to ${payloadText(event.payload, 'target_agent_id', 'another agent')} changed.`
    case 'memory_created':
      return `${payloadText(event.payload, 'owner_agent_id', 'Agent')} formed a new memory.`
    default:
      return event.event_type.replaceAll('_', ' ')
  }
}

function normalizeHistoryEvent(
  event: SimulationEvent,
  index: number,
): DashboardEvent {
  return {
    id: [
      'history',
      index,
      event.tick,
      event.event_type,
      event.agent_id,
    ].join('-'),
    tick: event.tick,
    event_type: event.event_type,
    timestamp: null,
    summary: event.summary,
  }
}

function normalizeStreamEvent(
  event: StreamEventEnvelope,
): DashboardEvent {
  const sourceEventType = event.payload.source_event_type
  const eventType = (
    event.event_type === 'action_executed'
    || event.event_type === 'action_rejected'
  ) && typeof sourceEventType === 'string'
    ? sourceEventType
    : event.event_type

  return {
    id: `stream-${event.world_id}-${event.sequence}`,
    tick: event.tick,
    event_type: eventType,
    timestamp: event.timestamp,
    summary: describeStreamEvent(event),
  }
}

export function useWorldEvents(
  worldId: string | null,
  streamEvents: StreamEventEnvelope[],
  connectionVersion: number,
  commandVersion: number,
): WorldEventsState {
  const [history, setHistory] = useState<StoredEventHistory>({
    worldId: null,
    events: [],
    loading: false,
    error: null,
  })
  const lastRequestKey = useRef<string | null>(null)

  useEffect(() => {
    let active = true

    if (worldId === null) {
      lastRequestKey.current = null
      return undefined
    }

    const requestKey = [
      worldId,
      connectionVersion,
      commandVersion,
    ].join(':')
    if (lastRequestKey.current === requestKey) {
      return undefined
    }

    lastRequestKey.current = requestKey
    const selectedWorldId = worldId

    async function loadHistory() {
      setHistory({
        worldId: selectedWorldId,
        events: [],
        loading: true,
        error: null,
      })

      try {
        const events = await listWorldEvents(selectedWorldId)

        if (active) {
          setHistory({
            worldId: selectedWorldId,
            events,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setHistory({
            worldId: selectedWorldId,
            events: [],
            loading: false,
            error: error instanceof Error
              ? error.message
              : 'Unable to load world events',
          })
        }
      }
    }

    void loadHistory()

    return () => {
      active = false
    }
  }, [commandVersion, connectionVersion, worldId])

  const events = useMemo(() => {
    if (worldId === null || history.worldId !== worldId) {
      return []
    }

    const historyEvents = history.events.map(normalizeHistoryEvent)
    const historyKeys = new Set(
      history.events.map((event) => [
        event.tick,
        event.event_type,
        event.summary,
      ].join(':')),
    )
    const liveEvents = streamEvents
      .filter((event) => event.world_id === worldId)
      .filter((event) => event.event_type !== 'world_event')
      .map(normalizeStreamEvent)
      .filter((event) => !historyKeys.has([
        event.tick,
        event.event_type,
        event.summary,
      ].join(':')))

    return [...historyEvents, ...liveEvents]
      .slice(-MAX_DASHBOARD_EVENTS)
      .reverse()
  }, [history, streamEvents, worldId])

  if (worldId === null) {
    return { events: [], loading: false, error: null }
  }

  if (history.worldId !== worldId) {
    return { events: [], loading: true, error: null }
  }

  return {
    events,
    loading: history.loading,
    error: history.error,
  }
}
