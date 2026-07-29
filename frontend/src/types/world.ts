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