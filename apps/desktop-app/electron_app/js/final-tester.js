/**
 * Angela AI - Final Integration Test Suite
 * 
 * Comprehensive test suite - verify all fixes and enhancements
 */

class FinalIntegrationTester {
    constructor() {
        this.testResults = {};
        this.testsPassed = 0;
        this.testsFailed = 0;
        this.totalTests = 0;
    }
    
    async runAllTests() {
        console.log('🧪 开始最终集成测试...\n');
        
        try {
            // 1. 基础功能测试
            await this.testBasicFunctionality();
            
            // 2. Live2D功能测试
            await this.testLive2DFeatures();
            
            // 3. 硬件兼容性测试
            await this.testHardwareCompatibility();
            
            // 4. API连接测试
            await this.testApiConnectivity();
            
            // 5. 性能测试
            await this.testPerformance();
            
            // 6. 安全功能测试
            await this.testSecurityFeatures();
            
            // 生成测试报告
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ 测试执行过程中出现错误:', error);
        }
        
        return this.testResults;
    }
    
    async testBasicFunctionality() {
        console.log('=== 基础功能测试 ===');
        
        const tests = [
            {
                name: '应用初始化',
                test: () => typeof window.app !== 'undefined'
            },
            {
                name: '硬件检测模块',
                test: () => typeof window.HardwareDetector !== 'undefined'
            },
            {
                name: 'Live2D管理器',
                test: () => typeof window.Live2DManager !== 'undefined'
            },
            {
                name: 'Canvas元素存在',
                test: () => document.getElementById('live2d-canvas') !== null
            }
        ];
        
        await this.runTestSuite('Basic Functionality', tests);
    }
    
    async testLive2DFeatures() {
        console.log('\n=== Live2D功能测试 ===');
        
        const tests = [
            {
                name: 'Live2D SDK加载',
                test: () => typeof window.Live2DCubismCore !== 'undefined'
            },
            {
                name: '增强包装器存在',
                test: () => typeof window.EnhancedLive2DCubismWrapper !== 'undefined'
            },
            {
                name: '根因分析器存在',
                test: () => typeof window.Live2DRootCauseAnalyzer !== 'undefined'
            },
            {
                name: '模型文件可访问',
                test: async () => {
                    try {
                        const response = await fetch('../resources/models/miara_pro/miara_pro_t03.model3.json');
                        return response.ok;
                    } catch {
                        return false;
                    }
                }
            }
        ];
        
        await this.runTestSuite('Live2D Features', tests);
    }
    
    async testHardwareCompatibility() {
        console.log('\n=== 硬件兼容性测试 ===');
        
        const tests = [
            {
                name: 'WebGL支持',
                test: () => {
                    const canvas = document.createElement('canvas');
                    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'));
                }
            },
            {
                name: '增强硬件检测',
                test: () => typeof window.EnhancedHardwareDetector !== 'undefined'
            },
            {
                name: '笔记本优化器存在',
                test: () => typeof window.LaptopOptimizer !== 'undefined'
            },
            {
                name: '硬件诊断工具存在',
                test: () => typeof window.diagnoseHardwareIssues === 'function'
            }
        ];
        
        await this.runTestSuite('Hardware Compatibility', tests);
    }
    
    async testApiConnectivity() {
        console.log('\n=== API连接测试 ===');
        
        const tests = [
            {
                name: '后端健康检查',
                test: async () => {
                    try {
                        const response = await fetch('http://localhost:8000/api/v1/health');
                        return response.ok;
                    } catch {
                        return false;
                    }
                }
            },
            {
                name: '系统状态访问',
                test: async () => {
                    try {
                        const response = await fetch('http://localhost:8000/api/v1/admin/status');
                        return response.ok;
                    } catch {
                        return false;
                    }
                }
            },
            {
                name: 'WebSocket连接',
                test: () => typeof WebSocket !== 'undefined'
            },
            {
                name: 'CORS配置',
                test: async () => {
                    try {
                        const response = await fetch('http://localhost:8000/api/v1/health', {
                            method: 'OPTIONS'
                        });
                        return response.headers.get('access-control-allow-origin') !== null;
                    } catch {
                        return false;
                    }
                }
            }
        ];
        
        await this.runTestSuite('API Connectivity', tests);
    }
    
    async testPerformance() {
        console.log('\n=== 性能测试 ===');
        
        const tests = [
            {
                name: '页面加载时间',
                test: () => {
                    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                    return loadTime < 5000; // 5秒内加载完成
                }
            },
            {
                name: '内存使用情况',
                test: () => {
                    if ('memory' in performance) {
                        const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;
                        return memoryMB < 200; // 使用内存小于200MB
                    }
                    return true; // 无法检测时默认通过
                }
            },
            {
                name: 'FPS监控存在',
                test: () => typeof window.performanceMonitor !== 'undefined'
            },
            {
                name: '垃圾回收监控',
                test: () => typeof window.gcMonitor !== 'undefined'
            }
        ];
        
        await this.runTestSuite('Performance', tests);
    }
    
    async testSecurityFeatures() {
        console.log('\n=== 安全功能测试 ===');
        
        const tests = [
            {
                name: '安全头检查',
                test: () => {
                    const metaTags = document.querySelectorAll('meta');
                    return Array.from(metaTags).some(tag => 
                        tag.getAttribute('http-equiv') === 'Content-Security-Policy'
                    );
                }
            },
            {
                name: '密钥存储',
                test: () => localStorage.getItem('encryption_key') !== null
            },
            {
                name: '安全通信',
                test: () => location.protocol === 'https:' || location.hostname === 'localhost'
            },
            {
                name: '输入验证',
                test: () => typeof window.inputValidator !== 'undefined'
            }
        ];
        
        await this.runTestSuite('Security Features', tests);
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
        console.log('📊 最终测试报告');
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
        
        console.log('\n🏆 测试总结:');
        if (this.testsPassed === this.totalTests) {
            console.log('🎉 所有测试通过！系统完全正常运行');
        } else if (successRate >= 80) {
            console.log('👍 大部分功能正常，少数问题需要关注');
        } else if (successRate >= 50) {
            console.log('⚠️ 功能基本可用，但存在问题需要修复');
        } else {
            console.log('❌ 存在严重问题，需要紧急修复');
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
            systemInfo: {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language
            }
        };
        
        window.finalTestReport = report;
        console.log('\n💾 测试报告已保存到 window.finalTestReport');
        
        return report;
    }
    
    exportReport(format = 'json') {
        const report = window.finalTestReport;
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
            let textReport = `Angela AI 最终测试报告\n`;
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
    console.log('🚀 启动最终集成测试套件...');
    const tester = new FinalIntegrationTester();
    window.finalTester = tester;
    
    await tester.runAllTests();
    
    console.log('\n🔧 测试工具已就绪');
    console.log('使用方法:');
    console.log('- 重新运行测试: window.finalTester.runAllTests()');
    console.log('- 导出报告: window.finalTester.exportReport("json")');
    console.log('- 查看报告: window.finalTestReport');
})();

// 导出类
window.FinalIntegrationTester = FinalIntegrationTester;