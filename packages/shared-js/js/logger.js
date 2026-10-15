// 在安裝 console→Logger 橋之前，先捕獲「原始 console」——Logger 自身的輸出
// sink 必須走原始 console，否則橋把 console 路由回 Logger 會無限遞迴。
const _origConsole =
  typeof console !== 'undefined'
    ? {
        debug: console.debug.bind(console),
        info: console.info.bind(console),
        log: console.log.bind(console),
        warn: console.warn.bind(console),
        error: console.error.bind(console),
      }
    : { debug() {}, info() {}, log() {}, warn() {}, error() {} }

class Logger {
  constructor(config = {}) {
    this.config = {
      level: config.level || 'info',
      maxLogs: config.maxLogs || 1000,
      persist: config.persist !== false,
      persistInterval: config.persistInterval || 5000,
      prefix: config.prefix || '[Angela]',
    }

    this.levels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
      critical: 4,
    }

    this.currentLevel = this.levels[this.config.level] || 1
    this.logs = []
    this.listeners = []
    this.persistTimer = null

    this._initPersistence()
  }

  _initPersistence() {
    if (this.config.persist) {
      this._loadFromStorage()

      this.persistTimer = setInterval(() => {
        this._persistToStorage()
      }, this.config.persistInterval)

      window.addEventListener('beforeunload', () => {
        this._persistToStorage()
      })
    }
  }

  _shouldLog(level) {
    return this.levels[level] >= this.currentLevel
  }

  _formatMessage(level, message, data) {
    const timestamp = new Date().toISOString()
    return { timestamp, level, message, data }
  }

  _addLog(logEntry) {
    this.logs.push(logEntry)

    if (this.logs.length > this.config.maxLogs) {
      this.logs.shift()
    }

    this._notifyListeners(logEntry)
  }

  _notifyListeners(logEntry) {
    this.listeners.forEach((listener) => {
      try {
        listener(logEntry)
      } catch (e) {
        _origConsole.error('Logger listener error:', e)
      }
    })
  }

  debug(message, data = null) {
    if (!this._shouldLog('debug')) return

    const logEntry = this._formatMessage('debug', message, data)
    this._addLog(logEntry)

    _origConsole.debug(`${logEntry.timestamp} ${logEntry.prefix}`, message, data || '')
  }

  info(message, data = null) {
    if (!this._shouldLog('info')) return

    const logEntry = this._formatMessage('info', message, data)
    this._addLog(logEntry)

    _origConsole.info(`${logEntry.timestamp} ${logEntry.prefix}`, message, data || '')
  }

  warn(message, data = null) {
    if (!this._shouldLog('warn')) return

    const logEntry = this._formatMessage('warn', message, data)
    this._addLog(logEntry)

    _origConsole.warn(`${logEntry.timestamp} ${logEntry.prefix}`, message, data || '')
  }

  error(message, error = null) {
    if (!this._shouldLog('error')) return

    const errorData = error
      ? {
          name: error.name,
          message: error.message,
          stack: error.stack,
        }
      : null

    const logEntry = this._formatMessage('error', message, errorData)
    this._addLog(logEntry)

    _origConsole.error(`${logEntry.timestamp} ${logEntry.prefix}`, message, error || '')
  }

  critical(message, error = null) {
    if (!this._shouldLog('critical')) return

    const errorData = error
      ? {
          name: error.name,
          message: error.message,
          stack: error.stack,
        }
      : null

    const logEntry = this._formatMessage('critical', message, errorData)
    this._addLog(logEntry)

    _origConsole.error(`🚨 ${logEntry.timestamp} ${logEntry.prefix}`, message, error || '')
  }

  setLevel(level) {
    if (this.levels[level] !== undefined) {
      this.currentLevel = this.levels[level]
      this.config.level = level
      this.info(`Log level changed to: ${level}`)
    }
  }

  onLog(listener) {
    this.listeners.push(listener)
  }

  offLog(listener) {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  getLogs(level = null, limit = null) {
    let filtered = this.logs

    if (level && this.levels[level] !== undefined) {
      filtered = filtered.filter((log) => log.level === level)
    }

    if (limit) {
      filtered = filtered.slice(-limit)
    }

    return filtered
  }

  getRecentLogs(count = 10) {
    return this.logs.slice(-count)
  }

  getErrorLogs() {
    return this.logs.filter((log) => log.level === 'error' || log.level === 'critical')
  }

  clearLogs() {
    this.logs = []
    this.info('Logs cleared')
  }

  exportLogs() {
    return JSON.stringify(this.logs, null, 2)
  }

  _persistToStorage() {
    if (!this.config.persist) return

    try {
      const data = JSON.stringify(this.logs)
      localStorage.setItem('angela_logs', data)
    } catch (e) {
      _origConsole.error('Failed to persist logs:', e)
    }
  }

  _loadFromStorage() {
    if (!this.config.persist) return

    try {
      const data = localStorage.getItem('angela_logs')
      if (data) {
        this.logs = JSON.parse(data)
        this.info(`Loaded ${this.logs.length} logs from storage`)
      }
    } catch (e) {
      _origConsole.error('Failed to load logs from storage:', e)
    }
  }

  getStats() {
    const stats = {
      total: this.logs.length,
      byLevel: {},
    }

    Object.keys(this.levels).forEach((level) => {
      stats.byLevel[level] = this.logs.filter((log) => log.level === level).length
    })

    return stats
  }

  createModuleLogger(moduleName) {
    const logger = this

    return {
      debug: (msg, data) => logger.debug(`[${moduleName}] ${msg}`, data),
      info: (msg, data) => logger.info(`[${moduleName}] ${msg}`, data),
      warn: (msg, data) => logger.warn(`[${moduleName}] ${msg}`, data),
      error: (msg, err) => logger.error(`[${moduleName}] ${msg}`, err),
      critical: (msg, err) => logger.critical(`[${moduleName}] ${msg}`, err),
    }
  }

  destroy() {
    if (this.persistTimer) {
      clearInterval(this.persistTimer)
      this.persistTimer = null
    }

    this._persistToStorage()
  }
}

