import { environment } from '../config/environment'
import type { HealthResponse } from '../types/connection'

export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(
    `${environment.apiBaseUrl}/health/live`,
  )

  if (!response.ok) {
    throw new Error(
      `Backend health check failed: ${response.status}`,
    )
  }

  return response.json() as Promise<HealthResponse>
}