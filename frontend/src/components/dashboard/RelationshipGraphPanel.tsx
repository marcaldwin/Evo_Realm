import { useState, type KeyboardEvent } from 'react'

import type { WorldRelationshipsState } from '../../hooks/useWorldRelationships'
import type { AgentRelationship } from '../../types/relationship'
import type { AgentSummary } from '../../types/world'
import { DashboardPanel } from './DashboardPanel'

interface RelationshipGraphPanelProps {
  agents: AgentSummary[]
  state: WorldRelationshipsState
  selectedAgentId: string | null
  onAgentSelect: (agentId: string) => void
}

interface Point {
  x: number
  y: number
}

type RelationshipTone = 'positive' | 'neutral' | 'negative'

const graphWidth = 620
const graphHeight = 400
const nodeRadius = 34

function relationshipStrength(
  relationship: AgentRelationship,
): number {
  return Math.round((
    Math.abs(relationship.trust)
    + Math.abs(relationship.affection)
    + Math.abs(relationship.respect)
  ) / 3)
}

function relationshipTone(
  relationship: AgentRelationship,
): RelationshipTone {
  const sentiment = (
    relationship.trust
    + relationship.affection
    + relationship.respect
  ) / 3
  if (sentiment > 5) {
    return 'positive'
  }
  if (sentiment < -5) {
    return 'negative'
  }
  return 'neutral'
}

function buildNodePositions(
  agents: AgentSummary[],
): Map<string, Point> {
  const positions = new Map<string, Point>()
  if (agents.length === 1) {
    positions.set(agents[0].id, {
      x: graphWidth / 2,
      y: graphHeight / 2,
    })
    return positions
  }

  agents.forEach((agent, index) => {
    const angle = (Math.PI * 2 * index) / agents.length - Math.PI / 2
    positions.set(agent.id, {
      x: graphWidth / 2 + Math.cos(angle) * 230,
      y: graphHeight / 2 + Math.sin(angle) * 140,
    })
  })
  return positions
}

function edgeGeometry(
  source: Point,
  target: Point,
  curved: boolean,
): { path: string; label: Point } {
  const dx = target.x - source.x
  const dy = target.y - source.y
  const distance = Math.max(Math.hypot(dx, dy), 1)
  const unitX = dx / distance
  const unitY = dy / distance
  const start = {
    x: source.x + unitX * nodeRadius,
    y: source.y + unitY * nodeRadius,
  }
  const end = {
    x: target.x - unitX * (nodeRadius + 8),
    y: target.y - unitY * (nodeRadius + 8),
  }
  const curve = curved ? 28 : 0
  const control = {
    x: (start.x + end.x) / 2 - unitY * curve,
    y: (start.y + end.y) / 2 + unitX * curve,
  }

  return {
    path: `M ${start.x} ${start.y} Q ${control.x} ${control.y} ${end.x} ${end.y}`,
    label: {
      x: 0.25 * start.x + 0.5 * control.x + 0.25 * end.x,
      y: 0.25 * start.y + 0.5 * control.y + 0.25 * end.y,
    },
  }
}

function handleNodeKeyDown(
  event: KeyboardEvent<SVGGElement>,
  agentId: string,
  onAgentSelect: (agentId: string) => void,
) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    onAgentSelect(agentId)
  }
}

