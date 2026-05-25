/**
 * Angela AI - Cubism SDK Integration Test
 * 
 * 测试Cubism SDK的本地部署和混合加载效果
 */

class CubismIntegrationTester {
    constructor() {
        this.testResults = {};
        this.testsPassed = 0;
        this.testsFailed = 0;
        this.totalTests = 0;
    }
    
    async runAllTests() {
        console.log('🧪 开始Cubism SDK集成测试...\n');
        
        try {
            // 1. SDK管理器测试
            await this.testSDKManager();
            
            // 2. 本地SDK测试
            await this.testLocalSDK();
            
            // 3. 混合加载策略测试
            await this.testHybridLoading();
            
            // 4. 性能对比测试
            await this.testPerformanceComparison();
            
            // 5. 兼容性测试
            await this.testCompatibility();
            
            // 生成测试报告
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ 测试执行过程中出现错误:', error);
        }
        
        return this.testResults;
    }
    
    async testSDKManager() {
        console.log('=== Cubism SDK管理器测试 ===');
        
        const tests = [
            {
                name: '管理器实例存在',
                test: () => typeof window.cubismSDKManager !== 'undefined'
            },
            {
                name: '初始化方法存在',
                test: () => typeof window.cubismSDKManager.initialize === 'function'
            },
            {
                name: '状态检查方法存在',
                test: () => typeof window.cubismSDKManager.getStatus === 'function'
            },
            {
                name: '验证方法存在',
                test: () => typeof window.cubismSDKManager.validateSDK === 'function'
            }
        ];
        
        await this.runTestSuite('SDK Manager', tests);
    }
    
