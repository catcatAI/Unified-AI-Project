/**
 * Angela AI - Main Application
 * 
 * 统一显示矩阵 (UDM) 集成版本
 */

class AngelaApp {
    constructor() {
        // 核心系统（按初始化顺序）
        this.udm = null;                    // 统一显示矩阵（最先）
        this.stateMatrix = null;             // 情感状态矩阵 (αβγδ)
        this.live2dManager = null;
        this.inputHandler = null;
        this.audioHandler = null;
        this.hapticHandler = null;
        this.wallpaperHandler = null;

        // 其他系统
        this.logger = null;
        this.dataPersistence = null;
        this.security = null;
        this.i18n = null;
        this.themeManager = null;
        this.pluginManager = null;
        this.userManager = null;
        this.performanceManager = null;
        this.maturityTracker = null;
        this.precisionManager = null;
        this.backendWebSocket = null;
        this.apiClient = null;
        this.hardwareDetector = null;
        this.dialogueUI = null;

        // UI 元素
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        this.progressBarFill = document.getElementById('progress-bar-fill');
        this.statusBar = document.getElementById('status-bar');
        this.controls = document.getElementById('controls');

        // 状态
        this.isInitialized = false;
        this.currentModel = null;
        this.idleTimer = null;
        this.idleTimeout = 60000;
        this.loadingProgress = 0;  // 加载进度 0-100

        // 初始化顺序追蹤
        this.initializationOrder = [];
        this.initializationDependencies = {
            'logger': [],                     // 無依賴
            'dataPersistence': [],             // 無依賴
            'security': [],                    // 無依賴
            'i18n': [],                        // 無依賴
            'themeManager': [],                // 無依賴
            'userManager': [],                 // 無依賴
            'hardwareDetection': [],           // 無依賴
            'udm': [],                         // 無依賴
            'stateMatrix': [],                 // 無依賴
            'precisionManager': [],            // 無依賴
            'maturityTracker': [],             // 無依賴
            'performanceManager': ['window.angelaApp'],  // 需要全局實例
            'detectionSystem': ['hardwareDetection'],    // 需要硬件檢測
            'live2D': ['udm'],                 // 需要 UDM
            'backendWebSocket': [],             // 無依賴
            'apiClient': [],                   // 無依賴
            'inputHandler': ['live2D'],        // 需要 Live2D
            'audioHandler': [],                // 無依賴
            'hapticHandler': [],               // 無依賴
            'wallpaperHandler': [],            // 無依賴
            'pluginManager': [],               // 無依賴
            'performanceMonitor': [],          // 無依賴
            'dialogueUI': []                   // 無依賴
        };

        this.initialize();
    }

