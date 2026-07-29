import type { WorldControlsState } from '../../hooks/useWorldControls'
import type { WorldCommand } from '../../types/dashboard'
import type { WorldStatus } from '../../types/world'
import { DashboardPanel } from './DashboardPanel'

interface SimulationControlsPanelProps {
  worldStatus: WorldStatus | null
  controls: WorldControlsState
}

interface ControlDefinition {
  command: WorldCommand
  label: string
  requiredStatus: WorldStatus | null
}

const controls: ControlDefinition[] = [
  { command: 'start', label: 'Start', requiredStatus: 'created' },
  { command: 'pause', label: 'Pause', requiredStatus: 'running' },
  { command: 'resume', label: 'Resume', requiredStatus: 'paused' },
  { command: 'step', label: 'Step one tick', requiredStatus: null },
]

export function SimulationControlsPanel({
  worldStatus,
  controls: controlState,
}: SimulationControlsPanelProps) {
  const busy = controlState.pendingCommand !== null

  return (
    <DashboardPanel
      title="Simulation Controls"
      className="simulation-controls-panel"
    >
      <div className="simulation-controls">
        {controls.map(({ command, label, requiredStatus }) => {
          const enabledForStatus = requiredStatus === null
            ? worldStatus !== null
            : worldStatus === requiredStatus
          const pending = controlState.pendingCommand === command

          return (
            <button
              key={command}
              type="button"
              disabled={busy || !enabledForStatus}
              aria-busy={pending}
              onClick={() => {
                void controlState.execute(command)
              }}
            >
              {pending ? `${label}...` : label}
            </button>
          )
        })}
      </div>

      {worldStatus === null && (
        <p className="dashboard-message">
          Select or create a world to enable controls.
        </p>
      )}

      {controlState.error !== null && (
        <p className="dashboard-error" role="alert">
          {controlState.error}
        </p>
      )}
    </DashboardPanel>
  )
}
