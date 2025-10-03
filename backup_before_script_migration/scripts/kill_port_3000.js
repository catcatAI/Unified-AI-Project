/**
 * 脚本用于杀死占用3000端口的进程
 */

const { execSync } = require('child_process');

function killPort3000() {
  try {
    console.log('Checking for processes on port 3000...');
    
    // 查找占用3000端口的进程
    const result = execSync('netstat -ano | findstr :3000', { encoding: 'utf8' });
    const lines = result.split('\n');
    
    let foundProcesses = false;
    for (const line of lines) {
      if (line.includes('LISTENING')) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 5) {
          const pid = parts[4];
          if (pid && !isNaN(parseInt(pid))) {
            console.log(`Found process ${pid} on port 3000, attempting to kill...`);
            try {
              execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
              console.log(`Successfully killed process ${pid}`);
              foundProcesses = true;
            } catch (killError) {
              console.log(`Failed to kill process ${pid}:`, killError.message);
            }
          }
        }
      }
    }
    
    if (!foundProcesses) {
      console.log('No processes found on port 3000');
    }
  } catch (error) {
    if (error.status === 1) {
      console.log('No processes found on port 3000');
    } else {
      console.error('Error checking port 3000:', error.message);
    }
  }
}

// 如果直接运行此脚本，则执行主函数
if (require.main === module) {
  killPort3000();
}

module.exports = killPort3000;