    async initialize() {
        console.log('[AngelaApp] Initializing...');

        // 重置进度
        this.loadingProgress = 0;
        this.updateLoadingProgress(0, 'Initializing Angela AI...');

        try {
            // 1. 基础设施 (10%)
            await this._initializeLogger();
            this.incrementLoadingProgress(2, 'Initializing logger...');
            await this._initializeDataPersistence();
            this.incrementLoadingProgress(2, 'Initializing data persistence...');
            await this._initializeSecurity();
            this.incrementLoadingProgress(2, 'Initializing security...');
            await this._initializeI18n();
            this.incrementLoadingProgress(2, 'Initializing i18n...');
            await this._initializeThemeManager();
            this.incrementLoadingProgress(1, 'Initializing theme...');
            await this._initializeUserManager();
            this.incrementLoadingProgress(1, 'Initializing user manager...');

            // 2. 硬件检测 (15%)
            await this._initializeHardwareDetection();
            this.incrementLoadingProgress(5, 'Detecting hardware...');

            // 3. 初始化 UDM（最先初始化，其他系统依赖它）(20%)
            console.log('[App] Initializing UDM...');
            await this._initializeUDM();  // 改為 async 確保完全初始化
            this.incrementLoadingProgress(5, 'Initializing display matrix...');

            // 4. Angela 逻辑系统 (35%)
            this._initializeStateMatrix();
            this.incrementLoadingProgress(5, 'Initializing state matrix...');
            this._initializePrecisionManager();
            this.incrementLoadingProgress(5, 'Initializing precision manager...');
            this._initializeMaturityTracker();
            this.incrementLoadingProgress(5, 'Initializing maturity tracker...');

            // 5. 性能管理器（需要在 window.angelaApp 设置后调用 toggleModule）(45%)
            // 先暴露实例，确保 PerformanceManager 能访问 toggleModule
            window.angelaApp = this;
            this._setupPlaceholderMethods();  // 设置占位方法
            await this._initializePerformanceManager();
            this.incrementLoadingProgress(10, 'Initializing performance manager...');

            // 6. 检测系统 (50%)
            await this._initializeDetectionSystem();
            this.incrementLoadingProgress(5, 'Initializing detection system...');

            // 7. Live2D（传入 UDM）(65%)
            // 確保 UDM 已完全初始化
            if (!this.udm) {
                console.error('[App] UDM 未初始化，無法初始化 Live2D');
                throw new Error('UDM initialization failed');
            }
            await this._initializeLive2D();
            this.incrementLoadingProgress(15, 'Initializing Live2D...');

            // 8. 连接系统 (70%)
            this._linkSystems();
            this.incrementLoadingProgress(5, 'Connecting systems...');

            // 9. 其他处理器 (90%)
            this._initializeBackendWebSocket();
            this._initializeAPIClient();
            this._initializeInputHandler();
            await this._initializeAudioHandler();
            this.incrementLoadingProgress(5, 'Initializing audio...');
            await this._initializeHapticHandler();
            this.incrementLoadingProgress(5, 'Initializing haptic...');
            await this._initializeWallpaperHandler();
            this.incrementLoadingProgress(5, 'Initializing wallpaper...');
            await this._initializePluginManager();
            await this._initializePerformanceMonitor();
            this.incrementLoadingProgress(5, 'Initializing plugins and monitor...');

            // 10. UI 组件 (95%)
            await this._initializeDialogueUI();
            this.incrementLoadingProgress(5, 'Initializing dialogue UI...');

            // 11. 最终设置 (100%)
            this._setupUIControls();
            this._setupElectronEvents();
            await this._loadDefaultModel();
            this.incrementLoadingProgress(3, 'Loading model...');
            this._setupIdleDetection();
            await this._syncWithBackend();
            this.incrementLoadingProgress(2, 'Finalizing...');

            this._hideLoading();
            window.angelaApp = this;

            this.isInitialized = true;
            this.showStatus('Angela AI Ready!', 3000);
            console.log('[AngelaApp] Initialization complete');

        } catch (error) {
            console.error('[AngelaApp] Critical error:', error);
            this.showStatus('Init failed. Check console.', 5000);
            setTimeout(() => this._hideLoading(), 2000);
        }
    }

    /**
     * 连接所有系统
     */
    _linkSystems() {
        console.log('[AngelaApp] Linking systems...');

        // StateMatrix → Live2D
        if (this.stateMatrix) {
            this.stateMatrix.setLive2DManager(this.live2dManager);
            this.stateMatrix.setWebSocket(this.backendWebSocket);
        }

        // PerformanceManager
        if (this.performanceManager) {
            this.performanceManager.setLive2DManager(this.live2dManager);
            this.performanceManager.setWebSocket(this.backendWebSocket);
        }

        // PrecisionManager
        if (this.precisionManager) {
            this.precisionManager.setPerformanceManager(this.performanceManager);
            this.precisionManager.setWebSocket(this.backendWebSocket);
        }

        // MaturityTracker
        if (this.maturityTracker) {
            this.maturityTracker.setWebSocket(this.backendWebSocket);
            this.maturityTracker.setStateMatrix(this.stateMatrix);
        }
    }

    // ========== 初始化方法 ==========

    /**
     * 記錄初始化步驟
     * @param {string} component 組件名稱
     */
    _trackInitialization(component) {
        this.initializationOrder.push({
            component: component,
            timestamp: Date.now()
        });
        console.log(`[AngelaApp] Initialized: ${component}`);
    }

    /**
     * 驗證初始化順序和依賴關係
     * @param {string} component 當前初始化的組件
     */
    _validateInitializationOrder(component) {
        const dependencies = this.initializationDependencies[component] || [];

        for (const dependency of dependencies) {
            // 檢查是否是依賴於全局變量
            if (dependency.startsWith('window.')) {
                const globalVar = dependency.replace('window.', '');
                if (!window[globalVar]) {
                    console.error(`[AngelaApp] Initialization order error: ${component} requires ${dependency} to be set first`);
                    throw new Error(`Missing dependency: ${dependency}`);
                }
            } else {
                // 檢查是否是依賴於其他組件
                const initialized = this.initializationOrder.some(step => step.component === dependency);
                if (!initialized) {
                    console.error(`[AngelaApp] Initialization order error: ${component} requires ${dependency} to be initialized first`);
                    throw new Error(`Missing dependency: ${dependency}`);
                }
            }
        }
    }

