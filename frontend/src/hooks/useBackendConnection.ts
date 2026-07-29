import { useEffect, useState } from 'react'

import { checkBackendHealth } from '../api/health'
import type { ConnectionStatus } from '../types/connection'

const HEALTH_CHECK_INTERVAL_MS = 5_000

export function useBackendConnection(): ConnectionStatus {
  const [status, setStatus] =
    useState<ConnectionStatus>('connecting')

  useEffect(() => {
    let active = true

    async function checkConnection() {
      try {
        await checkBackendHealth()

        if (active) {
          setStatus('connected')
        }
      } catch {
        if (active) {
          setStatus('disconnected')
        }
      }
    }

    void checkConnection()

    const intervalId = window.setInterval(
      () => void checkConnection(),
      HEALTH_CHECK_INTERVAL_MS,
    )

    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [])

  return status
}