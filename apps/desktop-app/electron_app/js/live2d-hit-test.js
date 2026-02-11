/**
 * Angela AI - Live2D Hit Test Manager
 * 
 * Live2D原生hitTest功能 - 使用Cubism SDK API精确检测触摸区域
 * 
 * 功能：
 * - 基于Live2D SDK的getDrawableAt获取精确触摸区域
 * - 支持多drawable的hitArea检测
 * - 与UnifiedDisplayMatrix集成
 * - 缓存机制提高性能
 * - 调试和可视化功能
 */

class Live2DHitTestManager {
    constructor(options = {}) {
        // ============================================================
        // 配置
        // ============================================================
        this.config = {
            enabled: true,
            cacheEnabled: true,
            cacheSize: 100,
            cacheTTL: 1000,  // 缓存有效期（毫秒）
            debugMode: false,
            debugCanvas: null,
            debugCtx: null
        };

        // ============================================================
        // Live2D组件引用
        // ============================================================
        this.live2DManager = null;
        this.cubismWrapper = null;
        this.unifiedDisplayMatrix = null;

        // ============================================================
        // HitArea映射
        // ============================================================
        // 将drawableID映射到身体部位名称
        this.hitAreaMapping = {
            'ParamEyeBallX': 'eyes',
            'ParamEyeBallY': 'eyes',
            'ParamMouthForm': 'mouth',
            'ParamMouthOpenY': 'mouth',
            'ParamCheek': 'face',
            'ParamBrowLY': 'face',
            'ParamBrowRY': 'face',
            'ParamBrowLX': 'face',
            'ParamBrowRX': 'face',
            'ParamHairFront': 'hair',
            'ParamHairSide': 'hair',
            'ParamHairBack': 'hair',
            'ParamBodyAngleX': 'body',
            'ParamBodyAngleY': 'body',
            'ParamArmL': 'shoulders',
            'ParamArmR': 'shoulders'
        };

        // ============================================================
        // 缓存
        // ============================================================
        this.hitTestCache = new Map();
        this.lastCacheClean = Date.now();

        // ============================================================
        // 统计
        // ============================================================
        this.stats = {
            hitTests: 0,
            cacheHits: 0,
            cacheMisses: 0,
            errors: 0
        };

        console.log('[HitTestManager] Initialized');
    }

    // ================================================================
    // 初始化和连接
    // ================================================================

    /**
     * 连接Live2D组件
     */
    connect(live2DManager, cubismWrapper, unifiedDisplayMatrix) {
        this.live2DManager = live2DManager;
        this.cubismWrapper = cubismWrapper;
        this.unifiedDisplayMatrix = unifiedDisplayMatrix;

        console.log('[HitTestManager] Connected to Live2D components');
    }

    /**
     * 设置调试模式
     */
    setDebugMode(enabled, debugCanvas = null) {
        this.config.debugMode = enabled;
        if (debugCanvas) {
            this.config.debugCanvas = debugCanvas;
            this.config.debugCtx = debugCanvas.getContext('2d');
        }
        console.log('[HitTestManager] Debug mode:', enabled);
    }

    // ================================================================
    // Hit Test 核心方法
    // ================================================================

    /**
     * 执行hitTest检测
     * @param {number} x - 画布X坐标
     * @param {number} y - 画布Y坐标
     * @returns {object} - 检测结果
     */
    hitTest(x, y) {
        if (!this.config.enabled) {
            return null;
        }

        this.stats.hitTests++;

        // 检查缓存
        if (this.config.cacheEnabled) {
            const cacheKey = `${Math.floor(x)}_${Math.floor(y)}`;
            const cached = this._getFromCache(cacheKey);
            if (cached) {
                this.stats.cacheHits++;
                return cached;
            }
        }

        this.stats.cacheMisses++;

        try {
            // 获取drawable
            const drawable = this._getDrawableAt(x, y);
            
            if (!drawable) {
                return null;
            }

            // 解析drawable信息
            const result = this._parseDrawable(drawable, x, y);

            // 缓存结果
            if (this.config.cacheEnabled && result) {
                const cacheKey = `${Math.floor(x)}_${Math.floor(y)}`;
                this._addToCache(cacheKey, result);
            }

            // 调试可视化
            if (this.config.debugMode) {
                this._debugDraw(result);
            }

            return result;
        } catch (error) {
            console.error('[HitTestManager] Hit test failed:', error);
            this.stats.errors++;
            return null;
        }
    }

