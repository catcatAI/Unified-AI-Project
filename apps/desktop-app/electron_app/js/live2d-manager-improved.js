
/**
 * =============================================================================
 * 改进的 Live2D 模型加载系统
 * =============================================================================
 * 改进内容：
 * 1. 统一路径处理 - 使用配置化的模型路径
 * 2. 改进错误处理 - 详细的错误消息和重试机制
 * 3. 添加缓存机制 - 缓存已加载的模型资源
 * 4. 添加模型验证 - 验证模型文件完整性
 * =============================================================================
 */

// ========== 模型配置 ==========
const LIVE2D_MODEL_CONFIG = {
    // 默认模型路径
    defaultModel: 'models/miara_pro_en/runtime/miara_pro_t03.model3.json',
    
    // 可用模型列表
    availableModels: [
        {
            id: 'miara_pro',
            name: 'Miara Pro',
            path: 'models/miara_pro_en/runtime/miara_pro_t03.model3.json',
            description: 'Miara Pro English Edition'
        },
        {
            id: 'epsilon',
            name: 'Epsilon',
            path: 'models/epsilon/runtime/epsilon.model3.json',
            description: 'Epsilon Model'
        }
    ],
    
    // 加载配置
    loading: {
        maxRetries: 3,
        retryDelay: 1000,  // ms
        cacheEnabled: true,
        validateFiles: true
    }
};

// ========== 模型加载缓存 ==========
class Live2DModelCache {
    constructor() {
        this.cache = new Map();
        this.maxSize = 5;  // 最多缓存 5 个模型
    }
    
