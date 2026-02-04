/**
 * Angela AI - Hardware Detection & Dynamic Performance
 * 
 * 檢測系統硬體能力並動態調整性能參數
 */

class HardwareDetector {
    constructor() {
        this.profile = null;
        this.capabilities = null;
    }
    
    async detect() {
        console.log('Detecting hardware capabilities...');
        
        const profile = {
            // RAM 檢測
            ram_gb: this._detectRAM(),
            // CPU 檢測
            cpu_cores: navigator.hardwareConcurrency || 4,
            // GPU 檢測
            gpu_info: await this._detectGPU(),
            // 系統檢測
            platform: this._detectPlatform(),
            // 設備類型
            device_type: this._detectDeviceType()
        };
        
        this.profile = profile;
        console.log('Hardware detected:', profile);
        
        // 計備能力
        this.capabilities = this._assessCapabilities(profile);
        
        return profile;
    }
    
    _detectRAM() {
        // 基於瀏覽器 API 的 RAM 估算
        // 注意：無法直接獲取確切 RAM，使用性能指標估算
        const performance = performance;
        
        // 檢查 WebGL 支援度
        if (!performance || !performance.memory) {
            return 4.0; // 默認值
        }
        
        // 基於 GPU 估算
        if (this.capabilities && this.capabilities.gpu_name) {
            if (this.capabilities.gpu_name.toLowerCase().includes('intel')) {
                return 8.0;
            } else if (this.capabilities.gpu_name.toLowerCase().includes('nvidia')) {
                return 16.0;
            } else if (this.capabilities.gpu_name.toLowerCase().includes('amd')) {
                return 8.0;
            } else if (this.capabilities.gpu_name.includes('Apple') || this.capabilities.gpu_name.includes('M1') || this.capabilities.gpu_name.includes('M2') || this.capabilities.gpu_name.includes('M3')) {
                return 16.0;
            }
        }
        
        // 基於瀏覽器功能
        if (this._hasWebGL2Support()) {
            return 8.0;
        } else if (this._hasWebGLSupport()) {
            return 4.0;
        }
        
        return 4.0;
    }
    
    async _detectGPU() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        if (!gl) {
            return { available: false, name: null };
        }
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        
        const gpuInfo = {
            available: true,
            vendor: gl.getParameter(gl.VENDOR),
            renderer: gl.getParameter(gl.RENDERER),
            name: this._parseGPUName(debugInfo),
            version: gl.getParameter(gl.VERSION)
        };
        
