const { ipcMain } = require('electron');
const { exec } = require('child_process');
const path = require('path');
const { error, info, warn } = require('./logger');

// Get project root directory
const projectRoot = path.join(__dirname, '../../');

// Valid scripts whitelist
const validScripts = [
  'tools/health-check.bat',
  'tools/train-manager.bat',
  'tools/cli-runner.bat',
  'tools/run-tests.bat',
  'tools/safe-git-cleanup.bat',
  'tools/view-error-logs.bat',
  'tools/emergency-git-fix.bat',
  'tools/setup-training.bat',
  'tools/run_data_pipeline.bat',
  'tools/automated-backup.bat',
  'tools/project-security-check.bat',
  'tools/fix-dependencies.bat',
  'tools/start-dev.bat'
];

// Valid CLI commands whitelist
const validCliCommands = [
  'health',
  'setup',
  'start',
  'test',
  'git',
  'train',
  'cli',
  'model',
  'data',
  'system'
];

// IPC handler for running scripts
const handleRunScript = async (event, { script, args = [] }) => {
  try {
    info(`Running script: ${script} with args: ${args.join(' ')}`);
    
    // Validate script is in whitelist
    if (!validScripts.includes(script)) {
      const errorMsg = `Invalid script: ${script}`;
      error(errorMsg);
      return { success: false, error: errorMsg };
    }

    // Construct full script path
    const scriptPath = path.join(projectRoot, script);
    
    // Check if script exists
    const fs = require('fs');
    if (!fs.existsSync(scriptPath)) {
      const errorMsg = `Script not found: ${scriptPath}`;
      error(errorMsg);
      return { success: false, error: errorMsg };
    }
    
    // Construct command with arguments
    const command = `"${scriptPath}" ${args.join(' ')}`;
    
    info(`Executing command: ${command}`);
    
    // Execute script
    const result = await new Promise((resolve) => {
      exec(command, { cwd: projectRoot, maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
        if (error) {
          warn(`Script execution error: ${error.message}`);
          resolve({
            success: false,
            error: error.message,
            stdout,
            stderr
          });
        } else {
          info(`Script executed successfully: ${script}`);
          resolve({
            success: true,
            stdout,
            stderr
          });
        }
      });
    });
    
    return result;
  } catch (err) {
    error(`Exception in handleRunScript: ${err.message}`, err);
    return { success: false, error: err.message };
  }
};

// IPC handler for running CLI commands
const handleRunCliCommand = async (event, { command, args = [] }) => {
  try {
    info(`Running CLI command: ${command} with args: ${args.join(' ')}`);
    
    // Validate command is in whitelist
    if (!validCliCommands.includes(command)) {
      const errorMsg = `Invalid command: ${command}`;
      error(errorMsg);
      return { success: false, error: errorMsg };
    }

    // Construct command
    const cliPath = path.join(projectRoot, 'cli/main.py');
    const fullCommand = `python "${cliPath}" ${command} ${args.join(' ')}`;
    
    info(`Executing CLI command: ${fullCommand}`);
    
    // Execute CLI command
    const result = await new Promise((resolve) => {
      exec(fullCommand, { cwd: projectRoot, maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
        if (error) {
          warn(`CLI command execution error: ${error.message}`);
          resolve({
            success: false,
            error: error.message,
            stdout,
            stderr
          });
        } else {
          info(`CLI command executed successfully: ${command}`);
          resolve({
            success: true,
            stdout,
            stderr
          });
        }
      });
    });
    
    return result;
  } catch (err) {
    error(`Exception in handleRunCliCommand: ${err.message}`, err);
    return { success: false, error: err.message };
  }
};

// IPC handler for getting system info
const handleGetSystemInfo = async () => {
  try {
    info('Getting system information');
    
    const os = process.platform;
    const arch = process.arch;
    const memory = Math.round(require('os').totalmem() / (1024 * 1024 * 1024)) + 'GB';
    
    info(`System info retrieved: ${os} ${arch} ${memory}`);
    
    return {
      success: true,
      data: {
        os,
        arch,
        memory
      }
    };
  } catch (err) {
    error(`Exception in handleGetSystemInfo: ${err.message}`, err);
    return { success: false, error: err.message };
  }
};

// IPC handler for checking environment
const handleCheckEnvironment = async () => {
  try {
    info('Checking environment');
    
    // Check for Node.js
    const nodeCheck = await new Promise((resolve) => {
      exec('node --version', { cwd: projectRoot }, (error, stdout) => {
        if (error) {
          warn('Node.js not found');
          resolve({ installed: false });
        } else {
          info(`Node.js version: ${stdout.trim()}`);
          resolve({ installed: true, version: stdout.trim() });
        }
      });
    });
    
    // Check for Python
    const pythonCheck = await new Promise((resolve) => {
      exec('python --version', { cwd: projectRoot }, (error, stdout) => {
        if (error) {
          warn('Python not found');
          resolve({ installed: false });
        } else {
          info(`Python version: ${stdout.trim()}`);
          resolve({ installed: true, version: stdout.trim() });
        }
      });
    });
    
    // Check for pnpm
    const pnpmCheck = await new Promise((resolve) => {
      exec('pnpm --version', { cwd: projectRoot }, (error, stdout) => {
        if (error) {
          warn('pnpm not found');
          resolve({ installed: false });
        } else {
          info(`pnpm version: ${stdout.trim()}`);
          resolve({ installed: true, version: stdout.trim() });
        }
      });
    });
    
    info('Environment check completed');
    
    return {
      success: true,
      data: {
        node: nodeCheck,
        python: pythonCheck,
        pnpm: pnpmCheck
      }
    };
  } catch (err) {
    error(`Exception in handleCheckEnvironment: ${err.message}`, err);
    return { success: false, error: err.message };
  }
};

module.exports = {
  handleRunScript,
  handleRunCliCommand,
  handleGetSystemInfo,
  handleCheckEnvironment
};