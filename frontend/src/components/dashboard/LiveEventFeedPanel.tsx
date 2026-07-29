import { DashboardPanel } from './DashboardPanel'

export function LiveEventFeedPanel() {
  return (
    <DashboardPanel
      title="Live Event Feed"
      className="live-event-feed-panel"
    >
      <ol className="event-feed" aria-live="polite">
        <li className="event-feed__empty">
          Waiting for simulation events...
        </li>
      </ol>
    </DashboardPanel>
  )
}