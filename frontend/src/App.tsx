import { useState, useEffect } from 'react'
import { getHealth, type HealthResponse } from './services/api'
import { ModelStatus } from './components/ModelStatus'

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function checkStatus() {
      try {
        const healthData = await getHealth()
        setHealth(healthData)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to connect')
      }
    }
    checkStatus()
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>MAI Framework V2</h1>
          <p style={{ margin: '0.25rem 0 0', color: '#6b7280', fontSize: '0.875rem' }}>
            Mac Studio Hybrid Edition
          </p>
        </div>
        <ModelStatus />
      </header>

      {error && (
        <div style={{
          color: '#991b1b',
          padding: '1rem',
          background: '#fee2e2',
          borderRadius: '0.5rem',
          marginBottom: '1rem'
        }}>
          Error: {error}
        </div>
      )}

      {health && (
        <div style={{
          background: '#f9fafb',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{ margin: '0 0 1rem', fontSize: '1.125rem' }}>System Status</h2>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            <div>
              <span style={{ color: '#6b7280' }}>Status: </span>
              <span style={{
                color: health.status === 'healthy' ? '#166534' : '#991b1b',
                fontWeight: 500
              }}>
                {health.status}
              </span>
            </div>
            <div>
              <span style={{ color: '#6b7280' }}>Version: </span>
              <span style={{ fontWeight: 500 }}>{health.version}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
