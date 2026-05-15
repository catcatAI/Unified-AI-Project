/**
 * WebSocket wrapper for Electron main process
 *
 * Uses native Node.js net module to avoid pnpm cross-workspace symlink
 * permission issues on Windows. Implements WebSocket client protocol manually.
 */

const net = require('net')
const events = require('events')
const crypto = require('crypto')

const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

function generateKey() {
  return crypto.randomBytes(16).toString('base64')
}

function generateAccept(key) {
  return crypto.createHash('sha1').update(key + GUID).digest('base64')
}

class WebSocketConnection extends events.EventEmitter {
  constructor(url) {
    super()
    this.url = url
    this.readyState = 'CONNECTING'
    this._socket = null
    this._buffer = Buffer.alloc(0)
    this._headers = {}

    this._parseUrl(url)
    this._connect()
  }

  _parseUrl(url) {
    const match = url.match(/^ws:\/\/([^\/:]+)(?::(\d+))?(\/.*)?$/)
    if (!match) throw new Error('Invalid WebSocket URL')
    this.host = match[1]
    this.port = parseInt(match[2] || '80', 10)
    this.path = match[3] || '/'
  }

  _connect() {
    this._socket = new net.Socket()
    this._socket.on('connect', () => this._sendHandshake())
    this._socket.on('data', (data) => this._onData(data))
    this._socket.on('close', () => this._onClose())
    this._socket.on('error', (err) => this.emit('error', err))
    this._socket.connect(this.port, this.host)
  }

  _sendHandshake() {
    const key = generateKey()
    const upgradeReq = [
      `GET ${this.path} HTTP/1.1`,
      `Host: ${this.host}:${this.port}`,
      `Upgrade: websocket`,
      `Connection: Upgrade`,
      `Sec-WebSocket-Version: 13`,
      `Sec-WebSocket-Key: ${key}`,
      '',
      '',
    ].join('\r\n')

    this._socket.write(upgradeReq)
    this._handshakeKey = key
  }

  _onData(data) {
    this._buffer = Buffer.concat([this._buffer, data])

    if (this.readyState === 'CONNECTING') {
      this._processHandshake()
    } else {
      this._processFrame()
    }
  }

  _processHandshake() {
    const str = this._buffer.toString('utf8', 0, Math.min(this._buffer.length, 4096))
    if (!str.includes('\r\n\r\n')) return

    const headerEnd = str.indexOf('\r\n\r\n')
    const headerStr = str.substring(0, headerEnd)
    const body = this._buffer.slice(headerEnd + 4)

    if (!headerStr.includes('HTTP/1.1 101')) {
      this._socket.end()
      this.emit('error', new Error('WebSocket handshake failed'))
      return
    }

    this.readyState = 'OPEN'
    this._buffer = body
    this.emit('open')
    if (this._buffer.length > 0) this._processFrame()
  }

  _processFrame() {
    while (this._buffer.length >= 2) {
      const firstByte = this._buffer[0]
      const secondByte = this._buffer[1]
      const opcode = firstByte & 0x0f
      const isFinal = (firstByte & 0x80) !== 0
      const masked = (secondByte & 0x80) !== 0
      let payloadLen = secondByte & 0x7f

      let offset = 2
      if (payloadLen === 126) {
        if (this._buffer.length < 4) return
        payloadLen = this._buffer.readUInt16BE(2)
        offset = 4
      } else if (payloadLen === 127) {
        if (this._buffer.length < 10) return
        payloadLen = this._buffer.readUInt32BE(6) // Just use lower 32 bits
        offset = 10
      }

      if (masked) {
        if (this._buffer.length < offset + 4) return
        const mask = this._buffer.slice(offset, offset + 4)
        offset += 4

        if (this._buffer.length < offset + payloadLen) return
        const payload = Buffer.from(this._buffer.slice(offset, offset + payloadLen))
        for (let i = 0; i < payload.length; i++) {
          payload[i] ^= mask[i % 4]
        }
        this._buffer = this._buffer.slice(offset + payloadLen)

        this._handleOpcode(opcode, payload)
      } else {
        if (this._buffer.length < offset + payloadLen) return
        const payload = this._buffer.slice(offset, offset + payloadLen)
        this._buffer = this._buffer.slice(offset + payloadLen)
        this._handleOpcode(opcode, payload)
      }
    }
  }

  _handleOpcode(opcode, payload) {
    switch (opcode) {
      case 0x1: // Text
        this.emit('message', payload.toString('utf8'))
        break
      case 0x2: // Binary
        this.emit('message', payload)
        break
      case 0x8: // Close
        this._socket.end()
        this.emit('close', 1005, Buffer.alloc(0))
        break
      case 0x9: // Ping
        this._sendFrame(0x10, payload) // Pong
        break
      case 0xA: // Pong - ignore
        break
    }
  }

  _sendFrame(opcode, data) {
    if (this.readyState !== 'OPEN') return

    const payload = Buffer.isBuffer(data) ? data : Buffer.from(data, 'utf8')
    const payloadLen = payload.length

    let frameLen = 2 + payloadLen
    if (payloadLen > 65535) frameLen += 8
    else if (payloadLen > 125) frameLen += 2

    const frame = Buffer.alloc(frameLen)
    frame[0] = 0x80 | opcode // FIN + opcode

    if (payloadLen <= 125) {
      frame[1] = payloadLen
    } else if (payloadLen <= 65535) {
      frame[1] = 126
      frame.writeUInt16BE(payloadLen, 2)
    } else {
      frame[1] = 127
      frame.writeUInt32BE(0, 2)
      frame.writeUInt32BE(payloadLen, 6)
    }

    payload.copy(frame, frameLen - payloadLen)
    this._socket.write(frame)
  }

  send(data) {
    this._sendFrame(0x81, data)
  }

  close() {
    if (this.readyState === 'OPEN') {
      this._sendFrame(0x88, Buffer.alloc(0))
    }
    this._socket.end()
  }

  terminate() {
    this._socket.destroy()
  }

  _onClose() {
    this.readyState = 'CLOSED'
    this.emit('close', 1006, Buffer.alloc(0))
  }
}

module.exports = WebSocketConnection