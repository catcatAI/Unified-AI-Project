/**
 * =============================================================================
 * ANGELA-MATRIX: L6[执行层] γ [C] L1+
 * =============================================================================
 *
 * 职责: 控制 Live2D 模型渲染，处理物理模拟和动画
 * 维度: 主要涉及物理维度 (γ) 的位置、速度、碰撞、表情和动作
 * 安全: 使用 Key C (桌面同步) 进行本地渲染
 * 成熟度: L1+ 等级即可看到视觉效果
 *
 * 功能:
 * - Live2D 模型加载和渲染 (60fps)
 * - 7 种表情: neutral, happy, sad, angry, surprised, confused, sleepy
 * - 10 种动作: idle, talk, think, happy, sad, angry, surprised, confused, sleepy, dance
 * - 物理模拟: 头发和衣服律动
 * - 唇型同步: 实时音频驱动的嘴唇动画
 *
 * @class Live2DManager
 */

// 导入 Cubism SDK Wrapper
// Live2DCubismWrapper 在 live2d-cubism-wrapper.js 中定义

class Live2DManager {
    constructor(canvas, unifiedDisplayMatrix = null, performanceManager = null) {
        console.log('[Live2DManager] Constructor with UDM:', !!unifiedDisplayMatrix, 'PM:', !!performanceManager);
        
        this.canvas = canvas;
        this.udm = unifiedDisplayMatrix;
        this.performanceManager = performanceManager;
        
        // Core state
        this.gl = null;
        this.wrapper = null;
        this.isFramework = false;
        this.frameworkLoaded = false;
        this.isFallback = true;
        
        this.modelLoaded = false;
        this.currentModel = null;
        
        // Rendering state
        this.isRunning = false;
        this.lastFrameTime = 0;
        this.currentExpression = 'neutral';
        this.currentMotion = 'idle';
        
        // Performance settings
        this.resolutionScale = 1.0;
        this.effectsLevel = 1.0;
        this.targetFPS = 60;
        this.currentFPS = 60;
        this.frameRate = 60;
        
        // Feature flags
        this.features = {
            advanced_animations: true,
            physics: true,
            lip_sync: true
        };
        
        // Effects
        this.effects = {
            breathing: true,
            blinking: true,
            idle_motion: true
        };
        
        // Fallback rendering - 三層渲染系統
        this.fallbackCanvas = null;
        this.fallbackCtx = null;
        this.fallbackWrapper = null;
        this.layerRenderer = null;  // LayerRenderer 實例
        this.characterImages = {};  // 存储所有加载的立繪圖片
        this.currentCharacterImageId = 'fullbody_ai_assistant';  // 當前選擇的主立繪ID
        this.expressionIndex = 0;  // 當前表情索引
        this.poseIndex = 0;  // 當前姿態索引
        this.lastRenderedImageId = '';  // 跟踪上次渲染的圖片
        this.lastRenderedSpriteIndex = -1;  // 跟踪上次渲染的 sprite sheet 索引
        
        // Expressions
        this.expressions = {
            neutral: { ParamEyeLOpen: 1, ParamEyeROpen: 1, ParamMouthForm: 0, ParamCheek: 0 },
            happy: { ParamEyeLOpen: 0.8, ParamEyeROpen: 0.8, ParamEyeLSmile: 1, ParamMouthForm: 0.5, ParamCheek: 0.5 },
            sad: { ParamEyeLOpen: 0.6, ParamEyeROpen: 0.6, ParamMouthForm: -0.3, ParamCheek: 0 },
            angry: { ParamEyeLOpen: 0.7, ParamEyeROpen: 0.7, ParamMouthForm: -0.4, ParamCheek: 0 },
            surprised: { ParamEyeLOpen: 1, ParamEyeROpen: 1, ParamMouthOpenY: 0.8, ParamCheek: 0 },
            shy: { ParamEyeLOpen: 0.7, ParamEyeROpen: 0.7, ParamMouthForm: 0.2, ParamCheek: 0.5 },
            love: { ParamEyeLOpen: 0.8, ParamEyeROpen: 0.8, ParamMouthForm: 0.3, ParamCheek: 0.8 },
            calm: { ParamEyeLOpen: 1, ParamEyeROpen: 1, ParamMouthForm: 0, ParamCheek: 0 }
        };
        
        // Parameters (for fallback mode)
        this.parameters = {
            ParamBreath: 0,
            ParamEyeLOpen: 1,
            ParamEyeROpen: 1,
            ParamEyeLSmile: 0,
            ParamEyeRSmile: 0,
            ParamMouthForm: 0,
            ParamMouthOpenY: 0,
            ParamBodyAngleX: 0,
            ParamBodyAngleY: 0,
            ParamCheek: 0
        };
        
        // Clickable regions
        this.clickableRegions = [];
        
        // Eye tracking
        this.eyeTracking = { x: 0.5, y: 0.5 };
        this.lipSync = { level: 0, phoneme: null };
        
        // Initialize
        this._init();
    }
    
