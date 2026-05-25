/**
 * Angela AI Performance Monitor
 * 性能監控和分析工具
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            memory: {
                used: 0,
                total: 0,
                limit: 0,
                trend: []
            },
            performance: {
                fps: 0,
                frameTime: 0,
                cpuUsage: 0,
                trend: []
            },
            live2d: {
                renderTime: 0,
                modelLoadTime: 0,
                animationTime: 0,
                trend: []
            },
            network: {
                requests: 0,
                errors: 0,
                latency: 0,
                trend: []
            }
        };
        
        this.thresholds = {
            memory: 80, // %
            fps: 30,
            cpuUsage: 85, // %
            renderTime: 16.67 // ms (60fps)
        };
        
        this.isMonitoring = false;
        this.monitoringInterval = null;
        this.startTime = performance.now();
    }

    /**
     * 開始性能監控
     */
    startMonitoring(intervalMs = 1000) {
        if (this.isMonitoring) {
            console.warn('Performance monitoring already started');
            return;
        }
        
        console.log('Starting performance monitoring...');
        this.isMonitoring = true;
        this.startTime = performance.now();
        
        this.monitoringInterval = setInterval(() => {
            this.collectMetrics();
            this.analyzePerformance();
        }, intervalMs);
    }

    /**
     * 停止性能監控
     */
    stopMonitoring() {
        if (!this.isMonitoring) {
            return;
        }
        
        console.log('Stopping performance monitoring...');
        this.isMonitoring = false;
        
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        this.generateReport();
    }

    /**
     * 收集性能指標
     */
    collectMetrics() {
        // 內存指標
        if (performance.memory) {
            const memory = performance.memory;
            this.metrics.memory.used = memory.usedJSHeapSize / 1024 / 1024; // MB
            this.metrics.memory.total = memory.totalJSHeapSize / 1024 / 1024; // MB
            this.metrics.memory.limit = memory.jsHeapSizeLimit / 1024 / 1024; // MB
        }
        
        // 性能指標
        this.metrics.performance.frameTime = this.getAverageFrameTime();
        this.metrics.performance.fps = 1000 / this.metrics.performance.frameTime;
        this.metrics.performance.cpuUsage = this.estimateCPUUsage();
        
        // Live2D指標
        if (window.live2dManager) {
            this.metrics.live2d.renderTime = this.getLive2DRenderTime();
        }
        
        // 網絡指標
        this.metrics.network.latency = this.getNetworkLatency();
        
        // 保存趨勢數據（保留最近100個數據點）
        this.saveTrendData();
    }

    /**
     * 分析性能狀況
     */
    analyzePerformance() {
        const issues = [];
        
        // 檢查內存使用
        const memoryUsage = (this.metrics.memory.used / this.metrics.memory.limit) * 100;
        if (memoryUsage > this.thresholds.memory) {
            issues.push({
                type: 'memory',
                severity: 'high',
                message: `High memory usage: ${memoryUsage.toFixed(1)}%`,
                value: memoryUsage,
                threshold: this.thresholds.memory
            });
        }
        
        // 檢查FPS
        if (this.metrics.performance.fps < this.thresholds.fps) {
            issues.push({
                type: 'fps',
                severity: 'medium',
                message: `Low FPS: ${this.metrics.performance.fps.toFixed(1)}`,
                value: this.metrics.performance.fps,
                threshold: this.thresholds.fps
            });
        }
        
        // 檢查CPU使用率
        if (this.metrics.performance.cpuUsage > this.thresholds.cpuUsage) {
            issues.push({
                type: 'cpu',
                severity: 'medium',
                message: `High CPU usage: ${this.metrics.performance.cpuUsage.toFixed(1)}%`,
                value: this.metrics.performance.cpuUsage,
                threshold: this.thresholds.cpuUsage
            });
        }
        
        // 檢查渲染時間
        if (this.metrics.live2d.renderTime > this.thresholds.renderTime) {
            issues.push({
                type: 'render',
                severity: 'medium',
                message: `High render time: ${this.metrics.live2d.renderTime.toFixed(2)}ms`,
                value: this.metrics.live2d.renderTime,
                threshold: this.thresholds.renderTime
            });
        }
        
        // 檢查內存泄漏
        const memoryLeak = this.detectMemoryLeak();
        if (memoryLeak.detected) {
            issues.push({
                type: 'memory_leak',
                severity: 'high',
                message: `Memory leak detected: ${memoryLeak.rate.toFixed(2)}MB/min`,
                value: memoryLeak.rate
            });
        }
        
        // 輸出問題
        issues.forEach(issue => {
            console.warn(`Performance Issue [${issue.type}]: ${issue.message}`);
        });
        
        return issues;
    }

    /**
     * 檢測內存泄漏
     */
    detectMemoryLeak() {
        if (this.metrics.memory.trend.length < 10) {
            return { detected: false, rate: 0 };
        }
        
        // 計算內存增長率
        const recent = this.metrics.memory.trend.slice(-10);
        const oldest = recent[0];
        const newest = recent[recent.length - 1];
        const timeDiff = (newest.timestamp - oldest.timestamp) / 1000 / 60; // 分鐘
        const memoryDiff = newest.value - oldest.value; // MB
        
        const rate = memoryDiff / timeDiff; // MB/分鐘
        
        return {
            detected: rate > 1.0, // 超過1MB/分鐘視為泄漏
            rate: rate
        };
    }

    /**
     * 獲取平均幀時間
     */
    getAverageFrameTime() {
        if (!window.frameTimeHistory || window.frameTimeHistory.length === 0) {
            return 16.67; // 默認60fps
        }
        
        const recent = window.frameTimeHistory.slice(-60); // 最近60幀
        const sum = recent.reduce((acc, time) => acc + time, 0);
        return sum / recent.length;
    }

    /**
     * 估算CPU使用率
     */
    estimateCPUUsage() {
        // 基於任務隊列和幀時間估算
        const frameTime = this.getAverageFrameTime();
        const idealFrameTime = 16.67; // 60fps
        const busyRatio = Math.min(frameTime / idealFrameTime, 1.0);
        return busyRatio * 100;
    }

    /**
     * 獲取Live2D渲染時間
     */
    getLive2DRenderTime() {
        if (window.live2dManager && window.live2dManager.lastRenderTime) {
            return window.live2dManager.lastRenderTime;
        }
        return 0;
    }

    /**
     * 獲取網絡延遲
     */
    getNetworkLatency() {
        // 如果有WebSocket連接，測量ping時間
        if (window.angelaWebSocket && window.angelaWebSocket.readyState === WebSocket.OPEN) {
            const start = performance.now();
            window.angelaWebSocket.send(JSON.stringify({ type: 'ping', timestamp: start }));
            // 實際延遲需要在pong響應中計算
        }
        return 0;
    }

    /**
     * 保存趨勢數據
     */
    saveTrendData() {
        const timestamp = performance.now() - this.startTime;
        
        // 內存趨勢
        this.metrics.memory.trend.push({
            timestamp,
            value: this.metrics.memory.used
        });
        
        // 性能趨勢
        this.metrics.performance.trend.push({
            timestamp,
            fps: this.metrics.performance.fps,
            frameTime: this.metrics.performance.frameTime
        });
        
        // 限制數據點數量
        const maxTrendLength = 100;
        
        if (this.metrics.memory.trend.length > maxTrendLength) {
            this.metrics.memory.trend = this.metrics.memory.trend.slice(-maxTrendLength);
        }
        
        if (this.metrics.performance.trend.length > maxTrendLength) {
            this.metrics.performance.trend = this.metrics.performance.trend.slice(-maxTrendLength);
        }
    }

    /**
     * 生成性能報告
     */
    generateReport() {
        const report = {
            monitoringDuration: (performance.now() - this.startTime) / 1000, // 秒
            memory: {
                current: this.metrics.memory.used.toFixed(2),
                peak: Math.max(...this.metrics.memory.trend.map(t => t.value)).toFixed(2),
                average: this.calculateAverage(this.metrics.memory.trend.map(t => t.value)).toFixed(2),
                limit: this.metrics.memory.limit.toFixed(2)
            },
            performance: {
                averageFPS: this.calculateAverage(this.metrics.performance.trend.map(t => t.fps)).toFixed(1),
                minFPS: Math.min(...this.metrics.performance.trend.map(t => t.fps)).toFixed(1),
                maxFPS: Math.max(...this.metrics.performance.trend.map(t => t.fps)).toFixed(1),
                averageFrameTime: this.calculateAverage(this.metrics.performance.trend.map(t => t.frameTime)).toFixed(2)
            },
            issues: this.analyzePerformance()
        };
        
        console.log('=== Performance Report ===');
        console.log(`Monitoring Duration: ${report.monitoringDuration}s`);
        console.log(`Memory Usage: ${report.memory.current}MB / ${report.memory.limit}MB`);
        console.log(`Peak Memory: ${report.memory.peak}MB`);
        console.log(`Average FPS: ${report.performance.averageFPS}`);
        console.log(`Min/Max FPS: ${report.performance.minFPS}/${report.performance.maxFPS}`);
        console.log(`Issues Found: ${report.issues.length}`);
        
        return report;
    }

    /**
     * 計算平均值
     */
    calculateAverage(values) {
        if (values.length === 0) return 0;
        const sum = values.reduce((acc, val) => acc + val, 0);
        return sum / values.length;
    }

    /**
     * 獲取當前狀態
     */
    getCurrentStatus() {
        return {
            isMonitoring: this.isMonitoring,
            metrics: this.metrics,
            thresholds: this.thresholds
        };
    }

    /**
     * 設置性能閾值
     */
    setThresholds(newThresholds) {
        this.thresholds = { ...this.thresholds, ...newThresholds };
        console.log('Performance thresholds updated:', this.thresholds);
    }

    /**
     * 清理資源
     */
    cleanup() {
        this.stopMonitoring();
        this.metrics = null;
        console.log('Performance monitor cleaned up');
    }
}

// 導出性能監控器
window.PerformanceMonitor = PerformanceMonitor;