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
            this._initializeUDM();
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

    async _initializeLogger() {
        this.updateLoadingText('Initializing logger...');
        this.logger = new Logger({
            level: 'info',
            maxLogs: 1000,
            persist: true,
            prefix: '[Angela]'
        });
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
     * 初始化统一显示矩阵 (UDM)
     * 这是最关键的初始化步骤，所有显示相关的系统都依赖它
     */
    _initializeUDM() {
        this.updateLoadingText('Initializing display matrix...');
        console.log('[AngelaApp] Creating UnifiedDisplayMatrix...');
        
        // 获取 wrapper 和 canvas 元素
        const wrapper = document.querySelector('.canvas-wrapper') || document.getElementById('fallback-wrapper');
        const canvas = document.getElementById('fallback-canvas') || document.getElementById('live2d-canvas');
        
        // 确保两个 canvas 都有正确的尺寸
        const live2dCanvas = document.getElementById('live2d-canvas');
        if (live2dCanvas) {
            live2dCanvas.width = 1280;
            live2dCanvas.height = 720;
            console.log('[AngelaApp] live2d-canvas dimensions set to 1280x720');
        }
        
        // 创建 UDM 实例（传入元素引用）
        try {
            this.udm = new UnifiedDisplayMatrix({
                wrapperElement: wrapper,
                canvasElement: canvas
            });
            
            // 设置 wrapper 尺寸为 UDM display size (720p = 100%)
            if (wrapper && this.udm) {
                const displaySize = this.udm.getDisplaySize();
                wrapper.style.width = displaySize.width + 'px';
                wrapper.style.height = displaySize.height + 'px';
                console.log('[AngelaApp] Wrapper size set:', displaySize.width, 'x', displaySize.height);
            }
            
            // 绑定按钮事件
            this._bindScaleButtons();
            
            console.log('[AngelaApp] UDM initialized successfully');
        } catch (error) {
            console.error('[AngelaApp] UDM初始化失败，使用降级方案:', error);
            
            // 降级方案：创建简化的UDM
            this.udm = {
                // 基本坐标转换
                screenToCanvas: (sx, sy) => {
                    if (!canvas) return { x: sx, y: sy };
                    const rect = canvas.getBoundingClientRect();
                    return {
                        x: (sx - rect.left) * (canvas.width / rect.width),
                        y: (sy - rect.top) * (canvas.height / rect.height)
                    };
                },
                
                // 基本缩放
                getUserScale: () => 1.0,
                setUserScale: (scale) => {},
                
                // 基本身体部位检测
                identifyBodyPart: (x, y) => {
                    // 简单的中心区域检测
                    const cx = 640; // 1280/2
                    const cy = 360; // 720/2
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
                getDisplaySize: () => ({ width: 1280, height: 720 })
            };
            
            // 仍然设置wrapper尺寸
            if (wrapper) {
                wrapper.style.width = '1280px';
                wrapper.style.height = '720px';
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

        document.getElementById('btn-close')?.addEventListener('click', () => {
            window.electronAPI?.window?.close();
        });

        // 将鼠标事件绑定到 controls 元素本身，而不是 document
        // 避免全局事件监听器导致的内存泄漏
        if (this.controls) {
            this.controls.addEventListener('mouseenter', () => {
                this.controls.classList.add('visible');
            });
            this.controls.addEventListener('mouseleave', () => {
                this.controls.classList.remove('visible');
            });
        }
    }

    _setupElectronEvents() {
        if (!window.electronAPI) return;
        
        window.electronAPI.on('window-ready', (d) => console.log('Window ready:', d));
        window.electronAPI.on('screen-changed', (d) => {
            console.log('Screen changed:', d);
            this.inputHandler?.updateRegions();
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
                case '1':
                    // 切換到表情包 1
                    this._switchToCharacterImage('expression_pack_1', '表情包 1');
                    break;
                case '2':
                    // 切換到 AI 助手
                    this._switchToCharacterImage('fullbody_ai_assistant', 'AI 助手');
                    break;
                case '3':
                    // 切換到姿態序列 1
                    this._switchToCharacterImage('pose_sequence_1', '姿態序列 1');
                    break;
                case '4':
                    // 切換到默認立繪
                    this._switchToCharacterImage('default', '默認立繪');
                    break;
                case '0':
                    // 切換到 Live2D 模式
                    if (this.live2dManager?.getMode() === 'fallback') {
                        this.live2dManager.switchToLive2D();
                        this.showStatus('切換到 Live2D 模式', 2000);
                    }
                    break;
                case '[':
                    // 上一張立繪
                    if (this.live2dManager?.getMode() === 'fallback') {
                        if (this.live2dManager?.previousCharacterImage()) {
                            const images = this.live2dManager?.getAvailableCharacterImages() || [];
                            const current = images.find(img => img.id === this.live2dManager?.currentCharacterImageId);
                            this.showStatus(`立繪: ${current?.name || 'Unknown'}`, 2000);
                        }
                    }
                    break;
                case ']':
                    // 下一張立繪
                    if (this.live2dManager?.getMode() === 'fallback') {
                        if (this.live2dManager?.nextCharacterImage()) {
                            const images = this.live2dManager?.getAvailableCharacterImages() || [];
                            const current = images.find(img => img.id === this.live2dManager?.currentCharacterImageId);
                            this.showStatus(`立繪: ${current?.name || 'Unknown'}`, 2000);
                        }
                    }
                    break;
                case '-':
                    // 上一個表情/姿態（適用於 sprite sheet）
                    if (this.live2dManager?.getMode() === 'fallback') {
                        const imageData = this.live2dManager?.characterImages[this.live2dManager?.currentCharacterImageId];
                        if (imageData?.config?.type === 'sprite_sheet') {
                            const config = imageData.config;
                            const totalCells = config.grid.rows * config.cols;
                            const currentIndex = this.live2dManager?.spriteSheetIndex || 0;
                            const newIndex = (currentIndex - 1 + totalCells) % totalCells;
                            this.live2dManager?.setSpriteSheetIndex(newIndex);
                            
                            const expressions = this.live2dManager?.getAvailableExpressions() || [];
                            const currentExpr = expressions[newIndex];
                            this.showStatus(`表情/姿態: ${currentExpr?.name || newIndex}`, 2000);
                        }
                    }
                    break;
                case '=':
                case '+':
                    // 下一個表情/姿態（適用於 sprite sheet）
                    if (this.live2dManager?.getMode() === 'fallback') {
                        const imageData2 = this.live2dManager?.characterImages[this.live2dManager?.currentCharacterImageId];
                        if (imageData2?.config?.type === 'sprite_sheet') {
                            const newIndex = this.live2dManager?.nextSpriteSheetIndex();
                            const expressions = this.live2dManager?.getAvailableExpressions() || [];
                            const currentExpr = expressions[newIndex];
                            this.showStatus(`表情/姿態: ${currentExpr?.name || newIndex}`, 2000);
                        }
                    }
                    break;
            }
        });
        
        console.log('[App] Keyboard shortcuts configured');
        console.log('[App] 0: 切換到 Live2D 模式 | 1-4: 切換立繪 | []: 上一張/下一張立繪 | -+: 上一個/下一個表情');
    }

    /**
     * 切換到指定的立繪圖片（自動切換到 fallback 模式）
     */
    async _switchToCharacterImage(imageId, imageName) {
        // 如果當前是 Live2D 模式，先切換到 fallback 模式
        if (this.live2dManager?.getMode() === 'live2d') {
            await this.live2dManager.switchToFallback();
        }
        
        // 切換立繪
        if (this.live2dManager?.setCharacterImage(imageId)) {
            this.showStatus(`切換到 ${imageName}`, 2000);
        }
    }
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
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AngelaApp;
}
