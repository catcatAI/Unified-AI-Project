import { useState, useEffect, useRef } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(
      /`(.+?)`/g,
      '<code style="background:rgba(0,0,0,0.3);padding:2px 4px;border-radius:3px;font-size:0.9em">$1</code>'
    )
    .replace(/\n/g, '<br/>')
}

export default function ChatPanel() {
  const MAX_MESSAGES = 200
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  // The instance name is per user (a user may have named their own Angela),
  // so the role label is resolved from the backend instead of being hardcoded.
  const [aiName, setAiName] = useState('Angela')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let cancelled = false
    const resolveName = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/identity?user_id=dashboard_user', {
          signal: AbortSignal.timeout(5000),
        })
        if (!res.ok) return
        const data = await res.json()
        if (!cancelled && data?.ai_name) setAiName(data.ai_name)
      } catch {
        // A failed lookup keeps the default name — the panel stays usable.
      }
    }
    resolveName()
    return () => {
      cancelled = true
    }
  }, [])

  const connect = () => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${window.location.hostname}:8000/ws`)

    ws.onopen = () => {
      setConnected(true)
      // 後端 websocket_handler 強制 handshake（10s 內無 handshake 即 4001 斷線）
      ws.send(
        JSON.stringify({
          type: 'handshake',
          client_type: 'web-dashboard',
          client_version: '7.5.0-dev',
        })
      )
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
        reconnectRef.current = null
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      reconnectRef.current = setTimeout(connect, 3000)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_response') {
          setMessages((prev: Message[]) => {
            const next: Message[] = [
              ...prev,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: data.content,
                timestamp: Date.now(),
              },
            ]
            return next.length > MAX_MESSAGES ? next.slice(-MAX_MESSAGES) : next
          })
        }
      } catch {
        console.error('Failed to parse WebSocket message:', event.data)
      }
    }

    wsRef.current = ws
  }

  useEffect(() => {
    connect()
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return

    setMessages((prev: Message[]) => {
      const next: Message[] = [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'user',
          content: input,
          timestamp: Date.now(),
        },
      ]
      return next.length > MAX_MESSAGES ? next.slice(-MAX_MESSAGES) : next
    })

    wsRef.current.send(
      JSON.stringify({
        type: 'chat_message',
        data: { content: input, user_name: 'User' },
      })
    )

    setInput('')
  }

  return (
    <div className="chat-panel">
      <h2>Chat</h2>
      <div className="status">{connected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <span className="role">{msg.role === 'user' ? 'You' : aiName}</span>
            <p dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
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
