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
        
        // Fallback rendering - 只使用美术资源
        this.fallbackCanvas = null;
        this.fallbackCtx = null;
        this.fallbackWrapper = null;
        this.characterImage = null;  // 只加载美术资源
        
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
            await this.wrapper.startRendering();
            
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
        
        // 加载美术资源
        await this._loadCharacterImage();
        
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
            wrapper.addEventListener('click', (e) => this._onClick(e));
            wrapper.addEventListener('mousemove', (e) => this._onHover(e));
        }
    }
    
    async _loadCharacterImage() {
        // 只加载美术资源，不生成占位图
        // 使用 local:// 协议加载
        const imagePaths = [
            'local://models/miara_pro_en/runtime/angela_character_masked.png',
            'local://resources/angela_character_masked.png',
            'models/miara_pro_en/runtime/angela_character_masked.png',
            'resources/angela_character_masked.png'
        ];
        
        for (const path of imagePaths) {
            try {
                const img = new Image();
                img.src = path;
                await new Promise((resolve, reject) => {
                    img.onload = () => resolve(img);
                    img.onerror = () => reject(new Error('Failed'));
                });
                this.characterImage = img;
                console.log('[Live2DManager] Character image loaded:', path);
                return;
            } catch (e) {
                console.warn('[Live2DManager] Could not load:', path);
            }
        }
        
        console.log('[Live2DManager] No character image found');
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
        
        const ctx = this.fallbackCtx;
        const canvas = this.fallbackCanvas;
        
        // Clear
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 只绘制美术资源，没有就不绘制
        if (this.characterImage) {
            const scale = this.udm ? this.udm.getResourceToBaseScale() : 1.0;
            ctx.drawImage(
                this.characterImage,
                508 * scale, 26 * scale,
                391 * scale, 491 * scale
            );
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