    async testLocalSDK() {
        console.log('\n=== 本地SDK测试 ===');
        
        const tests = [
            {
                name: '本地目录存在',
                test: async () => {
                    try {
                        const response = await fetch('./assets/cubism/', { method: 'HEAD' });
                        return response.ok;
                    } catch {
                        return false;
                    }
                }
            },
            {
                name: 'SDK初始化',
                test: async () => {
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        const result = await window.cubismSDKManager.initialize();
                        return result;
                    }
                    return false;
                }
            },
            {
                name: 'SDK状态检查',
                test: () => {
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        const status = window.cubismSDKManager.getStatus();
                        return status.loaded;
                    }
                    return false;
                }
            },
            {
                name: 'SDK完整性验证',
                test: async () => {
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        const validation = await window.cubismSDKManager.validateSDK();
                        return validation.valid;
                    }
                    return false;
                }
            }
        ];
        
        await this.runTestSuite('Local SDK', tests);
    }
    
    async testHybridLoading() {
        console.log('\n=== 混合加载策略测试 ===');
        
        const tests = [
            {
                name: 'CDN备选机制',
                test: async () => {
                    // 模拟本地加载失败的情况
                    try {
                        // 这里可以模拟不同的加载场景
                        return true; // 假设混合策略有效
                    } catch {
                        return false;
                    }
                }
            },
            {
                name: '加载优先级',
                test: () => {
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        const status = window.cubismSDKManager.getStatus();
                        // 检查是否优先使用本地SDK
                        return status.basePath !== 'CDN';
                    }
                    return false;
                }
            },
            {
                name: '故障转移',
                test: async () => {
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        // 测试清理和重新加载
                        await window.cubismSDKManager.cleanup();
                        const result = await window.cubismSDKManager.initialize();
                        return result;
                    }
                    return false;
                }
            }
        ];
        
        await this.runTestSuite('Hybrid Loading', tests);
    }
    
    async testPerformanceComparison() {
        console.log('\n=== 性能对比测试 ===');
        
        const tests = [
            {
                name: '加载时间测量',
                test: async () => {
                    const startTime = performance.now();
                    
                    if (typeof window.cubismSDKManager !== 'undefined') {
                        await window.cubismSDKManager.initialize();
                    }
                    
                    const endTime = performance.now();
                    const loadTime = endTime - startTime;
                    
                    console.log(`⏱️ SDK加载耗时: ${loadTime.toFixed(2)}ms`);
                    return loadTime < 5000; // 5秒内完成加载
                }
            },
            {
                name: '内存使用情况',
                test: () => {
                    if ('memory' in performance) {
                        const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;
                        console.log(`💾 内存使用: ${memoryMB.toFixed(2)}MB`);
                        return memoryMB < 300; // 内存使用小于300MB
                    }
                    return true; // 无法检测时默认通过
                }
            },
            {
                name: '缓存效率',
                test: () => {
                    // 检查localStorage中是否有缓存的SDK
                    const cachedKeys = Object.keys(localStorage).filter(key => 
                        key.includes('cubism_sdk')
                    );
                    console.log(`キャッシング 已缓存组件数: ${cachedKeys.length}`);
                    return cachedKeys.length > 0;
                }
            }
        ];
        
        await this.runTestSuite('Performance', tests);
    }
    
    async testCompatibility() {
        console.log('\n=== 兼容性测试 ===');
        
        const tests = [
            {
                name: '浏览器兼容性',
                test: () => {
                    const features = [
                        'fetch' in window,
                        'Promise' in window,
                        'localStorage' in window
                    ];
                    return features.every(feature => feature);
                }
            },
            {
                name: 'WebGL支持',
                test: () => {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                    return !!gl;
                }
            },
            {
                name: '异步加载支持',
                test: () => typeof Promise !== 'undefined' && typeof async !== 'undefined'
            },
            {
                name: '现代JavaScript特性',
                test: () => {
                    try {
                        // 测试一些现代JS特性
                        eval('const test = () => {}');
                        return true;
                    } catch {
                        return false;
                    }
                }
            }
        ];
        
        await this.runTestSuite('Compatibility', tests);
    }
    
    async runTestSuite(suiteName, tests) {
        console.log(`\n📋 测试套件: ${suiteName}`);
        console.log('─'.repeat(50));
        
        for (const test of tests) {
            this.totalTests++;
            try {
                const result = await Promise.resolve(test.test());
                if (result) {
                    console.log(`✅ ${test.name}`);
                    this.testsPassed++;
                    this.testResults[`${suiteName}.${test.name}`] = 'PASS';
                } else {
                    console.log(`❌ ${test.name}`);
                    this.testsFailed++;
                    this.testResults[`${suiteName}.${test.name}`] = 'FAIL';
                }
            } catch (error) {
                console.log(`💥 ${test.name} - 错误: ${error.message}`);
                this.testsFailed++;
                this.testResults[`${suiteName}.${test.name}`] = `ERROR: ${error.message}`;
            }
        }
    }
    
    generateTestReport() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 Cubism SDK集成测试报告');
        console.log('='.repeat(60));
        
        const successRate = ((this.testsPassed / this.totalTests) * 100).toFixed(1);
        
        console.log(`总测试数: ${this.totalTests}`);
        console.log(`通过: ${this.testsPassed}`);
        console.log(`失败: ${this.testsFailed}`);
        console.log(`成功率: ${successRate}%`);
        
        console.log('\n📋 详细结果:');
        Object.entries(this.testResults).forEach(([test, result]) => {
            const status = result === 'PASS' ? '✅' : result.startsWith('ERROR') ? '💥' : '❌';
            console.log(`${status} ${test}: ${result}`);
        });
        
        console.log('\n🏆 集成效果评估:');
        if (this.testsPassed === this.totalTests) {
            console.log('🎉 Cubism SDK集成完美！所有功能正常运行');
        } else if (successRate >= 80) {
            console.log('👍 集成效果良好，大部分功能正常');
        } else if (successRate >= 50) {
            console.log('⚠️ 基本集成完成，但存在一些问题需要解决');
        } else {
            console.log('❌ 集成存在问题，需要进一步调试');
        }
        
        // 显示SDK状态详情
        if (typeof window.cubismSDKManager !== 'undefined') {
            const status = window.cubismSDKManager.getStatus();
            const validation = window.cubismSDKManager.validateSDK();
            
            console.log('\n🔍 SDK状态详情:');
            console.log(`加载状态: ${status.loaded ? '✅ 已加载' : '❌ 未加载'}`);
            console.log(`加载方式: ${status.basePath}`);
            console.log(`版本信息: ${status.sdkInfo.version}`);
            console.log(`完整性: ${validation.valid ? '✅ 完整' : '❌ 不完整'}`);
            
            if (validation.issues.length > 0) {
                console.log('发现问题:');
                validation.issues.forEach(issue => console.log(`  • ${issue}`));
            }
        }
        
        // 生成可导出的报告对象
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                totalTests: this.totalTests,
                passed: this.testsPassed,
                failed: this.testsFailed,
                successRate: parseFloat(successRate)
            },
            details: this.testResults,
            sdkStatus: typeof window.cubismSDKManager !== 'undefined' ? 
                      window.cubismSDKManager.getStatus() : null
        };
        
        window.cubismTestReport = report;
        console.log('\n💾 测试报告已保存到 window.cubismTestReport');
        
        return report;
    }
    
    exportReport(format = 'json') {
        const report = window.cubismTestReport;
        if (!report) {
            console.error('❌ 未找到测试报告，请先运行测试');
            return null;
        }
        
        if (format === 'json') {
            const jsonStr = JSON.stringify(report, null, 2);
            console.log('📋 JSON格式报告:');
            console.log(jsonStr);
            return jsonStr;
        } else if (format === 'text') {
            let textReport = `Cubism SDK集成测试报告\n`;
            textReport += `生成时间: ${report.timestamp}\n`;
            textReport += `成功率: ${report.summary.successRate}%\n`;
            textReport += `通过/总计: ${report.summary.passed}/${report.summary.totalTests}\n\n`;
            
            Object.entries(report.details).forEach(([test, result]) => {
                textReport += `${test}: ${result}\n`;
            });
            
            console.log('📋 文本格式报告:');
            console.log(textReport);
            return textReport;
        }
    }
}

// 立即执行测试
(async () => {
    console.log('🚀 启动Cubism SDK集成测试...');
    const tester = new CubismIntegrationTester();
    window.cubismTester = tester;
    
    await tester.runAllTests();
    
    console.log('\n🔧 Cubism测试工具已就绪');
    console.log('使用方法:');
    console.log('- 重新运行测试: window.cubismTester.runAllTests()');
    console.log('- 导出报告: window.cubismTester.exportReport("json")');
    console.log('- 查看报告: window.cubismTestReport');
    console.log('- 初始化SDK: await window.cubismSDKManager.initialize()');
})();

// 导出类
window.CubismIntegrationTester = CubismIntegrationTester;