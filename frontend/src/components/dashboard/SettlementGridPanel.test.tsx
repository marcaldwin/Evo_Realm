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
  locations: [
    {
      id: 'farm',
      name: 'North Farm',
      location_type: 'farm',
      x: 1,
      y: 1,
      capacity: 10,
      inventory: { food: 20 },
    },
    {
      id: 'market',
      name: 'Central Market',
      location_type: 'market',
      x: 4,
      y: 3,
      capacity: 20,
      inventory: { food: 100 },
    },
    {
      id: 'clinic',
      name: 'Community Clinic',
      location_type: 'clinic',
      x: 7,
      y: 3,
      capacity: 8,
      inventory: { medicine: 20 },
    },
    {
      id: 'home',
      name: 'Hilltop Home',
      location_type: 'home',
      x: 1,
      y: 5,
      capacity: 4,
      inventory: {},
    },
    {
      id: 'town-hall',
      name: 'Town Hall',
      location_type: 'town_hall',
      x: 4,
      y: 5,
      capacity: 12,
      inventory: {},
    },
    {
      id: 'workshop',
      name: 'East Workshop',
      location_type: 'workshop',
      x: 7,
      y: 7,
      capacity: 8,
      inventory: { wood: 30 },
    },
  ],
  events: [],
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
  it('renders every location type at its backend coordinate', () => {
    const { container } = render(
      <SettlementGridPanel
        worldSnapshot={worldSnapshot}
        loading={false}
        error={null}
        streamEvents={[]}
        connectionVersion={0}
        selectedAgentId={null}
        onAgentSelect={vi.fn()}
      />,
    )

    expect(screen.getAllByRole('gridcell')).toHaveLength(100)

    for (const location of worldSnapshot.locations) {
      const locationCell = screen.getByRole('gridcell', {
        name: new RegExp(
          `${location.name} at ${location.x}, ${location.y}`,
          'i',
        ),
      })

      expect(locationCell.textContent).toContain(location.name)
      expect(locationCell.getAttribute('data-coordinate')).toBe(
        `${location.x},${location.y}`,
      )
    }

    expect(
      container.querySelectorAll(
        '.settlement-decoration--fence',
      ),
    ).toHaveLength(3)
  })

  it('selects an agent when its button is clicked', () => {
    const onAgentSelect = vi.fn()

    render(
      <SettlementGridPanel
        worldSnapshot={worldSnapshot}
        loading={false}
        error={null}
        streamEvents={[]}
        connectionVersion={0}
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
