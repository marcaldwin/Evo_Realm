import { environment } from '../config/environment'
import type { AgentRelationship } from '../types/relationship'


export async function getWorldRelationships(
  worldId: string,
): Promise<AgentRelationship[]> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}/relationships`,
  )

  if (!response.ok) {
    throw new Error(
      `Relationship snapshot failed: ${response.status}`,
    )
  }

  return response.json() as Promise<AgentRelationship[]>
}
