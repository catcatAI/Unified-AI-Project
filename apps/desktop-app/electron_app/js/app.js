/**
 * Angela AI - Main Application
 * 
 * Main entry point that coordinates all systems
 */

class AngelaApp {
    constructor() {
        this.live2dManager = null;
        this.inputHandler = null;
        this.audioHandler = null;
        this.hapticHandler = null;
        this.wallpaperHandler = null;
        
        // Core systems
        this.logger = null;
        this.dataPersistence = null;
        this.i18n = null;
        this.themeManager = null;
        this.pluginManager = null;
        this.userManager = null;
        this.performanceMonitor = null;
        
        // Angela systems
        this.stateMatrix = null;
        this.performanceManager = null;
        this.maturityTracker = null;
        this.precisionManager = null;
        this.backendWebSocket = null;
        this.hardwareDetector = null;
        
        // UI elements
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        this.statusBar = document.getElementById('status-bar');
        this.controls = document.getElementById('controls');
        
        // State
        this.isInitialized = false;
        this.currentModel = null;
        this.idleTimer = null;
        this.idleTimeout = 60000;
        
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Angela AI Desktop App...');
        
        try {
            // Initialize core systems first
            await this._initializeLogger();
            await this._initializeDataPersistence();
            await this._initializeI18n();
            await this._initializeThemeManager();
            await this._initializeUserManager();
            
            // Initialize hardware detection
            await this._initializeHardwareDetection();
            
            // Initialize Angela systems
            this._initializeStateMatrix();
            await this._initializePerformanceManager();
            this._initializeMaturityTracker();
            this._initializePrecisionManager();
            this._initializeBackendWebSocket();
            
            // Initialize Live2D manager
            await this._initializeLive2D();
            
            // Initialize input handler
            this._initializeInputHandler();
            
            // Initialize audio handler
            await this._initializeAudioHandler();
            
            // Initialize haptic handler
            await this._initializeHapticHandler();
            
            // Initialize wallpaper handler
            await this._initializeWallpaperHandler();
            
            // Initialize plugin manager
            await this._initializePluginManager();
            
            // Initialize performance monitor
            await this._initializePerformanceMonitor();
            
            // Setup UI controls
            this._setupUIControls();
            
            // Setup Electron API event listeners
            this._setupElectronEvents();
            
            // Load default model
            await this._loadDefaultModel();
            
            // Setup idle detection
            this._setupIdleDetection();
            
            // Sync with backend
            await this._syncWithBackend();
            
            // Hide loading overlay
            this._hideLoading();
            
            this.isInitialized = true;
            this.showStatus('Angela AI is ready!', 3000);
            
            console.log('Angela AI initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Angela AI:', error);
            this.showStatus('Initialization failed. Please check console.', 5000);
        }
    }

    async _initializeLogger() {
        this.updateLoadingText('Initializing logger...');
        
        this.logger = new Logger({
            level: 'info',
            maxLogs: 1000,
            persist: true,
            prefix: '[Angela]'
        });
        
        // Expose logger for other modules
        window.angelaAppLogger = this.logger;
        
        this.logger.info('Angela AI Desktop App starting...');
    }
    
    async _initializeDataPersistence() {
        this.updateLoadingText('Initializing data persistence...');
        
        this.dataPersistence = new DataPersistence({
            prefix: 'angela',
            autoSave: true,
            autoSaveInterval: 60000
        });
        
        // Initialize state persistence
        this.statePersistence = new StatePersistence({
            maxHistorySize: 100
        });
    }
    
    async _initializeI18n() {
        this.updateLoadingText('Initializing internationalization...');
        
        this.i18n = i18n;
        window.i18n = i18n;
        
        // Apply saved locale if exists
        const savedLocale = localStorage.getItem('angela_locale');
        if (savedLocale) {
            this.i18n.setLocale(savedLocale);
        }
    }
    
    async _initializeThemeManager() {
        this.updateLoadingText('Initializing theme manager...');
        
        this.themeManager = theme;
        window.theme = theme;
        
        // Apply saved theme if exists
        const savedTheme = localStorage.getItem('angela_theme');
        if (savedTheme) {
            this.themeManager.setTheme(savedTheme, false);
        }
    }
    
