import { useState } from 'react'

import './App.css'

import { DashboardLayout } from './components/dashboard/DashboardLayout'
import { useActiveWorld } from './hooks/useActiveWorld'
import { useAgentInspector } from './hooks/useAgentInspector'
import { useBackendConnection } from './hooks/useBackendConnection'
import { useWorldStream } from './hooks/useWorldStream'
import { useWorldSnapshot } from './hooks/useWorldSnapshot'

function App() {
  const [selectedAgent, setSelectedAgent] = useState<{
    worldId: string
    agentId: string
  } | null>(null)
  const backendStatus = useBackendConnection()
  const { world } = useActiveWorld()
  const { snapshot: worldSnapshot } = useWorldSnapshot(
    world?.id ?? null,
  )
  const {
    status: websocketStatus,
    latestEvent,
  } = useWorldStream(world?.id ?? null)
  const selectedAgentId = (
    selectedAgent !== null
    && selectedAgent.worldId === world?.id
  )
    ? selectedAgent.agentId
    : null
  const agentInspectorState = useAgentInspector(
    world?.id ?? null,
    selectedAgentId,
    latestEvent,
  )

  return (
    <DashboardLayout
      backendStatus={backendStatus}
      websocketStatus={websocketStatus}
      worldSnapshot={worldSnapshot}
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
