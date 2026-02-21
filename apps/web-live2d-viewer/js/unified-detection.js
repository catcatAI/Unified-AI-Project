/**
 * Angela AI - Unified Detection System
 * 
 * Integrates: Hardware Detection, Driver Detection, Availability Management
 * Provides: Real-time monitoring, health scoring, auto-recovery
 */

class UnifiedDetectionSystem {
    constructor(options = {}) {
        // Subsystems
        this.hardwareDetector = null;
        this.driverDetector = null;
        this.availabilityManager = null;
        
        // Configuration
        this.checkInterval = options.checkInterval || 15000;
        this.autoRecoveryEnabled = options.autoRecovery !== false;
        
        // State
        this.isInitialized = false;
        this.isMonitoring = false;
        
        // Cache
        this.statusCache = null;
        this.cacheTime = 0;
        this.cacheDuration = 5000; // 5 seconds
        
        // Event callbacks
        this.onStatusChange = null;
        this.onHealthChange = null;
        this.onAlert = null;
        this.onRecovery = null;
    }

    /**
     * Initialize the unified detection system
     */
    async initialize() {
        console.log('[UnifiedDetection] Initializing...');
        
        try {
            // Initialize hardware detector (HardwareDetector uses detect() method, not initialize())
            if (typeof HardwareDetector !== 'undefined') {
                this.hardwareDetector = new HardwareDetector();
                await this.hardwareDetector.detect();
            }

            // Initialize driver detector
            if (typeof DriverDetector !== 'undefined') {
                this.driverDetector = new DriverDetector();
                await this.driverDetector.initialize();
            }

            // Initialize availability manager
            this.availabilityManager = new AvailabilityManager({
                checkInterval: this.checkInterval,
                enableAutoRecovery: this.autoRecoveryEnabled
            });

            // Register subsystems
            this._registerSubsystems();
            
            // Start monitoring
            await this.availabilityManager.initialize();
            
            this.isInitialized = true;
            console.log('[UnifiedDetection] Initialization complete');
            
            return this.getFullStatus();
            
        } catch (error) {
            console.error('[UnifiedDetection] Initialization error:', error);
            return this.getFullStatus();
        }
    }

    /**
     * Register subsystems with availability manager
     */
    _registerSubsystems() {
        if (!this.availabilityManager) return;

        // Hardware subsystem
        this.availabilityManager.registerSubsystem(
            'hardware',
            () => this._checkHardware(),
            () => this._recoverHardware()
        );

        // Driver subsystem
        this.availabilityManager.registerSubsystem(
            'driver',
            () => this._checkDrivers(),
            () => this._recoverDrivers()
        );

        // Performance subsystem
        this.availabilityManager.registerSubsystem(
            'performance',
            () => this._checkPerformance(),
            () => this._recoverPerformance()
        );

        // Memory subsystem
        this.availabilityManager.registerSubsystem(
            'memory',
            () => this._checkMemory(),
            () => this._recoverMemory()
        );

        // WebGL subsystem
        this.availabilityManager.registerSubsystem(
            'webgl',
            () => this._checkWebGL(),
            null
        );
    }

    /**
     * Check hardware status
     */
    async _checkHardware() {
        if (!this.hardwareDetector) {
            return { status: 'unknown', message: 'Hardware detector not initialized' };
        }

        // HardwareDetector uses .profile property, not getHardwareStatus()
        const profile = this.hardwareDetector.profile || {};
        
        return {
            status: 'healthy',
            cores: profile.cpu_cores || navigator.hardwareConcurrency || 4,
            memory: profile.ram_gb || navigator.deviceMemory || 8,
            gpu: profile.gpu_info?.renderer || 'Unknown',
            platform: profile.platform || 'Unknown',
            score: 70
        };
    }

    /**
     * Calculate hardware health score
     */
    _calculateHardwareScore(status) {
        let score = 100;
        
        // Memory impact
        if (status.memory?.total < 4) score -= 30;
        else if (status.memory?.total < 8) score -= 15;
        
        // CPU impact
        if (!status.cpu?.cores || status.cpu.cores < 2) score -= 20;
        else if (status.cpu.cores < 4) score -= 10;
        
        // GPU impact
        if (!status.gpu?.renderer) score -= 20;
        else if (status.gpu.tier === 'low' || status.gpu.tier === 'very-low') score -= 15;
        
        return Math.max(0, Math.min(100, score));
    }

    /**
     * Check driver status
     */
    async _checkDrivers() {
        if (!this.driverDetector) {
            return { status: 'unknown', message: 'Driver detector not initialized' };
        }

        const driverStatus = this.driverDetector.getDriverStatus();
        const health = driverStatus.overallHealth || 'unknown';
        
        return {
            status: health === 'healthy' ? 'healthy' : 'degraded',
            gpu: driverStatus.gpu?.status,
            audio: driverStatus.audio?.status,
            input: driverStatus.input?.status,
            network: driverStatus.network?.status,
            score: health === 'healthy' ? 100 : health === 'warning' ? 70 : 40
        };
    }

