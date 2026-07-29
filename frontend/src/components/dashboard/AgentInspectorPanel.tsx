import { DashboardPanel } from './DashboardPanel'

export function AgentInspectorPanel() {
  return (
    <DashboardPanel
      title="Agent Inspector"
      className="agent-inspector-panel"
    >
      <div className="agent-inspector__empty">
        <p>Select an agent to inspect its current state.</p>
      </div>
    </DashboardPanel>
  )
}