/**
 * Angela AI - Availability Manager
 * 
 * Centralized system health and availability monitoring
 * Coordinates: Hardware Detection, Driver Detection, Performance Monitoring
 */

class AvailabilityManager {
    constructor(options = {}) {
        // Configuration
        this.checkInterval = options.checkInterval || 30000; // 30 seconds
        this.healthCheckInterval = options.healthCheckInterval || 60000; // 1 minute
        this.enableAutoRecovery = options.enableAutoRecovery !== false;
        
        // State
        this.isHealthy = false;
        this.systemState = 'initializing';
        this.lastCheck = null;
        this.lastRecovery = null;
        
        // Subsystems
        this.subsystems = {
            hardware: { status: 'unknown', lastCheck: null },
            driver: { status: 'unknown', lastCheck: null },
            performance: { status: 'unknown', lastCheck: null },
            network: { status: 'unknown', lastCheck: null },
            memory: { status: 'unknown', lastCheck: null }
        };
        
        // Health metrics
        this.healthMetrics = {
            score: 0,
            uptime: 0,
            errorCount: 0,
            warningCount: 0,
            recoveryCount: 0
        };
        
        // Recovery actions
        this.recoveryActions = new Map();
        this._registerDefaultRecoveries();
        
        // Event callbacks
        this.onStateChange = null;
        this.onHealthChange = null;
        this.onRecovery = null;
        this.onAlert = null;
        
        // Monitoring
        this.checkTimer = null;
        this.healthTimer = null;
        this.errorLog = [];
        this.alertHistory = [];
    }

    /**
     * Initialize the availability manager
     */
    async initialize() {
        console.log('[AvailabilityManager] Initializing...');
        
        try {
            // Initial health check
            await this.performHealthCheck();
            
            // Start monitoring
            this._startMonitoring();
            
            console.log('[AvailabilityManager] Initialization complete');
            return this.getAvailabilityStatus();
            
        } catch (error) {
            console.error('[AvailabilityManager] Initialization error:', error);
            return this.getAvailabilityStatus();
        }
    }

    /**
     * Register a subsystem
     */
    registerSubsystem(name, checker, recoveryFn = null) {
        this.subsystems[name] = {
            status: 'unknown',
            lastCheck: null,
            checker: checker,
            recovery: recoveryFn
        };
        
        console.log(`[AvailabilityManager] Registered subsystem: ${name}`);
    }

    /**
     * Perform full health check
     */
    async performHealthCheck() {
        console.log('[AvailabilityManager] Performing health check...');
        
        const results = {
            timestamp: new Date(),
            subsystems: {},
            overallScore: 100
        };
        
        // Check each registered subsystem
        for (const [name, subsystem] of Object.entries(this.subsystems)) {
            if (subsystem.checker && typeof subsystem.checker === 'function') {
                try {
                    const result = await subsystem.checker();
                    subsystem.status = result.status || 'unknown';
                    subsystem.lastCheck = new Date();
                    subsystem.result = result;
                    
                    results.subsystems[name] = result;
                    
                    // Calculate score impact
                    if (result.score !== undefined) {
                        results.overallScore *= (result.score / 100);
                    }
                } catch (error) {
                    subsystem.status = 'error';
                    subsystem.error = error.message;
                    results.subsystems[name] = { status: 'error', error: error.message };
                    results.overallScore *= 0.8;
                    
                    this._logError(name, error);
                }
            }
        }
        
        // Update health metrics
        this.healthMetrics.score = Math.round(results.overallScore);
        this.lastCheck = new Date();
        this._updateSystemState();
        
        console.log('[AvailabilityManager] Health check complete. Score:', this.healthMetrics.score);
        
        return this.getAvailabilityStatus();
    }

    /**
     * Start continuous monitoring
     */
    _startMonitoring() {
        // Regular availability checks
        this.checkTimer = setInterval(() => {
            this._performQuickCheck();
        }, this.checkInterval);
        
        // Full health checks
        this.healthTimer = setInterval(() => {
            this.performHealthCheck();
        }, this.healthCheckInterval);
        
        console.log('[AvailabilityManager] Monitoring started');
    }

