import { useMemo, useState } from 'react'

import type { WorldEventsState } from '../../hooks/useWorldEvents'
import type { ConnectionStatus } from '../../types/connection'
import { DashboardPanel } from './DashboardPanel'

interface LiveEventFeedPanelProps {
  state: WorldEventsState
  connectionStatus: ConnectionStatus
}

function formatEventType(eventType: string): string {
  return eventType.replaceAll('_', ' ')
}

export function LiveEventFeedPanel({
  state,
  connectionStatus,
}: LiveEventFeedPanelProps) {
  const [selectedType, setSelectedType] = useState('all')
  const eventTypes = useMemo(
    () => [...new Set(
      state.events.map((event) => event.event_type),
    )].sort(),
    [state.events],
  )
  const effectiveType = (
    selectedType === 'all'
    || eventTypes.includes(selectedType)
  )
    ? selectedType
    : 'all'
  const visibleEvents = effectiveType === 'all'
    ? state.events
    : state.events.filter(
      (event) => event.event_type === effectiveType,
    )

  return (
    <DashboardPanel
      title="Live Event Feed"
      className="live-event-feed-panel"
    >
      <div className="event-feed__toolbar">
        <label>
          Event type
          <select
            value={effectiveType}
            onChange={(event) => setSelectedType(event.target.value)}
          >
            <option value="all">All events</option>
            {eventTypes.map((eventType) => (
              <option key={eventType} value={eventType}>
                {formatEventType(eventType)}
              </option>
            ))}
          </select>
        </label>
        <span>{visibleEvents.length} shown</span>
      </div>

      {connectionStatus === 'disconnected' && (
        <p className="dashboard-warning" role="status">
          Live updates are disconnected. Existing events remain visible.
        </p>
      )}

      {state.error !== null && (
        <p className="dashboard-error" role="alert">
          {state.error}
        </p>
      )}

      {state.loading && state.events.length === 0 ? (
        <p className="event-feed__empty">
          Loading event history...
        </p>
      ) : visibleEvents.length === 0 ? (
        <p className="event-feed__empty">
          No events match this filter.
        </p>
      ) : (
        <ol className="event-feed" aria-live="polite">
          {visibleEvents.map((event) => (
            <li key={event.id}>
              <div className="event-feed__meta">
                <strong>Tick {event.tick}</strong>
                <span>{formatEventType(event.event_type)}</span>
                {event.timestamp !== null && (
                  <time dateTime={event.timestamp}>
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </time>
                )}
              </div>
              <p>{event.summary}</p>
            </li>
          ))}
        </ol>
      )}
    </DashboardPanel>
  )
}
