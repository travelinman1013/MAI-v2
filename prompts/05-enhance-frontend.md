# Task: Enhance Frontend with Model Status Component

**Project**: MAI-v2-Code-Quality (`/Users/maxwell/Projects/mai-v2`)
**Goal**: Add a ModelStatus component with auto-refresh and status indicator styles
**Sequence**: 5 of 6
**Depends On**: 04-add-backend-tests.md

---

## Archon Task Management (REQUIRED)

This task is managed via Archon. Update status as you work.

### Task Info

- **Task ID**: `9667a68c-de3e-4565-8e79-23366e3f1fb8`
- **Project ID**: `63fd8b5b-fde0-4034-bbd3-2a671551a348`

### Update Status

```bash
# Mark as in_progress when starting
curl -X PUT "http://localhost:8181/api/tasks/9667a68c-de3e-4565-8e79-23366e3f1fb8" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Mark as done when complete
curl -X PUT "http://localhost:8181/api/tasks/9667a68c-de3e-4565-8e79-23366e3f1fb8" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Context

Tasks 1-4 fixed the backend security issues and added tests. This task enhances the frontend with a visual model status indicator.

The current `frontend/src/App.tsx` displays LLM status in a basic text format. This task:
1. Creates a reusable `ModelStatus` component with a status indicator dot
2. Adds auto-refresh every 30 seconds
3. Updates the App layout to show the status in the header
4. Adds CSS styles for connected/disconnected states

The existing `frontend/src/services/api.ts` already has the `getLLMStatus()` function and `LLMStatusResponse` type that will be used.

---

## Requirements

### 1. Create Components Directory

```bash
mkdir -p /Users/maxwell/Projects/mai-v2/frontend/src/components
```

### 2. Create ModelStatus Component

Create `/Users/maxwell/Projects/mai-v2/frontend/src/components/ModelStatus.tsx`:

```tsx
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
```

### 3. Add Styles to index.css

Append the following styles to `/Users/maxwell/Projects/mai-v2/frontend/src/index.css`:

```css
/* Model Status Indicator */
.model-status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.model-status.loading {
  background: #f3f4f6;
  color: #6b7280;
}

.model-status.connected {
  background: #dcfce7;
  color: #166534;
}

.model-status.disconnected {
  background: #fee2e2;
  color: #991b1b;
}

.model-status.error {
  background: #fef3c7;
  color: #92400e;
}

.model-status .status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.model-status.loading .status-indicator {
  background: #9ca3af;
  animation: pulse 1.5s ease-in-out infinite;
}

.model-status.connected .status-indicator {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e;
}

.model-status.disconnected .status-indicator {
  background: #ef4444;
}

.model-status.error .status-indicator {
  background: #f59e0b;
}

.model-status .status-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 4. Update App.tsx

Replace `/Users/maxwell/Projects/mai-v2/frontend/src/App.tsx`:

```tsx
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
```

---

## Files to Create

- `frontend/src/components/ModelStatus.tsx` - Status indicator component

## Files to Modify

- `frontend/src/index.css` - Add status indicator styles
- `frontend/src/App.tsx` - Add ModelStatus to header

---

## Success Criteria

```bash
cd /Users/maxwell/Projects/mai-v2/frontend

# Verify component file exists
ls -la src/components/ModelStatus.tsx
# Expected: File exists

# Verify component can be imported (TypeScript check)
npx tsc --noEmit
# Expected: No errors

# Verify styles are in index.css
grep "model-status" src/index.css
# Expected: Shows .model-status styles

# Verify ModelStatus is imported in App.tsx
grep "ModelStatus" src/App.tsx
# Expected: Shows import and usage

# Build check
npm run build
# Expected: Build succeeds without errors
```

**Checklist:**
- [ ] `frontend/src/components/ModelStatus.tsx` exists
- [ ] Component fetches LLM status on mount
- [ ] Component auto-refreshes every 30 seconds
- [ ] Status indicator dot shows connected (green) / disconnected (red)
- [ ] Model name displayed when connected
- [ ] Styles added to `index.css`
- [ ] `App.tsx` updated with header layout
- [ ] TypeScript compiles without errors
- [ ] Build succeeds

---

## Technical Notes

- **Existing API**: `getLLMStatus()` and `LLMStatusResponse` are in `services/api.ts`
- **React hooks**: Use `useState` and `useEffect` for state and side effects
- **Cleanup**: Return cleanup function from `useEffect` to clear interval
- **CSS approach**: Use utility classes with semantic names

---

## Important

- Do NOT add any new npm dependencies
- Use the existing API functions from `services/api.ts`
- Ensure the component handles loading and error states gracefully
- The status indicator should be visible and clear at a glance

---

## On Completion

1. Mark Archon task as `done` using the command above
2. Verify ALL success criteria pass
3. The next task (06-improve-host-engine.md) depends on this completing successfully
