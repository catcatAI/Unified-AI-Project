/**
 * =============================================================================
 * ANGELA-MATRIX: L6[执行层] 全层级 [A→C] L1+
# =============================================================================
 *
 * 职责: 处理桌面应用与后端 API 服务器的通信
 * 维度: 涉及所有维度，传输状态矩阵数据
 * 安全: 使用 Key C (桌面同步) 与后端 Key A 安全通信
 * 成熟度: L1+ 等级即可使用基本对话功能
 *
 * API 端点:
 * - GET /health - 健康检查
 * - POST /dialogue - 对话接口
 * - POST /angela/chat - Angela 聊天接口
 * - WebSocket /ws - 实时双向通信
 *
 * @class AngelaAPIClient
 */

class AngelaAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.connected = false;
    }

    /**
     * Test connection to backend
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            this.connected = response.ok;
            return this.connected;
        } catch (error) {
            console.error('Backend connection failed:', error);
            this.connected = false;
            return false;
        }
    }

    /**
     * 驗證所有 API 端點的可用性
     * @returns {Promise<Object>} 驗證結果
     */
    async validateEndpoints() {
        const endpoints = [
            { path: '/health', method: 'GET', required: true },
            { path: '/status', method: 'GET', required: true },
            { path: '/dialogue', method: 'POST', required: true },
            { path: '/angela/chat', method: 'POST', required: true },
            { path: '/economy/balance', method: 'GET', required: false },
            { path: '/pet/action', method: 'POST', required: false }
        ];

        const results = {
            total: endpoints.length,
            success: 0,
            failed: 0,
            requiredSuccess: 0,
            requiredFailed: 0,
            details: []
        };

        for (const endpoint of endpoints) {
            const startTime = Date.now();
            let status = 'error';
            let statusCode = null;
            let errorMessage = null;

            try {
                const options = {
                    method: endpoint.method,
                    headers: { 'Content-Type': 'application/json' },
                    signal: AbortSignal.timeout(5000) // 5秒超時
                };

                if (endpoint.method === 'POST') {
                    options.body = JSON.stringify({
                        message: 'health_check',
                        action: 'ping'
                    });
                }

                const response = await fetch(`${this.baseURL}${endpoint.path}`, options);
                const duration = Date.now() - startTime;
                statusCode = response.status;

                if (response.ok) {
                    status = 'success';
                    results.success++;
                    if (endpoint.required) {
                        results.requiredSuccess++;
                    }
                } else {
                    status = 'error';
                    results.failed++;
                    if (endpoint.required) {
                        results.requiredFailed++;
                    }
                    errorMessage = `HTTP ${statusCode}: ${response.statusText}`;
                }

                results.details.push({
                    path: endpoint.path,
                    method: endpoint.method,
                    required: endpoint.required,
                    status: status,
                    statusCode: statusCode,
                    duration: duration,
                    errorMessage: errorMessage
                });

                console.log(`[APIClient] ${endpoint.method} ${endpoint.path} - ${status} (${duration}ms)`);
            } catch (error) {
                const duration = Date.now() - startTime;
                status = 'error';
                results.failed++;
                if (endpoint.required) {
                    results.requiredFailed++;
                }
                errorMessage = error.message;

                results.details.push({
                    path: endpoint.path,
                    method: endpoint.method,
                    required: endpoint.required,
                    status: status,
                    statusCode: null,
                    duration: duration,
                    errorMessage: errorMessage
                });

                console.error(`[APIClient] ${endpoint.method} ${endpoint.path} - error (${duration}ms):`, error.message);
            }
        }

        // 判斷整體狀態
        results.allRequiredPassed = results.requiredFailed === 0;
        results.overallStatus = results.allRequiredPassed ? 'healthy' : 'degraded';

        console.log(`[APIClient] API 端點驗證完成: ${results.success}/${results.total} 通過, ${results.requiredFailed} 個必需端點失敗`);

        return results;
    }

    /**
     * Send message to Angela
     * @param {string} message - User message
     * @returns {Promise<Object>} Angela's response
     */
    async sendMessage(message) {
        try {
            const response = await fetch(`${this.baseURL}/dialogue`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    user_id: 'desktop_user',
                    session_id: this.getSessionId()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return {
                success: true,
                response: data.response || data.message || 'No response',
                emotion: data.emotion || 'neutral',
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to send message:', error);
            return {
                success: false,
                response: `Error: ${error.message}`,
                emotion: 'confused',
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Get Angela's current status
     * @returns {Promise<Object>} Status data
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.baseURL}/status`);
            const data = await response.json();
            return {
                success: true,
                health: data.health || 100,
                energy: data.energy || 100,
                mood: data.mood || 'happy',
                status: data.status || 'idle'
            };
        } catch (error) {
            console.error('Failed to get status:', error);
            return {
                success: false,
                health: 0,
                energy: 0,
                mood: 'unknown',
                status: 'offline'
            };
        }
    }

    /**
     * Get economy/resource status
     * @returns {Promise<Object>} Economy data
     */
    async getEconomy() {
        try {
            const response = await fetch(`${this.baseURL}/economy/balance`);
            const data = await response.json();
            return {
                success: true,
                coins: data.coins || 0,
                food: data.food || 0,
                energy: data.energy || 0
            };
        } catch (error) {
            console.error('Failed to get economy:', error);
            return {
                success: false,
                coins: 0,
                food: 0,
                energy: 0
            };
        }
    }

    /**
     * Trigger pet action
     * @param {string} action - Action name (e.g., 'feed', 'play', 'rest')
     * @returns {Promise<Object>} Action result
     */
    async triggerAction(action) {
        try {
            const response = await fetch(`${this.baseURL}/pet/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await response.json();
            return {
                success: true,
                result: data.result || 'Action completed',
                newStatus: data.status || {}
            };
        } catch (error) {
            console.error('Failed to trigger action:', error);
            return {
                success: false,
                result: `Error: ${error.message}`
            };
        }
    }

    /**
     * Get or create session ID
     * @private
     */
    getSessionId() {
        let sessionId = localStorage.getItem('angela_session_id');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('angela_session_id', sessionId);
        }
        return sessionId;
    }

    /**
     * 檢查 LLM 服務的可用性
     * @returns {Promise<Object>} LLM 服務狀態
     */
    async checkLLMAvailability() {
        const llmEndpoints = [
            { path: '/angela/chat', name: 'Angela Chat', backend: 'angela' },
            { path: '/dialogue', name: 'Dialogue', backend: 'general' }
        ];

        const results = {
            available: false,
            services: [],
            errors: [],
            timestamp: new Date().toISOString()
        };

        for (const endpoint of llmEndpoints) {
            const startTime = Date.now();
            let status = 'unknown';
            let errorMessage = null;
            let responseTime = null;

            try {
                const response = await fetch(`${this.baseURL}${endpoint.path}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: 'ping',
                        test: true
                    }),
                    signal: AbortSignal.timeout(10000) // 10秒超時
                });

                responseTime = Date.now() - startTime;

                if (response.ok) {
                    const data = await response.json();
                    status = 'available';

                    // 檢查是否有有效的 LLM 響應
                    if (data.response || data.content || data.message) {
                        status = 'healthy';
                        results.available = true;
                    }
                } else {
                    status = 'unavailable';
                    errorMessage = `HTTP ${response.status}`;
                }
            } catch (error) {
                responseTime = Date.now() - startTime;
                status = 'error';
                errorMessage = error.message;
                results.errors.push({
                    endpoint: endpoint.name,
                    error: error.message
                });
            }

            results.services.push({
                name: endpoint.name,
                path: endpoint.path,
                backend: endpoint.backend,
                status: status,
                responseTime: responseTime,
                errorMessage: errorMessage
            });

            console.log(`[APIClient] LLM ${endpoint.name} - ${status} (${responseTime}ms)`);
        }

        // 總結狀態
        results.healthyServices = results.services.filter(s => s.status === 'healthy').length;
        results.summary = results.available ? 'LLM services are available' : 'LLM services are not available';

        return results;
    }

    /**
     * 快速檢查後端和 LLM 服務的健康狀態
     * @returns {Promise<Object>} 健康狀態摘要
     */
    async healthCheck() {
        console.log('[APIClient] Performing health check...');

        const results = {
            timestamp: new Date().toISOString(),
            backend: null,
            llm: null,
            overall: 'unknown'
        };

        // 檢查後端連接
        results.backend = await this.testConnection();

        if (results.backend) {
            // 檢查 LLM 服務
            results.llm = await this.checkLLMAvailability();
        } else {
            results.llm = {
                available: false,
                summary: 'Backend is not available, cannot check LLM'
            };
        }

        // 確定整體狀態
        if (results.backend && results.llm.available) {
            results.overall = 'healthy';
        } else if (results.backend) {
            results.overall = 'degraded';
        } else {
            results.overall = 'unhealthy';
        }

        console.log(`[APIClient] Health check completed: ${results.overall}`);

        return results;
    }
}

// Export for use in renderer
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AngelaAPIClient;
}
