import { useEffect, useRef, useState } from 'react'

import { getWorldDashboardMetrics } from '../api/dashboard'
import type { WorldDashboardMetrics } from '../types/dashboard'

export interface WorldMetricsState {
  metrics: WorldDashboardMetrics | null
  loading: boolean
  error: string | null
}

interface StoredWorldMetricsState extends WorldMetricsState {
  worldId: string | null
}

interface MetricsRefreshCheckpoint {
  worldId: string | null
  connectionVersion: number
  commandVersion: number
  tickSequence: number | null
}

export function useWorldMetrics(
  worldId: string | null,
  latestTickSequence: number | null,
  connectionVersion: number,
  commandVersion: number,
): WorldMetricsState {
  const [state, setState] = useState<StoredWorldMetricsState>({
    worldId: null,
    metrics: null,
    loading: false,
    error: null,
  })
  const checkpoint = useRef<MetricsRefreshCheckpoint>({
    worldId: null,
    connectionVersion: 0,
    commandVersion: 0,
    tickSequence: null,
  })

  useEffect(() => {
    let active = true

    if (worldId === null) {
      checkpoint.current = {
        worldId: null,
        connectionVersion: 0,
        commandVersion: 0,
        tickSequence: null,
      }
      return undefined
    }

    const needsRefresh = (
      checkpoint.current.worldId !== worldId
      || checkpoint.current.connectionVersion !== connectionVersion
      || checkpoint.current.commandVersion !== commandVersion
      || checkpoint.current.tickSequence !== latestTickSequence
    )

    if (!needsRefresh) {
      return undefined
    }

    checkpoint.current = {
      worldId,
      connectionVersion,
      commandVersion,
      tickSequence: latestTickSequence,
    }
    const selectedWorldId = worldId

    async function loadMetrics() {
      setState((current) => ({
        worldId: selectedWorldId,
        metrics: current.worldId === selectedWorldId
          ? current.metrics
          : null,
        loading: true,
        error: null,
      }))

      try {
        const metrics = await getWorldDashboardMetrics(
          selectedWorldId,
        )

        if (active) {
          setState({
            worldId: selectedWorldId,
            metrics,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setState({
            worldId: selectedWorldId,
            metrics: null,
            loading: false,
            error: error instanceof Error
              ? error.message
              : 'Unable to load world metrics',
          })
        }
      }
    }

    void loadMetrics()

    return () => {
      active = false
    }
  }, [
    commandVersion,
    connectionVersion,
    latestTickSequence,
    worldId,
  ])

  if (worldId === null) {
    return { metrics: null, loading: false, error: null }
  }

  if (state.worldId !== worldId) {
    return { metrics: null, loading: true, error: null }
  }

  return {
    metrics: state.metrics,
    loading: state.loading,
    error: state.error,
  }
}
