import type { WorldMetricsState } from '../../hooks/useWorldMetrics'
import { DashboardPanel } from './DashboardPanel'

interface WorldMetricsPanelProps {
  state: WorldMetricsState
}

export function WorldMetricsPanel({
  state,
}: WorldMetricsPanelProps) {
  return (
    <DashboardPanel
      title="World Metrics"
      className="world-metrics-panel"
    >
      {state.error !== null ? (
        <p className="dashboard-error" role="alert">
          {state.error}
        </p>
      ) : state.metrics === null ? (
        <p className="dashboard-message">
          {state.loading
            ? 'Loading world metrics...'
            : 'World metrics are not available.'}
        </p>
      ) : (
        <>
          {state.loading && (
            <p className="dashboard-message">
              Refreshing metrics...
            </p>
          )}
          <dl className="metrics-list">
            <div>
              <dt>Current tick</dt>
              <dd>{state.metrics.current_tick}</dd>
            </div>
            <div>
              <dt>World status</dt>
              <dd>{state.metrics.status}</dd>
            </div>
            <div>
              <dt>Total food</dt>
              <dd>{state.metrics.total_food}</dd>
            </div>
            <div>
              <dt>Average health</dt>
              <dd>{state.metrics.average_health.toFixed(1)}</dd>
            </div>
            <div>
              <dt>Successful trades</dt>
              <dd>{state.metrics.successful_trades}</dd>
            </div>
            <div>
              <dt>Help events</dt>
              <dd>{state.metrics.emergency_help_events}</dd>
            </div>
            <div>
              <dt>Rejected actions</dt>
              <dd>{state.metrics.rejected_actions}</dd>
            </div>
            <div>
              <dt>Active conversations</dt>
              <dd>{state.metrics.active_conversations}</dd>
            </div>
          </dl>
        </>
      )}
    </DashboardPanel>
  )
}
