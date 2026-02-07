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
    
    async initialize(externalProfile = null) {
        if (externalProfile) {
            // Map HardwareDetector profile format to PerformanceManager format if needed
            this.hardwareProfile = this._mapExternalProfile(externalProfile);
            console.log('Using external hardware profile for PerformanceManager:', this.hardwareProfile);
        } else {
            this.detectHardwareCapabilities();
        }
        
        this.recommendPerformanceMode();
        this.startPerformanceMonitoring();
        
        window.addEventListener('resize', () => this.handleResize());
        
        if (this.websocket && this.websocket.isConnected()) {
            this.websocket.send({
                type: 'hardware_detected',
                profile: this.hardwareProfile,
                recommended_mode: this.currentMode,
                timestamp: Date.now()
            });
        }
        
        return {
            hardware: this.hardwareProfile,
            mode: this.currentMode,
            performance: this.performanceModes[this.currentMode]
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
        const avgFPS = this.getAverageFPS();
        const targetFPS = this.targetFPS;
        const ratio = avgFPS / targetFPS;
        
        if (ratio < 0.8) {
            this.downgradePerformance();
        } else if (ratio > 1.2) {
            this.upgradePerformance();
        }
    }
    
    downgradePerformance() {
        const modes = Object.keys(this.performanceModes);
        const currentIndex = modes.indexOf(this.currentMode);
        
        if (currentIndex < modes.length - 1) {
            const newMode = modes[currentIndex + 1];
            console.log(`Performance too low, downgrading from ${this.currentMode} to ${newMode}`);
            this.setPerformanceMode(newMode);
            
            if (this.websocket && this.websocket.isConnected()) {
                this.websocket.send({
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
            
            if (this.websocket && this.websocket.isConnected()) {
                this.websocket.send({
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
    
    destroy() {
        if (this.performanceMonitor) {
            cancelAnimationFrame(this.performanceMonitor);
            this.performanceMonitor = null;
        }
    }
}