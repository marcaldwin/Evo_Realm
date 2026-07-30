import type { AgentDirection } from './AgentSprite'

export interface Coordinate {
  x: number
  y: number
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
