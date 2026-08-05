import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { WorldMetricsPanel } from './WorldMetricsPanel'


describe('WorldMetricsPanel', () => {
  it('renders the complete dashboard metric snapshot', () => {
    render(
      <WorldMetricsPanel
        state={{
          metrics: {
            world_id: 'world-1',
            current_tick: 12,
            status: 'running',
            total_food: 30,
            average_health: 92.5,
            successful_trades: 3,
            emergency_help_events: 2,
            rejected_actions: 4,
            active_conversations: 1,
          },
          loading: false,
          error: null,
        }}
      />,
    )

    expect(screen.getByText('12')).not.toBeNull()
    expect(screen.getByText('running')).not.toBeNull()
    expect(screen.getByText('30')).not.toBeNull()
    expect(screen.getByText('92.5')).not.toBeNull()
    expect(screen.getByText('3')).not.toBeNull()
    expect(screen.getByText('2')).not.toBeNull()
    expect(screen.getByText('4')).not.toBeNull()
    expect(screen.getByText('1')).not.toBeNull()
  })
})
