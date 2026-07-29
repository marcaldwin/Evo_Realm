import { DashboardPanel } from './DashboardPanel'
import type { AgentInspectorState } from '../../hooks/useAgentInspector'
import type { LocationSummary } from '../../types/world'

interface AgentInspectorPanelProps {
  state: AgentInspectorState
  locations: LocationSummary[]
  onClearSelection: () => void
}

function formatLabel(value: string): string {
  return value.replaceAll('_', ' ')
}

function formatScore(value: number): string {
  return value.toFixed(2)
}

export function AgentInspectorPanel({
  state,
  locations,
  onClearSelection,
}: AgentInspectorPanelProps) {
  const { agent } = state
  const location = agent === null
    ? null
    : locations.find(({ id }) => id === agent.location_id)

  return (
    <DashboardPanel
      title="Agent Inspector"
      className="agent-inspector-panel"
    >
      {agent === null ? (
        <div className="agent-inspector__empty">
          <p>
            {state.loading
              ? 'Loading agent details...'
              : state.notFound
                ? 'This agent is no longer available.'
                : state.error ?? 'Select an agent to inspect its current state.'}
          </p>
          {state.notFound && (
            <button
              className="agent-inspector__close"
              type="button"
              onClick={onClearSelection}
            >
              Clear selection
            </button>
          )}
        </div>
      ) : (
        <div className="agent-inspector">
          <section className="agent-inspector__section">
            <div className="agent-inspector__identity">
              <div>
                <h3>{agent.name}</h3>
                <p>{formatLabel(agent.occupation)}</p>
              </div>
              <span className="agent-inspector__status">
                {formatLabel(agent.status)}
              </span>
            </div>
            <dl className="agent-inspector__details">
              <div>
                <dt>Location</dt>
                <dd>{location?.name ?? agent.location_id}</dd>
              </div>
              <div>
                <dt>Agent ID</dt>
                <dd>{agent.id}</dd>
              </div>
            </dl>
          </section>

          <section className="agent-inspector__section">
            <h3>Needs</h3>
            <dl className="agent-inspector__details">
              <div><dt>Hunger</dt><dd>{agent.hunger}</dd></div>
              <div><dt>Energy</dt><dd>{agent.energy}</dd></div>
              <div><dt>Health</dt><dd>{agent.health}</dd></div>
            </dl>
          </section>

          <section className="agent-inspector__section">
            <h3>Resources</h3>
            <dl className="agent-inspector__details">
              <div><dt>Money</dt><dd>{agent.money}</dd></div>
            </dl>
            {Object.keys(agent.inventory).length === 0 ? (
              <p className="agent-inspector__empty">No inventory.</p>
            ) : (
              <dl className="agent-inspector__details">
                {Object.entries(agent.inventory).map(([resource, quantity]) => (
                  <div key={resource}>
                    <dt>{formatLabel(resource)}</dt>
                    <dd>{quantity}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>

          <section className="agent-inspector__section">
            <h3>Personality and goal</h3>
            {Object.keys(agent.personality_traits).length === 0 ? (
              <p className="agent-inspector__empty">No traits recorded.</p>
            ) : (
              <dl className="agent-inspector__details">
                {Object.entries(agent.personality_traits).map(([trait, value]) => (
                  <div key={trait}>
                    <dt>{formatLabel(trait)}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            )}
            <p className="agent-inspector__goal">
              {agent.active_goal ?? 'No active goal.'}
            </p>
          </section>

          <section className="agent-inspector__section">
            <h3>Recent actions</h3>
            {agent.recent_actions.length === 0 ? (
              <p className="agent-inspector__empty">No actions recorded.</p>
            ) : (
              <ul className="agent-inspector__list">
                {agent.recent_actions.map((action) => (
                  <li key={`${action.tick}-${action.summary}`}>
                    <strong>Tick {action.tick}</strong>
                    <span>{formatLabel(action.event_type)}</span>
                    <p>{action.summary}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="agent-inspector__section">
            <h3>Selected memories</h3>
            {agent.selected_retrieved_memories.length === 0 ? (
              <p className="agent-inspector__empty">No memories retrieved.</p>
            ) : (
              <ul className="agent-inspector__list">
                {agent.selected_retrieved_memories.map((memory) => (
                  <li key={memory.memory_id}>
                    <p>{memory.content}</p>
                    <span>
                      Tick {memory.creation_tick} · score {formatScore(memory.total_score)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </DashboardPanel>
  )
}