    async initialize() {
        console.log('[Live2DManager] initialize() called');
        return this.modelLoaded;
    }
    
    async loadModel(modelPath) {
        console.log('[Live2DManager] loadModel():', modelPath);
        this.currentModel = modelPath;
        this.modelLoaded = true;
        return true;
    }

    /**
     * 驗證模型尺寸
     * @param {number} width - 模型寬度
     * @param {number} height - 模型高度
     * @returns {object} - 驗證結果
     */
    validateModelSize(width, height) {
        const baseWidth = 1280;  // 720p 基準寬度
        const baseHeight = 720;  // 720p 基準高度

        // 檢查基本有效性
        if (!width || !height || width <= 0 || height <= 0) {
            return {
                valid: false,
                error: '無效的模型尺寸',
                expected: { width: baseWidth, height: baseHeight },
                actual: { width, height }
            };
        }

        // 計算寬高比
        const expectedRatio = baseWidth / baseHeight;
        const actualRatio = width / height;
        const ratioDiff = Math.abs(actualRatio - expectedRatio);

        // 檢查寬高比（允許 ±5% 偏差）
        if (ratioDiff > expectedRatio * 0.05) {
            return {
                valid: false,
                error: '模型寬高比超出允許範圍',
                expectedRatio: expectedRatio.toFixed(2),
                actualRatio: actualRatio.toFixed(2),
                expected: { width: baseWidth, height: baseHeight },
                actual: { width, height }
            };
        }

        // 檢查尺寸範圍（允許 ±20% 偏差）
        const widthDiff = Math.abs(width - baseWidth) / baseWidth;
        const heightDiff = Math.abs(height - baseHeight) / baseHeight;

        if (widthDiff > 0.2 || heightDiff > 0.2) {
            console.warn('[Live2DManager] 模型尺寸超出建議範圍（±20%）', {
                expected: { width: baseWidth, height: baseHeight },
                actual: { width, height },
                widthDiff: (widthDiff * 100).toFixed(1) + '%',
                heightDiff: (heightDiff * 100).toFixed(1) + '%'
            });
        }

        return {
            valid: true,
            message: '模型尺寸驗證通過',
            expected: { width: baseWidth, height: baseHeight },
            actual: { width, height },
            ratioDiff: ratioDiff.toFixed(4)
        };
    }
    
    _init() {
        console.log('[Live2DManager] Initializing...');
        this._waitForSDKAndInitialize();
    }
    
    _waitForSDKAndInitialize(maxWait = 5000, interval = 100) {
        const startTime = Date.now();
        
        const checkAndInit = () => {
            const elapsed = Date.now() - startTime;
            
            if (typeof window.Live2DCubismCore !== 'undefined') {
                console.log('[Live2DManager] Cubism Core detected after', elapsed, 'ms');
                this._initializeWithSDK(window.Live2DCubismCore);
            } else if (elapsed < maxWait) {
                console.log('[Live2DManager] Waiting for SDK...', elapsed, 'ms');
                setTimeout(checkAndInit, interval);
            } else {
                console.log('[Live2DManager] SDK timeout after', elapsed, 'ms, using 2D fallback');
                this._createFallbackManager();
            }
        };
        
        checkAndInit();
    }
    
    _initializeWithSDK(CubismCore) {
        this.isFramework = true;
        this.isFallback = false;
        
        // 加载 Live2D 模型
        this._loadLive2DModel();
    }
    
    async _loadLive2DModel() {
        console.log('[Live2DManager] Loading Live2D model...');
        
        // 無論 Live2D 是否加載成功，都先加載立繪圖片
        await this._loadCharacterImage();
        
        // 使用完整文件路径
        const modelPath = 'models/miara_pro_en/runtime/miara_pro_t03.model3.json';
        const settings = { modelPath: modelPath };
        
        try {
            // 确保 wrapper 已创建
            if (!this.wrapper) {
                console.log('[Live2DManager] Creating Live2DCubismWrapper...');
                this.wrapper = new Live2DCubismWrapper(this.canvas);
            }
            
            // 加载模型
            await this.wrapper.loadModel(settings);
            await this.wrapper.start();
            
            this.modelLoaded = true;
            this.isFallback = false;
            this.currentModel = modelPath;
            
            // 隐藏 fallback canvas，显示 live2d canvas
            const fallbackCanvas = document.getElementById('fallback-canvas');
            const fallbackWrapper = document.getElementById('fallback-wrapper');
            if (fallbackCanvas) fallbackCanvas.style.display = 'none';
            if (fallbackWrapper) fallbackWrapper.classList.remove('visible');
            this.canvas.style.display = 'block';
            
            console.log('[Live2DManager] Live2D model loaded successfully:', modelPath);
            
            // 更新PerformanceManager中的能力状态
            this._updateCapabilityStates();
        } catch (error) {
            console.error('[Live2DManager] Failed to load Live2D model:', error);
            console.log('[Live2DManager] Falling back to 2D rendering');
            this.isFallback = true;
            
            // 更新PerformanceManager中的能力状态（模型不可用）
            this._updateCapabilityStates();
            
            this._createFallbackManager();
        }
    }
    
