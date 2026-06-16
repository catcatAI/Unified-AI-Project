import { useState, useEffect } from 'react'

interface SystemMetrics {
  cpu: number
  memory: number
  uptime: number
  activeConnections: number
  totalInteractions: number
}

export default function SystemMonitor() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
    uptime: 0,
    activeConnections: 0,
    totalInteractions: 0
  })

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/api/system/metrics')
        if (res.ok) {
          const data = await res.json()
          setMetrics(data)
        }
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
      }
    }
    
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 2000)
    return () => clearInterval(interval)
  }, [])

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  return (
    <div className="system-monitor">
      <h2>System Monitor</h2>
      <div className="metrics">
        <div>CPU: {metrics.cpu.toFixed(1)}%</div>
        <div>Memory: {metrics.memory.toFixed(1)}%</div>
        <div>Uptime: {formatUptime(metrics.uptime)}</div>
        <div>Connections: {metrics.activeConnections}</div>
        <div>Interactions: {metrics.totalInteractions}</div>
      </div>
    </div>
  )
}