    /**
     * 驗證初始化是否成功
     * @returns {Object} 驗證結果
     */
    _validateInitialization() {
        const result = {
            success: true,
            errors: [],
            warnings: []
        };

        // 檢查所有必要組件是否已初始化
        const requiredComponents = [
            'logger', 'dataPersistence', 'security', 'i18n', 'themeManager',
            'userManager', 'hardwareDetection', 'udm', 'stateMatrix',
            'precisionManager', 'maturityTracker', 'performanceManager',
            'detectionSystem', 'live2D', 'backendWebSocket', 'apiClient',
            'inputHandler', 'audioHandler', 'hapticHandler', 'wallpaperHandler',
            'pluginManager', 'performanceMonitor', 'dialogueUI'
        ];

        for (const component of requiredComponents) {
            const initialized = this.initializationOrder.some(step => step.component === component);
            if (!initialized) {
                result.errors.push(`Component not initialized: ${component}`);
                result.success = false;
            }
        }

        // 檢查是否有重複初始化
        const componentCounts = {};
        for (const step of this.initializationOrder) {
            componentCounts[step.component] = (componentCounts[step.component] || 0) + 1;
        }

        for (const [component, count] of Object.entries(componentCounts)) {
            if (count > 1) {
                result.warnings.push(`Component initialized multiple times: ${component} (${count} times)`);
            }
        }

        return result;
    }

    async _initializeLogger() {
        this.updateLoadingText('Initializing logger...');

        // 驗證初始化順序
        this._validateInitializationOrder('logger');

        this.logger = new Logger({
            level: 'info',
            maxLogs: 1000,
            persist: true,
            prefix: '[Angela]'
        });

        // 追蹤初始化
        this._trackInitialization('logger');

        window.angelaAppLogger = this.logger;
        this.logger.info('Angela AI starting...');
    }

    async _initializeDataPersistence() {
        this.updateLoadingText('Initializing data persistence...');
        this.dataPersistence = new DataPersistence({
            prefix: 'angela',
            autoSave: true,
            autoSaveInterval: 60000
        });
        this.statePersistence = new StatePersistence({ maxHistorySize: 100 });
    }

    async _initializeSecurity() {
        this.updateLoadingText('Initializing security...');
        try {
            const backendHost = localStorage.getItem('backend_host') || 'localhost';
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch(`http://${backendHost}:8000/api/v1/security/sync-key-c`, { signal: controller.signal });
            clearTimeout(timeoutId);

            const data = await response.json();
            if (data.key_c) {
                const result = await window.electronAPI.security.init(data.key_c);
                if (result.success) {
                    this.security = window.electronAPI.security;
                    this.logger.info('Security initialized with remote Key C');
                    this._updateSecurityBadge(true);
                    return;
                }
            }
            throw new Error('Remote Key C unavailable');
        } catch (error) {
            this.logger.warn('Security fallback mode:', error.message);
            await window.electronAPI.security.init('Angela-Desktop-Sync-Key-C-Fallback');
            this.security = window.electronAPI.security;
            this._updateSecurityBadge(false);
        }
    }

    _updateSecurityBadge(isSecure) {
        const badge = document.getElementById('security-badge');
        if (badge) {
            badge.className = isSecure ? 'secure' : 'unsecure';
            badge.querySelector('.text').textContent = isSecure ? 'Security: Verified' : 'Security: Fallback';
            badge.querySelector('.icon').textContent = isSecure ? '🛡️' : '⚠️';
        }
    }

    async _initializeI18n() {
        this.updateLoadingText('Initializing i18n...');
        this.i18n = i18n;
        window.i18n = i18n;
        const saved = localStorage.getItem('angela_locale');
        if (saved) this.i18n.setLocale(saved);
    }

    async _initializeThemeManager() {
        this.updateLoadingText('Initializing theme...');
        this.themeManager = theme;
        window.theme = theme;
        const saved = localStorage.getItem('angela_theme');
        if (saved) this.themeManager.setTheme(saved, false);
    }

    async _initializeUserManager() {
        this.updateLoadingText('Initializing user manager...');
        this.userManager = userManager;
        window.userManager = userManager;
        if (this.userManager.getAllUsers().length === 0) {
            this.userManager.createUser({
                name: 'User',
                preferences: { language: this.i18n.getLocale(), theme: this.themeManager.getTheme() }
            });
        }
    }

    async _initializeHardwareDetection() {
        this.updateLoadingText('Detecting hardware...');
        const start = performance.now();
        this.hardwareDetector = new HardwareDetector();
        const hardware = await this.hardwareDetector.detect();
        console.log(`[Hardware] Detected in ${(performance.now() - start).toFixed(2)}ms`);
        return hardware;
    }