        console.log('GPU detected:', gpuInfo);
        return gpuInfo;
    }
    
    _parseGPUName(debugInfo) {
        if (!debugInfo) {
            return 'Unknown GPU';
        }
        
        const renderer = debugInfo.unmaskedRenderer || '';
        
        // NVIDIA
        if (renderer.includes('NVIDIA') || renderer.includes('GeForce') || renderer.includes('RTX')) {
            const match = renderer.match(/GeForce (RTX )?\d{4}/);
            if (match) return match[0];
        }
        
        // AMD
        if (renderer.includes('AMD') || renderer.includes('Radeon')) {
            const match = renderer.match(/Radeon\s+(RX\s+)?\d{4}/);
            if (match) return match[0];
        }
        
        // Intel
        if (renderer.includes('Intel')) {
            if (renderer.includes('Arc') || renderer.includes('HD Graphics') || renderer.includes('Iris')) {
                return 'Intel Arc / Iris';
            } else if (renderer.includes('UHD Graphics')) {
                return 'Intel UHD Graphics';
            } else {
                return 'Intel GPU';
            }
        }
        
        // Apple
        if (renderer.includes('Apple') || renderer.includes('M1') || renderer.includes('M2') || renderer.includes('M3')) {
            return renderer.match(/M[1-3]/)?.[0] || 'Apple Silicon';
        }
        
        return debugInfo.renderer || 'Unknown GPU';
    }
    
    _detectPlatform() {
        const userAgent = navigator.userAgent;
        
        if (userAgent.includes('Windows NT 10.0')) return 'Windows 10/11';
        if (userAgent.includes('Windows NT 6.1')) return 'Windows 7';
        if (userAgent.includes('Mac') && userAgent.includes('OS X')) {
            if (navigator.userAgent.includes('Intel') || navigator.userAgent.includes('ppc')) {
                return 'macOS (Intel)';
            }
            if (navigator.userAgent.includes('ARM') || navigator.userAgent.includes('arm64')) {
                return 'macOS (Apple Silicon)';
            }
            return 'macOS (Intel)';
        }
        if (userAgent.includes('Linux')) return 'Linux';
        if (userAgent.includes('Android')) return 'Android';
        if (userAgent.includes('iPhone') || userAgent.includes('iPad')) return 'iOS';
        if (userAgent.includes('CrOS')) return 'ChromeOS';
        
        return 'Unknown';
    }
    
    _detectDeviceType() {
        const platform = this._detectPlatform();
        
        // 檢查是否為筆記本電腦
        const isLaptop = this._isLaptopDevice(platform);
        const isMobile = this._isMobileDevice();
        
        return {
            type: isMobile ? 'mobile' : (isLaptop ? 'laptop' : 'desktop'),
            platform: platform,
            is_laptop: isLaptop
        };
    }
    
    _isLaptopDevice(platform) {
        // 基於觸控和屏幕尺寸
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const hasPointer = window.matchMedia('(pointer: coarse)').matches;
        
        // 小屏幕通常意味筆記本
        const screenWidth = window.screen.width;
        const screenHeight = window.screen.height;
        const isSmallScreen = screenWidth <= 1366 || screenHeight <= 768;
        
        return hasTouch && isSmallScreen && (platform.includes('Windows') || platform.includes('macOS'));
    }
    
    _isMobileDevice() {
        const userAgent = navigator.userAgent;
        const mobileKeywords = ['Mobile', 'Android', 'iPhone', 'iPad', 'Tablet'];
        return mobileKeywords.some(keyword => userAgent.includes(keyword));
    }
    
    _hasWebGL2Support() {
        const canvas = document.createElement('canvas');
        return !!(canvas.getContext('webgl2') === null);
    }
    
    _hasWebGLSupport() {
        const canvas = document.createElement('canvas');
        return !!(canvas.getContext('webgl') === null);
    }
    
    _assessCapabilities(profile) {
        const capabilities = {
            // 性能等級
            performance_level: this._assessPerformanceLevel(profile),
            // 支援的精確度模式
            precision_mode: this._assessPrecisionMode(profile),
            // 支援的渲染等級
            render_quality: this._assessRenderQuality(profile),
            // 支援的特效
            effects: this._assessSupportedEffects(profile),
            // 最大分辨率
            max_resolution: this._assessMaxResolution(profile),
            // 是否支援物理模擬
            has_physics: this._hasPhysicsSupport(),
            // 是否支援著色器
            has_shaders: this._hasShaderSupport()
        };
        
        return capabilities;
    }
    
    _assessPerformanceLevel(profile) {
        const ram = profile.ram_gb;
        const gpuName = profile.gpu_info.name;
        
        // NVIDIA RTX 系列
        if (gpuName.includes('RTX')) {
            if (ram >= 32) return 'ultra';
            if (ram >= 16) return 'high';
            return 'standard';
        }
        
        // Apple Silicon
        if (gpuName.includes('M1') || gpuName.includes('M2') || gpuName.includes('M3')) {
            if (ram >= 16) return 'ultra';
            if (ram >= 8) return 'high';
            return 'standard';
        }
        
        // AMD Radeon
        if (gpuName.includes('Radeon') || gpuName.includes('RX')) {
            if (ram >= 32) return 'high';
            if (ram >= 16) return 'standard';
            if (ram >= 8) return 'lite';
            return 'lite';
        }
        
        // Intel GPU
        if (gpuName.includes('Intel') || gpuName.includes('Arc')) {
            if (ram >= 16) return 'standard';
            if (ram >= 8) return 'lite';
            return 'lite';
        }
        
        // 低端設備
        if (ram < 4) return 'very-low';
        if (ram >= 4 && ram < 8) return 'low';
        
        return 'standard';
    }
    
    _assessPrecisionMode(profile) {
        const performanceLevel = this.capabilities.performance_level;
        const precisionModes = {
            'very-low': 'INT',       // 8-bit integer
            'low': 'DEC1',           // 10-bit decimal
            'lite': 'DEC2',             // 16-bit decimal
            'standard': 'DEC3',          // 32-bit decimal
            'high': 'DEC4',            // 64-bit decimal
            'ultra': 'DEC4+'            // 64-bit decimal with enhancements
        };
        
        return precisionModes[performanceLevel] || precisionModes['standard'];
    }
    
    _assessRenderQuality(profile) {
        const performanceLevel = this.capabilities.performance_level;
        const qualityLevels = {
            'very-low': {
                resolution: '480p',
                frameRate: 30,
                effects: ['basic'],
                antialiasing: 'off'
            },
            'low': {
                resolution: '720p',
                frameRate: 30,
                effects: ['basic', 'bloom'],
                antialiasing: 'fxaa'
            },
            'lite': {
                resolution: '1080p',
                frameRate: 60,
                effects: ['basic', 'bloom', 'shadows'],
                antialiasing: 'msaa'
            },
            'standard': {
                resolution: '1440p',
                frameRate: 60,
                effects: ['bloom', 'shadows', 'ambient-occlusion'],
                antialiasing: 'fxaa'
            },
            'high': {
                resolution: '2160p',
                frameRate: 60,
                effects: ['bloom', 'shadows', 'ambient-occlusion', 'depth-of-field'],
                antialiasing: 'msaa'
            },
            'ultra': {
                resolution: '4K',
                frameRate: 60,
                effects: ['bloom', 'shadows', 'ambient-accuracy', 'depth-of-field', 'global-illumination'],
                antialiasing: 'msaa-4x'
            }
        };
        
        return qualityLevels[performanceLevel] || qualityLevels['standard'];
    }
    
    _assessSupportedEffects(profile) {
        const performanceLevel = this.capabilities.performance_level;
        const effectsByPerformance = {
            'very-low': ['basic'],
            'low': ['basic', 'bloom'],
            'lite': ['basic', 'bloom', 'shadows'],
            'standard': ['bloom', 'shadows', 'ambient-occlusion'],
            'high': ['bloom', 'shadows', 'ambient-occlusion', 'depth-of-field'],
            'ultra': ['bloom', 'shadows', 'ambient-occlusion', 'depth-of-field', 'global-illumination', 'screen-space-reflections']
        };
        
        return effectsByPerformance[performanceLevel] || ['basic'];
    }
    
    _assessMaxResolution(profile) {
        const performanceLevel = this.capabilities.performance_level;
        const resolutionsByPerformance = {
            'very-low': { width: 1280, height: 720 },
            'low': { width: 1920, height: 1080 },
            'lite': { width: 2560, height: 1440 },
            'standard': { width: 3840, height: 2160 },
            'high': { width: 5120, height: 2880 },
            'ultra': { width: 7680, height: 4320 }
        };
        
        return resolutionsByPerformance[performanceLevel] || resolutionsByPerformance['standard'];
    }
    
    _hasPhysicsSupport() {
        // 檢查是否支援物理加速
        return this._hasWebGL2Support();
    }
    
    _hasShaderSupport() {
        return this._hasWebGL2Support();
    }
    
    getRecommendedMode() {
        if (!this.profile || !this.capabilities) {
            return 'standard';
        }
        
        const performanceLevel = this.capabilities.performance_level;
        
        // 基於性能推薦 Angela 模式
        const modeRecommendations = {
            'very-low': 'lite',
            'low': 'lite',
            'lite': 'standard',
            'standard': 'standard',
            'high': 'extended',
            'ultra': 'extended'
        };
        
        return modeRecommendations[performanceLevel] || 'standard';
    }
    
    getOptimalFrameRate() {
        if (!this.capabilities) {
            return 60;
        }
        
        return this.capabilities.render_quality.frameRate;
    }
    
    getOptimalResolution() {
        if (!this.capabilities) {
            return { width: 1440, height: 900 };
        }
        
        return this.capabilities.max_resolution;
    }
}

