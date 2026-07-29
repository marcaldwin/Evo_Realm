import './App.css'

import { DashboardLayout } from './components/dashboard/DashboardLayout'
import { useActiveWorld } from './hooks/useActiveWorld'
import { useBackendConnection } from './hooks/useBackendConnection'
import { useWorldStream } from './hooks/useWorldStream'

function App() {
  const backendStatus = useBackendConnection()
  const { world } = useActiveWorld()
  const { status: websocketStatus } = useWorldStream(
    world?.id ?? null,
  )

  return (
    <DashboardLayout
      backendStatus={backendStatus}
      websocketStatus={websocketStatus}
    />
  )
}

export default App