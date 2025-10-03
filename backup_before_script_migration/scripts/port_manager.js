/**
 * Unified Port Manager Script
 * 自动检测和管理端口冲突
 */

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

// 统一端口配置
const PORT_CONFIG = {
  FRONTEND_DASHBOARD: 3000,
  DESKTOP_APP: 3001,
  BACKEND_API: 8000
};

// PID文件目录
const PID_DIR = path.join(require('os').homedir(), '.unified-ai', 'pids');

// 确保PID目录存在
function ensurePidDir() {
  if (!fs.existsSync(PID_DIR)) {
    fs.mkdirSync(PID_DIR, { recursive: true });
  }
}

// 检查端口是否被占用
function checkPortInUse(port) {
  return new Promise((resolve) => {
    const server = require('net').createServer();
    server.listen(port, '127.0.0.1');
    server.on('error', () => {
      resolve(true); // 端口被占用
    });
    server.on('listening', () => {
      server.close();
      resolve(false); // 端口未被占用
    });
  });
}

// 查找占用端口的进程PID
function findProcessByPort(port) {
  return new Promise((resolve) => {
    try {
      // 在Windows上使用PowerShell查找进程
      const command = `netstat -ano | findstr :${port} | findstr LISTENING`;
      const result = execSync(command, { encoding: 'utf8' });
      const lines = result.split('\n');
      for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 5) {
          const pid = parts[4];
          if (pid && !isNaN(pid)) {
            resolve(parseInt(pid));
            return;
          }
        }
      }
      resolve(null);
    } catch (error) {
      resolve(null);
    }
  });
}

// 杀死进程
function killProcess(pid) {
  return new Promise((resolve) => {
    try {
      process.kill(pid, 'SIGTERM');
      console.log(`Terminated process ${pid}`);
      resolve(true);
    } catch (error) {
      try {
        execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
        console.log(`Force killed process ${pid}`);
        resolve(true);
      } catch (error) {
        console.log(`Failed to kill process ${pid}`);
        resolve(false);
      }
    }
  });
}

// 保存PID
function savePid(serviceName, pid) {
  try {
    const pidFile = path.join(PID_DIR, `${serviceName.toLowerCase()}.pid`);
    fs.writeFileSync(pidFile, pid.toString());
    console.log(`Saved PID ${pid} for ${serviceName} to ${pidFile}`);
  } catch (error) {
    console.error(`Failed to save PID for ${serviceName}:`, error);
  }
}

// 加载PID
function loadPid(serviceName) {
  try {
    const pidFile = path.join(PID_DIR, `${serviceName.toLowerCase()}.pid`);
    if (fs.existsSync(pidFile)) {
      const pid = fs.readFileSync(pidFile, 'utf8').trim();
      return parseInt(pid);
    }
    return null;
  } catch (error) {
    console.error(`Failed to load PID for ${serviceName}:`, error);
    return null;
  }
}

// 杀死已存在的服务进程
async function killExistingProcess(serviceName) {
  console.log(`Checking for existing process for ${serviceName}...`);
  
  // 首先尝试通过PID文件杀死进程
  const savedPid = loadPid(serviceName);
  if (savedPid) {
    console.log(`Found saved PID ${savedPid} for ${serviceName}, attempting to terminate...`);
    try {
      process.kill(savedPid, 'SIGTERM');
      console.log(`Terminated process ${savedPid} for ${serviceName}`);
      
      // 删除PID文件
      const pidFile = path.join(PID_DIR, `${serviceName.toLowerCase()}.pid`);
      if (fs.existsSync(pidFile)) {
        fs.unlinkSync(pidFile);
      }
      
      return true;
    } catch (error) {
      console.log(`Process ${savedPid} for ${serviceName} may have already terminated`);
      
      // 删除PID文件
      const pidFile = path.join(PID_DIR, `${serviceName.toLowerCase()}.pid`);
      if (fs.existsSync(pidFile)) {
        fs.unlinkSync(pidFile);
      }
    }
  }
  
  // 如果通过PID文件失败，尝试通过端口杀死进程
  const port = PORT_CONFIG[serviceName.toUpperCase()];
  if (port) {
    const inUse = await checkPortInUse(port);
    if (inUse) {
      console.log(`Port ${port} for ${serviceName} is in use, finding process...`);
      const pid = await findProcessByPort(port);
      if (pid) {
        console.log(`Found process ${pid} on port ${port}, attempting to kill...`);
        return await killProcess(pid);
      }
    }
  }
  
  console.log(`No existing process found for ${serviceName}`);
  return false;
}

// 获取所有端口信息
function getAllPorts() {
  return { ...PORT_CONFIG };
}

// 打印端口信息
async function printPortInfo() {
  console.log('Unified AI Project Port Configuration:');
  console.log('========================================');
  
  for (const [service, port] of Object.entries(PORT_CONFIG)) {
    const inUse = await checkPortInUse(port) ? ' (IN USE)' : '';
    console.log(`${service.padEnd(20)}: ${port}${inUse}`);
  }
  
  console.log('========================================');
}

// 主函数
async function main() {
  ensurePidDir();
  
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.log('Usage: node port_manager.js [command] [service_name]');
    console.log('Commands:');
    console.log('  info              - Show port information');
    console.log('  check [port]      - Check if port is in use');
    console.log('  kill-service [service] - Kill existing service process');
    console.log('  get-port [service] - Get port for service');
    return;
  }
  
  switch (command) {
    case 'info':
      await printPortInfo();
      break;
      
    case 'check':
      if (args.length < 2) {
        console.log('Usage: node port_manager.js check [port]');
        return;
      }
      const port = parseInt(args[1]);
      const inUse = await checkPortInUse(port);
      console.log(`Port ${port} is ${inUse ? 'in use' : 'available'}`);
      break;
      
    case 'kill-service':
      if (args.length < 2) {
        console.log('Usage: node port_manager.js kill-service [service]');
        return;
      }
      const serviceName = args[1].toUpperCase();
      if (!PORT_CONFIG[serviceName]) {
        console.log(`Unknown service: ${args[1]}`);
        return;
      }
      const success = await killExistingProcess(serviceName);
      if (success) {
        console.log(`Successfully killed existing process for ${serviceName}`);
      } else {
        console.log(`No existing process found for ${serviceName}`);
      }
      break;
      
    case 'get-port':
      if (args.length < 2) {
        console.log('Usage: node port_manager.js get-port [service]');
        return;
      }
      const service = args[1].toUpperCase();
      const portValue = PORT_CONFIG[service];
      if (portValue) {
        console.log(`Port for ${service}: ${portValue}`);
      } else {
        console.log(`Unknown service: ${args[1]}`);
      }
      break;
      
    default:
      console.log(`Unknown command: ${command}`);
      console.log('Usage: node port_manager.js [command] [service_name]');
  }
}

// 如果直接运行此脚本，则执行主函数
if (require.main === module) {
  main().catch(console.error);
}

// 导出函数供其他模块使用
module.exports = {
  PORT_CONFIG,
  checkPortInUse,
  killExistingProcess,
  savePid,
  loadPid,
  getAllPorts,
  printPortInfo
};