    /**
     * 更新PerformanceManager中的Live2D能力状态
     */
    _updateCapabilityStates() {
        if (!this.performanceManager) {
            return;
        }
        
        try {
            // 更新Live2D SDK状态
            this.performanceManager.updateCapability('live2d_sdk', this.isFramework && !this.isFallback);
            
            // 更新Live2D模型状态
            this.performanceManager.updateLive2DModelAvailability(this.modelLoaded && !this.isFallback);
            
            // 更新Live2D物理状态
            const physicsAvailable = this.isFramework && this.modelLoaded && !this.isFallback;
            this.performanceManager.updateLive2DPhysicsAvailability(physicsAvailable);
            
            // 更新Live2D唇型同步状态
            const lipsyncAvailable = this.isFramework && this.modelLoaded && !this.isFallback;
            this.performanceManager.updateLive2DLipsyncAvailability(lipsyncAvailable);
            
            console.log('[Live2DManager] 能力状态已更新:', {
                live2d_sdk: this.isFramework && !this.isFallback,
                live2d_model: this.modelLoaded && !this.isFallback,
                live2d_physics: physicsAvailable,
                live2d_lipsync: lipsyncAvailable
            });
        } catch (error) {
            console.error('[Live2DManager] 更新能力状态失败:', error);
        }
    }
    
    // ========== Fallback Rendering (只使用美术资源) ==========
    
    _createFallbackManager() {
        console.log('[Live2DManager] Creating 2D fallback manager');
        this._create2DFallbackCharacter();
    }
    
    async _create2DFallbackCharacter() {
        console.log('[Live2DManager] Creating 2D fallback character');
        
        const fallbackCanvas = document.getElementById('fallback-canvas');
        const ctx = fallbackCanvas?.getContext('2d');
        
        if (!fallbackCanvas || !ctx) {
            console.error('[Live2DManager] Fallback canvas not found');
            return;
        }
        
        this.fallbackCanvas = fallbackCanvas;
        this.fallbackCtx = ctx;
        
        fallbackCanvas.style.display = 'block';
        const wrapper = document.getElementById('fallback-wrapper');
        if (wrapper) {
            wrapper.classList.add('visible');
            this.fallbackWrapper = wrapper;
        }
        this.canvas.style.display = 'none';
        
        // Set canvas size
        if (this.udm) {
            const baseSize = this.udm.getBaseSize();
            fallbackCanvas.width = baseSize.width;
            fallbackCanvas.height = baseSize.height;
        } else {
            fallbackCanvas.width = 1280;
            fallbackCanvas.height = 720;
        }
        
        // 初始化 LayerRenderer（三層渲染系統）
        if (typeof window.LayerRenderer !== 'undefined') {
            this.layerRenderer = new window.LayerRenderer(fallbackCanvas, this.udm);
            console.log('[Live2DManager] LayerRenderer initialized');
        }
        
        // 加载美术资源
        await this._loadCharacterImage();
        
        // 如果 LayerRenderer 可用，將圖片加載到 LayerRenderer
        if (this.layerRenderer) {
            await this.layerRenderer.loadLayerImages(this.characterImages);
            console.log('[Live2DManager] Layer images loaded into LayerRenderer');
        }
        
        // 设置点击事件
        this._setupClickHandlers();
        
        // 初始化点击区域
        this._initTouchDetector();
        
        // 启动动画循环
        this._startAnimation();
    }
    
    _setupClickHandlers() {
        const wrapper = document.querySelector('.canvas-wrapper') || this.fallbackWrapper;
        if (wrapper) {
            // 保存事件监听器引用以便清理
            this._clickHandler = (e) => this._onClick(e);
            this._hoverHandler = (e) => this._onHover(e);
            this._wrapperElement = wrapper;
            
            wrapper.addEventListener('click', this._clickHandler);
            wrapper.addEventListener('mousemove', this._hoverHandler);
        }
    }
    
