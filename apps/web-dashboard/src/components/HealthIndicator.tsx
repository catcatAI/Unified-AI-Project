import { useState, useEffect } from 'react'

interface HealthData {
  status: string
  cpu_percent: number
  memory_percent: number
  disk_percent: number
}

export default function HealthIndicator() {
  const [health, setHealth] = useState<HealthData | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('/api/ops/health')
        if (res.ok) {
          setHealth(await res.json())
        }
      } catch {}
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  if (!health) return <span className="health-badge health-unknown">⏳</span>

  const color =
    health.status === 'healthy'
      ? 'health-ok'
      : health.status === 'degraded'
        ? 'health-warn'
        : 'health-err'

  return (
    <span
      className={`health-badge ${color}`}
      title={`CPU ${health.cpu_percent.toFixed(0)}% · MEM ${health.memory_percent.toFixed(0)}%`}
    >
      {health.status === 'healthy' ? '🟢' : health.status === 'degraded' ? '🟡' : '🔴'}{' '}
      {health.status}
    </span>
  )
}