    /**
     * Check performance status
     */
    async _checkPerformance() {
        const result = {
            status: 'healthy',
            fps: 60,
            frameTime: 16.67,
            memory: 0,
            score: 100
        };

        // Get performance metrics
        if (performance.now) {
            const perfNow = performance.now();
            result.fps = Math.round(1000 / (perfNow - (this._lastFrameTime || perfNow)));
            this._lastFrameTime = perfNow;
        }

        // Memory
        if (performance.memory) {
            const usedMB = Math.round(performance.memory.usedJSHeapSize / 1048576);
            const limitMB = Math.round(performance.memory.jsHeapSizeLimit / 1048576);
            result.memory = usedMB;
            result.memoryLimit = limitMB;
            
            // Memory impact on score
            if (usedMB / limitMB > 0.9) {
                result.status = 'critical';
                result.score = 20;
            } else if (usedMB / limitMB > 0.7) {
                result.status = 'degraded';
                result.score = 60;
            }
        }

        return result;
    }

    /**
     * Check memory status
     */
    async _checkMemory() {
        const result = {
            status: 'healthy',
            used: 0,
            total: 0,
            limit: 0,
            percentage: 0
        };

        if (performance.memory) {
            result.used = Math.round(performance.memory.usedJSHeapSize / 1048576);
            result.total = Math.round(performance.memory.totalJSHeapSize / 1048576);
            result.limit = Math.round(performance.memory.jsHeapSizeLimit / 1048576);
            result.percentage = Math.round((result.used / result.limit) * 100);
            
            if (result.percentage > 90) {
                result.status = 'critical';
            } else if (result.percentage > 70) {
                result.status = 'degraded';
            }
        } else {
            result.status = 'unknown';
        }

        return result;
    }

    /**
     * Check WebGL status
     */
    async _checkWebGL() {
        const result = {
            status: 'healthy',
            webgl2: false,
            webgl1: false,
            extensions: 0,
            vendor: null,
            renderer: null
        };

        try {
            const canvas = document.createElement('canvas');
            
            // Check WebGL 2
            const gl2 = canvas.getContext('webgl2');
            result.webgl2 = !!gl2;
            
            // Check WebGL 1
            const gl1 = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            result.webgl1 = !!gl1;
            
            const gl = gl2 || gl1;
            if (gl) {
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    result.vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    result.renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
                
                result.extensions = gl.getSupportedExtensions()?.length || 0;
                
                // Check for required Live2D extensions
                const required = ['OES_element_index_uint'];
                const missing = required.filter(ext => !gl.getExtension(ext));
                
                if (missing.length > 0) {
                    result.status = 'degraded';
                    result.missingExtensions = missing;
                    result.recommendation = 'Some WebGL extensions are missing. Live2D may run in compatibility mode.';
                }
            } else {
                result.status = 'critical';
                result.error = 'WebGL not supported';
            }
            
        } catch (error) {
            result.status = 'error';
            result.error = error.message;
        }

        return result;
    }

    /**
     * Recovery actions
     */
    async _recoverHardware() {
        console.log('[UnifiedDetection] Attempting hardware recovery...');
        // Hardware recovery is limited - mainly logging and alerting
        return true;
    }

    async _recoverDrivers() {
        console.log('[UnifiedDetection] Attempting driver recovery...');
        // Driver recovery would trigger driver update checks
        if (this.driverDetector) {
            await this.driverDetector.checkForUpdates();
        }
        return true;
    }

    async _recoverPerformance() {
        console.log('[UnifiedDetection] Attempting performance recovery...');
        // Clear caches if available
        if (window.clearCaches) {
            window.clearCaches();
        }
        return true;
    }

    async _recoverMemory() {
        console.log('[UnifiedDetection] Attempting memory recovery...');
        // Suggest garbage collection
        if (window.gc) {
            window.gc();
        }
        return true;
    }

    /**
     * Get full system status (cached)
     */
    getFullStatus() {
        // Return cached status if still valid
        const now = Date.now();
        if (this.statusCache && (now - this.cacheTime) < this.cacheDuration) {
            return this.statusCache;
        }

        const status = {
            timestamp: new Date(),
            isInitialized: this.isInitialized,
            isMonitoring: this.isMonitoring,
            
            // Hardware - HardwareDetector uses .profile property
            hardware: this.hardwareDetector?.profile || null,
            
            // Drivers
            drivers: this.driverDetector?.getDriverStatus?.() || null,
            
            // Availability
            availability: this.availabilityManager?.getAvailabilityStatus?.() || null,
            
            // Quick status
            quickStatus: this._getQuickStatus()
        };

        this.statusCache = status;
        this.cacheTime = now;
        
        return status;
    }