    async _loadCharacterImage() {
        // 從配置中加載所有立繪圖片
        if (typeof window.ANGELA_CHARACTER_IMAGES === 'undefined') {
            console.warn('[Live2DManager] ANGELA_CHARACTER_IMAGES not loaded, loading default only');
            await this._loadSingleImage('resources/angela_character_masked.png', 'default');
            return;
        }

        const config = window.ANGELA_CHARACTER_IMAGES;
        console.log('[Live2DManager] Loading character images from config...');
        
        // 嘗試加載所有配置的圖片
        for (const [imageId, imageConfig] of Object.entries(config)) {
            try {
                const img = new Image();
                img.src = `local://${imageConfig.path}`;
                
                await new Promise((resolve, reject) => {
                    img.onload = () => {
                        console.log(`[Live2DManager] Loaded image: ${imageId} (${img.width}x${img.height})`);
                        resolve(img);
                    };
                    img.onerror = () => reject(new Error('Failed'));
                });
                
                this.characterImages[imageId] = {
                    image: img,
                    config: imageConfig
                };
            } catch (e) {
                console.warn(`[Live2DManager] Could not load image: ${imageId}`, e.message);
            }
        }

        // 設置當前圖片（優先使用非默認的圖片）
        const availableIds = Object.keys(this.characterImages);
        if (availableIds.length > 1) {
            // 選擇第一個非默認的圖片
            for (const id of availableIds) {
                if (id !== 'default') {
                    this.currentCharacterImageId = id;
                    break;
                }
            }
        } else if (availableIds.length === 1) {
            this.currentCharacterImageId = availableIds[0];
        }

        // 如果當前選擇的圖片不可用，切換到可用的圖片
        if (!this.characterImages[this.currentCharacterImageId]) {
            const firstAvailable = availableIds[0];
            this.currentCharacterImageId = firstAvailable;
        }

        console.log('[Live2DManager] Current character image:', this.currentCharacterImageId);
    }

    async _loadSingleImage(path, imageId) {
        try {
            const img = new Image();
            img.src = `local://${path}`;
            
            await new Promise((resolve, reject) => {
                img.onload = () => resolve(img);
                img.onerror = () => reject(new Error('Failed'));
            });
            
            this.characterImages[imageId] = {
                image: img,
                config: {
                    name: imageId,
                    path: path,
                    type: 'single_image',
                    totalSize: { width: img.width, height: img.height },
                    renderParams: {
                        targetWidth: img.width,
                        targetHeight: img.height,
                        offsetX: 0,
                        offsetY: 0,
                        scaleX: 1.0,
                        scaleY: 1.0
                    }
                }
            };
            
            if (this.currentCharacterImageId === 'default') {
                this.currentCharacterImageId = imageId;
            }
            
            console.log('[Live2DManager] Character image loaded:', path);
        } catch (e) {
            console.warn('[Live2DManager] Could not load:', path, e.message);
        }
    }

    /**
     * 切換立繪圖片
     * @param {string} imageId - 圖片ID
     */
    setCharacterImage(imageId) {
        if (!this.characterImages[imageId]) {
            console.warn(`[Live2DManager] Image not found: ${imageId}`);
            return false;
        }

        this.currentCharacterImageId = imageId;
        console.log(`[Live2DManager] Switched to image: ${imageId}`);

        // 如果是 sprite sheet，重置索引
        const config = this.characterImages[imageId].config;
        if (config.type === 'sprite_sheet') {
            this.spriteSheetIndex = 0;
        }

        return true;
    }

    /**
     * 切換到下一張立繪
     */
    nextCharacterImage() {
        const availableIds = Object.keys(this.characterImages);
        if (availableIds.length <= 1) return false;

        const currentIndex = availableIds.indexOf(this.currentCharacterImageId);
        const nextIndex = (currentIndex + 1) % availableIds.length;
        return this.setCharacterImage(availableIds[nextIndex]);
    }

    /**
     * 切換到上一張立繪
     */
    previousCharacterImage() {
        const availableIds = Object.keys(this.characterImages);
        if (availableIds.length <= 1) return false;

        const currentIndex = availableIds.indexOf(this.currentCharacterImageId);
        const prevIndex = (currentIndex - 1 + availableIds.length) % availableIds.length;
        return this.setCharacterImage(availableIds[prevIndex]);
    }

    /**
     * 獲取當前可用的立繪列表
     */
    getAvailableCharacterImages() {
        return Object.keys(this.characterImages).map(id => ({
            id: id,
            name: this.characterImages[id]?.config?.name || id,
            type: this.characterImages[id]?.config?.type || 'unknown'
        }));
    }