/**
 * Angela AI - State Matrix Integration
 * 
 * 將後端的 4D 狀態矩陣整合到桌面端
 */

class StateMatrixIntegration {
    constructor(live2dManager) {
        this.live2dManager = live2dManager;
        this.alpha = {
            energy: 50,
            comfort: 50,
            arousal: 50,
            rest_need: 50
        };
        this.beta = {
            curiosity: 50,
            focus: 50,
            confusion: 50,
            learning: 50,
            clarity: 50,
            creativity: 50
        };
        this.gamma = {
            happiness: 50,
            sadness: 0,
            anger: 0,
            fear: 0,
            disgust: 0,
            surprise: 0,
            trust: 50,
            anticipation: 50,
            love: 0,
            calm: 50
        };
        this.delta = {
            attention: 50,
            bond: 50,
            trust: 50,
            presence: 50,
            intimacy: 50,
            engagement: 50
        };
        
        this.influenceMatrix = {
            alpha: { beta: 0.3, gamma: 0.5, delta: 0.2 },
            beta: { alpha: 0.2, gamma: 0.4, delta: 0.3 },
            gamma: { alpha: 0.5, beta: 0.4, delta: 0.6 },
            delta: { alpha: 0.2, beta: 0.3, gamma: 0.4 }
        };
    }
    