    async _initializeUserManager() {
        this.updateLoadingText('Initializing user manager...');
        
        this.userManager = userManager;
        window.userManager = userManager;
        
        // Create default user if none exists
        if (this.userManager.getAllUsers().length === 0) {
            this.userManager.createUser({
                name: 'User',
                preferences: {
                    language: this.i18n.getLocale(),
                    theme: this.themeManager.getTheme()
                }
            });
        }
    }
    
    async _initializeHardwareDetection() {
        this.updateLoadingText('Detecting hardware...');
        
        this.hardwareDetector = new HardwareDetector();
        const hardware = await this.hardwareDetector.detect();
        
        this.logger.info('Hardware detected', hardware);
    }
    
    _initializeStateMatrix() {
        this.updateLoadingText('Initializing state matrix...');
        
        this.stateMatrix = new StateMatrix4D();
    }
    
    async _initializePerformanceManager() {
        this.updateLoadingText('Initializing performance manager...');
        
        this.performanceManager = new PerformanceManager();
        
        await this.performanceManager.initialize();
        
        this.stateMatrix.setLive2DManager(this.live2dManager);
        this.precisionManager.setPerformanceManager(this.performanceManager);
    }
    
    _initializeMaturityTracker() {
        this.updateLoadingText('Initializing maturity tracker...');
        
        this.maturityTracker = new MaturityTracker();
        
        this.stateMatrix.setStateMatrix(this.maturityTracker);
    }
    
    _initializePrecisionManager() {
        this.updateLoadingText('Initializing precision manager...');
        
        this.precisionManager = new PrecisionManager();
    }
    
    _initializeBackendWebSocket() {
        this.updateLoadingText('Setting up backend connection...');
        
        this.backendWebSocket = new BackendWebSocket();
        
        this.stateMatrix.setWebSocket(this.backendWebSocket);
        this.maturityTracker.setWebSocket(this.backendWebSocket);
        this.precisionManager.setWebSocket(this.backendWebSocket);
        
        this.backendWebSocket.onMessage = (message) => this._handleBackendMessage(message);
    }
    
    async _initializeLive2D() {
        this.updateLoadingText('Initializing Live2D...');
        
        const canvas = document.getElementById('live2d-canvas');
        this.live2dManager = new Live2DManager(canvas);
        
        await this.live2dManager.initialize();
        
        this.stateMatrix.setLive2DManager(this.live2dManager);
        this.performanceManager.setLive2DManager(this.live2dManager);
    }

    _initializeInputHandler() {
        this.updateLoadingText('Setting up input handler...');
        
        const clickLayer = document.getElementById('click-layer');
        this.inputHandler = new InputHandler(this.live2dManager, clickLayer);
        
        // Setup callbacks
        this.inputHandler.onClick = this._handleClick.bind(this);
        this.inputHandler.onDrag = this._handleDrag.bind(this);
        this.inputHandler.onHover = this._handleHover.bind(this);
    }

    async _initializeAudioHandler() {
        this.updateLoadingText('Initializing audio system...');
        
        this.audioHandler = new AudioHandler();
        
        // Setup speech recognition callback
        this.audioHandler.onSpeechRecognized = this._handleSpeechRecognized.bind(this);
    }

    async _initializeHapticHandler() {
        this.updateLoadingText('Initializing haptic system...');
        
        this.hapticHandler = new HapticHandler();
    }

    async _initializeWallpaperHandler() {
        this.updateLoadingText('Initializing wallpaper system...');
        
        this.wallpaperHandler = new WallpaperHandler();
    }
    
    async _initializePluginManager() {
        this.updateLoadingText('Initializing plugin manager...');
        
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
        
        // Hook into performance manager
        if (this.performanceManager) {
            this.performanceManager.onModeChange = (mode) => {
                this.performanceMonitor.addCustomMetric('performance_mode', mode);
            };
        }
    }

