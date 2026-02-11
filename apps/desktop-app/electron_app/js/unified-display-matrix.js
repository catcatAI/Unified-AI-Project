/**
 * Angela AI - Unified Display Matrix (UDM)
 * 
 * 统一显示矩阵系统 - 720p (1280×720) = 100% 基准
 * 
 * 职责划分:
 * ┌─────────────────────────────────────────────────────────────────┐
 * │                     UDM 与 Angela 系统连接                         │
 ├─────────────────────────────────────────────────────────────────┤
 │                                                                 │
 │  UDM (本文件) - 显示层                                             │
 │  ├── 坐标转换: screen ↔ canvas ↔ resource                        │
 │  ├── 显示缩放: 50%-300% 用户缩放                                 │
 │  ├── 资源精度: 720p/1080p/2K/4K/8K                              │
 │  └── 触觉强度: baseIntensity × touchAreaRatio × dpiRatio          │
 │                                                                 │
 │  StateMatrix4D (state-matrix.js) - 情感层                          │
 │  ├── α (生理): energy, comfort, arousal, vitality                │
 │  ├── β (认知): curiosity, focus, clarity, creativity              │
 │  ├── γ (情感): happiness, calm, love, trust                       │
 │  └── δ (社交): attention, bond, intimacy, engagement             │
 │                                                                 │
 │  触摸事件流程:                                                   │
 │  1. UDM.screenToResource() → 获取资源坐标                         │
 │  2. UDM.identifyBodyPart() → 识别人体区域                         │
 │  3. UDM.calculateHapticIntensity() → 计算触觉强度                 │
 │  4. StateMatrix4D.handleInteraction('touch', data) → 更新情感    │
 │  5. Live2DManager.setExpression() → 触发表情                      │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
 */

class UnifiedDisplayMatrix {
    constructor(options = {}) {
        // ============================================================
        // 基础配置 (720p = 100%)
        // ============================================================
        this.baseConfig = {
            // 720p 基准尺寸 (100%)
            baseWidth: 1280,
            baseHeight: 720,
            
            // 缩放范围
            minUserScale: 0.5,
            maxUserScale: 3.0,
            defaultUserScale: 1.0,
            
            // 缩放步长
            scaleStep: 0.25,
        };

        // ============================================================
        // 资源精度矩阵 (Resource Precision Matrix)
        // ============================================================
        this.resourceMatrix = {
            '720p':  { width: 1280, height: 720,  scale: 1.0,  name: '720p (HD)' },
            '1080p': { width: 1920, height: 1080, scale: 1.5,  name: '1080p (FHD)' },
            '2k':    { width: 2560, height: 1440, scale: 1.78, name: '2K (QHD)' },
            '4k':    { width: 3840, height: 2160, scale: 3.0,  name: '4K (UHD)' },
            '8k':    { width: 7680, height: 4320, scale: 6.0,  name: '8K (FUHD)' }
        };

        // ============================================================
        // 显示缩放矩阵 (Display Scale Matrix)
        // ============================================================
        this.displayMatrix = {
            '50%':   { scale: 0.5,  name: '50%' },
            '75%':   { scale: 0.75, name: '75%' },
            '100%':  { scale: 1.0,  name: '100% (默认)' },
            '125%':  { scale: 1.25, name: '125%' },
            '150%':  { scale: 1.5,  name: '150%' },
            '200%':  { scale: 2.0,  name: '200%' },
            '250%':  { scale: 2.5,  name: '250%' },
            '300%':  { scale: 3.0,  name: '300%' }
        };

        // ============================================================
        // 当前状态
        // ============================================================
        this.currentState = {
            userScale: this.baseConfig.defaultUserScale,
            resourcePrecision: '720p',
            baseWidth: this.resourceMatrix['720p'].width,
            baseHeight: this.resourceMatrix['720p'].height,
            windowWidth: 0,
            windowHeight: 0,
            devicePixelRatio: window.devicePixelRatio || 1.0
        };

        // ============================================================
        // DOM 元素
        // ============================================================
        this.wrapperElement = null;
        this.canvasElement = null;
        this.touchDetector = null;
        this.isInitialized = false;

        // ============================================================
        // Angela 系统连接
        // ============================================================
        this.angelaSystem = {
            stateMatrix: null,
            live2DManager: null,
            hapticHandler: null
        };

        // ============================================================
        // 监听器
        // ============================================================
        this.listeners = {
            scaleChange: [],
            precisionChange: [],
            resize: [],
            touch: []  // 触摸事件监听器
        };

        console.log('[UDM] UnifiedDisplayMatrix initialized (720p=100%)');
    }

