import type { AgentSummary } from './world'

export interface AgentAction {
  tick: number
  event_type: string
  location_id: string
  summary: string
}

export interface RetrievedMemory {
  memory_id: string
  content: string
  importance: number
  emotional_value: number
  creation_tick: number
  source_event_sequence: number
  source_agent_id: string
  semantic_similarity: number
  importance_score: number
  recency_score: number
  relationship_relevance: number
  total_score: number
}

export interface AgentInspector extends AgentSummary {
  personality_traits: Record<string, number>
  active_goal: string | null
  recent_actions: AgentAction[]
  selected_retrieved_memories: RetrievedMemory[]
}
