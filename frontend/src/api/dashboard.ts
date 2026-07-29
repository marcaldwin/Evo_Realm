import { environment } from '../config/environment'
import type { WorldDashboardMetrics } from '../types/dashboard'
import { createApiRequestError } from './errors'


export async function getWorldDashboardMetrics(
  worldId: string,
): Promise<WorldDashboardMetrics> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}/metrics`,
  )

  if (!response.ok) {
    throw await createApiRequestError(
      response,
      `World metrics request failed: ${response.status}`,
    )
  }

  return response.json() as Promise<WorldDashboardMetrics>
}