    updateFromBackend(stateData) {
        if (!stateData) return;
        
        // 更新各維度
        if (stateData.alpha) {
            this.alpha = { ...this.alpha, ...stateData.alpha };
        }
        if (stateData.beta) {
            this.beta = { ...this.beta, ...stateData.beta };
        }
        if (stateData.gamma) {
            this.gamma = { ...this.gamma, ...stateData.gamma };
        }
        if (stateData.delta) {
            this.delta = { ...this.delta, ...stateData.delta };
        }
        
        // 應狀態更新 Live2D
        this._applyStateToLive2D();
    }
    
    _applyStateToLive2D() {
        if (!this.live2dManager) return;
        
        // 根據情感維度更新表情
        const emotionExpression = this._getEmotionExpression();
        if (emotionExpression) {
            this.live2dManager.setExpression(emotionExpression);
        }
        
        // 根據生理維度更新參數
        this._applyPhysiologicalParameters();
        
        // 根據社交維度更新行為
        this._applyBehavioralParameters();
    }
    
    _getEmotionExpression() {
        if (!this.gamma) return null;
        
        const emotions = this.gamma;
        const emotionValues = {
            happiness: emotions.happiness - (emotions.sadness + emotions.anger + emotions.fear),
            joy: emotions.happiness,
            sadness: emotions.sadness,
            anger: emotions.anger,
            fear: emotions.fear,
            surprise: emotions.surprise
        };
        
        let dominantEmotion = 'neutral';
        let maxEmotionValue = 0;
        
        for (const [emotion, value] of Object.entries(emotionValues)) {
            if (value > maxEmotionValue) {
                maxEmotionValue = value;
                dominantEmotion = emotion;
            }
        }
        
        // 映射到 Live2D 表情
        const emotionMapping = {
            'happiness': 'happy',
            'joy': 'happy',
            'neutral': 'neutral',
            'sadness': 'sad',
            'sad': 'sad',
            'anger': 'anger',
            'fear': 'surprised',
            'surprise': 'surprised'
        };
        
        return emotionMapping[dominantEmotion] || 'neutral';
    }
    
    _applyPhysiologicalParameters() {
        if (!this.live2dManager || !this.alpha) return;
        
        // 根據能量調整呼吸參數
        const energy = this.alpha.energy / 100;
        const arousal = this.alpha.arousal / 100;
        
        // 呼吸參數：能量越高，呼吸越急促
        const breathFrequency = 0.5 + (energy * 1.5) / 100;
        const breathDepth = 0.1 + (arousal * 0.9) / 100;
        
        this.live2dManager.setParameter('ParamBreath', breathFrequency);
        
        // 眼睛開闔度：疲勞時微閉
        const eyeOpenness = Math.max(0.3, 1.0 - (this.alpha.rest_need / 100 * 0.5));
        this.live2dManager.setParameter('ParamEyeLOpen', eyeOpenness);
        this.live2dManager.setParameter('ParamEyeROpen', eyeOpenness);
        
        // 身體放鬆程度
        const bodyRelaxation = 1.0 - (this.alpha.comfort / 100 * 0.3);
        // 身體姿態受影響（需後端協作）
    }
    
