import farmerSpriteUrl from '../../assets/agents/farmer.png'

export type AgentDirection = 'down' | 'right' | 'left' | 'up'

interface AgentSpriteProps {
  direction?: AgentDirection
  walking?: boolean
}

export function AgentSprite({
  direction = 'down',
  walking = false,
}: AgentSpriteProps) {
  return (
    <span
      className={[
        'agent-sprite',
        `agent-sprite--${direction}`,
        walking ? 'agent-sprite--walking' : '',
      ].filter(Boolean).join(' ')}
      data-direction={direction}
      data-walking={walking}
      style={{ backgroundImage: `url("${farmerSpriteUrl}")` }}
      aria-hidden="true"
    />
  )
}
