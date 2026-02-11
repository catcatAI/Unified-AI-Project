/**
 * =============================================================================
 * ANGELA-MATRIX: L6[执行层] 全层级 [A→C] L2+
# =============================================================================
 *
 * 职责: 处理与后端 WebSocket 的通信和状态矩阵同步
 * 维度: 涉及所有维度 (αβγδ)，实时同步状态矩阵数据
 * 安全: 使用 Key C (桌面同步) 与后端 Key A 安全通信
 * 成熟度: L2+ 等级理解实时通信的概念
 *
 * 功能:
 * - WebSocket 连接管理
 * - 自动重连机制
 * - 心跳保持
 * - 状态矩阵同步
 * - 事件处理和分发
 *
 * @class BackendWebSocketClient
 */

class BackendWebSocketClient {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.heartbeatInterval = null;
        this.eventHandlers = {};
    }
    
    async connect(url) {
        console.log('Connecting to backend:', url);
        
        if (this.connected) {
            console.log('Already connected');
            return;
        }
        
        try {
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                
                // 開始心跳
                this._startHeartbeat();
                
                // 通知連接成功
                this._fireEvent('connected', { url, timestamp: Date.now() });
            };
            
            this.ws.onmessage = (event) => this._handleMessage(event);
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this._fireEvent('error', error);
                this._handleReconnect();
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.connected = false;
                this._stopHeartbeat();
                this._handleReconnect();
            };
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this._handleReconnect();
        }
    }
    
    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this._routeMessage(message);
        } catch (error) {
            console.error('Failed to parse message:', error, event.data);
        }
    }
    
    _routeMessage(message) {
        const type = message.type;
        const data = message.data;
        
        switch (type) {
            case 'connected':
                console.log('Backend confirmed connection:', message);
                this._fireEvent('connected', message);
                break;
            case 'state_update':
                this._handleStateUpdate(data);
                break;
            case 'tactile_response':
                this._handleTactileResponse(data);
                break;
            case 'performance_update':
                this._handlePerformanceUpdate(data);
                break;
            case 'hardware_detected':
                this._handleHardwareDetected(data);
                break;
            case 'wallpaper_object_injection':
                this._handleWallpaperObjectInjection(data);
                break;
            case 'chat_response':
                this._handleChatResponse(data);
                break;
            case 'echo':
                // FIX: Handle echo message (heartbeat/ping from backend)
                // Echo is used for keep-alive, respond with pong if needed
                console.log('Received echo (keep-alive):', message);
                break;
            default:
                // Log as debug instead of warning to reduce noise
                console.debug('Unknown message type:', type, message);
        }
    }
    
    _handleModuleStatusChanged(data) {
        console.log('Module status changed from backend:', data);
        
        // 更新前端模組狀態
        if (window.angelaApp) {
            window.angelaApp.toggleModule(data.module, data.enabled, true);
        }
        
        // 觸發事件
        this._fireEvent('moduleStatusChanged', data);
    }

    _handleWallpaperObjectInjection(data) {
        console.log('Wallpaper object injection received:', data);
        
        // 注入到桌布管理器
        if (window.angelaApp && window.angelaApp.wallpaperHandler) {
            window.angelaApp.wallpaperHandler.injectObject(data);
        }
        
        // 觸發事件
        this._fireEvent('wallpaperObjectInjected', data);
    }
    
    _handleStateUpdate(data) {
        console.log('State update received:', data);
        
        // 更新 StateMatrix4D
        if (window.angelaApp && window.angelaApp.stateMatrix) {
            window.angelaApp.stateMatrix.updateFromBackend(data);
        }
        
        // 觸發事件
        this._fireEvent('stateUpdated', data);
    }
    
    _handleTactileResponse(data) {
        console.log('Tactile response received:', data);
        
        // 更新 Live2D 參數
        if (window.angelaApp && window.angelaApp.live2dManager) {
            const parameters = data.parameters || {};
            for (const [paramName, value] of Object.entries(parameters)) {
                window.angelaApp.live2dManager.setParameter(paramName, value);
            }
        }
        
        // 設置表情
        if (data.emotion && window.angelaApp.live2dManager) {
            window.angelaApp.live2dManager.setExpression(data.emotion);
        }
        
        // 觸發事件
        this._fireEvent('tactileResponse', data);
    }
    
    _handlePerformanceUpdate(data) {
        console.log('Performance update received:', data);
        
        // 更新性能設定
        if (window.angelaApp && window.angelaApp.performanceManager) {
            if (data.mode) {
                window.angelaApp.performanceManager.setPerformanceMode(data.mode);
            }
            if (data.frameRate) {
                window.angelaApp.performanceManager.setTargetFPS(data.frameRate);
            }
        }
        
        // 觸發事件
        this._fireEvent('performanceUpdated', data);
    }
    
    _handleHardwareDetected(data) {
        console.log('Hardware detected:', data);
        
        // 更新硬體檢測器
        if (window.angelaApp && window.angelaApp.hardwareDetector) {
            window.angelaApp.hardwareDetector.profile = data.profile;
            window.angelaApp.hardwareDetector.capabilities = data.capabilities;
        }
        
        // 觸發事件
        this._fireEvent('hardwareDetected', data);
    }
    
    _startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.connected && this.ws) {
                this.ws.send(JSON.stringify({
                    type: 'ping',
                    timestamp: Date.now()
                }));
            }
        }, 30000); // 每 30 秒
    }
    
    _stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    _handleReconnect() {
        console.log('Attempting to reconnect... (attempt', this.reconnectAttempts + 1, 'of', this.maxReconnectAttempts + 1, ')');
        
        this._stopHeartbeat();
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            
            // FIX: Exponential backoff with cap at 5 seconds (not 17 minutes!)
            const maxDelay = 5000; // Max 5 seconds between attempts
            const baseDelay = 500; // Start with 500ms
            const exponentialDelay = Math.min(baseDelay * Math.pow(2, this.reconnectAttempts - 1), maxDelay);
            const jitter = Math.random() * 200; // Add small jitter to prevent thundering herd
            
            const reconnectDelay = exponentialDelay + jitter;
            console.log(`Reconnecting in ${reconnectDelay.toFixed(0)}ms...`);
            
            this.reconnectInterval = setTimeout(() => {
                this.connect(this.url || 'ws://localhost:8000/ws');
            }, reconnectDelay);
        } else {
            console.error('Max reconnect attempts reached, will retry every 10 seconds');
            // Keep trying every 10 seconds even after max attempts
            this.reconnectInterval = setTimeout(() => {
                this.reconnectAttempts = 0; // Reset to try again with shorter delays
                this._handleReconnect();
            }, 10000);
        }
    }
    
    send(message) {
        if (!this.connected || !this.ws) {
            console.warn('Not connected, message not sent:', message);
            return;
        }
        
        try {
            this.ws.send(JSON.stringify(message));
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    }

    /**
     * Send chat message and wait for response
     * @param {string} text - Message text
     * @returns {Promise<{success: boolean, response: string}>}
     */
    async sendMessage(text) {
        if (!this.connected || !this.ws) {
            console.warn('Not connected, message not sent:', text);
            return { success: false, response: 'Not connected to backend' };
        }

        return new Promise((resolve) => {
            const messageId = Date.now().toString();
            const timeout = setTimeout(() => {
                this._pendingResponses.delete(messageId);
                resolve({ success: false, response: 'Timeout waiting for response' });
            }, 30000);

            this._pendingResponses = this._pendingResponses || new Map();
            this._pendingResponses.set(messageId, { timeout, resolve });

            try {
                this.ws.send(JSON.stringify({
                    type: 'chat_message',
                    data: {
                        message_id: messageId,
                        content: text,
                        timestamp: new Date().toISOString()
                    }
                }));
            } catch (error) {
                clearTimeout(timeout);
                this._pendingResponses.delete(messageId);
                resolve({ success: false, response: error.message });
            }
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
        
        this.connected = false;
        this._stopHeartbeat();
        
        if (this.reconnectInterval) {
            clearTimeout(this.reconnectInterval);
            this.reconnectInterval = null;
        }
    }
    
    // 事件註冊
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
        }
    }
    
    _fireEvent(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(event, data);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }
    
    getConnectionStatus() {
        return {
            connected: this.connected,
            url: this.url,
            reconnectAttempts: this.reconnectAttempts
        };
    }
    
    isConnected() {
        return this.connected;
    }

    _handleChatResponse(data) {
        if (!data || !data.message_id) return;

        const pending = this._pendingResponses?.get(data.message_id);
        if (pending) {
            clearTimeout(pending.timeout);
            this._pendingResponses.delete(data.message_id);
            pending.resolve({
                success: true,
                response: data.content || data.response || ''
            });
        }
    }
}

// 導出到全局
if (typeof window !== 'undefined') {
    window.BackendWebSocketClient = BackendWebSocketClient;
    
    console.log('Backend WebSocket Client loaded');
}
