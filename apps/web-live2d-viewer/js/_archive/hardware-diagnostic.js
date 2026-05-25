/**
 * Angela AI - Advanced Hardware Diagnostic Tool
 * 
 * 深入诊断硬件兼容性和支持问题
 */

class HardwareDiagnosticTool {
    constructor() {
        this.results = {};
        this.diagnosticSteps = [
            'webglSupport',
            'gpuCapabilities',
            'driverStatus',
            'memoryAnalysis',
            'extensionCheck',
            'performanceTest'
        ];
    }
    
    async runCompleteDiagnosis() {
        console.log('🔬 开始全面硬件诊断...');
        
        for (const step of this.diagnosticSteps) {
            try {
                await this[step]();
            } catch (error) {
                console.error(`诊断步骤 ${step} 失败:`, error);
                this.results[step] = { status: 'error', error: error.message };
            }
        }
        
        this.generateDiagnosisReport();
        return this.results;
    }
    
    async webglSupport() {
        console.log('🔍 检查 WebGL 支持...');
        
        const canvas = document.createElement('canvas');
        let webgl2 = false;
        let webgl1 = false;
        let context = null;
        
        try {
            context = canvas.getContext('webgl2');
            webgl2 = !!context;
            console.log(`WebGL 2.0: ${webgl2 ? '✅ 支持' : '❌ 不支持'}`);
        } catch (e) {
            console.log('WebGL 2.0 检查失败:', e.message);
        }
        
        if (!webgl2) {
            try {
                context = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                webgl1 = !!context;
                console.log(`WebGL 1.0: ${webgl1 ? '✅ 支持' : '❌ 不支持'}`);
            } catch (e) {
                console.log('WebGL 1.0 检查失败:', e.message);
            }
        }
        
        this.results.webglSupport = {
            webgl2: webgl2,
            webgl1: webgl1,
            context: context,
            status: webgl2 || webgl1 ? 'supported' : 'not_supported'
        };
    }
    
    async gpuCapabilities() {
        console.log('🎮 分析 GPU 能力...');
        
        if (!this.results.webglSupport?.context) {
            this.results.gpuCapabilities = {
                status: 'error',
                error: 'No WebGL context available'
            };
            return;
        }
        
        const gl = this.results.webglSupport.context;
        
        // 获取GPU信息
        const vendor = gl.getParameter(gl.VENDOR);
        const renderer = gl.getParameter(gl.RENDERER);
        const version = gl.getParameter(gl.VERSION);
        
        // 获取扩展支持
        const extensions = gl.getSupportedExtensions();
        const requiredExtensions = [
            'OES_texture_float',
            'OES_standard_derivatives', 
            'WEBGL_depth_texture',
            'EXT_texture_filter_anisotropic'
        ];
        
        const missingExtensions = requiredExtensions.filter(ext => !extensions.includes(ext));
        const hasRequiredExtensions = missingExtensions.length === 0;
        
        // 获取硬件限制
        const maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        const maxRenderbufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
        const maxVertexAttribs = gl.getParameter(gl.MAX_VERTEX_ATTRIBS);
        
        console.log(`GPU Vendor: ${vendor}`);
        console.log(`GPU Renderer: ${renderer}`);
        console.log(`WebGL Version: ${version}`);
        console.log(`Max Texture Size: ${maxTextureSize}`);
        console.log(`Required Extensions Missing: ${missingExtensions.length}`);
        
        this.results.gpuCapabilities = {
            vendor: vendor,
            renderer: renderer,
            version: version,
            extensions: extensions,
            missingExtensions: missingExtensions,
            hasRequiredExtensions: hasRequiredExtensions,
            maxTextureSize: maxTextureSize,
            maxRenderbufferSize: maxRenderbufferSize,
            maxVertexAttribs: maxVertexAttribs,
            status: hasRequiredExtensions && maxTextureSize >= 2048 ? 'adequate' : 'insufficient'
        };
    }
    