    /**
     * 切換 Sprite Sheet 表情/姿態
     * @param {number} index - 表情/姿態索引
     */
    setSpriteSheetIndex(index) {
        const imageData = this.characterImages[this.currentCharacterImageId];
        if (!imageData || imageData.config.type !== 'sprite_sheet') {
            console.warn('[Live2DManager] Current image is not a sprite sheet');
            return false;
        }

        const config = imageData.config;
        const totalCells = config.grid.rows * config.cols;
        
        if (index < 0 || index >= totalCells) {
            console.warn(`[Live2DManager] Invalid index: ${index} (0-${totalCells-1})`);
            return false;
        }

        this.spriteSheetIndex = index;
        console.log(`[Live2DManager] Set sprite sheet index: ${index}`);

        return true;
    }

    /**
     * 下一個表情/姿態（適用於 sprite sheet）
     */
    nextSpriteSheetIndex() {
        const imageData = this.characterImages[this.currentCharacterImageId];
        if (!imageData || imageData.config.type !== 'sprite_sheet') {
            return false;
        }

        const config = imageData.config;
        const totalCells = config.grid.rows * config.cols;
        this.spriteSheetIndex = (this.spriteSheetIndex + 1) % totalCells;

        console.log(`[Live2DManager] Next sprite sheet index: ${this.spriteSheetIndex}`);
        return this.spriteSheetIndex;
    }

    /**
     * 獲取當前圖片的可用表情/姿態列表（適用於 sprite sheet）
     */
    getAvailableExpressions() {
        const imageData = this.characterImages[this.currentCharacterImageId];
        if (!imageData || imageData.config.type !== 'sprite_sheet') {
            return [];
        }

        const config = imageData.config;
        if (config.expressions) {
            return config.expressions;
        } else if (config.poses) {
            return config.poses;
        }

        return [];
    }

    /**
     * 切換到 fallback 模式（立繪模式）
     */
    async switchToFallback() {
        if (this.isFallback) {
            console.log('[Live2DManager] Already in fallback mode');
            return true;
        }

        console.log('[Live2DManager] Switching to fallback mode...');
        
        // 停止 Live2D
        if (this.wrapper) {
            try {
                this.wrapper.stop();
            } catch (e) {
                console.warn('[Live2DManager] Error stopping Live2D:', e);
            }
        }

        // 切換到 fallback 模式
        this.isFallback = true;
        this.modelLoaded = false;

        // 顯示 fallback canvas，隱藏 live2d canvas
        const fallbackCanvas = document.getElementById('fallback-canvas');
        const fallbackWrapper = document.getElementById('fallback-wrapper');
        if (fallbackCanvas) fallbackCanvas.style.display = 'block';
        if (fallbackWrapper) fallbackWrapper.classList.add('visible');
        this.canvas.style.display = 'none';

        // 如果還沒有創建 fallback manager，創建它
        if (!this.fallbackCanvas || !this.fallbackCtx) {
            await this._createFallbackManager();
        } else {
            // 啟動動畫循環
            if (!this.isRunning) {
                this._startAnimation();
            }
        }

        console.log('[Live2DManager] Switched to fallback mode');
        return true;
    }

    /**
     * 切換到 Live2D 模式
     */
    async switchToLive2D() {
        if (!this.isFallback) {
            console.log('[Live2DManager] Already in Live2D mode');
            return true;
        }

        console.log('[Live2DManager] Switching to Live2D mode...');

        // 停止 fallback 動畫
        this.isRunning = false;

        // 嘗試加載 Live2D 模型
        try {
            // 顯示 live2d canvas，隱藏 fallback canvas
            const fallbackCanvas = document.getElementById('fallback-canvas');
            const fallbackWrapper = document.getElementById('fallback-wrapper');
            if (fallbackCanvas) fallbackCanvas.style.display = 'none';
            if (fallbackWrapper) fallbackWrapper.classList.remove('visible');
            this.canvas.style.display = 'block';

            // 如果 wrapper 已經存在，重新啟動
            if (this.wrapper) {
                await this.wrapper.start();
            } else {
                // 否則重新加載模型
                await this._loadLive2DModel();
            }

            this.isFallback = false;
            this.modelLoaded = true;

            console.log('[Live2DManager] Switched to Live2D mode');
            return true;
        } catch (error) {
            console.error('[Live2DManager] Failed to switch to Live2D mode:', error);
            // 回退到 fallback 模式
            await this.switchToFallback();
            return false;
        }
    }

    /**
     * 獲取當前模式
     */
    getMode() {
        return this.isFallback ? 'fallback' : 'live2d';
    }

    _initTouchDetector() {
        // 使用 angela_character_config.json 中的区域定义
        this.clickableRegions = [
            { id: 'face', name: 'Face', x: 508, y: 26, width: 391, height: 150 },
            { id: 'eyes', name: 'Eyes', x: 550, y: 80, width: 150, height: 50 },
            { id: 'mouth', name: 'Mouth', x: 600, y: 160, width: 120, height: 60 },
            { id: 'neck', name: 'Neck', x: 620, y: 200, width: 100, height: 80 },
            { id: 'hair', name: 'Hair', x: 500, y: 30, width: 400, height: 200 }
        ];
    }
    
