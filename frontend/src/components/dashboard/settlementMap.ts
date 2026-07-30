import type {
  AgentSummary,
  LocationSummary,
  LocationType,
} from '../../types/world'

export const SETTLEMENT_SIZE = 10

export type TerrainType = 'grass' | 'field' | 'path' | 'road'
export type DecorationType =
  | 'fence'
  | 'flowers'
  | 'rock'
  | 'tree'

export interface LocationAsset {
  label: string
  symbol: string
}

export interface SettlementCell {
  key: string
  x: number
  y: number
  terrain: TerrainType
  decoration: DecorationType | null
  location: LocationSummary | null
  agents: AgentSummary[]
}

export const LOCATION_ASSETS: Record<LocationType, LocationAsset> = {
  home: { label: 'Home', symbol: '⌂' },
  farm: { label: 'Farm', symbol: '▦' },
  market: { label: 'Market', symbol: '◫' },
  clinic: { label: 'Clinic', symbol: '+' },
  workshop: { label: 'Workshop', symbol: '⚒' },
  town_hall: { label: 'Town Hall', symbol: '◆' },
}

const roadCoordinates = new Set([
  '4,0',
  '4,1',
  '4,2',
  '4,3',
  '4,4',
  '4,5',
  '4,6',
  '4,7',
  '4,8',
  '4,9',
  '0,5',
  '1,5',
  '2,5',
  '3,5',
  '5,5',
  '6,5',
  '7,5',
  '8,5',
  '9,5',
])

const pathCoordinates = new Set([
  '1,2',
  '1,3',
  '2,3',
  '3,3',
  '5,3',
  '6,3',
  '7,3',
  '2,6',
  '2,7',
  '5,7',
  '6,7',
  '7,7',
])

const fieldCoordinates = new Set([
  '0,0',
  '1,0',
  '2,0',
  '0,1',
  '1,1',
  '2,1',
  '0,2',
  '2,2',
])

const decorations = new Map<string, DecorationType>([
  ['3,0', 'fence'],
  ['3,1', 'fence'],
  ['3,2', 'fence'],
  ['8,0', 'tree'],
  ['9,1', 'tree'],
  ['8,2', 'rock'],
  ['0,4', 'flowers'],
  ['8,4', 'flowers'],
  ['0,7', 'tree'],
  ['9,7', 'rock'],
  ['1,9', 'rock'],
  ['6,9', 'tree'],
  ['9,9', 'flowers'],
])

function coordinateKey(x: number, y: number): string {
  return `${x},${y}`
}

function getTerrain(x: number, y: number): TerrainType {
  const key = coordinateKey(x, y)

  if (roadCoordinates.has(key)) {
    return 'road'
  }

  if (pathCoordinates.has(key)) {
    return 'path'
  }

  if (fieldCoordinates.has(key)) {
    return 'field'
  }

  return 'grass'
}

export function buildSettlementCells(
  locations: LocationSummary[],
  agents: AgentSummary[],
): SettlementCell[] {
  const locationsByCoordinate = new Map(
    locations
      .filter(({ x, y }) => (
        Number.isInteger(x)
        && Number.isInteger(y)
        && x >= 0
        && x < SETTLEMENT_SIZE
        && y >= 0
        && y < SETTLEMENT_SIZE
      ))
      .map((location) => [
        coordinateKey(location.x, location.y),
        location,
      ]),
  )
  const agentsByLocation = new Map<string, AgentSummary[]>()

  for (const agent of agents) {
    const locationAgents = agentsByLocation.get(agent.location_id) ?? []
    locationAgents.push(agent)
    agentsByLocation.set(agent.location_id, locationAgents)
  }

  return Array.from(
    { length: SETTLEMENT_SIZE * SETTLEMENT_SIZE },
    (_, index) => {
      const x = index % SETTLEMENT_SIZE
      const y = Math.floor(index / SETTLEMENT_SIZE)
      const key = coordinateKey(x, y)
      const location = locationsByCoordinate.get(key) ?? null

      return {
        key,
        x,
        y,
        terrain: getTerrain(x, y),
        decoration: location === null
          ? decorations.get(key) ?? null
          : null,
        location,
        agents: location === null
          ? []
          : agentsByLocation.get(location.id) ?? [],
      }
    },
  )
}
