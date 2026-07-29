import type { SimulationEvent } from './dashboard'

export type WorldStatus =
  | 'created'
  | 'running'
  | 'paused'

export interface WorldSummary {
  id: string
  name: string
  current_tick: number
  seed: number
  status: WorldStatus
  agent_count: number
}

export interface AgentSummary {
  id: string
  name: string
  occupation: string
  location_id: string
  status: string
  hunger: number
  energy: number
  health: number
  money: number
  inventory: Record<string, number>
}

export interface LocationSummary {
  id: string
  name: string
  location_type: string
  x: number
  y: number
  capacity: number
  inventory: Record<string, number>
}

export interface WorldSnapshot {
  id: string
  name: string
  current_tick: number
  seed: number
  status: WorldStatus
  locations: LocationSummary[]
  agents: AgentSummary[]
  events: SimulationEvent[]
}