    async driverStatus() {
        console.log('🔧 检查驱动程序状态...');
        
        // 检查浏览器信息
        const userAgent = navigator.userAgent;
        const platform = navigator.platform;
        
        // 检查硬件并发能力
        const hardwareConcurrency = navigator.hardwareConcurrency || 'unknown';
        const deviceMemory = navigator.deviceMemory || 'unknown';
        
        console.log(`User Agent: ${userAgent}`);
        console.log(`Platform: ${platform}`);
        console.log(`CPU Cores: ${hardwareConcurrency}`);
        console.log(`Device Memory: ${deviceMemory} GB`);
        
        this.results.driverStatus = {
            userAgent: userAgent,
            platform: platform,
            hardwareConcurrency: hardwareConcurrency,
            deviceMemory: deviceMemory,
            status: 'checked'
        };
    }
    
    async memoryAnalysis() {
        console.log('💾 分析内存使用情况...');
        
        let memoryInfo = {};
        try {
            if (performance.memory) {
                memoryInfo = {
                    used: Math.round(performance.memory.usedJSHeapSize / 1048576),
                    total: Math.round(performance.memory.totalJSHeapSize / 1048576),
                    limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
                };
                console.log(`内存使用: ${memoryInfo.used}MB / ${memoryInfo.total}MB (限制: ${memoryInfo.limit}MB)`);
            }
        } catch (e) {
            console.log('无法获取内存信息:', e.message);
        }
        
        this.results.memoryAnalysis = {
            memoryInfo: memoryInfo,
            status: memoryInfo.used ? 'monitored' : 'unavailable'
        };
    }
    
    async extensionCheck() {
        console.log('🔌 检查必需的 WebGL 扩展...');
        
        if (!this.results.webglSupport?.context) {
            this.results.extensionCheck = {
                status: 'skipped',
                reason: 'No WebGL context'
            };
            return;
        }
        
        const gl = this.results.webglSupport.context;
        const extensions = gl.getSupportedExtensions();
        
        const criticalExtensions = {
            'OES_texture_float': '浮点纹理支持',
            'OES_standard_derivatives': '标准导数支持',
            'WEBGL_depth_texture': '深度纹理支持',
            'OES_element_index_uint': '大索引支持',
            'EXT_texture_filter_anisotropic': '各向异性过滤'
        };
        
        const missing = [];
        const available = [];
        
        for (const [ext, desc] of Object.entries(criticalExtensions)) {
            if (extensions.includes(ext)) {
                available.push({ extension: ext, description: desc });
                console.log(`✅ ${ext} - ${desc}`);
            } else {
                missing.push({ extension: ext, description: desc });
                console.log(`❌ ${ext} - ${desc} (缺失)`);
            }
        }
        
        const isCriticalMissing = missing.some(item => 
            item.extension === 'OES_texture_float' || 
            item.extension === 'OES_standard_derivatives'
        );
        
        this.results.extensionCheck = {
            available: available,
            missing: missing,
            isCriticalMissing: isCriticalMissing,
            status: isCriticalMissing ? 'critical_missing' : 'acceptable'
        };
    }
    
    async performanceTest() {
        console.log('⚡ 执行性能基准测试...');
        
        if (!this.results.webglSupport?.context) {
            this.results.performanceTest = {
                status: 'skipped',
                reason: 'No WebGL context'
            };
            return;
        }
        
        const gl = this.results.webglSupport.context;
        
        // 简单的渲染性能测试
        const startTime = performance.now();
        
        try {
            // 创建简单着色器程序
            const vertexShader = gl.createShader(gl.VERTEX_SHADER);
            gl.shaderSource(vertexShader, `
                attribute vec2 position;
                void main() {
                    gl_Position = vec4(position, 0.0, 1.0);
                }
            `);
            gl.compileShader(vertexShader);
            
            const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
            gl.shaderSource(fragmentShader, `
                void main() {
                    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
                }
            `);
            gl.compileShader(fragmentShader);
            
            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);
            gl.useProgram(program);
            
            // 创建顶点数据
            const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
            const buffer = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
            gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
            
            const positionLoc = gl.getAttribLocation(program, 'position');
            gl.enableVertexAttribArray(positionLoc);
            gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);
            
