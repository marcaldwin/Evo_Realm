import type { StreamEventType } from './realtime'
import type { WorldStatus } from './world'

export type WorldCommand =
  | 'start'
  | 'pause'
  | 'resume'
  | 'step'

export interface WorldDashboardMetrics {
  world_id: string
  current_tick: number
  status: WorldStatus
  total_food: number
  average_health: number
  successful_trades: number
  emergency_help_events: number
  rejected_actions: number
  active_conversations: number
}

export interface SimulationEvent {
  tick: number
  event_type: string
  agent_id: string
  location_id: string
  summary: string
}

export interface DashboardEvent {
  id: string
  tick: number
  event_type: string | StreamEventType
  timestamp: string | null
  summary: string
}
