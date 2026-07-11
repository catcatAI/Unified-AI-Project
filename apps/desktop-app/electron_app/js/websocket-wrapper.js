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
  constructor(url, options) {
    super()
    this.url = url
    this.CONNECTING = 0
    this.OPEN = 1
    this.CLOSING = 2
    this.CLOSED = 3
    this.readyState = this.CONNECTING
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

    if (this.readyState === this.CONNECTING) {
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

    this.readyState = this.OPEN
    this._buffer = body
    this.emit('open')
    if (this._buffer.length > 0) this._processFrame()
  }

  _processFrame() {
    while (this._buffer.length >= 2) {
      const firstByte = this._buffer[0]
      const secondByte = this._buffer[1]
      const opcode = firstByte & 0x0f
      const rsv = firstByte & 0x70
      if (rsv !== 0) {
        // Invalid frame with reserved bits - log but try to recover
        const textPreview = this._buffer.slice(0, Math.min(50, this._buffer.length)).toString('utf8')
        console.warn('[NativeWS] Received frame with RSV bits set (ignoring). firstByte=0x' + firstByte.toString(16) + ', text="...' + textPreview.replace(/[\r\n]/g, ' ') + '"')
        // Clear this byte and try to resync
        this._buffer = this._buffer.slice(1)
        continue  // Skip this byte and try again
      }
      const masked = (secondByte & 0x80) !== 0
      let payloadLen = secondByte & 0x7f

      let headerLen = 2
      if (payloadLen === 126) {
        if (this._buffer.length < 4) return
        payloadLen = this._buffer.readUInt16BE(2)
        headerLen = 4
      } else if (payloadLen === 127) {
        if (this._buffer.length < 10) return
        const high = this._buffer.readUInt32BE(2)
        const low = this._buffer.readUInt32BE(6)
        payloadLen = low
        headerLen = 10
      }

      const dataStart = headerLen + (masked ? 4 : 0)
      if (this._buffer.length < dataStart + payloadLen) return

      let payload
      if (masked) {
        const mask = this._buffer.slice(headerLen, headerLen + 4)
        payload = Buffer.alloc(payloadLen)
        for (let i = 0; i < payloadLen; i++) {
          payload[i] = this._buffer[dataStart + i] ^ mask[i % 4]
        }
      } else {
        payload = this._buffer.slice(dataStart, dataStart + payloadLen)
      }

      this._buffer = this._buffer.slice(dataStart + payloadLen)
      this._handleOpcode(opcode, payload)
    }
  }

  _handleOpcode(opcode, payload) {
    switch (opcode) {
      case 0x1:
        this.emit('message', payload.toString('utf8'))
        break
      case 0x2:
        this.emit('message', payload)
        break
      case 0x8:
        this._socket.end()
        this.emit('close', 1005, Buffer.alloc(0))
        break
      case 0x9:
        this._sendFrame(0xA, payload)
        break
      case 0xA:
        break
    }
  }

  _sendFrame(opcode, data) {
    if (this.readyState !== this.OPEN) return

    const payload = Buffer.isBuffer(data) ? data : Buffer.from(String(data), 'utf8')
    const payloadLen = payload.length

    const mask = crypto.randomBytes(4)

    let headerLen = 2
    if (payloadLen > 125) {
      if (payloadLen > 65535) {
        headerLen = 10
      } else {
        headerLen = 4
      }
    }

    const frame = Buffer.alloc(headerLen + 4 + payloadLen)

    // Byte 0: FIN=1 (0x80), RSV=000, opcode
    frame[0] = 0x80 | opcode

    // Byte 1: MASK=1 (0x80), length
    if (payloadLen <= 125) {
      frame[1] = 0x80 | payloadLen
    } else if (payloadLen <= 65535) {
      frame[1] = 0x80 | 126
      frame.writeUInt16BE(payloadLen, 2)
    } else {
      frame[1] = 0x80 | 127
      frame[2] = 0
      frame[3] = 0
      frame[4] = 0
      frame[5] = 0
      frame.writeUInt32BE(payloadLen, 6)
    }

    // Copy mask key
    mask.copy(frame, headerLen)

    // Apply mask to payload
    const payloadStart = headerLen + 4
    for (let i = 0; i < payloadLen; i++) {
      frame[payloadStart + i] = payload[i] ^ mask[i % 4]
    }

    // Debug: log first few bytes
    const hexDump = frame.slice(0, Math.min(16, frame.length)).toString('hex')
    console.debug('[NativeWS] Sending frame: opcode=0x' + opcode.toString(16) + ', payloadLen=' + payloadLen + ', firstBytes=' + hexDump)

    this._socket.write(frame)
  }

  send(data) {
    this._sendFrame(0x1, data)
  }

  close() {
    if (this.readyState === this.OPEN) {
      this._sendFrame(0x88, Buffer.alloc(0))
    }
    this._socket.end()
  }

  terminate() {
    this._socket.destroy()
  }

  _onClose() {
    this.readyState = this.CLOSED
    this.emit('close', 1006, Buffer.alloc(0))
  }
}

module.exports = WebSocketConnection