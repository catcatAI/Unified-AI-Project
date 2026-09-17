import { useState, useEffect } from 'react'

interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  error?: string
}

export default function SystemMonitor() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
    disk: 0,
  })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/api/system/metrics')
        const data = await res.json()
        if (!res.ok) {
          setError(data.error || `HTTP ${res.status}`)
          return
        }
        setError(null)
        setMetrics(data)
      } catch (err) {
        setError('Backend unreachable')
        console.error('Failed to fetch metrics:', err)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 2000)
    return () => clearInterval(interval)
  }, [])

  const bar = (v: number) => '█'.repeat(Math.round(v / 10)).padEnd(10, '░')

  return (
    <div className="system-monitor">
      <h2>System Monitor</h2>
      {error && <div className="error-hint">⚠️ {error} — is the backend running on :8000?</div>}
      <div className="metrics">
        <div>CPU: {metrics.cpu.toFixed(1)}% [{bar(metrics.cpu)}]</div>
        <div>Memory: {metrics.memory.toFixed(1)}% [{bar(metrics.memory)}]</div>
        <div>Disk: {metrics.disk.toFixed(1)}% [{bar(metrics.disk)}]</div>
      </div>
    </div>
  )
}