    // ================================================================
    // Angela 系统连接接口
    // ================================================================

    /**
     * 连接 Angela 系统组件
     * @param {Object} components - { stateMatrix, live2DManager, hapticHandler }
     */
    connectAngelaSystem(components) {
        this.angelaSystem.stateMatrix = components.stateMatrix || null;
        this.angelaSystem.live2DManager = components.live2DManager || null;
        this.angelaSystem.hapticHandler = components.hapticHandler || null;

        if (this.angelaSystem.stateMatrix) {
            console.log('[UDM] Connected to StateMatrix4D');
        }
        if (this.angelaSystem.live2DManager) {
            console.log('[UDM] Connected to Live2DManager');
        }
        if (this.angelaSystem.hapticHandler) {
            console.log('[UDM] Connected to HapticHandler');
        }

        return this;
    }

    /**
     * 处理触摸事件 - 完整的 Angela 交互流程
     * 
     * 使用方法:
     *   udm.handleTouch(screenX, screenY, touchType);
     * 
     * 内部流程:
     *   1. 坐标转换: screen → canvas → resource
     *   2. 识别人体区域
     *   3. 计算触觉强度
     *   4. 更新 StateMatrix4D
     *   5. 触发 Live2D 表情
     * 
     * @param {number} screenX - 屏幕 X 坐标
     * @param {number} screenY - 屏幕 Y 坐标
     * @param {string} touchType - 触摸类型 ('pat', 'poke', 'stroke')
     * @returns {object} - 触摸结果
     */
    handleTouch(screenX, screenY, touchType = 'pat') {
        const result = {
            success: false,
            coordinates: null,
            bodyPart: null,
            hapticIntensity: 0,
            stateUpdate: null,
            expression: null,
            errors: []
        };

        try {
            // 1. 坐标转换: screen → canvas → resource
            let canvasCoords, resourceCoords;
            try {
                canvasCoords = this.screenToCanvas(screenX, screenY);
                resourceCoords = this.canvasToResource(canvasCoords.x, canvasCoords.y);
                
                result.coordinates = {
                    screen: { x: screenX, y: screenY },
                    canvas: canvasCoords,
                    resource: resourceCoords
                };
            } catch (coordError) {
                console.error('[UDM] 坐标转换失败:', coordError);
                result.errors.push({
                    step: 'coordinate_conversion',
                    error: coordError.message
                });
                return result;
            }

            // 2. 识别人体区域
            let bodyPart;
            try {
                bodyPart = this.identifyBodyPart(resourceCoords.x, resourceCoords.y);
                result.bodyPart = bodyPart;
            } catch (detectError) {
                console.error('[UDM] 人体区域识别失败:', detectError);
                result.errors.push({
                    step: 'body_part_detection',
                    error: detectError.message
                });
                return result;
            }

            if (!bodyPart) {
                console.log('[UDM] No body part detected at:', resourceCoords);
                return result;
            }

            // 3. 计算触觉强度
            let hapticIntensity = 0;
            try {
                hapticIntensity = this.calculateHapticIntensity(0.8, canvasCoords, { width: 20, height: 20 });
                result.hapticIntensity = hapticIntensity;
            } catch (hapticError) {
                console.warn('[UDM] 触觉强度计算失败，使用默认值:', hapticError);
                result.errors.push({
                    step: 'haptic_intensity',
                    error: hapticError.message
                });
                hapticIntensity = 0.5; // 使用默认值
            }

            // 4. 更新 StateMatrix4D (如果已连接)
            if (this.angelaSystem && this.angelaSystem.stateMatrix) {
                try {
                    const stateData = {
                        type: touchType,
                        part: bodyPart.name,
                        intensity: hapticIntensity,
                        position: canvasCoords
                    };

                    this.angelaSystem.stateMatrix.handleInteraction('touch', stateData);
                    result.stateUpdate = {
                        updated: true,
                        dimension: 'alpha+delta+gamma',
                        emotions: {
                            comfort: '+0.1',
                            intimacy: '+0.15',
                            calm: '+0.1'
                        }
                    };
                } catch (stateError) {
                    console.error('[UDM] 状态矩阵更新失败:', stateError);
                    result.errors.push({
                        step: 'state_matrix_update',
                        error: stateError.message
                    });
                }
            }

            // 5. 触发触觉反馈 (如果已连接)
            if (this.angelaSystem && this.angelaSystem.hapticHandler && hapticIntensity > 0.1) {
                try {
                    this.angelaSystem.hapticHandler.triggerHaptic(hapticIntensity, touchType);
                } catch (hapticTriggerError) {
                    console.warn('[UDM] 触觉反馈触发失败:', hapticTriggerError);
                    result.errors.push({
                        step: 'haptic_feedback',
                        error: hapticTriggerError.message
                    });
                }
            }

            // 6. 触发 Live2D 表情 (如果已连接)
            if (this.angelaSystem && this.angelaSystem.live2DManager && bodyPart.expression) {
                try {
                    this.angelaSystem.live2DManager.setExpression(bodyPart.expression);
                    result.expression = bodyPart.expression;
                } catch (expressionError) {
                    console.warn('[UDM] Live2D表情设置失败:', expressionError);
                    result.errors.push({
                        step: 'live2d_expression',
                        error: expressionError.message
                    });
                }
            }

            // 7. 通知触摸监听器
            try {
                this._notifyListeners('touch', {
                    type: touchType,
                    bodyPart: bodyPart,
                    intensity: hapticIntensity,
                    coordinates: result.coordinates
                });
            } catch (notifyError) {
                console.warn('[UDM] 触摸监听器通知失败:', notifyError);
                result.errors.push({
                    step: 'notify_listeners',
                    error: notifyError.message
                });
            }

            result.success = result.errors.length === 0 || result.errors.every(e => 
                e.step === 'haptic_feedback' || e.step === 'live2d_expression' || e.step === 'notify_listeners'
            );
            
            if (result.success) {
                console.log('[UDM] Touch handled:', touchType, bodyPart.name, 'intensity:', hapticIntensity.toFixed(2));
            } else if (result.errors.length > 0) {
                console.warn('[UDM] Touch handled with errors:', result.errors);
            }

        } catch (globalError) {
            console.error('[UDM] 触摸处理全局错误:', globalError);
            result.errors.push({
                step: 'global',
                error: globalError.message
            });
        }

        return result;
    }

