import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { AgentRelationship } from '../../types/relationship'
import type { AgentSummary } from '../../types/world'
import { RelationshipGraphPanel } from './RelationshipGraphPanel'

const agents: AgentSummary[] = [
  {
    id: 'elena',
    name: 'Elena',
    occupation: 'farmer',
    location_id: 'farm',
    status: 'idle',
    hunger: 10,
    energy: 90,
    health: 100,
    money: 5,
    inventory: {},
  },
  {
    id: 'marco',
    name: 'Marco',
    occupation: 'merchant',
    location_id: 'market',
    status: 'idle',
    hunger: 20,
    energy: 80,
    health: 95,
    money: 20,
    inventory: {},
  },
  {
    id: 'sofia',
    name: 'Sofia',
    occupation: 'worker',
    location_id: 'workshop',
    status: 'idle',
    hunger: 15,
    energy: 85,
    health: 98,
    money: 12,
    inventory: {},
  },
]

const relationships: AgentRelationship[] = [
  {
    relationship_id: 'one',
    world_id: 'world-1',
    source_agent_id: 'elena',
    target_agent_id: 'marco',
    trust: 30,
    affection: 10,
    respect: 20,
    interaction_count: 3,
  },
  {
    relationship_id: 'two',
    world_id: 'world-1',
    source_agent_id: 'marco',
    target_agent_id: 'elena',
    trust: -60,
    affection: -30,
    respect: -30,
    interaction_count: 5,
  },
  {
    relationship_id: 'three',
    world_id: 'world-1',
    source_agent_id: 'elena',
    target_agent_id: 'sofia',
    trust: 5,
    affection: 5,
    respect: 5,
    interaction_count: 1,
  },
]

describe('RelationshipGraphPanel', () => {
  it('renders directed values and opens the inspector from a node', () => {
    const onAgentSelect = vi.fn()
    render(
      <RelationshipGraphPanel
        agents={agents}
        state={{ relationships, loading: false, error: null }}
        selectedAgentId={null}
        onAgentSelect={onAgentSelect}
      />,
    )

    expect(
      screen.getByRole('group', {
        name: 'Directed agent relationship graph',
      }),
    ).not.toBeNull()
    expect(screen.getByText('Elena → Marco')).not.toBeNull()
    expect(screen.getByText('Trust -60')).not.toBeNull()
    expect(screen.getByText('Affection 10')).not.toBeNull()
    expect(screen.getByText('Respect 20')).not.toBeNull()
    expect(screen.getByText('5 interactions')).not.toBeNull()

    fireEvent.click(
      screen.getByRole('button', { name: 'Inspect Marco' }),
    )
    expect(onAgentSelect).toHaveBeenCalledWith('marco')
  })

  it('filters edges by agent and relationship strength', () => {
    render(
      <RelationshipGraphPanel
        agents={agents}
        state={{ relationships, loading: false, error: null }}
        selectedAgentId="elena"
        onAgentSelect={vi.fn()}
      />,
    )

    fireEvent.change(screen.getByLabelText('Agent'), {
      target: { value: 'sofia' },
    })
    expect(screen.getByText('Elena → Sofia')).not.toBeNull()
    expect(screen.queryByText('Elena → Marco')).toBeNull()

    fireEvent.change(
      screen.getByLabelText('Minimum relationship strength'),
      { target: { value: '10' } },
    )
    expect(screen.queryByText('Elena → Sofia')).toBeNull()
    expect(
      screen.getByText('No relationships match the current filters.'),
    ).not.toBeNull()
  })
})