            // 执行几次渲染
            for (let i = 0; i < 10; i++) {
                gl.clear(gl.COLOR_BUFFER_BIT);
                gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
                gl.finish();
            }
            
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            console.log(`性能测试完成: ${duration.toFixed(2)}ms`);
            
            this.results.performanceTest = {
                duration: duration,
                frames: 10,
                fps: Math.round(10000 / duration),
                status: 'completed'
            };
            
        } catch (error) {
            console.error('性能测试失败:', error);
            this.results.performanceTest = {
                status: 'failed',
                error: error.message
            };
        }
    }
    
    generateDiagnosisReport() {
        console.log('\n📋 硬件诊断报告');
        console.log('================');
        
        // WebGL 支持状态
        const webgl = this.results.webglSupport;
        console.log(`WebGL 支持: ${webgl?.webgl2 ? 'WebGL 2.0' : webgl?.webgl1 ? 'WebGL 1.0' : '❌ 不支持'}`);
        
        // GPU 能力
        const gpu = this.results.gpuCapabilities;
        if (gpu) {
            console.log(`GPU: ${gpu.vendor} ${gpu.renderer}`);
            console.log(`纹理支持: ${gpu.maxTextureSize}x${gpu.maxTextureSize}`);
            console.log(`扩展支持: ${gpu.hasRequiredExtensions ? '✅ 充足' : '❌ 不足'}`);
        }
        
        // 扩展检查
        const ext = this.results.extensionCheck;
        if (ext) {
            console.log(`关键扩展缺失: ${ext.missing?.length || 0} 个`);
            if (ext.isCriticalMissing) {
                console.log('⚠️ 缺少关键扩展，可能影响 Live2D 渲染');
            }
        }
        
        // 性能测试
        const perf = this.results.performanceTest;
        if (perf?.status === 'completed') {
            console.log(`渲染性能: ${perf.fps} FPS`);
        }
        
        // 总体评估
        const issues = [];
        if (!webgl?.webgl2 && !webgl?.webgl1) {
            issues.push('WebGL 不支持');
        }
        if (gpu && !gpu.hasRequiredExtensions) {
            issues.push('缺少必要 WebGL 扩展');
        }
        if (ext?.isCriticalMissing) {
            issues.push('关键图形扩展缺失');
        }
        
        if (issues.length === 0) {
            console.log('\n✅ 硬件完全支持 Angela AI');
        } else {
            console.log('\n❌ 发现以下硬件兼容性问题:');
            issues.forEach(issue => console.log(`  • ${issue}`));
        }
        
        // 保存详细结果
        try {
            localStorage.setItem('hardware_diagnosis_results', JSON.stringify(this.results));
            console.log('\n💾 诊断结果已保存到 localStorage');
        } catch (e) {
            console.log('\n⚠️ 无法保存诊断结果');
        }
        
        return {
            issues: issues,
            results: this.results
        };
    }
    
    // 快速检查方法
    static async quickCheck() {
        const tool = new HardwareDiagnosticTool();
        return await tool.runCompleteDiagnosis();
    }
}

// 立即执行诊断
(async () => {
    console.log('🚀 启动硬件诊断工具...');
    const tool = new HardwareDiagnosticTool();
    await tool.runCompleteDiagnosis();
    
    // 将工具暴露给全局作用域
    window.hardwareDiagnostic = tool;
    console.log('🔧 硬件诊断工具已就绪');
    console.log('使用方法: window.hardwareDiagnostic.runCompleteDiagnosis()');
})();

// 导出类
window.HardwareDiagnosticTool = HardwareDiagnosticTool;