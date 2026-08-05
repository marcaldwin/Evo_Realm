import { environment } from '../config/environment'
import type { SimulationEvent } from '../types/dashboard'
import { createApiRequestError } from './errors'


export async function listWorldEvents(
  worldId: string,
): Promise<SimulationEvent[]> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}/events`,
  )

  if (!response.ok) {
    throw await createApiRequestError(
      response,
      `World event request failed: ${response.status}`,
    )
  }

  return response.json() as Promise<SimulationEvent[]>
}
