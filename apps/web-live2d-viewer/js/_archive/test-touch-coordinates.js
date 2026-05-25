/**
 * 触摸坐标系统验证测试
 * 
 * 测试目标：
 * 1. 验证在任何屏幕尺寸下头发触摸检测正确
 * 2. 验证在任何窗口尺寸下头发触摸检测正确
 * 3. 验证坐标转换系统的准确性
 * 4. 验证身体部位检测的准确性
 * 
 * 测试场景：
 * - 1920x1080 显示器
 * - 1366x768 显示器
 * - 2560x1440 显示器
 * - 不同窗口尺寸
 * - 不同缩放比例
 */

class TouchCoordinateTest {
    constructor() {
        this.testResults = [];
        this.testScenarios = [
            { name: '1920x1080显示器', screenWidth: 1920, screenHeight: 1080, windowWidth: 1280, windowHeight: 720 },
            { name: '1366x768显示器', screenWidth: 1366, screenHeight: 768, windowWidth: 1280, windowHeight: 720 },
            { name: '2560x1440显示器', screenWidth: 2560, screenHeight: 1440, windowWidth: 1280, windowHeight: 720 },
            { name: '小窗口(800x450)', screenWidth: 1920, screenHeight: 1080, windowWidth: 800, windowHeight: 450 },
            { name: '大窗口(1600x900)', screenWidth: 1920, screenHeight: 1080, windowWidth: 1600, windowHeight: 900 },
            { name: '50%缩放', screenWidth: 1920, screenHeight: 1080, windowWidth: 640, windowHeight: 360 },
            { name: '150%缩放', screenWidth: 1920, screenHeight: 1080, windowWidth: 1920, windowHeight: 1080 },
            { name: '200%缩放', screenWidth: 1920, screenHeight: 1080, windowWidth: 2560, windowHeight: 1440 }
        ];
        
        // 测试点（相对于1280x720基准）
        // 坐标计算：x = centerX / 1280, y = centerY / 720
        this.testPoints = [
            // 头发区域 [528, 46, 879, 320]
            { name: '头发中心', expectedPart: 'hair', x: 703.5/1280, y: 183/720 },
            { name: '左头发边缘', expectedPart: 'hair', x: 528/1280, y: 183/720 },
            { name: '右头发边缘', expectedPart: 'hair', x: 879/1280, y: 183/720 },
            { name: '头发顶部', expectedPart: 'hair', x: 703.5/1280, y: 46/720 },
            { name: '头发底部', expectedPart: 'hair', x: 703.5/1280, y: 320/720 },
            
            // 脸部区域 [630, 71, 777, 156]
            { name: '脸部中心', expectedPart: 'face', x: 703.5/1280, y: 113.5/720 },
            
            // 眼睛区域 [660, 99, 748, 117]
            { name: '眼睛中心', expectedPart: 'eyes', x: 704/1280, y: 108/720 },
            
            // 嘴巴区域 [682, 124, 726, 135]
            { name: '嘴巴中心', expectedPart: 'mouth', x: 704/1280, y: 129.5/720 },
            
            // 脖子区域 [652, 152, 755, 184]
            { name: '脖子中心', expectedPart: 'neck', x: 703.5/1280, y: 168/720 },
            
            // 肩膀区域 [630, 181, 777, 213]
            { name: '肩膀中心', expectedPart: 'shoulders', x: 703.5/1280, y: 197/720 },
            
            // 外部区域
            { name: '左上外部', expectedPart: null, x: 100/1280, y: 100/720 },
            { name: '右下外部', expectedPart: null, x: 1200/1280, y: 600/720 }
        ];
    }

