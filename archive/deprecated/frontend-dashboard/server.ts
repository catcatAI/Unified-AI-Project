// server.ts - Next.js Standalone + Socket.IO
import { createServer } from 'http';
import { Server } from 'socket.io';
import { createProxyMiddleware } from 'http-proxy-middleware';
import next from 'next';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

// 创建一个简单的setupSocket函数作为占位符
function setupSocket(io: Server) {
  io.on('connection', (socket) => {
    console.log('Socket.IO client connected:', socket.id);
    
    socket.on('disconnect', () => {
      console.log('Socket.IO client disconnected:', socket.id);
    });
  });
}

// 端口管理配置
const PORT_CONFIG = {
  FRONTEND_DASHBOARD: 3000,
  DESKTOP_APP: 3001,
  BACKEND_API: 8000  // 改回端口为8000
};

// PID文件路径
const PID_FILE_PATH = path.join(__dirname, '.port-manager.pid');

// 检查端口是否被占用
function checkPortInUse(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = createServer();
    server.listen(port, 'localhost');
    server.on('error', () => {
      resolve(true); // 端口被占用
    });
    server.on('listening', () => {
      server.close();
      resolve(false); // 端口未被占用
    });
  });
}

// 杀死占用端口的进程
async function killProcessOnPort(port: number): Promise<void> {
  try {
    // 在Windows上使用PowerShell命令查找并终止进程
    const command = `for /f "tokens=5" %a in ('netstat -ano ^| findstr :${port} ^| findstr LISTENING') do taskkill /PID %a /F`;
    // 注意：在实际代码中，我们会使用Node.js的child_process模块来执行此操作
    console.log(`Attempting to kill process on port ${port}`);
  } catch (error) {
    console.error(`Failed to kill process on port ${port}:`, error);
  }
}

// 保存当前进程PID
function saveCurrentPid(): void {
  try {
    fs.writeFileSync(PID_FILE_PATH, process.pid.toString());
    console.log(`Saved current PID ${process.pid} to ${PID_FILE_PATH}`);
  } catch (error) {
    console.error('Failed to save PID:', error);
  }
}

