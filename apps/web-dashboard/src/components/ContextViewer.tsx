import { useState, useEffect } from 'react'

interface ContextData {
  state: Record<string, Record<string, number>>
  eta: { execution_count: number; success_rate: number; structural_drift: number } | null
  memory: { initialized: boolean; recent_count?: number }
  intents: { count: number; names: string[] }
  llm: { available: boolean; active: string | null; mode: string }
}

const AXIS_LABELS: Record<string, string> = {
  alpha: 'α Energy',
  beta: 'β Focus',
  gamma: 'γ Happy',
  delta: 'δ Bond',
  epsilon: 'ε Precision',
  theta: 'θ Novelty',
}

function Bar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? '#2ecc71' : value >= 0.4 ? '#f1c40f' : '#e74c3c'
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="bar-value">{value.toFixed(2)}</span>
    </div>
  )
}

export default function ContextViewer() {
  const [ctx, setCtx] = useState<ContextData | null>(null)

  useEffect(() => {
    const fetchCtx = async () => {
      try {
        const res = await fetch('/api/context/summary')
        if (res.ok) setCtx(await res.json())
      } catch {}
    }
    fetchCtx()
    const interval = setInterval(fetchCtx, 5000)
    return () => clearInterval(interval)
  }, [])

  if (!ctx) return <div className="panel-loading">Loading context...</div>

  return (
    <div className="context-viewer">
      <h2>Context</h2>

      {/* 8D State Matrix */}
      <div className="ctx-section">
        <h3>State Matrix</h3>
        {Object.entries(AXIS_LABELS).map(([axis, label]) => {
          const vals = ctx.state[axis]
          if (!vals)
            return (
              <div key={axis} className="bar-row">
                <span className="bar-label">{label}</span>
                <span className="bar-value">(no data)</span>
              </div>
            )
          const avg = Object.values(vals).reduce((a, b) => a + b, 0) / Object.values(vals).length
          return <Bar key={axis} value={avg} label={label} />
        })}
        {ctx.eta && (
          <div className="eta-info">
            η exec={ctx.eta.execution_count} success={ctx.eta.success_rate.toFixed(1) + '%'} drift=
            {ctx.eta.structural_drift.toFixed(4)}
          </div>
        )}
      </div>

      {/* Quick status */}
      <div className="ctx-section">
        <h3>Status</h3>
        <div className="ctx-grid">
          <div className="ctx-item">
            <span className="ctx-label">Memory</span>
            <span className="ctx-value">
              {ctx.memory.initialized ? '✅' : '❌'}
              {ctx.memory.recent_count !== undefined ? ` ${ctx.memory.recent_count} recent` : ''}
            </span>
          </div>
          <div className="ctx-item">
            <span className="ctx-label">Intents</span>
            <span className="ctx-value">{ctx.intents.count}</span>
          </div>
          <div className="ctx-item">
            <span className="ctx-label">LLM</span>
            <span className="ctx-value">
              {ctx.llm.available ? '✅' : '❌'} {ctx.llm.active || '(none)'}
            </span>
          </div>
        </div>
      </div>

      {/* Intent list */}
      {ctx.intents.names.length > 0 && (
        <div className="ctx-section">
          <h3>Intents ({ctx.intents.count})</h3>
          <div className="intent-list">
            {ctx.intents.names.map((name) => (
              <span key={name} className="intent-tag">
                {name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
