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
        
        // 使用一個外部 Promise 來封裝，確保不會因為同步代碼阻塞而無法啟動超時
        return new Promise(async (resolve) => {
            let isResolved = false;

            // 1. 根據設備性能設定動態超時
            const isLowEnd = navigator.hardwareConcurrency <= 2 || (navigator.deviceMemory && navigator.deviceMemory <= 2);
            const timeout = isLowEnd ? 8000 : 5000;
            
            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error(`Hardware detection timed out (${timeout}ms), using fallback`);
                    const fallback = this._getFallbackProfile();
                    this.profile = fallback;
                    this.capabilities = this._assessCapabilities(fallback);
                    resolve(fallback);
                }
            }, timeout);

            try {
                // 2. 執行檢測 (使用 Promise.resolve().then 確保它是非同步開始的)
                const profile = await Promise.resolve().then(async () => {
                    // 檢測 GPU
                    const gpu_info = await this._detectGPU();
                    
                    // 基於 GPU 資訊檢測其他硬體
                    const p = {
                        ram_gb: this._detectRAM(gpu_info),
                        cpu_cores: navigator.hardwareConcurrency || 4,
                        gpu_info: gpu_info,
                        platform: this._detectPlatform(),
                        device_type: this._detectDeviceType()
                    };
                    return p;
                });

                if (!isResolved) {
                    clearTimeout(timeoutId);
                    isResolved = true;
                    this.profile = profile;
                    this.capabilities = this._assessCapabilities(profile);
                    resolve(profile);
                }
            } catch (error) {
                if (!isResolved) {
                    clearTimeout(timeoutId);
                    isResolved = true;
                    console.error('Hardware detection failed, using fallback:', error);
                    const fallback = this._getFallbackProfile();
                    this.profile = fallback;
                    this.capabilities = this._assessCapabilities(fallback);
                    resolve(fallback);
                }
            }
        });
    }

    _getFallbackProfile() {
        return {
            ram_gb: 4.0,
            cpu_cores: 4,
            gpu_info: { available: false, name: 'Fallback GPU' },
            platform: 'Unknown',
            device_type: { type: 'desktop', platform: 'Unknown', is_laptop: false }
        };
    }
    
    _detectRAM(gpuInfo) {
        // 基於瀏覽器 API 的 RAM 估算
        const perf = window.performance;
        
        // 1. 檢查 navigator.deviceMemory (現代瀏覽器)
        if (navigator.deviceMemory) {
            return navigator.deviceMemory;
        }

        // 2. 檢查 memory API 支援度 (Chrome 特有)
        if (perf && perf.memory) {
            return Math.round(perf.memory.jsHeapSizeLimit / (1024 * 1024 * 1024) * 2); 
        }
        
        // 3. 基於 GPU 估算
        if (gpuInfo && gpuInfo.name) {
            const name = gpuInfo.name.toLowerCase();
            if (name.includes('rtx') || name.includes('gtx')) return 16.0;
            if (name.includes('radeon')) return 8.0;
            if (name.includes('intel')) return 8.0;
            if (name.includes('apple') || name.includes('m1') || name.includes('m2') || name.includes('m3')) return 16.0;
        }
        
        // 4. 基於瀏覽器功能
        if (this._hasWebGL2Support()) {
            return 8.0;
        }
        
        return 4.0;
    }
    
    async _detectGPU() {
        return new Promise((resolve) => {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                
                if (!gl) {
                    resolve({ available: false, name: 'No WebGL' });
                    return;
                }
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                let vendor = gl.getParameter(gl.VENDOR);
                let renderer = gl.getParameter(gl.RENDERER);
                let unmaskedRenderer = '';
                let unmaskedVendor = '';

                if (debugInfo) {
                    unmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    unmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
                
                const gpuInfo = {
                    available: true,
                    vendor: unmaskedVendor || vendor,
                    renderer: unmaskedRenderer || renderer,
                    name: this._parseGPUName(unmaskedRenderer || renderer),
                    version: gl.getParameter(gl.VERSION)
                };
                
                console.log('GPU detected:', gpuInfo);
                resolve(gpuInfo);
            } catch (e) {
                console.warn('GPU detection error:', e);
                resolve({ available: false, name: 'Detection Error' });
            }
        });
    }
    
    _parseGPUName(renderer) {
        if (!renderer) {
            return 'Unknown GPU';
        }
        
        const r = renderer.toUpperCase();
        
        // NVIDIA
        if (r.includes('NVIDIA') || r.includes('GEFORCE') || r.includes('RTX')) {
            const match = renderer.match(/RTX\s+\d{4}/i) || renderer.match(/GTX\s+\d{4}/i);
            return match ? match[0] : 'NVIDIA GPU';
        }
        
        // AMD
        if (r.includes('AMD') || r.includes('RADEON')) {
            const match = renderer.match(/RX\s+\d{4}/i);
            return match ? match[0] : 'AMD Radeon';
        }
        
        // Intel
        if (r.includes('INTEL')) {
            if (r.includes('ARC')) return 'Intel Arc';
            if (r.includes('IRIS')) return 'Intel Iris';
            if (r.includes('UHD')) return 'Intel UHD';
            return 'Intel GPU';
        }
        
        // Apple
        if (r.includes('APPLE') || r.includes('M1') || r.includes('M2') || r.includes('M3')) {
            const match = renderer.match(/M[1-3]/i);
            return match ? match[0] : 'Apple Silicon';
        }
        
        return renderer;
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
        return !!canvas.getContext('webgl2');
    }
    
    _hasWebGLSupport() {
        const canvas = document.createElement('canvas');
        return !!canvas.getContext('webgl');
    }
    
    _assessCapabilities(profile) {
        const performanceLevel = this._assessPerformanceLevel(profile);
        
        const capabilities = {
            // 性能等級
            performance_level: performanceLevel,
            // 支援的精確度模式
            precision_mode: this._assessPrecisionMode(performanceLevel),
            // 支援的渲染模式 (2D, 2.5D, 3D)
            wallpaper_mode: this._assessWallpaperMode(profile),
            // 支援的渲染等級
            render_quality: this._assessRenderQuality(performanceLevel),
            // 支援的特效
            effects: this._assessSupportedEffects(performanceLevel),
            // 最大分辨率
            max_resolution: this._assessMaxResolution(performanceLevel),
            // 是否支援物理模擬
            has_physics: this._hasPhysicsSupport(),
            // 是否支援著色器
            has_shaders: this._hasShaderSupport()
        };
        
        return capabilities;
    }

    _assessWallpaperMode(profile) {
        const ram = profile.ram_gb;
        const gpuName = profile.gpu_info.name;
        
        // 3D 模式要求：16GB RAM + 獨立顯卡
        if (ram >= 16 && (gpuName.includes('RTX') || gpuName.includes('Radeon') || gpuName.includes('M'))) {
            return '3D';
        }
        
        // 2.5D 模式要求：8GB RAM
        if (ram >= 8) {
            return '2.5D';
        }
        
        // 預設 2D
        return '2D';
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
    
    _assessPrecisionMode(performanceLevel) {
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
    
    _assessRenderQuality(performanceLevel) {
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
    
    _assessSupportedEffects(performanceLevel) {
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
    
    _assessMaxResolution(performanceLevel) {
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
        
        // 智能性能調整
        const isLowEnd = !profile.gpu_info.available || 
                        profile.cpu_cores <= 2 || 
                        (profile.ram_gb && profile.ram_gb <= 4);
        
        const isHighEnd = profile.gpu_info.available && 
                         profile.cpu_cores >= 6 && 
                         (profile.ram_gb && profile.ram_gb >= 16);
        
        // 根據性能等級設置
        let frameRate, resolution, effects;
        
        if (isLowEnd) {
            frameRate = 30;
            resolution = 0.6;
            effects = 1;
            console.log('檢測到低端配置，應用性能優化');
        } else if (isHighEnd) {
            frameRate = 60;
            resolution = 1.0;
            effects = 3;
            console.log('檢測到高端配置，啟用完整功能');
        } else {
            frameRate = 45;
            resolution = 0.8;
            effects = 2;
            console.log('檢測到中端配置，應用平衡設置');
        }
        
        // 設置幀率
        if (this.live2dManager && this.live2dManager.setFrameRate) {
            this.live2dManager.setFrameRate(frameRate);
        }
        
        // 設置分辨率（通過 Canvas 縮放）
        this._setResolutionScale({ width: window.screen.width * resolution });
        
        // 設置渲染品質
        this._setRenderQuality({ frameRate, quality: effects });
        
        // 設置特效等級
        this._setEffectsLevel(effects);
        
        // 設置動態性能調整參數
        this._configureDynamicAdjustments(isLowEnd, isHighEnd);
    }
    
    _configureDynamicAdjustments(isLowEnd, isHighEnd) {
        // 配置動態調整參數
        this.adjustmentConfig = {
            isLowEnd,
            isHighEnd,
            targetFPS: isLowEnd ? 30 : (isHighEnd ? 60 : 45),
            memoryLimit: isLowEnd ? 100 : (isHighEnd ? 500 : 200), // MB
            cpuThreshold: isLowEnd ? 70 : (isHighEnd ? 90 : 80), // %
            gpuThreshold: isLowEnd ? 80 : (isHighEnd ? 95 : 85)  // %
        };
        
        console.log('性能調整配置:', this.adjustmentConfig);
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
            'very-low': { antialiasing: 'off', shadowQuality: 'low' },
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