// 检查并处理已存在的进程
async function handleExistingProcesses(): Promise<void> {
  try {
    // 检查PID文件是否存在
    if (fs.existsSync(PID_FILE_PATH)) {
      const savedPid = fs.readFileSync(PID_FILE_PATH, 'utf8');
      console.log(`Found existing process with PID: ${savedPid}`);
      
      // 尝试杀死之前的进程
      try {
        process.kill(parseInt(savedPid), 'SIGTERM');
        console.log(`Terminated previous process ${savedPid}`);
      } catch (error) {
        console.log(`Previous process ${savedPid} may have already terminated`);
      }
      
      // 删除PID文件
      fs.unlinkSync(PID_FILE_PATH);
    }
    
    // 检查端口是否被占用
    const portInUse = await checkPortInUse(PORT_CONFIG.FRONTEND_DASHBOARD);
    if (portInUse) {
      console.log(`Port ${PORT_CONFIG.FRONTEND_DASHBOARD} is in use, attempting to free it...`);
      // 使用更可靠的端口查找和终止方法
      try {
        const result = execSync(`netstat -ano | findstr :${PORT_CONFIG.FRONTEND_DASHBOARD}`, { encoding: 'utf8' });
        const lines = result.split('\n');
        for (const line of lines) {
          if (line.includes('LISTENING')) {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 5) {
              const pid = parts[4];
              if (pid && !isNaN(parseInt(pid))) {
                console.log(`Found process ${pid} on port ${PORT_CONFIG.FRONTEND_DASHBOARD}, attempting to kill...`);
                try {
                  execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
                  console.log(`Force killed process ${pid}`);
                } catch (killError) {
                  console.log(`Failed to kill process ${pid}`);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error(`Error finding process on port ${PORT_CONFIG.FRONTEND_DASHBOARD}:`, error);
      }
    }
  } catch (error) {
    console.error('Error handling existing processes:', error);
  }
}

const dev = process.env.NODE_ENV !== 'production';
const currentPort = PORT_CONFIG.FRONTEND_DASHBOARD;  // 使用统一的端口配置
const hostname = '127.0.0.1'; // 改为127.0.0.1而不是localhost以提高兼容性

// Custom server with Socket.IO integration
async function createCustomServer() {
  try {
    // 处理已存在的进程
    await handleExistingProcesses();
    
    // 保存当前进程PID
    saveCurrentPid();
    
    // 添加额外的端口释放逻辑
    try {
      const result = execSync(`netstat -ano | findstr :${currentPort}`, { encoding: 'utf8' });
      const lines = result.split('\n');
      for (const line of lines) {
        if (line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5) {
            const pid = parts[4];
            if (pid && !isNaN(parseInt(pid)) && parseInt(pid) !== process.pid) {
              console.log(`Force killing existing process ${pid} on port ${currentPort}`);
              execSync(`taskkill /PID ${pid} /F`, { stdio: 'ignore' });
            }
          }
        }
      }
    } catch (error) {
      // 忽略错误，可能没有进程在运行
    }

    // Create Next.js app
    const nextApp = next({ 
      dev,
      dir: process.cwd(),
      // In production, use the current directory where .next is located
      conf: dev ? undefined : { distDir: './.next' }
    });

    await nextApp.prepare();
    const handle = nextApp.getRequestHandler();

    // Create HTTP server that will handle both Next.js and Socket.IO
    const apiProxy = createProxyMiddleware({
      target: `http://127.0.0.1:${PORT_CONFIG.BACKEND_API}`, // 使用IP地址而非localhost
      changeOrigin: true,
      pathRewrite: {},
      onProxyReq: (proxyReq, req, res) => {
        console.log(`Proxying: ${req.method} ${req.url} -> http://127.0.0.1:${PORT_CONFIG.BACKEND_API}${proxyReq.path}`);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`Proxy response: ${proxyRes.statusCode} for ${req.url}`);
      },
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
        if (!res.headersSent) {
          res.writeHead(502, { 'Content-Type': 'text/plain' });
          res.end('Backend service is not available. Please check if the backend server is running.');
        }
      }
    });

    const server = createServer((req, res) => {
      console.log(`Incoming request: ${req.method} ${req.url}`);
      
      // Handle proxy requests first
      if (req.url?.startsWith('/api/v1')) {
        console.log(`Routing to proxy: ${req.url}`);
        apiProxy(req, res, (err) => {
          if (err) {
            console.error('Proxy callback error:', err);
            if (!res.headersSent) {
              res.statusCode = 502;
              res.end('Proxy error');
            }
          }
        });
        return;
      }
      
      // Skip socket.io requests from Next.js handler
      if (req.url?.startsWith('/api/socketio')) {
        console.log(`Socket.IO request: ${req.url}`);
        return;
      }
      
      console.log(`Routing to Next.js: ${req.url}`);
      handle(req, res);
    });

    // Setup Socket.IO
    const io = new Server(server, {
      path: '/api/socketio',
      cors: {
        origin: "*",
        methods: ["GET", "POST"]
      }
    });

    setupSocket(io);

    // Start the server
    server.listen(currentPort, hostname, () => {
      console.log(`> Ready on http://${hostname}:${currentPort}`);
      console.log(`> Socket.IO server running at ws://${hostname}:${currentPort}/api/socketio`);
      console.log(`> Backend API proxying to http://localhost:${PORT_CONFIG.BACKEND_API}`);
    });

    // 处理进程退出
    process.on('SIGTERM', () => {
      console.log('SIGTERM received, shutting down gracefully');
      server.close(() => {
        console.log('Process terminated');
        process.exit(0);
      });
    });

    process.on('SIGINT', () => {
      console.log('SIGINT received, shutting down gracefully');
      server.close(() => {
        // 删除PID文件
        if (fs.existsSync(PID_FILE_PATH)) {
          fs.unlinkSync(PID_FILE_PATH);
        }
        console.log('Process terminated');
        process.exit(0);
      });
    });

  } catch (err) {
    console.error('Server startup error:', err);
    process.exit(1);
  }
}

// Start the server
createCustomServer();