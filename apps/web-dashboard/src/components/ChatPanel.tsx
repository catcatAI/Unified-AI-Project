import { useState, useEffect, useRef } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws`)
    
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.content,
          timestamp: Date.now()
        }])
      }
    }
    
    wsRef.current = ws
    return () => ws.close()
  }, [])

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return
    
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    }])
    
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      content: input
    }))
    
    setInput('')
  }

  return (
    <div className="chat-panel">
      <h2>Chat</h2>
      <div className="status">
        {connected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <span className="role">{msg.role === 'user' ? 'You' : 'Angela'}</span>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  )
}
