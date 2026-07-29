export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'

export interface HealthResponse {
  status: string
}