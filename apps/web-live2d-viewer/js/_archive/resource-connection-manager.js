/**
 * Angela AI - 资源连接管理器
 * 
 * 管理所有外部资源连接（WebSocket、HTTP、MQTT等）
 * 提供统一的连接状态监控和重连机制
 */

class ResourceConnectionManager {
    constructor() {
        this.connections = new Map();
        this.connectionStats = {
            total: 0,
            connected: 0,
            disconnected: 0,
            connecting: 0,
            error: 0
        };
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 5;
        this.reconnectDelays = [1000, 2000, 5000, 10000, 30000]; // 重连延迟（秒）
        
        console.log('[ResourceConnectionManager] Initialized');
    }
    
    /**
     * 注册连接
     * @param {string} id - 连接ID
     * @param {Object} connection - 连接对象
     * @param {Object} options - 连接选项
     */
    register(id, connection, options = {}) {
        const connInfo = {
            id,
            connection,
            type: options.type || 'unknown',
            autoReconnect: options.autoReconnect !== false,
            priority: options.priority || 'normal',
            status: 'disconnected',
            lastConnected: null,
            lastDisconnected: null,
            errorCount: 0,
            reconnectDelay: options.reconnectDelay || 1000
        };
        
        this.connections.set(id, connInfo);
        this._updateStats();
        
        console.log(`[ResourceConnectionManager] Connection registered: ${id} (${connInfo.type})`);
        
        return connInfo;
    }
    
    /**
     * 注销连接
     * @param {string} id - 连接ID
     */
    unregister(id) {
        if (this.connections.has(id)) {
            const conn = this.connections.get(id);
            
            // 断开连接
            if (conn.connection && conn.connection.disconnect) {
                conn.connection.disconnect();
            }
            
            this.connections.delete(id);
            this.reconnectAttempts.delete(id);
            this._updateStats();
            
            console.log(`[ResourceConnectionManager] Connection unregistered: ${id}`);
        }
    }
    
    /**
     * 更新连接状态
     * @param {string} id - 连接ID
     * @param {string} status - 状态
     * @param {Object} metadata - 元数据
     */
    updateStatus(id, status, metadata = {}) {
        if (!this.connections.has(id)) {
            console.warn(`[ResourceConnectionManager] Unknown connection: ${id}`);
            return false;
        }
        
        const conn = this.connections.get(id);
        const oldStatus = conn.status;
        conn.status = status;
        
        // 更新时间戳
        if (status === 'connected') {
            conn.lastConnected = Date.now();
            conn.errorCount = 0;
            this.reconnectAttempts.delete(id);
        } else if (status === 'disconnected' || status === 'error') {
            conn.lastDisconnected = Date.now();
            conn.errorCount++;
            
            // 自动重连
            if (conn.autoReconnect && status === 'disconnected') {
                this._scheduleReconnect(id);
            }
        }
        
        // 更新元数据
        Object.assign(conn, metadata);
        
        this._updateStats();
        
        // 触发事件
        this._fireEvent('statusChanged', { id, oldStatus, newStatus: status, conn });
        
        console.log(`[ResourceConnectionManager] Status updated: ${id} ${oldStatus} -> ${status}`);
        
        return true;
    }
    
    /**
     * 获取连接状态
     * @param {string} id - 连接ID
     */
    getStatus(id) {
        const conn = this.connections.get(id);
        if (!conn) {
            return null;
        }
        
        return {
            id: conn.id,
            type: conn.type,
            status: conn.status,
            priority: conn.priority,
            lastConnected: conn.lastConnected,
            lastDisconnected: conn.lastDisconnected,
            errorCount: conn.errorCount,
            uptime: conn.lastConnected ? Date.now() - conn.lastConnected : 0
        };
    }
    
    /**
     * 获取所有连接状态
     */
    getAllStatus() {
        const status = [];
        
        for (const [id, conn] of this.connections.entries()) {
            status.push(this.getStatus(id));
        }
        
        return status;
    }
    
    /**
     * 获取连接统计
     */
    getStats() {
        return { ...this.connectionStats };
    }
    
    /**
     * 手动重连
     * @param {string} id - 连接ID
     */
    async reconnect(id) {
        if (!this.connections.has(id)) {
            console.warn(`[ResourceConnectionManager] Unknown connection: ${id}`);
            return false;
        }
        
        const conn = this.connections.get(id);
        
        // 清除待定的重连
        if (this.reconnectAttempts.has(id)) {
            clearTimeout(this.reconnectAttempts.get(id).timeout);
            this.reconnectAttempts.delete(id);
        }
        
        console.log(`[ResourceConnectionManager] Manual reconnect: ${id}`);
        
        // 执行重连
        return await this._performReconnect(id);
    }
    