    /**
     * Stop monitoring
     */
    stop() {
        if (this.checkTimer) {
            clearInterval(this.checkTimer);
            this.checkTimer = null;
        }
        if (this.healthTimer) {
            clearInterval(this.healthTimer);
            this.healthTimer = null;
        }
        console.log('[AvailabilityManager] Monitoring stopped');
    }

    /**
     * Quick availability check
     */
    async _performQuickCheck() {
        const checks = [];
        
        // Memory check
        if (performance.memory) {
            const usedMB = Math.round(performance.memory.usedJSHeapSize / 1048576);
            const totalMB = Math.round(performance.memory.totalJSHeapSize / 1048576);
            const limitMB = Math.round(performance.memory.jsHeapSizeLimit / 1048576);
            
            if (usedMB / limitMB > 0.9) {
                this._triggerAlert('memory', 'critical', `Memory usage critical: ${usedMB}/${limitMB}MB`);
            }
        }
        
        // Network connectivity check
        if (!navigator.onLine) {
            this._triggerAlert('network', 'critical', 'Network connectivity lost');
        }
        
        // Check for unresponsive subsystems
        for (const [name, subsystem] of Object.entries(this.subsystems)) {
            if (subsystem.status === 'error' && this.enableAutoRecovery) {
                await this._attemptRecovery(name);
            }
        }
        
        this.lastCheck = new Date();
        return this.getAvailabilityStatus();
    }

    /**
     * Attempt subsystem recovery
     */
    async _attemptRecovery(subsystemName) {
        const subsystem = this.subsystems[subsystemName];
        if (!subsystem || !subsystem.recovery) return false;
        
        try {
            console.log(`[AvailabilityManager] Attempting recovery for: ${subsystemName}`);
            
            await subsystem.recovery();
            
            // Verify recovery
            const result = await subsystem.checker();
            if (result.status === 'healthy' || result.status === 'active') {
                this.healthMetrics.recoveryCount++;
                this.lastRecovery = new Date();
                this._triggerAlert(subsystemName, 'info', `Recovery successful`);
                
                if (this.onRecovery) {
                    this.onRecovery(subsystemName, true);
                }
                return true;
            }
        } catch (error) {
            console.error(`[AvailabilityManager] Recovery failed for ${subsystemName}:`, error);
        }
        
        if (this.onRecovery) {
            this.onRecovery(subsystemName, false);
        }
        return false;
    }

    /**
     * Register default recovery actions
     */
    _registerDefaultRecoveries() {
        // Memory recovery
        this.recoveryActions.set('memory', () => {
            // Force garbage collection hint
            if (window.gc) {
                window.gc();
            }
            // Clear caches
            if (window.clearCaches) {
                window.clearCaches();
            }
        });
        
        // Network recovery
        this.recoveryActions.set('network', () => {
            // Reconnect WebSocket if needed
            if (window.reconnectWebSocket) {
                window.reconnectWebSocket();
            }
        });
    }

    /**
     * Update system state based on health
     */
    _updateSystemState() {
        const previousState = this.systemState;
        const score = this.healthMetrics.score;
        
        // Determine state
        if (score >= 90) {
            this.systemState = 'healthy';
        } else if (score >= 70) {
            this.systemState = 'degraded';
        } else if (score >= 50) {
            this.systemState = 'warning';
        } else {
            this.systemState = 'critical';
        }
        
        // Notify state change
        if (previousState !== this.systemState && this.onStateChange) {
            this.onStateChange(this.systemState, previousState);
        }
        
        this.isHealthy = score >= 70;
    }

    /**
     * Trigger an alert
     */
    _triggerAlert(subsystem, level, message) {
        const alert = {
            subsystem,
            level, // info, warning, critical
            message,
            timestamp: new Date()
        };
        
        this.alertHistory.push(alert);
        if (this.alertHistory.length > 100) {
            this.alertHistory.shift();
        }
        
        if (level === 'critical') {
            this.healthMetrics.errorCount++;
        } else if (level === 'warning') {
            this.healthMetrics.warningCount++;
        }
        
        console.warn(`[AvailabilityManager] Alert [${level.toUpperCase()}] ${subsystem}:`, message);
        
        if (this.onAlert) {
            this.onAlert(alert);
        }
    }