    _startAnimation() {
        if (this.isRunning) return;
        this.isRunning = true;
        this._animationLoop();
    }
    
    _animationLoop() {
        if (!this.isRunning) return;
        
        const now = performance.now();
        const deltaTime = now - this.lastFrameTime;
        this.lastFrameTime = now;
        
        // Calculate FPS
        this.currentFPS = 1000 / (deltaTime || 16.67);
        
        // Update fallback state
        this._updateBlink(deltaTime);
        this._updateBreathing(deltaTime);
        
        // Render
        this._renderFallback();
        
        requestAnimationFrame(() => this._animationLoop());
    }
    
    _renderFallback() {
        if (!this.fallbackCtx || !this.fallbackCanvas) return;
        
        // 如果 LayerRenderer 可用，使用三層渲染
        if (this.layerRenderer) {
            // 更新 LayerRenderer 的狀態
            this.layerRenderer.setExpressionIndex(this.expressionIndex);
            this.layerRenderer.setPoseIndex(this.poseIndex);
            
            // 渲染三層
            this.layerRenderer.render();
            return;
        }
        
        // 否則使用舊的單層渲染（降級方案）
        const ctx = this.fallbackCtx;
        const canvas = this.fallbackCanvas;
        
        // Clear
        ctx.fillStyle = '#1a1a1e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 繪制當前選擇的立繪
        const imageData = this.characterImages[this.currentCharacterImageId];
        if (!imageData) {
            console.warn('[Live2DManager] No character image loaded:', this.currentCharacterImageId);
            return;
        }

        const img = imageData.image;
        const config = imageData.config;
        const params = config.renderParams;
        const udmScale = this.udm ? this.udm.getResourceToBaseScale() : 1.0;

        if (config.type === 'single_image') {
            // 單張圖片渲染
            const imgWidth = img.width;
            const imgHeight = img.height;
            
            let renderWidth, renderHeight, renderX, renderY;
            
            if (params.scaleToHeight) {
                const scale = params.scaleToHeight / imgHeight;
                renderHeight = params.scaleToHeight * udmScale;
                renderWidth = imgWidth * scale * udmScale;
                
                if (renderWidth > canvas.width) {
                    const widthScale = canvas.width / renderWidth;
                    renderWidth = canvas.width;
                    renderHeight = renderHeight * widthScale;
                }
                
                renderX = (canvas.width - renderWidth) / 2;
                renderY = params.offsetY ? params.offsetY * udmScale : (canvas.height - renderHeight) / 2;
            } else {
                renderWidth = params.targetWidth * udmScale;
                renderHeight = params.targetHeight * udmScale;
                
                if (renderWidth > canvas.width) renderWidth = canvas.width;
                if (renderHeight > canvas.height) renderHeight = canvas.height;
                
                renderX = params.offsetX ? params.offsetX * udmScale : (canvas.width - renderWidth) / 2;
                renderY = params.offsetY ? params.offsetY * udmScale : (canvas.height - renderHeight) / 2;
            }
            
            ctx.drawImage(img, renderX, renderY, renderWidth, renderHeight);
            
            if (this.lastRenderedImageId !== this.currentCharacterImageId) {
                console.log('[Live2DManager] Rendered single image:', config.name, 
                            `size=${renderWidth.toFixed(0)}x${renderHeight.toFixed(0)}, pos=(${renderX.toFixed(0)}, ${renderY.toFixed(0)})`);
                this.lastRenderedImageId = this.currentCharacterImageId;
            }
        } else if (config.type === 'sprite_sheet') {
            // Sprite sheet 渲染
            const cellSize = config.cellSize;
            const totalSize = config.totalSize;
            const grid = config.grid;
            
            const colIndex = this.spriteSheetIndex % grid.cols;
            const rowIndex = Math.floor(this.spriteSheetIndex / grid.cols);
            
            const sourceX = colIndex * cellSize.width;
            const sourceY = rowIndex * cellSize.height;
            
            let renderWidth, renderHeight, renderX, renderY;
            
            if (params.scaleToHeight) {
                const scale = params.scaleToHeight / totalSize.height;
                renderHeight = params.scaleToHeight * udmScale;
                renderWidth = totalSize.width * scale * udmScale;
                
                if (renderWidth > canvas.width) {
                    const widthScale = canvas.width / renderWidth;
                    renderWidth = canvas.width;
                    renderHeight = renderHeight * widthScale;
                }
                
                const cellRenderWidth = renderWidth / grid.cols;
                const cellRenderHeight = renderHeight / grid.rows;
                
                renderX = (canvas.width - cellRenderWidth) / 2;
                renderY = (canvas.height - cellRenderHeight) / 2;
                
                ctx.drawImage(
                    img,
                    sourceX, sourceY,
                    cellSize.width, cellSize.height,
                    renderX, renderY,
                    cellRenderWidth, cellRenderHeight
                );
            } else {
                const cellRenderWidth = params.targetWidth * udmScale;
                const cellRenderHeight = params.targetHeight * udmScale;
                
                renderX = params.offsetX ? params.offsetX * udmScale : (canvas.width - cellRenderWidth) / 2;
                renderY = params.offsetY ? params.offsetY * udmScale : (canvas.height - cellRenderHeight) / 2;
                
                ctx.drawImage(
                    img,
                    sourceX, sourceY,
                    cellSize.width, cellSize.height,
                    renderX, renderY,
                    cellRenderWidth, cellRenderHeight
                );
            }
            
            if (this.lastRenderedImageId !== this.currentCharacterImageId || 
                this.lastRenderedSpriteIndex !== this.spriteSheetIndex) {
                console.log('[Live2DManager] Rendered sprite sheet cell:', config.name, 
                            `index=${this.spriteSheetIndex}, pos=(${colIndex}, ${rowIndex})`);
                this.lastRenderedImageId = this.currentCharacterImageId;
                this.lastRenderedSpriteIndex = this.spriteSheetIndex;
            }
        }
    }
    
