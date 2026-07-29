import { environment } from '../config/environment'
import type { AgentInspector } from '../types/agent'

export class AgentNotFoundError extends Error {
  constructor() {
    super('This agent is no longer available.')
  }
}

export async function getAgentInspector(
  worldId: string,
  agentId: string,
): Promise<AgentInspector> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}/agents/${encodeURIComponent(agentId)}`,
  )

  if (response.status === 404) {
    throw new AgentNotFoundError()
  }

  if (!response.ok) {
    throw new Error(
      `Agent inspector request failed: ${response.status}`,
    )
  }

  return response.json() as Promise<AgentInspector>
}