    /**
     * Log an error
     */
    _logError(subsystem, error) {
        this.errorLog.push({
            subsystem,
            error: error.message,
            stack: error.stack,
            timestamp: new Date()
        });
        
        if (this.errorLog.length > 50) {
            this.errorLog.shift();
        }
    }

    /**
     * Get comprehensive availability status
     */
    getAvailabilityStatus() {
        return {
            isHealthy: this.isHealthy,
            systemState: this.systemState,
            score: this.healthMetrics.score,
            uptime: this._getUptime(),
            lastCheck: this.lastCheck,
            lastRecovery: this.lastRecovery,
            subsystems: Object.entries(this.subsystems).reduce((acc, [name, sub]) => {
                acc[name] = {
                    status: sub.status,
                    lastCheck: sub.lastCheck,
                    ...sub.result
                };
                return acc;
            }, {}),
            alerts: this.alertHistory.slice(-10),
            errors: this.errorLog.slice(-10)
        };
    }

    /**
     * Get uptime
     */
    _getUptime() {
        return Math.round((Date.now() - this.startTime) / 1000);
    }

    /**
     * Generate availability report
     */
    generateReport() {
        return {
            title: 'Angela AI - Availability Report',
            generatedAt: new Date().toISOString(),
            systemState: this.systemState,
            healthScore: this.healthMetrics.score,
            uptime: this._getUptime(),
            subsystems: this.subsystems,
            metrics: this.healthMetrics,
            alerts: this.alertHistory,
            recommendations: this._generateRecommendations()
        };
    }

    /**
     * Generate recommendations based on current state
     */
    _generateRecommendations() {
        const recommendations = [];
        const status = this.getAvailabilityStatus();
        
        // Check subsystem health
        for (const [name, sub] of Object.entries(status.subsystems)) {
            if (sub.status !== 'healthy' && sub.status !== 'active') {
                recommendations.push({
                    subsystem: name,
                    priority: sub.status === 'error' ? 'high' : 'medium',
                    currentStatus: sub.status,
                    suggestion: `Check ${name} subsystem health`
                });
            }
        }
        
        // Check health score
        if (status.score < 70) {
            recommendations.push({
                priority: 'high',
                message: 'Overall system health is degraded',
                suggestion: 'Run full diagnostic: availabilityManager.performHealthCheck()'
            });
        }
        
        // Check error count
        if (this.healthMetrics.errorCount > 10) {
            recommendations.push({
                priority: 'medium',
                message: `High error count: ${this.healthMetrics.errorCount}`,
                suggestion: 'Review error log for patterns'
            });
        }
        
        return recommendations;
    }

    /**
     * Get quick status for UI
     */
    getQuickStatus() {
        const status = this.getAvailabilityStatus();
        
        return {
            healthy: status.isHealthy,
            state: status.systemState,
            score: status.score,
            icon: this._getStatusIcon(status.systemState),
            color: this._getStatusColor(status.systemState)
        };
    }

    /**
     * Get status icon
     */
    _getStatusIcon(state) {
        const icons = {
            healthy: '✓',
            degraded: '⚠',
            warning: '⚡',
            critical: '✗',
            initializing: '...'
        };
        return icons[state] || '?';
    }

    /**
     * Get status color
     */
    _getStatusColor(state) {
        const colors = {
            healthy: '#4ade80',
            degraded: '#fbbf24',
            warning: '#f97316',
            critical: '#ef4444',
            initializing: '#94a3b8'
        };
        return colors[state] || '#94a3b8';
    }

    /**
     * Run full diagnostic
     */
    async runDiagnostics() {
        console.log('[AvailabilityManager] Running diagnostics...');
        
        const results = {
            timestamp: new Date(),
            healthCheck: await this.performHealthCheck(),
            driverCheck: null,
            hardwareCheck: null,
            performanceCheck: null
        };
        
        return results;
    }

    /**
     * Destroy the manager
     */
    destroy() {
        this.stop();
        this.onStateChange = null;
        this.onHealthChange = null;
        this.onRecovery = null;
        this.onAlert = null;
        console.log('[AvailabilityManager] Destroyed');
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvailabilityManager;
}