export function RelationshipGraphPanel({
  agents,
  state,
  selectedAgentId,
  onAgentSelect,
}: RelationshipGraphPanelProps) {
  const [agentFilter, setAgentFilter] = useState('all')
  const [minimumStrength, setMinimumStrength] = useState(0)
  const activeAgentFilter = (
    agentFilter === 'all'
    || agents.some((agent) => agent.id === agentFilter)
  ) ? agentFilter : 'all'
  const agentsById = new Map(
    agents.map((agent) => [agent.id, agent]),
  )
  const positions = buildNodePositions(agents)
  const filteredRelationships = state.relationships.filter(
    (relationship) => (
      agentsById.has(relationship.source_agent_id)
      && agentsById.has(relationship.target_agent_id)
      && (
        activeAgentFilter === 'all'
        || relationship.source_agent_id === activeAgentFilter
        || relationship.target_agent_id === activeAgentFilter
      )
      && relationshipStrength(relationship) >= minimumStrength
    ),
  )

  return (
    <DashboardPanel
      title="Agent Relationships"
      className="relationship-graph-panel"
    >
      <div className="relationship-graph-controls">
        <label>
          Agent
          <select
            value={activeAgentFilter}
            onChange={(event) => setAgentFilter(event.target.value)}
          >
            <option value="all">All agents</option>
            {agents.map((agent) => (
              <option value={agent.id} key={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Minimum strength: {minimumStrength}
          <input
            aria-label="Minimum relationship strength"
            type="range"
            min="0"
            max="100"
            value={minimumStrength}
            onChange={(event) => {
              setMinimumStrength(Number(event.target.value))
            }}
          />
        </label>
      </div>

      {state.error !== null && (
        <p className="dashboard-error" role="alert">
          {state.error}
        </p>
      )}
      {state.loading && (
        <p className="dashboard-message">Refreshing relationships...</p>
      )}

      {agents.length === 0 ? (
        <p className="dashboard-message">
          This world has no agents to display.
        </p>
      ) : (
        <>
          <div className="relationship-graph-viewport">
            <svg
              className="relationship-graph"
              viewBox={`0 0 ${graphWidth} ${graphHeight}`}
              role="group"
              aria-label="Directed agent relationship graph"
            >
              <defs>
                {(['positive', 'neutral', 'negative'] as const).map(
                  (tone) => (
                    <marker
                      id={`relationship-arrow-${tone}`}
                      key={tone}
                      markerWidth="8"
                      markerHeight="8"
                      refX="7"
                      refY="4"
                      orient="auto"
                      markerUnits="strokeWidth"
                    >
                      <path
                        className={`relationship-arrow relationship-arrow--${tone}`}
                        d="M 0 0 L 8 4 L 0 8 z"
                      />
                    </marker>
                  ),
                )}
              </defs>

              {filteredRelationships.map((relationship) => {
                const source = positions.get(
                  relationship.source_agent_id,
                )
                const target = positions.get(
                  relationship.target_agent_id,
                )
                if (source === undefined || target === undefined) {
                  return null
                }
                const hasReverse = filteredRelationships.some(
                  (candidate) => (
                    candidate.source_agent_id
                      === relationship.target_agent_id
                    && candidate.target_agent_id
                      === relationship.source_agent_id
                  ),
                )
                const geometry = edgeGeometry(
                  source,
                  target,
                  hasReverse,
                )
                const tone = relationshipTone(relationship)

                return (
                  <g key={relationship.relationship_id}>
                    <path
                      className={`relationship-edge relationship-edge--${tone}`}
                      d={geometry.path}
                      markerEnd={`url(#relationship-arrow-${tone})`}
                      data-strength={relationshipStrength(relationship)}
                    >
                      <title>
                        {`${relationship.source_agent_id} to ${relationship.target_agent_id}: trust ${relationship.trust}, affection ${relationship.affection}, respect ${relationship.respect}, interactions ${relationship.interaction_count}`}
                      </title>
                    </path>
                    <text
                      className="relationship-edge__count"
                      x={geometry.label.x}
                      y={geometry.label.y}
                    >
                      {relationship.interaction_count}×
                    </text>
                  </g>
                )
              })}

              {agents.map((agent) => {
                const position = positions.get(agent.id)
                if (position === undefined) {
                  return null
                }
                const dimmed = (
                  activeAgentFilter !== 'all'
                  && activeAgentFilter !== agent.id
                )

                return (
                  <g
                    className={[
                      'relationship-node',
                      selectedAgentId === agent.id
                        ? 'relationship-node--selected'
                        : '',
                      dimmed ? 'relationship-node--dimmed' : '',
                    ].filter(Boolean).join(' ')}
                    transform={`translate(${position.x} ${position.y})`}
                    role="button"
                    tabIndex={0}
                    aria-label={`Inspect ${agent.name}`}
                    aria-pressed={selectedAgentId === agent.id}
                    key={agent.id}
                    onClick={() => onAgentSelect(agent.id)}
                    onKeyDown={(event) => {
                      handleNodeKeyDown(event, agent.id, onAgentSelect)
                    }}
                  >
                    <circle r={nodeRadius} />
                    <text className="relationship-node__name" y="-2">
                      {agent.name}
                    </text>
                    <text className="relationship-node__occupation" y="15">
                      {agent.occupation}
                    </text>
                  </g>
                )
              })}
            </svg>
          </div>

          {filteredRelationships.length === 0 ? (
            <p className="dashboard-message">
              No relationships match the current filters.
            </p>
          ) : (
            <ul className="relationship-list">
              {filteredRelationships.map((relationship) => (
                <li key={relationship.relationship_id}>
                  <strong>
                    {agentsById.get(relationship.source_agent_id)?.name}
                    {' → '}
                    {agentsById.get(relationship.target_agent_id)?.name}
                  </strong>
                  <span>Trust {relationship.trust}</span>
                  <span>Affection {relationship.affection}</span>
                  <span>Respect {relationship.respect}</span>
                  <span>{relationship.interaction_count} interactions</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </DashboardPanel>
  )
}
