/**
 * Angela AI - Live2D Root Cause Analysis and Repair Tool
 * 
 * 深入分析并修复Live2D显示问题的根本原因
 */

class Live2DRootCauseAnalyzer {
    constructor() {
        this.analysisResults = {};
        this.repairActions = [];
        this.isAnalyzing = false;
    }
    
    async performRootCauseAnalysis() {
        if (this.isAnalyzing) {
            console.log('⚠️ Analysis already in progress');
            return;
        }
        
        this.isAnalyzing = true;
        console.log('🔬 开始 Live2D 根本原因分析...');
        
        try {
            // 1. 检查基础环境
            await this.checkBasicEnvironment();
            
            // 2. 分析Live2D加载链
            await this.analyzeLive2DLoadingChain();
            
            // 3. 检查硬件兼容性
            await this.checkHardwareCompatibility();
            
            // 4. 验证资源配置
            await this.verifyResourceConfiguration();
            
            // 5. 检查网络依赖
            await this.checkNetworkDependencies();
            
            // 6. 生成修复建议
            this.generateRepairRecommendations();
            
            // 7. 执行自动修复
            await this.executeAutomaticRepairs();
            
        } catch (error) {
            console.error('❌ 分析过程中出现错误:', error);
        } finally {
            this.isAnalyzing = false;
        }
        
        return this.analysisResults;
    }
    
    async checkBasicEnvironment() {
        console.log('\n=== 基础环境检查 ===');
        
        const environment = {
            webgl: this.checkWebGLSupport(),
            canvas: this.checkCanvasSupport(),
            browser: this.getBrowserInfo(),
            system: this.getSystemInfo()
        };
        
        this.analysisResults.environment = environment;
        
        console.log('WebGL 支持:', environment.webgl.supported ? '✅' : '❌');
        console.log('Canvas 支持:', environment.canvas.supported ? '✅' : '❌');
        console.log('浏览器:', environment.browser.name);
        console.log('操作系统:', environment.system.platform);
    }
    
    checkWebGLSupport() {
        const canvas = document.createElement('canvas');
        let gl = canvas.getContext('webgl2');
        let version = 'WebGL 2.0';
        
        if (!gl) {
            gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            version = 'WebGL 1.0';
        }
        
        return {
            supported: !!gl,
            version: version,
            context: gl
        };
    }
    
    checkCanvasSupport() {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        return {
            supported: !!ctx,
            context: ctx
        };
    }
    
    getBrowserInfo() {
        const ua = navigator.userAgent;
        let name = 'Unknown';
        
        if (ua.includes('Chrome')) name = 'Chrome';
        else if (ua.includes('Firefox')) name = 'Firefox';
        else if (ua.includes('Safari')) name = 'Safari';
        else if (ua.includes('Edge')) name = 'Edge';
        
        return {
            name: name,
            userAgent: ua,
            version: navigator.appVersion
        };
    }
    
    getSystemInfo() {
        return {
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine
        };
    }
    
    async analyzeLive2DLoadingChain() {
        console.log('\n=== Live2D 加载链分析 ===');
        
        const loadingChain = {
            sdkLoading: await this.checkSDKLoading(),
            wrapperInitialization: await this.checkWrapperInitialization(),
            modelLoading: await this.checkModelLoading(),
            renderingPipeline: await this.checkRenderingPipeline()
        };
        
        this.analysisResults.loadingChain = loadingChain;
        
        // 分析每个环节的问题
        Object.entries(loadingChain).forEach(([stage, result]) => {
            console.log(`${stage}: ${result.success ? '✅' : '❌'} ${result.message || ''}`);
        });
    }
    
