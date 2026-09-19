import { useState, useEffect } from 'react'

interface ConfigData {
  deployment: { mode: string; selection: string }
  llm: {
    available: boolean
    mode: string
    active: string | null
    backends: Array<{ name: string; active: boolean; type: string }>
  }
  intents: { count: number; names: string[] }
  memory: { initialized: boolean }
  web_search: { enabled: boolean; provider: string }
  uptime_seconds: number
}

export default function ConfigPanel() {
  const [config, setConfig] = useState<ConfigData | null>(null)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch('/api/system/discovery')
        if (res.ok) setConfig(await res.json())
      } catch {}
    }
    fetchConfig()
    const interval = setInterval(fetchConfig, 10000)
    return () => clearInterval(interval)
  }, [])

  if (!config) return <div className="panel-loading">Loading config...</div>

  const modeIcon: Record<string, string> = {
    local: '🏠',
    'local+llm': '🔗',
    llm: '☁️',
    auto: '🤖',
  }

  const uptimeH = Math.floor(config.uptime_seconds / 3600)
  const uptimeM = Math.floor((config.uptime_seconds % 3600) / 60)

  return (
    <div className="config-panel">
      <h2>Configuration</h2>

      <div className="config-section">
        <h3>Deployment</h3>
        <div className="config-row">
          <span className="label">Mode</span>
          <span className="value">
            {modeIcon[config.deployment.mode] || '❓'} {config.deployment.mode}
          </span>
        </div>
        <div className="config-row">
          <span className="label">Selection</span>
          <span className="value">{config.deployment.selection}</span>
        </div>
        <div className="config-row">
          <span className="label">Uptime</span>
          <span className="value">
            {uptimeH}h {uptimeM}m
          </span>
        </div>
      </div>

      <div className="config-section">
        <h3>LLM</h3>
        <div className="config-row">
          <span className="label">Status</span>
          <span className="value">{config.llm.available ? '✅ available' : '❌ unavailable'}</span>
        </div>
        <div className="config-row">
          <span className="label">Mode</span>
          <span className="value">{config.llm.mode}</span>
        </div>
        <div className="config-row">
          <span className="label">Active</span>
          <span className="value">{config.llm.active || '(none)'}</span>
        </div>
      </div>

      <div className="config-section">
        <h3>Backends ({config.llm.backends.length})</h3>
        {config.llm.backends.map((b) => (
          <div key={b.name} className="config-row">
            <span className="label">
              {b.active ? '★' : '·'} {b.name}
            </span>
            <span className="value">{b.type}</span>
          </div>
        ))}
        {config.llm.backends.length === 0 && (
          <div className="config-row">
            <span className="value">(none registered)</span>
          </div>
        )}
      </div>

      <div className="config-section">
        <h3>System</h3>
        <div className="config-row">
          <span className="label">Intents</span>
          <span className="value">{config.intents.count}</span>
        </div>
        <div className="config-row">
          <span className="label">Memory</span>
          <span className="value">{config.memory.initialized ? '✅' : '❌'}</span>
        </div>
        <div className="config-row">
          <span className="label">Web Search</span>
          <span className="value">
            {config.web_search.enabled ? `✅ ${config.web_search.provider}` : '❌'}
          </span>
        </div>
      </div>
    </div>
  )
}
