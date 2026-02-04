/**
 * Angela AI - Backend WebSocket Client
 * 
 * �後端通信並同步狀態矩陣
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
            default:
                console.warn('Unknown message type:', type);
        }
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
                window.angelaApp.performanceManager.setMode(data.mode);
            }
            if (data.frameRate) {
                window.angelaApp.performanceManager._setFrameRate(data.frameRate);
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
        console.log('Attempting to reconnect...');
        
        this._stopHeartbeat();
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectInterval = setTimeout(() => {
                this.reconnectAttempts++;
                this.connect(this.url || 'ws://localhost:8000/ws');
            }, Math.pow(2, this.reconnectAttempts) * 1000);
        } else {
            console.error('Max reconnect attempts reached');
            this._fireEvent('disconnected', { reason: 'max_attempts' });
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
}

// 導出到全局
if (typeof window !== 'undefined') {
    window.BackendWebSocketClient = BackendWebSocketClient;
    
    console.log('Backend WebSocket Client loaded');
}
