import { DashboardPanel } from './DashboardPanel'
import type { WorldSnapshot } from '../../types/world'

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
      ) : worldSnapshot.agents.length === 0 ? (
        <div className="placeholder-content">
          <p>This world has no agents.</p>
        </div>
      ) : (
        <div className="settlement-grid">
          {worldSnapshot.agents.map((agent) => (
            <button
              className={
                selectedAgentId === agent.id
                  ? 'settlement-agent settlement-agent--selected'
                  : 'settlement-agent'
              }
              key={agent.id}
              type="button"
              aria-pressed={selectedAgentId === agent.id}
              onClick={() => onAgentSelect(agent.id)}
            >
              <strong>{agent.name}</strong>
              <span>{agent.occupation}</span>
              <span>{agent.status}</span>
            </button>
          ))}
        </div>
      )}
    </DashboardPanel>
  )
}
