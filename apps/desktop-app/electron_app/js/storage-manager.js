/**
 * Angela AI - Unified Storage Manager
 * 
 * 统一的localStorage管理器，防止不同组件间的数据冲突
 * 
 * 功能：
 * - 统一的命名空间管理
 * - 自动添加组件前缀
 * - 类型安全的数据存取
 * - 自动JSON序列化/反序列化
 * - 存储空间监控
 * - 数据过期管理
 * - 备份和恢复功能
 */

class UnifiedStorageManager {
    constructor(config = {}) {
        this.namespace = config.namespace || 'angela';
        this.storageAvailable = this._checkStorageAvailability();
        this.storageQuota = config.storageQuota || 5 * 1024 * 1024; // 默认5MB
        this.componentPrefixes = {
            'backend': 'be',
            'live2d': 'l2d',
            'state': 'sm',
            'audio': 'au',
            'performance': 'pm',
            'websocket': 'ws',
            'haptic': 'ha',
            'logger': 'log',
            'data': 'dt',
            'app': 'app'
        };
        this.metrics = {
            getOperations: 0,
            setOperations: 0,
            deleteOperations: 0,
            errors: 0
        };
        
        console.log('[StorageManager] Initialized with namespace:', this.namespace);
    }
    
    /**
     * 检查localStorage是否可用
     */
    _checkStorageAvailability() {
        try {
            const testKey = '__storage_test__';
            localStorage.setItem(testKey, 'test');
            localStorage.removeItem(testKey);
            return true;
        } catch (error) {
            console.error('[StorageManager] localStorage not available:', error);
            return false;
        }
    }
    
    /**
     * 生成完整的存储键
     * @param {string} component 组件名称
     * @param {string} key 数据键
     * @returns {string} 完整的存储键
     */
    _generateKey(component, key) {
        const prefix = this.componentPrefixes[component] || 'custom';
        return `${this.namespace}_${prefix}_${key}`;
    }
    
    /**
     * 设置数据
     * @param {string} component 组件名称
     * @param {string} key 数据键
     * @param {*} value 数据值
     * @param {Object} options 选项
     * @returns {boolean} 是否成功
     */
    set(component, key, value, options = {}) {
        if (!this.storageAvailable) {
            console.warn('[StorageManager] localStorage not available');
            return false;
        }
        
        try {
            const fullKey = this._generateKey(component, key);
            const data = {
                value: value,
                timestamp: Date.now(),
                expires: options.expires ? Date.now() + options.expires : null,
                version: options.version || 1
            };
            
            const serialized = JSON.stringify(data);
            
            // 检查存储空间
            if (serialized.length > this.storageQuota) {
                console.error('[StorageManager] Data too large:', fullKey);
                return false;
            }
            
            localStorage.setItem(fullKey, serialized);
            this.metrics.setOperations++;
            return true;
        } catch (error) {
            console.error('[StorageManager] Failed to set:', component, key, error);
            this.metrics.errors++;
            return false;
        }
    }
    
    /**
     * 获取数据
     * @param {string} component 组件名称
     * @param {string} key 数据键
     * @param {*} defaultValue 默认值
     * @returns {*} 数据值或默认值
     */
    get(component, key, defaultValue = null) {
        if (!this.storageAvailable) {
            console.warn('[StorageManager] localStorage not available');
            return defaultValue;
        }
        
        try {
            const fullKey = this._generateKey(component, key);
            const serialized = localStorage.getItem(fullKey);
            
            if (!serialized) {
                return defaultValue;
            }
            
            const data = JSON.parse(serialized);
            
            // 检查数据是否过期
            if (data.expires && Date.now() > data.expires) {
                this.delete(component, key);
                return defaultValue;
            }
            
            this.metrics.getOperations++;
            return data.value;
        } catch (error) {
            console.error('[StorageManager] Failed to get:', component, key, error);
            this.metrics.errors++;
            return defaultValue;
        }
    }
    
