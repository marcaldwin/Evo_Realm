import { useEffect, useRef, useState } from 'react'

import {
  AgentNotFoundError,
  getAgentInspector,
} from '../api/agents'
import type { AgentInspector } from '../types/agent'
import type { StreamEventEnvelope } from '../types/realtime'

export interface AgentInspectorState {
  agent: AgentInspector | null
  loading: boolean
  error: string | null
  notFound: boolean
}

interface StoredAgentInspectorState extends AgentInspectorState {
  requestKey: string | null
}

export function useAgentInspector(
  worldId: string | null,
  agentId: string | null,
  latestEvent: StreamEventEnvelope | null,
): AgentInspectorState {
  const [state, setState] = useState<StoredAgentInspectorState>({
    agent: null,
    loading: false,
    error: null,
    notFound: false,
    requestKey: null,
  })
  const lastRequestedAgentKey = useRef<string | null>(null)

  useEffect(() => {
    let active = true

    if (worldId === null || agentId === null) {
      lastRequestedAgentKey.current = null
      return undefined
    }

    const selectedWorldId = worldId
    const selectedAgentId = agentId
    const agentKey = `${selectedWorldId}:${selectedAgentId}`
    const eventAgentId = latestEvent?.payload.agent_id
    const hasRelevantUpdate = (
      latestEvent?.event_type === 'agent_moved'
      || latestEvent?.event_type === 'agent_state_changed'
    ) && eventAgentId === selectedAgentId

    if (
      lastRequestedAgentKey.current === agentKey
      && !hasRelevantUpdate
    ) {
      return undefined
    }

    lastRequestedAgentKey.current = agentKey

    async function loadAgent() {
      setState((current) => ({
        agent: current.agent?.id === selectedAgentId
          ? current.agent
          : null,
        loading: true,
        error: null,
        notFound: false,
        requestKey: agentKey,
      }))

      try {
        const agent = await getAgentInspector(
          selectedWorldId,
          selectedAgentId,
        )

        if (active) {
          setState({
            agent,
            loading: false,
            error: null,
            notFound: false,
            requestKey: agentKey,
          })
        }
      } catch (error) {
        if (active) {
          setState({
            agent: null,
            loading: false,
            error: error instanceof AgentNotFoundError
              ? null
              : error instanceof Error
                ? error.message
                : 'Unable to load the selected agent.',
            notFound: error instanceof AgentNotFoundError,
            requestKey: agentKey,
          })
        }
      }
    }

    void loadAgent()

    return () => {
      active = false
    }
  }, [agentId, latestEvent, worldId])

  if (worldId === null || agentId === null) {
    return {
      agent: null,
      loading: false,
      error: null,
      notFound: false,
    }
  }

  const selectedAgentKey = `${worldId}:${agentId}`

  if (state.requestKey !== selectedAgentKey) {
    return {
      agent: null,
      loading: true,
      error: null,
      notFound: false,
    }
  }

  return {
    agent: state.agent,
    loading: state.loading,
    error: state.error,
    notFound: state.notFound,
  }
}