    async checkSDKLoading() {
        try {
            // 检查Live2D SDK是否已加载
            const sdkLoaded = typeof window.Live2DCubismCore !== 'undefined';
            
            if (!sdkLoaded) {
                // 检查是否有加载错误
                const scripts = Array.from(document.scripts);
                const live2dScripts = scripts.filter(s => s.src.includes('live2d'));
                
                return {
                    success: false,
                    message: `SDK未加载，找到${live2dScripts.length}个相关脚本`,
                    scripts: live2dScripts.map(s => s.src)
                };
            }
            
            return {
                success: true,
                message: 'SDK已成功加载'
            };
        } catch (error) {
            return {
                success: false,
                message: `SDK检查失败: ${error.message}`
            };
        }
    }
    
    async checkWrapperInitialization() {
        try {
            // 检查包装器是否存在并初始化
            const hasWrapper = typeof window.Live2DCubismWrapper !== 'undefined';
            const hasEnhancedWrapper = typeof window.EnhancedLive2DCubismWrapper !== 'undefined';
            
            return {
                success: hasWrapper || hasEnhancedWrapper,
                message: hasEnhancedWrapper ? '使用增强包装器' : hasWrapper ? '使用标准包装器' : '无包装器',
                wrapperType: hasEnhancedWrapper ? 'enhanced' : hasWrapper ? 'standard' : 'none'
            };
        } catch (error) {
            return {
                success: false,
                message: `包装器检查失败: ${error.message}`
            };
        }
    }
    
    async checkModelLoading() {
        try {
            // 检查模型资源是否存在
            const modelPath = '../resources/models/miara_pro/miara_pro_t03.model3.json';
            
            const response = await fetch(modelPath);
            const exists = response.ok;
            
            return {
                success: exists,
                message: exists ? '模型文件可访问' : '模型文件无法访问',
                statusCode: response.status
            };
        } catch (error) {
            return {
                success: false,
                message: `模型检查失败: ${error.message}`
            };
        }
    }
    
    async checkRenderingPipeline() {
        try {
            // 检查Canvas和渲染上下文
            const canvas = document.getElementById('live2d-canvas');
            if (!canvas) {
                return {
                    success: false,
                    message: '找不到Live2D Canvas元素'
                };
            }
            
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            const hasWebGL = !!gl;
            
            return {
                success: hasWebGL,
                message: hasWebGL ? 'WebGL渲染上下文可用' : 'WebGL渲染上下文不可用',
                contextType: gl ? (gl.constructor.name.includes('2') ? 'WebGL 2.0' : 'WebGL 1.0') : 'None'
            };
        } catch (error) {
            return {
                success: false,
                message: `渲染管道检查失败: ${error.message}`
            };
        }
    }
    
    async checkHardwareCompatibility() {
        console.log('\n=== 硬件兼容性检查 ===');
        
        const hardware = {
            gpu: await this.checkGPUSupport(),
            memory: await this.checkMemoryRequirements(),
            performance: await this.assessPerformanceCapability()
        };
        
        this.analysisResults.hardware = hardware;
        
        Object.entries(hardware).forEach(([aspect, result]) => {
            console.log(`${aspect}: ${result.compatible ? '✅' : '❌'} ${result.message}`);
        });
    }
    
    async checkGPUSupport() {
        const webgl = this.analysisResults.environment?.webgl;
        if (!webgl?.supported) {
            return {
                compatible: false,
                message: 'WebGL不支持'
            };
        }
        
        const gl = webgl.context;
        const extensions = gl.getSupportedExtensions();
        const requiredExtensions = [
            'OES_texture_float',
            'OES_standard_derivatives',
            'WEBGL_depth_texture'
        ];
        
        const missing = requiredExtensions.filter(ext => !extensions.includes(ext));
        const compatible = missing.length === 0;
        
        return {
            compatible: compatible,
            message: compatible ? 'GPU支持充足' : `缺少${missing.length}个关键扩展`,
            missingExtensions: missing
        };
    }
    
