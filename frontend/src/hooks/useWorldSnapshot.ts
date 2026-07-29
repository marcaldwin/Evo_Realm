import { useEffect, useState } from 'react'

import { getWorldSnapshot } from '../api/worlds'
import type { WorldSnapshot } from '../types/world'

interface WorldSnapshotState {
  snapshot: WorldSnapshot | null
  loading: boolean
  error: string | null
}

export function useWorldSnapshot(
  worldId: string | null,
): WorldSnapshotState {
  const [state, setState] = useState<WorldSnapshotState>({
    snapshot: null,
    loading: worldId !== null,
    error: null,
  })

  useEffect(() => {
    let active = true

    if (worldId === null) {
      return undefined
    }

    const selectedWorldId = worldId

    async function loadSnapshot() {
      setState((current) => ({
        ...current,
        loading: true,
        error: null,
      }))

      try {
        const snapshot = await getWorldSnapshot(selectedWorldId)

        if (active) {
          setState({
            snapshot,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState({
            snapshot: null,
            loading: false,
            error:
              error instanceof Error
                ? error.message
                : 'Unable to load world snapshot',
          })
        }
      }
    }

    void loadSnapshot()

    return () => {
      active = false
    }
  }, [worldId])

  return worldId === null
    ? { snapshot: null, loading: false, error: null }
    : state
}
