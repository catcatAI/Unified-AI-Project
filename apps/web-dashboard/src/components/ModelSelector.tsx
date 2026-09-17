import { useState, useEffect, useCallback } from 'react'

interface Backend {
  name: string
  active: boolean
  health: string
  type: string
}

interface LLMStatus {
  available: boolean
  mode: string
  active: string | null
  backends: Backend[]
  stats: Record<string, unknown>
}

export default function ModelSelector() {
  const [status, setStatus] = useState<LLMStatus | null>(null)
  const [switching, setSwitching] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/llm/status')
      if (res.ok) setStatus(await res.json())
    } catch {}
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 8000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const handleSwitch = async (backendName: string) => {
    setSwitching(backendName)
    try {
      const res = await fetch('/api/llm/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backend: backendName }),
      })
      const data = await res.json()
      if (data.ok) {
        await fetchStatus()
      } else {
        alert(data.error || 'Switch failed')
      }
    } catch (e) {
      alert(`Switch error: ${e}`)
    } finally {
      setSwitching(null)
    }
  }

  if (!status) return <div className="panel-loading">Loading models...</div>

  return (
    <div className="model-selector">
      <h2>AI Models</h2>

      <div className="model-status">
        <span className={`status-badge ${status.available ? 'ok' : 'err'}`}>
          {status.available ? '✅' : '❌'} {status.mode}
        </span>
        {status.active && <span className="active-model">Active: <strong>{status.active}</strong></span>}
      </div>

      <table className="model-table">
        <thead>
          <tr>
            <th>Backend</th>
            <th>Type</th>
            <th>Health</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {status.backends.map((b) => (
            <tr key={b.name} className={b.active ? 'active-row' : ''}>
              <td>{b.active ? '★ ' : ''}{b.name}</td>
              <td>{b.type}</td>
              <td>
                <span className={`health-${b.health}`}>
                  {b.health === 'ok' ? '✅' : b.health === 'fail' ? '❌' : '❓'}
                </span>
              </td>
              <td>
                {!b.active && (
                  <button
                    className="btn-switch"
                    onClick={() => handleSwitch(b.name)}
                    disabled={switching !== null}
                  >
                    {switching === b.name ? '...' : 'Switch'}
                  </button>
                )}
                {b.active && <span className="active-label">active</span>}
              </td>
            </tr>
          ))}
          {status.backends.length === 0 && (
            <tr><td colSpan={4}>No backends registered</td></tr>
          )}
        </tbody>
      </table>

      {Object.keys(status.stats).length > 0 && (
        <div className="model-stats">
          <h3>Statistics</h3>
          {Object.entries(status.stats).map(([k, v]) => (
            <div key={k} className="config-row">
              <span className="label">{k}</span>
              <span className="value">{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