    /**
     * 重连所有断开的连接
     */
    async reconnectAll() {
        const promises = [];
        
        for (const [id, conn] of this.connections.entries()) {
            if (conn.status === 'disconnected' || conn.status === 'error') {
                promises.push(this.reconnect(id));
            }
        }
        
        const results = await Promise.allSettled(promises);
        
        console.log(`[ResourceConnectionManager] Reconnected ${results.length} connections`);
        
        return results;
    }
    
    /**
     * 断开所有连接
     */
    disconnectAll() {
        for (const [id, conn] of this.connections.entries()) {
            if (conn.connection && conn.connection.disconnect) {
                conn.connection.disconnect();
                this.updateStatus(id, 'disconnected');
            }
        }
        
        console.log('[ResourceConnectionManager] All connections disconnected');
    }
    
    /**
     * 安排重连
     * @param {string} id - 连接ID
     */
    _scheduleReconnect(id) {
        const conn = this.connections.get(id);
        if (!conn) return;
        
        // 检查重连次数
        const attempts = this.reconnectAttempts.get(id)?.attempts || 0;
        if (attempts >= this.maxReconnectAttempts) {
            console.warn(`[ResourceConnectionManager] Max reconnect attempts reached: ${id}`);
            this._fireEvent('reconnectFailed', { id, attempts });
            return;
        }
        
        // 计算延迟
        const delay = this.reconnectDelays[Math.min(attempts, this.reconnectDelays.length - 1)];
        
        console.log(`[ResourceConnectionManager] Scheduling reconnect: ${id} in ${delay}ms (attempt ${attempts + 1})`);
        
        // 安排重连
        const timeout = setTimeout(async () => {
            await this._performReconnect(id);
        }, delay);
        
        this.reconnectAttempts.set(id, { attempts: attempts + 1, timeout });
    }
    
    /**
     * 执行重连
     * @param {string} id - 连接ID
     */
    async _performReconnect(id) {
        const conn = this.connections.get(id);
        if (!conn) return false;
        
        this.updateStatus(id, 'connecting');
        
        try {
            // 调用连接对象的connect方法
            if (conn.connection && conn.connection.connect) {
                await conn.connection.connect();
                this.updateStatus(id, 'connected');
                this._fireEvent('reconnectSuccess', { id });
                return true;
            }
        } catch (error) {
            console.error(`[ResourceConnectionManager] Reconnect failed: ${id}`, error);
            this.updateStatus(id, 'error', { error: error.message });
            
            // 继续尝试重连
            if (conn.autoReconnect) {
                this._scheduleReconnect(id);
            }
            
            return false;
        }
        
        return false;
    }
    
    /**
     * 更新统计
     */
    _updateStats() {
        this.connectionStats = {
            total: this.connections.size,
            connected: 0,
            disconnected: 0,
            connecting: 0,
            error: 0
        };
        
        for (const conn of this.connections.values()) {
            this.connectionStats[conn.status]++;
        }
    }
    
    /**
     * 触发事件
     * @param {string} event - 事件名称
     * @param {Object} data - 事件数据
     */
    _fireEvent(event, data) {
        // 这里可以添加事件分发逻辑
        console.log(`[ResourceConnectionManager] Event: ${event}`, data);
    }
    
    /**
     * 注册事件处理器
     * @param {string} event - 事件名称
     * @param {Function} handler - 处理器
     */
    on(event, handler) {
        // 这里可以添加事件处理器注册逻辑
    }
    
    /**
     * 健康检查
     */
    healthCheck() {
        const health = {
            status: 'healthy',
            connections: [],
            issues: []
        };
        
        for (const [id, conn] of this.connections.entries()) {
            const connHealth = {
                id,
                status: conn.status,
                errorCount: conn.errorCount,
                lastConnected: conn.lastConnected
            };
            
            // 检查是否有问题
            if (conn.status === 'error') {
                health.status = 'degraded';
                health.issues.push({
                    id,
                    issue: 'Connection in error state',
                    errorCount: conn.errorCount
                });
            } else if (conn.status === 'disconnected' && conn.autoReconnect) {
                health.status = 'degraded';
                health.issues.push({
                    id,
                    issue: 'Connection disconnected',
                    lastConnected: conn.lastConnected
                });
            }
            
            health.connections.push(connHealth);
        }
        
        return health;
    }
    
    /**
     * 销毁
     */
    destroy() {
        // 断开所有连接
        this.disconnectAll();
        
        // 清除所有重连定时器
        for (const [id, attempt] of this.reconnectAttempts.entries()) {
            clearTimeout(attempt.timeout);
        }
        this.reconnectAttempts.clear();
        
        // 清除连接
        this.connections.clear();
        
        console.log('[ResourceConnectionManager] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResourceConnectionManager;
}