    set(key, data) {
        if (this.cache.size >= this.maxSize) {
            // 移除最旧的条目
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    get(key) {
        const entry = this.cache.get(key);
        if (entry) {
            // 检查缓存是否过期 (1小时)
            if (Date.now() - entry.timestamp < 3600000) {
                return entry.data;
            }
            this.cache.delete(key);
        }
        return null;
    }
    
    clear() {
        this.cache.clear();
    }
    
    size() {
        return this.cache.size;
    }
}

// ========== 模型验证器 ==========
class Live2DModelValidator {
    /**
     * 验证模型文件是否存在且有效
     * @param {string} modelPath - 模型 JSON 文件路径
     * @returns {Promise<{valid: boolean, errors: string[]}>}
     */
    static async validate(modelPath) {
        const errors = [];
        const warnings = [];
        
        try {
            // 检查 model3.json
            const modelJsonResponse = await fetch(`local://${modelPath}`);
            if (!modelJsonResponse.ok) {
                errors.push(`无法加载模型文件: ${modelPath}`);
                return { valid: false, errors, warnings };
            }
            
            const modelJson = await modelJsonResponse.json();
            
            // 验证必需的文件引用
            const fileRefs = modelJson.FileReferences;
            if (!fileRefs) {
                errors.push('模型 JSON 缺少 FileReferences 字段');
                return { valid: false, errors, warnings };
            }
            
            // 获取基础目录
            const lastSlash = modelPath.lastIndexOf('/');
            const baseDir = modelPath.substring(0, lastSlash + 1);
            
            // 检查 MOC3 文件
            const mocFileName = fileRefs.Moc;
            if (!mocFileName) {
                errors.push('模型缺少 MOC3 文件引用');
            } else {
                const mocPath = `local://${baseDir}${mocFileName}`;
                try {
                    const mocResponse = await fetch(mocPath, { method: 'HEAD' });
                    if (!mocResponse.ok) {
                        errors.push(`MOC3 文件不可访问: ${mocPath}`);
                    }
                } catch (e) {
                    errors.push(`MOC3 文件检查失败: ${mocPath}`);
                }
            }
            
            // 检查纹理文件
            const textures = fileRefs.Textures || [];
            if (textures.length === 0) {
                warnings.push('模型没有纹理文件');
            } else {
                for (let i = 0; i < textures.length; i++) {
                    const texPath = `local://${baseDir}${textures[i]}`;
                    try {
                        const texResponse = await fetch(texPath, { method: 'HEAD' });
                        if (!texResponse.ok) {
                            errors.push(`纹理文件 ${i+1} 不可访问: ${texPath}`);
                        }
                    } catch (e) {
                        errors.push(`纹理文件 ${i+1} 检查失败: ${texPath}`);
                    }
                }
            }
            
            // 检查可选文件
            if (!fileRefs.Physics) {
                warnings.push('模型没有物理模拟文件 (可选)');
            }
            if (!fileRefs.DisplayInfo) {
                warnings.push('模型没有显示信息文件 (可选)');
            }
            
        } catch (error) {
            errors.push(`验证过程中出错: ${error.message}`);
        }
        
        return {
            valid: errors.length === 0,
            errors,
            warnings
        };
    }
}

// ========== 改进的 Live2DManager 扩展 ==========
class ImprovedLive2DManager extends Live2DManager {
    constructor(canvas, unifiedDisplayMatrix = null, performanceManager = null) {
        super(canvas, unifiedDisplayMatrix, performanceManager);
        
        // 添加缓存
        this.modelCache = new Live2DModelCache();
        
        // 添加模型加载状态
        this.loadingState = {
            isLoading: false,
            currentAttempt: 0,
            lastError: null
        };
        
        // 添加模型列表
        this.availableModels = LIVE2D_MODEL_CONFIG.availableModels;
        this.currentModelId = null;
    }
    
    /**
     * 改进的模型加载方法
     * @param {string} modelIdOrPath - 模型 ID 或路径
     * @param {Object} options - 加载选项
     * @returns {Promise<boolean>}
     */
    async loadModel(modelIdOrPath, options = {}) {
        const {
            useCache = LIVE2D_MODEL_CONFIG.loading.cacheEnabled,
            validate = LIVE2D_MODEL_CONFIG.loading.validateFiles,
            retries = LIVE2D_MODEL_CONFIG.loading.maxRetries
        } = options;
        
        // 解析模型路径
        let modelPath = modelIdOrPath;
        let modelId = modelIdOrPath;
        
        // 如果是 ID，从配置中查找路径
        const modelConfig = this.availableModels.find(m => m.id === modelIdOrPath);
        if (modelConfig) {
            modelPath = modelConfig.path;
            modelId = modelConfig.id;
        }
        
        console.log(`[ImprovedLive2DManager] Loading model: ${modelId}`);
        console.log(`[ImprovedLive2DManager] Model path: ${modelPath}`);
        
        // 检查是否正在加载
        if (this.loadingState.isLoading) {
            console.warn('[ImprovedLive2DManager] 模型正在加载中...');
            return false;
        }
        
        this.loadingState.isLoading = true;
        this.loadingState.currentAttempt = 0;
        
        try {
            // 检查缓存
            if (useCache) {
                const cached = this.modelCache.get(modelId);
                if (cached) {
                    console.log('[ImprovedLive2DManager] 使用缓存的模型');
                    await this._applyCachedModel(cached);
                    this.currentModelId = modelId;
                    return true;
                }
            }
            
            // 验证模型文件
            if (validate) {
                console.log('[ImprovedLive2DManager] 验证模型文件...');
                const validation = await Live2DModelValidator.validate(modelPath);
                
                if (!validation.valid) {
                    console.error('[ImprovedLive2DManager] 模型验证失败:');
                    validation.errors.forEach(err => console.error(`  - ${err}`));
                    
                    if (validation.warnings.length > 0) {
                        console.warn('[ImprovedLive2DManager] 警告:');
                        validation.warnings.forEach(warn => console.warn(`  - ${warn}`));
                    }
                    
                    // 尝试加载下一个可用模型
                    return await this._tryNextModel(modelId, options);
                }
                
                if (validation.warnings.length > 0) {
                    console.warn('[ImprovedLive2DManager] 模型验证警告:');
                    validation.warnings.forEach(warn => console.warn(`  - ${warn}`));
                }
            }
            
            // 加载模型（带重试）
            const result = await this._loadModelWithRetry(modelPath, retries);
            
            if (result) {
                // 缓存模型
                if (useCache) {
                    this.modelCache.set(modelId, {
                        modelPath,
                        model3Json: this.model3Json,
                        moc3: this.moc3,
                        texturePaths: this.texturePaths,
                        physics3Json: this.physics3Json,
                        cdi3Json: this.cdi3Json
                    });
                }
                
                this.currentModelId = modelId;
                this.currentModel = modelPath;
                this.modelLoaded = true;
                
                console.log(`[ImprovedLive2DManager] 模型加载成功: ${modelId}`);
                return true;
            }
            
            return false;
            
        } catch (error) {
            console.error(`[ImprovedLive2DManager] 模型加载失败: ${error.message}`);
            this.loadingState.lastError = error;
            
            // 尝试加载下一个可用模型
            return await this._tryNextModel(modelId, options);
            
        } finally {
            this.loadingState.isLoading = false;
        }
    }
    
    /**
     * 带重试的模型加载
     * @param {string} modelPath - 模型路径
     * @param {number} maxRetries - 最大重试次数
     * @returns {Promise<boolean>}
     */
    async _loadModelWithRetry(modelPath, maxRetries) {
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            this.loadingState.currentAttempt = attempt + 1;
            
            try {
                console.log(`[ImprovedLive2DManager] 加载尝试 ${attempt + 1}/${maxRetries}`);
                
                // 调用父类的加载方法
                await super.loadModel({ modelPath });
                
                return true;
                
            } catch (error) {
                console.error(`[ImprovedLive2DManager] 加载尝试 ${attempt + 1} 失败: ${error.message}`);
                
                if (attempt < maxRetries - 1) {
                    // 等待后重试
                    const delay = LIVE2D_MODEL_CONFIG.loading.retryDelay * (attempt + 1);
                    console.log(`[ImprovedLive2DManager] 等待 ${delay}ms 后重试...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }
        
        return false;
    }
    
    /**
     * 尝试加载下一个可用模型
     * @param {string} failedModelId - 失败的模型 ID
     * @param {Object} options - 加载选项
     * @returns {Promise<boolean>}
     */
    async _tryNextModel(failedModelId, options) {
        const currentIndex = this.availableModels.findIndex(m => m.id === failedModelId);
        
        if (currentIndex < 0 || currentIndex >= this.availableModels.length - 1) {
            console.error('[ImprovedLive2DManager] 没有更多可用的模型');
            return false;
        }
        
        const nextModel = this.availableModels[currentIndex + 1];
        console.log(`[ImprovedLive2DManager] 尝试加载下一个模型: ${nextModel.id}`);
        
        return await this.loadModel(nextModel.id, options);
    }
    
    /**
     * 应用缓存的模型
     * @param {Object} cached - 缓存的模型数据
     * @returns {Promise<void>}
     */
    async _applyCachedModel(cached) {
        this.model3Json = cached.model3Json;
        this.moc3 = cached.moc3;
        this.texturePaths = cached.texturePaths;
        this.physics3Json = cached.physics3Json;
        this.cdi3Json = cached.cdi3Json;
        
        await this.createCubismModel();
        await this.setupMotionGroups();
        await this.setupModelParameters();
        this.createRenderer();
        
        this.isLoaded = true;
        this.isFallback = false;
        
        if (this.callbacks.onLoaded) {
            this.callbacks.onLoaded();
        }
    }
    
    /**
     * 获取可用模型列表
     * @returns {Array}
     */
    getAvailableModels() {
        return this.availableModels;
    }
    
    /**
     * 获取当前模型信息
     * @returns {Object|null}
     */
    getCurrentModelInfo() {
        if (!this.currentModelId) {
            return null;
        }
        
        return this.availableModels.find(m => m.id === this.currentModelId);
    }
    
    /**
     * 清除缓存
     */
    clearCache() {
        this.modelCache.clear();
        console.log('[ImprovedLive2DManager] 模型缓存已清除');
    }
}

// ========== 导出 ==========
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ImprovedLive2DManager,
        Live2DModelCache,
        Live2DModelValidator,
        LIVE2D_MODEL_CONFIG
    };
}
