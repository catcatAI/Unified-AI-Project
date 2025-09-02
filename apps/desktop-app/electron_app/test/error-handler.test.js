const ErrorHandler = require('../src/error-handler');
const fs = require('fs');
const path = require('path');

// Mock console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

describe('ErrorHandler', () => {
  let errorHandler;
  let logOutput = [];
  
  beforeEach(() => {
    // Mock console methods to capture output
    console.log = jest.fn((...args) => logOutput.push({ type: 'log', args }));
    console.error = jest.fn((...args) => logOutput.push({ type: 'error', args }));
    console.warn = jest.fn((...args) => logOutput.push({ type: 'warn', args }));
    
    errorHandler = new ErrorHandler();
    logOutput = [];
  });
  
  afterEach(() => {
    // Restore original console methods
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
    
    // Clean up log files
    const logDir = path.join(__dirname, '..', '..', 'logs');
    if (fs.existsSync(logDir)) {
      const files = fs.readdirSync(logDir);
      files.forEach(file => {
        fs.unlinkSync(path.join(logDir, file));
      });
      fs.rmdirSync(logDir);
    }
  });
  
  test('should create log directory if it does not exist', () => {
    const logDir = path.join(__dirname, '..', '..', 'logs');
    expect(fs.existsSync(logDir)).toBe(true);
  });
  
  test('should log info messages to console and file', () => {
    errorHandler.log('info', 'Test info message');
    
    // Check console output
    expect(console.log).toHaveBeenCalledWith(expect.stringContaining('Test info message'));
    
    // Check that error and warn were not called
    expect(console.error).not.toHaveBeenCalled();
    expect(console.warn).not.toHaveBeenCalled();
  });
  
  test('should log warning messages to console and file', () => {
    errorHandler.log('warn', 'Test warning message');
    
    // Check console output
    expect(console.warn).toHaveBeenCalledWith(expect.stringContaining('Test warning message'));
    
    // Check that error and log were not called
    expect(console.error).not.toHaveBeenCalled();
    expect(console.log).not.toHaveBeenCalled();
  });
  
  test('should log error messages to console and file', () => {
    errorHandler.log('error', 'Test error message');
    
    // Check console output
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('Test error message'));
    
    // Check that warn and log were not called
    expect(console.warn).not.toHaveBeenCalled();
    expect(console.log).not.toHaveBeenCalled();
  });
  
  test('should handle errors with context and additional info', () => {
    const error = new Error('Test error');
    const result = errorHandler.handleError('test context', error, { additional: 'info' });
    
    // Check returned result
    expect(result.success).toBe(false);
    expect(result.error.message).toBe('Test error');
    expect(result.error.context).toBe('test context');
    expect(result.error.additional).toBe('info');
    
    // Check console output
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('Error in test context: Test error'));
  });
  
  test('should handle API errors with response info', () => {
    const response = {
      status: 404,
      statusText: 'Not Found'
    };
    const result = errorHandler.handleApiError('test api context', response, { additional: 'info' });
    
    // Check returned result
    expect(result.success).toBe(false);
    expect(result.error.message).toBe('API request failed with status 404');
    expect(result.error.code).toBe(404);
    expect(result.error.context).toBe('test api context');
    expect(result.error.additional).toBe('info');
    
    // Check console output
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('API Error in test api context: 404 Not Found'));
  });
});