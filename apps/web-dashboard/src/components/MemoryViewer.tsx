import { useState, useEffect } from 'react'

interface Memory {
  content: string
  type: string
  importance: number
  emotion: string
  timestamp?: string
}

interface MemoryResponse {
  initialized: boolean
  memories: Memory[]
  count?: number
  hint?: string
  error?: string
}

export default function MemoryViewer() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [initialized, setInitialized] = useState(true)
  const [hint, setHint] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const res = await fetch('/api/memories?limit=20')
        const data: MemoryResponse = await res.json()
        if (!res.ok) {
          setHint(data.error || `HTTP ${res.status}`)
          setInitialized(false)
          return
        }
        setInitialized(data.initialized)
        setHint(data.hint || data.error || null)
        if (data.initialized) {
          setMemories(data.memories || [])
        }
      } catch (err) {
        console.error('Failed to fetch memories:', err)
        setHint('Backend unreachable — is the backend running on :8000?')
        setInitialized(false)
      }
    }

    fetchMemories()
    const interval = setInterval(fetchMemories, 10000)
    return () => clearInterval(interval)
  }, [])

  const filteredMemories = memories.filter((m) => {
    const matchesSearch = m.content.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = category === 'all' || m.type === category
    return matchesSearch && matchesCategory
  })

  const formatDate = (timestamp?: string) => {
    if (!timestamp) return ''
    const d = new Date(timestamp)
    return isNaN(d.getTime()) ? '' : d.toLocaleString()
  }

  return (
    <div className="memory-viewer">
      <h2>Memory Viewer</h2>
      {!initialized && <div className="error-hint">⚠️ Memory system not initialized. {hint}</div>}
      {initialized && hint && <div className="error-hint">⚠️ {hint}</div>}
      <div className="filters">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search memories..."
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="all">All Categories</option>
          <option value="conversation">Conversation</option>
          <option value="fact">Fact</option>
          <option value="emotion">Emotion</option>
          <option value="skill">Skill</option>
        </select>
      </div>
      <div className="memory-list">
        {filteredMemories.map((memory, i) => (
          <div key={i} className="memory-item">
            <div className="memory-header">
              <span className="category">{memory.type || 'unknown'}</span>
              <span className="importance">
                Importance: {(memory.importance * 100).toFixed(0)}%
              </span>
            </div>
            <p className="content">{memory.content}</p>
            {formatDate(memory.timestamp) && (
              <span className="timestamp">{formatDate(memory.timestamp)}</span>
            )}
          </div>
        ))}
        {initialized && filteredMemories.length === 0 && (
          <div className="empty-hint">
            No memories match. Talk to Angela first to build memories.
          </div>
        )}
      </div>
    </div>
  )
}
