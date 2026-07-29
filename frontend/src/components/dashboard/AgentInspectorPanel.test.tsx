import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { AgentInspectorPanel } from './AgentInspectorPanel'
import type { AgentInspectorState } from '../../hooks/useAgentInspector'

const agentState: AgentInspectorState = {
  agent: {
    id: 'elena',
    name: 'Elena',
    occupation: 'farmer',
    location_id: 'farm',
    status: 'working',
    hunger: 20,
    energy: 80,
    health: 100,
    money: 5,
    inventory: { food: 2 },
    personality_traits: { kindness: 8 },
    active_goal: 'Grow food for the settlement.',
    recent_actions: [
      {
        tick: 4,
        event_type: 'farm_work_succeeded',
        location_id: 'farm',
        summary: 'Elena produced food.',
      },
    ],
    selected_retrieved_memories: [
      {
        memory_id: 'memory-1',
        content: 'The farm needs more food.',
        importance: 0.8,
        emotional_value: 0.2,
        creation_tick: 3,
        source_event_sequence: 2,
        source_agent_id: 'elena',
        semantic_similarity: 0.9,
        importance_score: 0.8,
        recency_score: 0.7,
        relationship_relevance: 0,
        total_score: 0.82,
      },
    ],
  },
  loading: false,
  error: null,
  notFound: false,
}

describe('AgentInspectorPanel', () => {
  it('renders an agent\'s inspector data', () => {
    render(
      <AgentInspectorPanel
        state={agentState}
        locations={[
          {
            id: 'farm',
            name: 'North Farm',
            location_type: 'farm',
            x: 2,
            y: 3,
            capacity: 5,
            inventory: {},
          },
        ]}
        onClearSelection={vi.fn()}
      />,
    )

    expect(screen.getByText('Elena')).not.toBeNull()
    expect(screen.getByText('North Farm')).not.toBeNull()
    expect(screen.getByText('Grow food for the settlement.')).not.toBeNull()
    expect(screen.getByText('Elena produced food.')).not.toBeNull()
    expect(screen.getByText('The farm needs more food.')).not.toBeNull()
  })

  it('shows a recoverable state when the selected agent is missing', () => {
    const onClearSelection = vi.fn()

    render(
      <AgentInspectorPanel
        state={{
          agent: null,
          loading: false,
          error: null,
          notFound: true,
        }}
        locations={[]}
        onClearSelection={onClearSelection}
      />,
    )

    fireEvent.click(
      screen.getByRole('button', { name: /clear selection/i }),
    )

    expect(onClearSelection).toHaveBeenCalledTimes(1)
  })
})
