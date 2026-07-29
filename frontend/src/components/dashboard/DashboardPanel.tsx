import type { ReactNode } from 'react'

interface DashboardPanelProps {
  title: string
  children: ReactNode
  className?: string
}

export function DashboardPanel({
  title,
  children,
  className = '',
}: DashboardPanelProps) {
  return (
    <section className={`dashboard-panel ${className}`}>
      <header className="dashboard-panel__header">
        <h2>{title}</h2>
      </header>

      <div className="dashboard-panel__content">
        {children}
      </div>
    </section>
  )
}