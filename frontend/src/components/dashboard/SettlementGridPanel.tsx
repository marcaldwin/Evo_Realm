import { DashboardPanel } from './DashboardPanel'

export function SettlementGridPanel() {
  return (
    <DashboardPanel
      title="Settlement Grid"
      className="settlement-grid-panel"
    >
      <div className="placeholder-content">
        <p>Settlement locations and agents will appear here.</p>
      </div>
    </DashboardPanel>
  )
}