    /**
     * 处理点击事件
     */
    handleClick(screenX, screenY) {
        try {
            const result = this.handleTouch(screenX, screenY, 'pat');

            if (this.angelaSystem && this.angelaSystem.stateMatrix && result.bodyPart) {
                try {
                    this.angelaSystem.stateMatrix.handleInteraction('click', {
                        part: result.bodyPart.name
                    });
                } catch (clickStateError) {
                    console.error('[UDM] 点击状态更新失败:', clickStateError);
                    if (!result.errors) result.errors = [];
                    result.errors.push({
                        step: 'click_state_update',
                        error: clickStateError.message
                    });
                }
            }

            return result;
        } catch (clickError) {
            console.error('[UDM] 点击处理全局错误:', clickError);
            return {
                success: false,
                coordinates: { screen: { x: screenX, y: screenY } },
                bodyPart: null,
                hapticIntensity: 0,
                stateUpdate: null,
                expression: null,
                errors: [{ step: 'global', error: clickError.message }]
            };
        }
    }

    // ================================================================
    // 初始化
    // ================================================================

    initialize(wrapperElement, canvasElement) {
        this.wrapperElement = wrapperElement;
        this.canvasElement = canvasElement;

        this._updateWindowSize();
        this._updateBaseSize();
        this._applyDisplayScale();
        this._bindWindowResize();

        this.isInitialized = true;
        
        console.log('[UDM] Initialized:', {
            baseSize: `${this.currentState.baseWidth}x${this.currentState.baseHeight}`,
            userScale: `${(this.currentState.userScale * 100).toFixed(0)}%`
        });

        return this;
    }

