const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
const websocketBaseUrl = import.meta.env.VITE_WS_BASE_URL

if (!apiBaseUrl || !websocketBaseUrl) {
  throw new Error('Backend connection settings are missing')
}

export const environment = {
  apiBaseUrl,
  websocketBaseUrl,
} as const