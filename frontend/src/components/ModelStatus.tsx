import { useEffect, useState } from 'react'
import { getLLMStatus, type LLMStatusResponse } from '../services/api'

interface ModelStatusProps {
  refreshInterval?: number
}

export function ModelStatus({ refreshInterval = 30000 }: ModelStatusProps) {
  const [status, setStatus] = useState<LLMStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStatus() {
      try {
        const data = await getLLMStatus()
        setStatus(data)
        setError(null)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch status')
        setStatus(null)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  if (loading) {
    return (
      <div className="model-status loading">
        <span className="status-indicator" />
        <span className="status-text">Loading...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="model-status error">
        <span className="status-indicator" />
        <span className="status-text">Error</span>
      </div>
    )
  }

  const isConnected = status?.connected ?? false
  const statusClass = isConnected ? 'connected' : 'disconnected'
  const displayText = isConnected
    ? (status?.model || 'Connected')
    : 'Disconnected'

  return (
    <div className={`model-status ${statusClass}`}>
      <span className="status-indicator" />
      <span className="status-text">{displayText}</span>
    </div>
  )
}