    _applyBehavioralParameters() {
        if (!this.live2dManager || !this.delta) return;
        
        // 根據關注度調整眼球追蹤
        const attention = this.delta.attention / 100;
        
        // 根據親密程度調整行為
        const intimacy = this.delta.intimacy / 100;
        
        // 信任程度影響表情開放度
        const trust = this.delta.trust / 100;
        const expressionOpenness = 0.5 + (trust * 0.5);
        
        // 存在感
        const presence = this.delta.presence / 100;
        const bodyActivity = presence > 70 ? 1.0 : 0.5;
        
        // 姿態微調
        const bodyAngleVariation = bodyActivity * 0.1;
        this.live2dManager.setParameter('ParamBodyAngleX', this.live2dManager.getParameter('ParamBodyAngleX') + (Math.random() - 0.5) * bodyAngleVariation);
    }
    
    // 計算維度影響（用於動態調整）
    computeInfluence(source, target) {
        if (!this.influenceMatrix) return 0;
        
        const sourceDimension = this[source.toLowerCase()];
        const influenceStrength = this.influenceMatrix[sourceDimension];
        
        if (!influenceStrength || !influenceStrength[target]) return 0;
        
        return influenceStrength[target];
    }
    
    // 獲取當前狀態（發送到後端）
    getCurrentState() {
        return {
            alpha: this.alpha,
            beta: this.beta,
            gamma: this.gamma,
            delta: this.delta
        };
    }
}

/**
 * Angela AI - Dynamic Performance Manager
 * 
 * 根據硬體能力和使用情況動態調整性能
 */

class DynamicPerformanceManager {
    constructor(live2dManager) {
        this.live2dManager = live2dManager;
        this.hardwareDetector = new HardwareDetector();
        this.currentMode = 'standard';
        this.frameRates = {
            'very-low': 30,
            'low': 30,
            'lite': 60,
            'standard': 60,
            'high': 60,
            'ultra': 60
        };
        this.resolutionScale = 1.0;
        this.renderQuality = 'standard';
        this.enabled = false;
    }
    
    async initialize() {
        console.log('Initializing dynamic performance manager...');
        
        // 檢測硬體
        await this.hardwareDetector.detect();
        
        // 根據硬體設置最佳性能
        this._optimizeForHardware();
        
        // 啟用動態調整
        this.enabled = true;
        this._startMonitoring();
        
        console.log('Dynamic performance manager initialized');
    }
    
    _optimizeForHardware() {
        const profile = this.hardwareDetector.profile;
        const capabilities = this.hardwareDetector.capabilities;
        
        // 根據性能等級設置
        const frameRate = capabilities.render_quality.frameRate;
        const resolution = capabilities.max_resolution;
        
        // 設置幀率
        this.live2dManager.setFrameRate(frameRate);
        
        // 設置分辨率（通過 Canvas 縮放）
        this._setResolutionScale(resolution);
        
        // 設置渲染品質
        this._setRenderQuality(capabilities.render_quality);
        
        // 設置特效等級
        this._setEffectsLevel(capabilities.effects);
    }
    
    _setResolutionScale(resolution) {
        const screenInfo = {
            width: window.screen.width,
            height: window.screen.height,
            devicePixelRatio: window.devicePixelRatio
        };
        
        // �置繪布尺寸匹配最佳分辨率
        if (resolution && resolution.width) {
            this.resolutionScale = Math.min(1.0, screenInfo.width / resolution.width);
        } else {
            this.resolutionScale = 1.0;
        }
        
        console.log(`Resolution scale: ${this.resolutionScale}x`);
    }
    
