import { useState } from 'react'

import './App.css'

import { DashboardLayout } from './components/dashboard/DashboardLayout'
import { useActiveWorld } from './hooks/useActiveWorld'
import { useAgentInspector } from './hooks/useAgentInspector'
import { useBackendConnection } from './hooks/useBackendConnection'
import { useWorldControls } from './hooks/useWorldControls'
import { useWorldEvents } from './hooks/useWorldEvents'
import { useWorldMetrics } from './hooks/useWorldMetrics'
import { useWorldStream } from './hooks/useWorldStream'
import { useWorldSnapshot } from './hooks/useWorldSnapshot'

function App() {
  const [selectedAgent, setSelectedAgent] = useState<{
    worldId: string
    agentId: string
  } | null>(null)
  const backendStatus = useBackendConnection()
  const { world } = useActiveWorld()
  const worldId = world?.id ?? null
  const {
    status: websocketStatus,
    latestEvent,
    latestTickSequence,
    events: streamEvents,
    connectionVersion,
  } = useWorldStream(worldId)
  const {
    snapshot: worldSnapshot,
    loading: worldSnapshotLoading,
    error: worldSnapshotError,
    adoptSnapshot,
  } = useWorldSnapshot(
    worldId,
    latestTickSequence,
    connectionVersion,
  )
  const worldControls = useWorldControls(worldId, adoptSnapshot)
  const worldMetrics = useWorldMetrics(
    worldId,
    latestTickSequence,
    connectionVersion,
    worldControls.completionVersion,
  )
  const worldEvents = useWorldEvents(
    worldId,
    streamEvents,
    connectionVersion,
    worldControls.completionVersion,
  )
  const selectedAgentId = (
    selectedAgent !== null
    && selectedAgent.worldId === world?.id
  )
    ? selectedAgent.agentId
    : null
  const agentInspectorState = useAgentInspector(
    worldId,
    selectedAgentId,
    latestEvent,
  )

  return (
    <DashboardLayout
      backendStatus={backendStatus}
      websocketStatus={websocketStatus}
      worldSnapshot={worldSnapshot}
      worldSnapshotLoading={worldSnapshotLoading}
      worldSnapshotError={worldSnapshotError}
      worldControls={worldControls}
      worldMetrics={worldMetrics}
      worldEvents={worldEvents}
      streamEvents={streamEvents}
      connectionVersion={connectionVersion}
      selectedAgentId={selectedAgentId}
      onAgentSelect={(agentId) => {
        if (world !== null) {
          setSelectedAgent({
            worldId: world.id,
            agentId,
          })
        }
      }}
      agentInspectorState={agentInspectorState}
      onClearAgentSelection={() => setSelectedAgent(null)}
    />
  )
}

export default App
