/**
 * Angela AI - Final Integration and Testing
 * 
 * Integrate all optimizations and system test
 */

class AngelaIntegrationTester {
    constructor() {
        this.testResults = {};
        this.isTesting = false;
    }
    
    async runFullIntegrationTest() {
        if (this.isTesting) {
            console.log('⚠️ Test already in progress');
            return;
        }
        
        this.isTesting = true;
        console.log('🧪 Starting full integration test...');
        
        try {
            // 1. 测试API连接
            await this.testAPISystem();
            
            // 2. 测试硬件检测增强
            await this.testHardwareDetection();
            
            // 3. 测试Live2D加载优化
            await this.testLive2DLoading();
            
            // 4. 测试笔记本优化
            await this.testLaptopOptimization();
            
            // 5. 生成测试报告
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ Integration test failed:', error);
        } finally {
            this.isTesting = false;
        }
    }
    
    async testAPISystem() {
        console.log('📡 Testing API system...');
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/status');
            const data = await response.json();
            
            this.testResults.api = {
                status: 'passed',
                response: data,
                timestamp: new Date().toISOString()
            };
            
            console.log('✅ API test passed');
        } catch (error) {
            this.testResults.api = {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            
            console.error('❌ API test failed:', error);
        }
    }
    
    async testHardwareDetection() {
        console.log('🖥️ Testing hardware detection...');
        
        try {
            // 等待硬件检测完成
            await this._waitForHardwareDetection();
            
            const detector = window.angelaApp?.hardwareDetector;
            if (!detector) {
                throw new Error('Hardware detector not found');
            }
            
            const profile = detector.profile;
            const capabilities = detector.capabilities;
            
            this.testResults.hardware = {
                status: 'passed',
                profile: profile,
                capabilities: capabilities,
                enhanced: typeof window.EnhancedHardwareDetector !== 'undefined',
                timestamp: new Date().toISOString()
            };
            
            console.log('✅ Hardware detection test passed');
            console.log('🖥️ Detected hardware:', profile);
        } catch (error) {
            this.testResults.hardware = {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            
            console.error('❌ Hardware detection test failed:', error);
        }
    }
    
    async testLive2DLoading() {
        console.log('🎭 Testing Live2D loading...');
        
        try {
            const manager = window.angelaApp?.live2dManager;
            if (!manager) {
                throw new Error('Live2D manager not found');
            }
            
            // 检查SDK加载状态
            const sdkLoaded = manager.sdk !== undefined;
            const modelLoaded = manager.modelLoaded;
            
            this.testResults.live2d = {
                status: 'passed',
                sdkLoaded: sdkLoaded,
                modelLoaded: modelLoaded,
                enhancedWrapper: typeof window.EnhancedLive2DCubismWrapper !== 'undefined',
                timestamp: new Date().toISOString()
            };
            
            console.log('✅ Live2D loading test passed');
            console.log(`🎭 Live2D Status - SDK: ${sdkLoaded}, Model: ${modelLoaded}`);
        } catch (error) {
            this.testResults.live2d = {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            
            console.error('❌ Live2D loading test failed:', error);
        }
    }
    
    async testLaptopOptimization() {
        console.log('🔋 Testing laptop optimization...');
        
        try {
            const optimizer = window.laptopOptimizer;
            if (!optimizer) {
                // 不是笔记本电脑或者优化器未加载
                this.testResults.laptop = {
                    status: 'skipped',
                    reason: 'Not a laptop or optimizer not loaded',
                    timestamp: new Date().toISOString()
                };
                console.log('⏭️ Laptop optimization test skipped');
                return;
            }
            
            const status = optimizer.getOptimizationStatus();
            
            this.testResults.laptop = {
                status: 'passed',
                isLaptop: status.isLaptop,
                isOptimized: status.isOptimized,
                currentProfile: status.currentProfile,
                batteryStatus: status.batteryStatus,
                timestamp: new Date().toISOString()
            };
            
            console.log('✅ Laptop optimization test passed');
            console.log('🔋 Laptop Status:', status);
        } catch (error) {
            this.testResults.laptop = {
                status: 'failed',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            
            console.error('❌ Laptop optimization test failed:', error);
        }
    }
    
    async _waitForHardwareDetection() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 40;  // 增加超時次數
            
            const checkInterval = setInterval(() => {
                attempts++;
                
                if (window.angelaApp?.hardwareDetector?.profile) {
                    clearInterval(checkInterval);
                    resolve();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('Hardware detection timeout after ' + (attempts * 500) + 'ms'));
                }
            }, 500);
        });
    }
    
    generateTestReport() {
        console.log('\n📋 INTEGRATION TEST REPORT');
        console.log('==========================');
        
        const totalTests = Object.keys(this.testResults).length;
        let passedTests = 0;
        let failedTests = 0;
        let skippedTests = 0;
        
        for (const [testName, result] of Object.entries(this.testResults)) {
            const statusIcon = result.status === 'passed' ? '✅' : 
                              result.status === 'failed' ? '❌' : '⏭️';
            
            console.log(`${statusIcon} ${testName.toUpperCase()}: ${result.status}`);
            
            if (result.status === 'passed') passedTests++;
            else if (result.status === 'failed') failedTests++;
            else skippedTests++;
        }
        
        console.log('\n📊 SUMMARY:');
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests}`);
        console.log(`Failed: ${failedTests}`);
        console.log(`Skipped: ${skippedTests}`);
        console.log(`Success Rate: ${Math.round((passedTests / totalTests) * 100)}%`);
        
        // 生成详细报告对象
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: totalTests,
                passed: passedTests,
                failed: failedTests,
                skipped: skippedTests,
                successRate: Math.round((passedTests / totalTests) * 100)
            },
            details: this.testResults
        };
        
        // 保存报告到localStorage
        try {
            localStorage.setItem('angela_integration_test_report', JSON.stringify(report));
            console.log('💾 Test report saved to localStorage');
        } catch (error) {
            console.warn('⚠️ Failed to save test report:', error);
        }
        
        return report;
    }
    
    // 快速健康检查
    async quickHealthCheck() {
        console.log('🩺 Running quick health check...');
        
        const checks = {
            api: await this._checkAPIHealth(),
            hardware: await this._checkHardwareHealth(),
            live2d: await this._checkLive2DHealth(),
            laptop: await this._checkLaptopHealth()
        };
        
        const healthy = Object.values(checks).every(check => check.healthy);
        
        console.log(`🩺 Health Check Result: ${healthy ? 'HEALTHY' : 'ISSUES FOUND'}`);
        
        return {
            healthy: healthy,
            checks: checks,
            timestamp: new Date().toISOString()
        };
    }
    
    async _checkAPIHealth() {
        try {
            const response = await fetch('http://127.0.0.1:8000/health', { timeout: 5000 });
            return { healthy: response.ok, details: 'API responding' };
        } catch {
            return { healthy: false, details: 'API not responding' };
        }
    }
    
    async _checkHardwareHealth() {
        const detector = window.angelaApp?.hardwareDetector;
        return {
            healthy: !!detector?.profile,
            details: detector ? 'Hardware detected' : 'No hardware detection'
        };
    }
    
    async _checkLive2DHealth() {
        const manager = window.angelaApp?.live2dManager;
        return {
            healthy: !!manager,
            details: manager ? 'Live2D manager active' : 'No Live2D manager'
        };
    }
    
    async _checkLaptopHealth() {
        const optimizer = window.laptopOptimizer;
        return {
            healthy: !!optimizer,
            details: optimizer ? 'Laptop optimizer active' : 'No laptop optimization'
        };
    }
}

// 自动运行测试
(function() {
    // 延迟执行以确保所有系统加载完成
    setTimeout(async () => {
        const tester = new AngelaIntegrationTester();
        window.integrationTester = tester;
        
        console.log('🚀 Angela AI Integration Tester Ready');
        console.log('Commands available:');
        console.log('- window.integrationTester.runFullIntegrationTest()');
        console.log('- window.integrationTester.quickHealthCheck()');
        
        // 自动运行快速健康检查
        const health = await tester.quickHealthCheck();
        if (!health.healthy) {
            console.warn('⚠️ System health issues detected, running full test...');
            await tester.runFullIntegrationTest();
        } else {
            console.log('✅ System health check passed');
        }
    }, 3000);
})();

// 导出测试器
window.AngelaIntegrationTester = AngelaIntegrationTester;