/**
 * Angela AI - System Profile & Hardware Management
 * 
 * Consolidated module for hardware detection, performance profiling, 
 * and system resource monitoring.
 */

class SystemProfileManager {
    constructor() {
        this.profile = null;
        this.capabilities = null;
        this.metrics = {
            cpu: 0,
            memory: 0,
            gpu: 0
        };
        this.isInitialized = false;
    }

    /**
     * Initialize system profile by detecting hardware and starting monitoring
     */
    async initialize() {
        if (this.isInitialized) return;
        
        console.log('[SystemProfile] Initializing system profile...');
        
        // 1. Detect hardware (Core profile)
        this.profile = await this._detectHardware();
        
        // 2. Assess capabilities
        this.capabilities = this._assessCapabilities(this.profile);
        
        this.isInitialized = true;
        console.log('[SystemProfile] Profile initialized:', this.profile);
        
        return this.profile;
    }

    /**
     * Get current system metrics (CPU, RAM, etc.)
     * Prefers data from backend if available
     */
    async getMetrics() {
        // In a real implementation, this would fetch from Electron main process
        // which in turn might fetch from the Python backend's resource manager.
        if (window.electronAPI && window.electronAPI.performance) {
            // Placeholder: this IPC would be implemented in main.js
            // this.metrics = await window.electronAPI.performance.getMetrics();
        }
        return this.metrics;
    }

    /**
     * Internal hardware detection (Browser-based fallback)
     */
    async _detectHardware() {
        const gpuInfo = await this._detectGPU();
        
        return {
            cpu_cores: navigator.hardwareConcurrency || 4,
            memory_gb: navigator.deviceMemory || 8,
            gpu: gpuInfo,
            platform: navigator.platform,
            userAgent: navigator.userAgent,
            timestamp: Date.now()
        };
    }

    async _detectGPU() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (!gl) return { name: 'Unknown', vendor: 'Unknown' };

        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            return {
                vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL),
                name: this._parseGPUName(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL))
            };
        }
        return { name: 'Generic WebGL', vendor: gl.getParameter(gl.VENDOR) };
    }

    _parseGPUName(renderer) {
        if (!renderer) return 'Unknown';
        const r = renderer.toUpperCase();
        if (r.includes('RTX')) return 'NVIDIA RTX Series';
        if (r.includes('GTX')) return 'NVIDIA GTX Series';
        if (r.includes('RADEON')) return 'AMD Radeon';
        if (r.includes('INTEL')) return 'Intel Graphics';
        if (r.includes('APPLE')) return 'Apple Silicon';
        return renderer;
    }

    _assessCapabilities(profile) {
        const cpu = profile.cpu_cores;
        const mem = profile.memory_gb;
        
        let tier = 'standard';
        if (cpu >= 8 && mem >= 16) tier = 'high';
        else if (cpu <= 2 || mem <= 4) tier = 'lite';
        
        return {
            tier: tier,
            maxFPS: tier === 'high' ? 120 : (tier === 'standard' ? 60 : 30),
            renderQuality: tier === 'high' ? 'ultra' : (tier === 'standard' ? 'high' : 'medium'),
            physicsPrecision: tier === 'high' ? 2 : 1
        };
    }

    getRecommendedSettings() {
        if (!this.capabilities) return {};
        return {
            frameRate: this.capabilities.maxFPS,
            renderQuality: this.capabilities.renderQuality,
            autoSwitch: this.capabilities.tier === 'lite'
        };
    }
}

// Export singleton
const systemProfile = new SystemProfileManager();
if (typeof module !== 'undefined' && module.exports) {
    module.exports = systemProfile;
} else {
    window.systemProfile = systemProfile;
}
