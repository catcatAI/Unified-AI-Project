/**
 * Simplified hardware diagnostic - can be run directly in console
 */

function diagnoseHardwareIssues() {
    console.log('🔬 开始硬件兼容性诊断...\n');
    
    const results = {};
    
    // 1. WebGL 支持检查
    console.log('=== WebGL 支持检查 ===');
    const canvas = document.createElement('canvas');
    let gl = canvas.getContext('webgl2');
    let webglVersion = 'WebGL 2.0';
    
    if (!gl) {
        gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        webglVersion = 'WebGL 1.0';
    }
    
    if (gl) {
        console.log(`✅ ${webglVersion} 支持正常`);
        results.webgl = { status: 'supported', version: webglVersion };
    } else {
        console.log('❌ WebGL 不支持 - 这是主要问题！');
        results.webgl = { status: 'not_supported', error: 'No WebGL context' };
        return results;
    }
    
    // 2. GPU 信息检查
    console.log('\n=== GPU 信息检查 ===');
    try {
        const vendor = gl.getParameter(gl.VENDOR);
        const renderer = gl.getParameter(gl.RENDERER);
        const version = gl.getParameter(gl.VERSION);
        
        console.log(`制造商: ${vendor}`);
        console.log(`渲染器: ${renderer}`);
        console.log(`版本: ${version}`);
        
        results.gpu = { vendor, renderer, version };
        
        // 检查是否为 Intel 核显
        if (renderer.toLowerCase().includes('intel')) {
            console.log('💡 检测到 Intel 核显');
        }
        // 检查是否为 AMD 核显
        else if (renderer.toLowerCase().includes('amd') || renderer.toLowerCase().includes('ati')) {
            console.log('💡 检测到 AMD 核显');
        }
        
    } catch (e) {
        console.log('⚠️ 无法获取 GPU 信息:', e.message);
    }
    
    // 3. 关键扩展检查
    console.log('\n=== 关键扩展检查 ===');
    const extensions = gl.getSupportedExtensions();
    const requiredExtensions = [
        'OES_texture_float',
        'OES_standard_derivatives',
        'WEBGL_depth_texture'
    ];
    
    const missingExtensions = [];
    requiredExtensions.forEach(ext => {
        if (extensions.includes(ext)) {
            console.log(`✅ ${ext}`);
        } else {
            console.log(`❌ ${ext} (缺失)`);
            missingExtensions.push(ext);
        }
    });
    
    results.extensions = {
        missing: missingExtensions,
        total: requiredExtensions.length,
        available: requiredExtensions.length - missingExtensions.length
    };
    
    if (missingExtensions.length > 0) {
        console.log(`\n⚠️ 缺少 ${missingExtensions.length} 个关键扩展`);
    }
    
    // 4. 硬件限制检查
    console.log('\n=== 硬件限制检查 ===');
    try {
        const maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
        const maxRenderbufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
        
        console.log(`最大纹理尺寸: ${maxTextureSize}x${maxTextureSize}`);
        console.log(`最大渲染缓冲区: ${maxRenderbufferSize}x${maxRenderbufferSize}`);
        
        results.limits = { maxTextureSize, maxRenderbufferSize };
        
        if (maxTextureSize < 2048) {
            console.log('⚠️ 纹理尺寸限制可能影响高质量渲染');
        }
        
    } catch (e) {
        console.log('⚠️ 无法获取硬件限制信息:', e.message);
    }
    
    // 5. 内存检查
    console.log('\n=== 系统内存检查 ===');
    try {
        if (navigator.deviceMemory) {
            console.log(`设备内存: ${navigator.deviceMemory} GB`);
            results.memory = { deviceMemory: navigator.deviceMemory };
            
            if (navigator.deviceMemory < 4) {
                console.log('⚠️ 内存较低，可能影响性能');
            }
        } else {
            console.log('⚠️ 无法检测设备内存');
        }
        
        if (navigator.hardwareConcurrency) {
            console.log(`CPU 核心数: ${navigator.hardwareConcurrency}`);
            results.cpu = { cores: navigator.hardwareConcurrency };
        }
        
    } catch (e) {
        console.log('⚠️ 内存信息获取失败:', e.message);
    }
    
    // 6. 问题诊断和建议
    console.log('\n=== 问题诊断和建议 ===');
    const issues = [];
    
    if (!gl) {
        issues.push({
            problem: 'WebGL 不支持',
            severity: 'critical',
            solution: '更新显卡驱动或使用支持 WebGL 的浏览器'
        });
    }
    
    if (results.extensions?.missing?.length > 0) {
        issues.push({
            problem: `缺少 ${results.extensions.missing.length} 个关键扩展`,
            severity: 'high',
            solution: '更新显卡驱动到最新版本'
        });
    }
    
    if (results.limits?.maxTextureSize < 2048) {
        issues.push({
            problem: '纹理尺寸限制过低',
            severity: 'medium',
            solution: '降低渲染质量设置或更新驱动'
        });
    }
    
    if (results.memory?.deviceMemory < 4) {
        issues.push({
            problem: '系统内存不足',
            severity: 'medium',
            solution: '关闭其他应用程序释放内存'
        });
    }
    
    if (issues.length === 0) {
        console.log('✅ 硬件完全兼容，应该能够正常运行 Angela AI');
        results.compatibility = 'full';
    } else {
        console.log('❌ 发现以下兼容性问题:');
        issues.forEach((issue, index) => {
            console.log(`${index + 1}. ${issue.problem} (${issue.severity})`);
            console.log(`   解决方案: ${issue.solution}`);
        });
        
        results.compatibility = 'partial';
        results.issues = issues;
    }
    
    // 7. Live2D 特定建议
    console.log('\n=== Live2D 运行建议 ===');
    if (results.compatibility === 'full') {
        console.log('✅ 应该能够正常显示 Live2D 模型');
    } else {
        console.log('⚠️ 可能需要以下调整:');
        console.log('  1. 降低渲染质量设置');
        console.log('  2. 禁用部分视觉特效');
        console.log('  3. 使用 2D 而非 3D 渲染模式');
        console.log('  4. 确保显卡驱动为最新版本');
    }
    
    console.log('\n📋 诊断完成');
    return results;
}

// 立即执行诊断
console.log('🚀 运行硬件诊断...');
const diagnosisResults = diagnoseHardwareIssues();

// 将结果保存到全局作用域便于查看
window.hardwareDiagnosis = diagnosisResults;
console.log('\n🔧 诊断结果已保存到 window.hardwareDiagnosis');
console.log('💡 如需重新诊断，请在控制台输入: diagnoseHardwareIssues()');