    _setupUIControls() {
        // Settings button
        document.getElementById('btn-settings').addEventListener('click', () => {
            if (window.electronAPI && window.electronAPI.settings) {
                window.electronAPI.settings.open();
            }
        });
        
        // Minimize button
        document.getElementById('btn-minimize').addEventListener('click', () => {
            if (window.electronAPI && window.electronAPI.window) {
                window.electronAPI.window.minimize();
            }
        });
        
        // Close button
        document.getElementById('btn-close').addEventListener('click', () => {
            if (window.electronAPI && window.electronAPI.window) {
                window.electronAPI.window.close();
            }
        });
        
        // Show controls on hover
        document.addEventListener('mouseenter', () => {
            this.controls.classList.add('visible');
        });
        
        document.addEventListener('mouseleave', () => {
            this.controls.classList.remove('visible');
        });
    }

    _setupElectronEvents() {
        if (!window.electronAPI) return;
        
        // Window ready
        window.electronAPI.on('window-ready', (data) => {
            console.log('Window ready:', data);
        });
        
        // Screen changed
        window.electronAPI.on('screen-changed', (data) => {
            console.log('Screen changed:', data);
            this.inputHandler.updateRegions();
        });
        
        // Theme changed
        window.electronAPI.on('theme-changed', (data) => {
            console.log('Theme changed:', data);
            this._applyTheme(data.shouldUseDarkColors);
        });
    }

