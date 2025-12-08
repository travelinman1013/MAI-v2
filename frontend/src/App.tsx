import { useState, useEffect } from 'react'
import { getHealth, getLLMStatus, type HealthResponse, type LLMStatusResponse } from './services/api'

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function checkStatus() {
      try {
        const [healthData, llmData] = await Promise.all([
          getHealth(),
          getLLMStatus().catch(() => null)
        ])
        setHealth(healthData)
        setLlmStatus(llmData)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to connect')
      }
    }
    checkStatus()
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>MAI Framework V2</h1>
      <p>Mac Studio Hybrid Edition</p>

      {error && (
        <div style={{ color: 'red', marginTop: '1rem' }}>
          Error: {error}
        </div>
      )}

      {health && (
        <div style={{ marginTop: '1rem' }}>
          <h2>System Status</h2>
          <p>Status: {health.status}</p>
          <p>Version: {health.version}</p>
        </div>
      )}

      {llmStatus && (
        <div style={{ marginTop: '1rem' }}>
          <h2>LLM Status</h2>
          <p>Provider: {llmStatus.provider}</p>
          <p>Connected: {llmStatus.connected ? 'Yes' : 'No'}</p>
          {llmStatus.model && <p>Model: {llmStatus.model}</p>}
          {llmStatus.error && <p style={{ color: 'red' }}>Error: {llmStatus.error}</p>}
        </div>
      )}
    </div>
  )
}

export default App
