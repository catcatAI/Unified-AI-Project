/**
 * Angela AI - Hardware Detection Configuration
 * 
 * 配置文件，控制使用哪个硬件检测模块
 */

// 配置硬件检测模块的优先级
const HARDWARE_DETECTION_CONFIG = {
    // 是否使用增强版硬件检测
    useEnhancedDetection: true,
    
    // 回退到标准检测的时间（毫秒）
    fallbackTimeout: 5000,
    
    // 支持的硬件类型优化
    hardwareOptimizations: {
        intel_integrated: {
            name: "Intel核显优化",
            enabled: true,
            features: ["power_saving", "resolution_scaling", "effect_limiting"]
        },
        amd_integrated: {
            name: "AMD核显优化", 
            enabled: true,
            features: ["compute_optimization", "memory_efficiency", "shader_enhancement"]
        },
        nvidia_dedicated: {
            name: "NVIDIA独显优化",
            enabled: true,
            features: ["ray_tracing", "high_precision", "full_effects"]
        },
        laptop_battery: {
            name: "笔记本电池优化",
            enabled: true,
            features: ["fps_limiting", "quality_downscaling", "power_management"]
        }
    },
    
    // 性能等级映射
    performanceMapping: {
        'very-low': { fps: 30, quality: 'low', effects: 1 },
        'low': { fps: 30, quality: 'medium', effects: 2 },
        'lite': { fps: 45, quality: 'medium', effects: 3 },
        'standard': { fps: 60, quality: 'high', effects: 4 },
        'high': { fps: 60, quality: 'high', effects: 5 },
        'ultra': { fps: 60, quality: 'ultra', effects: 6 }
    }
};

// 硬件兼容性矩阵
const HARDWARE_COMPATIBILITY_MATRIX = {
    // Intel核显支持矩阵
    intel: {
        'iris xe': { min_ram: 8, max_resolution: '1440p', supported_effects: 4 },
        'uhd': { min_ram: 4, max_resolution: '1080p', supported_effects: 3 },
        'hd': { min_ram: 4, max_resolution: '720p', supported_effects: 2 },
        'arc': { min_ram: 16, max_resolution: '4K', supported_effects: 6 }
    },
    
    // AMD核显支持矩阵
    amd: {
        'vega': { min_ram: 8, max_resolution: '1440p', supported_effects: 5 },
        'rdna': { min_ram: 8, max_resolution: '2160p', supported_effects: 5 },
        'gcn': { min_ram: 6, max_resolution: '1080p', supported_effects: 3 }
    },
    
    // 通用兼容性规则
    general: {
        min_vram_for_3d: 2048,      // 3D模式最小显存要求
        min_ram_for_hd: 6,          // 高清渲染最小内存
        battery_saving_threshold: 0.3 // 电池电量低于30%时启用节能
    }
};

// 导出配置
window.HARDWARE_DETECTION_CONFIG = HARDWARE_DETECTION_CONFIG;
window.HARDWARE_COMPATIBILITY_MATRIX = HARDWARE_COMPATIBILITY_MATRIX;