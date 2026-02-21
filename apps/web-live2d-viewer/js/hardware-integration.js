/**
 * Angela AI - Hardware Detection Integration
 * 
 * 自动选择和集成最佳的硬件检测模块
 */

(function() {
    'use strict';
    
    // 检查是否已存在增强版硬件检测
    if (typeof window.EnhancedHardwareDetector !== 'undefined') {
        console.log('✅ Enhanced Hardware Detector already loaded');
        return;
    }
    
    // 动态加载增强版硬件检测
    function loadEnhancedHardwareDetection() {
        const script = document.createElement('script');
        script.src = 'js/hardware-detection-enhanced.js';
        script.async = true;
        
        script.onload = function() {
            console.log('✅ Enhanced Hardware Detection module loaded successfully');
            
            // 如果应用已初始化，替换硬件检测器
            if (typeof window.AngelaApp !== 'undefined' && window.angelaAppInstance) {
                console.log('🔄 Replacing hardware detector in existing app');
                window.angelaAppInstance.hardwareDetector = new window.EnhancedHardwareDetector();
            }
        };
        
        script.onerror = function() {
            console.warn('⚠️ Failed to load enhanced hardware detection, falling back to standard');
        };
        
        document.head.appendChild(script);
    }
    
    // 检查配置并决定是否加载增强版
    function shouldUseEnhancedDetection() {
        // 检查配置
        if (typeof window.HARDWARE_DETECTION_CONFIG !== 'undefined') {
            return window.HARDWARE_DETECTION_CONFIG.useEnhancedDetection;
        }
        
        // 默认情况下，如果有现代浏览器特性就使用增强版
        return !!(
            navigator.deviceMemory && 
            navigator.hardwareConcurrency && 
            typeof WebGL2RenderingContext !== 'undefined'
        );
    }
    
    // 延迟加载以避免阻塞
    setTimeout(() => {
        if (shouldUseEnhancedDetection()) {
            console.log('🚀 Loading enhanced hardware detection...');
            loadEnhancedHardwareDetection();
        } else {
            console.log('📱 Using standard hardware detection for this device');
        }
    }, 1000);
    
})();

// 硬件兼容性检查工具
window.HardwareCompatibilityChecker = {
    checkIntelIntegrated: function() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        if (!gl) return { supported: false, reason: 'No WebGL support' };
        
        const renderer = gl.getParameter(gl.RENDERER).toLowerCase();
        const vendor = gl.getParameter(gl.VENDOR).toLowerCase();
        
        const isIntel = renderer.includes('intel') || vendor.includes('intel');
        if (!isIntel) return { supported: false, reason: 'Not Intel graphics' };
        
        // 检查基本功能
        const extensions = gl.getSupportedExtensions();
        const requiredExtensions = [
            'OES_texture_float',
            'OES_standard_derivatives',
            'WEBGL_depth_texture'
        ];
        
        const missingExtensions = requiredExtensions.filter(ext => !extensions.includes(ext));
        
        return {
            supported: missingExtensions.length === 0,
            renderer: renderer,
            missingExtensions: missingExtensions,
            performanceTier: this.assessIntelPerformance(renderer)
        };
    },
    
    assessIntelPerformance: function(renderer) {
        const r = renderer.toLowerCase();
        
        if (r.includes('arc')) return 'high';
        if (r.includes('iris xe')) return 'medium-high';
        if (r.includes('iris')) return 'medium';
        if (r.includes('uhd')) return 'low-medium';
        if (r.includes('hd')) return 'low';
        
        return 'very-low';
    },
    
    checkAMDIntegrated: function() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        
        if (!gl) return { supported: false, reason: 'No WebGL support' };
        
        const renderer = gl.getParameter(gl.RENDERER).toLowerCase();
        const vendor = gl.getParameter(gl.VENDOR).toLowerCase();
        
        const isAMD = renderer.includes('amd') || renderer.includes('ati') || vendor.includes('amd');
        if (!isAMD) return { supported: false, reason: 'Not AMD graphics' };
        
        return {
            supported: true,
            renderer: renderer,
            performanceTier: this.assessAMDPerformance(renderer)
        };
    },
    
    assessAMDPerformance: function(renderer) {
        const r = renderer.toLowerCase();
        
        if (r.includes('vega')) return 'medium-high';
        if (r.includes('rdna')) return 'medium-high';
        if (r.includes('gcn')) return 'medium';
        
        return 'low-medium';
    },
    
    getOptimalSettings: function(hardwareType, performanceTier) {
        const settings = {
            intel: {
                'high': { fps: 60, quality: 'high', effects: 5 },
                'medium-high': { fps: 50, quality: 'medium-high', effects: 4 },
                'medium': { fps: 45, quality: 'medium', effects: 3 },
                'low-medium': { fps: 30, quality: 'low-medium', effects: 2 },
                'low': { fps: 30, quality: 'low', effects: 1 }
            },
            amd: {
                'medium-high': { fps: 55, quality: 'medium-high', effects: 4 },
                'medium': { fps: 45, quality: 'medium', effects: 3 },
                'low-medium': { fps: 35, quality: 'low-medium', effects: 2 }
            }
        };
        
        return settings[hardwareType]?.[performanceTier] || { fps: 30, quality: 'low', effects: 1 };
    }
};