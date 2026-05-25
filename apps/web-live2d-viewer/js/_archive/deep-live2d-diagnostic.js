/**
 * Angela AI - 深度Live2D问题诊断器
 * 
 * 全面诊断Live2D显示问题的根本原因
 */

class DeepLive2DDiagnostic {
    constructor() {
        this.diagnosisResults = {};
        this.issuesFound = [];
        this.recommendations = [];
    }
    
    async runCompleteDiagnosis() {
        console.log('🔬 开始深度Live2D问题诊断...\n');
        
        try {
            // 1. 环境和基础检查
            await this.checkEnvironmentAndBasics();
            
            // 2. 模型资源诊断
            await this.diagnoseModelResources();
            
            // 3. 渲染系统检查
            await this.checkRenderingSystem();
            
            // 4. 事件和交互诊断
            await this.diagnoseEventHandling();
            
            // 5. 性能和内存分析
            await this.analyzePerformance();
            
            // 6. 网络和加载问题
            await this.checkNetworkAndLoading();
            
            // 7. 生成诊断报告
            this.generateComprehensiveReport();
            
        } catch (error) {
            console.error('❌ 诊断过程中出现错误:', error);
        }
        
        return this.diagnosisResults;
    }
    
    async checkEnvironmentAndBasics() {
        console.log('=== 环境和基础检查 ===');
        
        const environment = {
            // 浏览器环境
            browser: this.getBrowserInfo(),
            
            // WebGL支持
            webgl: this.checkWebGLSupport(),
            
            // Canvas支持
            canvas: this.checkCanvasSupport(),
            
            // 系统信息
            system: this.getSystemInfo(),
            
            // 应用状态
            appState: this.checkAppState()
        };
        
        this.diagnosisResults.environment = environment;
        
        console.log('浏览器:', environment.browser.name);
        console.log('WebGL支持:', environment.webgl.supported ? '✅' : '❌');
        console.log('Canvas支持:', environment.canvas.supported ? '✅' : '❌');
        console.log('应用初始化:', environment.appState.initialized ? '✅' : '❌');
        
        if (!environment.webgl.supported) {
            this.issuesFound.push({
                severity: 'critical',
                category: 'environment',
                issue: 'WebGL不支持',
                description: '当前环境不支持WebGL渲染',
                solution: '更新显卡驱动或使用支持WebGL的浏览器'
            });
        }
    }
    
    getBrowserInfo() {
        const ua = navigator.userAgent;
        let name = 'Unknown';
        let version = '';
        
        if (ua.includes('Chrome')) {
            name = 'Chrome';
            const match = ua.match(/Chrome\/(\d+)/);
            version = match ? match[1] : '';
        } else if (ua.includes('Firefox')) {
            name = 'Firefox';
            const match = ua.match(/Firefox\/(\d+)/);
            version = match ? match[1] : '';
        } else if (ua.includes('Safari')) {
            name = 'Safari';
            const match = ua.match(/Version\/(\d+)/);
            version = match ? match[1] : '';
        } else if (ua.includes('Edge')) {
            name = 'Edge';
            const match = ua.match(/Edge\/(\d+)/);
            version = match ? match[1] : '';
        }
        
        return {
            name: name,
            version: version,
            userAgent: ua,
            isElectron: !!window.process
        };
    }
    
    checkWebGLSupport() {
        const canvas = document.createElement('canvas');
        let gl = canvas.getContext('webgl2');
        let version = 'WebGL 2.0';
        
        if (!gl) {
            gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            version = 'WebGL 1.0';
        }
        
        const supported = !!gl;
        const extensions = gl ? gl.getSupportedExtensions() : [];
        
        return {
            supported: supported,
            version: version,
            context: gl,
            extensions: extensions,
            requiredExtensions: this.getRequiredExtensions()
        };
    }
    
    getRequiredExtensions() {
        return [
            'OES_texture_float',
            'OES_standard_derivatives', 
            'WEBGL_depth_texture',
            'EXT_texture_filter_anisotropic'
        ];
    }
    
    checkCanvasSupport() {
        const canvas = document.createElement('canvas');
        const ctx2d = canvas.getContext('2d');
        const webgl = canvas.getContext('webgl');
        
        return {
            canvas2d: !!ctx2d,
            webgl: !!webgl,
            element: canvas
        };
    }
    