    /**
     * 删除数据
     * @param {string} component 组件名称
     * * @param {string} key 数据键（可选）
     * @returns {boolean} 是否成功
     */
    delete(component, key = null) {
        if (!this.storageAvailable) {
            return false;
        }
        
        try {
            if (key) {
                const fullKey = this._generateKey(component, key);
                localStorage.removeItem(fullKey);
            } else {
                // 删除组件的所有数据
                const prefix = `${this.namespace}_${this.componentPrefixes[component] || 'custom'}_`;
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const storageKey = localStorage.key(i);
                    if (storageKey.startsWith(prefix)) {
                        keysToRemove.push(storageKey);
                    }
                }
                keysToRemove.forEach(k => localStorage.removeItem(k));
            }
            
            this.metrics.deleteOperations++;
            return true;
        } catch (error) {
            console.error('[StorageManager] Failed to delete:', component, key, error);
            this.metrics.errors++;
            return false;
        }
    }
    
    /**
     * 检查数据是否存在
     * @param {string} component 组件名称
     * @param {string} key 数据键
     * @returns {boolean} 是否存在
     */
    has(component, key) {
        if (!this.storageAvailable) {
            return false;
        }
        
        try {
            const fullKey = this._generateKey(component, key);
            const serialized = localStorage.getItem(fullKey);
            
            if (!serialized) {
                return false;
            }
            
            const data = JSON.parse(serialized);
            
            // 检查数据是否过期
            if (data.expires && Date.now() > data.expires) {
                this.delete(component, key);
                return false;
            }
            
            return true;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * 获取组件的所有键
     * @param {string} component 组件名称
     * @returns {Array} 键列表
     */
    getKeys(component) {
        if (!this.storageAvailable) {
            return [];
        }
        
        try {
            const prefix = `${this.namespace}_${this.componentPrefixes[component] || 'custom'}_`;
            const keys = [];
            
            for (let i = 0; i < localStorage.length; i++) {
                const storageKey = localStorage.key(i);
                if (storageKey.startsWith(prefix)) {
                    // 移除前缀，返回原始键
                    const originalKey = storageKey.substring(prefix.length);
                    keys.push(originalKey);
                }
            }
            
            return keys;
        } catch (error) {
            console.error('[StorageManager] Failed to get keys:', component, error);
            return [];
        }
    }
    
    /**
     * 清理组件的所有数据
     * @param {string} component 组件名称
     * @returns {number} 清理的数量
     */
    clear(component) {
        const keys = this.getKeys(component);
        this.delete(component);
        return keys.length;
    }
    
    /**
     * 清理所有过期数据
     * @returns {number} 清理的数量
     */
    cleanupExpired() {
        if (!this.storageAvailable) {
            return 0;
        }
        
        try {
            let cleanedCount = 0;
            const now = Date.now();
            const keysToRemove = [];
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key.startsWith(`${this.namespace}_`)) {
                    try {
                        const data = JSON.parse(localStorage.getItem(key));
                        if (data.expires && now > data.expires) {
                            keysToRemove.push(key);
                        }
                    } catch (e) {
                        // 忽略解析错误，这些键可能在清理范围外
                    }
                }
            }
            
            keysToRemove.forEach(k => localStorage.removeItem(k));
            cleanedCount = keysToRemove.length;
            
            if (cleanedCount > 0) {
                console.log('[StorageManager] 清理了', cleanedCount, '个过期数据');
            }
            
            return cleanedCount;
        } catch (error) {
            console.error('[StorageManager] Cleanup failed:', error);
            return 0;
        }
    }
    
    /**
     * 获取存储使用情况
     * @returns {Object} 存储使用情况
     */
    getStorageUsage() {
        if (!this.storageAvailable) {
            return { available: false, used: 0, total: 0, percentage: 0 };
        }
        
        try {
            let used = 0;
            const namespacePrefix = `${this.namespace}_`;
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key.startsWith(namespacePrefix)) {
                    used += localStorage.getItem(key).length;
                }
            }
            
            return {
                available: true,
                used: used,
                total: this.storageQuota,
                percentage: (used / this.storageQuota) * 100,
                keysCount: localStorage.length
            };
        } catch (error) {
            console.error('[StorageManager] Failed to get storage usage:', error);
            return { available: false, used: 0, total: 0, percentage: 0 };
        }
    }
    
    /**
     * 获取指标
     * @returns {Object} 指标数据
     */
    getMetrics() {
        return { ...this.metrics };
    }
    
    /**
     * 重置指标
     */
    resetMetrics() {
        this.metrics = {
            getOperations: 0,
            setOperations: 0,
            deleteOperations: 0,
            errors: 0
        };
    }
    
    /**
     * 导出数据
     * @returns {Object} 所有数据
     */
    exportData() {
        if (!this.storageAvailable) {
            return null;
        }
        
        try {
            const data = {};
            const namespacePrefix = `${this.namespace}_`;
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key.startsWith(namespacePrefix)) {
                    data[key] = localStorage.getItem(key);
                }
            }
            
            return data;
        } catch (error) {
            console.error('[StorageManager] Export failed:', error);
            return null;
        }
    }
    
    /**
     * 导入数据
     * @param {Object} data 数据对象
     * @returns {boolean} 是否成功
     */
    importData(data) {
        if (!this.storageAvailable || !data) {
            return false;
        }
        
        try {
            const namespacePrefix = `${this.namespace}_`;
            
            for (const [key, value] of Object.entries(data)) {
                if (key.startsWith(namespacePrefix)) {
                    localStorage.setItem(key, value);
                }
            }
            
            console.log('[StorageManager] 导入了', Object.keys(data).length, '条数据');
            return true;
        } catch (error) {
            console.error('[StorageManager] Import failed:', error);
            return false;
        }
    }
}

// 创建全局单例
if (typeof window !== 'undefined') {
    window.unifiedStorageManager = new UnifiedStorageManager();
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedStorageManager;
}