import { useCallback, useRef, useState } from 'react'

import { executeWorldCommand } from '../api/worlds'
import type { WorldCommand } from '../types/dashboard'
import type { WorldSnapshot } from '../types/world'

export interface WorldControlsState {
  pendingCommand: WorldCommand | null
  error: string | null
  completionVersion: number
  execute: (command: WorldCommand) => Promise<void>
}

export function useWorldControls(
  worldId: string | null,
  onWorldUpdated: (snapshot: WorldSnapshot) => void,
): WorldControlsState {
  const [pendingCommand, setPendingCommand] =
    useState<WorldCommand | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [completionVersion, setCompletionVersion] = useState(0)
  const pendingRef = useRef(false)

  const execute = useCallback(async (command: WorldCommand) => {
    if (worldId === null || pendingRef.current) {
      return
    }

    pendingRef.current = true
    setPendingCommand(command)
    setError(null)

    try {
      const snapshot = await executeWorldCommand(worldId, command)
      onWorldUpdated(snapshot)
      setCompletionVersion((version) => version + 1)
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : `Unable to ${command} the world.`,
      )
    } finally {
      pendingRef.current = false
      setPendingCommand(null)
    }
  }, [onWorldUpdated, worldId])

  return {
    pendingCommand,
    error,
    completionVersion,
    execute,
  }
}
