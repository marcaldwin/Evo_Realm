import doctorSpriteUrl from '../../assets/agents/doctor.png'
import farmerSpriteUrl from '../../assets/agents/farmer.png'
import leaderSpriteUrl from '../../assets/agents/leader.png'
import merchantSpriteUrl from '../../assets/agents/merchant.png'
import workerSpriteUrl from '../../assets/agents/worker.png'
import type { AgentOccupation } from '../../types/world'

export type AgentDirection = 'down' | 'right' | 'left' | 'up'

interface AgentSpriteProps {
  occupation: AgentOccupation
  direction?: AgentDirection
  walking?: boolean
}

const spriteUrls: Record<AgentOccupation, string> = {
  farmer: farmerSpriteUrl,
  merchant: merchantSpriteUrl,
  doctor: doctorSpriteUrl,
  worker: workerSpriteUrl,
  leader: leaderSpriteUrl,
}

export function AgentSprite({
  occupation,
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
      data-occupation={occupation}
      data-walking={walking}
      style={{ backgroundImage: `url("${spriteUrls[occupation]}")` }}
      aria-hidden="true"
    />
  )
}
