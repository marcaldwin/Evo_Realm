import type { ConnectionStatus } from '../../types/connection'
import { ConnectionStatusBadge } from './ConnectionStatusBadge'

interface DashboardHeaderProps {
  backendStatus: ConnectionStatus
  websocketStatus: ConnectionStatus
}

export function DashboardHeader({
  backendStatus,
  websocketStatus,
}: DashboardHeaderProps) {
  return (
    <header className="dashboard-header">
      <div>
        <p className="dashboard-header__eyebrow">
          Simulation Control Center
        </p>
        <h1>EvoRealm</h1>
        <p>Observe and control the living settlement.</p>
      </div>

      <div className="dashboard-header__connections">
        <ConnectionStatusBadge
          label="Backend"
          status={backendStatus}
        />
        <ConnectionStatusBadge
          label="Live stream"
          status={websocketStatus}
        />
      </div>
    </header>
  )
}