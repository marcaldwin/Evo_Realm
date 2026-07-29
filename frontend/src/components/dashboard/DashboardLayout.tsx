import type { ConnectionStatus } from '../../types/connection'
import type { WorldSnapshot } from '../../types/world'
import type { AgentInspectorState } from '../../hooks/useAgentInspector'
import { AgentInspectorPanel } from './AgentInspectorPanel'
import { DashboardHeader } from './DashboardHeader'
import { LiveEventFeedPanel } from './LiveEventFeedPanel'
import { SettlementGridPanel } from './SettlementGridPanel'
import { SimulationControlsPanel } from './SimulationControlsPanel'
import { WorldMetricsPanel } from './WorldMetricsPanel'

interface DashboardLayoutProps {
  backendStatus: ConnectionStatus
  websocketStatus: ConnectionStatus
  worldSnapshot: WorldSnapshot | null
  selectedAgentId: string | null
  onAgentSelect: (agentId: string) => void
  agentInspectorState: AgentInspectorState
  onClearAgentSelection: () => void
}

export function DashboardLayout({
  backendStatus,
  websocketStatus,
  worldSnapshot,
  selectedAgentId,
  onAgentSelect,
  agentInspectorState,
  onClearAgentSelection,
}: DashboardLayoutProps) {
  return (
    <main className="dashboard">
      <DashboardHeader
        backendStatus={backendStatus}
        websocketStatus={websocketStatus}
      />

      <div className="dashboard__layout">
        <div className="dashboard__primary">
          <SettlementGridPanel
            worldSnapshot={worldSnapshot}
            selectedAgentId={selectedAgentId}
            onAgentSelect={onAgentSelect}
          />
          <LiveEventFeedPanel />
        </div>

        <aside className="dashboard__sidebar">
          <SimulationControlsPanel />
          <WorldMetricsPanel />
          <AgentInspectorPanel
            state={agentInspectorState}
            locations={worldSnapshot?.locations ?? []}
            onClearSelection={onClearAgentSelection}
          />
        </aside>
      </div>
    </main>
  )
}
