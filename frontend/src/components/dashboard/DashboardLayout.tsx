import type { ConnectionStatus } from '../../types/connection'
import { AgentInspectorPanel } from './AgentInspectorPanel'
import { DashboardHeader } from './DashboardHeader'
import { LiveEventFeedPanel } from './LiveEventFeedPanel'
import { SettlementGridPanel } from './SettlementGridPanel'
import { SimulationControlsPanel } from './SimulationControlsPanel'
import { WorldMetricsPanel } from './WorldMetricsPanel'

interface DashboardLayoutProps {
  backendStatus: ConnectionStatus
  websocketStatus: ConnectionStatus
}

export function DashboardLayout({
  backendStatus,
  websocketStatus,
}: DashboardLayoutProps) {
  return (
    <main className="dashboard">
      <DashboardHeader
        backendStatus={backendStatus}
        websocketStatus={websocketStatus}
      />

      <div className="dashboard__layout">
        <div className="dashboard__primary">
          <SettlementGridPanel />
          <LiveEventFeedPanel />
        </div>

        <aside className="dashboard__sidebar">
          <SimulationControlsPanel />
          <WorldMetricsPanel />
          <AgentInspectorPanel />
        </aside>
      </div>
    </main>
  )
}