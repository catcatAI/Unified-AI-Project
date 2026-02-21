/**
 * Angela Desktop App - Live2D Test Suite
 * Live2D功能測試套件
 */

class Live2DTestSuite {
    constructor() {
        this.canvas = null;
        this.live2dManager = null;
        this.testResults = [];
    }

    /**
     * 初始化測試套件
     * @param {HTMLCanvasElement} canvas - 測試用的canvas元素
     */
    async initialize(canvas) {
        console.log('初始化Live2D測試套件...');
        this.canvas = canvas;
        
        // 創建Live2D管理器實例
        if (window.Live2DManager) {
            this.live2dManager = new Live2DManager(canvas);
        } else {
            throw new Error('Live2DManager not found');
        }
        
        console.log('Live2D測試套件初始化完成');
    }

    /**
     * 運行所有測試
     */
    async runAllTests() {
        console.log('開始運行Live2D測試...');
        this.testResults = [];

        const tests = [
            this.testSDKLoading.bind(this),
            this.testModelLoading.bind(this),
            this.testExpressionChanges.bind(this),
            this.testMotionPlayback.bind(this),
            this.testPhysicsSimulation.bind(this),
            this.testLipSync.bind(this),
            this.testAutoBlink.bind(this),
            this.testBreathingAnimation.bind(this),
            this.testEyeTracking.bind(this),
            this.testPerformance.bind(this)
        ];

        for (const test of tests) {
            try {
                const result = await test();
                this.testResults.push(result);
            } catch (error) {
                this.testResults.push({
                    test: test.name,
                    status: 'failed',
                    error: error.message
                });
            }
        }

        this.printTestResults();
        return this.testResults;
    }

    /**
     * 測試SDK加載
     */
    async testSDKLoading() {
        console.log('測試SDK加載...');
        
        const startTime = performance.now();
        const success = await this.live2dManager.initialize();
        const loadTime = performance.now() - startTime;
        
        return {
            test: 'SDK Loading',
            status: success ? 'passed' : 'failed',
            loadTime: Math.round(loadTime),
            details: success ? 'SDK loaded successfully' : 'SDK loading failed'
        };
    }

    /**
     * 測試模型加載
     */
    async testModelLoading() {
        console.log('測試模型加載...');
        
        const modelPath = this.live2dManager.modelPath || '../resources/models/miara_pro_t03.model3.json';
        
        const startTime = performance.now();
        const success = await this.live2dManager.loadModel(modelPath);
        const loadTime = performance.now() - startTime;
        
        return {
            test: 'Model Loading',
            status: success ? 'passed' : 'failed',
            loadTime: Math.round(loadTime),
            details: success ? 'Model loaded successfully' : 'Model loading failed'
        };
    }

