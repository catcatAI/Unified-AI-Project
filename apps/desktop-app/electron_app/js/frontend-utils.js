/**
 * Angela AI - Frontend Utilities
 * 通用前端工具模块，提供健壮的边界情况处理
 */

const FrontendUtils = {
  // ==================== DOM 工具 ====================
  
  /**
   * 安全获取元素尺寸（考虑 DOM 布局时序）
   */
  getElementSize(element, defaultWidth = 800, defaultHeight = 600) {
    if (!element) return { width: defaultWidth, height: defaultHeight };
    
    // 优先使用 getBoundingClientRect（需要 DOM 已布局）
    if (element.getBoundingClientRect) {
      const rect = element.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        return {
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        };
      }
    }
    
    // 回退到 window 尺寸
    return {
      width: window.innerWidth || defaultWidth,
      height: window.innerHeight || defaultHeight
    };
  },
  
  /**
   * 等待 DOM 布局完成
   */
  waitForLayout(timeout = 1000) {
    return new Promise((resolve) => {
      // 立即检查
      const check = () => {
        const dummy = document.createElement('div');
        const rect = dummy.getBoundingClientRect();
        if (rect.width >= 0) {
          resolve();
        } else if (Date.now() > start + timeout) {
          console.warn('[FrontendUtils] DOM layout timeout, proceeding anyway');
          resolve();
        } else {
          requestAnimationFrame(check);
        }
      };
      const start = Date.now();
      requestAnimationFrame(check);
    });
  },
  
  /**
   * 防抖函数
   */
  debounce(fn, delay = 100) {
    let timer = null;
    return function (...args) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },
  
  /**
   * 节流函数
   */
  throttle(fn, interval = 100) {
    let lastTime = 0;
    return function (...args) {
      const now = Date.now();
      if (now - lastTime >= interval) {
        lastTime = now;
        fn.apply(this, args);
      }
    };
  },
  
  // ==================== 路径工具 ====================
  
  /**
   * 安全解析模型路径
   * @param {string} modelPath - 模型路径（可能是目录名、相对路径或绝对路径）
   * @param {Object} options - 选项
   * @returns {Object} {fullPath: string, isFile: boolean, error?: string}
   */
  resolveModelPath(modelPath, options = {}) {
    const {
      modelsDir = '/home/cat/桌面/Unified-AI-Project/resources/models',
      requiredPattern = '_t03.model3.json'
    } = options;
    
    if (!modelPath || typeof modelPath !== 'string') {
      return { fullPath: '', isFile: false, error: 'Invalid model path' };
    }
    
    // 规范化路径分隔符
    const normalizedPath = modelPath.replace(/\\/g, '/');
    
    // 判断路径类型
    let fullPath;
    let isFile = false;
    
    if (normalizedPath.startsWith('/') || normalizedPath.includes(':')) {
      // 绝对路径
      fullPath = normalizedPath;
      isFile = this.isFile(fullPath);
    } else if (normalizedPath.includes('/')) {
      // 相对路径（包含目录）
      fullPath = this.pathJoin(modelsDir, normalizedPath);
      isFile = this.isFile(fullPath);
    } else {
      // 仅仅是模型名称
      const modelDir = this.pathJoin(modelsDir, normalizedPath);
      
      if (this.isDir(modelDir)) {
        // 查找模型文件
        const modelFile = this.findFileInDir(modelDir, requiredPattern) ||
                          this.findFileInDir(modelDir, '.model3.json');
        if (modelFile) {
          fullPath = modelFile;
          isFile = true;
        } else {
          fullPath = modelDir;
          isFile = false;
        }
      } else {
        fullPath = modelDir;
        isFile = false;
      }
    }
    
    return { fullPath, isFile };
  },
  
  /**
   * 路径拼接（跨平台）
   */
  pathJoin(...parts) {
    return parts
      .map(part => part.replace(/[\/\\]+/g, '/').replace(/\/$/, ''))
      .filter(Boolean)
      .join('/');
  },
  
  /**
   * 检查路径是否为文件
   */
  isFile(filePath) {
    try {
      return require('fs').existsSync(filePath) && 
             require('fs').statSync(filePath).isFile();
    } catch (e) {
      return false;
    }
  },
  
  /**
   * 检查路径是否为目录
   */
  isDir(dirPath) {
    try {
      return require('fs').existsSync(dirPath) && 
             require('fs').statSync(dirPath).isDirectory();
    } catch (e) {
      return false;
    }
  },
  
  /**
   * 在目录中查找文件
   */
  findFileInDir(dirPath, pattern) {
    if (!this.isDir(dirPath)) return null;
    
    try {
      const files = require('fs').readdirSync(dirPath);
      const match = files.find(f => 
        pattern.startsWith('*') ? f.endsWith(pattern.slice(1)) : f.includes(pattern)
      );
      return match ? require('path').join(dirPath, match) : null;
    } catch (e) {
      return null;
    }
  },
  
  /**
   * 从文件路径提取目录
   */
  dirname(filePath) {
    const normalized = filePath.replace(/\\/g, '/');
    const lastSlash = normalized.lastIndexOf('/');
    return lastSlash > 0 ? normalized.slice(0, lastSlash) : normalized;
  },
  
  // ==================== 页面可见性工具 ====================
  
  /**
   * 页面可见性管理器
   */
  visibility: {
    _listeners: [],
    _isVisible: true,
    
    init() {
      document.addEventListener('visibilitychange', () => {
        this._isVisible = !document.hidden;
        this._listeners.forEach(cb => cb(this._isVisible));
      });
    },
    
    get isVisible() {
      return !document.hidden && this._isVisible;
    },
    
    onChange(callback) {
      this._listeners.push(callback);
      return () => {
        this._listeners = this._listeners.filter(cb => cb !== callback);
      };
    },
    
    whenVisible(fn, fallback = null) {
      if (this.isVisible) {
        fn();
      } else if (fallback) {
        fallback();
      }
    }
  },
  
  // ==================== WebGL 工具 ====================
  
  // WebGL Context 管理器
  _webglContextManager: {
    contexts: new WeakMap(),
    maxContexts: 3,
    _createdContexts: [],
    
    register(canvas, gl) {
      if (!this.contexts.has(canvas)) {
        if (this._createdContexts.length >= this.maxContexts) {
          console.warn(`WebGL Context count limit reached (${this.maxContexts}), cleaning up oldest`);
          this.cleanupOldest();
        }
        this.contexts.set(canvas, { gl, createdAt: Date.now() });
        this._createdContexts.push(canvas);
        console.log(`WebGL Context registered (${this._createdContexts.length}/${this.maxContexts})`);
      }
    },
    
    unregister(canvas) {
      if (this.contexts.has(canvas)) {
        const ctx = this.contexts.get(canvas);
        if (ctx.gl) {
          const ext = ctx.gl.getExtension('WEBGL_lose_context');
          if (ext) ext.loseContext();
        }
        this.contexts.delete(canvas);
        this._createdContexts = this._createdContexts.filter(c => c !== canvas);
      }
    },
    
    cleanupOldest() {
      if (this._createdContexts.length > 0) {
        const oldest = this._createdContexts[0];
        this.unregister(oldest);
      }
    },
    
    getCount() {
      return this._createdContexts.length;
    }
  },
  
  /**
   * 检查 WebGL 扩展（兼容性模式）
   */
  checkGLExtensions(gl, required = [], optional = []) {
    const result = {
      supported: [],
      missing: [],
      allRequired: true
    };
    
    // 必需扩展
    for (const ext of required) {
      const supported = gl.getExtension(ext);
      if (supported) {
        result.supported.push(ext);
      } else {
        result.missing.push(ext);
        result.allRequired = false;
      }
    }
    
    // 可选扩展（记录但不阻止）
    for (const ext of optional) {
      const supported = gl.getExtension(ext);
      if (supported) {
        result.supported.push(ext);
      } else {
        result.missing.push(ext);
      }
    }
    
    return result;
  },
  
  /**
   * 获取安全的 WebGL 上下文
   */
  getWebGLContext(canvas, options = {}) {
    const defaults = {
      alpha: false,
      antialias: false,
      preserveDrawingBuffer: true,
      powerPreference: 'low-power',
      desynchronized: true,
      failIfMajorPerformanceCaveat: false
    };
    
    const glOptions = { ...defaults, ...options };
    
    const contexts = ['webgl2', 'webgl', 'experimental-webgl'];
    
    for (const ctxName of contexts) {
      const gl = canvas.getContext(ctxName, glOptions);
      if (gl) {
        // 註冊 Context 以追蹤和管理
        this._webglContextManager.register(canvas, gl);
        return gl;
      }
    }
    
    return null;
  },
  
  // ==================== 资源加载工具 ====================
  
  /**
   * 安全的图片加载（带超时）
   */
  loadImage(src, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const timer = setTimeout(() => {
        reject(new Error(`Image load timeout: ${src}`));
      }, timeout);
      
      img.onload = () => {
        clearTimeout(timer);
        resolve(img);
      };
      
      img.onerror = () => {
        clearTimeout(timer);
        reject(new Error(`Failed to load image: ${src}`));
      };
      
      img.src = src;
    });
  },
  
  /**
   * 安全的 JSON 加载
   */
  async loadJSON(url, timeout = 5000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      clearTimeout(timer);
      return data;
    } catch (e) {
      clearTimeout(timer);
      throw new Error(`Failed to load JSON: ${url} - ${e.message}`);
    }
  },
  
  // ==================== 性能工具 ====================
  
  /**
   * 创建节流的动画循环
   */
  createThrottledAnimation(targetFPS = 60, renderFn) {
    const frameInterval = 1000 / targetFPS;
    let lastFrameTime = 0;
    
    return (timestamp) => {
      const elapsed = timestamp - lastFrameTime;
      
      if (elapsed >= frameInterval) {
        lastFrameTime = timestamp - (elapsed % frameInterval);
        renderFn();
      }
      
      return requestAnimationFrame((t) => this.createThrottledAnimation(targetFPS, renderFn)(t));
    };
  },
  
  /**
   * FPS 计数器
   */
  createFPSCounter(maxHistory = 60) {
    let frames = 0;
    let lastTime = performance.now();
    const history = [];
    
    return {
      tick() {
        frames++;
        const now = performance.now();
        const elapsed = now - lastTime;
        
        if (elapsed >= 1000) {
          const fps = Math.round((frames * 1000) / elapsed);
          history.push(fps);
          if (history.length > maxHistory) history.shift();
          frames = 0;
          lastTime = now;
          return fps;
        }
        return null;
      },
      
      getAverage() {
        if (history.length === 0) return 60;
        return Math.round(history.reduce((a, b) => a + b, 0) / history.length);
      }
    };
  },
  
  // ==================== 错误处理工具 ====================
  
  /**
   * 创建安全的函数包装器
   */
  safe(fn, fallback = null, context = 'unknown') {
    return (...args) => {
      try {
        return fn(...args);
      } catch (e) {
        console.warn(`[FrontendUtils] Error in ${context}:`, e.message);
        return fallback;
      }
    };
  },
  
  /**
   * 创建异步安全的函数包装器
   */
  async safeAsync(fn, fallback = null, context = 'unknown') {
    try {
      return await fn();
    } catch (e) {
      console.warn(`[FrontendUtils] Async error in ${context}:`, e.message);
      return fallback;
    }
  },
  
  // ==================== 配置工具 ====================
  
  /**
   * 合并配置（深度）
   */
  deepMerge(target, source) {
    const result = { ...target };
    
    for (const key of Object.keys(source)) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  },
  
  /**
   * 获取带默认值的配置
   */
  getConfig(config, defaults) {
    return this.deepMerge(defaults, config || {});
  }
};

// 初始化页面可见性
FrontendUtils.visibility.init();

// 导出到全局
if (typeof window !== 'undefined') {
  window.FrontendUtils = FrontendUtils;
}
