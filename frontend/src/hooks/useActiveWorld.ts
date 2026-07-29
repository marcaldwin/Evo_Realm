import { useEffect, useState } from 'react'

import { listWorlds } from '../api/worlds'
import type { WorldSummary } from '../types/world'

interface ActiveWorldState {
  world: WorldSummary | null
  loading: boolean
  error: string | null
}

export function useActiveWorld(): ActiveWorldState {
  const [state, setState] = useState<ActiveWorldState>({
    world: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let active = true

    async function loadWorld() {
      try {
        const worlds = await listWorlds()

        if (active) {
          setState({
            world: worlds[0] ?? null,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState({
            world: null,
            loading: false,
            error:
              error instanceof Error
                ? error.message
                : 'Unable to load worlds',
          })
        }
      }
    }

    void loadWorld()

    return () => {
      active = false
    }
  }, [])

  return state
}