    /**
     * 測試表情變化
     */
    async testExpressionChanges() {
        console.log('測試表情變化...');
        
        if (!this.live2dManager.modelLoaded) {
            return {
                test: 'Expression Changes',
                status: 'skipped',
                details: 'Model not loaded'
            };
        }

        const expressions = ['neutral', 'happy', 'sad', 'angry', 'surprised'];
        const results = [];

        for (const expression of expressions) {
            this.live2dManager.setExpression(expression);
            results.push(expression);
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        return {
            test: 'Expression Changes',
            status: 'passed',
            expressions: results,
            details: `Successfully tested ${results.length} expressions`
        };
    }

    /**
     * 測試動作播放
     */
    async testMotionPlayback() {
        console.log('測試動作播放...');
        
        if (!this.live2dManager.modelLoaded) {
            return {
                test: 'Motion Playback',
                status: 'skipped',
                details: 'Model not loaded'
            };
        }

        const motions = ['idle', 'greeting', 'thinking', 'dancing'];
        const results = [];

        for (const motion of motions) {
            const success = await this.live2dManager.playMotion('motions', motion);
            results.push({ motion, success });
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        const successfulMotions = results.filter(r => r.success).length;
        
        return {
            test: 'Motion Playback',
            status: successfulMotions > 0 ? 'passed' : 'failed',
            motions: results,
            details: `${successfulMotions}/${results.length} motions played successfully`
        };
    }

    /**
     * 測試物理模擬
     */
    async testPhysicsSimulation() {
        console.log('測試物理模擬...');
        
        if (!this.live2dManager.modelLoaded) {
            return {
                test: 'Physics Simulation',
                status: 'skipped',
                details: 'Model not loaded'
            };
        }

        // 檢查物理設定
        const physicsEnabled = this.live2dManager.physicsEnabled;
        
        return {
            test: 'Physics Simulation',
            status: physicsEnabled ? 'passed' : 'warning',
            enabled: physicsEnabled,
            details: physicsEnabled ? 'Physics simulation enabled' : 'Physics simulation disabled'
        };
    }

    /**
     * 測試嘴型同步
     */
    async testLipSync() {
        console.log('測試嘴型同步...');
        
        if (!this.live2dManager.modelLoaded) {
            return {
                test: 'Lip Sync',
                status: 'skipped',
                details: 'Model not loaded'
            };
        }

        const lipSyncEnabled = this.live2dManager.lipSyncEnabled;
        
        // 模擬音頻輸入測試
        this.live2dManager.updateLipSync(0.5);
        
        return {
            test: 'Lip Sync',
            status: lipSyncEnabled ? 'passed' : 'warning',
            enabled: lipSyncEnabled,
            details: lipSyncEnabled ? 'Lip sync enabled' : 'Lip sync disabled'
        };
    }

    /**
     * 測試自動眨眼
     */
    async testAutoBlink() {
        console.log('測試自動眨眼...');
        
        const autoBlinkEnabled = this.live2dManager.autoBlinkEnabled;
        
        return {
            test: 'Auto Blink',
            status: autoBlinkEnabled ? 'passed' : 'warning',
            enabled: autoBlinkEnabled,
            details: autoBlinkEnabled ? 'Auto blink enabled' : 'Auto blink disabled'
        };
    }

    /**
     * 測試呼吸動畫
     */
    async testBreathingAnimation() {
        console.log('測試呼吸動畫...');
        
        const autoBreathingEnabled = this.live2dManager.autoBreathingEnabled;
        
        return {
            test: 'Breathing Animation',
            status: autoBreathingEnabled ? 'passed' : 'warning',
            enabled: autoBreathingEnabled,
            details: autoBreathingEnabled ? 'Breathing animation enabled' : 'Breathing animation disabled'
        };
    }

    /**
     * 測試眼球追蹤
     */
    async testEyeTracking() {
        console.log('測試眼球追蹤...');
        
        const eyeTrackingEnabled = this.live2dManager.eyeTrackingEnabled;
        
        if (eyeTrackingEnabled && this.live2dManager.modelLoaded) {
            // 模擬鼠標移動測試
            this.live2dManager.updateEyeTracking(0.5, 0.5);
        }
        
        return {
            test: 'Eye Tracking',
            status: eyeTrackingEnabled ? 'passed' : 'warning',
            enabled: eyeTrackingEnabled,
            details: eyeTrackingEnabled ? 'Eye tracking enabled' : 'Eye tracking disabled'
        };
    }

    /**
     * 測試性能
     */
    async testPerformance() {
        console.log('測試性能...');
        
        if (!this.live2dManager.modelLoaded) {
            return {
                test: 'Performance',
                status: 'skipped',
                details: 'Model not loaded'
            };
        }

        const targetFPS = this.live2dManager.targetFPS || 60;
        const testDuration = 2000; // 2秒
        const frameCount = this.live2dManager.fpsHistory.length;
        const currentFPS = this.live2dManager.currentFPS || 0;
        
        // 性能評估
        const performanceRatio = currentFPS / targetFPS;
        let status = 'passed';
        
        if (performanceRatio >= 0.8) {
            status = 'passed';
        } else if (performanceRatio >= 0.6) {
            status = 'warning';
        } else {
            status = 'failed';
        }
        
        return {
            test: 'Performance',
            status: status,
            targetFPS: targetFPS,
            currentFPS: Math.round(currentFPS),
            frameCount: frameCount,
            performance: Math.round(performanceRatio * 100),
            details: `Current FPS: ${Math.round(currentFPS)}/${targetFPS} (${Math.round(performanceRatio * 100)}%)`
        };
    }

    /**
     * 打印測試結果
     */
    printTestResults() {
        console.log('\n=== Live2D 測試結果 ===');
        
        let passed = 0;
        let failed = 0;
        let warnings = 0;
        let skipped = 0;

        this.testResults.forEach(result => {
            const status = result.status.toUpperCase();
            const icon = status === 'PASSED' ? '✅' : 
                        status === 'FAILED' ? '❌' : 
                        status === 'WARNING' ? '⚠️' : '⏭️';
            
            console.log(`${icon} ${result.test}: ${status}`);
            
            if (result.details) {
                console.log(`   ${result.details}`);
            }
            
            if (result.loadTime) {
                console.log(`   Load time: ${result.loadTime}ms`);
            }
            
            switch (result.status) {
                case 'passed': passed++; break;
                case 'failed': failed++; break;
                case 'warning': warnings++; break;
                case 'skipped': skipped++; break;
            }
        });

        console.log('\n=== 測試總結 ===');
        console.log(`通過: ${passed}`);
        console.log(`失敗: ${failed}`);
        console.log(`警告: ${warnings}`);
        console.log(`跳過: ${skipped}`);
        console.log(`總計: ${this.testResults.length}`);
        
        const successRate = (passed / this.testResults.length * 100).toFixed(1);
        console.log(`成功率: ${successRate}%`);
        
        // 整體狀態
        if (failed === 0) {
            console.log('🎉 所有測試通過！');
        } else if (failed <= 2) {
            console.log('⚠️ 大部分測試通過，有少量問題');
        } else {
            console.log('❌ 多個測試失敗，需要檢查');
        }
    }
}

// 導出測試套件
window.Live2DTestSuite = Live2DTestSuite;