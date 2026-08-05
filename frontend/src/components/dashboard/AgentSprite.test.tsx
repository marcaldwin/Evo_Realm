import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AgentSprite } from './AgentSprite'

describe('AgentSprite', () => {
  it.each([
    'down',
    'right',
    'left',
    'up',
  ] as const)('renders the %s directional row', (direction) => {
    const { container } = render(
      <AgentSprite occupation="farmer" direction={direction} />,
    )
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite).not.toBeNull()
    expect(
      sprite?.classList.contains(`agent-sprite--${direction}`),
    ).toBe(true)
    expect(sprite?.getAttribute('data-direction')).toBe(direction)
    expect(sprite?.getAttribute('style')).toContain('farmer.png')
  })

  it('faces down by default', () => {
    const { container } = render(
      <AgentSprite occupation="farmer" />,
    )
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite?.getAttribute('data-direction')).toBe('down')
  })

  it('enables the walking animation only when requested', () => {
    const { container } = render(
      <AgentSprite occupation="farmer" walking />,
    )
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite?.classList.contains('agent-sprite--walking')).toBe(true)
    expect(sprite?.getAttribute('data-walking')).toBe('true')
  })

  it.each([
    'farmer',
    'merchant',
    'doctor',
    'worker',
    'leader',
  ] as const)('uses the %s occupation sheet', (occupation) => {
    const { container } = render(
      <AgentSprite occupation={occupation} />,
    )
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite?.getAttribute('data-occupation')).toBe(occupation)
    expect(sprite?.getAttribute('style')).toContain(
      `${occupation}.png`,
    )
  })
})
