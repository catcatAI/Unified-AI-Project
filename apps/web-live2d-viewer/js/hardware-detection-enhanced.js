/**
 * Angela AI - Enhanced Hardware Detection
 * 
 * 通用性硬件检测模块，特别优化Intel/AMD核显支持
 * 保持向后兼容性，同时提供更精细的硬件分类
 */

class EnhancedHardwareDetector {
    constructor() {
        this.profile = null;
        this.capabilities = null;
        this.optimizationProfiles = this._getOptimizationProfiles();
    }
    
    async detect() {
        console.log('🔍 Starting enhanced hardware detection...');
        
        return new Promise(async (resolve) => {
            let isResolved = false;
            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error('Hardware detection timed out, using fallback');
                    const fallback = this._getFallbackProfile();
                    this.profile = fallback;
                    this.capabilities = this._assessCapabilities(fallback);
                    resolve(fallback);
                }
            }, 8000); // 增加到8秒超时
            
            try {
                const profile = await Promise.resolve().then(async () => {
                    // 检测GPU（增强版）
                    const gpu_info = await this._detectGPUEnhanced();
                    
                    // 基于GPU信息检测其他硬件
                    const p = {
                        ram_gb: this._detectRAM(gpu_info),
                        cpu_cores: navigator.hardwareConcurrency || 4,
                        gpu_info: gpu_info,
                        platform: this._detectPlatform(),
                        device_type: this._detectDeviceType(),
                        battery_status: await this._detectBatteryStatus(),
                        power_performance: this._assessPowerPerformance()
                    };
                    return p;
                });
                
                if (!isResolved) {
                    clearTimeout(timeoutId);
                    this.profile = profile;
                    this.capabilities = this._assessCapabilities(profile);
                    console.log('✅ Enhanced hardware detection completed:', this.profile);
                    resolve(profile);
                }
            } catch (error) {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    console.error('Hardware detection failed:', error);
                    const fallback = this._getFallbackProfile();
                    this.profile = fallback;
                    this.capabilities = this._assessCapabilities(fallback);
                    resolve(fallback);
                }
            }
        });
    }
    
    async _detectGPUEnhanced() {
        return new Promise((resolve) => {
            try {
                const canvas = document.createElement('canvas');
                // 优先尝试WebGL2
                let gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                
                if (!gl) {
                    resolve({ 
                        available: false, 
                        name: 'No WebGL Support',
                        type: 'unsupported',
                        tier: 'very-low'
                    });
                    return;
                }
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                let vendor = gl.getParameter(gl.VENDOR);
                let renderer = gl.getParameter(gl.RENDERER);
                let version = gl.getParameter(gl.VERSION);
                
                // 获取未屏蔽的信息
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
                    version: version,
                    name: this._parseGPUName(unmaskedRenderer || renderer),
                    type: this._classifyGPUType(unmaskedRenderer || renderer),
                    tier: this._assessGPUTier(unmaskedRenderer || renderer),
                    capabilities: this._assessGPUCapabilities(gl)
                };
                
                console.log('🎮 Enhanced GPU detected:', gpuInfo);
                resolve(gpuInfo);
            } catch (e) {
                console.warn('GPU detection error:', e);
                resolve({ 
                    available: false, 
                    name: 'Detection Error',
                    type: 'error',
                    tier: 'very-low'
                });
            }
        });
    }
    
    _classifyGPUType(renderer) {
        const r = (renderer || '').toUpperCase();
        
        // Intel核显分类
        if (r.includes('INTEL')) {
            if (r.includes('ARC')) return 'intel_arc';          // 独立显卡
            if (r.includes('IRIS XE')) return 'intel_iris_xe';  // 高性能核显
            if (r.includes('IRIS')) return 'intel_iris';        // 中端核显
            if (r.includes('UHD')) return 'intel_uhd';          // 标准核显
            if (r.includes('HD')) return 'intel_hd';            // 入门核显
            return 'intel_integrated';                          // 未知Intel
        }
        
        // AMD核显分类
        if (r.includes('AMD') || r.includes('ATI') || r.includes('RADEON')) {
            if (r.includes('VEGA')) return 'amd_vega';          // 高性能核显
            if (r.includes('RDNA')) return 'amd_rdna';          // 新架构核显
            if (r.includes('GCN')) return 'amd_gcn';            // 旧架构核显
            return 'amd_integrated';                            // 一般AMD核显
        }
        
        // NVIDIA分类
        if (r.includes('NVIDIA') || r.includes('GEFORCE')) {
            if (r.includes('RTX')) return 'nvidia_rtx';         // 光线追踪显卡
            if (r.includes('GTX')) return 'nvidia_gtx';         // 游戏显卡
            return 'nvidia_integrated';                         // GeForce MX系列等
        }
        
        // Apple Silicon
        if (r.includes('APPLE')) return 'apple_silicon';
        
        return 'unknown';
    }
    
    _assessGPUTier(renderer) {
        const r = (renderer || '').toUpperCase();
        const type = this._classifyGPUType(renderer);
        
        // Intel核显分级
        if (type.startsWith('intel')) {
            if (type === 'intel_arc') return 'high';           // 独立显卡级别
            if (type === 'intel_iris_xe') return 'medium';     // 高性能核显
            if (type === 'intel_iris') return 'low-medium';    // 中端核显
            if (type === 'intel_uhd') return 'low';            // 标准核显
            if (type === 'intel_hd') return 'very-low';        // 入门核显
            return 'very-low';                                 // 未知Intel
        }
        
        // AMD核显分级
        if (type.startsWith('amd')) {
            if (type === 'amd_vega' || type === 'amd_rdna') return 'medium-high';
            if (type === 'amd_gcn') return 'medium';
            return 'low-medium';
        }
        
        // NVIDIA分级
        if (type.startsWith('nvidia')) {
            if (type === 'nvidia_rtx') return 'ultra';
            if (type === 'nvidia_gtx') return 'high';
            return 'medium';
        }
        
        // Apple分级
        if (type === 'apple_silicon') return 'high';
        
        return 'very-low';
    }
    
    _assessGPUCapabilities(gl) {
        const capabilities = {
            webgl2: !!gl.canvas.getContext('webgl2'),
            texture_float: !!gl.getExtension('OES_texture_float'),
            texture_half_float: !!gl.getExtension('OES_texture_half_float'),
            vertex_array_object: !!gl.getExtension('OES_vertex_array_object'),
            instanced_arrays: !!gl.getExtension('ANGLE_instanced_arrays'),
            standard_derivatives: !!gl.getExtension('OES_standard_derivatives'),
            depth_texture: !!gl.getExtension('WEBGL_depth_texture'),
            max_texture_size: gl.getParameter(gl.MAX_TEXTURE_SIZE),
            max_renderbuffer_size: gl.getParameter(gl.MAX_RENDERBUFFER_SIZE)
        };
        
        return capabilities;
    }
    
    _parseGPUName(renderer) {
        if (!renderer) return 'Unknown GPU';
        
        const r = renderer.toUpperCase();
        
        // Intel系列
        if (r.includes('INTEL')) {
            // Arc系列
            if (r.includes('ARC')) {
                const arcMatch = renderer.match(/ARC\s[A-Z]?\d{3,4}/i);
                return arcMatch ? arcMatch[0] : 'Intel Arc';
            }
            // Iris Xe系列
            if (r.includes('IRIS XE')) {
                return 'Intel Iris Xe';
            }
            // Iris系列
            if (r.includes('IRIS')) {
                return 'Intel Iris';
            }
            // UHD系列
            if (r.includes('UHD')) {
                const uhdMatch = renderer.match(/UHD\sGRAPHICS\s\d+/i);
                return uhdMatch ? uhdMatch[0] : 'Intel UHD Graphics';
            }
            // HD系列
            if (r.includes('HD')) {
                const hdMatch = renderer.match(/HD\sGRAPHICS\s\d+/i);
                return hdMatch ? hdMatch[0] : 'Intel HD Graphics';
            }
            return 'Intel Integrated Graphics';
        }
        
        // AMD系列
        if (r.includes('AMD') || r.includes('ATI') || r.includes('RADEON')) {
            if (r.includes('VEGA')) return 'AMD Radeon Vega';
            if (r.includes('RDNA')) return 'AMD Radeon RDNA';
            if (r.includes('GCN')) return 'AMD Radeon GCN';
            const rxMatch = renderer.match(/RX\s\d{4}/i);
            return rxMatch ? rxMatch[0] : 'AMD Radeon';
        }
        
        // NVIDIA系列
        if (r.includes('NVIDIA') || r.includes('GEFORCE')) {
            const rtxMatch = renderer.match(/RTX\s\d{4}/i);
            if (rtxMatch) return rtxMatch[0];
            
            const gtxMatch = renderer.match(/GTX\s\d{3,4}/i);
            if (gtxMatch) return gtxMatch[0];
            
            return 'NVIDIA GeForce';
        }
        
        // Apple系列
        if (r.includes('APPLE')) {
            const appleMatch = renderer.match(/M[1-3]/i);
            return appleMatch ? `${appleMatch[0]} GPU` : 'Apple GPU';
        }
        
        return renderer;
    }
    
    _assessCapabilities(profile) {
        const performanceLevel = this._assessPerformanceLevel(profile);
        const gpuTier = profile.gpu_info.tier;
        const gpuType = profile.gpu_info.type;
        
        const capabilities = {
            // 性能等级
            performance_level: performanceLevel,
            // 精确度模式
            precision_mode: this._assessPrecisionMode(performanceLevel, gpuType),
            // 壁纸模式
            wallpaper_mode: this._assessWallpaperMode(profile, gpuType),
            // 渲染质量
            render_quality: this._assessRenderQuality(performanceLevel, gpuTier),
            // 支持的特效
            effects: this._assessSupportedEffects(performanceLevel, gpuType),
            // 最大分辨率
            max_resolution: this._assessMaxResolution(performanceLevel, gpuTier),
            // 物理模拟支持
            has_physics: this._hasPhysicsSupport(gpuTier),
            // 着色器支持
            has_shaders: this._hasShaderSupport(gpuTier),
            // 电池优化
            battery_optimized: this._isBatteryOptimized(profile),
            // 专用优化配置
            optimization_profile: this._getDeviceOptimizationProfile(profile)
        };
        
        return capabilities;
    }
    
    _assessWallpaperMode(profile, gpuType) {
        const ram = profile.ram_gb;
        const tier = profile.gpu_info.tier;
        
        // 针对核显的特殊处理
        if (gpuType.includes('intel') || gpuType.includes('amd')) {
            // Intel/AMD核显优化
            if (tier === 'high' || tier === 'medium-high') {
                if (ram >= 16) return '2.5D';
                if (ram >= 8) return '2D-enhanced';
                return '2D';
            }
            
            if (tier === 'medium') {
                if (ram >= 12) return '2D-enhanced';
                return '2D';
            }
            
            // 低端核显
            return '2D';
        }
        
        // 独立显卡逻辑（保持原有）
        if (ram >= 16 && (tier === 'ultra' || tier === 'high')) {
            return '3D';
        }
        
        if (ram >= 8) {
            return '2.5D';
        }
        
        return '2D';
    }
    
    _assessPerformanceLevel(profile) {
        const ram = profile.ram_gb;
        const gpuTier = profile.gpu_info.tier;
        const cpuCores = profile.cpu_cores;
        
        // 综合评分系统
        let score = 0;
        
        // RAM贡献 (最大40分)
        if (ram >= 32) score += 40;
        else if (ram >= 16) score += 30;
        else if (ram >= 8) score += 20;
        else if (ram >= 4) score += 10;
        
        // GPU贡献 (最大40分)
        const gpuScores = {
            'ultra': 40, 'high': 35, 'medium-high': 30, 'medium': 25,
            'low-medium': 20, 'low': 15, 'very-low': 10
        };
        score += gpuScores[gpuTier] || 10;
        
        // CPU贡献 (最大20分)
        if (cpuCores >= 8) score += 20;
        else if (cpuCores >= 4) score += 15;
        else if (cpuCores >= 2) score += 10;
        else score += 5;
        
        // 根据总分确定性能等级
        if (score >= 85) return 'ultra';
        if (score >= 70) return 'high';
        if (score >= 55) return 'standard';
        if (score >= 40) return 'lite';
        if (score >= 25) return 'low';
        return 'very-low';
    }
    
    _isBatteryOptimized(profile) {
        // 笔记本电脑且使用电池时启用节能模式
        return profile.device_type === 'laptop' && 
               profile.battery_status?.charging === false &&
               profile.battery_status?.level < 0.5;
    }
    
    _getDeviceOptimizationProfile(profile) {
        // 为不同设备类型提供专用优化配置
        const profiles = {
            laptop_intel: {
                target_fps: 45,
                quality_preset: 'balanced',
                power_saving: true,
                thermal_throttling: true
            },
            laptop_amd: {
                target_fps: 50,
                quality_preset: 'performance',
                power_saving: true,
                compute_optimized: true
            },
            desktop_high_end: {
                target_fps: 60,
                quality_preset: 'quality',
                power_saving: false,
                ray_tracing: true
            },
            default: {
                target_fps: 30,
                quality_preset: 'performance',
                power_saving: false,
                basic_features: true
            }
        };
        
        // 根据设备特征选择配置文件
        if (profile.device_type === 'laptop') {
            if (profile.gpu_info.type.includes('intel')) {
                return profiles.laptop_intel;
            }
            if (profile.gpu_info.type.includes('amd')) {
                return profiles.laptop_amd;
            }
        }
        
        if (profile.device_type === 'desktop' && 
            ['ultra', 'high'].includes(profile.gpu_info.tier)) {
            return profiles.desktop_high_end;
        }
        
        return profiles.default;
    }
    
    _getFallbackProfile() {
        return {
            ram_gb: 8,
            cpu_cores: 4,
            gpu_info: {
                available: true,
                name: 'Generic GPU',
                type: 'unknown',
                tier: 'low',
                capabilities: {}
            },
            platform: 'Unknown',
            device_type: 'desktop',
            battery_status: null,
            power_performance: 'balanced'
        };
    }
    
    // 保留原有接口以确保兼容性
    _detectRAM(gpu_info) {
        try {
            return navigator.deviceMemory || 8; // 默认8GB
        } catch {
            return 8;
        }
    }
    
    _detectPlatform() {
        const ua = navigator.userAgent;
        if (ua.includes('Windows')) return 'Windows';
        if (ua.includes('Mac')) return 'macOS';
        if (ua.includes('Linux')) return 'Linux';
        return 'Unknown';
    }
    
    _detectDeviceType() {
        // 简单的设备类型检测
        const ua = navigator.userAgent;
        if (ua.includes('Mobile') || ua.includes('Android') || ua.includes('iPhone')) {
            return 'mobile';
        }
        return 'desktop'; // 默认桌面设备
    }
    
    async _detectBatteryStatus() {
        try {
            if (navigator.getBattery) {
                const battery = await navigator.getBattery();
                return {
                    charging: battery.charging,
                    level: battery.level,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            }
        } catch (e) {
            console.warn('Battery detection not available');
        }
        return null;
    }
    
    _assessPowerPerformance() {
        // 简单的电源性能评估
        return 'balanced';
    }
    
    _assessPrecisionMode(performanceLevel, gpuType) {
        // 根据硬件类型调整精度模式
        if (gpuType.includes('intel') || gpuType.includes('amd')) {
            // 核显通常更适合中等精度
            return performanceLevel === 'ultra' ? 'DEC2' : 'INT';
        }
        return performanceLevel === 'ultra' ? 'DEC4' : 
               performanceLevel === 'high' ? 'DEC2' : 'INT';
    }
    
    _assessRenderQuality(performanceLevel, gpuTier) {
        const qualityLevels = {
            'very-low': { resolution: '480p', frameRate: 30, effects: ['basic'] },
            'low': { resolution: '720p', frameRate: 30, effects: ['basic', 'bloom'] },
            'lite': { resolution: '1080p', frameRate: 45, effects: ['basic', 'bloom', 'shadows'] },
            'standard': { resolution: '1080p', frameRate: 60, effects: ['bloom', 'shadows'] },
            'high': { resolution: '1440p', frameRate: 60, effects: ['bloom', 'shadows', 'ambient-occlusion'] },
            'ultra': { resolution: '2160p', frameRate: 60, effects: ['full'] }
        };
        
        // 核显优化：降低分辨率但保持流畅度
        if (gpuTier.includes('intel') || gpuTier.includes('amd')) {
            const base = qualityLevels[performanceLevel] || qualityLevels.standard;
            return {
                ...base,
                resolution: performanceLevel === 'ultra' ? '1440p' : base.resolution,
                frameRate: Math.min(base.frameRate, 60)
            };
        }
        
        return qualityLevels[performanceLevel] || qualityLevels.standard;
    }
    
    _assessSupportedEffects(performanceLevel, gpuType) {
        const baseEffects = ['basic'];
        
        if (performanceLevel === 'very-low') return baseEffects;
        if (performanceLevel === 'low') return [...baseEffects, 'bloom'];
        if (performanceLevel === 'lite') return [...baseEffects, 'bloom', 'shadows'];
        
        // 核显优化：选择性启用特效
        if (gpuType.includes('intel') || gpuType.includes('amd')) {
            if (performanceLevel === 'standard') return [...baseEffects, 'bloom', 'shadows'];
            if (performanceLevel === 'high') return [...baseEffects, 'bloom', 'shadows', 'ambient-occlusion'];
            if (performanceLevel === 'ultra') return [...baseEffects, 'bloom', 'shadows', 'ambient-occlusion', 'depth-of-field'];
        } else {
            // 独立显卡：启用更多特效
            if (performanceLevel === 'standard') return [...baseEffects, 'bloom', 'shadows', 'ambient-occlusion'];
            if (performanceLevel === 'high') return [...baseEffects, 'bloom', 'shadows', 'ambient-occlusion', 'depth-of-field'];
            if (performanceLevel === 'ultra') return [...baseEffects, 'bloom', 'shadows', 'ambient-occlusion', 'depth-of-field', 'global-illumination'];
        }
        
        return baseEffects;
    }
    
    _assessMaxResolution(performanceLevel, gpuTier) {
        const resolutions = {
            'very-low': '720p',
            'low': '1080p',
            'lite': '1080p',
            'standard': '1440p',
            'high': '2160p',
            'ultra': '4K'
        };
        
        // 核显限制：最高2K
        if (gpuTier.includes('intel') || gpuTier.includes('amd')) {
            const res = resolutions[performanceLevel] || '1080p';
            if (res === '4K') return '2160p';
            if (res === '2160p') return '1440p';
            return res;
        }
        
        return resolutions[performanceLevel] || '1080p';
    }
    
    _hasPhysicsSupport(gpuTier) {
        return !gpuTier.includes('very-low');
    }
    
    _hasShaderSupport(gpuTier) {
        return gpuTier !== 'very-low';
    }
    
    _getOptimizationProfiles() {
        return {
            intel_integrated: {
                fps_target: 45,
                quality_bias: 'performance',
                memory_limit: 2048,
                effect_limit: 3
            },
            amd_integrated: {
                fps_target: 50,
                quality_bias: 'balanced',
                memory_limit: 2048,
                effect_limit: 4
            },
            nvidia_dedicated: {
                fps_target: 60,
                quality_bias: 'quality',
                memory_limit: 4096,
                effect_limit: 6
            }
        };
    }
}

// 保持向后兼容性
window.EnhancedHardwareDetector = EnhancedHardwareDetector;