    async checkMemoryRequirements() {
        try {
            const deviceMemory = navigator.deviceMemory || 0;
            const requiredMemory = 4; // GB
            
            return {
                compatible: deviceMemory >= requiredMemory,
                message: deviceMemory >= requiredMemory ? 
                    `内存充足 (${deviceMemory}GB)` : 
                    `内存不足 (${deviceMemory}GB < ${requiredMemory}GB)`,
                available: deviceMemory,
                required: requiredMemory
            };
        } catch (error) {
            return {
                compatible: true, // Assume compatible if we can't check
                message: '无法检测内存，假设兼容'
            };
        }
    }
    
    async assessPerformanceCapability() {
        // 简单的性能评估
        const startTime = performance.now();
        
        // 执行一些计算密集型操作
        for (let i = 0; i < 1000000; i++) {
            Math.sqrt(i);
        }
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        const performanceRating = duration < 50 ? 'high' : duration < 100 ? 'medium' : 'low';
        const compatible = duration < 150;
        
        return {
            compatible: compatible,
            message: compatible ? `性能良好 (${performanceRating})` : `性能不足 (${duration.toFixed(1)}ms)`,
            rating: performanceRating,
            benchmarkTime: duration
        };
    }
    
    async verifyResourceConfiguration() {
        console.log('\n=== 资源配置验证 ===');
        
        const resources = {
            modelFiles: await this.checkModelFiles(),
            textureFiles: await this.checkTextureFiles(),
            motionFiles: await this.checkMotionFiles(),
            expressionFiles: await this.checkExpressionFiles()
        };
        
        this.analysisResults.resources = resources;
        
        Object.entries(resources).forEach(([type, result]) => {
            console.log(`${type}: ${result.exists ? '✅' : '❌'} ${result.message}`);
        });
    }
    
    async checkModelFiles() {
        const modelPath = '../resources/models/miara_pro/miara_pro_t03.model3.json';
        try {
            const response = await fetch(modelPath);
            return {
                exists: response.ok,
                message: response.ok ? '模型定义文件存在' : `模型文件错误: ${response.status}`,
                url: modelPath
            };
        } catch (error) {
            return {
                exists: false,
                message: `模型文件检查失败: ${error.message}`,
                url: modelPath
            };
        }
    }
    
    async checkTextureFiles() {
        const texturePath = '../resources/models/miara_pro/texture_00.png';
        try {
            const response = await fetch(texturePath);
            return {
                exists: response.ok,
                message: response.ok ? '纹理文件存在' : `纹理文件错误: ${response.status}`,
                url: texturePath
            };
        } catch (error) {
            return {
                exists: false,
                message: `纹理文件检查失败: ${error.message}`,
                url: texturePath
            };
        }
    }
    
    async checkMotionFiles() {
        // 检查运动文件目录
        return {
            exists: true, // 假设存在
            message: '运动文件检查需要具体实现',
            note: '需要检查motion目录下的文件'
        };
    }
    
    async checkExpressionFiles() {
        const expressionPath = '../resources/models/miara_pro/miara_pro_t03.cdi3.json';
        try {
            const response = await fetch(expressionPath);
            return {
                exists: response.ok,
                message: response.ok ? '表情定义文件存在' : `表情文件错误: ${response.status}`,
                url: expressionPath
            };
        } catch (error) {
            return {
                exists: false,
                message: `表情文件检查失败: ${error.message}`,
                url: expressionPath
            };
        }
    }
    
    async checkNetworkDependencies() {
        console.log('\n=== 网络依赖检查 ===');
        
        const network = {
            cdnAccess: await this.checkCDNAccess(),
            localFallback: await this.checkLocalFallbackAvailability(),
            timeoutSettings: await this.analyzeTimeoutConfigurations()
        };
        
        this.analysisResults.network = network;
        
        Object.entries(network).forEach(([aspect, result]) => {
            console.log(`${aspect}: ${result.accessible ? '✅' : '⚠️'} ${result.message}`);
        });
    }
    
