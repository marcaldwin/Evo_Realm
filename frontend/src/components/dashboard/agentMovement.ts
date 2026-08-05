import type { StreamEventEnvelope } from '../../types/realtime'
import type { LocationSummary } from '../../types/world'
import type { AgentDirection } from './AgentSprite'

export interface Coordinate {
  x: number
  y: number
}

export interface ConfirmedAgentMove {
  sequence: number
  agentId: string
  fromLocationId: string
  toLocationId: string
  destination: Coordinate
}

export function getMovementDirection(
  previous: Coordinate,
  current: Coordinate,
): AgentDirection {
  const horizontalDistance = current.x - previous.x
  const verticalDistance = current.y - previous.y

  if (
    Math.abs(horizontalDistance)
    >= Math.abs(verticalDistance)
  ) {
    return horizontalDistance >= 0 ? 'right' : 'left'
  }

  return verticalDistance >= 0 ? 'down' : 'up'
}

export function buildTilePath(
  start: Coordinate,
  destination: Coordinate,
): Coordinate[] {
  const path: Coordinate[] = []
  let x = start.x
  let y = start.y

  while (x !== destination.x) {
    x += destination.x > x ? 1 : -1
    path.push({ x, y })
  }

  while (y !== destination.y) {
    y += destination.y > y ? 1 : -1
    path.push({ x, y })
  }

  return path
}

export function collectLatestConfirmedMoves(
  events: StreamEventEnvelope[],
  locations: LocationSummary[],
): Map<string, ConfirmedAgentMove> {
  const locationsById = new Map(
    locations.map((location) => [location.id, location]),
  )
  const movesByAgent = new Map<string, ConfirmedAgentMove>()

  for (const event of events) {
    if (event.event_type !== 'agent_moved') {
      continue
    }

    const agentId = event.payload.agent_id
    const fromLocationId = event.payload.from_location_id
    const toLocationId = event.payload.to_location_id

    if (
      typeof agentId !== 'string'
      || typeof fromLocationId !== 'string'
      || typeof toLocationId !== 'string'
    ) {
      continue
    }

    const destination = locationsById.get(toLocationId)
    if (destination === undefined) {
      continue
    }

    movesByAgent.set(agentId, {
      sequence: event.sequence,
      agentId,
      fromLocationId,
      toLocationId,
      destination: {
        x: destination.x,
        y: destination.y,
      },
    })
  }

  return movesByAgent
}
