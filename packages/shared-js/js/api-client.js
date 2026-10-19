/**
 * =============================================================================
 * ANGELA-MATRIX: L6[Execution Layer] Full Levels [A→C] L1+
 * =============================================================================
 *
 * Responsibility: Handle communication between desktop app and backend API server
 * Dimensions: Involves all dimensions, transmits state matrix data
 * Security: Uses Key C (Desktop Sync) for secure communication with backend Key A
 * Maturity: L1+ level for basic dialogue functionality
 *
 * API endpoints:
 * - GET /health - 健康检查
 * - POST /api/v1/chat/unified - 统一对话接口
 * - GET /api/v1/ops/status - 系统状态
 * - WebSocket /ws - 实时双向通信
 *
 * @class AngelaAPIClient
 */

class AngelaAPIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL
    this.connected = false
    this.unifiedChatPath = '/api/v1/chat/unified' // 新接口（迁移目标）
    // The stable user key: the instance name is stored per user, so every
    // call that depends on "who am I talking to" must use the same id.
    this.userId = 'desktop_user'

    // 超時配置（毫秒）
    this.timeouts = {
      connection: 5000, // 連接超時
      chat: 30000, // 對話超時
      status: 5000, // 狀態查詢超時
      action: 5000, // 動作超時
    }
  }

  /**
   * Test connection to backend
   */
  async testConnection() {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
      this.connected = response.ok
      return this.connected
    } catch (error) {
      console.error('Backend connection failed:', error)
      this.connected = false
      return false
    }
  }

  /**
   * 驗證所有 API 端點的可用性
   * @returns {Promise<Object>} 驗證結果
   */
  async validateEndpoints() {
    const endpoints = [
      { path: '/health', method: 'GET', required: true },
      { path: '/api/v1/ops/status', method: 'GET', required: true },
      { path: this.unifiedChatPath, method: 'POST', required: true },
    ]

    const results = {
      total: endpoints.length,
      success: 0,
      failed: 0,
      requiredSuccess: 0,
      requiredFailed: 0,
      details: [],
    }

    for (const endpoint of endpoints) {
      const startTime = Date.now()
      let status = 'error'
      let statusCode = null
      let errorMessage = null

      try {
        const options = {
          method: endpoint.method,
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(5000), // 5秒超時
        }

        if (endpoint.method === 'POST') {
          options.body = JSON.stringify({
            message: 'health_check',
            action: 'ping',
          })
        }

        const response = await fetch(`${this.baseURL}${endpoint.path}`, options)
        const duration = Date.now() - startTime
        statusCode = response.status

        if (response.ok) {
          status = 'success'
          results.success++
          if (endpoint.required) {
            results.requiredSuccess++
          }
        } else {
          status = 'error'
          results.failed++
          if (endpoint.required) {
            results.requiredFailed++
          }
          errorMessage = `HTTP ${statusCode}: ${response.statusText}`
        }

        results.details.push({
          path: endpoint.path,
          method: endpoint.method,
          required: endpoint.required,
          status: status,
          statusCode: statusCode,
          duration: duration,
          errorMessage: errorMessage,
        })

        console.log(`[APIClient] ${endpoint.method} ${endpoint.path} - ${status} (${duration}ms)`)
      } catch (error) {
        const duration = Date.now() - startTime
        status = 'error'
        results.failed++
        if (endpoint.required) {
          results.requiredFailed++
        }
        errorMessage = error.message

        results.details.push({
          path: endpoint.path,
          method: endpoint.method,
          required: endpoint.required,
          status: status,
          statusCode: null,
          duration: duration,
          errorMessage: errorMessage,
        })

        console.error(
          `[APIClient] ${endpoint.method} ${endpoint.path} - error (${duration}ms):`,
          error.message
        )
      }
    }

    // 判斷整體狀態
    results.allRequiredPassed = results.requiredFailed === 0
    results.overallStatus = results.allRequiredPassed ? 'healthy' : 'degraded'

    console.log(
      `[APIClient] API 端點驗證完成: ${results.success}/${results.total} 通過, ${results.requiredFailed} 個必需端點失敗`
    )

    return results
  }

  /**
   * Fetch the identity of this user's Angela (its name and persona state).
   *
   * The name is per user: a user may have named their own Angela, so the UI
   * must not hardcode it. A failure is not fatal — the caller falls back to
   * the default name.
   * @returns {Promise<Object|null>} {ai_name, persona_state, host, ...} or null
   */
  async getIdentity() {
    try {
      const response = await fetch(
        `${this.baseURL}/api/v1/identity?user_id=${encodeURIComponent(this.userId)}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(this.timeouts.status),
        }
      )
      if (!response.ok) return null
      return await response.json()
    } catch (error) {
      console.warn('Identity lookup failed:', error)
      return null
    }
  }

  /**
   * Name this user's Angela (the workshop handover).
   * @param {string} name - the chosen name
   * @returns {Promise<Object|null>} {ok, ai_name, persona_state, message} or null
   */
  async setIdentityName(name) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/identity/name`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, user_id: this.userId }),
        signal: AbortSignal.timeout(this.timeouts.status),
      })
      if (!response.ok) return null
      return await response.json()
    } catch (error) {
      console.warn('Naming the AI failed:', error)
      return null
    }
  }

  /**
   * Send message to Angela
   * @param {string} message - User message
   * @returns {Promise<Object>} Angela's response
   */
  async sendMessage(message) {
    // 參數驗證
    const validation = this._validateMessage(message)
    if (!validation.valid) {
      return {
        success: false,
        response: `Error: ${validation.error}`,
        emotion: 'confused',
        timestamp: new Date().toISOString(),
      }
    }

    console.log(`[APIClient] Fetching: ${this.baseURL}${this.unifiedChatPath}`, { message })
    try {
      const response = await fetch(`${this.baseURL}${this.unifiedChatPath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_id: this.userId,
          session_id: this.getSessionId(),
          tenant_id: 'default',
          persona_id: 'angela',
          client_id: 'desktop_electron',
        }),
        signal: AbortSignal.timeout(this.timeouts.chat),
      })

      // No backward compatibility fallback — legacy /dialogue removed in v7.5.0

      console.log(`[APIClient] Response Status: ${response.status} ${response.statusText}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      console.log(`[APIClient] Received Data:`, data)

      return {
        success: true,
        response: data.response || data.message || 'No response',
        emotion: data.emotion || 'neutral',
        source: data.source || 'unknown',
        neuro_blend: data.neuro_blend || null,
        timestamp: new Date().toISOString(),
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      return {
        success: false,
        response: `Error: ${error.message}`,
        emotion: 'confused',
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * Stream message to Angela via SSE (POST /api/v1/chat/stream).
   * Falls back to sendMessage when streaming is unavailable.
   * @param {string} message - User message
   * @param {function} onToken - called per token chunk (string)
   * @returns {Promise<Object>} final {success, response, backend}
   */
  async sendMessageStream(message, onToken) {
    const validation = this._validateMessage(message)
    if (!validation.valid) {
      return { success: false, response: `Error: ${validation.error}` }
    }
    const streamPath = (this.unifiedChatPath || '/api/v1/chat/unified').replace(
      /\/chat\/unified$/,
      '/chat/stream'
    )
    try {
      const response = await fetch(`${this.baseURL}${streamPath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_id: this.userId,
          session_id: this.getSessionId(),
          tenant_id: 'default',
          persona_id: 'angela',
          client_id: 'desktop_electron',
        }),
        signal: AbortSignal.timeout(this.timeouts.chat * 10 || 300000),
      })
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let fullText = ''
      let backend = 'unknown'
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop()
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const payload = line.slice(5).trim()
          if (!payload || payload === '[DONE]') continue
          let event
          try {
            event = JSON.parse(payload)
          } catch (e) {
            continue
          }
          if (event.token && typeof onToken === 'function') {
            try {
              onToken(event.token)
            } catch (e) {
              /* consumer error must not break the stream */
            }
            fullText += event.token
          }
          if (event.done) {
            if (event.response_text) fullText = event.response_text
            if (event.backend) backend = event.backend
          }
          if (event.error) {
            throw new Error(event.error)
          }
        }
      }
      return { success: true, response: fullText, backend: backend }
    } catch (error) {
      console.error('Stream failed, falling back to sendMessage:', error)
      return this.sendMessage(message)
    }
  }

  /**
   * 驗證消息參數
   * @param {string} message - 用戶消息
   * @returns {object} - 驗證結果
   */
  _validateMessage(message) {
    const result = {
      valid: true,
      error: null,
    }

    // 檢查是否為字符串
    if (typeof message !== 'string') {
      result.valid = false
      result.error = 'Message must be a string'
      return result
    }

    // 檢查是否為空
    if (!message || message.trim().length === 0) {
      result.valid = false
      result.error = 'Message cannot be empty'
      return result
    }

    // 檢查長度限制
    if (message.length > 10000) {
      result.valid = false
      result.error = 'Message too long (max 10000 characters)'
      return result
    }

    // 檢查是否包含潛在的惡意內容
    const dangerousPatterns = [/<script[^>]*>/i, /javascript:/i, /on\w+\s*=/i]

    for (const pattern of dangerousPatterns) {
      if (pattern.test(message)) {
        result.valid = false
        result.error = 'Message contains potentially malicious content'
        return result
      }
    }

    return result
  }

  /**
   * Get Angela's current status
   * @returns {Promise<Object>} Status data
   */
  async getStatus() {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/ops/status`, {
        signal: AbortSignal.timeout(10000),
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = await response.json()
      return {
        success: true,
        status: data.status || 'idle',
        metrics: data.metrics || {},
        service: data.service || null,
        timestamp: data.timestamp || new Date().toISOString(),
      }
    } catch (error) {
      console.error('Failed to get status:', error)
      return {
        success: false,
        status: 'offline',
        metrics: {},
        service: null,
        timestamp: new Date().toISOString(),
      }
    }
  }

  /**
   * Get or create session ID
   * @private
   */
  getSessionId() {
    let sessionId = localStorage.getItem('angela_session_id')
    if (!sessionId) {
      const arr = new Uint32Array(1)
      crypto.getRandomValues(arr)
      sessionId = `session_${Date.now()}_${arr[0].toString(36)}`
      localStorage.setItem('angela_session_id', sessionId)
    }
    return sessionId
  }

  /**
   * 檢查 LLM 服務的可用性
   * @returns {Promise<Object>} LLM 服務狀態
   */
  async checkLLMAvailability() {
    const llmEndpoints = [{ path: this.unifiedChatPath, name: 'Unified Chat', backend: 'unified' }]

    const results = {
      available: false,
      services: [],
      errors: [],
      timestamp: new Date().toISOString(),
    }

    for (const endpoint of llmEndpoints) {
      const startTime = Date.now()
      let status = 'unknown'
      let errorMessage = null
      let responseTime = null

      try {
        const response = await fetch(`${this.baseURL}${endpoint.path}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'ping',
            test: true,
          }),
          signal: AbortSignal.timeout(10000), // 10秒超時
        })

        responseTime = Date.now() - startTime

        if (response.ok) {
          const data = await response.json()
          status = 'available'

          // 檢查是否有有效的 LLM 響應
          if (data.response || data.content || data.message) {
            status = 'healthy'
            results.available = true
          }
        } else {
          status = 'unavailable'
          errorMessage = `HTTP ${response.status}`
        }
      } catch (error) {
        responseTime = Date.now() - startTime
        status = 'error'
        errorMessage = error.message
        results.errors.push({
          endpoint: endpoint.name,
          error: error.message,
        })
      }

      results.services.push({
        name: endpoint.name,
        path: endpoint.path,
        backend: endpoint.backend,
        status: status,
        responseTime: responseTime,
        errorMessage: errorMessage,
      })

      console.log(`[APIClient] LLM ${endpoint.name} - ${status} (${responseTime}ms)`)
    }

    // 總結狀態
    results.healthyServices = results.services.filter((s) => s.status === 'healthy').length
    results.summary = results.available
      ? 'LLM services are available'
      : 'LLM services are not available'

    return results
  }

  /**
   * 快速檢查後端和 LLM 服務的健康狀態
   * @returns {Promise<Object>} 健康狀態摘要
   */
  async healthCheck() {
    console.log('[APIClient] Performing health check...')

    const results = {
      timestamp: new Date().toISOString(),
      backend: null,
      llm: null,
      overall: 'unknown',
    }

    // 檢查後端連接
    results.backend = await this.testConnection()

    if (results.backend) {
      // 檢查 LLM 服務
      results.llm = await this.checkLLMAvailability()
    } else {
      results.llm = {
        available: false,
        summary: 'Backend is not available, cannot check LLM',
      }
    }

    // 確定整體狀態
    if (results.backend && results.llm.available) {
      results.overall = 'healthy'
    } else if (results.backend) {
      results.overall = 'degraded'
    } else {
      results.overall = 'unhealthy'
    }

    console.log(`[APIClient] Health check completed: ${results.overall}`)

    return results
  }
}

// Export for use in renderer
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AngelaAPIClient
}

// A classic <script> has no `module`, so module.exports never runs and the
// symbol would stay invisible to every `window.AngelaAPIClient` reader. Assign both
// (same pattern as settings-manager.js) so the desktop preload-less renderer
// and the web viewer see the same globals.

if (typeof window !== 'undefined') {
  window.AngelaAPIClient = AngelaAPIClient
}
