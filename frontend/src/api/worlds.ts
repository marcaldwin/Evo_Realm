import { environment } from '../config/environment'
import type {
  WorldSnapshot,
  WorldSummary,
} from '../types/world'

export async function listWorlds(): Promise<WorldSummary[]> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds`,
  )

  if (!response.ok) {
    throw new Error(
      `World listing failed: ${response.status}`,
    )
  }

  return response.json() as Promise<WorldSummary[]>
}

export async function getWorldSnapshot(
  worldId: string,
): Promise<WorldSnapshot> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}`,
  )

  if (!response.ok) {
    throw new Error(
      `World snapshot failed: ${response.status}`,
    )
  }

  return response.json() as Promise<WorldSnapshot>
}

interface WorldSnapshotHandshake {
  current_tick: number
}

export async function getWorldSnapshotTick(
  worldId: string,
): Promise<number> {
  const response = await fetch(
    `${environment.apiBaseUrl}/api/worlds/${encodeURIComponent(worldId)}`,
  )

  if (!response.ok) {
    throw new Error(
      `World snapshot failed: ${response.status}`,
    )
  }

  const world =
    await response.json() as WorldSnapshotHandshake

  return world.current_tick
}
