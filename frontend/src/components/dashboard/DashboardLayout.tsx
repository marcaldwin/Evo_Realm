import type { ConnectionStatus } from '../../types/connection'
import type { WorldSnapshot } from '../../types/world'
import type { StreamEventEnvelope } from '../../types/realtime'
import type { AgentInspectorState } from '../../hooks/useAgentInspector'
import type { WorldControlsState } from '../../hooks/useWorldControls'
import type { WorldEventsState } from '../../hooks/useWorldEvents'
import type { WorldMetricsState } from '../../hooks/useWorldMetrics'
import type { WorldRelationshipsState } from '../../hooks/useWorldRelationships'
import { AgentInspectorPanel } from './AgentInspectorPanel'
import { DashboardHeader } from './DashboardHeader'
import { LiveEventFeedPanel } from './LiveEventFeedPanel'
import { RelationshipGraphPanel } from './RelationshipGraphPanel'
import { SettlementGridPanel } from './SettlementGridPanel'
import { SimulationControlsPanel } from './SimulationControlsPanel'
import { WorldMetricsPanel } from './WorldMetricsPanel'

interface DashboardLayoutProps {
  backendStatus: ConnectionStatus
  websocketStatus: ConnectionStatus
  worldSnapshot: WorldSnapshot | null
  worldSnapshotLoading: boolean
  worldSnapshotError: string | null
  worldControls: WorldControlsState
  worldMetrics: WorldMetricsState
  worldEvents: WorldEventsState
  worldRelationships: WorldRelationshipsState
  streamEvents: StreamEventEnvelope[]
  connectionVersion: number
  selectedAgentId: string | null
  onAgentSelect: (agentId: string) => void
  agentInspectorState: AgentInspectorState
  onClearAgentSelection: () => void
}

export function DashboardLayout({
  backendStatus,
  websocketStatus,
  worldSnapshot,
  worldSnapshotLoading,
  worldSnapshotError,
  worldControls,
  worldMetrics,
  worldEvents,
  worldRelationships,
  streamEvents,
  connectionVersion,
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
            loading={worldSnapshotLoading}
            error={worldSnapshotError}
            streamEvents={streamEvents}
            connectionVersion={connectionVersion}
            selectedAgentId={selectedAgentId}
            onAgentSelect={onAgentSelect}
          />
          <RelationshipGraphPanel
            agents={worldSnapshot?.agents ?? []}
            state={worldRelationships}
            selectedAgentId={selectedAgentId}
            onAgentSelect={onAgentSelect}
          />
          <LiveEventFeedPanel
            state={worldEvents}
            connectionStatus={websocketStatus}
          />
        </div>

        <aside className="dashboard__sidebar">
          <SimulationControlsPanel
            worldStatus={worldSnapshot?.status ?? null}
            controls={worldControls}
          />
          <WorldMetricsPanel state={worldMetrics} />
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