    /**
     * 获取指定位置的drawable
     */
    _getDrawableAt(x, y) {
        if (!this.cubismWrapper || !this.cubismWrapper.live2dModel) {
            console.warn('[HitTestManager] Cubism model not available');
            return null;
        }

        try {
            // 获取Live2D模型
            const model = this.cubismWrapper.live2dModel;
            
            // 检查是否有getDrawableAt方法（Cubism SDK 4.x）
            if (typeof model.getDrawableAt === 'function') {
                const drawableIndex = model.getDrawableAt(x, y);
                if (drawableIndex >= 0) {
                    return this._getDrawableInfo(drawableIndex);
                }
            }
            
            // 备用方案：检查所有drawable的hitAreas
            return this._checkDrawableHitAreas(x, y);
        } catch (error) {
            console.error('[HitTestManager] GetDrawableAt failed:', error);
            return null;
        }
    }

    /**
     * 获取drawable信息
     */
    _getDrawableInfo(drawableIndex) {
        if (!this.cubismWrapper || !this.cubismWrapper.live2dModel) {
            return null;
        }

        try {
            const model = this.cubismWrapper.live2dModel;
            
            // 获取drawable信息
            const info = {
                index: drawableIndex,
                id: model.getDrawableId(drawableIndex),
                name: model.getDrawableName(drawableIndex),
                visible: model.getDrawableVisible(drawableIndex),
                opacity: model.getDrawableOpacity(drawableIndex)
            };

            return info;
        } catch (error) {
            console.error('[HitTestManager] GetDrawableInfo failed:', error);
            return null;
        }
    }

    /**
     * 检查drawable的hitAreas
     */
    _checkDrawableHitAreas(x, y) {
        if (!this.cubismWrapper || !this.cubismWrapper.live2dModel) {
            return null;
        }

        try {
            const model = this.cubismWrapper.live2dModel;
            
            // 获取drawable数量
            const drawableCount = model.getDrawableCount ? model.getDrawableCount() : 0;
            
            // 检查每个drawable
            for (let i = 0; i < drawableCount; i++) {
                if (!model.getDrawableVisible(i)) {
                    continue;
                }

                // 检查点是否在drawable区域内
                if (this._isPointInDrawable(x, y, i)) {
                    return this._getDrawableInfo(i);
                }
            }

            return null;
        } catch (error) {
            console.error('[HitTestManager] CheckDrawableHitAreas failed:', error);
            return null;
        }
    }

    /**
     * 检查点是否在drawable区域内
     */
    _isPointInDrawable(x, y, drawableIndex) {
        if (!this.cubismWrapper || !this.cubismWrapper.live2dModel) {
            return false;
        }

        try {
            const model = this.cubismWrapper.live2dModel;
            
            // 获取drawable的边界
            const left = model.getDrawableLeft(drawableIndex);
            const right = model.getDrawableRight(drawableIndex);
            const top = model.getDrawableTop(drawableIndex);
            const bottom = model.getDrawableBottom(drawableIndex);

            // 检查点是否在边界内
            return x >= left && x <= right && y >= top && y <= bottom;
        } catch (error) {
            return false;
        }
    }