    /**
     * 初始化統一顯示矩陣 (UDM)
     * 這是最關鍵的初始化步驟，所有顯示相關的系統都依賴它
     * @returns {Promise<void>}
     */
    async _initializeUDM() {
        this.updateLoadingText('Initializing display matrix...');
        console.log('[AngelaApp] Creating UnifiedDisplayMatrix...');

        // 獲取 wrapper 和 canvas 元素
        const wrapper = document.querySelector('.canvas-wrapper') || document.getElementById('fallback-wrapper');
        const canvas = document.getElementById('fallback-canvas') || document.getElementById('live2d-canvas');

        // 確保兩個 canvas 都有正確的尺寸
        const live2dCanvas = document.getElementById('live2d-canvas');
        const fallbackCanvas = document.getElementById('fallback-canvas');

        // 基準尺寸 (720p)
        const baseWidth = 1280;
        const baseHeight = 720;
        const devicePixelRatio = window.devicePixelRatio || 1;

        // 設置 canvas 尺寸，考慮 devicePixelRatio
        const setCanvasSize = (canvasEl) => {
            if (canvasEl) {
                // 物理像素尺寸
                canvasEl.width = baseWidth * devicePixelRatio;
                canvasEl.height = baseHeight * devicePixelRatio;

                // CSS 尺寸
                canvasEl.style.width = baseWidth + 'px';
                canvasEl.style.height = baseHeight + 'px';

                console.log(`[AngelaApp] ${canvasEl.id} dimensions set: ${canvasEl.width}x${canvasEl.height} (physical), ${baseWidth}x${baseHeight} (CSS), DPR: ${devicePixelRatio}`);
            }
        };

        setCanvasSize(live2dCanvas);
        setCanvasSize(fallbackCanvas);

        // 創建 UDM 實例（傳入元素引用）
        try {
            this.udm = new UnifiedDisplayMatrix({
                wrapperElement: wrapper,
                canvasElement: canvas
            });

            // 設置 wrapper 尺寸為 UDM display size (720p = 100%)
            if (wrapper && this.udm) {
                const displaySize = this.udm.getDisplaySize();
                wrapper.style.width = displaySize.width + 'px';
                wrapper.style.height = displaySize.height + 'px';
                console.log('[AngelaApp] Wrapper size set:', displaySize.width, 'x', displaySize.height);
            }

            // 綁定按鈕事件
            this._bindScaleButtons();

            // 確保 UDM 已完全初始化
            if (!this.udm || typeof this.udm.screenToCanvas !== 'function') {
                throw new Error('UDM initialization incomplete');
            }

            console.log('[AngelaApp] UDM initialized successfully');
        } catch (error) {
            console.error('[AngelaApp] UDM初始化失敗，使用降級方案:', error);

            // 降級方案：創建簡化的UDM
            this.udm = {
                // 基本坐標轉換（修正版本）
                screenToCanvas: (sx, sy) => {
                    if (!canvas) return { x: sx, y: sy };
                    const rect = canvas.getBoundingClientRect();
                    return {
                        x: (sx - rect.left) * (baseWidth / rect.width),
                        y: (sy - rect.top) * (baseHeight / rect.height)
                    };
                },

                // 基本縮放
                getUserScale: () => 1.0,
                setUserScale: (scale) => { },

                // 基本身體部位檢測
                identifyBodyPart: (x, y) => {
                    // 簡單的中心區域檢測
                    const cx = baseWidth / 2;
                    const cy = baseHeight / 2;
                    const dx = x - cx;
                    const dy = y - cy;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < 100) {
                        return { name: 'face', priority: 1, expression: 'neutral' };
                    }
                    return null;
                },

                // 基本触觉强度计算
                calculateHapticIntensity: (base, pos, size) => base,

                // 基本方法
                handleTouch: (x, y, type) => ({ success: false }),
                handleClick: (x, y) => ({ success: false }),

                // 显示尺寸
                getDisplaySize: () => ({ width: baseWidth, height: baseHeight })
            };

            // 仍然设置wrapper尺寸
            if (wrapper) {
                wrapper.style.width = baseWidth + 'px';
                wrapper.style.height = baseHeight + 'px';
            }

            console.warn('[AngelaApp] 使用简化的UDM降级方案');

            // 通知用户
            if (this._showNotification) {
                this._showNotification('部分功能受限，使用降级模式', 'warning');
            }
        }
    }

    /**
     * 绑定缩放按钮
     */
    _bindScaleButtons() {
        const scaleUp = document.getElementById('scale-up-btn');
        const scaleDown = document.getElementById('scale-down-btn');

        if (scaleUp) {
            scaleUp.onclick = () => {
                if (this.udm) {
                    this.udm.increaseUserScale(0.1);
                    console.log('[App] Scale up:', this.udm.getUserScale());
                }
            };
        }

        if (scaleDown) {
            scaleDown.onclick = () => {
                if (this.udm) {
                    this.udm.decreaseUserScale(0.1);
                    console.log('[App] Scale down:', this.udm.getUserScale());
                }
            };
        }

        console.log('[App] Scale buttons bound');
    }

    _initializeStateMatrix() {
        this.updateLoadingText('Initializing state matrix...');
        this.stateMatrix = new StateMatrix4D();
    }

    async _initializePerformanceManager() {
        this.updateLoadingText('Initializing performance manager...');
        this.performanceManager = new PerformanceManager();
        const profile = this.hardwareDetector ? this.hardwareDetector.profile : null;
        await this.performanceManager.initialize(profile);
    }

    _initializeMaturityTracker() {
        this.updateLoadingText('Initializing maturity tracker...');
        this.maturityTracker = new MaturityTracker();
        this.maturityTracker.setStateMatrix(this.stateMatrix);
    }

    _initializePrecisionManager() {
        this.updateLoadingText('Initializing precision manager...');
        this.precisionManager = new PrecisionManager();
    }

    async _initializeDetectionSystem() {
        this.updateLoadingText('Initializing detection system...');
        // Detection system initialization
    }

    async _initializeLive2D() {
        this.updateLoadingText('Initializing Live2D...');
        const canvas = document.getElementById('live2d-canvas');

        // 传入 UDM 进行坐标转换
        this.live2dManager = new Live2DManager(canvas, this.udm);
        console.log('[App] Live2DManager created with UDM');

        await this.live2dManager.initialize?.();

        // 恢復上次選擇的模式
        const savedMode = localStorage.getItem('render_mode') || 'live2d';
        if (savedMode === 'fallback') {
            await this.live2dManager.switchToFallback();
            console.log('[App] 恢復到立繫模式');
        }
    }

    _initializeBackendWebSocket() {
        this.updateLoadingText('Connecting to backend...');
        this.backendWebSocket = new BackendWebSocketClient();
        this.stateMatrix?.setWebSocket(this.backendWebSocket);
        this.maturityTracker?.setWebSocket(this.backendWebSocket);
        this.precisionManager?.setWebSocket(this.backendWebSocket);
        this.backendWebSocket.onMessage = (m) => this._handleBackendMessage(m);
    }

    _initializeAPIClient() {
        this.updateLoadingText('Setting up API...');
        const backendIP = localStorage.getItem('backend_ip') || 'http://localhost:8000';
        this.apiClient = new AngelaAPIClient(backendIP);
    }

    _initializeInputHandler() {
        this.updateLoadingText('Setting up input...');
        const clickLayer = document.getElementById('click-layer');
        this.inputHandler = new InputHandler(this.live2dManager, clickLayer);
        this.inputHandler.onClick = this._handleClick.bind(this);
        this.inputHandler.onDrag = this._handleDrag.bind(this);
        this.inputHandler.onHover = this._handleHover.bind(this);
    }

    async _initializeAudioHandler() {
        this.updateLoadingText('Initializing audio...');
        this.audioHandler = new AudioHandler();
        this.audioHandler.onSpeechRecognized = this._handleSpeechRecognized.bind(this);
    }

    async _initializeHapticHandler() {
        this.updateLoadingText('Initializing haptic...');
        // 传入 UDM 进行触觉计算
        this.hapticHandler = new HapticHandler(this.udm);
    }

    async _initializeWallpaperHandler() {
        this.updateLoadingText('Initializing wallpaper...');
        this.wallpaperHandler = new WallpaperHandler();
    }

    async _initializePluginManager() {
        this.updateLoadingText('Initializing plugins...');
        this.pluginManager = new PluginManager({
            pluginsDir: 'plugins',
            autoLoad: false,
            sandbox: true
        });
        this.pluginManager.setLogger(this.logger);
        await this.pluginManager.init();
    }

    async _initializePerformanceMonitor() {
        this.updateLoadingText('Initializing performance monitor...');
        this.performanceMonitor = performanceMonitor;
        window.performanceMonitor = performanceMonitor;
        this.performanceMonitor.startCollecting();
    }

    async _initializeDialogueUI() {
        this.updateLoadingText('Initializing dialogue UI...');
        try {
            if (typeof DialogueUI !== 'undefined') {
                this.dialogueUI = new DialogueUI(this.apiClient);
            }
        } catch (e) {
            console.warn('[App] DialogueUI init failed:', e);
        }
    }

    /**
     * 设置占位方法（供 PerformanceManager 等在完全初始化前调用）
     */
    _setupPlaceholderMethods() {
        // toggleModule - 切换模块启用状态
        this.toggleModule = (module, enabled) => {
            console.log(`[App] toggleModule called: ${module} = ${enabled}`);
            // 实际实现可以延迟到这里
            switch (module) {
                case 'audio':
                    if (this.audioHandler && typeof this.audioHandler.setEnabled === 'function') {
                        this.audioHandler.setEnabled(enabled);
                    }
                    break;
                case 'tactile':
                    if (this.hapticHandler && typeof this.hapticHandler.setEnabled === 'function') {
                        this.hapticHandler.setEnabled(enabled);
                    }
                    break;
            }
            return true;  // 始终返回成功，避免抛错
        };
        console.log('[App] Placeholder methods set');
    }

    // ========== 事件处理 ==========

    _handleBackendMessage(message) {
        // 处理后端消息
        if (message.type === 'state_update') {
            this.stateMatrix?.updateFromBackend(message);
        }

        // P0-2: 处理生物事件
        if (message.type === 'biological_event') {
            this._handleBiologicalEvent(message.data);
        }
    }

    /**
     * P0-2: 处理生物事件
     */
    _handleBiologicalEvent(data) {
        console.log('[App] Biological event received:', data);

        const eventType = data.event;
        const eventData = data.data || {};

        switch (eventType) {
            case 'emotion_changed':
                this._handleEmotionChanged(eventData);
                break;
            case 'stress_changed':
                this._handleStressChanged(eventData);
                break;
            case 'energy_changed':
                this._handleEnergyChanged(eventData);
                break;
            case 'mood_changed':
                this._handleMoodChanged(eventData);
                break;
            case 'arousal_changed':
                this._handleArousalChanged(eventData);
                break;
            case 'hormone_changed':
                this._handleHormoneChanged(eventData);
                break;
            case 'tactile_stimulus':
                this._handleTactileStimulus(eventData);
                break;
            default:
                console.warn('[App] Unknown biological event:', eventType);
        }
    }

    /**
     * P0-2: 处理情绪变化
     */
    _handleEmotionChanged(data) {
        if (this.live2dManager) {
            // 更新 Live2D 表情
            const emotionMap = {
                'happy': 'happy',
                'sad': 'sad',
                'angry': 'angry',
                'fear': 'fear',
                'surprised': 'surprised',
                'love': 'love',
                'calm': 'calm',
                'disgust': 'disgust'
            };

            const expression = emotionMap[data.new_emotion] || 'neutral';
            this.live2dManager.setExpression(expression);

            // 更新情绪强度参数
            if (this.live2dManager.setParameter) {
                this.live2dManager.setParameter('ParamEmotionIntensity', data.intensity || 0.5);
            }
        }
    }

    /**
     * P0-2: 处理压力变化
     */
    _handleStressChanged(data) {
        if (this.stateMatrix) {
            this.stateMatrix.updateAlpha({
                tension: data.stress || 0.5,
                energy: 1.0 - (data.stress || 0.5) * 0.3
            });
        }
    }

    /**
     * P0-2: 处理能量变化
     */
    _handleEnergyChanged(data) {
        if (this.stateMatrix) {
            this.stateMatrix.updateAlpha({
                energy: data.energy || 0.5,
                vitality: data.energy || 0.5
            });
        }
    }

    /**
     * P0-2: 处理心情变化
     */
    _handleMoodChanged(data) {
        if (this.stateMatrix) {
            this.stateMatrix.updateGamma({
                happiness: Math.max(0, data.mood),
                calm: Math.max(0, 1 - Math.abs(data.mood))
            });
        }
    }

    /**
     * P0-2: 处理唤醒水平变化
     */
    _handleArousalChanged(data) {
        if (this.stateMatrix) {
            this.stateMatrix.updateAlpha({
                arousal: data.arousal / 100.0
            });
        }

        if (this.live2dManager && this.live2dManager.setParameter) {
            // 更新 Live2D 唤醒参数
            this.live2dManager.setParameter('ParamArousal', data.arousal / 100.0);
        }
    }

    /**
     * P0-2: 处理激素变化
     */
    _handleHormoneChanged(data) {
        // 可以根据激素类型调整行为
        console.log('[App] Hormone changed:', data);
    }

    /**
     * P0-2: 处理触觉刺激
     */
    _handleTactileStimulus(data) {
        // 触发触觉反馈
        if (this.hapticHandler) {
            this.hapticHandler.trigger(data.intensity || 0.5);
        }
    }

    _handleClick(data, coords) {
        if (data?.bodyPart) {
            // 触摸检测结果
            this.stateMatrix?.handleInteraction('click', { part: data.bodyPart });
        }
    }

    _handleDrag(data, coords) {
        if (data?.bodyPart) {
            this.stateMatrix?.handleInteraction('drag', { part: data.bodyPart });
        }
    }

    _handleHover(data, coords) {
        // 悬停处理
    }

    _handleSpeechRecognized(text) {
        this.stateMatrix?.handleInteraction('speech', { text });
        // 发送到后端
        this.backendWebSocket?.send({ type: 'speech', text });
    }

    // ========== UI 设置 ==========

    _setupUIControls() {
        document.getElementById('btn-settings')?.addEventListener('click', () => {
            window.electronAPI?.settings?.open();
        });

        document.getElementById('btn-minimize')?.addEventListener('click', () => {
            window.electronAPI?.window?.minimize();
        });

        document.getElementById('btn-maximize')?.addEventListener('click', () => {
            window.electronAPI?.window?.maximize();
        });

        document.getElementById('btn-close')?.addEventListener('click', () => {
            window.electronAPI?.window?.close();
        });

        // Dialogue system
        const dialogueInput = document.getElementById('dialogue-input');
        const btnSend = document.getElementById('btn-send');
        const btnToggle = document.getElementById('btn-toggle-dialogue');
        const bottomBar = document.getElementById('bottom-bar');
        const messagesContainer = document.getElementById('dialogue-messages');

        // Toggle dialogue panel
        btnToggle?.addEventListener('click', () => {
            bottomBar?.classList.toggle('expanded');
            if (bottomBar?.classList.contains('expanded')) {
                dialogueInput?.focus();
            }
        });

        // Add message to display
        const addMessage = (sender, text) => {
            if (!messagesContainer) return;

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;

            const time = new Date().toLocaleTimeString('zh-TW', {
                hour: '2-digit',
                minute: '2-digit'
            });

            const escapeHtml = (str) => {
                const div = document.createElement('div');
                div.textContent = str;
                return div.innerHTML;
            };

            messageDiv.innerHTML = `
                <div class="message-text">${escapeHtml(text)}</div>
                <div class="message-time">${time}</div>
            `;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        };

        const sendMessage = () => {
            const message = dialogueInput?.value?.trim();
            if (!message) return;

            console.log('[App] Sending message:', message);

            // Add user message to display
            addMessage('user', message);

            // Send to backend via WebSocket
            if (this.backendClient && this.backendClient.isConnected()) {
                this.backendClient.sendMessage({
                    type: 'user_message',
                    content: message,
                    timestamp: new Date().toISOString()
                });
            }

            // Clear input
            dialogueInput.value = '';
        };

        btnSend?.addEventListener('click', sendMessage);

        dialogueInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Listen for backend responses
        if (this.backendClient) {
            this.backendClient.on('angela_response', (data) => {
                if (data.response) {
                    addMessage('angela', data.response);
                }
            });
        }

        console.log('[App] Dialogue system initialized');
    }


    _setupElectronEvents() {
        if (!window.electronAPI) return;

        window.electronAPI.on('window-ready', (d) => console.log('Window ready:', d));
        window.electronAPI.on('screen-changed', (d) => {
            console.log('Screen changed:', d);
            this.inputHandler?.updateRegions();
        });

        // Listen for WebSocket messages from Main process
        window.electronAPI.on('websocket-message', (message) => {
            if (this.backendWebSocket) {
                // Ensure the message is routed correctly
                this.backendWebSocket._routeMessage(message);
            }
        });

        window.electronAPI.on('websocket-connected', () => {
            if (this.backendWebSocket) {
                this.backendWebSocket.connected = true;
                this.backendWebSocket._fireEvent('connected', { success: true });
            }
        });

        window.electronAPI.on('websocket-disconnected', () => {
            if (this.backendWebSocket) {
                this.backendWebSocket.connected = false;
                this.backendWebSocket._fireEvent('disconnected', { success: false });
            }
        });

        // 處理渲染模式切換
        window.electronAPI.on('render-mode', (mode) => {
            if (this.live2dManager) {
                if (mode === 'live2d' && this.live2dManager.getMode() === 'fallback') {
                    this.live2dManager.switchToLive2D();
                    this.showStatus('切換到 Live2D 模式', 2000);
                } else if (mode === 'fallback' && this.live2dManager.getMode() === 'live2d') {
                    this.live2dManager.switchToFallback();
                    this.showStatus('切換到立繫模式', 2000);
                }
                // 保存到本地存儲
                localStorage.setItem('render_mode', mode);
            }
        });

        // 設置鍵盤快捷鍵
        this._setupKeyboardShortcuts();
    }

    /**
     * 設置鍵盤快捷鍵
     */
    _setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 如果在輸入框中，不處理快捷鍵
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            switch (e.key) {
                case '0':
                    // 雙向切換：Live2D ↔ 立繫模式
                    if (this.live2dManager?.getMode() === 'fallback') {
                        this.live2dManager.switchToLive2D();
                        this.showStatus('切換到 Live2D 模式', 2000);
                    } else {
                        this.live2dManager.switchToFallback();
                        this.showStatus('切換到立繫模式', 2000);
                    }
                    break;
            }
        });

        console.log('[App] Keyboard shortcuts configured');
        console.log('[App] 0: 切換 Live2D/立繫 模式');
    }

    async _loadDefaultModel() {
        this.updateLoadingText('Loading model...');
        // 模型加载逻辑
    }

    _setupIdleDetection() {
        // 空闲检测
    }

    async _syncWithBackend() {
        // 同步状态
    }

    // ========== 工具方法 ==========

    updateLoadingText(text) {
        if (this.loadingText) this.loadingText.textContent = text;
    }

    updateLoadingProgress(progress, text = null) {
        // progress: 0-100
        this.loadingProgress = Math.min(100, Math.max(0, progress));

        if (this.progressBarFill) {
            this.progressBarFill.style.width = `${this.loadingProgress}%`;

            // 完成时添加完成样式
            if (this.loadingProgress >= 100) {
                this.progressBarFill.classList.add('complete');
            } else {
                this.progressBarFill.classList.remove('complete');
            }
        }

        // 可选地更新文本
        if (text) {
            this.updateLoadingText(text);
        }
    }

    incrementLoadingProgress(delta, text = null) {
        this.updateLoadingProgress(this.loadingProgress + delta, text);
    }

    _hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    showStatus(message, duration = 3000) {
        if (this.statusBar) {
            this.statusBar.textContent = message;
            this.statusBar.classList.add('visible');
            setTimeout(() => this.statusBar.classList.remove('visible'), duration);
        }
    }

    /**
     * 清理所有資源
     * 確保所有事件監聽器、WebSocket 連接等都被正確釋放
     */
    cleanup() {
        console.log('[AngelaApp] Cleaning up resources...');

        try {
            // 清理 InputHandler
            if (this.inputHandler && typeof this.inputHandler.destroy === 'function') {
                this.inputHandler.destroy();
                this.inputHandler = null;
                console.log('[AngelaApp] InputHandler cleaned up');
            }

            // 清理 WebSocket
            if (this.backendWebSocket) {
                if (typeof this.backendWebSocket.destroy === 'function') {
                    this.backendWebSocket.destroy();
                } else if (typeof this.backendWebSocket.disconnect === 'function') {
                    this.backendWebSocket.disconnect();
                }
                this.backendWebSocket = null;
                console.log('[AngelaApp] WebSocket cleaned up');
            }

            // 清理 Live2D Manager
            if (this.live2dManager) {
                // 停止渲染循環
                if (typeof this.live2dManager.stop === 'function') {
                    this.live2dManager.stop();
                }
                this.live2dManager = null;
                console.log('[AngelaApp] Live2DManager cleaned up');
            }

            // 清理 AudioHandler
            if (this.audioHandler) {
                if (typeof this.audioHandler.destroy === 'function') {
                    this.audioHandler.destroy();
                }
                this.audioHandler = null;
                console.log('[AngelaApp] AudioHandler cleaned up');
            }

            // 清理 HapticHandler
            if (this.hapticHandler) {
                if (typeof this.hapticHandler.destroy === 'function') {
                    this.hapticHandler.destroy();
                }
                this.hapticHandler = null;
                console.log('[AngelaApp] HapticHandler cleaned up');
            }

            // 清理 PluginManager
            if (this.pluginManager) {
                if (typeof this.pluginManager.destroy === 'function') {
                    this.pluginManager.destroy();
                }
                this.pluginManager = null;
                console.log('[AngelaApp] PluginManager cleaned up');
            }

            // 清理 PerformanceManager
            if (this.performanceManager) {
                if (typeof this.performanceManager.destroy === 'function') {
                    this.performanceManager.destroy();
                }
                this.performanceManager = null;
                console.log('[AngelaApp] PerformanceManager cleaned up');
            }

            // 清理定時器
            if (this.idleTimer) {
                clearTimeout(this.idleTimer);
                this.idleTimer = null;
            }

            // 清理 UI 引用
            this.loadingOverlay = null;
            this.loadingText = null;
            this.progressBarFill = null;
            this.statusBar = null;
            this.controls = null;

            console.log('[AngelaApp] All resources cleaned up successfully');
        } catch (error) {
            console.error('[AngelaApp] Error during cleanup:', error);
        }
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AngelaApp;
}
