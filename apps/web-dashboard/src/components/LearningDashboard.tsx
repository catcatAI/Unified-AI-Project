import { useState, useEffect } from 'react'

interface LearningStats {
  ed3nDictionarySize: number
  gardenQueryCount: number
  learningRate: number
  totalInteractions: number
  successRate: number
}

export default function LearningDashboard() {
  const [stats, setStats] = useState<LearningStats>({
    ed3nDictionarySize: 0,
    gardenQueryCount: 0,
    learningRate: 0,
    totalInteractions: 0,
    successRate: 0
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('/api/learning/stats')
        if (res.ok) {
          const data = await res.json()
          setStats(data)
        }
      } catch (err) {
        console.error('Failed to fetch learning stats:', err)
      }
    }
    
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="learning-dashboard">
      <h2>Learning Dashboard</h2>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>ED3N Dictionary</h3>
          <div className="value">{stats.ed3nDictionarySize}</div>
          <div className="label">Entries</div>
        </div>
        <div className="stat-card">
          <h3>GARDEN Queries</h3>
          <div className="value">{stats.gardenQueryCount}</div>
          <div className="label">Total Queries</div>
        </div>
        <div className="stat-card">
          <h3>Learning Rate</h3>
          <div className="value">{(stats.learningRate * 100).toFixed(1)}%</div>
          <div className="label">Success Rate</div>
        </div>
        <div className="stat-card">
          <h3>Total Interactions</h3>
          <div className="value">{stats.totalInteractions}</div>
          <div className="label">Processed</div>
        </div>
      </div>
    </div>
  )
}
