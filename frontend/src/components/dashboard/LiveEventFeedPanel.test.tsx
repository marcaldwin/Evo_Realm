import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LiveEventFeedPanel } from './LiveEventFeedPanel'


describe('LiveEventFeedPanel', () => {
  it('filters events by type and reports a disconnected stream', () => {
    render(
      <LiveEventFeedPanel
        connectionStatus="disconnected"
        state={{
          events: [
            {
              id: 'event-2',
              tick: 2,
              event_type: 'conversation_message',
              timestamp: '2026-07-29T10:00:00Z',
              summary: 'Elena offered food.',
            },
            {
              id: 'event-1',
              tick: 1,
              event_type: 'food_consumed',
              timestamp: null,
              summary: 'Marco ate food.',
            },
          ],
          loading: false,
          error: null,
        }}
      />,
    )

    expect(screen.getByRole('status').textContent).toContain(
      'Live updates are disconnected',
    )

    fireEvent.change(screen.getByLabelText('Event type'), {
      target: { value: 'conversation_message' },
    })

    expect(screen.getByText('Elena offered food.')).not.toBeNull()
    expect(screen.queryByText('Marco ate food.')).toBeNull()
  })
})
