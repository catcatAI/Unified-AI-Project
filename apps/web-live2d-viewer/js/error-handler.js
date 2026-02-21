/**
 * 統一錯誤處理工具
 * 用於減少 try-catch 重複代碼並提供一致的錯誤處理
 */

class ErrorHandler {
    constructor() {
        this.errorLog = [];
        this.maxLogSize = 100;
    }

    /**
     * 執行函數並統一處理錯誤
     * @param {Function} fn - 要執行的函數
     * @param {Object} options - 選項
     * @param {string} options.context - 上下文描述
     * @param {Function} options.onError - 錯誤回調
     * @param {any} options.defaultValue - 默認返回值
     * @returns {any} �數執行結果或默認值
     */
    static safeExecute(fn, options = {}) {
        const {
            context = 'Unknown',
            onError = null,
            defaultValue = null,
            logErrors = true
        } = options;

        try {
            return fn();
        } catch (error) {
            if (logErrors) {
                ErrorHandler.logError(error, context);
            }
            if (onError) {
                onError(error);
            }
            return defaultValue;
        }
    }

    /**
     * 執行異步函數並統一處理錯誤
     * @param {Function} fn - 要執行的異步函數
     * @param {Object} options - 選項
     * @returns {Promise<any>} 函數執行結果或默認值
     */
    static async safeExecuteAsync(fn, options = {}) {
        const {
            context = 'Unknown',
            onError = null,
            defaultValue = null,
            logErrors = true
        } = options;

        try {
            return await fn();
        } catch (error) {
            if (logErrors) {
                ErrorHandler.logError(error, context);
            }
            if (onError) {
                onError(error);
            }
            return defaultValue;
        }
    }

    /**
     * 記錄錯誤
     * @param {Error} error - 錯誤對象
     * @param {string} context - 上下文描述
     */
    static logError(error, context = 'Unknown') {
        const errorInfo = {
            timestamp: new Date().toISOString(),
            context: context,
            message: error.message,
            stack: error.stack,
            type: error.constructor.name
        };

        console.error(`[${context}] Error:`, error.message);
        if (error.stack) {
            console.error(error.stack);
        }

        // 保存到錯誤日誌
        if (this.errorLog) {
            this.errorLog.push(errorInfo);
            if (this.errorLog.length > this.maxLogSize) {
                this.errorLog.shift();
            }
        }
    }

    /**
     * 裝飾器模式：為方法添加錯誤處理
     * @param {Object} options - 選項
     * @returns {Function} 裝飾器函數
     */
    static withErrorHandling(options = {}) {
        return function(target, propertyKey, descriptor) {
            const originalMethod = descriptor.value;

            descriptor.value = function(...args) {
                const context = options.context || `${target.constructor.name}.${propertyKey}`;
                return ErrorHandler.safeExecute(
                    () => originalMethod.apply(this, args),
                    { ...options, context }
                );
            };

            return descriptor;
        };
    }

    /**
     * 批量執行函數，收集所有錯誤
     * @param {Array<Function>} functions - 函數數組
     * @param {Object} options - 選項
     * @returns {Object} { results: [], errors: [] }
     */
    static batchExecute(functions, options = {}) {
        const results = [];
        const errors = [];

        functions.forEach((fn, index) => {
            const context = options.context || `Batch[${index}]`;
            try {
                results.push(fn());
            } catch (error) {
                ErrorHandler.logError(error, context);
                errors.push({ index, error, context });
                results.push(options.defaultValue || null);
            }
        });

        return { results, errors };
    }

    /**
     * 重試執行函數
     * @param {Function} fn - 要執行的函數
     * @param {Object} options - 選項
     * @returns {any} 函數執行結果
     */
    static async retry(fn, options = {}) {
        const {
            maxRetries = 3,
            delay = 1000,
            context = 'Retry',
            onError = null
        } = options;

        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;
                ErrorHandler.logError(error, `${context} (attempt ${attempt}/${maxRetries})`);

                if (attempt < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, delay * attempt));
                }

                if (onError) {
                    onError(error, attempt);
                }
            }
        }

        throw lastError;
    }

    /**
     * 獲取錯誤日誌
     * @returns {Array} 錯誤日誌
     */
    static getErrorLog() {
        return [...this.errorLog];
    }

    /**
     * 清除錯誤日誌
     */
    static clearErrorLog() {
        this.errorLog = [];
    }

    /**
     * 創建防抖錯誤處理器
     * @param {Function} fn - 錯誤處理函數
     * @param {number} delay - 延遲時間
     * @returns {Function} 防抖函數
     */
    static debounceError(fn, delay = 1000) {
        let timeoutId;
        return function(error, context) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                fn(error, context);
            }, delay);
        };
    }
}

// 初始化靜態屬性
ErrorHandler.errorLog = [];
ErrorHandler.maxLogSize = 100;

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorHandler };
} else {
    window.ErrorHandler = ErrorHandler;
}