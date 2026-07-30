import { describe, expect, it } from 'vitest'

import type { AgentSummary, LocationSummary } from '../../types/world'
import {
  buildSettlementCells,
  SETTLEMENT_SIZE,
} from './settlementMap'

const farm: LocationSummary = {
  id: 'farm',
  name: 'North Farm',
  location_type: 'farm',
  x: 1,
  y: 1,
  capacity: 10,
  inventory: { food: 20 },
}

const farmer: AgentSummary = {
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
}

describe('buildSettlementCells', () => {
  it('builds a complete 10 by 10 grid in row-major order', () => {
    const cells = buildSettlementCells([], [])

    expect(cells).toHaveLength(SETTLEMENT_SIZE * SETTLEMENT_SIZE)
    expect(cells[0]).toMatchObject({ x: 0, y: 0 })
    expect(cells[34]).toMatchObject({ x: 4, y: 3 })
    expect(cells[99]).toMatchObject({ x: 9, y: 9 })
  })

  it('places locations and their agents in the matching coordinate cell', () => {
    const cells = buildSettlementCells([farm], [farmer])
    const farmCell = cells.find(({ x, y }) => x === 1 && y === 1)

    expect(farmCell?.location).toEqual(farm)
    expect(farmCell?.agents).toEqual([farmer])
  })

  it('includes fence decorations around the farm terrain', () => {
    const cells = buildSettlementCells([], [])
    const fenceCell = cells.find(
      ({ x, y }) => x === 3 && y === 1,
    )

    expect(fenceCell?.decoration).toBe('fence')
  })

  it('ignores locations outside the supported settlement bounds', () => {
    const invalidLocation: LocationSummary = {
      ...farm,
      id: 'outside',
      x: 10,
    }

    const cells = buildSettlementCells([invalidLocation], [])

    expect(cells.every(({ location }) => location === null)).toBe(true)
  })
})
