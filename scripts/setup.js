#!/usr/bin/env node

/**
 * Unified AI Project 项目设置脚本
 * 自动检查和安装项目依赖
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// 颜色输出
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

function colorLog(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function execPromise(command, options = {}) {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject({ error, stdout, stderr });
            } else {
                resolve({ stdout, stderr });
            }
        });
    });
}

async function checkCommand(command, name) {
    try {
        await execPromise(`${command} --version`);
        colorLog(`✓ ${name} 已安装`, 'green');
        return true;
    } catch (error) {
        colorLog(`✗ ${name} 未安装或不在 PATH 中`, 'red');
        return false;
    }
}

async function checkDependencies() {
    colorLog('检查系统依赖...', 'cyan');
    
    const deps = [
        { command: 'node', name: 'Node.js' },
        { command: 'pnpm', name: 'pnpm' },
        { command: 'python', name: 'Python' }
    ];
    
    const results = await Promise.all(
        deps.map(dep => checkCommand(dep.command, dep.name))
    );
    
    const allInstalled = results.every(result => result);
    
    if (!allInstalled) {
        colorLog('\n安装说明:', 'yellow');
        if (!results[0]) colorLog('- 安装 Node.js: https://nodejs.org/', 'yellow');
        if (!results[1]) colorLog('- 安装 pnpm: npm install -g pnpm', 'yellow');
        if (!results[2]) colorLog('- 安装 Python: https://python.org/', 'yellow');
        process.exit(1);
    }
    
    colorLog('✓ 所有系统依赖已满足', 'green');
    return true;
}

async function installNodeDependencies() {
    colorLog('\n安装 Node.js 依赖...', 'cyan');
    
    try {
        await execPromise('pnpm install', { cwd: process.cwd() });
        colorLog('✓ Node.js 依赖安装完成', 'green');
    } catch (error) {
        colorLog('✗ Node.js 依赖安装失败', 'red');
        console.error(error.stderr);
        process.exit(1);
    }
}

async function setupPythonEnvironment() {
    colorLog('\n设置 Python 环境...', 'cyan');
    
    const backendDir = path.join(process.cwd(), 'apps', 'backend');
    const venvDir = path.join(backendDir, 'venv');
    
    // 检查虚拟环境是否存在
    if (!fs.existsSync(venvDir)) {
        colorLog('创建 Python 虚拟环境...', 'yellow');
        try {
            await execPromise('python -m venv venv', { cwd: backendDir });
            colorLog('✓ Python 虚拟环境创建成功', 'green');
        } catch (error) {
            colorLog('✗ Python 虚拟环境创建失败', 'red');
            console.error(error.stderr);
            process.exit(1);
        }
    } else {
        colorLog('✓ Python 虚拟环境已存在', 'green');
    }
    
    // 安装 Python 依赖
    colorLog('安装 Python 依赖...', 'yellow');
    
    const isWindows = os.platform() === 'win32';
    const activateCmd = isWindows 
        ? 'venv\\\\Scripts\\\\activate.bat' 
        : 'source venv/bin/activate';
    
    const pipCommands = [
        'pip install --upgrade pip',
        'pip install -r requirements.txt',
        'pip install -r requirements-dev.txt'
    ];
    
    try {
        for (const cmd of pipCommands) {
            const fullCmd = isWindows 
                ? `${activateCmd} && ${cmd}`
                : `${activateCmd} && ${cmd}`;
            
            await execPromise(fullCmd, { 
                cwd: backendDir,
                shell: true 
            });
        }
        colorLog('✓ Python 依赖安装完成', 'green');
    } catch (error) {
        colorLog('✗ Python 依赖安装失败', 'red');
        console.error(error.stderr);
        process.exit(1);
    }
}

async function createConfigFiles() {
    colorLog('\n创建配置文件...', 'cyan');
    
    const configDir = path.join(process.cwd(), 'apps', 'backend', 'configs');
    const configFile = path.join(configDir, 'config.yaml');
    
    if (!fs.existsSync(configFile)) {
        const defaultConfig = `# Unified AI Project 配置文件
# 开发环境配置

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  debug: true
  reload: true

# ChromaDB 配置
chromadb:
  host: "localhost"
  port: 8001
  persist_directory: "./chromadb"

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# AI 模型配置
ai_models:
  use_simulated_resources: true
  default_model: "gpt-3.5-turbo"

# HSP 配置
hsp:
  mqtt_broker: "localhost"
  mqtt_port: 1883
  client_id: "unified_ai_backend"

# 安全配置
security:
  secret_key: "development-secret-key-change-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 30
`;
        
        fs.writeFileSync(configFile, defaultConfig);
        colorLog('✓ 默认配置文件已创建', 'green');
    } else {
        colorLog('✓ 配置文件已存在', 'green');
    }
}

async function runHealthCheck() {
    colorLog('\n运行健康检查...', 'cyan');
    
    try {
        const healthScript = path.join(process.cwd(), 'scripts', 'health_check.py');
        if (fs.existsSync(healthScript)) {
            await execPromise(`python "${healthScript}"`, { 
                cwd: process.cwd() 
            });
            colorLog('✓ 健康检查通过', 'green');
        } else {
            colorLog('! 健康检查脚本不存在，跳过', 'yellow');
        }
    } catch (error) {
        colorLog('! 健康检查失败，但不影响安装', 'yellow');
        console.log(error.stderr);
    }
}

async function showUsageInstructions() {
    colorLog('\n🎉 项目设置完成！', 'green');
    colorLog('\n使用说明:', 'cyan');
    colorLog('开发环境:', 'yellow');
    colorLog('  pnpm dev          - 启动后端和前端', 'reset');
    colorLog('  pnpm dev:backend  - 只启动后端', 'reset');
    colorLog('  pnpm dev:frontend - 只启动前端', 'reset');
    colorLog('  pnpm dev:desktop  - 启动桌面应用', 'reset');
    colorLog('  pnpm dev-test     - 开发环境 + 测试监控', 'reset');
    
    colorLog('\n测试:', 'yellow');
    colorLog('  pnpm test            - 运行所有测试', 'reset');
    colorLog('  pnpm test:backend    - 运行后端测试', 'reset');
    colorLog('  pnpm test:frontend   - 运行前端测试', 'reset');
    colorLog('  pnpm test:coverage   - 运行测试覆盖率', 'reset');
    colorLog('  pnpm test:watch      - 测试监听模式', 'reset');
    
    colorLog('\nWindows 用户也可以使用:', 'yellow');
    colorLog('  scripts\\\\dev.bat install  - 安装依赖', 'reset');
    colorLog('  scripts\\\\dev.bat dev      - 启动开发环境', 'reset');
    colorLog('  scripts\\\\dev.bat test     - 运行测试', 'reset');
    colorLog('  scripts\\\\dev.bat dev-test - 开发 + 测试', 'reset');
    
    colorLog('\n🚀 准备开始开发 Unified AI Project！', 'bright');
}

async function main() {
    try {
        colorLog('=== Unified AI Project 项目设置 ===', 'bright');
        
        await checkDependencies();
        await installNodeDependencies();
        await setupPythonEnvironment();
        await createConfigFiles();
        await runHealthCheck();
        await showUsageInstructions();
        
    } catch (error) {
        colorLog('设置过程中发生错误:', 'red');
        console.error(error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { main };