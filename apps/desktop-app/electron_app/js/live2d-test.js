import Live2DCubismWrapper from './live2d-cubism-wrapper.js';
import { logger } from './logger.js';

class Live2DTestSuite {
    constructor() {
        this.wrapper = null;
        this.canvas = null;
        this.testResults = [];
    }

    async initialize(canvas) {
        this.canvas = canvas;
        this.wrapper = new Live2DCubismWrapper();
        
        const result = await this.wrapper.initialize(this.canvas);
        this.recordTest('Initialize', result);
        return result;
    }

    async runAllTests() {
        logger.info('Live2D Test Suite', 'Starting comprehensive tests...');
        
        await this.testSDKLoading();
        await this.testModelLoading();
        await this.testMotionPlayback();
        await this.testExpressionChanges();
        await this.testPhysics();
        await this.testLipSync();
        await this.testAutoBlink();
        await this.testBreathing();
        await this.testEyeTracking();
        await this.testPerformance();
        
        this.printResults();
    }

    async testSDKLoading() {
        logger.info('Live2D Test', 'Testing SDK loading...');
        
        try {
            const sdkLoaded = this.wrapper.isSDKLoaded();
            this.recordTest('SDK Loading', sdkLoaded, 'Cubism SDK loaded successfully');
            
            const cubismLoaded = this.wrapper.isCubismLoaded();
            this.recordTest('Cubism Loading', cubismLoaded, 'Cubism core loaded successfully');
            
            const rendererReady = this.wrapper.isRendererReady();
            this.recordTest('Renderer Ready', rendererReady, 'Renderer initialized successfully');
        } catch (error) {
            this.recordTest('SDK Loading', false, error.message);
        }
    }

    async testModelLoading() {
        logger.info('Live2D Test', 'Testing model loading...');
        
        try {
            const modelPath = 'resources/models/miara_pro_en/runtime/miara_pro_t03.model3.json';
            const loaded = await this.wrapper.loadModel(modelPath);
            this.recordTest('Model Loading', loaded, 'Model loaded successfully');
            
            if (loaded) {
                const model = this.wrapper.getModel();
                this.recordTest('Model Instance', model !== null, 'Model instance created');
                
                const canvasSize = this.wrapper.getCanvasSize();
                this.recordTest('Canvas Size', canvasSize.width > 0, `Canvas: ${canvasSize.width}x${canvasSize.height}`);
            }
        } catch (error) {
            this.recordTest('Model Loading', false, error.message);
        }
    }

    async testMotionPlayback() {
        logger.info('Live2D Test', 'Testing motion playback...');
        
        const motions = [
            'idle',
            'greeting',
            'thinking',
            'dancing',
            'waving',
            'clapping',
            'nod',
            'shake'
        ];
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Motion Playback', false, 'Model not loaded');
            return;
        }
        
