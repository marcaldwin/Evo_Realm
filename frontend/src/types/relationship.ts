export interface AgentRelationship {
  relationship_id: string
  world_id: string
  source_agent_id: string
  target_agent_id: string
  trust: number
  affection: number
  respect: number
  interaction_count: number
}
