export type StreamEventType =
  | 'stream_ready'
  | 'tick_committed'
  | 'agent_state_changed'
  | 'agent_moved'
  | 'action_executed'
  | 'action_rejected'
  | 'conversation_message'
  | 'relationship_changed'
  | 'memory_created'
  | 'world_event'

export interface StreamEventEnvelope {
  version: '1.0'
  sequence: number
  world_id: string
  tick: number
  event_type: StreamEventType
  timestamp: string
  payload: Record<string, unknown>
}

export interface SnapshotLoadedMessage {
  type: 'snapshot_loaded'
  snapshot_tick: number
}