    setMode(mode) {
        this.currentMode = mode;
        const performanceLevel = this.hardwareDetector.capabilities.performance_level;
        
        const modeConfigs = {
            'lite': {
                frameRate: 30,
                effects: ['basic']
            },
            'standard': {
                frameRate: 60,
                effects: ['basic', 'bloom']
            },
            'extended': {
                frameRate: 60,
                effects: ['bloom', 'shadows', 'ambient-occlusion']
            }
        };
        
        const config = modeConfigs[mode] || modeConfigs['standard'];
        
        this.live2dManager.setFrameRate(config.frameRate);
        this._setEffectsLevel(config.effects);
    }
    
    _setFrameRate(fps) {
        if (this.live2dManager) {
            this.live2dManager.setFrameRate(fps);
        console.log(`Setting frame rate: ${fps} FPS`);
        }
    }
    
    _setRenderQuality(quality) {
        if (!this.live2dManager) return;
        
        const qualityParams = {
            very-low: { antialiasing: 'off', shadowQuality: 'low' },
            low: { antialiasing: 'fxaa', shadowQuality: 'low' },
            lite: { antialiasing: 'msaa', shadowQuality: 'medium' },
            standard: { antialiasing: 'fxaa', shadowQuality: 'high' },
            high: { antialiasing: 'msaa-4x', shadowQuality: 'very-high' },
            ultra: { antialiasing: 'msaa-8x', shadowQuality: 'ultra' }
        };
        
        const params = qualityParams[quality] || qualityParams['standard'];
        this.live2dManager.setRenderQuality(params);
    }
    
    _setEffectsLevel(effects) {
        if (!this.live2dManager) return;
        
        const supportedEffects = this.hardwareDetector.capabilities.effects || ['basic'];
        
        this.live2dManager.setEffects(effects);
    }
    
    _startMonitoring() {
        // 監控性能指標
        this._monitoringInterval = setInterval(() => {
            this._checkPerformanceMetrics();
        }, 5000); // 每 5 秒檢查一次
    }
    
    _checkPerformanceMetrics() {
        // 這裡可以添加：
        // - FPS 監控
        // - 內存監控
        // - GPU 使用率
        console.log('Checking performance metrics...');
    }
    
    stopMonitoring() {
        if (this._monitoringInterval) {
            clearInterval(this._monitoringInterval);
            this._monitoringInterval = null;
        }
    }
    
    // 根據當前使用情況動態調整
    adjustPerformance() {
        if (!this.enabled || !this.hardwareDetector.profile) return;
        
        const currentFPS = this.live2dManager.getCurrentFPS();
        const targetFPS = this.hardwareDetector.capabilities.render_quality.frameRate;
        
        if (currentFPS < targetFPS * 0.8) {
            this._downgradePerformance();
        } else if (currentFPS >= targetFPS * 1.2) {
            this._upgradePerformance();
        }
    }
    
    _downgradePerformance() {
        console.log('Downgrading performance...');
        
        // 降低幀率
        const newFPS = Math.max(30, this.hardwareDetector.capabilities.render_quality.frameRate - 15);
        this.live2dManager.setFrameRate(newFPS);
        
        // 降低特效
        const currentEffects = this.live2dManager.getEffects();
        const reducedEffects = currentEffects.filter(e => e !== 'depth-of-field' && e !== 'screen-space-reflections');
        this.live2D.setEffects(reducedEffects);
    }
    
    _upgradePerformance() {
        console.log('Upgrading performance...');
        
        // 提升幀率
        const maxFPS = this.hardwareDetector.capabilities.render_quality.frameRate;
        this.live2dManager.setFrameRate(maxFPS);
        
        // 啟用更多特效
        const maxEffects = this.hardwareDetector.capabilities.effects;
        this.live2D.setEffects(maxEffects);
    }
}

// 導出到全局
if (typeof window !== 'undefined') {
    window.HardwareDetector = HardwareDetector;
    window.StateMatrixIntegration = StateMatrixIntegration;
    window.DynamicPerformanceManager = DynamicPerformanceManager;
    
    console.log('Hardware Detection and Dynamic Performance modules loaded');
}