    _updateBlink(deltaTime) {
        if (!this.fallbackState) {
            this.fallbackState = {
                blinkTimer: 0,
                blinkInterval: 2000 + Math.random() * 3000,
                isBlinking: false,
                eyeOpenness: 1
            };
        }
        
        this.fallbackState.blinkTimer += deltaTime;
        
        if (this.fallbackState.isBlinking) {
            this.fallbackState.eyeOpenness -= deltaTime / 100;
            if (this.fallbackState.eyeOpenness <= 0) {
                this.fallbackState.isBlinking = false;
                this.fallbackState.eyeOpenness = 1;
                this.fallbackState.blinkInterval = 2000 + Math.random() * 3000;
            }
        } else if (this.fallbackState.blinkTimer >= this.fallbackState.blinkInterval) {
            this.fallbackState.isBlinking = true;
            this.fallbackState.blinkTimer = 0;
        }
        
        this.parameters.ParamEyeLOpen = this.fallbackState.eyeOpenness;
        this.parameters.ParamEyeROpen = this.fallbackState.eyeOpenness;
    }
    
    _updateBreathing(deltaTime) {
        const time = performance.now() / 1000;
        this.parameters.ParamBreath = Math.sin(time * 2) * 0.1;
    }
    
    // ========== Event Handlers ==========
    
    _onClick(event) {
        if (!this.characterImage) return;
        
        const rect = event.currentTarget.getBoundingClientRect();
        const x = (event.clientX - rect.left) * (this.fallbackCanvas.width / rect.width);
        const y = (event.clientY - rect.top) * (this.fallbackCanvas.height / rect.height);
        
        const result = this._detectBodyPart(x, y);
        if (result && result.hit) {
            this._triggerReaction(result.bodyPart);
        }
    }
    
    _onHover(event) {
        if (!this.characterImage) return;
        
        const rect = event.currentTarget.getBoundingClientRect();
        const x = (event.clientX - rect.left) * (this.fallbackCanvas.width / rect.width);
        const y = (event.clientY - rect.top) * (this.fallbackCanvas.height / rect.height);
        this._updateHoverState(x, y);
    }
    
    _detectBodyPart(x, y) {
        const scale = this.udm ? this.udm.getResourceToBaseScale() : 1.0;
        
        for (const region of this.clickableRegions) {
            const rx = region.x * scale;
            const ry = region.y * scale;
            const rw = region.width * scale;
            const rh = region.height * scale;
            
            if (x >= rx && x <= rx + rw && y >= ry && y <= ry + rh) {
                return { bodyPart: region.id, confidence: 0.8, hit: true };
            }
        }
        
        // Check character bbox
        const bbox = { x: 508, y: 26, width: 391, height: 491 };
        if (x >= bbox.x * scale && x < (bbox.x + bbox.width) * scale &&
            y >= bbox.y * scale && y < (bbox.y + bbox.height) * scale) {
            return { bodyPart: 'generic', confidence: 0.5, hit: true };
        }
        
        return { hit: false };
    }
    
    _updateHoverState(x, y) {
        if (!this.fallbackState) return;
        const result = this._detectBodyPart(x, y);
        if (result && result.bodyPart !== this.fallbackState?.hoverRegion) {
            this.fallbackState.hoverRegion = result.bodyPart;
        }
    }
    
