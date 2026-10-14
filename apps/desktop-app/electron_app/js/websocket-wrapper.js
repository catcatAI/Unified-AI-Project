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

class WebSocketConnection extends events.EventEmitter {
  constructor(url, _options) {
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
    this._fragments = null
    this._fragmentOpcode = 0

    this._parseUrl(url)
    this._connect()
  }

  _parseUrl(url) {
    // host 必须是捕获组 1：原正则 host 未分组，match[1]=port、match[2]=path
    // → this.host 拿到端口字符串、this.port = parseInt('/path') 恒 NaN，
    // net.connect 立刻抛 ERR_SOCKET_BAD_PORT（连接从未可能成功）
    const match = url.match(/^ws:\/\/([^/:]+)(?::(\d+))?(\/.*)?$/)
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

    // RFC 6455 §4.2.1: 客户端必须校验 Sec-WebSocket-Accept（GUID 此前是
    // 死常量，accept 从未验证——任何回 101 的服务端都会被接受）
    const acceptMatch = headerStr.match(/sec-websocket-accept:\s*(\S+)/i)
    const expectedAccept = crypto
      .createHash('sha1')
      .update(this._handshakeKey + GUID)
      .digest('base64')
    if (!acceptMatch || acceptMatch[1].trim() !== expectedAccept) {
      this._socket.end()
      this.emit(
        'error',
        new Error('WebSocket handshake accept mismatch (invalid Sec-WebSocket-Accept)')
      )
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
      const fin = (firstByte & 0x80) !== 0
      const opcode = firstByte & 0x0f
      const rsv = firstByte & 0x70
      if (rsv !== 0) {
        // RFC 6455: 未协商扩展时 RSV 必须为 0 —原「逐字节跳过重新对齐」
        // 会把失步的流当合法帧继续解析（伪恢复）。fail-closed + 明确报错。
        this.emit(
          'error',
          new Error(`Invalid WebSocket frame: RSV bits set (firstByte=0x${firstByte.toString(16)})`)
        )
        this._socket.destroy()
        return
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
        this._buffer.readUInt32BE(2)
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
      this._handleOpcode(opcode, payload, fin)
    }
  }

  _handleOpcode(opcode, payload, fin) {
    switch (opcode) {
      case 0x1:
      case 0x2:
        if (fin) {
          this.emit('message', opcode === 0x2 ? payload : payload.toString('utf8'))
        } else {
          // 分片消息：暂存 opcode，续帧（0x0）拼接完成后统一 emit
          this._fragmentOpcode = opcode
          this._fragments = [payload]
        }
        break
      case 0x0:
        if (this._fragments === null) {
          // 无首帧的 continuation = 协议错误（原 switch 无 0x0 分支，静默丢弃）
          this.emit('error', new Error('Unexpected WebSocket continuation frame'))
          this._socket.destroy()
          return
        }
        this._fragments.push(payload)
        if (fin) {
          const full = Buffer.concat(this._fragments)
          const op = this._fragmentOpcode
          this._fragments = null
          this._fragmentOpcode = 0
          this.emit('message', op === 0x2 ? full : full.toString('utf8'))
        }
        break
      case 0x8: {
        // 收到关闭帧：按 RFC 回帧、解析状态码、只发一次 close
        // （原不回帧、状态码恒 1005、随后 socket close 还会再发 1006）
        const code = payload.length >= 2 ? payload.readUInt16BE(0) : 1005
        if (this.readyState === this.OPEN) this._sendFrame(0x88, payload)
        this.readyState = this.CLOSED
        this._socket.end()
        this.emit('close', code, payload.length > 2 ? payload.slice(2) : Buffer.alloc(0))
        break
      }
      case 0x9:
        this._sendFrame(0xa, payload)
        break
      case 0xa:
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
    console.debug(
      '[NativeWS] Sending frame: opcode=0x' +
        opcode.toString(16) +
        ', payloadLen=' +
        payloadLen +
        ', firstBytes=' +
        hexDump
    )

    this._socket.write(frame)
  }

  send(data) {
    this._sendFrame(0x1, data)
  }

  close() {
    if (this.readyState === this.OPEN) {
      this._sendFrame(0x88, Buffer.alloc(0))
      // 主动关闭：_onClose 将报 1005（干净关闭）而非误报 1006（异常断开）
      this.readyState = this.CLOSING
    }
    this._socket.end()
  }

  terminate() {
    this._socket.destroy()
  }

  _onClose() {
    if (this.readyState === this.CLOSED) return // 0x8 路径已发过 close（原会双发）
    const localClose = this.readyState === this.CLOSING
    this.readyState = this.CLOSED
    this.emit('close', localClose ? 1005 : 1006, Buffer.alloc(0))
  }
}

module.exports = WebSocketConnection
