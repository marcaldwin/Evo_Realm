import { useEffect, useRef, useState } from 'react'

import type {
  AgentSummary,
  LocationSummary,
} from '../../types/world'
import {
  AgentSprite,
  type AgentDirection,
} from './AgentSprite'
import {
  buildTilePath,
  getMovementDirection,
  type Coordinate,
} from './agentMovement'

interface AgentMapMarkerProps {
  agent: AgentSummary
  location: LocationSummary
  selected: boolean
  stackIndex: number
  stackCount: number
  onSelect: (agentId: string) => void
}

export const TILE_STEP_DURATION_MS = 300

export function AgentMapMarker({
  agent,
  location,
  selected,
  stackIndex,
  stackCount,
  onSelect,
}: AgentMapMarkerProps) {
  const initialCoordinate = {
    x: location.x,
    y: location.y,
  }
  const visualCoordinateRef =
    useRef<Coordinate>(initialCoordinate)
  const [visualCoordinate, setVisualCoordinate] =
    useState<Coordinate>(initialCoordinate)
  const [pendingSteps, setPendingSteps] =
    useState<Coordinate[]>([])
  const [direction, setDirection] =
    useState<AgentDirection>('down')
  const walking = pendingSteps.length > 0
  const horizontalOffset =
    (stackIndex - ((stackCount - 1) / 2)) * 16

  useEffect(() => {
    const destination = {
      x: location.x,
      y: location.y,
    }

    const pathFrame = window.requestAnimationFrame(() => {
      setPendingSteps(
        buildTilePath(
          visualCoordinateRef.current,
          destination,
        ),
      )
    })

    return () => window.cancelAnimationFrame(pathFrame)
  }, [location.x, location.y])

  useEffect(() => {
    const nextStep = pendingSteps[0]

    if (nextStep === undefined) {
      return undefined
    }

    let movementTimer: number | undefined
    const movementFrame = window.requestAnimationFrame(() => {
      const currentCoordinate = visualCoordinateRef.current
      setDirection(
        getMovementDirection(currentCoordinate, nextStep),
      )
      visualCoordinateRef.current = nextStep
      setVisualCoordinate(nextStep)

      movementTimer = window.setTimeout(() => {
        setPendingSteps((currentSteps) =>
          currentSteps.slice(1),
        )
      }, TILE_STEP_DURATION_MS)
    })

    return () => {
      window.cancelAnimationFrame(movementFrame)
      if (movementTimer !== undefined) {
        window.clearTimeout(movementTimer)
      }
    }
  }, [pendingSteps])

  return (
    <button
      className={
        selected
          ? 'settlement-agent settlement-agent--selected'
          : 'settlement-agent'
      }
      type="button"
      title={`${agent.name}, ${agent.occupation}, ${agent.status}`}
      aria-pressed={selected}
      data-visual-x={visualCoordinate.x}
      data-visual-y={visualCoordinate.y}
      style={{
        left: `${(visualCoordinate.x + 0.5) * 10}%`,
        top: `${(visualCoordinate.y + 0.5) * 10}%`,
        marginLeft: `${horizontalOffset}px`,
      }}
      onClick={() => onSelect(agent.id)}
    >
      {agent.occupation === 'farmer' ? (
        <AgentSprite
          direction={direction}
          walking={walking || agent.status === 'moving'}
        />
      ) : (
        agent.name.slice(0, 1).toUpperCase()
      )}
      <span className="settlement-agent__name">
        {agent.name}
      </span>
    </button>
  )
}