    // ================================================================
    // 资源精度控制
    // ================================================================

    setResourcePrecision(precision) {
        if (!this.resourceMatrix[precision]) {
            console.warn('[UDM] Unknown precision:', precision);
            return false;
        }

        const oldPrecision = this.currentState.resourcePrecision;
        this.currentState.resourcePrecision = precision;
        this._updateBaseSize();

        this._notifyListeners('precisionChange', {
            oldPrecision,
            newPrecision: precision,
            baseWidth: this.currentState.baseWidth,
            baseHeight: this.currentState.baseHeight
        });

        console.log('[UDM] Resource precision:', oldPrecision, '→', precision);
        return true;
    }

    getResourcePrecision() {
        return this.currentState.resourcePrecision;
    }

    getResourceToBaseScale() {
        const resource = this.resourceMatrix[this.currentState.resourcePrecision];
        return this.currentState.baseWidth / resource.width;
    }

    getAvailablePrecisions() {
        return Object.entries(this.resourceMatrix).map(([key, value]) => ({ key, ...value }));
    }

    _updateBaseSize() {
        const precision = this.resourceMatrix[this.currentState.resourcePrecision];
        this.currentState.baseWidth = precision.width;
        this.currentState.baseHeight = precision.height;
    }

    // ================================================================
    // 用户缩放控制
    // ================================================================

    setUserScale(scale) {
        const clampedScale = Math.max(
            this.baseConfig.minUserScale,
            Math.min(this.baseConfig.maxUserScale, scale)
        );

        if (clampedScale !== this.currentState.userScale) {
            const oldScale = this.currentState.userScale;
            this.currentState.userScale = clampedScale;
            this._applyDisplayScale();

            this._notifyListeners('scaleChange', {
                oldScale,
                newScale: clampedScale,
                displayWidth: this.getDisplayWidth(),
                displayHeight: this.getDisplayHeight()
            });

            console.log('[UDM] Scale:', `${(oldScale * 100).toFixed(0)}% → ${(clampedScale * 100).toFixed(0)}%`);
        }
    }

    getUserScale() {
        return this.currentState.userScale;
    }

    increaseUserScale(delta = null) {
        this.setUserScale(this.currentState.userScale + (delta || this.baseConfig.scaleStep));
    }

    decreaseUserScale(delta = null) {
        this.setUserScale(this.currentState.userScale - (delta || this.baseConfig.scaleStep));
    }

    resetUserScale() {
        this.setUserScale(this.baseConfig.defaultUserScale);
    }

    // ================================================================
    // 显示尺寸计算
    // ================================================================

    getDisplayWidth() {
        return this.currentState.baseWidth * this.currentState.userScale;
    }

    getDisplayHeight() {
        return this.currentState.baseHeight * this.currentState.userScale;
    }

        getDisplaySize() {
            return {
                width: this.getDisplayWidth(),
                height: this.getDisplayHeight(),
                scale: this.currentState.userScale
            };
        }
        
        // 基准尺寸方法 (供 Live2DManager 使用)
        getBaseSize() {
            return {
                width: this.currentState.baseWidth,
                height: this.currentState.baseHeight
            };
        }
        
        getBaseWidth() {
            return this.currentState.baseWidth;
        }
        
