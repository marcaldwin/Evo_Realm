import { DashboardPanel } from './DashboardPanel'
import type { WorldSnapshot } from '../../types/world'
import { SettlementTilemap } from './SettlementTilemap'

interface SettlementGridPanelProps {
  worldSnapshot: WorldSnapshot | null
  loading: boolean
  error: string | null
  selectedAgentId: string | null
  onAgentSelect: (agentId: string) => void
}

export function SettlementGridPanel({
  worldSnapshot,
  loading,
  error,
  selectedAgentId,
  onAgentSelect,
}: SettlementGridPanelProps) {
  return (
    <DashboardPanel
      title="Settlement Grid"
      className="settlement-grid-panel"
    >
      {error !== null ? (
        <div className="placeholder-content">
          <p className="dashboard-error" role="alert">{error}</p>
        </div>
      ) : worldSnapshot === null ? (
        <div className="placeholder-content">
          <p>
            {loading
              ? 'Loading settlement data...'
              : 'Settlement data is not available.'}
          </p>
        </div>
      ) : worldSnapshot.locations.length === 0 ? (
        <div className="placeholder-content">
          <p>This world has no settlement locations.</p>
        </div>
      ) : (
        <div className="settlement-map">
          <div className="settlement-map__summary">
            <span>10 × 10 tiles</span>
            <span>{worldSnapshot.locations.length} locations</span>
            <span>{worldSnapshot.agents.length} agents</span>
          </div>
          <SettlementTilemap
            locations={worldSnapshot.locations}
            agents={worldSnapshot.agents}
            selectedAgentId={selectedAgentId}
            onAgentSelect={onAgentSelect}
          />
        </div>
      )}
    </DashboardPanel>
  )
}