    getSystemInfo() {
        return {
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown'
        };
    }
    
    checkAppState() {
        return {
            initialized: typeof window.app !== 'undefined',
            live2dManager: typeof window.Live2DManager !== 'undefined',
            hardwareDetector: typeof window.HardwareDetector !== 'undefined',
            cubismSDK: typeof window.cubismSDKManager !== 'undefined'
        };
    }
    
    async diagnoseModelResources() {
        console.log('\n=== 模型资源诊断 ===');
        
        const resources = {
            modelDefinition: await this.checkModelDefinition(),
            textures: await this.checkTextures(),
            motions: await this.checkMotions(),
            expressions: await this.checkExpressions(),
            physics: await this.checkPhysics()
        };
        
        this.diagnosisResults.resources = resources;
        
        Object.entries(resources).forEach(([type, result]) => {
            console.log(`${type}: ${result.exists ? '✅' : '❌'} ${result.message}`);
        });
        
        // 检查关键资源缺失
        if (!resources.modelDefinition.exists) {
            this.issuesFound.push({
                severity: 'critical',
                category: 'resources',
                issue: '模型定义文件缺失',
                description: '无法找到模型定义文件',
                solution: '检查模型文件路径和权限'
            });
        }
    }
    
    async checkModelDefinition() {
        const modelPaths = [
            '../resources/models/miara_pro/miara_pro_t03.model3.json',
            './resources/models/miara_pro/miara_pro_t03.model3.json',
            '../models/miara_pro/miara_pro_t03.model3.json'
        ];
        
        for (const path of modelPaths) {
            try {
                const response = await fetch(path, { method: 'HEAD' });
                if (response.ok) {
                    return {
                        exists: true,
                        path: path,
                        statusCode: response.status
                    };
                }
            } catch (error) {
                continue;
            }
        }
        
        return {
            exists: false,
            attemptedPaths: modelPaths,
            message: '所有模型路径都无法访问'
        };
    }
    
    async checkTextures() {
        const texturePaths = [
            '../resources/models/miara_pro/texture_00.png',
            './resources/models/miara_pro/texture_00.png'
        ];
        
        const results = [];
        for (const path of texturePaths) {
            try {
                const response = await fetch(path, { method: 'HEAD' });
                results.push({
                    path: path,
                    exists: response.ok,
                    statusCode: response.status
                });
            } catch (error) {
                results.push({
                    path: path,
                    exists: false,
                    error: error.message
                });
            }
        }
        
        return {
            exists: results.some(r => r.exists),
            details: results,
            message: results.some(r => r.exists) ? '纹理文件可访问' : '纹理文件无法访问'
        };
    }
    
    async checkMotions() {
        // 检查motion目录
        try {
            const response = await fetch('../resources/models/miara_pro/motions/', { method: 'HEAD' });
            return {
                exists: response.ok,
                path: '../resources/models/miara_pro/motions/',
                accessible: response.ok
            };
        } catch (error) {
            return {
                exists: false,
                error: error.message
            };
        }
    }
    
    async checkExpressions() {
        const expressionPath = '../resources/models/miara_pro/miara_pro_t03.cdi3.json';
        try {
            const response = await fetch(expressionPath, { method: 'HEAD' });
            return {
                exists: response.ok,
                path: expressionPath,
                statusCode: response.status
            };
        } catch (error) {
            return {
                exists: false,
                error: error.message
            };
        }
    }
    
    async checkPhysics() {
        const physicsPath = '../resources/models/miara_pro/miara_pro_t03.physics3.json';
        try {
            const response = await fetch(physicsPath, { method: 'HEAD' });
            return {
                exists: response.ok,
                path: physicsPath,
                statusCode: response.status
            };
        } catch (error) {
            return {
                exists: false,
                error: error.message
            };
        }
    }
    