        getBaseHeight() {
            return this.currentState.baseHeight;
        }
        
        _applyDisplayScale() {        if (!this.wrapperElement) return;

        const displayWidth = this.getDisplayWidth();
        const displayHeight = this.getDisplayHeight();

        this.wrapperElement.style.width = `${displayWidth}px`;
        this.wrapperElement.style.height = `${displayHeight}px`;

        if (this.canvasElement) {
            this.canvasElement.width = this.currentState.baseWidth;
            this.canvasElement.height = this.currentState.baseHeight;
        }
    }

    // ================================================================
    // 坐标转换矩阵
    // ================================================================

    /**
     * 屏幕坐标 → 画布坐标
     * 
     * 公式:
     * canvasX = (screenX - wrapperLeft) / displayWidth × baseWidth
     * canvasY = (screenY - wrapperTop)  / displayHeight × baseHeight
     */
    screenToCanvas(screenX, screenY) {
        if (!this.wrapperElement || !this.canvasElement) {
            return { x: screenX, y: screenY };
        }

        const rect = this.wrapperElement.getBoundingClientRect();
        const displayWidth = rect.width;
        const displayHeight = rect.height;
        const baseWidth = this.currentState.baseWidth;
        const baseHeight = this.currentState.baseHeight;

        const canvasX = ((screenX - rect.left) / displayWidth) * baseWidth;
        const canvasY = ((screenY - rect.top) / displayHeight) * baseHeight;

        return { x: canvasX, y: canvasY };
    }

    /**
     * 画布坐标 → 屏幕坐标
     */
    canvasToScreen(canvasX, canvasY) {
        if (!this.wrapperElement) {
            return { x: canvasX, y: canvasY };
        }

        const rect = this.wrapperElement.getBoundingClientRect();
        const displayWidth = rect.width;
        const displayHeight = rect.height;
        const baseWidth = this.currentState.baseWidth;
        const baseHeight = this.currentState.baseHeight;

        const screenX = rect.left + (canvasX / baseWidth) * displayWidth;
        const screenY = rect.top + (canvasY / baseHeight) * displayHeight;

        return { x: screenX, y: screenY };
    }

    /**
     * 画布坐标 → 原始资源坐标
     * 
     * 公式:
     * resourceX = canvasX × (resourceWidth / baseWidth)
     * resourceY = canvasY × (resourceHeight / baseHeight)
     */
    canvasToResource(canvasX, canvasY) {
        const precision = this.resourceMatrix[this.currentState.resourcePrecision];
        const baseWidth = this.currentState.baseWidth;
        const baseHeight = this.currentState.baseHeight;

        const resourceX = canvasX * (precision.width / baseWidth);
        const resourceY = canvasY * (precision.height / baseHeight);

        return { x: resourceX, y: resourceY };
    }

    /**
     * 原始资源坐标 → 画布坐标
     */
    resourceToCanvas(resourceX, resourceY) {
        const precision = this.resourceMatrix[this.currentState.resourcePrecision];
        const baseWidth = this.currentState.baseWidth;
        const baseHeight = this.currentState.baseHeight;

        const canvasX = resourceX * (baseWidth / precision.width);
        const canvasY = resourceY * (baseHeight / precision.height);

        return { x: canvasX, y: canvasY };
    }

    /**
     * 屏幕坐标 → 原始资源坐标
     */
    screenToResource(screenX, screenY) {
        const canvasCoords = this.screenToCanvas(screenX, screenY);
        return this.canvasToResource(canvasCoords.x, canvasCoords.y);
    }

    /**
     * 原始资源坐标 → 屏幕坐标
     */
    resourceToScreen(resourceX, resourceY) {
        const canvasCoords = this.resourceToCanvas(resourceX, resourceY);
        return this.canvasToScreen(canvasCoords.x, canvasCoords.y);
    }

    // ================================================================
    // 人体区域识别 (与 angela_character_config 配合)
    // ================================================================