    async _loadDefaultModel() {
        this.updateLoadingText('Loading Live2D model...');
        
        try {
            // Get available models
            const models = await window.electronAPI?.live2d?.getModels() || [];
            
            if (models.length > 0) {
                // Load Miara Pro model
                const model = models.find(m => m.name === 'miara_pro') || models[0];
                
                if (model) {
                    const modelPath = model.path.replace(/\\/g, '/');
                    const success = await this.live2dManager.loadModel(modelPath);
                    
                    if (success) {
                        this.currentModel = model.name;
                        this.updateLoadingText(`Loading ${model.name} model...`);
                        
                        // Initialize clickable regions
                        this.inputHandler.updateRegions();
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load default model:', error);
        }
    }

    _handleClick(region, position) {
        console.log('Clicked on:', region, position);
        
        // Visual feedback
        this.inputHandler.showVisualFeedback(position.x, position.y);
        
        // Haptic feedback
        this.hapticHandler.hapticBodyPart(region.name, 0.8);
        
        // Sound effect
        this.audioHandler.playSoundEffect('click');
        
        // Update Live2D expression based on region
        this._updateExpressionFromRegion(region);
        
        // Update state matrix
        this.stateMatrix.handleInteraction('click', { part: region.name });
        
        // Track experience
        this.maturityTracker.addExperience('click', 5);
        
        // Update user stats
        const currentUser = this.userManager.getCurrentUser();
        if (currentUser) {
            this.userManager.incrementInteraction(currentUser.id, 'click');
            this.userManager.updateStats(currentUser.id, {
                clickCount: 1
            });
        }
        
        // Performance monitoring
        this.performanceMonitor.recordInteraction('click');
        
        // Reset idle timer
        this._resetIdleTimer();
        
        this.showStatus(this.i18n.t('interaction.click', { part: region.name }), 2000);
    }

    _handleDrag(drag) {
        console.log('Drag:', drag);
        
        if (drag.region) {
            // Update Live2D body angle based on drag
            const angleX = (drag.deltaX / window.innerWidth) * 30;
            const angleY = (drag.deltaY / window.innerHeight) * 20;
            
            this.live2dManager.setParameter('ParamBodyAngleX', angleX);
            this.live2dManager.setParameter('ParamBodyAngleY', angleY);
        }
    }

    _handleDragEnd(drag) {
        console.log('Drag end:', drag);
        
        // Reset body angle
        this.live2dManager.setParameter('ParamBodyAngleX', 0);
        this.live2dManager.setParameter('ParamBodyAngleY', 0);
    }

    _handleHover(region, position) {
        // Haptic feedback on hover
        if (region && region.type === 'interactive') {
            this.hapticHandler.hapticHover();
        }
    }

    _handleSpeechRecognized(text, isFinal) {
        console.log('Speech recognized:', text, 'Final:', isFinal);
        
        if (isFinal) {
            // Process speech command
            this._processCommand(text);
        }
    }

    _processCommand(text) {
        const command = text.toLowerCase().trim();
        
        this.stateMatrix.handleInteraction('speech', { text, emotion: null });
        this.maturityTracker.addExperience('speech', 10);
        this._resetIdleTimer();
        
        // Update user stats
        const currentUser = this.userManager.getCurrentUser();
        if (currentUser) {
            this.userManager.incrementInteraction(currentUser.id, 'speech');
            this.userManager.updateStats(currentUser.id, {
                speechCount: 1
            });
        }
        
        // Performance monitoring
        this.performanceMonitor.recordInteraction('speech');
        
        // Simple command parsing with i18n
        if (command.includes('hello') || command.includes('hi')) {
            this._speak(this.i18n.t('app.name') + '! How can I help you today?');
            this.live2dManager.setExpression('happy');
            this.stateMatrix.updateGamma({ happiness: 0.8 });
        } else if (command.includes('sad')) {
            this.live2dManager.setExpression('sad');
            this.hapticHandler.hapticEmotion('sad');
            this.stateMatrix.updateGamma({ sadness: 0.7 });
        } else if (command.includes('happy') || command.includes('smile')) {
            this.live2dManager.setExpression('happy');
            this.hapticHandler.hapticEmotion('happy');
            this.stateMatrix.updateGamma({ happiness: 0.8 });
        } else if (command.includes('angry')) {
            this.live2dManager.setExpression('angry');
            this.hapticHandler.hapticEmotion('angry');
            this.stateMatrix.updateGamma({ anger: 0.7 });
        } else if (command.includes('reset') || command.includes('neutral')) {
            this.live2dManager.setExpression('neutral');
            this.live2dManager.resetPose();
            this.stateMatrix.reset();
        } else if (command.includes('screenshot') || command.includes('snapshot')) {
            this.wallpaperHandler.saveSnapshot();
            this.showStatus('Snapshot saved!', 3000);
        } else if (command.includes('theme') && (command.includes('light') || command.includes('dark'))) {
            const newTheme = command.includes('light') ? 'light' : 'dark';
            this.themeManager.setTheme(newTheme);
            this.showStatus(`Theme changed to ${newTheme}`, 2000);
        } else if (command.includes('language') || command.includes('lang')) {
            const supported = ['en', 'zh-CN', 'ja', 'ko'];
            for (const lang of supported) {
                if (command.includes(lang.toLowerCase()) || command.includes(lang)) {
                    this.i18n.setLocale(lang);
                    this.showStatus(`Language changed to ${lang}`, 2000);
                    break;
                }
            }
        }
        
        // Forward to backend for more complex processing
        if (window.electronAPI && window.electronAPI.websocket) {
            window.electronAPI.websocket.send({
                type: 'speech',
                text: text
            });
        }
    }
    
    _setupIdleDetection() {
        this._resetIdleTimer();
        
        const resetTimer = () => this._resetIdleTimer();
        
        document.addEventListener('click', resetTimer);
        document.addEventListener('mousemove', resetTimer);
        document.addEventListener('keydown', resetTimer);
    }
    
    _resetIdleTimer() {
        if (this.idleTimer) {
            clearTimeout(this.idleTimer);
        }
        
        this.idleTimer = setTimeout(() => {
            this._handleIdle();
        }, this.idleTimeout);
    }
    
    _handleIdle() {
        console.log('User idle, updating state...');
        this.stateMatrix.handleInteraction('idle', { duration: 60 });
    }
    
    async _syncWithBackend() {
        try {
            const backendUrl = localStorage.getItem('backend_url') || 'ws://localhost:8765';
            
            if (this.backendWebSocket) {
                await this.backendWebSocket.connect(backendUrl);
            }
            
            // Send initial state to backend
            if (this.backendWebSocket.isConnected()) {
                this.backendWebSocket.send({
                    type: 'init',
                    state: this.stateMatrix.exportToDict(),
                    maturity: this.maturityTracker.getStatus(),
                    performance: this.performanceManager.getPerformanceMetrics(),
                    precision: this.precisionManager.getMetrics()
                });
            }
        } catch (error) {
            console.error('Failed to sync with backend:', error);
        }
    }
    
    _handleBackendMessage(message) {
        console.log('Received backend message:', message);
        
        switch (message.type) {
            case 'state_update':
                this._handleBackendStateUpdate(message);
                break;
            case 'performance_change':
                this._handleBackendPerformanceChange(message);
                break;
            case 'precision_change':
                this._handleBackendPrecisionChange(message);
                break;
            case 'level_up':
                this._handleBackendLevelUp(message);
                break;
            case 'hardware_detected':
                this._handleBackendHardwareDetected(message);
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }
    
    _handleBackendStateUpdate(message) {
        if (message.dimension && message.changes) {
            this.stateMatrix[`update${message.dimension.charAt(0).toUpperCase() + message.dimension.slice(1)}`](message.changes);
        }
    }
    
    _handleBackendPerformanceChange(message) {
        if (message.to) {
            this.performanceManager.setPerformanceMode(message.to);
        }
    }
    
    _handleBackendPrecisionChange(message) {
        if (message.level !== undefined) {
            this.precisionManager.setGlobalPrecision(message.level);
        }
    }
    
    _handleBackendLevelUp(message) {
        if (message.to !== undefined) {
            console.log(`Backend confirms level up to L${message.to}`);
        }
    }
    
    _handleBackendHardwareDetected(message) {
        if (message.profile && message.recommended_mode) {
            console.log('Backend hardware detection:', message.recommended_mode);
            this.performanceManager.setPerformanceMode(message.recommended_mode);
        }
    }

    _speak(text) {
        this.audioHandler.speak(text, {
            rate: 1,
            pitch: 1,
            volume: 1
        });
        
        // Enable lip sync
        this.live2dManager.enableLipSync(true);
    }

    _updateExpressionFromRegion(region) {
        const expressionMap = {
            'head': 'surprised',
            'face': 'happy',
            'chest': 'shy',
            'left_arm': 'happy',
            'right_arm': 'happy'
        };
        
        const expression = expressionMap[region.name] || 'happy';
        this.live2dManager.setExpression(expression);
    }

    _applyTheme(isDark) {
        // Apply theme to app
        if (isDark) {
            document.body.style.background = 'rgba(0, 0, 0, 0)';
        } else {
            document.body.style.background = 'rgba(255, 255, 255, 0)';
        }
    }

    updateLoadingText(text) {
        if (this.loadingText) {
            this.loadingText.textContent = text;
        }
    }

    _hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    showStatus(message, duration = 3000) {
        if (this.statusBar) {
            this.statusBar.textContent = message;
            this.statusBar.classList.add('visible');
            
            setTimeout(() => {
                this.statusBar.classList.remove('visible');
            }, duration);
        }
    }

    // Public API
    async loadModel(modelPath) {
        const success = await this.live2dManager.loadModel(modelPath);
        
        if (success) {
            this.inputHandler.updateRegions();
            this.showStatus('Model loaded!', 2000);
        }
        
        return success;
    }

    setExpression(expression) {
        this.live2dManager.setExpression(expression);
    }

    speak(text) {
        this._speak(text);
    }

    takeSnapshot() {
        this.wallpaperHandler.saveSnapshot();
    }

    async connectBackend(url) {
        if (window.electronAPI && window.electronAPI.websocket) {
            window.electronAPI.websocket.connect(url);
            this.showStatus('Connected to backend', 3000);
        }
    }

    async disconnectBackend() {
        if (window.electronAPI && window.electronAPI.websocket) {
            window.electronAPI.websocket.disconnect();
            this.showStatus('Disconnected from backend', 3000);
        }
    }

    shutdown() {
        console.log('Shutting down Angela AI...');
        
        // Shutdown all handlers
        if (this.live2dManager) this.live2dManager.shutdown();
        if (this.inputHandler) this.inputHandler.destroy();
        if (this.audioHandler) this.audioHandler.shutdown();
        if (this.hapticHandler) this.hapticHandler.shutdown();
        if (this.wallpaperHandler) this.wallpaperHandler.cleanup();
        
        // Shutdown core systems
        if (this.performanceMonitor) this.performanceMonitor.stopCollecting();
        if (this.pluginManager) this.pluginManager.destroy();
        if (this.logger) this.logger.destroy();
        if (this.dataPersistence) this.dataPersistence.destroy();
        
        // Save state before shutdown
        if (this.stateMatrix) {
            this.statePersistence?.saveState(this.stateMatrix.exportToDict());
        }
        
        // Disconnect from backend
        if (this.backendWebSocket) {
            this.backendWebSocket.disconnect();
        }
        
        console.log('Angela AI shutdown complete');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.angelaApp = new AngelaApp();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AngelaApp;
}