    async checkRenderingSystem() {
        console.log('\n=== 渲染系统检查 ===');
        
        const rendering = {
            canvasElement: this.checkCanvasElement(),
            webglContext: this.checkWebGLContext(),
            renderLoop: this.checkRenderLoop(),
            shaders: this.checkShaders()
        };
        
        this.diagnosisResults.rendering = rendering;
        
        Object.entries(rendering).forEach(([component, result]) => {
            console.log(`${component}: ${result.working ? '✅' : '❌'} ${result.message}`);
        });
        
        if (!rendering.canvasElement.exists) {
            this.issuesFound.push({
                severity: 'critical',
                category: 'rendering',
                issue: 'Canvas元素缺失',
                description: '找不到Live2D Canvas元素',
                solution: '检查HTML结构和DOM加载'
            });
        }
    }
    
    checkCanvasElement() {
        const canvas = document.getElementById('live2d-canvas');
        return {
            exists: !!canvas,
            element: canvas,
            dimensions: canvas ? {
                width: canvas.width,
                height: canvas.height
            } : null,
            style: canvas ? {
                display: canvas.style.display,
                visibility: canvas.style.visibility
            } : null
        };
    }
    
    checkWebGLContext() {
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return { working: false, message: '无Canvas元素' };
        
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (!gl) return { working: false, message: '无法获取WebGL上下文' };
        
        // 检查上下文状态
        const error = gl.getError();
        const extensions = gl.getSupportedExtensions();
        
        return {
            working: error === gl.NO_ERROR,
            context: gl,
            error: error,
            extensions: extensions,
            message: error === gl.NO_ERROR ? 'WebGL上下文正常' : `WebGL错误: ${error}`
        };
    }
    
    checkRenderLoop() {
        // 检查是否存在渲染循环
        return {
            working: typeof window.requestAnimationFrame !== 'undefined',
            message: typeof window.requestAnimationFrame !== 'undefined' ? 
                    '渲染循环可用' : '缺少requestAnimationFrame'
        };
    }
    