    /**
     * 识别人体区域
     * 
     * 使用方法:
     *   const part = udm.identifyBodyPart(resourceX, resourceY);
     *   // part = { name: 'face', description: '臉部', priority: 1, expression: 'blush', ... }
     * 
     * @param {number} resourceX - 原始资源 X 坐标
     * @param {number} resourceY - 原始资源 Y 坐标
     * @returns {object|null} - 区域信息或 null
     */
    identifyBodyPart(resourceX, resourceY) {
        // 人体区域配置 (与 angela_character_config.json 对应)
        // 注意: 这些坐标是针对原始资源 (1408x768) 的
        // 需要根据当前精度进行转换
        const bodyZones = this._getBodyZones();

        for (const zone of bodyZones) {
            if (this._isInZone(resourceX, resourceY, zone.rect)) {
                return {
                    name: zone.name,
                    description: zone.description,
                    priority: zone.priority,
                    paramId: zone.param_id,
                    expression: zone.expression,
                    tactileType: zone.tactile_type,
                    rect: zone.rect
                };
            }
        }

        return null;
    }

    _getBodyZones() {
        // 默认人体区域 (基于 angela_character_config.json)
        // 这些坐标是 720p 基准 (1280x720)
        // 原始资源配置是 1408x768，需要按比例转换
        const originalTo720p = (x, y) => ({
            x: x * 1280 / 1408,
            y: y * 720 / 768
        });

        const face = originalTo720p(630, 71, 777, 156);
        const eyes = originalTo720p(660, 99, 748, 117);
        const mouth = originalTo720p(682, 124, 726, 135);

        return [
            {
                name: 'face',
                rect: [face.x, face.y, 777 * 1280 / 1408, 156 * 720 / 768],
                description: '臉部',
                priority: 1,
                param_id: 'PARAM_CHEEK',
                expression: 'blush',
                tactile_type: 'pat'
            },
            {
                name: 'eyes',
                rect: [eyes.x, eyes.y, 748 * 1280 / 1408, 117 * 720 / 768],
                description: '眼睛',
                priority: 1,
                param_id: 'PARAM_EYE_OPEN',
                expression: 'wink',
                tactile_type: 'poke'
            },
            {
                name: 'mouth',
                rect: [mouth.x, mouth.y, 726 * 1280 / 1408, 135 * 720 / 768],
                description: '嘴巴',
                priority: 1,
                param_id: 'PARAM_MOUTH_OPEN',
                expression: 'smile',
                tactile_type: 'poke'
            }
        ];
    }

    _isInZone(x, y, rect) {
        return x >= rect[0] && x <= rect[2] && y >= rect[1] && y <= rect[3];
    }

    // ================================================================
    // 触觉强度计算 (Haptic Intensity Matrix)
    // ================================================================

    /**
     * 计算触觉强度
     * 
     * 公式:
     * intensity = baseIntensity × touchAreaRatio × dpiRatio
     * 
     * 关键: 强度不随显示器分辨率变化，保证物理触感一致
     * 
     * @param {number} baseIntensity - 基础强度 (0-1)
     * @param {object} touchPosition - 触摸位置 (画布坐标)
     * @param {object} touchSize - 触摸区域大小 (像素)
     * @returns {number} - 调整后的触觉强度 (0-1)
     */
    calculateHapticIntensity(baseIntensity, touchPosition = null, touchSize = null) {
        // 基准触摸区域 (100% 缩放下的 40×40 像素)
        const baseTouchArea = 40 * 40;

        // 触摸区域比例 (0.5 - 2.0)
        let touchAreaRatio = 1.0;
        if (touchSize) {
            const currentTouchArea = touchSize.width * touchSize.height;
            touchAreaRatio = Math.max(0.5, Math.min(2.0, currentTouchArea / baseTouchArea));
        }

        // DPI 调整因子 (保证物理触感一致)
        const dpiRatio = this.currentState.devicePixelRatio;

        // 缩放调整因子
        const scaleRatio = this.currentState.userScale;

        // 综合计算
        const adjustedIntensity = baseIntensity * touchAreaRatio * dpiRatio * Math.sqrt(scaleRatio);

        // 限制在合理范围
        return Math.max(0.1, Math.min(1.0, adjustedIntensity));
    }