    _triggerReaction(bodyPart) {
        const reactions = {
            'face': 'happy', 'eyes': 'surprised', 'mouth': 'happy',
            'neck': 'shy', 'hair': 'neutral', 'generic': 'neutral'
        };
        this.setExpression(reactions[bodyPart] || 'neutral');
    }
    
    handleCharacterInteraction(x, y) {
        return this._detectBodyPart(x, y);
    }
    
    // ========== Public API ==========
    
    // Expression control
    setExpression(expression) {
        try {
            if (this.expressions[expression]) {
                this.currentExpression = expression;
                console.log(`[Live2DManager] Expression: ${expression}`);
            } else {
                console.warn(`[Live2DManager] Unknown expression: ${expression}, available:`, Object.keys(this.expressions));
                // 回退到neutral表情
                if (this.expressions['neutral']) {
                    this.currentExpression = 'neutral';
                }
            }
        } catch (error) {
            console.error('[Live2DManager] Failed to set expression:', error, 'expression:', expression);
            // 尝试回退到neutral
            if (this.expressions && this.expressions['neutral']) {
                try {
                    this.currentExpression = 'neutral';
                } catch (fallbackError) {
                    console.error('[Live2DManager] Fallback to neutral also failed:', fallbackError);
                }
            }
        }
    }
    
    // Motion control
    startMotion(motion) {
        this.currentMotion = motion;
        console.log(`[Live2DManager] Motion: ${motion}`);
    }
    
    async playMotion(category, motion) {
        console.log(`[Live2DManager] Play motion: ${category}/${motion}`);
        return true;
    }
    
    // Parameter control
    setParameter(param, value) {
        this.parameters[param] = value;
    }
    
    getParameter(param) {
        return this.parameters[param] || 0;
    }
    
    /**
     * 设置PerformanceManager引用
     * @param {PerformanceManager} pm - PerformanceManager实例
     */
    setPerformanceManager(pm) {
        this.performanceManager = pm;
        console.log('[Live2DManager] PerformanceManager已设置:', !!pm);
        
        // 如果模型已加载，立即更新能力状态
        if (this.modelLoaded || this.isFallback) {
            this._updateCapabilityStates();
        }
    }
    
    // Eye tracking
    lookAt(normalizedX, normalizedY) {
        this.eyeTracking.x = normalizedX;
        this.eyeTracking.y = normalizedY;
    }
    
    updateEyeTracking(x, y) {
        this.eyeTracking.x = x;
        this.eyeTracking.y = y;
    }
    
    // Lip sync
    updateLipSync(level, strength = 0.8) {
        this.lipSync.level = level;
        this.parameters.ParamMouthOpenY = level * strength;
    }
    
    // Clickable regions
    getClickableRegions() {
        return this.clickableRegions;
    }
    
    updateRegions() {
        this._initTouchDetector();
    }
    
    // ========== Performance Methods (required by PerformanceManager) ==========
    
    setResolutionScale(scale) {
        this.resolutionScale = scale;
    }
    
    setEffectsLevel(level) {
        this.effectsLevel = level;
    }
    
    setAdvancedAnimations(enabled) {
        this.features.advanced_animations = enabled;
    }
    
    setPhysics(enabled) {
        this.features.physics = enabled;
    }
    
    setLipSync(enabled) {
        this.features.lip_sync = enabled;
    }
    
    setTargetFPS(fps) {
        this.targetFPS = fps;
    }
    
    getCurrentFPS() {
        return this.currentFPS;
    }
    
    setFrameRate(fps) {
        this.frameRate = fps;
    }
    
    setRenderQuality(quality) {
        console.log(`[Live2DManager] Render quality: ${quality}`);
    }
    
    setEffects(effects) {
        this.effects = { ...this.effects, ...effects };
    }
    
    getEffects() {
        return { ...this.effects };
    }
    
    setFrameRateConfig(config) {
        this.frameRate = config.targetFPS || 60;
    }
    
    // Lifecycle
    stop() {
        this.isRunning = false;
    }
    
    destroy() {
        this.isRunning = false;
        
        // 停止动画循环
        this._stopAnimation();
        
        // 清理事件监听器
        if (this._wrapperElement) {
            if (this._clickHandler) {
                this._wrapperElement.removeEventListener('click', this._clickHandler);
            }
            if (this._hoverHandler) {
                this._wrapperElement.removeEventListener('mousemove', this._hoverHandler);
            }
        }
        
        // 清理引用
        this._clickHandler = null;
        this._hoverHandler = null;
        this._wrapperElement = null;
        this.characterImage = null;
    }
    
    enableDebugOverlay(enable = true) {
        this.showDebugOverlay = enable;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DManager;
}