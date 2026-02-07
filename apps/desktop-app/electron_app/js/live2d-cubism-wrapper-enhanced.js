/**
 * Angela AI - Enhanced Live2D Cubism Web SDK Wrapper
 * 
 * 优化版本，支持多种加载方式和更好的错误处理
 * 专门为核显和笔记本电脑优化
 */

class EnhancedLive2DCubismWrapper {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = null;
        this.sdkLoaded = false;
        this.cubismSdk = null;
        this.live2dModel = null;
        this.isLoaded = false;
        this.isRunning = false;
        this.targetFPS = 60;
        
        this.callbacks = {
            onLoaded: null,
            onMotionFinished: null,
            onError: null
        };
        
        this.loadSDK();
    }
    
    async loadSDK() {
        console.log('🔄 Loading Enhanced Live2D Cubism Web SDK...');
        
        try {
            // 检查是否已加载
            if (window.Live2DCubismCore) {
                this.cubismSdk = window.Live2DCubismCore;
                this.sdkLoaded = true;
                console.log('✅ Live2D Cubism Core already loaded');
                return;
            }
            
            // 尝试多种加载方式
            await this.loadCubismScriptWithFallback();
            await this.waitForCubismSDK();
            
            this.sdkLoaded = true;
            console.log('✅ Enhanced Live2D Cubism SDK loaded successfully');
        } catch (error) {
            console.error('❌ Failed to load Live2D Cubism SDK:', error);
            this.handleSDKLoadFailure(error);
            throw error;
        }
    }
    
    async loadCubismScriptWithFallback() {
        console.log('🔄 Attempting to load Live2D Cubism SDK with fallback mechanisms...');
        
        // 方法1: 本地加载（最高优先级）
        try {
            console.log('📦 Trying local SDK loading...');
            await this.loadLocalCubismScript();
            return;
        } catch (localError) {
            console.warn('⚠️ Local SDK loading failed:', localError.message);
        }
        
        // 方法2: 多CDN重试机制
        console.log('🌐 Falling back to CDN loading with retry mechanism...');
        const cdnSources = [
            {
                name: 'Official Live2D CDN',
                url: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js'
            },
            {
                name: 'jsDelivr CDN',
                url: 'https://cdn.jsdelivr.net/npm/live2d-cubism-sdk-core@4.2.0/dist/live2dcubismcore.min.js'
            },
            {
                name: 'UNPKG CDN',
                url: 'https://unpkg.com/live2d-cubism-sdk-core@4.2.0/dist/live2dcubismcore.min.js'
            }
        ];
        
        for (let i = 0; i < cdnSources.length; i++) {
            const source = cdnSources[i];
            try {
                console.log(`📡 Trying ${source.name} (${i + 1}/${cdnSources.length}): ${source.url}`);
                await this.loadFromUrl(source.url);
                console.log(`✅ Successfully loaded from ${source.name}`);
                return;
            } catch (cdnError) {
                console.warn(`⚠️ ${source.name} failed:`, cdnError.message);
                if (i === cdnSources.length - 1) {
                    throw new Error(`All loading methods failed. Last error: ${cdnError.message}`);
                }
            }
        }
    }
    
    async loadLocalCubismScript() {
        // 检查Electron环境中本地资源
        const localPaths = [
            './assets/live2dcubismcore.min.js',
            '../assets/live2dcubismcore.min.js',
            '../../assets/live2dcubismcore.min.js'
        ];
        
        for (const path of localPaths) {
            try {
                console.log(`🔍 Checking local path: ${path}`);
                await this.loadFromUrl(path);
                console.log(`✅ Local SDK loaded from: ${path}`);
                return;
            } catch (error) {
                console.log(`⏭️ Local path not found: ${path}`);
                continue;
            }
        }
        
        throw new Error('Local SDK not found in any checked paths');
    }
    
    loadFromUrl(url) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.async = true;
            script.crossOrigin = 'anonymous';
            
            // 更长的超时时间，适应网络波动
            const timeoutId = setTimeout(() => {
                script.remove();
                reject(new Error(`Script loading timeout after 10 seconds: ${url}`));
            }, 10000);
            
            script.onload = () => {
                clearTimeout(timeoutId);
                console.log(`✅ Script loaded successfully: ${url}`);
                resolve();
            };
            
            script.onerror = (error) => {
                clearTimeout(timeoutId);
                script.remove();
                console.error(`❌ Script loading failed: ${url}`, error);
                reject(new Error(`Failed to load script from ${url}`));
            };
            
            document.head.appendChild(script);
        });
    }
    
    waitForCubismSDK(maxChecks = 50) {
        return new Promise((resolve, reject) => {
            let checks = 0;
            const checkInterval = setInterval(() => {
                checks++;
                if (window.Live2DCubismCore) {
                    clearInterval(checkInterval);
                    console.log(`✅ Live2D Cubism SDK detected after ${checks} checks (${checks * 200}ms)`);
                    resolve();
                } else if (checks >= maxChecks) {
                    clearInterval(checkInterval);
                    reject(new Error(`Live2D Cubism SDK not detected after ${maxChecks} checks (${maxChecks * 200}ms)`));
                }
            }, 200); // 每200ms检查一次
        });
    }
    
    handleSDKLoadFailure(error) {
        console.error('💥 SDK Load Failure Handler Activated');
        console.error('Error details:', error);
        
        // 提供降级方案
        this.createFallbackRenderer();
    }
    
    createFallbackRenderer() {
        console.log('🔄 Creating fallback renderer for degraded experience');
        
        // 创建简单的Canvas 2D渲染作为后备
        this.gl = this.canvas.getContext('2d');
        if (this.gl) {
            this.isLoaded = true;
            this.isRunning = true;
            
            // 绘制占位符
            this.drawPlaceholder();
            
            if (this.callbacks.onLoaded) {
                this.callbacks.onLoaded({
                    success: true,
                    fallback: true,
                    message: 'Using 2D canvas fallback renderer'
                });
            }
        } else {
            if (this.callbacks.onError) {
                this.callbacks.onError(new Error('Cannot create any rendering context'));
            }
        }
    }
    
    drawPlaceholder() {
        if (!this.gl || !this.gl.clearRect) return;
        
        const ctx = this.gl;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // 清除画布
        ctx.clearRect(0, 0, width, height);
        
        // 绘制占位符
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, width, height);
        
        ctx.fillStyle = '#666';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Live2D Loading...', width/2, height/2);
        ctx.fillText('Please wait or check console', width/2, height/2 + 30);
    }
    
    // 保留原有接口以保证兼容性
    async initializeWebGL() {
        console.log('🎮 Initializing WebGL context (Enhanced)...');
        
        try {
            // 尝试WebGL2
            this.gl = this.canvas.getContext('webgl2', {
                alpha: true,
                antialias: true,
                depth: false,
                stencil: false,
                preserveDrawingBuffer: true,
                premultipliedAlpha: false
            });
            
            if (!this.gl) {
                // 回退到WebGL1
                console.log('🔄 WebGL2 not available, falling back to WebGL1');
                this.gl = this.canvas.getContext('webgl', {
                    alpha: true,
                    antialias: true,
                    depth: false,
                    stencil: false,
                    preserveDrawingBuffer: true,
                    premultipliedAlpha: false
                });
            }
            
            if (!this.gl) {
                throw new Error('WebGL not supported');
            }
            
            console.log('✅ WebGL context initialized successfully');
            return true;
        } catch (error) {
            console.error('❌ WebGL initialization failed:', error);
            this.createFallbackRenderer();
            return false;
        }
    }
    
    setCallback(event, callback) {
        if (this.callbacks.hasOwnProperty(event)) {
            this.callbacks[event] = callback;
        }
    }
}

// 导出增强版包装器
window.EnhancedLive2DCubismWrapper = EnhancedLive2DCubismWrapper;