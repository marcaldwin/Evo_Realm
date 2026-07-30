import type {
  AgentSummary,
  LocationSummary,
} from '../../types/world'
import {
  buildSettlementCells,
  LOCATION_ASSETS,
} from './settlementMap'
import { AgentMapMarker } from './AgentMapMarker'

interface SettlementTilemapProps {
  locations: LocationSummary[]
  agents: AgentSummary[]
  selectedAgentId: string | null
  onAgentSelect: (agentId: string) => void
}

const decorationSymbols = {
  fence: '',
  flowers: '✿',
  rock: '●',
  tree: '♠',
}

export function SettlementTilemap({
  locations,
  agents,
  selectedAgentId,
  onAgentSelect,
}: SettlementTilemapProps) {
  const cells = buildSettlementCells(locations, agents)
  const locationsById = new Map(
    locations.map((location) => [location.id, location]),
  )
  const agentCountsByLocation = new Map<string, number>()
  const agentIndexesByLocation = new Map<string, number>()

  for (const agent of agents) {
    agentCountsByLocation.set(
      agent.location_id,
      (agentCountsByLocation.get(agent.location_id) ?? 0) + 1,
    )
  }

  return (
    <div className="settlement-map-viewport">
      <div
        className="settlement-tilemap"
        role="grid"
        aria-label="10 by 10 settlement map"
      >
        {cells.map((cell) => {
          const locationAsset = cell.location === null
            ? null
            : LOCATION_ASSETS[cell.location.location_type]

          return (
            <div
              className={[
                'settlement-cell',
                `settlement-cell--${cell.terrain}`,
              ].join(' ')}
              data-coordinate={`${cell.x},${cell.y}`}
              key={cell.key}
              role="gridcell"
              aria-label={
                cell.location === null
                  ? `Empty tile at ${cell.x}, ${cell.y}`
                  : `${cell.location.name} at ${cell.x}, ${cell.y}`
              }
            >
              <span className="settlement-cell__coordinate">
                {cell.x},{cell.y}
              </span>

              {cell.decoration !== null && (
                <span
                  className={[
                    'settlement-decoration',
                    `settlement-decoration--${cell.decoration}`,
                  ].join(' ')}
                  aria-hidden="true"
                >
                  {decorationSymbols[cell.decoration]}
                </span>
              )}

              {cell.location !== null && locationAsset !== null && (
                <div
                  className={[
                    'settlement-location',
                    `settlement-location--${cell.location.location_type}`,
                  ].join(' ')}
                >
                  <span
                    className="settlement-location__symbol"
                    aria-hidden="true"
                  >
                    {locationAsset.symbol}
                  </span>
                  <strong>{cell.location.name}</strong>
                  <span>{locationAsset.label}</span>
                  <span className="settlement-location__capacity">
                    Capacity {cell.location.capacity}
                  </span>
                </div>
              )}

            </div>
          )
        })}

        <div
          className="settlement-agent-layer"
          aria-label="Settlement agents"
        >
          {agents.map((agent) => {
            const location = locationsById.get(agent.location_id)

            if (location === undefined) {
              return null
            }

            const stackIndex =
              agentIndexesByLocation.get(agent.location_id) ?? 0
            agentIndexesByLocation.set(
              agent.location_id,
              stackIndex + 1,
            )

            return (
              <AgentMapMarker
                agent={agent}
                location={location}
                selected={selectedAgentId === agent.id}
                stackIndex={stackIndex}
                stackCount={
                  agentCountsByLocation.get(agent.location_id) ?? 1
                }
                key={agent.id}
                onSelect={onAgentSelect}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}
