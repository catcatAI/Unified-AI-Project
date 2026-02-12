

class PerformanceManager {
    constructor(config = {}) {
        this.config = config;
        this.hardwareProfile = null;
        this.currentMode = 'standard';
        this.wallpaperMode = '2D'; // 預設 2D
        this.targetFPS = 60;
        this.currentFPS = 60;
        this.resolutionScale = 1.0;
        this.effectsLevel = 2;
        this.live2DManager = null;
        this.websocket = null;
        this.fpsHistory = [];
        this.maxFpsHistory = 60;
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.performanceMonitor = null;
        this.autoAdjustEnabled = true;
        this.lastModeChangeTime = 0;
        this.modeChangeCooldown = 10000; // 10 seconds cooldown between mode changes
        this.lastAutoConfigureTime = 0; // 防止短时间内重复自动配置
        this.pendingModeChange = null;
        this.pendingModeChangeTime = 0;
        this.isVisible = true; // Page visibility tracking
        
        // 性能变更消息确认机制
        this._pendingPerformanceChanges = new Map(); // 存储待确认的性能变更
        this._changeConfirmationTimeout = 5000; // 5秒确认超时
        this._changeRetryCount = 3; // 最大重试次数
        
        // 性能能力矩阵 - 三级降级架构
        this.capabilityMatrix = {
            // 硬件能力
            webgl2: { available: false, required: true, fallback: 'webgl' },
            webgl: { available: false, required: true, fallback: null },
            gpu: { available: false, required: true, fallback: 'software' },
            audio: { available: false, required: true, fallback: 'speech' },
            microphone: { available: false, required: false, fallback: null },
            haptic: { available: false, required: false, fallback: null },
            
            // Live2D 能力
            live2d_sdk: { available: false, required: true, fallback: 'fallback' },
            live2d_model: { available: false, required: true, fallback: 'placeholder' },
            live2d_physics: { available: false, required: false, fallback: null },
            live2d_lipsync: { available: false, required: false, fallback: null },
            
            // 性能能力
            high_fps: { available: false, required: false, fallback: 'standard' },
            high_resolution: { available: false, required: false, fallback: 'low' },
            advanced_effects: { available: false, required: false, fallback: 'basic' },
            
            // 系统能力
            websocket: { available: false, required: true, fallback: 'polling' },
            localStorage: { available: false, required: true, fallback: 'memory' },
            indexedDB: { available: false, required: false, fallback: 'memory' },
        };
        
        // 当前能力状态
        this.capabilityState = {
            complete: true,      // 完整版：所有必需能力可用
            degraded: false,      // 降级版：部分能力缺失但有回退
            basic: false,          // 基础版：只有最基本功能
            missing_caps: [],     // 缺失的能力列表
            fallbacks_active: []   // 激活的回退方案
        };
        
        // Add page visibility handling to pause monitoring when hidden
        this._visibilityChangeHandler = () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                // Resume performance monitoring
                this.lastFrameTime = performance.now();
                this.frameCount = 0;
                if (!this.performanceMonitor) {
                    this.startMonitoring();
                }
            } else {
                // Pause performance monitoring when hidden
                if (this.performanceMonitor) {
                    cancelAnimationFrame(this.performanceMonitor);
                    this.performanceMonitor = null;
                }
            }
        };
        document.addEventListener('visibilitychange', this._visibilityChangeHandler);
        
        
        this.performanceModes = {
            very_low: {
                fps: 30,
                resolution: 0.5,
                effects: 0,
                description: '最低配置模式'
            },
            low: {
                fps: 30,
                resolution: 0.6,
                effects: 1,
                description: '低配模式'
            },
            medium: {
                fps: 45,
                resolution: 0.75,
                effects: 2,
                description: '中等配置模式'
            },
            high: {
                fps: 60,
                resolution: 1.0,
                effects: 3,
                description: '高配模式'
            },
            ultra: {
                fps: 120,
                resolution: 1.25,
                effects: 4,
                description: '极致模式'
            }
        };
        
        this.angelaModes = {
            lite: {
                performance_mode: 'low',
                features: {
                    basic_animations: true,
                    advanced_animations: false,
                    physics: false,
                    lip_sync: true,
                    haptic_feedback: false
                }
            },
            standard: {
                performance_mode: 'medium',
                features: {
                    basic_animations: true,
                    advanced_animations: true,
                    physics: true,
                    lip_sync: true,
                    haptic_feedback: true
                }
            },
            extended: {
                performance_mode: 'high',
                features: {
                    basic_animations: true,
                    advanced_animations: true,
                    physics: true,
                    lip_sync: true,
                    haptic_feedback: true
                }
            },
            ultra: {
                performance_mode: 'ultra',
                features: {
                    basic_animations: true,
                    advanced_animations: true,
                    physics: true,
                    lip_sync: true,
                    haptic_feedback: true
                }
            }
        };
    }
    
    setLive2DManager(manager) {
        this.live2DManager = manager;
        if (manager) {
            this.applyPerformanceSettings();
        }
    }
    
    setWebSocket(ws) {
        this.websocket = ws;
    }
    
    /**
     * 检测系统能力并更新能力矩阵
     * @returns {Object} 能力检测结果
     */
    detectCapabilities() {
        console.log('[PerformanceManager] 开始检测系统能力...');
        
        // WebGL2 检测
        this.capabilityMatrix.webgl2.available = this._checkWebGL2();
        
        // WebGL 检测
        this.capabilityMatrix.webgl.available = this._checkWebGL();
        
        // GPU 检测
        this.capabilityMatrix.gpu.available = this.capabilityMatrix.webgl2.available || this.capabilityMatrix.webgl.available;
        
        // 音频检测
        this.capabilityMatrix.audio.available = this._checkAudio();
        
        // 麦克风检测
        this.capabilityMatrix.microphone.available = this._checkMicrophone();
        
        // 触觉反馈检测
        this.capabilityMatrix.haptic.available = this._checkHaptic();
        
        // Live2D SDK 检测
        this.capabilityMatrix.live2d_sdk.available = this._checkLive2DSDK();
        
        // Live2D 模型检测
        this.capabilityMatrix.live2d_model.available = this._checkLive2DModel();
        
        // WebSocket 检测
        this.capabilityMatrix.websocket.available = this._checkWebSocket();
        
        // localStorage 检测
        this.capabilityMatrix.localStorage.available = this._checkLocalStorage();
        
        // indexedDB 检测
        this.capabilityMatrix.indexedDB.available = this._checkIndexedDB();
        
        // 确定能力状态级别
        this._determineCapabilityState();
        
        return {
            matrix: this.capabilityMatrix,
            state: this.capabilityState
        };
    }
    
    _checkWebGL2() {
        try {
            const canvas = document.createElement('canvas');
            return !!canvas.getContext('webgl2');
        } catch (e) {
            console.warn('[PerformanceManager] WebGL2 check failed:', e);
            return false;
        }
    }
    
    _checkWebGL() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('webgl2'));
        } catch (e) {
            console.warn('[PerformanceManager] WebGL check failed:', e);
            return false;
        }
    }
    
    _checkAudio() {
        try {
            return 'AudioContext' in window || 'webkitAudioContext' in window;
        } catch (e) {
            console.warn('[PerformanceManager] Audio check failed:', e);
            return false;
        }
    }
    
    _checkMicrophone() {
        try {
            return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        } catch (e) {
            console.warn('[PerformanceManager] Microphone check failed:', e);
            return false;
        }
    }
    
    _checkHaptic() {
        try {
            return 'vibrate' in navigator || ('navigator' in navigator);
        } catch (e) {
            console.warn('[PerformanceManager] Haptic check failed:', e);
            return false;
        }
    }
    
    _checkLive2DSDK() {
        try {
            return window.Live2DCubismCore !== undefined && window.Live2DCubismCore !== null;
        } catch (e) {
            console.warn('[PerformanceManager] Live2D SDK check failed:', e);
            return false;
        }
    }
    
    _checkLive2DModel() {
        // 模型检测由Live2DManager执行，这里标记为待检查
        return 'pending';
    }
    
    _checkWebSocket() {
        return 'WebSocket' in window;
    }
    
    _checkLocalStorage() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            console.warn('[PerformanceManager] localStorage check failed:', e);
            return false;
        }
    }
    
    _checkIndexedDB() {
        return 'indexedDB' in window;
    }
    
    /**
     * 确定当前能力状态级别
     */
    /**
     * 更新特定能力的状态
     * @param {string} capability 能力名称
     * @param {boolean} available 是否可用
     */
    updateCapability(capability, available) {
        if (this.capabilityMatrix[capability]) {
            this.capabilityMatrix[capability].available = available;
            console.log(`[PerformanceManager] 更新能力 ${capability}:`, available);
            
            // 重新确定能力状态
            this._determineCapabilityState();
            
            // 根据新的能力状态调整性能模式
            this._adjustModeForCapabilityState();
        }
    }
    
    /**
     * 更新Live2D模型可用性
     * @param {boolean} available 模型是否可用
     */
    updateLive2DModelAvailability(available) {
        this.updateCapability('live2d_model', available);
    }
    
    /**
     * 更新Live2D物理可用性
     * @param {boolean} available 物理是否可用
     */
    updateLive2DPhysicsAvailability(available) {
        this.updateCapability('live2d_physics', available);
    }
    
    /**
     * 更新Live2D唇形同步可用性
     * @param {boolean} available 唇形同步是否可用
     */
    updateLive2DLipsyncAvailability(available) {
        this.updateCapability('live2d_lipsync', available);
    }
    
    /**
     * 获取当前能力状态报告
     * @returns {Object} 能力状态报告
     */
    getCapabilityReport() {
        const report = {
            state: this.capabilityState.complete ? '完整版' : 
                    this.capabilityState.degraded ? '降级版' : '基础版',
            capabilities: {},
            missing: [],
            fallbacks: []
        };
        
        for (const [cap, info] of Object.entries(this.capabilityMatrix)) {
            report.capabilities[cap] = {
                available: info.available,
                required: info.required,
                fallback: info.fallback
            };
            
            if (!info.available && info.available !== 'pending') {
                if (info.required) {
                    report.missing.push({
                        capability: cap,
                        required: true,
                        fallback: info.fallback
                    });
                } else {
                    report.missing.push({
                        capability: cap,
                        required: false,
                        fallback: info.fallback
                    });
                }
            }
        }
        
        report.fallbacks = this.capabilityState.fallbacks_active;
        
        return report;
    }
    
    
    _determineCapabilityState() {
        const missingRequired = [];
        const missingOptional = [];
        const fallbacks = [];
        
        // 检查必需能力
        for (const [cap, info] of Object.entries(this.capabilityMatrix)) {
            if (info.required && !info.available && info.available !== 'pending') {
                missingRequired.push(cap);
                if (info.fallback) {
                    fallbacks.push({ capability: cap, fallback: info.fallback });
                }
            } else if (!info.required && !info.available && info.available !== 'pending') {
                missingOptional.push(cap);
            }
        }
        
        // 确定状态级别
        if (missingRequired.length === 0) {
            this.capabilityState.complete = true;
            this.capabilityState.degraded = false;
            this.capabilityState.basic = false;
        } else if (missingRequired.length > 0 && fallbacks.length > 0) {
            this.capabilityState.complete = false;
            this.capabilityState.degraded = true;
            this.capabilityState.basic = false;
            this.capabilityState.fallbacks_active = fallbacks;
        } else {
            this.capabilityState.complete = false;
            this.capabilityState.degraded = false;
            this.capabilityState.basic = true;
        }
        
        this.capabilityState.missing_caps = [...missingRequired, ...missingOptional];
        
        console.log('[PerformanceManager] 能力状态:',
            this.capabilityState.complete ? '完整版' : 
            this.capabilityState.degraded ? '降级版' : '基础版',
            this.capabilityState.missing_caps.length > 0 ? `缺失能力: ${this.capabilityState.missing_caps.join(', ')}` : '所有能力正常'
        );
    }

    /**
     * 根据能力状态调整推荐模式
     * 根据缺失的能力降低性能模式，确保系统能够运行
     */
    _adjustModeForCapabilityState() {
        if (!this.capabilityState) {
            return;
        }
        
        // 如果是完整版，使用当前推荐模式
        if (this.capabilityState.complete) {
            return;
        }
        
        // 降级版或基础版，降低模式
        if (this.capabilityState.degraded) {
            console.log('[PerformanceManager] 降级模式启用，调整性能配置');
            // 根据缺失能力降低模式
            if (this.currentMode === 'ultra' || this.currentMode === 'high') {
                this.setPerformanceMode('medium');
            }
        } else if (this.capabilityState.basic) {
            console.log('[PerformanceManager] 基础模式启用，使用最低性能配置');
            this.setPerformanceMode('low');
        }
    }
    
    
    async initialize(externalProfile = null) {
        // 检测系统能力并更新能力矩阵
        const capabilityResult = this.detectCapabilities();
        console.log('[PerformanceManager] 能力检测结果:', capabilityResult);
        
        if (externalProfile) {
            // Map HardwareDetector profile format to PerformanceManager format if needed
            this.hardwareProfile = this._mapExternalProfile(externalProfile);
            console.log('Using external hardware profile for PerformanceManager:', this.hardwareProfile);
        } else {
            this.detectHardwareCapabilities();
        }
        
        // 推荐性能模式（基于硬件）
        this.recommendPerformanceMode();
        
        // 根据能力状态调整推荐模式
        this._adjustModeForCapabilityState();
        this.startPerformanceMonitoring();
        
        window.addEventListener('resize', () => this.handleResize());
        
        if (this.websocket && this.websocket.isConnected()) {
            this.websocket.send({
                type: 'hardware_detected',
                profile: this.hardwareProfile,
                recommended_mode: this.currentMode,
                capability_matrix: this.capabilityMatrix,
                capability_state: this.capabilityState,
                timestamp: Date.now()
            });
        }
        
        return {
            hardware: this.hardwareProfile,
            mode: this.currentMode,
            performance: this.performanceModes[this.currentMode],
            capability_matrix: this.capabilityMatrix,
            capability_state: this.capabilityState
        };
    }

    /**
     * Maps profile from HardwareDetector to PerformanceManager's internal format
     * @param {Object} profile External profile from HardwareDetector
     * @returns {Object} Mapped profile
     */
    _mapExternalProfile(profile) {
        // If it's already in the correct format, return it
        if (profile.memory && profile.gpu && profile.cores) {
            return profile;
        }

        // Map from HardwareDetector format
        const gpuName = (profile.gpu_info && profile.gpu_info.name) || 'unknown';
        
        return {
            os: profile.platform || 'unknown',
            browser: this.getBrowserInfo().browser,
            memory: {
                total: profile.ram_gb || 4,
                unit: 'GB',
                estimated: true
            },
            gpu: {
                name: gpuName,
                vendor: (profile.gpu_info && profile.gpu_info.vendor) || 'unknown',
                renderer: (profile.gpu_info && profile.gpu_info.renderer) || 'unknown',
                vram: this.estimateVRAM(gpuName),
                webgl2: profile.gpu_info ? !!profile.gpu_info.version?.includes('WebGL 2') : false
            },
            cores: {
                logical: profile.cpu_cores || 4,
                estimated: false
            },
            device: {
                type: (profile.device_type && profile.device_type.type) || 'desktop',
                width: window.innerWidth,
                height: window.innerHeight,
                pixelRatio: window.devicePixelRatio
            },
            timestamp: Date.now()
        };
    }
    
    detectHardwareCapabilities() {
        const info = this.getBrowserInfo();
        const memory = this.getMemoryInfo();
        const gpu = this.getGPUInfo();
        const cores = this.getCoresInfo();
        const device = this.getDeviceInfo();
        
        this.hardwareProfile = {
            os: info.os,
            browser: info.browser,
            memory: memory,
            gpu: gpu,
            cores: cores,
            device: device,
            timestamp: Date.now()
        };
        
        return this.hardwareProfile;
    }
    
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let os = 'unknown';
        let browser = 'unknown';
        
        if (userAgent.indexOf('Win') !== -1) os = 'windows';
        else if (userAgent.indexOf('Mac') !== -1) os = 'macos';
        else if (userAgent.indexOf('Linux') !== -1) os = 'linux';
        else if (userAgent.indexOf('Android') !== -1) os = 'android';
        else if (userAgent.indexOf('iOS') !== -1) os = 'ios';
        
        if (userAgent.indexOf('Chrome') !== -1 && userAgent.indexOf('Edge') === -1) browser = 'chrome';
        else if (userAgent.indexOf('Safari') !== -1) browser = 'safari';
        else if (userAgent.indexOf('Firefox') !== -1) browser = 'firefox';
        else if (userAgent.indexOf('Edge') !== -1) browser = 'edge';
        
        return { os, browser, userAgent };
    }
    
    getMemoryInfo() {
        return {
            total: navigator.deviceMemory || 8,
            unit: 'GB',
            estimated: navigator.deviceMemory === undefined
        };
    }
    
    getGPUInfo() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        if (!gl) {
            return { name: 'unknown', vendor: 'unknown', renderer: 'software' };
        }
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        
        let name = 'unknown';
        let vendor = 'unknown';
        
        if (debugInfo) {
            vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            name = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        }
        
        const vram = this.estimateVRAM(name);
        
        return {
            name,
            vendor,
            renderer: name,
            vram: vram,
            webgl2: !!canvas.getContext('webgl2')
        };
    }
    
    estimateVRAM(gpuName) {
        const name = gpuName.toLowerCase();
        
        if (name.includes('nvidia')) {
            if (name.includes('rtx') || name.includes('gtx')) {
                if (name.includes('4090') || name.includes('4080')) return 24;
                if (name.includes('4070') || name.includes('4060')) return 12;
                if (name.includes('3080') || name.includes('3090')) return 12;
                if (name.includes('3060') || name.includes('3070')) return 12;
                if (name.includes('2080') || name.includes('2070') || name.includes('2060')) return 8;
                if (name.includes('1080') || name.includes('1070') || name.includes('1060')) return 8;
            }
            return 6;
        }
        
        if (name.includes('amd') || name.includes('radeon')) {
            if (name.includes('rx')) {
                if (name.includes('7900') || name.includes('7800')) return 16;
                if (name.includes('7700') || name.includes('7600')) return 12;
                if (name.includes('6900') || name.includes('6800')) return 16;
                if (name.includes('6700') || name.includes('6600')) return 12;
            }
            return 8;
        }
        
        if (name.includes('intel')) {
            if (name.includes('iris') || name.includes('arc')) return 4;
            if (name.includes('uhd') || name.includes('hd')) return 2;
        }
        
        if (name.includes('apple') && (name.includes('m1') || name.includes('m2') || name.includes('m3'))) {
            return 8;
        }
        
        return 2;
    }
    
    getCoresInfo() {
        return {
            logical: navigator.hardwareConcurrency || 4,
            estimated: navigator.hardwareConcurrency === undefined
        };
    }
    
    getDeviceInfo() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTablet = isMobile && window.innerWidth >= 768;
        
        return {
            type: isTablet ? 'tablet' : (isMobile ? 'mobile' : 'desktop'),
            width: window.innerWidth,
            height: window.innerHeight,
            pixelRatio: window.devicePixelRatio
        };
    }
    
    recommendPerformanceMode() {
        if (!this.hardwareProfile) {
            return 'medium';
        }
        
        const { memory, gpu, cores, device } = this.hardwareProfile;
        
        let score = 0;
        
        score += Math.min(memory.total, 32) * 3;
        score += Math.min(gpu.vram, 24) * 4;
        score += Math.min(cores.logical, 16) * 2;
        
        if (device.type === 'mobile') score *= 0.5;
        if (device.type === 'tablet') score *= 0.7;
        
        let recommendedMode;
        
        if (score < 15) {
            recommendedMode = 'very_low';
        } else if (score < 30) {
            recommendedMode = 'low';
        } else if (score < 50) {
            recommendedMode = 'medium';
        } else if (score < 80) {
            recommendedMode = 'high';
        } else {
            recommendedMode = 'ultra';
        }
        
        this.setPerformanceMode(recommendedMode);
        
        return recommendedMode;
    }
    
    setPerformanceMode(mode) {
        if (!this.performanceModes[mode]) {
            console.warn(`Unknown performance mode: ${mode}`);
            return;
        }
        
        this.currentMode = mode;
        const settings = this.performanceModes[mode];
        
        this.targetFPS = settings.fps;
        this.resolutionScale = settings.resolution;
        this.effectsLevel = settings.effects;
        
        // 根據性能自動推薦桌布模式
        if (this.autoAdjustEnabled) {
            if (mode === 'ultra' || mode === 'high') {
                this.setWallpaperMode('3D');
            } else if (mode === 'medium') {
                this.setWallpaperMode('2.5D');
            } else {
                this.setWallpaperMode('2D');
            }
        }
        
        this.applyPerformanceSettings();
        
        console.log(`Performance mode changed to: ${mode} (${settings.description})`);
    }

    setWallpaperMode(mode) {
        const validModes = ['2D', '2.5D', '3D'];
        if (!validModes.includes(mode)) {
            console.warn(`Unknown wallpaper mode: ${mode}`);
            return;
        }
        
        this.wallpaperMode = mode;
        console.log(`Wallpaper mode set to: ${mode}`);
        
        // 通知桌布處理器更新渲染模式
        const wallpaperHandler = window.wallpaperHandler || (window.angelaApp && window.angelaApp.wallpaperHandler);
        if (wallpaperHandler) {
            wallpaperHandler.setRenderingMode(mode);
        }
        
        // 如果有 WebSocket，通知後端
        if (this.websocket && this.websocket.isConnected()) {
            this.websocket.send({
                type: 'wallpaper_mode_changed',
                mode: mode,
                timestamp: Date.now()
            });
        }
    }
    
    setAngelaMode(mode) {
        if (!this.angelaModes[mode]) {
            console.warn(`Unknown Angela mode: ${mode}`);
            return;
        }
        
        const angelaSettings = this.angelaModes[mode];
        const perfMode = angelaSettings.performance_mode;
        
        this.setPerformanceMode(perfMode);
        this.applyAngelaFeatures(angelaSettings.features);
        
        console.log(`Angela mode changed to: ${mode}`);
    }
    
    _autoConfigureModules() {
        if (!this.hardwareProfile) return;
        
        // 防止短时间内重复执行（500ms内）
        const now = performance.now();
        if (now - this.lastAutoConfigureTime < 500) {
            return;
        }
        this.lastAutoConfigureTime = now;
        
        const ram = this.hardwareProfile.ram_gb || 4;
        const gpu = this.hardwareProfile.gpu_info ? this.hardwareProfile.gpu_info.name : '';
        const level = this.currentMode;
        
        console.log(`Auto-configuring modules for ${level} mode on ${ram}GB RAM...`);
        
        // 視覺模組：極低配置下禁用，或 RAM < 4GB
        const visionEnabled = level !== 'lite' && ram >= 4;
        
        // 音頻模組：基本都開啟，除非極低配置
        const audioEnabled = level !== 'lite' || ram >= 4;
        
        // 觸覺模組：基本都開啟
        const tactileEnabled = true;
        
        // 動作執行：Lite 模式下簡化，但不完全關閉
        const actionEnabled = true;
        
        // 應用變更
        if (window.angelaApp) {
            window.angelaApp.toggleModule('vision', visionEnabled, true);
            window.angelaApp.toggleModule('audio', audioEnabled, true);
            window.angelaApp.toggleModule('tactile', tactileEnabled, true);
            window.angelaApp.toggleModule('action', actionEnabled, true);
        }
    }

    applyPerformanceSettings() {
        if (this.autoAdjustEnabled && this._autoConfigureModules) {
            // 自動配置模組
            this._autoConfigureModules();
        }

        const canvas = document.querySelector('#live2d-canvas');
        if (!canvas) return;
        
        const targetWidth = canvas.clientWidth * this.resolutionScale;
        const targetHeight = canvas.clientHeight * this.resolutionScale;
        
        if (this.live2DManager) {
            this.live2DManager.setResolutionScale(this.resolutionScale);
            this.live2DManager.setEffectsLevel(this.effectsLevel);
        }
        
        document.documentElement.style.setProperty('--resolution-scale', this.resolutionScale);
    }
    
    applyAngelaFeatures(features) {
        if (this.live2DManager) {
            this.live2DManager.setAdvancedAnimations(features.advanced_animations);
            this.live2DManager.setPhysics(features.physics);
            this.live2DManager.setLipSync(features.lip_sync);
        }
    }
    
    startPerformanceMonitoring() {
        if (this.performanceMonitor) {
            cancelAnimationFrame(this.performanceMonitor);
        }
        
        const monitor = (timestamp) => {
            // Skip monitoring when page is hidden
            if (!this.isVisible) {
                this.performanceMonitor = null;
                return;
            }
            
            this.frameCount++;
            
            const elapsed = timestamp - this.lastFrameTime;
            
            if (elapsed >= 1000) {
                this.currentFPS = this.frameCount;
                this.frameCount = 0;
                this.lastFrameTime = timestamp;
                
                this.updateFPSHistory(this.currentFPS);
                
                if (this.autoAdjustEnabled) {
                    this.autoAdjustPerformance();
                }
            }
            
            this.performanceMonitor = requestAnimationFrame(monitor);
        };
        
        this.performanceMonitor = requestAnimationFrame(monitor);
    }
    
    updateFPSHistory(fps) {
        this.fpsHistory.push(fps);
        
        if (this.fpsHistory.length > this.maxFpsHistory) {
            this.fpsHistory.shift();
        }
    }
    
    getAverageFPS() {
        if (this.fpsHistory.length === 0) return 60;
        return this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length;
    }
    
    autoAdjustPerformance() {
        const now = Date.now();
        const avgFPS = this.getAverageFPS();
        const targetFPS = this.targetFPS;
        const ratio = avgFPS / targetFPS;
        
        // Check cooldown - prevent rapid mode changes
        if (now - this.lastModeChangeTime < this.modeChangeCooldown) {
            return;
        }
        
        // Check pending mode change (delayed decision)
        if (this.pendingModeChange) {
            if (now - this.pendingModeChangeTime >= 3000) {
                // Wait 3 seconds before committing to mode change
                const pendingMode = this.pendingModeChange;
                this.pendingModeChange = null;
                
                // Verify conditions still met
                const newAvgFPS = this.getAverageFPS();
                const newRatio = newAvgFPS / this.targetFPS;
                
                if (pendingMode === 'downgrade' && newRatio < 0.85) {
                    this.downgradePerformance();
                } else if (pendingMode === 'upgrade' && newRatio > 1.15) {
                    this.upgradePerformance();
                }
            }
            return;
        }
        
        // Use hysteresis: different thresholds for up vs down
        // Downgrade if FPS is consistently low (< 80% of target for 2 consecutive checks)
        // Upgrade only if FPS is consistently high (> 120% of target for 3 consecutive checks)
        if (ratio < 0.8) {
            // First low reading - set pending downgrade
            this.pendingModeChange = 'downgrade';
            this.pendingModeChangeTime = now;
            console.log(`FPS low (${avgFPS.toFixed(1)}/${targetFPS}), pending downgrade check...`);
        } else if (ratio > 1.2) {
            // First high reading - set pending upgrade
            this.pendingModeChange = 'upgrade';
            this.pendingModeChangeTime = now;
            console.log(`FPS high (${avgFPS.toFixed(1)}/${targetFPS}), pending upgrade check...`);
        } else {
            // Cancel pending change if FPS returns to normal
            this.pendingModeChange = null;
        }
    }
    
    downgradePerformance() {
        const modes = Object.keys(this.performanceModes);
        const currentIndex = modes.indexOf(this.currentMode);
        
        if (currentIndex < modes.length - 1) {
            const newMode = modes[currentIndex + 1];
            console.log(`Performance too low, downgrading from ${this.currentMode} to ${newMode}`);
            this.setPerformanceMode(newMode);
            this.lastModeChangeTime = Date.now();
            this.pendingModeChange = null;
            
            if (this.websocket && this.websocket.isConnected()) {
                this._sendPerformanceChangeWithConfirmation({
                    type: 'performance_change',
                    action: 'downgrade',
                    from: this.currentMode,
                    to: newMode,
                    fps: this.getAverageFPS(),
                    timestamp: Date.now()
                });
            }
        }
    }
    
    upgradePerformance() {
        const modes = Object.keys(this.performanceModes);
        const currentIndex = modes.indexOf(this.currentMode);
        
        if (currentIndex > 0) {
            const newMode = modes[currentIndex - 1];
            console.log(`Performance stable, upgrading from ${this.currentMode} to ${newMode}`);
            this.setPerformanceMode(newMode);
            this.lastModeChangeTime = Date.now();
            this.pendingModeChange = null;
            
            if (this.websocket && this.websocket.isConnected()) {
                this._sendPerformanceChangeWithConfirmation({
                    type: 'performance_change',
                    action: 'upgrade',
                    from: this.currentMode,
                    to: newMode,
                    fps: this.getAverageFPS(),
                    timestamp: Date.now()
                });
            }
        }
    }
    
    handleResize() {
        this.applyPerformanceSettings();
    }
    
    setAutoAdjust(enabled) {
        this.autoAdjustEnabled = enabled;
    }
    
    getPerformanceMetrics() {
        return {
            current_mode: this.currentMode,
            target_fps: this.targetFPS,
            current_fps: this.getAverageFPS(),
            resolution_scale: this.resolutionScale,
            effects_level: this.effectsLevel,
            hardware: this.hardwareProfile,
            history: [...this.fpsHistory]
        };
    }
    
    setTargetFPS(fps) {
        this.targetFPS = Math.max(15, Math.min(144, fps));
    }
    
    setResolutionScale(scale) {
        this.resolutionScale = Math.max(0.5, Math.min(2.0, scale));
        this.applyPerformanceSettings();
    }
    
    setEffectsLevel(level) {
        this.effectsLevel = Math.max(0, Math.min(4, level));
        
        if (this.live2DManager) {
            this.live2DManager.setEffectsLevel(this.effectsLevel);
        }
    }
    
    /**
     * 发送带确认的性能变更消息
     * @param {Object} message 消息内容
     */
    _sendPerformanceChangeWithConfirmation(message) {
        const changeId = `${message.action}_${message.to}_${Date.now()}`;
        const messageWithId = { ...message, changeId };
        
        // 保存待确认的变更
        this._pendingPerformanceChanges.set(changeId, {
            message: messageWithId,
            retryCount: 0,
            timestamp: Date.now()
        });
        
        // 发送消息
        try {
            const sent = this.websocket.send(messageWithId);
            if (!sent) {
                // 发送失败，重试
                console.warn('[PerformanceManager] 性能变更消息发送失败，重试中...');
                setTimeout(() => this._retryPerformanceChange(changeId), 1000);
                return;
            }
            
            // 设置确认超时
            setTimeout(() => {
                if (this._pendingPerformanceChanges.has(changeId)) {
                    console.warn('[PerformanceManager] 性能变更确认超时，重试:', changeId);
                    this._retryPerformanceChange(changeId);
                }
            }, this._changeConfirmationTimeout);
            
        } catch (error) {
            console.error('[PerformanceManager] 发送性能变更消息失败:', error);
            this._retryPerformanceChange(changeId);
        }
    }
    
    /**
     * 重试性能变更消息
     * @param {string} changeId 变更ID
     */
    _retryPerformanceChange(changeId) {
        const pending = this._pendingPerformanceChanges.get(changeId);
        if (!pending) {
            return;
        }
        
        if (pending.retryCount >= this._changeRetryCount) {
            console.error('[PerformanceManager] 性能变更重试次数已达上限:', changeId);
            this._pendingPerformanceChanges.delete(changeId);
            return;
        }
        
        pending.retryCount++;
        
        try {
            const sent = this.websocket.send(pending.message);
            if (sent) {
                console.log('[PerformanceManager] 性能变更消息重试成功:', changeId);
                
                // 重置超时
                setTimeout(() => {
                    if (this._pendingPerformanceChanges.has(changeId)) {
                        this._retryPerformanceChange(changeId);
                    }
                }, this._changeConfirmationTimeout);
            } else {
                setTimeout(() => this._retryPerformanceChange(changeId), 1000);
            }
        } catch (error) {
            console.error('[PerformanceManager] 重试性能变更消息失败:', error);
            setTimeout(() => this._retryPerformanceChange(changeId), 1000);
        }
    }
    
    /**
     * 确认性能变更
     * @param {string} changeId 变更ID
     */
    confirmPerformanceChange(changeId) {
        if (this._pendingPerformanceChanges.has(changeId)) {
            console.log('[PerformanceManager] 性能变更已确认:', changeId);
            this._pendingPerformanceChanges.delete(changeId);
        }
    }
    
    destroy() {
        // 停止性能监控
        if (this.performanceMonitor) {
            cancelAnimationFrame(this.performanceMonitor);
            this.performanceMonitor = null;
        }
        
        // 清理visibilitychange事件监听器
        if (this._visibilityChangeHandler) {
            document.removeEventListener('visibilitychange', this._visibilityChangeHandler);
            this._visibilityChangeHandler = null;
        }
        
        // 清理性能变更确认机制
        this._pendingPerformanceChanges.clear();
    }
}