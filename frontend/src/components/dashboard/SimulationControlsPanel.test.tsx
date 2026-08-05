import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SimulationControlsPanel } from './SimulationControlsPanel'
import type { WorldControlsState } from '../../hooks/useWorldControls'

function createControls(
  overrides: Partial<WorldControlsState> = {},
): WorldControlsState {
  return {
    pendingCommand: null,
    error: null,
    completionVersion: 0,
    execute: vi.fn(),
    ...overrides,
  }
}

describe('SimulationControlsPanel', () => {
  it('enables controls that match the world lifecycle state', () => {
    const controls = createControls()

    render(
      <SimulationControlsPanel
        worldStatus="created"
        controls={controls}
      />,
    )

    const start = screen.getByRole('button', { name: 'Start' })
    const pause = screen.getByRole('button', { name: 'Pause' })
    const resume = screen.getByRole('button', { name: 'Resume' })
    const step = screen.getByRole('button', {
      name: 'Step one tick',
    })

    expect((start as HTMLButtonElement).disabled).toBe(false)
    expect((pause as HTMLButtonElement).disabled).toBe(true)
    expect((resume as HTMLButtonElement).disabled).toBe(true)
    expect((step as HTMLButtonElement).disabled).toBe(false)

    fireEvent.click(start)

    expect(controls.execute).toHaveBeenCalledWith('start')
  })

  it('disables every command while one is pending and shows errors', () => {
    render(
      <SimulationControlsPanel
        worldStatus="running"
        controls={createControls({
          pendingCommand: 'pause',
          error: 'Database unavailable',
        })}
      />,
    )

    for (const button of screen.getAllByRole('button')) {
      expect((button as HTMLButtonElement).disabled).toBe(true)
    }
    expect(screen.getByRole('alert').textContent).toContain(
      'Database unavailable',
    )
  })
})