    /**
     * Get quick status for UI
     */
    _getQuickStatus() {
        const availability = this.availabilityManager?.getQuickStatus();
        
        return {
            healthy: availability?.healthy ?? false,
            state: availability?.state ?? 'initializing',
            score: availability?.score ?? 0,
            icon: availability?.icon ?? '?',
            color: availability?.color ?? '#94a3b8'
        };
    }

    /**
     * Perform full diagnostic
     */
    async runDiagnostics() {
        console.log('[UnifiedDetection] Running diagnostics...');
        
        const results = {
            timestamp: new Date(),
            hardware: null,
            drivers: null,
            availability: null,
            webgl: null,
            performance: null
        };

        // Hardware diagnostic
        if (this.hardwareDetector?.runDiagnostics) {
            results.hardware = await this.hardwareDetector.runDiagnostics();
        }

        // Driver diagnostic
        if (this.driverDetector?.runDiagnostics) {
            results.drivers = await this.driverDetector.runDiagnostics();
        }

        // Availability diagnostic
        results.availability = await this.availabilityManager?.runDiagnostics();

        // WebGL diagnostic
        results.webgl = await this._checkWebGL();

        // Performance snapshot
        results.performance = await this._checkPerformance();

        // Calculate overall score
        results.overallScore = this._calculateOverallScore(results);

        return results;
    }

    /**
     * Calculate overall diagnostic score
     */
    _calculateOverallScore(results) {
        let score = 100;
        
        // Hardware impact
        if (results.hardware?.score) {
            score *= (results.hardware.score / 100);
        }
        
        // Driver impact
        if (results.drivers?.score) {
            score *= (results.drivers.score / 100);
        }
        
        // WebGL impact
        if (results.webgl?.status === 'critical') {
            score *= 0.5;
        } else if (results.webgl?.status === 'degraded') {
            score *= 0.8;
        }
        
        // Performance impact
        if (results.performance?.score) {
            score *= (results.performance.score / 100);
        }
        
        return Math.round(score);
    }

    /**
     * Generate comprehensive report
     */
    generateReport() {
        const status = this.getFullStatus();
        
        return {
            title: 'Angela AI - Unified Detection Report',
            generatedAt: new Date().toISOString(),
            summary: {
                healthy: status.quickStatus.healthy,
                overallScore: status.quickStatus.score,
                state: status.quickStatus.state
            },
            hardware: status.hardware,
            drivers: status.drivers,
            availability: status.availability,
            recommendations: this._generateRecommendations(status),
            diagnostics: null // Will be populated if runDiagnostics() called
        };
    }

    /**
     * Generate recommendations
     */
    _generateRecommendations(status) {
        const recommendations = [];
        
        // WebGL recommendations
        if (status.availability?.subsystems?.webgl?.status === 'degraded') {
            recommendations.push({
                priority: 'high',
                area: 'WebGL',
                message: 'Some WebGL extensions are missing',
                action: status.availability.subsystems.webgl.recommendation
            });
        }
        
        // Driver recommendations
        if (status.drivers?.gpu?.status === 'error') {
            recommendations.push({
                priority: 'high',
                area: 'GPU Driver',
                message: 'GPU driver issue detected',
                action: 'Consider updating graphics drivers for better performance'
            });
        }
        
        // Memory recommendations
        if (status.availability?.subsystems?.memory?.percentage > 70) {
            recommendations.push({
                priority: 'medium',
                area: 'Memory',
                message: 'Memory usage is high',
                action: 'Close unused tabs/applications to free memory'
            });
        }
        
        return recommendations;
    }

    /**
     * Start monitoring
     */
    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        console.log('[UnifiedDetection] Monitoring started');
        
        // Set up availability manager callbacks
        if (this.availabilityManager) {
            this.availabilityManager.onStateChange = (newState, oldState) => {
                if (this.onStatusChange) {
                    this.onStatusChange('state', newState, oldState);
                }
            };
            
            this.availabilityManager.onAlert = (alert) => {
                if (this.onAlert) {
                    this.onAlert(alert);
                }
            };
            
            this.availabilityManager.onRecovery = (subsystem, success) => {
                if (this.onRecovery) {
                    this.onRecovery(subsystem, success);
                }
            };
        }
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        this.isMonitoring = false;
        this.availabilityManager?.stop();
        console.log('[UnifiedDetection] Monitoring stopped');
    }

    /**
     * Destroy the system
     */
    destroy() {
        this.stopMonitoring();
        this.availabilityManager?.destroy();
        this.isInitialized = false;
        console.log('[UnifiedDetection] Destroyed');
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedDetectionSystem;
}