    /**
     * 解析drawable信息为身体部位
     */
    _parseDrawable(drawable, x, y) {
        if (!drawable) {
            return null;
        }

        // 从drawable ID或名称提取身体部位
        let bodyPart = null;
        
        // 检查ID映射
        for (const [paramId, part] of Object.entries(this.hitAreaMapping)) {
            if (drawable.id && drawable.id.includes(paramId)) {
                bodyPart = part;
                break;
            }
            if (drawable.name && drawable.name.includes(paramId)) {
                bodyPart = part;
                break;
            }
        }

        // 如果没有找到，使用默认值
        if (!bodyPart) {
            bodyPart = 'body';
        }

        return {
            bodyPart: bodyPart,
            drawable: {
                id: drawable.id,
                name: drawable.name,
                index: drawable.index,
                visible: drawable.visible,
                opacity: drawable.opacity
            },
            position: {
                x: x,
                y: y
            },
            timestamp: Date.now()
        };
    }

    // ================================================================
    // 缓存管理
    // ================================================================

    _addToCache(key, value) {
        if (this.hitTestCache.size >= this.config.cacheSize) {
            this._cleanCache();
        }
        
        this.hitTestCache.set(key, {
            value: value,
            timestamp: Date.now()
        });
    }

    _getFromCache(key) {
        const entry = this.hitTestCache.get(key);
        if (!entry) {
            return null;
        }

        const age = Date.now() - entry.timestamp;
        if (age > this.config.cacheTTL) {
            this.hitTestCache.delete(key);
            return null;
        }

        return entry.value;
    }

    _cleanCache() {
        const now = Date.now();
        const keysToDelete = [];

        for (const [key, entry] of this.hitTestCache.entries()) {
            const age = now - entry.timestamp;
            if (age > this.config.cacheTTL) {
                keysToDelete.push(key);
            }
        }

        keysToDelete.forEach(key => this.hitTestCache.delete(key));
        this.lastCacheClean = now;
    }

    clearCache() {
        this.hitTestCache.clear();
    }

    // ================================================================
    // 调试功能
    // ================================================================

    _debugDraw(result) {
        if (!this.config.debugCtx || !result) {
            return;
        }

        const ctx = this.config.debugCtx;
        const size = 20;

        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(result.position.x, result.position.y, size, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = '#00ff00';
        ctx.font = '12px Arial';
        ctx.fillText(
            `${result.bodyPart} (${result.drawable.id})`,
            result.position.x + size + 5,
            result.position.y
        );
    }

    // ================================================================
    // 工具方法
    // ================================================================

    /**
     * 获取所有可点击的身体部位
     */
    getInteractiveParts() {
        return Object.keys(this.hitAreaMapping).map(paramId => ({
            paramId: paramId,
            bodyPart: this.hitAreaMapping[paramId]
        }));
    }

    /**
     * 添加hitArea映射
     */
    addHitAreaMapping(paramId, bodyPart) {
        this.hitAreaMapping[paramId] = bodyPart;
    }

    /**
     * 移除hitArea映射
     */
    removeHitAreaMapping(paramId) {
        delete this.hitAreaMapping[paramId];
    }

    // ================================================================
    // 统计和状态
    // ================================================================

    getStats() {
        return {
            ...this.stats,
            cacheSize: this.hitTestCache.size,
            cacheHitRate: this.stats.hitTests > 0 
                ? (this.stats.cacheHits / this.stats.hitTests * 100).toFixed(2) + '%'
                : '0%'
        };
    }

    resetStats() {
        this.stats = {
            hitTests: 0,
            cacheHits: 0,
            cacheMisses: 0,
            errors: 0
        };
    }

    getConfig() {
        return { ...this.config };
    }

    setConfig(config) {
        this.config = { ...this.config, ...config };
    }

    // ================================================================
    // 销毁
    // ================================================================

    destroy() {
        this.clearCache();
        this.live2DManager = null;
        this.cubismWrapper = null;
        this.unifiedDisplayMatrix = null;
        this.config.debugCanvas = null;
        this.config.debugCtx = null;
        console.log('[HitTestManager] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DHitTestManager;
}