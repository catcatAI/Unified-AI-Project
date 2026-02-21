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
            errors: 0,
            validationErrors: 0,
            securityErrors: 0
        };

        // 数据验证配置
        this.validationConfig = {
            enableChecksum: config.enableChecksum !== false,
            enableSizeValidation: config.enableSizeValidation !== false,
            enableTypeValidation: config.enableTypeValidation !== false,
            maxSizePerItem: config.maxSizePerItem || 1024 * 1024, // 1MB per item
            maxSizePerString: config.maxSizePerString || 100 * 1024, // 100KB per string
            allowedTypes: config.allowedTypes || [
                'string', 'number', 'boolean', 'object', 'array', 'null'
            ]
        };

        // 安全密钥（用于数据签名）
        this.securityKey = config.securityKey || this._generateSecurityKey();

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
     * 生成安全密钥
     * @returns {string} 安全密钥
     */
    _generateSecurityKey() {
        return 'angela_storage_security_' + Date.now();
    }

    /**
     * 计算数据的 checksum
     * @param {string} data 数据字符串
     * @returns {string} checksum
     */
    _calculateChecksum(data) {
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash.toString(16);
    }

    /**
     * 验证数据完整性
     * @param {Object} data 数据对象
     * @returns {boolean} 是否有效
     */
    _validateIntegrity(data) {
        if (!this.validationConfig.enableChecksum) {
            return true;
        }

        if (!data || !data.checksum || !data.value) {
            return false;
        }

        const serialized = JSON.stringify(data.value);
        const calculatedChecksum = this._calculateChecksum(serialized);

        return calculatedChecksum === data.checksum;
    }

    /**
     * 验证数据类型
     * @param {*} value 数据值
     * @returns {boolean} 是否有效
     */
    _validateType(value) {
        if (!this.validationConfig.enableTypeValidation) {
            return true;
        }

        const type = typeof value;
        const arrayType = Array.isArray(value) ? 'array' : type;

        return this.validationConfig.allowedTypes.includes(arrayType);
    }

    /**
     * 验证数据大小
     * @param {*} value 数据值
     * @returns {boolean} 是否有效
     */
    _validateSize(value) {
        if (!this.validationConfig.enableSizeValidation) {
            return true;
        }

        try {
            const serialized = JSON.stringify(value);

            // 检查总大小
            if (serialized.length > this.validationConfig.maxSizePerItem) {
                console.warn('[StorageManager] Data size exceeds limit:', serialized.length, '>', this.validationConfig.maxSizePerItem);
                return false;
            }

            // 检查字符串长度
            if (typeof value === 'string' && value.length > this.validationConfig.maxSizePerString) {
                console.warn('[StorageManager] String length exceeds limit:', value.length, '>', this.validationConfig.maxSizePerString);
                return false;
            }

            return true;
        } catch (error) {
            console.error('[StorageManager] Failed to validate size:', error);
            return false;
        }
    }

    /**
     * 检测恶意数据
     * @param {*} value 数据值
     * @returns {boolean} 是否安全
     */
    _detectMaliciousData(value) {
        if (typeof value === 'string') {
            // 检测潜在的 XSS 攻击
            const xssPatterns = [
                /<script/i,
                /javascript:/i,
                /onerror=/i,
                /onload=/i,
                /onclick=/i,
                /<iframe/i,
                /<object/i,
                /<embed/i
            ];

            for (const pattern of xssPatterns) {
                if (pattern.test(value)) {
                    console.warn('[StorageManager] Potential XSS detected in string data');
                    this.metrics.securityErrors++;
                    return false;
                }
            }
        }

        // 检测过深的嵌套（可能导致栈溢出）
        if (typeof value === 'object' && value !== null) {
            const depth = this._getObjectDepth(value);
            if (depth > 20) {
                console.warn('[StorageManager] Object nesting too deep:', depth);
                this.metrics.securityErrors++;
                return false;
            }
        }

        return true;
    }

    /**
     * 获取对象的嵌套深度
     * @param {*} obj 对象
     * @param {number} depth 当前深度
     * @returns {number} 深度
     */
    _getObjectDepth(obj, depth = 1) {
        if (typeof obj !== 'object' || obj === null) {
            return depth;
        }

        let maxDepth = depth;
        for (const value of Object.values(obj)) {
            if (typeof value === 'object' && value !== null) {
                const childDepth = this._getObjectDepth(value, depth + 1);
                maxDepth = Math.max(maxDepth, childDepth);
            }
        }

        return maxDepth;
    }

    /**
     * 验证数据
     * @param {*} value 数据值
     * @returns {Object} 验证结果 { valid: boolean, error: string }
     */
    validateData(value) {
        // 类型验证
        if (!this._validateType(value)) {
            this.metrics.validationErrors++;
            return {
                valid: false,
                error: 'Invalid data type'
            };
        }

        // 大小验证
        if (!this._validateSize(value)) {
            this.metrics.validationErrors++;
            return {
                valid: false,
                error: 'Data size exceeds limit'
            };
        }

        // 恶意数据检测
        if (!this._detectMaliciousData(value)) {
            this.metrics.securityErrors++;
            return {
                valid: false,
                error: 'Potential malicious data detected'
            };
        }

        return {
            valid: true,
            error: null
        };
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

        // 验证数据
        const validation = this.validateData(value);
        if (!validation.valid) {
            console.error('[StorageManager] Data validation failed:', validation.error, component, key);
            this.metrics.errors++;
            return false;
        }

        try {
            const fullKey = this._generateKey(component, key);

            // 序列化值以计算 checksum
            const serializedValue = JSON.stringify(value);
            const checksum = this._calculateChecksum(serializedValue);

            const data = {
                value: value,
                checksum: checksum,
                timestamp: Date.now(),
                expires: options.expires ? Date.now() + options.expires : null,
                version: options.version || 1,
                validated: true
            };

            const serialized = JSON.stringify(data);

            // 检查存储空间
            if (serialized.length > this.storageQuota) {
                console.error('[StorageManager] Data too large:', fullKey, serialized.length, '>', this.storageQuota);
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

            // 验证数据完整性
            if (data.validated && !this._validateIntegrity(data)) {
                console.error('[StorageManager] Data integrity check failed:', fullKey);
                this.metrics.validationErrors++;
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

    /**
     * 初始化版本控制
     * @returns {boolean} 是否成功
     */
    initVersionControl() {
        if (!this.storageAvailable) {
            return false;
        }

        const versionKey = `${this.namespace}_version`;
        const storedVersion = localStorage.getItem(versionKey);

        if (!storedVersion) {
            // 首次运行，写入当前版本
            localStorage.setItem(versionKey, this.currentVersion);
            console.log('[StorageManager] Version control initialized:', this.currentVersion);
            return true;
        }

        // 检查版本兼容性
        const compatibility = this._checkVersionCompatibility(storedVersion, this.currentVersion);

        if (!compatibility.compatible) {
            console.warn('[StorageManager] Version incompatible:', {
                stored: storedVersion,
                current: this.currentVersion,
                message: compatibility.message
            });

            // 尝试迁移
            const migrationResult = this._migrateData(storedVersion, this.currentVersion);

            if (migrationResult.success) {
                // 迁移成功，更新版本
                localStorage.setItem(versionKey, this.currentVersion);
                console.log('[StorageManager] Migration successful:', this.currentVersion);
                return true;
            } else {
                console.error('[StorageManager] Migration failed:', migrationResult.error);
                return false;
            }
        } else if (storedVersion !== this.currentVersion) {
            // 版本兼容但不是最新，更新版本号
            localStorage.setItem(versionKey, this.currentVersion);
            console.log('[StorageManager] Version updated:', this.currentVersion);
            return true;
        }

        return true;
    }

    /**
     * 检查版本兼容性
     * @param {string} storedVersion 存储的版本
     * @param {string} currentVersion 当前版本
     * @returns {Object} 兼容性检查结果
     */
    _checkVersionCompatibility(storedVersion, currentVersion) {
        // 简单的版本比较
        const storedParts = storedVersion.split('.').map(Number);
        const currentParts = currentVersion.split('.').map(Number);
        const minParts = this.minimumCompatibleVersion.split('.').map(Number);

        // 检查是否低于最低兼容版本
        for (let i = 0; i < Math.max(storedParts.length, minParts.length); i++) {
            const s = storedParts[i] || 0;
            const m = minParts[i] || 0;
            if (s < m) {
                return {
                    compatible: false,
                    message: `Version ${storedVersion} is below minimum compatible version ${this.minimumCompatibleVersion}`
                };
            }
        }

        // 检查是否需要迁移
        for (let i = 0; i < Math.max(storedParts.length, currentParts.length); i++) {
            const s = storedParts[i] || 0;
            const c = currentParts[i] || 0;
            if (c > s) {
                return {
                    compatible: true,
                    needsMigration: true,
                    message: `Version ${storedVersion} can be migrated to ${currentVersion}`
                };
            }
        }

        return {
            compatible: true,
            needsMigration: false,
            message: `Version ${storedVersion} is compatible with ${currentVersion}`
        };
    }

    /**
     * 迁移数据
     * @param {string} fromVersion 源版本
     * @param {string} toVersion 目标版本
     * @returns {Object} 迁移结果
     */
    _migrateData(fromVersion, toVersion) {
        try {
            const backup = this.exportData();
            let currentData = backup;
            const versionPath = this._getVersionPath(fromVersion, toVersion);

            console.log('[StorageManager] Starting migration:', versionPath);

            // 按顺序执行迁移
            for (const version of versionPath) {
                const migration = this.migrations.find(m => m.version === version);
                if (migration) {
                    console.log('[StorageManager] Running migration:', version);
                    currentData = migration.migrate(currentData);
                }
            }

            // 应用迁移后的数据
            localStorage.clear();
            this.importData(currentData);

            return {
                success: true,
                fromVersion,
                toVersion,
                versionPath
            };
        } catch (error) {
            console.error('[StorageManager] Migration error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取版本迁移路径
     * @param {string} fromVersion 源版本
     * @param {string} toVersion 目标版本
     * @returns {Array} 版本路径
     */
    _getVersionPath(fromVersion, toVersion) {
        const versions = this.migrations.map(m => m.version);
        const fromIndex = versions.indexOf(fromVersion);
        const toIndex = versions.indexOf(toVersion);

        if (fromIndex === -1 || toIndex === -1) {
            return [];
        }

        return versions.slice(fromIndex + 1, toIndex + 1);
    }

    /**
     * 迁移到 1.1.0
     * @param {Object} data 数据
     * @returns {Object} 迁移后的数据
     */
    _migrateTo110(data) {
        // 示例迁移逻辑
        return data;
    }

    /**
     * 迁移到 1.2.0
     * @param {Object} data 数据
     * @returns {Object} 迁移后的数据
     */
    _migrateTo120(data) {
        // 示例迁移逻辑
        return data;
    }

    /**
     * 生成安全密钥
     * @private
     */
    _generateSecurityKey() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2);
        return `angela_${timestamp}_${random}`;
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