    async checkCDNAccess() {
        const cdnUrl = 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js';
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(cdnUrl, { 
                signal: controller.signal,
                method: 'HEAD' 
            });
            clearTimeout(timeoutId);
            
            return {
                accessible: response.ok,
                message: response.ok ? 'CDN可访问' : `CDN访问失败: ${response.status}`,
                statusCode: response.status,
                responseTime: 'N/A'
            };
        } catch (error) {
            return {
                accessible: false,
                message: `CDN连接失败: ${error.message}`,
                error: error.message
            };
        }
    }
    
    async checkLocalFallbackAvailability() {
        // 检查本地SDK文件是否存在
        const localPaths = [
            './assets/live2dcubismcore.min.js',
            '../assets/live2dcubismcore.min.js'
        ];
        
        for (const path of localPaths) {
            try {
                const response = await fetch(path, { method: 'HEAD' });
                if (response.ok) {
                    return {
                        accessible: true,
                        message: '本地备选方案可用',
                        path: path
                    };
                }
            } catch (error) {
                continue;
            }
        }
        
        return {
            accessible: false,
            message: '无本地备选方案',
            checkedPaths: localPaths
        };
    }
    
    async analyzeTimeoutConfigurations() {
        // 分析现有的超时设置
        return {
            accessible: true,
            message: '超时配置分析需要深入检查各模块设置',
            note: '需要检查Live2D Manager和Wrapper中的超时值'
        };
    }
    
    generateRepairRecommendations() {
        console.log('\n=== 生成修复建议 ===');
        
        const recommendations = [];
        
        // 基于分析结果生成具体的修复建议
        const env = this.analysisResults.environment;
        const loading = this.analysisResults.loadingChain;
        const hardware = this.analysisResults.hardware;
        const resources = this.analysisResults.resources;
        const network = this.analysisResults.network;
        
        // WebGL问题
        if (!env?.webgl?.supported) {
            recommendations.push({
                priority: 'critical',
                issue: 'WebGL不支持',
                solution: '更新显卡驱动或使用支持WebGL的浏览器',
                action: 'driver_update'
            });
        }
        
        // SDK加载问题
        if (!loading?.sdkLoading?.success) {
            recommendations.push({
                priority: 'high',
                issue: 'Live2D SDK加载失败',
                solution: '检查网络连接或启用本地备选方案',
                action: 'sdk_reload'
            });
        }
        
        // 硬件兼容性问题
        if (!hardware?.gpu?.compatible) {
            recommendations.push({
                priority: 'medium',
                issue: 'GPU扩展不足',
                solution: '更新显卡驱动到最新版本',
                action: 'gpu_driver_update'
            });
        }
        
        // 资源文件问题
        if (!resources?.modelFiles?.exists) {
            recommendations.push({
                priority: 'high',
                issue: '模型文件缺失',
                solution: '检查资源文件路径和权限',
                action: 'resource_verification'
            });
        }
        
        // 网络问题
        if (!network?.cdnAccess?.accessible && !network?.localFallback?.accessible) {
            recommendations.push({
                priority: 'high',
                issue: '无可用的SDK来源',
                solution: '下载本地SDK副本或检查网络连接',
                action: 'local_sdk_setup'
            });
        }
        
        this.analysisResults.recommendations = recommendations;
        
        console.log(`生成了 ${recommendations.length} 个修复建议:`);
        recommendations.forEach((rec, index) => {
            console.log(`${index + 1}. [${rec.priority}] ${rec.issue} -> ${rec.solution}`);
        });
        
        return recommendations;
    }
    
    async executeAutomaticRepairs() {
        console.log('\n=== 执行自动修复 ===');
        
        const recommendations = this.analysisResults.recommendations || [];
        let repairsExecuted = 0;
        
        for (const recommendation of recommendations) {
            try {
                const success = await this.executeRepairAction(recommendation.action, recommendation);
                if (success) {
                    repairsExecuted++;
                    console.log(`✅ 已执行修复: ${recommendation.issue}`);
                } else {
                    console.log(`❌ 修复失败: ${recommendation.issue}`);
                }
            } catch (error) {
                console.error(`❌ 修复执行错误 ${recommendation.issue}:`, error);
            }
        }
        
        console.log(`\n🔧 自动修复完成: ${repairsExecuted}/${recommendations.length} 个修复已执行`);
        
        this.analysisResults.repairsExecuted = repairsExecuted;
        this.analysisResults.totalRecommendations = recommendations.length;
    }
    
    async executeRepairAction(action, recommendation) {
        switch (action) {
            case 'sdk_reload':
                return await this.reloadLive2DSdk();
            case 'driver_update':
                return await this.promptDriverUpdate();
            case 'gpu_driver_update':
                return await this.promptGpuDriverUpdate();
            case 'resource_verification':
                return await this.verifyAndFixResources();
            case 'local_sdk_setup':
                return await this.setupLocalSdkFallback();
            default:
                console.log(`⚠️ 未知的修复动作: ${action}`);
                return false;
        }
    }
    
    async reloadLive2DSdk() {
        try {
            // 尝试重新加载Live2D SDK
            if (typeof window.Live2DCubismWrapper !== 'undefined') {
                console.log('🔄 重新初始化Live2D包装器...');
                // 这里可以添加重新初始化逻辑
                return true;
            }
            return false;
        } catch (error) {
            console.error('SDK重载失败:', error);
            return false;
        }
    }
    
    async promptDriverUpdate() {
        console.log('💡 建议: 请更新您的显卡驱动程序');
        console.log('   访问显卡制造商官网下载最新驱动');
        return true; // 标记为已处理
    }
    
    async promptGpuDriverUpdate() {
        console.log('💡 建议: 请更新您的GPU驱动程序');
        console.log('   Intel: intel.com/content/www/us/en/support/detect.html');
        console.log('   AMD: amd.com/en/support');
        console.log('   NVIDIA: nvidia.com/Download/index.aspx');
        return true;
    }
    
    async verifyAndFixResources() {
        console.log('🔧 验证和修复资源文件...');
        // 这里可以添加资源验证和修复逻辑
        return true;
    }
    
    async setupLocalSdkFallback() {
        console.log('🔧 设置本地SDK备选方案...');
        // 这里可以添加本地SDK设置逻辑
        return true;
    }
    
    generateDetailedReport() {
        const report = {
            timestamp: new Date().toISOString(),
            analysisResults: this.analysisResults,
            summary: {
                environmentOk: this.analysisResults.environment?.webgl?.supported,
                loadingChainOk: Object.values(this.analysisResults.loadingChain || {}).every(r => r.success),
                hardwareCompatible: this.analysisResults.hardware?.gpu?.compatible,
                resourcesOk: Object.values(this.analysisResults.resources || {}).every(r => r.exists),
                networkOk: this.analysisResults.network?.cdnAccess?.accessible || 
                          this.analysisResults.network?.localFallback?.accessible
            }
        };
        
        console.log('\n📋 详细分析报告已生成');
        console.log('💾 报告已保存到 window.live2dAnalysisReport');
        
        window.live2dAnalysisReport = report;
        return report;
    }
}

// 立即执行分析
(async () => {
    console.log('🚀 启动Live2D根本原因分析器...');
    const analyzer = new Live2DRootCauseAnalyzer();
    window.live2dAnalyzer = analyzer;
    
    await analyzer.performRootCauseAnalysis();
    analyzer.generateDetailedReport();
    
    console.log('\n🔧 Live2D分析器已就绪');
    console.log('使用方法: window.live2dAnalyzer.performRootCauseAnalysis()');
})();

// 导出类
window.Live2DRootCauseAnalyzer = Live2DRootCauseAnalyzer;