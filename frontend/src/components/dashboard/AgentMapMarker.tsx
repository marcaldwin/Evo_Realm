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
  type ConfirmedAgentMove,
  type Coordinate,
} from './agentMovement'

interface AgentMapMarkerProps {
  agent: AgentSummary
  location: LocationSummary
  confirmedMove: ConfirmedAgentMove | null
  syncVersion: number
  selected: boolean
  stackIndex: number
  stackCount: number
  onSelect: (agentId: string) => void
}

export const TILE_STEP_DURATION_MS = 600
export const DESYNC_SNAP_DELAY_MS = 250

function coordinatesMatch(
  first: Coordinate,
  second: Coordinate,
): boolean {
  return first.x === second.x && first.y === second.y
}

export function AgentMapMarker({
  agent,
  location,
  confirmedMove,
  syncVersion,
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
  const activeDestinationRef = useRef<Coordinate | null>(null)
  const lastProcessedMoveSequence = useRef(
    confirmedMove?.sequence ?? -1,
  )
  const previousSyncVersion = useRef(syncVersion)
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
    const authoritativeCoordinate = {
      x: location.x,
      y: location.y,
    }
    const syncChanged = previousSyncVersion.current !== syncVersion
    previousSyncVersion.current = syncVersion

    if (syncChanged) {
      lastProcessedMoveSequence.current = Math.max(
        lastProcessedMoveSequence.current,
        confirmedMove?.sequence ?? -1,
      )
      activeDestinationRef.current = null
      visualCoordinateRef.current = authoritativeCoordinate

      const syncFrame = window.requestAnimationFrame(() => {
        setPendingSteps([])
        setVisualCoordinate(authoritativeCoordinate)
      })

      return () => window.cancelAnimationFrame(syncFrame)
    }

    const activeDestination = activeDestinationRef.current
    if (
      coordinatesMatch(
        visualCoordinateRef.current,
        authoritativeCoordinate,
      )
      || (
        activeDestination !== null
        && coordinatesMatch(
          activeDestination,
          authoritativeCoordinate,
        )
      )
    ) {
      return undefined
    }

    const snapTimer = window.setTimeout(() => {
      activeDestinationRef.current = null
      visualCoordinateRef.current = authoritativeCoordinate
      setPendingSteps([])
      setVisualCoordinate(authoritativeCoordinate)
    }, DESYNC_SNAP_DELAY_MS)

    return () => window.clearTimeout(snapTimer)
  }, [
    confirmedMove?.sequence,
    location.x,
    location.y,
    syncVersion,
  ])

  useEffect(() => {
    if (
      confirmedMove === null
      || confirmedMove.sequence
        <= lastProcessedMoveSequence.current
    ) {
      return undefined
    }

    lastProcessedMoveSequence.current = confirmedMove.sequence
    activeDestinationRef.current = confirmedMove.destination

    const pathFrame = window.requestAnimationFrame(() => {
      setPendingSteps(
        buildTilePath(
          visualCoordinateRef.current,
          confirmedMove.destination,
        ),
      )
    })

    return () => window.cancelAnimationFrame(pathFrame)
  }, [confirmedMove])

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
      <AgentSprite
        occupation={agent.occupation}
        direction={direction}
        walking={walking}
      />
      <span className="settlement-agent__name">
        {agent.name}
      </span>
    </button>
  )
}
