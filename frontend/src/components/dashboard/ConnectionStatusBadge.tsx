import type { ConnectionStatus } from '../../types/connection'

interface ConnectionStatusBadgeProps {
  label: string
  status: ConnectionStatus
}

export function ConnectionStatusBadge({
  label,
  status,
}: ConnectionStatusBadgeProps) {
  return (
    <div className={`connection-badge connection-badge--${status}`}>
      <span className="connection-badge__indicator" />
      <span>{label}</span>
      <strong>{status}</strong>
    </div>
  )
}