import { useEffect, useMemo, useRef, useState } from 'react'

import { getWorldRelationships } from '../api/relationships'
import type { StreamEventEnvelope } from '../types/realtime'
import type { AgentRelationship } from '../types/relationship'

export interface WorldRelationshipsState {
  relationships: AgentRelationship[]
  loading: boolean
  error: string | null
}

interface RelationshipBaseline {
  worldId: string | null
  relationships: AgentRelationship[]
  eventFloor: number
  loading: boolean
  error: string | null
}

const relationshipFields = [
  'trust',
  'affection',
  'respect',
  'interaction_count',
] as const

type RelationshipField = typeof relationshipFields[number]

function latestSequence(events: StreamEventEnvelope[]): number {
  return events.reduce(
    (latest, event) => Math.max(latest, event.sequence),
    0,
  )
}

function changedValue(
  payload: Record<string, unknown>,
  field: RelationshipField,
): number | null {
  const changes = payload.changes
  if (
    typeof changes !== 'object'
    || changes === null
    || Array.isArray(changes)
  ) {
    return null
  }

  const change = (changes as Record<string, unknown>)[field]
  if (
    typeof change !== 'object'
    || change === null
    || Array.isArray(change)
  ) {
    return null
  }

  const after = (change as Record<string, unknown>).after
  if (typeof after !== 'number' || !Number.isInteger(after)) {
    return null
  }
  if (field === 'interaction_count') {
    return (after as number) >= 0 ? after as number : null
  }
  return (after as number) >= -100 && (after as number) <= 100
    ? after as number
    : null
}

function projectRelationshipEvents(
  baseline: AgentRelationship[],
  events: StreamEventEnvelope[],
  worldId: string,
  eventFloor: number,
): AgentRelationship[] {
  const relationships = new Map(
    baseline.map((relationship) => [
      relationship.relationship_id,
      relationship,
    ]),
  )

  const updates = events
    .filter((event) => (
      event.world_id === worldId
      && event.event_type === 'relationship_changed'
      && event.sequence > eventFloor
    ))
    .sort((first, second) => first.sequence - second.sequence)

  for (const event of updates) {
    const relationshipId = event.payload.relationship_id
    const sourceAgentId = event.payload.source_agent_id
    const targetAgentId = event.payload.target_agent_id
    if (
      typeof relationshipId !== 'string'
      || typeof sourceAgentId !== 'string'
      || typeof targetAgentId !== 'string'
    ) {
      continue
    }

    const current = relationships.get(relationshipId) ?? {
      relationship_id: relationshipId,
      world_id: worldId,
      source_agent_id: sourceAgentId,
      target_agent_id: targetAgentId,
      trust: 0,
      affection: 0,
      respect: 0,
      interaction_count: 0,
    }
    const updated = { ...current }

    for (const field of relationshipFields) {
      const value = changedValue(event.payload, field)
      if (value !== null) {
        updated[field] = value
      }
    }

    relationships.set(relationshipId, updated)
  }

  return [...relationships.values()].sort((first, second) => (
    first.source_agent_id.localeCompare(second.source_agent_id)
    || first.target_agent_id.localeCompare(second.target_agent_id)
  ))
}

export function useWorldRelationships(
  worldId: string | null,
  streamEvents: StreamEventEnvelope[],
  connectionVersion: number,
): WorldRelationshipsState {
  const streamEventsRef = useRef(streamEvents)
  streamEventsRef.current = streamEvents
  const [baseline, setBaseline] = useState<RelationshipBaseline>({
    worldId: null,
    relationships: [],
    eventFloor: 0,
    loading: false,
    error: null,
  })

  useEffect(() => {
    let active = true
    if (worldId === null) {
      return undefined
    }

    const selectedWorldId = worldId
    const eventFloor = latestSequence(streamEventsRef.current)
    setBaseline((current) => ({
      worldId: selectedWorldId,
      relationships: current.worldId === selectedWorldId
        ? current.relationships
        : [],
      eventFloor,
      loading: true,
      error: null,
    }))

    async function loadRelationships() {
      try {
        const relationships = await getWorldRelationships(
          selectedWorldId,
        )
        if (active) {
          setBaseline({
            worldId: selectedWorldId,
            relationships,
            eventFloor,
            loading: false,
            error: null,
          })
        }
      } catch (error) {
        if (active) {
          setBaseline((current) => ({
            ...current,
            worldId: selectedWorldId,
            eventFloor,
            loading: false,
            error: error instanceof Error
              ? error.message
              : 'Unable to load relationships.',
          }))
        }
      }
    }

    void loadRelationships()
    return () => {
      active = false
    }
  }, [connectionVersion, worldId])

  const relationships = useMemo(() => {
    if (worldId === null || baseline.worldId !== worldId) {
      return []
    }
    return projectRelationshipEvents(
      baseline.relationships,
      streamEvents,
      worldId,
      baseline.eventFloor,
    )
  }, [baseline, streamEvents, worldId])

  if (worldId === null || baseline.worldId !== worldId) {
    return {
      relationships: [],
      loading: worldId !== null,
      error: null,
    }
  }

  return {
    relationships,
    loading: baseline.loading,
    error: baseline.error,
  }
}
