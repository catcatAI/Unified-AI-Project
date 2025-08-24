#!/usr/bin/env node

/**
 * 测试监控脚本 - 在开发过程中持续监控文件变化并运行测试
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const chokidar = require('chokidar');

class TestWatcher {
    constructor() {
        this.isRunning = false;
        this.testProcesses = new Map();
        this.lastRunTime = new Map();
        this.debounceDelay = 1000; // 1秒防抖
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const colors = {
            info: '\x1b[36m',  // cyan
            success: '\x1b[32m', // green
            error: '\x1b[31m',   // red
            warning: '\x1b[33m', // yellow
            reset: '\x1b[0m'
        };
        
        console.log(`${colors[type]}[${timestamp}] ${message}${colors.reset}`);
    }

    async runTests(component, testType = 'unit') {
        const now = Date.now();
        const lastRun = this.lastRunTime.get(`${component}-${testType}`) || 0;
        
        // 防抖：如果距离上次运行不到指定时间，则跳过
        if (now - lastRun < this.debounceDelay) {
            return;
        }
        
        this.lastRunTime.set(`${component}-${testType}`, now);
        
        // 如果已有测试进程在运行，先终止它
        const processKey = `${component}-${testType}`;
        if (this.testProcesses.has(processKey)) {
            this.testProcesses.get(processKey).kill();
            this.testProcesses.delete(processKey);
        }

        this.log(`Running ${testType} tests for ${component}...`, 'info');

        let command, args, cwd;

        switch (component) {
            case 'backend':
                command = process.platform === 'win32' ? 'cmd' : 'bash';
                args = process.platform === 'win32' 
                    ? ['/c', 'call venv\\Scripts\\activate.bat && pytest --tb=short -v --timeout=30']
                    : ['-c', 'source venv/bin/activate && pytest --tb=short -v --timeout=30'];
                cwd = path.join(process.cwd(), 'apps', 'backend');
                break;
                
            case 'frontend':
                command = 'pnpm';
                args = ['test', '--passWithNoTests'];
                cwd = path.join(process.cwd(), 'apps', 'frontend-dashboard');
                break;
                
            case 'desktop':
                command = 'pnpm';
                args = ['test', '--passWithNoTests'];
                cwd = path.join(process.cwd(), 'apps', 'desktop-app');
                break;
                
            default:
                this.log(`Unknown component: ${component}`, 'error');
                return;
        }

        const testProcess = spawn(command, args, {
            cwd,
            stdio: ['pipe', 'pipe', 'pipe'],
            shell: true
        });

        this.testProcesses.set(processKey, testProcess);

        let output = '';
        let errorOutput = '';

        testProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        testProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });

        testProcess.on('close', (code) => {
            this.testProcesses.delete(processKey);
            
            if (code === 0) {
                this.log(`✓ ${component} tests passed`, 'success');
            } else {
                this.log(`✗ ${component} tests failed (exit code: ${code})`, 'error');
                if (errorOutput) {
                    console.log(errorOutput);
                }
            }
        });

        testProcess.on('error', (error) => {
            this.testProcesses.delete(processKey);
            this.log(`Test process error for ${component}: ${error.message}`, 'error');
        });
    }

    setupWatchers() {
        // 后端文件监控
        const backendWatcher = chokidar.watch([
            'apps/backend/src/**/*.py',
            'apps/backend/tests/**/*.py'
        ], {
            ignored: /(^|[\/\\])\../, // 忽略隐藏文件
            persistent: true
        });

        backendWatcher.on('change', (filePath) => {
            this.log(`Backend file changed: ${filePath}`, 'warning');
            this.runTests('backend');
        });

        // 前端文件监控
        const frontendWatcher = chokidar.watch([
            'apps/frontend-dashboard/src/**/*.{ts,tsx,js,jsx}',
            'apps/frontend-dashboard/__tests__/**/*.{ts,tsx,js,jsx}'
        ], {
            ignored: /(^|[\/\\])\../,
            persistent: true
        });

        frontendWatcher.on('change', (filePath) => {
            this.log(`Frontend file changed: ${filePath}`, 'warning');
            this.runTests('frontend');
        });

        // 桌面应用文件监控
        const desktopWatcher = chokidar.watch([
            'apps/desktop-app/**/*.{ts,tsx,js,jsx}',
            '!apps/desktop-app/node_modules/**'
        ], {
            ignored: /(^|[\/\\])\../,
            persistent: true
        });

        desktopWatcher.on('change', (filePath) => {
            this.log(`Desktop app file changed: ${filePath}`, 'warning');
            this.runTests('desktop');
        });

        this.log('File watchers started for all components', 'success');
    }

    async runInitialTests() {
        this.log('Running initial test suite...', 'info');
        
        // 并行运行所有组件的测试
        await Promise.all([
            this.runTests('backend'),
            this.runTests('frontend'),
            this.runTests('desktop')
        ]);
    }

    start() {
        if (this.isRunning) {
            this.log('Test watcher is already running', 'warning');
            return;
        }

        this.isRunning = true;
        this.log('Starting test watcher...', 'info');

        // 设置文件监控
        this.setupWatchers();

        // 运行初始测试
        this.runInitialTests();

        // 处理退出信号
        process.on('SIGINT', () => {
            this.stop();
        });

        process.on('SIGTERM', () => {
            this.stop();
        });

        this.log('Test watcher is running. Press Ctrl+C to stop.', 'success');
    }

    stop() {
        this.log('Stopping test watcher...', 'info');
        
        // 终止所有运行中的测试进程
        for (const [key, process] of this.testProcesses) {
            this.log(`Terminating ${key} test process...`, 'warning');
            process.kill();
        }
        
        this.testProcesses.clear();
        this.isRunning = false;
        
        this.log('Test watcher stopped', 'success');
        process.exit(0);
    }
}

// 命令行接口
if (require.main === module) {
    const watcher = new TestWatcher();
    watcher.start();
}

module.exports = TestWatcher;