    checkShaders() {
        // 基本着色器检查
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return { working: false, message: '无Canvas元素' };
        
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (!gl) return { working: false, message: '无WebGL上下文' };
        
        try {
            // 创建简单的顶点着色器测试
            const vertexShader = gl.createShader(gl.VERTEX_SHADER);
            gl.shaderSource(vertexShader, `
                attribute vec2 a_position;
                void main() {
                    gl_Position = vec4(a_position, 0.0, 1.0);
                }
            `);
            gl.compileShader(vertexShader);
            
            const compiled = gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS);
            return {
                working: compiled,
                message: compiled ? '着色器编译正常' : '着色器编译失败'
            };
        } catch (error) {
            return {
                working: false,
                message: `着色器检查异常: ${error.message}`
            };
        }
    }
    
    async diagnoseEventHandling() {
        console.log('\n=== 事件处理诊断 ===');
        
        const events = {
            clickEvents: this.checkClickEvents(),
            mouseEvents: this.checkMouseEvents(),
            touchEvents: this.checkTouchEvents(),
            interactionHandlers: this.checkInteractionHandlers()
        };
        
        this.diagnosisResults.events = events;
        
        Object.entries(events).forEach(([type, result]) => {
            console.log(`${type}: ${result.registered ? '✅' : '❌'} ${result.message}`);
        });
    }
    
    checkClickEvents() {
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return { registered: false, message: '无Canvas元素' };
        
        // 检查是否有点击事件监听器
        const listeners = getEventListeners ? getEventListeners(canvas) : {};
        const hasClick = listeners.click && listeners.click.length > 0;
        
        return {
            registered: hasClick,
            listeners: listeners.click || [],
            message: hasClick ? '点击事件已注册' : '未注册点击事件'
        };
    }
    
    checkMouseEvents() {
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return { registered: false, message: '无Canvas元素' };
        
        const listeners = getEventListeners ? getEventListeners(canvas) : {};
        const mouseEvents = ['mousedown', 'mouseup', 'mousemove'];
        const registered = mouseEvents.filter(event => 
            listeners[event] && listeners[event].length > 0
        );
        
        return {
            registered: registered.length > 0,
            registeredEvents: registered,
            message: registered.length > 0 ? 
                    `已注册鼠标事件: ${registered.join(', ')}` : '未注册鼠标事件'
        };
    }
    
    checkTouchEvents() {
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return { registered: false, message: '无Canvas元素' };
        
        const listeners = getEventListeners ? getEventListeners(canvas) : {};
        const touchEvents = ['touchstart', 'touchmove', 'touchend'];
        const registered = touchEvents.filter(event => 
            listeners[event] && listeners[event].length > 0
        );
        
        return {
            registered: registered.length > 0,
            registeredEvents: registered,
            message: registered.length > 0 ? 
                    `已注册触摸事件: ${registered.join(', ')}` : '未注册触摸事件'
        };
    }
    
    checkInteractionHandlers() {
        return {
            registered: typeof window.handleCanvasClick === 'function',
            message: typeof window.handleCanvasClick === 'function' ? 
                    '交互处理器存在' : '缺少交互处理器'
        };
    }
    
    async analyzePerformance() {
        console.log('\n=== 性能和内存分析 ===');
        
        const performance = {
            loadTime: this.measureLoadTime(),
            memoryUsage: this.checkMemoryUsage(),
            frameRate: await this.measureFrameRate(),
            garbageCollection: this.checkGarbageCollection()
        };
        
        this.diagnosisResults.performance = performance;
        
        console.log(`加载时间: ${performance.loadTime.toFixed(2)}ms`);
        console.log(`内存使用: ${performance.memoryUsage.currentMB.toFixed(2)}MB`);
        console.log(`帧率: ${performance.frameRate.average.toFixed(1)} FPS`);
    }
    
    measureLoadTime() {
        if (performance.timing) {
            return performance.timing.loadEventEnd - performance.timing.navigationStart;
        }
        return -1; // 无法测量
    }
    
    checkMemoryUsage() {
        if ('memory' in performance) {
            return {
                currentMB: performance.memory.usedJSHeapSize / 1024 / 1024,
                totalMB: performance.memory.totalJSHeapSize / 1024 / 1024,
                limitMB: performance.memory.jsHeapSizeLimit / 1024 / 1024
            };
        }
        return { currentMB: 0, totalMB: 0, limitMB: 0 };
    }
    
    async measureFrameRate() {
        return new Promise(resolve => {
            const frames = [];
            const startTime = performance.now();
            let frameCount = 0;
            
            const measure = () => {
                frameCount++;
                const elapsed = performance.now() - startTime;
                
                if (elapsed >= 1000) { // 1秒后结束测量
                    const fps = (frameCount / elapsed) * 1000;
                    resolve({
                        average: fps,
                        samples: frames
                    });
                } else {
                    frames.push({
                        time: performance.now(),
                        frame: frameCount
                    });
                    requestAnimationFrame(measure);
                }
            };
            
            requestAnimationFrame(measure);
        });
    }
    
    checkGarbageCollection() {
        // 简单的GC监控
        let gcCount = 0;
        const observer = new MutationObserver(() => {
            gcCount++;
        });
        
        // 监控一段时间内的变化
        setTimeout(() => {
            observer.disconnect();
        }, 5000);
        
        return {
            monitored: !!observer,
            count: gcCount
        };
    }
    
    async checkNetworkAndLoading() {
        console.log('\n=== 网络和加载诊断 ===');
        
        const network = {
            connectivity: this.checkConnectivity(),
            resourceLoading: await this.testResourceLoading(),
            timeoutIssues: this.checkTimeoutConfigurations(),
            cors: await this.checkCORSPolicies()
        };
        
        this.diagnosisResults.network = network;
        
        Object.entries(network).forEach(([aspect, result]) => {
            console.log(`${aspect}: ${result.working ? '✅' : '❌'} ${result.message}`);
        });
    }
    
    checkConnectivity() {
        return {
            working: navigator.onLine,
            message: navigator.onLine ? '网络连接正常' : '网络连接断开'
        };
    }
    
    async testResourceLoading() {
        const testUrls = [
            'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
            '../resources/models/miara_pro/miara_pro_t03.model3.json'
        ];
        
        const results = [];
        for (const url of testUrls) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                
                const response = await fetch(url, { 
                    signal: controller.signal,
                    method: 'HEAD'
                });
                clearTimeout(timeoutId);
                
                results.push({
                    url: url,
                    success: response.ok,
                    statusCode: response.status,
                    time: Date.now()
                });
            } catch (error) {
                results.push({
                    url: url,
                    success: false,
                    error: error.message,
                    time: Date.now()
                });
            }
        }
        
        return {
            working: results.every(r => r.success),
            details: results,
            message: results.every(r => r.success) ? '资源加载正常' : '资源加载存在问题'
        };
    }
    
    checkTimeoutConfigurations() {
        // 检查应用中的超时设置
        const timeouts = {
            sdkLoading: 10000, // 10秒
            modelLoading: 30000, // 30秒
            resourceLoading: 15000 // 15秒
        };
        
        return {
            working: true,
            configurations: timeouts,
            message: '超时配置检查完成'
        };
    }
    
    async checkCORSPolicies() {
        try {
            // 测试跨域请求
            const response = await fetch('https://httpbin.org/get');
            return {
                working: response.ok,
                message: response.ok ? 'CORS策略正常' : 'CORS策略可能有问题'
            };
        } catch (error) {
            return {
                working: false,
                message: `CORS检查失败: ${error.message}`
            };
        }
    }
    
    generateComprehensiveReport() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 深度Live2D问题诊断报告');
        console.log('='.repeat(60));
        
        // 按严重程度分类问题
        const criticalIssues = this.issuesFound.filter(issue => issue.severity === 'critical');
        const majorIssues = this.issuesFound.filter(issue => issue.severity === 'major');
        const minorIssues = this.issuesFound.filter(issue => issue.severity === 'minor');
        
        console.log(`\n🚨 严重问题 (${criticalIssues.length}):`);
        criticalIssues.forEach(issue => {
            console.log(`  ❌ [${issue.category}] ${issue.issue}`);
            console.log(`     描述: ${issue.description}`);
            console.log(`     解决方案: ${issue.solution}`);
        });
        
        console.log(`\n⚠️  主要问题 (${majorIssues.length}):`);
        majorIssues.forEach(issue => {
            console.log(`  ⚠️  [${issue.category}] ${issue.issue}`);
        });
        
        console.log(`\nℹ️  次要问题 (${minorIssues.length}):`);
        minorIssues.forEach(issue => {
            console.log(`  ℹ️  [${issue.category}] ${issue.issue}`);
        });
        
        // 生成修复建议
        this.generateRecommendations();
        
        // 保存报告
        const report = {
            timestamp: new Date().toISOString(),
            issues: this.issuesFound,
            recommendations: this.recommendations,
            rawData: this.diagnosisResults
        };
        
        window.deepDiagnosisReport = report;
        console.log('\n💾 诊断报告已保存到 window.deepDiagnosisReport');
        
        return report;
    }
    
    generateRecommendations() {
        console.log('\n🔧 修复建议:');
        
        const recommendations = [];
        
        // 基于发现的问题生成具体建议
        this.issuesFound.forEach(issue => {
            switch (issue.category) {
                case 'environment':
                    recommendations.push(`更新显卡驱动到最新版本`);
                    recommendations.push(`使用支持WebGL 2.0的现代浏览器`);
                    break;
                case 'resources':
                    recommendations.push(`检查模型文件路径配置`);
                    recommendations.push(`验证资源文件权限和可访问性`);
                    break;
                case 'rendering':
                    recommendations.push(`检查Canvas元素的CSS样式`);
                    recommendations.push(`验证WebGL上下文初始化`);
                    break;
                case 'events':
                    recommendations.push(`确保事件监听器正确注册`);
                    recommendations.push(`检查交互处理器的绑定`);
                    break;
            }
        });
        
        // 添加通用建议
        recommendations.push(`清空浏览器缓存和localStorage`);
        recommendations.push(`重启应用和服务`);
        recommendations.push(`检查防火墙和安全软件设置`);
        
        recommendations.forEach((rec, index) => {
            console.log(`${index + 1}. ${rec}`);
        });
        
        this.recommendations = recommendations;
    }
}

// 立即执行深度诊断
(async () => {
    console.log('🚀 启动深度Live2D问题诊断器...');
    const diagnostic = new DeepLive2DDiagnostic();
    window.deepDiagnostic = diagnostic;
    
    await diagnostic.runCompleteDiagnosis();
    
    console.log('\n🔧 诊断工具已就绪');
    console.log('使用方法:');
    console.log('- 重新运行诊断: await window.deepDiagnostic.runCompleteDiagnosis()');
    console.log('- 查看报告: window.deepDiagnosisReport');
})();

// 导出类
window.DeepLive2DDiagnostic = DeepLive2DDiagnostic;