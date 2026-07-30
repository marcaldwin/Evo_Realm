import { useCallback, useEffect, useRef, useState } from 'react'

import { getWorldSnapshot } from '../api/worlds'
import type { WorldSnapshot } from '../types/world'

interface WorldSnapshotState {
  snapshot: WorldSnapshot | null
  loading: boolean
  error: string | null
  adoptSnapshot: (snapshot: WorldSnapshot) => void
}

interface StoredWorldSnapshotState {
  worldId: string | null
  snapshot: WorldSnapshot | null
  loading: boolean
  error: string | null
}

interface RefreshCheckpoint {
  worldId: string | null
  connectionVersion: number
  tickSequence: number | null
}

export function useWorldSnapshot(
  worldId: string | null,
  latestTickSequence: number | null,
  connectionVersion: number,
): WorldSnapshotState {
  const [state, setState] = useState<StoredWorldSnapshotState>({
    worldId: null,
    snapshot: null,
    loading: false,
    error: null,
  })
  const checkpoint = useRef<RefreshCheckpoint>({
    worldId: null,
    connectionVersion: 0,
    tickSequence: null,
  })

  useEffect(() => {
    let active = true

    if (worldId === null) {
      checkpoint.current = {
        worldId: null,
        connectionVersion: 0,
        tickSequence: null,
      }
      return undefined
    }

    const selectedWorldId = worldId
    const needsRefresh = (
      checkpoint.current.worldId !== selectedWorldId
      || checkpoint.current.connectionVersion !== connectionVersion
      || checkpoint.current.tickSequence !== latestTickSequence
    )

    if (!needsRefresh) {
      return undefined
    }

    checkpoint.current = {
      worldId: selectedWorldId,
      connectionVersion,
      tickSequence: latestTickSequence,
    }

    async function loadSnapshot() {
      setState((current) => ({
        worldId: selectedWorldId,
        snapshot: current.worldId === selectedWorldId
          ? current.snapshot
          : null,
        loading: true,
        error: null,
      }))

      try {
        const snapshot = await getWorldSnapshot(selectedWorldId)

        if (active) {
          setState({
            worldId: selectedWorldId,
            snapshot,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState({
            worldId: selectedWorldId,
            snapshot: null,
            loading: false,
            error: error instanceof Error
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
  }, [connectionVersion, latestTickSequence, worldId])

  const adoptSnapshot = useCallback((snapshot: WorldSnapshot) => {
    setState({
      worldId: snapshot.id,
      snapshot,
      loading: false,
      error: null,
    })
  }, [])

  if (worldId === null) {
    return {
      snapshot: null,
      loading: false,
      error: null,
      adoptSnapshot,
    }
  }

  if (state.worldId !== worldId) {
    return {
      snapshot: null,
      loading: true,
      error: null,
      adoptSnapshot,
    }
  }

  return {
    snapshot: state.snapshot,
    loading: state.loading,
    error: state.error,
    adoptSnapshot,
  }
}
