import { DashboardPanel } from './DashboardPanel'

export function WorldMetricsPanel() {
  return (
    <DashboardPanel
      title="World Metrics"
      className="world-metrics-panel"
    >
      <dl className="metrics-list">
        <div>
          <dt>Current tick</dt>
          <dd>--</dd>
        </div>

        <div>
          <dt>Agents</dt>
          <dd>--</dd>
        </div>

        <div>
          <dt>Total food</dt>
          <dd>--</dd>
        </div>

        <div>
          <dt>World status</dt>
          <dd>Not loaded</dd>
        </div>
      </dl>
    </DashboardPanel>
  )
}