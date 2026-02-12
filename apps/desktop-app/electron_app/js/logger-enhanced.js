/**
 * Angela AI - Enhanced Logger
 * 增强日志系统

功能：
1. 统一日志格式
2. 日志级别过滤
3. 日志持久化
4. 日志导出
5. 性能监控
 */

class AngelaLogger {
    constructor(options = {}) {
        this.moduleName = options.moduleName || 'General';
        this.minLevel = options.minLevel || 'info'; // debug, info, warn, error
        this.enableConsole = options.enableConsole !== false;
        this.enableStorage = options.enableStorage || false;
        this.maxStorageSize = options.maxStorageSize || 1000;
        
        // 日志颜色
        this.colors = {
            debug: '#888888',
            info: '#00aaff',
            warn: '#ffaa00',
            error: '#ff4444'
        };
        
        // 日志存储
        this.logs = [];
        this.sessionStartTime = Date.now();
        
        // 性能统计
        this.stats = {
            debug: 0,
            info: 0,
            warn: 0,
            error: 0
        };
        
        // 初始化
        if (this.enableStorage) {
            this._loadFromStorage();
        }
    }
    
    /**
     * 格式化日志消息
     */
    _format(level, message, data) {
        const timestamp = new Date().toISOString();
        const elapsed = Date.now() - this.sessionStartTime;
        
        let formattedMessage = `[${timestamp}] [${this.moduleName}] [${level.toUpperCase()}]`;
        if (elapsed > 0) {
            formattedMessage += ` [+${elapsed}ms]`;
        }
        formattedMessage += ` ${message}`;
        
        if (data !== undefined) {
            formattedMessage += ` ${this._formatData(data)}`;
        }
        
        return formattedMessage;
    }
    
    /**
     * 格式化数据对象
     */
    _formatData(data) {
        try {
            return JSON.stringify(data, null, 2);
        } catch (e) {
            return String(data);
        }
    }
    
    /**
     * 记录日志
     */
    _log(level, message, data) {
        // 检查日志级别
        if (!this._shouldLog(level)) {
            return;
        }
        
        const logEntry = {
            timestamp: Date.now(),
            level: level,
            module: this.moduleName,
            message: message,
            data: data
        };
        
        // 存储日志
        this.logs.push(logEntry);
        this.stats[level]++;
        
        // 限制存储大小
        if (this.logs.length > this.maxStorageSize) {
            this.logs.shift();
        }
        
        // 控制台输出
        if (this.enableConsole) {
            const formatted = this._format(level, message, data);
            const style = `color: ${this.colors[level]}`;
            
            switch (level) {
                case 'debug':
                    console.log(`%c${formatted}`, style);
                    break;
                case 'info':
                    console.log(`%c${formatted}`, style);
                    break;
                case 'warn':
                    console.warn(`%c${formatted}`, style);
                    break;
                case 'error':
                    console.error(`%c${formatted}`, style);
                    break;
            }
        }
        
        // 持久化
        if (this.enableStorage) {
            this._saveToStorage();
        }
    }
    
    /**
     * 检查是否应该记录此级别的日志
     */
    _shouldLog(level) {
        const levels = ['debug', 'info', 'warn', 'error'];
        const currentLevel = levels.indexOf(level);
        const minLevel = levels.indexOf(this.minLevel);
        return currentLevel >= minLevel;
    }
    
    /**
     * Debug 日志
     */
    debug(message, data) {
        this._log('debug', message, data);
    }
    
    /**
     * Info 日志
     */
    info(message, data) {
        this._log('info', message, data);
    }
    
    /**
     * Warning 日志
     */
    warn(message, data) {
        this._log('warn', message, data);
    }
    
    /**
     * Error 日志
     */
    error(message, data) {
        this._log('error', message, data);
    }
    
    /**
     * 保存到 localStorage
     */
    _saveToStorage() {
        try {
            const storageKey = `angela_logs_${this.moduleName}`;
            const data = JSON.stringify(this.logs.slice(-500)); // 只保存最后500条
            localStorage.setItem(storageKey, data);
        } catch (e) {
            // 静默失败
        }
    }
    
    /**
     * 从 localStorage 加载
     */
    _loadFromStorage() {
        try {
            const storageKey = `angela_logs_${this.moduleName}`;
            const data = localStorage.getItem(storageKey);
            if (data) {
                this.logs = JSON.parse(data);
            }
        } catch (e) {
            // 静默失败
        }
    }
    
    /**
     * 清除日志
     */
    clear() {
        this.logs = [];
        this.stats = { debug: 0, info: 0, warn: 0, error: 0 };
        
        if (this.enableStorage) {
            const storageKey = `angela_logs_${this.moduleName}`;
            localStorage.removeItem(storageKey);
        }
        
        this.info('Logs cleared');
    }
    
    /**
     * 导出日志
     */
    export() {
        return {
            module: this.moduleName,
            sessionStart: new Date(this.sessionStartTime).toISOString(),
            stats: this.stats,
            logs: this.logs
        };
    }
    
    /**
     * 导出为文本
     */
    exportAsText() {
        const exported = this.export();
        let text = `=== ${exported.module} Log Export ===\n`;
        text += `Session Start: ${exported.sessionStart}\n`;
        text += `Total Logs: ${exported.logs.length}\n`;
        text += `Debug: ${exported.stats.debug}\n`;
        text += `Info: ${exported.stats.info}\n`;
        text += `Warn: ${exported.stats.warn}\n`;
        text += `Error: ${exported.stats.error}\n\n`;
        text += `--- Logs ---\n`;
        
        exported.logs.forEach(log => {
            const timestamp = new Date(log.timestamp).toISOString();
            text += `[${timestamp}] [${log.level.toUpperCase()}] ${log.message}\n`;
        });
        
        return text;
    }
    
    /**
     * 下载日志文件
     */
    download() {
        const text = this.exportAsText();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `angela_logs_${this.moduleName}_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// 全局日志实例
window.AngelaLogger = AngelaLogger;

// 创建日志工厂
window.createLogger = (moduleName, options = {}) => {
    return new AngelaLogger({ ...options, moduleName });
};

// 向后兼容的 console 替换（可选）
if (typeof window !== 'undefined') {
    window.AngelaLoggerInfo = window.createLogger('App');
    
    // 替换 console（仅在生产环境）
    if (window.AngelaLoggerInfo.enableConsole) {
        const originalConsole = {
            log: console.log,
            warn: console.warn,
            error: console.error,
            info: console.info
        };
        
        // 保留原始 console 作为 fallback
        window._originalConsole = originalConsole;
    }
}

console.log('📝 Enhanced Logger loaded');
