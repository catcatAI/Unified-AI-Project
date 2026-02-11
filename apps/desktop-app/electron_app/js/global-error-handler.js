/**
 * Angela AI - 统一错误处理器
 * 
 * 提供全局错误捕获和处理机制
 */

class GlobalErrorHandler {
    constructor() {
        this.errorHandlers = [];
        this.errorLog = [];
        this.maxLogSize = 100;
        this.fatalErrorThreshold = 10; // 10次致命错误后重启
        this.fatalErrorCount = 0;
        this.fatalErrorResetInterval = null;
        
        console.log('[GlobalErrorHandler] Initialized');
    }
    
    /**
     * 初始化全局错误处理
     */
    initialize() {
        try {
            // 浏览器环境
            if (typeof window !== 'undefined') {
                this._setupBrowserHandlers();
            }
            
            // Node.js环境
            if (typeof process !== 'undefined') {
                this._setupNodeHandlers();
            }
            
            // 启动致命错误计数器重置
            this._startFatalErrorReset();
            
            console.log('[GlobalErrorHandler] Global error handling initialized');
        } catch (error) {
            console.error('[GlobalErrorHandler] Failed to initialize:', error);
        }
    }
    
    /**
     * 设置浏览器环境错误处理器
     */
    _setupBrowserHandlers() {
        // 全局错误
        window.addEventListener('error', (event) => {
            this._handleGlobalError(event.error || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });
        
        // 未捕获的Promise rejection
        window.addEventListener('unhandledrejection', (event) => {
            this._handleUnrejection(event.reason, {
                promise: event.promise
            });
        });
        
        // 资源加载错误
        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                this._handleResourceError(event.target.src || event.target.href, event);
            }
        }, true);
        
        console.log('[GlobalErrorHandler] Browser handlers setup');
    }
    
    /**
     * 设置Node.js环境错误处理器
     */
    _setupNodeHandlers() {
        // 未捕获的异常
        process.on('uncaughtException', (error) => {
            this._handleUncaughtException(error);
        });
        
        // 未处理的Promise rejection
        process.on('unhandledRejection', (reason, promise) => {
            this._handleUnrejection(reason, { promise });
        });
        
        // 警告
        process.on('warning', (warning) => {
            this._handleWarning(warning);
        });
        
        console.log('[GlobalErrorHandler] Node.js handlers setup');
    }
    
    /**
     * 处理全局错误
     */
    _handleGlobalError(error, context = {}) {
        const errorInfo = {
            type: 'error',
            message: error?.message || String(error),
            stack: error?.stack,
            timestamp: new Date().toISOString(),
            context: context,
            severity: 'error'
        };
        
        this._logError(errorInfo);
        this._notifyHandlers(errorInfo);
    }
    
    /**
     * 处理未捕获的异常
     */
    _handleUncaughtException(error) {
        const errorInfo = {
            type: 'uncaughtException',
            message: error?.message || String(error),
            stack: error?.stack,
            timestamp: new Date().toISOString(),
            severity: 'fatal'
        };
        
        this._logError(errorInfo);
        this._notifyHandlers(errorInfo);
        
        // 致命错误计数
        this.fatalErrorCount++;
        console.error(`[GlobalErrorHandler] Fatal error count: ${this.fatalErrorCount}/${this.fatalErrorThreshold}`);
        
        // 超过阈值，建议重启
        if (this.fatalErrorCount >= this.fatalErrorThreshold) {
            this._handleFatalThreshold();
        }
    }
    
    /**
     * 处理未处理的Promise rejection
     */
    _handleUnrejection(reason, context = {}) {
        const errorInfo = {
            type: 'unhandledRejection',
            message: reason?.message || String(reason),
            stack: reason?.stack,
            timestamp: new Date().toISOString(),
            context: context,
            severity: 'warning'
        };
        
        this._logError(errorInfo);
        this._notifyHandlers(errorInfo);
    }
    
    /**
     * 处理资源加载错误
     */
    _handleResourceError(url, event) {
        const errorInfo = {
            type: 'resourceError',
            message: `Failed to load resource: ${url}`,
            url: url,
            timestamp: new Date().toISOString(),
            severity: 'warning'
        };
        
        this._logError(errorInfo);
        this._notifyHandlers(errorInfo);
    }
    
    /**
     * 处理警告
     */
    _handleWarning(warning) {
        const errorInfo = {
            type: 'warning',
            message: warning.message || String(warning),
            stack: warning.stack,
            timestamp: new Date().toISOString(),
            severity: 'warning'
        };
        
        this._logError(errorInfo);
        this._notifyHandlers(errorInfo);
    }
    
    /**
     * 处理致命错误阈值
     */
    _handleFatalThreshold() {
        console.error('[GlobalErrorHandler] Fatal error threshold reached, recommending restart');
        
        // 通知所有处理器
        this.errorHandlers.forEach(handler => {
            if (handler.onFatalThreshold) {
                handler.onFatalThreshold(this.fatalErrorCount);
            }
        });
    }
    
    /**
     * 记录错误
     */
    _logError(errorInfo) {
        // 添加到日志
        this.errorLog.push(errorInfo);
        
        // 限制日志大小
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }
        
        // 根据严重程度输出日志
        switch (errorInfo.severity) {
            case 'fatal':
                console.error('[GlobalErrorHandler] FATAL:', errorInfo.message, errorInfo);
                break;
            case 'error':
                console.error('[GlobalErrorHandler] ERROR:', errorInfo.message, errorInfo);
                break;
            case 'warning':
                console.warn('[GlobalErrorHandler] WARNING:', errorInfo.message, errorInfo);
                break;
            default:
                console.log('[GlobalErrorHandler] INFO:', errorInfo.message, errorInfo);
        }
        
        // 持久化到localStorage
        this._persistErrorLog();
    }
    
    /**
     * 通知所有处理器
     */
    _notifyHandlers(errorInfo) {
        this.errorHandlers.forEach(handler => {
            try {
                handler(errorInfo);
            } catch (error) {
                console.error('[GlobalErrorHandler] Error handler failed:', error);
            }
        });
    }
    
    /**
     * 注册错误处理器
     */
    on(handler) {
        if (typeof handler === 'function') {
            this.errorHandlers.push(handler);
        }
    }
    
    /**
     * 移除错误处理器
     */
    off(handler) {
        const index = this.errorHandlers.indexOf(handler);
        if (index !== -1) {
            this.errorHandlers.splice(index, 1);
        }
    }
    
    /**
     * 获取错误日志
     */
    getErrorLog(filter = {}) {
        let logs = [...this.errorLog];
        
        // 按严重程度过滤
        if (filter.severity) {
            logs = logs.filter(log => log.severity === filter.severity);
        }
        
        // 按类型过滤
        if (filter.type) {
            logs = logs.filter(log => log.type === filter.type);
        }
        
        // 按时间范围过滤
        if (filter.since) {
            const since = new Date(filter.since).getTime();
            logs = logs.filter(log => new Date(log.timestamp).getTime() >= since);
        }
        
        return logs;
    }
    
    /**
     * 清空错误日志
     */
    clearErrorLog() {
        this.errorLog = [];
        this._persistErrorLog();
        console.log('[GlobalErrorHandler] Error log cleared');
    }
    
    /**
     * 持久化错误日志
     */
    _persistErrorLog() {
        try {
            if (typeof localStorage !== 'undefined') {
                // 只保存最近的50条
                const recentLogs = this.errorLog.slice(-50);
                localStorage.setItem('angela_error_log', JSON.stringify(recentLogs));
            }
        } catch (error) {
            console.error('[GlobalErrorHandler] Failed to persist error log:', error);
        }
    }
    
    /**
     * 从localStorage加载错误日志
     */
    _loadErrorLog() {
        try {
            if (typeof localStorage !== 'undefined') {
                const data = localStorage.getItem('angela_error_log');
                if (data) {
                    this.errorLog = JSON.parse(data);
                    console.log(`[GlobalErrorHandler] Loaded ${this.errorLog.length} error logs`);
                }
            }
        } catch (error) {
            console.error('[GlobalErrorHandler] Failed to load error log:', error);
        }
    }
    
    /**
     * 启动致命错误计数器重置
     */
    _startFatalErrorReset() {
        // 每5分钟重置致命错误计数
        this.fatalErrorResetInterval = setInterval(() => {
            if (this.fatalErrorCount > 0) {
                console.log(`[GlobalErrorHandler] Resetting fatal error count: ${this.fatalErrorCount} -> 0`);
                this.fatalErrorCount = 0;
            }
        }, 5 * 60 * 1000); // 5分钟
    }
    
    /**
     * 手动触发错误
     */
    triggerError(error, context = {}) {
        this._handleGlobalError(error, context);
    }
    
    /**
     * 获取错误统计
     */
    getErrorStats() {
        const stats = {
            total: this.errorLog.length,
            bySeverity: {},
            byType: {},
            fatalErrorCount: this.fatalErrorCount
        };
        
        this.errorLog.forEach(log => {
            // 按严重程度统计
            stats.bySeverity[log.severity] = (stats.bySeverity[log.severity] || 0) + 1;
            
            // 按类型统计
            stats.byType[log.type] = (stats.byType[log.type] || 0) + 1;
        });
        
        return stats;
    }
    
    /**
     * 销毁
     */
    destroy() {
        if (this.fatalErrorResetInterval) {
            clearInterval(this.fatalErrorResetInterval);
            this.fatalErrorResetInterval = null;
        }
        
        this.errorHandlers = [];
        console.log('[GlobalErrorHandler] Destroyed');
    }
}

// 创建全局单例
const globalErrorHandler = new GlobalErrorHandler();

// 自动初始化
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        globalErrorHandler.initialize();
    });
} else {
    globalErrorHandler.initialize();
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GlobalErrorHandler, globalErrorHandler };
}