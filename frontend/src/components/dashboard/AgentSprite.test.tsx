import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AgentSprite } from './AgentSprite'

describe('AgentSprite', () => {
  it('renders the requested directional row from the farmer sheet', () => {
    const { container } = render(<AgentSprite direction="left" />)
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite).not.toBeNull()
    expect(sprite?.classList.contains('agent-sprite--left')).toBe(true)
    expect(sprite?.getAttribute('data-direction')).toBe('left')
    expect(sprite?.getAttribute('style')).toContain('farmer.png')
  })

  it('faces down by default', () => {
    const { container } = render(<AgentSprite />)
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite?.getAttribute('data-direction')).toBe('down')
  })

  it('enables the walking animation only when requested', () => {
    const { container } = render(<AgentSprite walking />)
    const sprite = container.querySelector('.agent-sprite')

    expect(sprite?.classList.contains('agent-sprite--walking')).toBe(true)
    expect(sprite?.getAttribute('data-walking')).toBe('true')
  })
})
