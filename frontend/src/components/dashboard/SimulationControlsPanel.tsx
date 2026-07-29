import { DashboardPanel } from './DashboardPanel'

export function SimulationControlsPanel() {
  return (
    <DashboardPanel
      title="Simulation Controls"
      className="simulation-controls-panel"
    >
      <div className="simulation-controls">
        <button type="button" disabled>
          Start
        </button>

        <button type="button" disabled>
          Pause
        </button>

        <button type="button" disabled>
          Step one tick
        </button>
      </div>
    </DashboardPanel>
  )
}