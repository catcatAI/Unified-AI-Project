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
        
        // 离线消息队列
        this._offlineQueue = [];
        this._maxQueueSize = 100; // 最大队列大小
        this._queuePersisted = false; // 是否已持久化到localStorage
        
        // 恢复持久化的离线消息
        this._loadOfflineQueue();
        
        // 待处理响应清理定时器
        this._pendingResponsesCleanupInterval = 60000; // 每分钟清理一次
        this._pendingResponsesCleanupTimer = null;

        // P0-1: 4D 状态矩阵同步优化
        this.messageSequence = 0; // 消息序列号
        this.expectedSequence = 0; // 期望的序列号
        this.pendingUpdates = new Map(); // 待处理的消息缓存
        this.updateBatchSize = 5; // 批处理大小
        this.updateBatchInterval = 100; // 批处理间隔 (ms)
        this.updateBatchTimer = null; // 批处理定时器
        this.pendingStateUpdates = []; // 待批处理的状态更新
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
                
                // 启动待处理响应清理
                this._startPendingResponsesCleanup();
                
                // 通知連接成功
                this._fireEvent('connected', { url, timestamp: Date.now() });
                
                // 发送离线队列中的消息
                this._flushOfflineQueue();
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
            // P0-2: 处理生物事件
            case 'biological_event':
                this._handleBiologicalEvent(data);
                break;
            default:
                // Log as debug instead of warning to reduce noise
                console.debug('Unknown message type:', type, message);
        }
    }

    /**
     * P0-2: 处理生物事件
     */
    _handleBiologicalEvent(data) {
        console.log('Biological event received:', data);

        // 触发事件
        this._fireEvent('biologicalEvent', data);
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

        // P0-1: 消息顺序保证
        if (data.sequence !== undefined) {
            if (data.sequence < this.expectedSequence) {
                console.warn(`[BackendWebSocket] 收到过期消息: ${data.sequence} < ${this.expectedSequence}`);
                return;
            }

            // 如果收到乱序消息，缓存起来
            if (data.sequence > this.expectedSequence) {
                console.log(`[BackendWebSocket] 收到乱序消息: ${data.sequence}, 期望: ${this.expectedSequence}`);
                this.pendingUpdates.set(data.sequence, data);
                return;
            }

            // 消息顺序正确，处理并更新期望序列号
            this.expectedSequence = data.sequence + 1;

            // 处理缓存的消息
            while (this.pendingUpdates.has(this.expectedSequence)) {
                const pendingData = this.pendingUpdates.get(this.expectedSequence);
                this.pendingUpdates.delete(this.expectedSequence);
                this._processStateUpdate(pendingData);
                this.expectedSequence++;
            }
        }

        // 处理当前消息
        this._processStateUpdate(data);
    }

    /**
     * P0-1: 处理状态更新（内部方法）
     */
    _processStateUpdate(data) {
        // P0-1: 状态合并机制
        const mergedData = this._mergeStateData(data);

        // 更新 StateMatrix4D
        if (window.angelaApp && window.angelaApp.stateMatrix) {
            window.angelaApp.stateMatrix.updateFromBackend(mergedData);
        }

        // 觸發事件
        this._fireEvent('stateUpdated', mergedData);
    }

    /**
     * P0-1: 状态数据合并（避免覆盖）
     */
    _mergeStateData(updateData) {
        if (!window.angelaApp || !window.angelaApp.stateMatrix) {
            return updateData;
        }

        const currentState = window.angelaApp.stateMatrix.getState();
        const merged = {
            alpha: { ...currentState.alpha, ...(updateData.alpha || {}) },
            beta: { ...currentState.beta, ...(updateData.beta || {}) },
            gamma: { ...currentState.gamma, ...(updateData.gamma || {}) },
            delta: { ...currentState.delta, ...(updateData.delta || {}) }
        };

        return merged;
    }

    /**
     * P0-1: 批处理状态更新
     */
    _addToUpdateBatch(data) {
        this.pendingStateUpdates.push(data);

        // 如果达到批处理大小或没有定时器，立即发送
        if (this.pendingStateUpdates.length >= this.updateBatchSize || !this.updateBatchTimer) {
            this._flushUpdateBatch();
            return;
        }

        // 设置批处理定时器
        if (!this.updateBatchTimer) {
            this.updateBatchTimer = setTimeout(() => {
                this._flushUpdateBatch();
            }, this.updateBatchInterval);
        }
    }

    /**
     * P0-1: 刷新批处理队列
     */
    _flushUpdateBatch() {
        if (this.pendingStateUpdates.length === 0) {
            return;
        }

        // 合并所有更新
        const mergedUpdate = this.pendingStateUpdates.reduce((acc, update) => {
            return this._mergeStateData({ ...acc, ...update });
        }, {});

        // 发送合并后的更新
        this._processStateUpdate(mergedUpdate);

        // 清空批处理队列
        this.pendingStateUpdates = [];
        this.updateBatchTimer = null;
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
    
    _startPendingResponsesCleanup() {
        this._pendingResponsesCleanupTimer = setInterval(() => {
            this._cleanupExpiredPendingResponses();
        }, this._pendingResponsesCleanupInterval);
    }
    
    _stopPendingResponsesCleanup() {
        if (this._pendingResponsesCleanupTimer) {
            clearInterval(this._pendingResponsesCleanupTimer);
            this._pendingResponsesCleanupTimer = null;
        }
    }
    
    _cleanupExpiredPendingResponses() {
        if (!this._pendingResponses || this._pendingResponses.size === 0) {
            return;
        }
        
        const now = Date.now();
        let cleanedCount = 0;
        
        for (const [messageId, pending] of this._pendingResponses.entries()) {
            // 检查超时（30秒后清理）
            const elapsed = now - pending.timestamp;
            if (elapsed >= 35000) { // 给5秒缓冲时间
                clearTimeout(pending.timeout);
                pending.resolve({ success: false, response: 'Response expired and cleaned up' });
                this._pendingResponses.delete(messageId);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            console.log('[BackendWebSocket] 清理了', cleanedCount, '个过期响应');
        }
    }
    
    _handleReconnect() {
        console.log('Attempting to reconnect... (attempt', this.reconnectAttempts + 1, 'of', this.maxReconnectAttempts + 1, ')');

        this._stopHeartbeat();

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;

            // 改进的指數退避策略
            const maxDelay = 30000; // 最大30秒
            const baseDelay = 1000; // 起始1秒
            const exponentialDelay = Math.min(baseDelay * Math.pow(2, this.reconnectAttempts - 1), maxDelay);
            const jitter = Math.random() * 1000; // 添加隨機抖動，防止雷群效應

            const reconnectDelay = exponentialDelay + jitter;
            console.log(`Reconnecting in ${reconnectDelay.toFixed(0)}ms (${(reconnectDelay / 1000).toFixed(1)}s)...`);

            // 清理舊的 WebSocket 連接
            if (this.ws) {
                try {
                    this.ws.onopen = null;
                    this.ws.onmessage = null;
                    this.ws.onerror = null;
                    this.ws.onclose = null;
                    if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                        this.ws.close();
                    }
                    this.ws = null;
                } catch (error) {
                    console.warn('[BackendWebSocket] Error cleaning up old WebSocket:', error);
                }
            }

            this.reconnectInterval = setTimeout(() => {
                this.connect(this.url || 'ws://localhost:8000/ws');
            }, reconnectDelay);
        } else {
            console.error('[BackendWebSocket] Max reconnect attempts reached, entering long-poll mode');
            // 達到最大重試次數後，進入長輪詢模式，每30秒重試一次
            this.reconnectInterval = setTimeout(() => {
                this.reconnectAttempts = 0; // 重置計數器，以便重新使用指數退避
                this._handleReconnect();
            }, 30000);
        }
    }
    
    send(message) {
        if (!this.connected || !this.ws) {
            // 离线时添加到队列
            this._addToOfflineQueue(message);
            console.warn('Not connected, message queued:', message);
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Failed to send message, adding to queue:', error);
            // 发送失败，添加到离线队列
            this._addToOfflineQueue(message);
            return false;
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
            this._pendingResponses.set(messageId, { timeout, resolve, timestamp: Date.now() });

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

    /**
     * 添加消息到离线队列
     * @param {Object} message - 消息对象
     */
    _addToOfflineQueue(message) {
        // 消息去重：檢查是否已存在相同的消息
        const messageKey = this._getMessageKey(message);
        const existingIndex = this._offlineQueue.findIndex(msg => this._getMessageKey(msg) === messageKey);

        if (existingIndex !== -1) {
            // 消息已存在，更新時間戳和重試次數
            console.log('[BackendWebSocket] 消息已在队列中，更新时间戳:', messageKey);
            this._offlineQueue[existingIndex]._queuedAt = Date.now();
            this._offlineQueue[existingIndex]._retryCount = (this._offlineQueue[existingIndex]._retryCount || 0) + 1;
            this._persistOfflineQueue();
            return;
        }

        const queuedMessage = {
            ...message,
            _queuedAt: Date.now(),
            _id: this._generateQueueId(),
            _priority: this._getMessagePriority(message),
            _retryCount: 0
        };

        // 按優先級插入隊列
        this._insertByPriority(queuedMessage);

        // 限制隊列大小
        if (this._offlineQueue.length > this._maxQueueSize) {
            // 移除優先級最低且最舊的消息
            this._offlineQueue.sort((a, b) => {
                if (a._priority !== b._priority) {
                    return b._priority - a._priority; // 高優先級在前
                }
                return a._queuedAt - b._queuedAt; // 舊消息在前
            });

            const removed = this._offlineQueue.pop();
            console.warn('[BackendWebSocket] 队列已满，移除優先級最低/最舊的消息:', removed._id);
        }

        // 持久化到localStorage
        this._persistOfflineQueue();

        console.log(`[BackendWebSocket] 消息已加入離線隊列 (${this._offlineQueue.length}/${this._maxQueueSize}), 優先級: ${queuedMessage._priority}`);
    }

    /**
     * 獲取消息的標識符（用於去重）
     * @param {Object} message 消息對象
     * @returns {string} 消息標識符
     */
    _getMessageKey(message) {
        if (!message) return '';

        const keyParts = [];
        if (message.type) keyParts.push(message.type);
        if (message.action) keyParts.push(message.action);
        if (message.data) {
            if (message.data.id) keyParts.push(`id:${message.data.id}`);
            if (message.data.message_id) keyParts.push(`msg:${message.data.message_id}`);
            if (message.data.user_id) keyParts.push(`user:${message.data.user_id}`);
        }

        return keyParts.join('|');
    }

    /**
     * 獲取消息的優先級
     * @param {Object} message 消息對象
     * @returns {number} 優先級（數字越大優先級越高）
     */
    _getMessagePriority(message) {
        if (!message || !message.type) return 0;

        // 高優先級消息
        const highPriorityTypes = ['emergency', 'alert', 'critical'];
        // 中等優先級消息
        const mediumPriorityTypes = ['state_update', 'tactile_response', 'performance_update'];
        // 低優先級消息
        const lowPriorityTypes = ['chat_message', 'log', 'info'];

        if (highPriorityTypes.includes(message.type)) return 3;
        if (mediumPriorityTypes.includes(message.type)) return 2;
        if (lowPriorityTypes.includes(message.type)) return 1;

        return 0; // 默認優先級
    }

    /**
     * 按優先級插入消息
     * @param {Object} message 消息對象
     */
    _insertByPriority(message) {
        // 找到插入位置（第一個優先級低於當前消息的位置）
        let insertIndex = this._offlineQueue.findIndex(msg => msg._priority < message._priority);

        if (insertIndex === -1) {
            // 沒有找到優先級更低的消息，插入到末尾
            this._offlineQueue.push(message);
        } else {
            // 插入到找到的位置
            this._offlineQueue.splice(insertIndex, 0, message);
        }
    }
    
    /**
     * 發送離線隊列中的所有消息
     */
    async _flushOfflineQueue() {
        if (this._offlineQueue.length === 0) {
            console.log('[BackendWebSocket] 離線隊列為空，無需發送');
            return;
        }

        console.log(`[BackendWebSocket] 開始發送 ${this._offlineQueue.length} 條離線消息`);

        // 保持優先級順序：高優先級先發送
        const queue = [...this._offlineQueue].sort((a, b) => {
            if (a._priority !== b._priority) {
                return b._priority - a._priority; // 高優先級在前
            }
            return a._queuedAt - b._queuedAt; // 舊消息在前
        });

        this._offlineQueue = [];
        this._persistOfflineQueue();

        let successCount = 0;
        let failCount = 0;

        // 批處理發送：每批最多10條消息
        const batchSize = 10;
        for (let i = 0; i < queue.length; i += batchSize) {
            const batch = queue.slice(i, i + batchSize);

            for (const message of batch) {
                try {
                    await new Promise((resolve, reject) => {
                        const timeout = setTimeout(() => {
                            reject(new Error('Timeout'));
                        }, 5000); // 每條消息5秒超時

                        try {
                            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                                this.ws.send(JSON.stringify(message));
                                clearTimeout(timeout);
                                resolve();
                            } else {
                                clearTimeout(timeout);
                                reject(new Error('WebSocket not ready'));
                            }
                        } catch (error) {
                            clearTimeout(timeout);
                            reject(error);
                        }
                    });

                    successCount++;

                    // 添加延遲，避免發送過快
                    if (queue.indexOf(message) < queue.length - 1) {
                        await new Promise(resolve => setTimeout(resolve, 50));
                    }
                } catch (error) {
                    console.error('[BackendWebSocket] 發送離線消息失敗:', error, message);
                    failCount++;

                    // 重新加入隊列（最多重試3次）
                    if ((message._retryCount || 0) < 3) {
                        message._retryCount = (message._retryCount || 0) + 1;
                        message._queuedAt = Date.now(); // 更新時間戳
                        this._insertByPriority(message);
                    } else {
                        console.warn('[BackendWebSocket] 消息已達最大重試次數，丟棄:', message._id);
                    }
                }
            }

            // 批次之間添加延遲
            if (i + batchSize < queue.length) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        // 持久化剩餘消息
        if (this._offlineQueue.length > 0) {
            this._persistOfflineQueue();
        }

        console.log(`[BackendWebSocket] 離線消息發送完成: ${successCount} 成功, ${failCount} 失敗, ${this._offlineQueue.length} 剩餘`);

        this._fireEvent('offlineQueueFlushed', {
            successCount,
            failCount,
            remaining: this._offlineQueue.length
        });
    }
    
    /**
     * 从localStorage加载离线队列
     */
    _loadOfflineQueue() {
        try {
            const data = localStorage.getItem('angela_offline_queue');
            if (data) {
                this._offlineQueue = JSON.parse(data);
                console.log(`[BackendWebSocket] 从localStorage恢复 ${this._offlineQueue.length} 条离线消息`);
                
                // 检查消息是否过期（7天）
                const expireTime = 7 * 24 * 60 * 60 * 1000;
                const now = Date.now();
                this._offlineQueue = this._offlineQueue.filter(msg => {
                    return !msg._queuedAt || (now - msg._queuedAt) < expireTime;
                });
                
                if (this._offlineQueue.length > 0) {
                    this._persistOfflineQueue();
                }
            }
        } catch (error) {
            console.error('[BackendWebSocket] 加载离线队列失败:', error);
            this._offlineQueue = [];
        }
    }
    
    /**
     * 持久化离线队列到localStorage
     */
    _persistOfflineQueue() {
        try {
            if (this._offlineQueue.length > 0) {
                localStorage.setItem('angela_offline_queue', JSON.stringify(this._offlineQueue));
            } else {
                localStorage.removeItem('angela_offline_queue');
            }
            this._queuePersisted = true;
        } catch (error) {
            console.error('[BackendWebSocket] 持久化离线队列失败:', error);
        }
    }
    
    /**
     * 清空离线队列
     */
    clearOfflineQueue() {
        this._offlineQueue = [];
        try {
            localStorage.removeItem('angela_offline_queue');
        } catch (error) {
            console.error('[BackendWebSocket] 清空离线队列失败:', error);
        }
        console.log('[BackendWebSocket] 离线队列已清空');
    }
    
    /**
     * 获取离线队列状态
     */
    getOfflineQueueStatus() {
        return {
            size: this._offlineQueue.length,
            maxSize: this._maxQueueSize,
            oldestMessage: this._offlineQueue[0]?._queuedAt || null,
            newestMessage: this._offlineQueue[this._offlineQueue.length - 1]?._queuedAt || null
        };
    }
    
    /**
     * 生成队列ID
     */
    _generateQueueId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    disconnect() {
        console.log('[BackendWebSocket] Disconnecting...');

        // Stop reconnection attempts
        if (this.reconnectInterval) {
            clearTimeout(this.reconnectInterval);
            this.reconnectInterval = null;
        }

        // Close WebSocket connection
        if (this.ws) {
            // Clear event handlers before closing
            this.ws.onopen = null;
            this.ws.onmessage = null;
            this.ws.onerror = null;
            this.ws.onclose = null;

            // Close connection
            if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                this.ws.close();
            }

            this.ws = null;
        }

        this.connected = false;

        // Stop heartbeat
        this._stopHeartbeat();

        // Stop pending responses cleanup
        this._stopPendingResponsesCleanup();

        // Clear all pending responses
        if (this._pendingResponses && this._pendingResponses.size > 0) {
            console.log(`[BackendWebSocket] Clearing ${this._pendingResponses.size} pending responses`);
            for (const [messageId, pending] of this._pendingResponses.entries()) {
                clearTimeout(pending.timeout);
                pending.reject(new Error('Connection closed'));
            }
            this._pendingResponses.clear();
            this._pendingResponses = null;
        }

        // Persist offline queue before disconnecting
        this._persistOfflineQueue();

        console.log('[BackendWebSocket] Disconnected successfully');
    }

    /**
     * 完全銷毀 WebSocket 客戶端，清理所有資源
     * 用於應用程序退出或不再需要 WebSocket 連接時
     */
    destroy() {
        console.log('[BackendWebSocket] Destroying...');

        // Disconnect first
        this.disconnect();

        // Clear offline queue
        this.clearOfflineQueue();

        // Clear all event handlers
        this.eventHandlers = {};

        // Clear references
        this.url = null;
        this.reconnectAttempts = 0;
        this._maxQueueSize = 0;
        this._pendingResponsesCleanupInterval = 0;

        console.log('[BackendWebSocket] Destroyed successfully');
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
