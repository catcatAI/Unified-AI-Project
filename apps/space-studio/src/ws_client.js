/**
 * =============================================================================
 * ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
 * =============================================================================
 * Space socket — subscribe to the authoritative stage, send actions back.
 *
 * Degrades deliberately: without a WebSocket (or when the backend is down) the
 * stage keeps running locally. "No backend" is a mode, not a crash.
 */

export function createSpaceSocket({
  url,
  roomId = 'studio_a',
  WebSocketImpl = globalThis.WebSocket,
  onSnapshot = () => {},
  onStatus = () => {},
  autoReconnect = true,
  reconnectDelayMs = 2000,
  schedule = (fn, ms) => setTimeout(fn, ms),
} = {}) {
  const state = { socket: null, status: 'idle', closed: false }

  if (!url) throw new Error('space socket needs a url')
  if (!WebSocketImpl) {
    state.status = 'unsupported'
    onStatus('unsupported')
  }

  const setStatus = (status) => {
    state.status = status
    onStatus(status)
  }

  const endpoint = () => `${url}?room_id=${encodeURIComponent(roomId)}`

  function connect() {
    if (!WebSocketImpl) return false
    if (state.socket) return true
    const socket = new WebSocketImpl(endpoint())
    state.socket = socket

    socket.onopen = () => setStatus('connected')
    socket.onerror = () => setStatus('error')
    socket.onmessage = (event) => {
      let message = null
      try {
        message = JSON.parse(event.data)
      } catch {
        return // one malformed frame must not break the feed
      }
      if (message && message.type === 'space.snapshot') onSnapshot(message)
    }
    socket.onclose = () => {
      state.socket = null
      setStatus('closed')
      if (autoReconnect && !state.closed) schedule(() => connect(), reconnectDelayMs)
    }
    return true
  }

  function send(action) {
    const socket = state.socket
    if (!socket || socket.readyState !== 1) return false
    socket.send(JSON.stringify({ type: 'space.action', data: action }))
    return true
  }

  function close() {
    state.closed = true
    if (state.socket) state.socket.close()
    state.socket = null
    setStatus('closed')
  }

  return {
    connect,
    send,
    close,
    get status() {
      return state.status
    },
  }
}