        for (const motion of motions) {
            try {
                this.wrapper.playMotion(motion);
                await this.sleep(500);
                this.recordTest(`Motion: ${motion}`, true, 'Motion played successfully');
            } catch (error) {
                this.recordTest(`Motion: ${motion}`, false, error.message);
            }
        }
    }

    async testExpressionChanges() {
        logger.info('Live2D Test', 'Testing expression changes...');
        
        const expressions = [
            'neutral',
            'happy',
            'sad',
            'angry',
            'surprised',
            'shy',
            'love'
        ];
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Expression Changes', false, 'Model not loaded');
            return;
        }
        
        for (const expr of expressions) {
            try {
                this.wrapper.setExpression(expr);
                await this.sleep(500);
                this.recordTest(`Expression: ${expr}`, true, 'Expression applied successfully');
            } catch (error) {
                this.recordTest(`Expression: ${expr}`, false, error.message);
            }
        }
    }

    async testPhysics() {
        logger.info('Live2D Test', 'Testing physics...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Physics', false, 'Model not loaded');
            return;
        }
        
        try {
            this.wrapper.enablePhysics(true);
            this.recordTest('Physics Enable', true, 'Physics enabled');
            
            await this.sleep(1000);
            
            this.wrapper.enablePhysics(false);
            this.recordTest('Physics Disable', true, 'Physics disabled');
        } catch (error) {
            this.recordTest('Physics', false, error.message);
        }
    }

    async testLipSync() {
        logger.info('Live2D Test', 'Testing lip sync...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Lip Sync', false, 'Model not loaded');
            return;
        }
        
        try {
            this.wrapper.enableLipSync(true);
            this.recordTest('Lip Sync Enable', true, 'Lip sync enabled');
            
            for (let i = 0; i < 10; i++) {
                const value = Math.random();
                this.wrapper.updateLipSync(value);
                await this.sleep(100);
            }
            
            this.recordTest('Lip Sync Update', true, 'Lip sync values updated');
            
            this.wrapper.enableLipSync(false);
            this.recordTest('Lip Sync Disable', true, 'Lip sync disabled');
        } catch (error) {
            this.recordTest('Lip Sync', false, error.message);
        }
    }

    async testAutoBlink() {
        logger.info('Live2D Test', 'Testing auto blink...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Auto Blink', false, 'Model not loaded');
            return;
        }
        
        try {
            this.wrapper.enableAutoBlink(true);
            this.recordTest('Auto Blink Enable', true, 'Auto blink enabled');
            
            await this.sleep(2000);
            
            this.wrapper.enableAutoBlink(false);
            this.recordTest('Auto Blink Disable', true, 'Auto blink disabled');
        } catch (error) {
            this.recordTest('Auto Blink', false, error.message);
        }
    }

    async testBreathing() {
        logger.info('Live2D Test', 'Testing breathing animation...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Breathing', false, 'Model not loaded');
            return;
        }
        
        try {
            this.wrapper.enableBreathing(true);
            this.recordTest('Breathing Enable', true, 'Breathing enabled');
            
            await this.sleep(2000);
            
            this.wrapper.enableBreathing(false);
            this.recordTest('Breathing Disable', true, 'Breathing disabled');
        } catch (error) {
            this.recordTest('Breathing', false, error.message);
        }
    }

    async testEyeTracking() {
        logger.info('Live2D Test', 'Testing eye tracking...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Eye Tracking', false, 'Model not loaded');
            return;
        }
        
        try {
            for (let x = -1; x <= 1; x += 0.5) {
                for (let y = -1; y <= 1; y += 0.5) {
                    this.wrapper.updateEyeTracking(x, y);
                    await this.sleep(200);
                }
            }
            
            this.recordTest('Eye Tracking', true, 'Eye tracking updated for multiple positions');
        } catch (error) {
            this.recordTest('Eye Tracking', false, error.message);
        }
    }

    async testPerformance() {
        logger.info('Live2D Test', 'Testing performance...');
        
        const model = this.wrapper.getModel();
        if (!model) {
            this.recordTest('Performance', false, 'Model not loaded');
            return;
        }
        
        try {
            const targetFPS = 60;
            const duration = 1000;
            const startTime = performance.now();
            let frameCount = 0;
            
            const testInterval = setInterval(() => {
                this.wrapper.update();
                this.wrapper.draw();
                frameCount++;
            }, 16);
            
            await this.sleep(duration);
            clearInterval(testInterval);
            
            const actualFPS = frameCount / (duration / 1000);
            const performanceRatio = actualFPS / targetFPS;
            
            this.recordTest('Performance', performanceRatio >= 0.8, 
                `Target: ${targetFPS} FPS, Actual: ${actualFPS.toFixed(1)} FPS (${(performanceRatio * 100).toFixed(1)}%)`);
            
            const memoryUsage = performance.memory ? 
                (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB' : 'N/A';
            
            this.recordTest('Memory Usage', true, `Memory: ${memoryUsage}`);
        } catch (error) {
            this.recordTest('Performance', false, error.message);
        }
    }

    recordTest(name, passed, details) {
        const result = {
            name,
            passed,
            details,
            timestamp: new Date().toISOString()
        };
        
        this.testResults.push(result);
        
        const status = passed ? '✓' : '✗';
        const message = `${status} ${name}: ${details}`;
        
        if (passed) {
            logger.info('Live2D Test', message);
        } else {
            logger.error('Live2D Test', message);
        }
    }

    printResults() {
        logger.info('Live2D Test Suite', 'Test Results Summary:');
        console.log('\n'.padEnd(80, '='));
        console.log('LIVE2D CUBISM WEB SDK TEST RESULTS');
        console.log('='.padEnd(80, '='));
        
        const passed = this.testResults.filter(r => r.passed).length;
        const failed = this.testResults.filter(r => !r.passed).length;
        const total = this.testResults.length;
        
        console.log(`\nTotal Tests: ${total}`);
        console.log(`Passed: ${passed} (${(passed / total * 100).toFixed(1)}%)`);
        console.log(`Failed: ${failed} (${(failed / total * 100).toFixed(1)}%)`);
        
        console.log('\nDetailed Results:');
        console.log('-'.padEnd(80, '-'));
        
        for (const result of this.testResults) {
            const status = result.passed ? 'PASS' : 'FAIL';
            const line = `${status.padEnd(6)} | ${result.name.padEnd(30)} | ${result.details}`;
            console.log(line);
        }
        
        console.log('='.padEnd(80, '='));
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

export default Live2DTestSuite;
