const fs = require('fs');
const path = require('path');

class ErrorHandler {
  constructor() {
    this.logDir = path.join(__dirname, '..', '..', 'logs');
    this.ensureLogDirectory();
  }

  ensureLogDirectory() {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  log(level, message, error = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    
    // 控制台输出
    if (level === 'error') {
      console.error(logMessage);
    } else if (level === 'warn') {
      console.warn(logMessage);
    } else {
      console.log(logMessage);
    }
    
    // 文件日志
    const logFile = path.join(this.logDir, `${new Date().toISOString().split('T')[0]}.log`);
    const logEntry = `${logMessage}${error ? `\n${error.stack}` : ''}\n`;
    
    try {
      fs.appendFileSync(logFile, logEntry);
    } catch (logError) {
      console.error(`Failed to write to log file: ${logError.message}`);
    }
  }

  handleError(context, error, additionalInfo = {}) {
    const errorMessage = `Error in ${context}: ${error.message}`;
    this.log('error', errorMessage, error);
    
    // 返回结构化的错误信息
    return {
      success: false,
      error: {
        message: error.message,
        code: error.code || 'UNKNOWN_ERROR',
        context: context,
        timestamp: new Date().toISOString(),
        ...additionalInfo
      }
    };
  }

  handleApiError(context, response, additionalInfo = {}) {
    const errorMessage = `API Error in ${context}: ${response.status} ${response.statusText}`;
    this.log('error', errorMessage);
    
    return {
      success: false,
      error: {
        message: `API request failed with status ${response.status}`,
        code: response.status,
        context: context,
        timestamp: new Date().toISOString(),
        ...additionalInfo
      }
    };
  }
}

module.exports = ErrorHandler;