// ── console → Logger 橋（全域，載入 logger.js 即生效）──────────────────────
// 各共享腳本以全域 <script> 載入、非 ES module，內部大量裸 console.* 呼叫
// 繞過了 Logger（分級 + 持久化 + 監聽）。本橋在 logger.js 載入時**替換
// console.debug/info/log/warn/error**，把它們路由到 Logger —— 既有呼叫點
// 零改動即全部走正規日誌通道（console 恆存在，無 ReferenceError 風險）。
// Logger 未就緒（app.js 尚未建 window.angelaAppLogger）時降級直印 console，
// 維持可觀測。這把「繞過 Logger 的裸 console」根治為「分級持久化日誌」。
;(function installConsoleBridge() {
  if (typeof console === 'undefined' || console.__angelaBridged) return
  const orig = {
    debug: console.debug.bind(console),
    info: console.info.bind(console),
    log: console.log.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
  }
  const join = (args) =>
    args
      .map((a) => {
        if (typeof a === 'string') return a
        if (a instanceof Error) return a.stack || a.message
        try {
          return JSON.stringify(a)
        } catch {
          return String(a)
        }
      })
      .join(' ')
  const sink =
    (level) =>
    (...args) => {
      const lg = typeof window !== 'undefined' ? window.angelaAppLogger : null
      if (lg && typeof lg[level] === 'function') {
        lg[level](join(args))
      } else {
        // Logger 未就緒 —— 用原始 console 輸出（保留可觀測）
        orig[level === 'log' ? 'info' : level](...args)
      }
    }
  console.debug = sink('debug')
  console.info = sink('info')
  console.log = sink('info') // console.log 視為 info 級
  console.warn = sink('warn')
  console.error = sink('error')
  console.__angelaBridged = true
})()
