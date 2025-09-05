const fs = require('fs');
const path = require('path');

// Define log file path
const logDir = path.join(__dirname, '../../logs');
const logFile = path.join(logDir, 'graphic-launcher.log');

// Create logs directory if it doesn't exist
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Log levels
const LOG_LEVELS = {
  ERROR: 'ERROR',
  WARN: 'WARN',
  INFO: 'INFO',
  DEBUG: 'DEBUG'
};

// Current log level (can be adjusted based on environment)
const CURRENT_LOG_LEVEL = process.env.LOG_LEVEL || LOG_LEVELS.INFO;

// Check if a log level should be logged
const shouldLog = (level) => {
  const levels = [LOG_LEVELS.ERROR, LOG_LEVELS.WARN, LOG_LEVELS.INFO, LOG_LEVELS.DEBUG];
  const currentLevelIndex = levels.indexOf(CURRENT_LOG_LEVEL);
  const messageLevelIndex = levels.indexOf(level);
  
  return messageLevelIndex <= currentLevelIndex;
};

// Write log to file
const writeLog = (level, message, error = null) => {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] [${level}] ${message}`;
  
  // Write to file
  fs.appendFileSync(logFile, logEntry + '\n');
  
  // Also log to console for ERROR and WARN levels
  if (level === LOG_LEVELS.ERROR || level === LOG_LEVELS.WARN) {
    console.error(logEntry);
  }
  
  // Log error stack trace if provided
  if (error && error.stack) {
    fs.appendFileSync(logFile, `[${timestamp}] [${level}] Error stack: ${error.stack}\n`);
  }
};

// Logger functions
const error = (message, error = null) => {
  if (shouldLog(LOG_LEVELS.ERROR)) {
    writeLog(LOG_LEVELS.ERROR, message, error);
  }
};

const warn = (message) => {
  if (shouldLog(LOG_LEVELS.WARN)) {
    writeLog(LOG_LEVELS.WARN, message);
  }
};

const info = (message) => {
  if (shouldLog(LOG_LEVELS.INFO)) {
    writeLog(LOG_LEVELS.INFO, message);
  }
};

const debug = (message) => {
  if (shouldLog(LOG_LEVELS.DEBUG)) {
    writeLog(LOG_LEVELS.DEBUG, message);
  }
};

module.exports = {
  error,
  warn,
  info,
  debug,
  LOG_LEVELS
};