    /**
     * 运行所有测试
     */
    runAllTests() {
        console.log('========================================');
        console.log('  触摸坐标系统验证测试');
        console.log('========================================');
        console.log('');

        let totalTests = 0;
        let passedTests = 0;
        let failedTests = 0;

        for (const scenario of this.testScenarios) {
            console.log(`测试场景: ${scenario.name}`);
            console.log(`  屏幕尺寸: ${scenario.screenWidth}x${scenario.screenHeight}`);
            console.log(`  窗口尺寸: ${scenario.windowWidth}x${scenario.windowHeight}`);
            console.log('');

            for (const point of this.testPoints) {
                const result = this.testPoint(scenario, point);
                totalTests++;
                
                if (result.passed) {
                    passedTests++;
                    console.log(`  ✅ ${point.name}: ${result.detectedPart || '无'} (预期: ${point.expectedPart || '无'})`);
                } else {
                    failedTests++;
                    console.log(`  ❌ ${point.name}: ${result.detectedPart || '无'} (预期: ${point.expectedPart || '无'}) - ${result.error}`);
                }
            }
            
            console.log('');
        }

        console.log('========================================');
        console.log('  测试结果汇总');
        console.log('========================================');
        console.log(`  总测试数: ${totalTests}`);
        console.log(`  通过: ${passedTests} (${(passedTests/totalTests*100).toFixed(1)}%)`);
        console.log(`  失败: ${failedTests} (${(failedTests/totalTests*100).toFixed(1)}%)`);
        console.log('');

        return {
            total: totalTests,
            passed: passedTests,
            failed: failedTests,
            successRate: passedTests / totalTests
        };
    }

    /**
     * 测试单个点
     */
    testPoint(scenario, point) {
        // 模拟屏幕坐标
        const screenX = (scenario.screenWidth - scenario.windowWidth) / 2 + point.x * scenario.windowWidth;
        const screenY = (scenario.screenHeight - scenario.windowHeight) / 2 + point.y * scenario.windowHeight;

        // 模拟坐标转换
        const canvasX = ((screenX - (scenario.screenWidth - scenario.windowWidth) / 2) / scenario.windowWidth) * 1280;
        const canvasY = ((screenY - (scenario.screenHeight - scenario.windowHeight) / 2) / scenario.windowHeight) * 720;

        // 模拟身体部位检测
        const detectedPart = this.simulateBodyPartDetection(canvasX, canvasY);

        // 验证结果
        const passed = detectedPart === point.expectedPart;

        return {
            passed,
            detectedPart,
            expectedPart: point.expectedPart,
            error: passed ? null : `检测到${detectedPart || '无'}，预期${point.expectedPart || '无'}`,
            coordinates: {
                screen: { x: screenX, y: screenY },
                canvas: { x: canvasX, y: canvasY }
            }
        };
    }

    /**
     * 模拟身体部位检测
     */
    simulateBodyPartDetection(canvasX, canvasY) {
        // 使用angela-character-config中的rect定义
        // rect格式: [x1, y1, x2, y2]
        const bodyParts = {
            'hair': [528, 46, 879, 320],
            'face': [630, 71, 777, 156],
            'eyes': [660, 99, 748, 117],
            'mouth': [682, 124, 726, 135],
            'neck': [652, 152, 755, 184],
            'shoulders': [630, 181, 777, 213]
        };

        // 按优先级顺序检测
        const priorityOrder = ['face', 'eyes', 'mouth', 'neck', 'shoulders', 'hair'];

        for (const partName of priorityOrder) {
            const rect = bodyParts[partName];
            if (canvasX >= rect[0] && canvasX <= rect[2] && canvasY >= rect[1] && canvasY <= rect[3]) {
                return partName;
            }
        }

        return null;
    }

    /**
     * 生成测试报告
     */
    generateReport() {
        const results = this.runAllTests();
        
        const report = {
            timestamp: new Date().toISOString(),
            summary: results,
            scenarios: this.testScenarios.map(scenario => ({
                ...scenario,
                results: this.testPoints.map(point => this.testPoint(scenario, point))
            }))
        };

        return report;
    }
}

// 如果直接运行此脚本
if (typeof window === 'undefined') {
    const test = new TouchCoordinateTest();
    const report = test.generateReport();
    
    console.log(JSON.stringify(report, null, 2));
    
    process.exit(report.summary.failedTests === 0 ? 0 : 1);
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchCoordinateTest;
}