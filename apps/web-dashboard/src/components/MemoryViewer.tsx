import { useState, useEffect } from 'react'

interface Memory {
  id: string
  content: string
  importance: number
  timestamp: number
  category: string
}

export default function MemoryViewer() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        const res = await fetch('/api/memories')
        if (res.ok) {
          const data = await res.json()
          setMemories(data)
        }
      } catch (err) {
        console.error('Failed to fetch memories:', err)
      }
    }
    
    fetchMemories()
    const interval = setInterval(fetchMemories, 10000)
    return () => clearInterval(interval)
  }, [])

  const filteredMemories = memories.filter(m => {
    const matchesSearch = m.content.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = category === 'all' || m.category === category
    return matchesSearch && matchesCategory
  })

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  return (
    <div className="memory-viewer">
      <h2>Memory Viewer</h2>
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
        {filteredMemories.map(memory => (
          <div key={memory.id} className="memory-item">
            <div className="memory-header">
              <span className="category">{memory.category}</span>
              <span className="importance">Importance: {(memory.importance * 100).toFixed(0)}%</span>
            </div>
            <p className="content">{memory.content}</p>
            <span className="timestamp">{formatDate(memory.timestamp)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