    // ================================================================
    // 窗口管理
    // ================================================================

    _updateWindowSize() {
        this.currentState.windowWidth = window.innerWidth;
        this.currentState.windowHeight = window.innerHeight;
        this.currentState.devicePixelRatio = window.devicePixelRatio || 1.0;
    }

    _bindWindowResize() {
        window.addEventListener('resize', () => {
            const oldWidth = this.currentState.windowWidth;
            const oldHeight = this.currentState.windowHeight;

            this._updateWindowSize();

            this._notifyListeners('resize', {
                oldWidth, oldHeight,
                newWidth: this.currentState.windowWidth,
                newHeight: this.currentState.windowHeight,
                devicePixelRatio: this.currentState.devicePixelRatio
            });
        });
    }

    // ================================================================
    // 监听器管理
    // ================================================================

    onScaleChange(callback) {
        this.listeners.scaleChange.push(callback);
    }

    onPrecisionChange(callback) {
        this.listeners.precisionChange.push(callback);
    }

    onResize(callback) {
        this.listeners.resize.push(callback);
    }

    onTouch(callback) {
        this.listeners.touch.push(callback);
    }

    _notifyListeners(event, data) {
        const callbacks = this.listeners[event] || [];
        for (const callback of callbacks) {
            try {
                callback(data);
            } catch (e) {
                console.error('[UDM] Listener error:', e);
            }
        }
    }

    // ================================================================
    // 工具方法
    // ================================================================

    getStatus() {
        const precision = this.resourceMatrix[this.currentState.resourcePrecision];

        return {
            baseSize: {
                width: this.currentState.baseWidth,
                height: this.currentState.baseHeight
            },
            displaySize: this.getDisplaySize(),
            userScale: this.currentState.userScale,
            userScalePercent: `${(this.currentState.userScale * 100).toFixed(0)}%`,
            resourcePrecision: this.currentState.resourcePrecision,
            resourceScale: precision.scale,
            windowSize: {
                width: this.currentState.windowWidth,
                height: this.currentState.windowHeight
            },
            devicePixelRatio: this.currentState.devicePixelRatio,
            angelaConnected: {
                stateMatrix: !!this.angelaSystem.stateMatrix,
                live2DManager: !!this.angelaSystem.live2DManager,
                hapticHandler: !!this.angelaSystem.hapticHandler
            }
        };
    }

    getTransformMatrix(from, to) {
        const matrices = {
            'screen→canvas': {
                scaleX: this.currentState.baseWidth / this.getDisplayWidth(),
                scaleY: this.currentState.baseHeight / this.getDisplayHeight()
            },
            'canvas→screen': {
                scaleX: this.getDisplayWidth() / this.currentState.baseWidth,
                scaleY: this.getDisplayHeight() / this.currentState.baseHeight
            },
            'canvas→resource': {
                scaleX: this.resourceMatrix[this.currentState.resourcePrecision].width / this.currentState.baseWidth,
                scaleY: this.resourceMatrix[this.currentState.resourcePrecision].height / this.currentState.baseHeight
            },
            'resource→canvas': {
                scaleX: this.currentState.baseWidth / this.resourceMatrix[this.currentState.resourcePrecision].width,
                scaleY: this.currentState.baseHeight / this.resourceMatrix[this.currentState.resourcePrecision].height
            }
        };

        return matrices[`${from}→${to}`] || null;
    }

    destroy() {
        this.wrapperElement = null;
        this.canvasElement = null;
        this.angelaSystem = { stateMatrix: null, live2DManager: null, hapticHandler: null };
        this.listeners = { scaleChange: [], precisionChange: [], resize: [], touch: [] };
        this.isInitialized = false;
        console.log('[UDM] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedDisplayMatrix;
}