import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SettlementGridPanel } from './SettlementGridPanel'
import type { WorldSnapshot } from '../../types/world'

const worldSnapshot: WorldSnapshot = {
  id: 'world-1',
  name: 'Test World',
  current_tick: 4,
  seed: 12,
  status: 'running',
  locations: [],
  agents: [
    {
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
    },
  ],
}

describe('SettlementGridPanel', () => {
  it('selects an agent when its button is clicked', () => {
    const onAgentSelect = vi.fn()

    render(
      <SettlementGridPanel
        worldSnapshot={worldSnapshot}
        selectedAgentId={null}
        onAgentSelect={onAgentSelect}
      />,
    )

    const agentButton = screen.getByRole('button', {
      name: /elena/i,
    })
    fireEvent.click(agentButton)

    expect(onAgentSelect).toHaveBeenCalledWith('elena')
  })
})
