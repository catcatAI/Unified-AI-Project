/**
 * Angela AI - 模型资源深度检查工具
 * 
 * 专门检查Live2D模型资源的完整性和可访问性
 */

class ModelResourceChecker {
    constructor() {
        this.modelPaths = {
            base: '../resources/models/miara_pro/',
            alternative: './resources/models/miara_pro/',
            backup: '../models/miara_pro/'
        };
        
        this.requiredFiles = {
            model: 'miara_pro_t03.model3.json',
            texture: 'texture_00.png',
            expressions: 'miara_pro_t03.cdi3.json',
            physics: 'miara_pro_t03.physics3.json',
            pose: 'miara_pro_t03.pose3.json'
        };
        
        this.optionalFiles = {
            motions: 'motions/',
            textures: 'textures/',
            sounds: 'sounds/'
        };
        
        this.checkResults = {};
    }
    
    async runCompleteResourceCheck() {
        console.log('🔍 开始模型资源深度检查...\n');
        
        try {
            // 1. 检查基础路径可访问性
            await this.checkBasePaths();
            
            // 2. 验证必需文件
            await this.verifyRequiredFiles();
            
            // 3. 检查可选资源
            await this.checkOptionalResources();
            
            // 4. 验证文件完整性
            await this.validateFileIntegrity();
            
            // 5. 测试加载性能
            await this.testLoadingPerformance();
            
            // 6. 生成详细报告
            this.generateResourceReport();
            
        } catch (error) {
            console.error('❌ 资源检查过程中出现错误:', error);
        }
        
        return this.checkResults;
    }
    
    async checkBasePaths() {
        console.log('=== 基础路径检查 ===');
        
        const pathResults = {};
        
        for (const [name, path] of Object.entries(this.modelPaths)) {
            try {
                const response = await fetch(path, { method: 'HEAD' });
                pathResults[name] = {
                    accessible: response.ok,
                    statusCode: response.status,
                    path: path
                };
                console.log(`${name}: ${response.ok ? '✅' : '❌'} (${response.status}) ${path}`);
            } catch (error) {
                pathResults[name] = {
                    accessible: false,
                    error: error.message,
                    path: path
                };
                console.log(`${name}: ❌ 错误 - ${error.message}`);
            }
        }
        
        this.checkResults.paths = pathResults;
        
        // 确定主路径
        const accessiblePaths = Object.entries(pathResults)
            .filter(([_, result]) => result.accessible);
            
        if (accessiblePaths.length > 0) {
            this.mainPath = accessiblePaths[0][1].path;
            console.log(`\n🎯 确定主路径: ${this.mainPath}`);
        } else {
            console.log('\n❌ 无可用路径');
        }
    }
    
    async verifyRequiredFiles() {
        console.log('\n=== 必需文件验证 ===');
        
        if (!this.mainPath) {
            console.log('❌ 无可用的基础路径');
            return;
        }
        
        const fileResults = {};
        
        for (const [type, filename] of Object.entries(this.requiredFiles)) {
            const fullPath = this.mainPath + filename;
            try {
                const response = await fetch(fullPath, { method: 'HEAD' });
                fileResults[type] = {
                    exists: response.ok,
                    statusCode: response.status,
                    size: response.headers.get('content-length'),
                    path: fullPath
                };
                console.log(`${type}: ${response.ok ? '✅' : '❌'} ${filename}`);
            } catch (error) {
                fileResults[type] = {
                    exists: false,
                    error: error.message,
                    path: fullPath
                };
                console.log(`${type}: ❌ ${filename} - ${error.message}`);
            }
        }
        
        this.checkResults.requiredFiles = fileResults;
        
        // 检查关键文件缺失
        const missingCritical = Object.entries(fileResults)
            .filter(([type, result]) => !result.exists && ['model', 'texture'].includes(type));
            
        if (missingCritical.length > 0) {
            console.log('\n🚨 关键文件缺失:');
            missingCritical.forEach(([type, _]) => {
                console.log(`  • ${type}: ${this.requiredFiles[type]}`);
            });
        }
    }
    
    async checkOptionalResources() {
        console.log('\n=== 可选资源检查 ===');
        
        if (!this.mainPath) return;
        
        const optionalResults = {};
        
        for (const [type, resource] of Object.entries(this.optionalFiles)) {
            const fullPath = this.mainPath + resource;
            try {
                const response = await fetch(fullPath, { method: 'HEAD' });
                optionalResults[type] = {
                    accessible: response.ok,
                    statusCode: response.status,
                    path: fullPath
                };
                console.log(`${type}: ${response.ok ? '✅' : '⚠️'} ${resource}`);
            } catch (error) {
                optionalResults[type] = {
                    accessible: false,
                    error: error.message,
                    path: fullPath
                };
                console.log(`${type}: ❌ ${resource} - ${error.message}`);
            }
        }
        
        this.checkResults.optionalResources = optionalResults;
    }
    
    async validateFileIntegrity() {
        console.log('\n=== 文件完整性验证 ===');
        
        if (!this.mainPath) return;
        
        const integrityResults = {};
        
        // 验证模型定义文件内容
        const modelPath = this.mainPath + this.requiredFiles.model;
        try {
            const response = await fetch(modelPath);
            if (response.ok) {
                const content = await response.json();
                integrityResults.model = this.validateModelDefinition(content);
                console.log(`模型定义: ${integrityResults.model.valid ? '✅' : '❌'}`);
            }
        } catch (error) {
            integrityResults.model = {
                valid: false,
                error: error.message
            };
            console.log(`模型定义: ❌ ${error.message}`);
        }
        
        // 验证纹理文件
        const texturePath = this.mainPath + this.requiredFiles.texture;
        try {
            const response = await fetch(texturePath);
            integrityResults.texture = {
                valid: response.ok,
                contentType: response.headers.get('content-type'),
                size: response.headers.get('content-length')
            };
            console.log(`纹理文件: ${response.ok ? '✅' : '❌'}`);
        } catch (error) {
            integrityResults.texture = {
                valid: false,
                error: error.message
            };
            console.log(`纹理文件: ❌ ${error.message}`);
        }
        
        this.checkResults.integrity = integrityResults;
    }
    
    validateModelDefinition(content) {
        const requiredFields = ['Version', 'FileReferences'];
        const missingFields = requiredFields.filter(field => !content[field]);
        
        return {
            valid: missingFields.length === 0,
            missingFields: missingFields,
            version: content.Version,
            hasMoc: !!content.FileReferences?.Moc,
            hasTextures: Array.isArray(content.FileReferences?.Textures),
            textureCount: content.FileReferences?.Textures?.length || 0
        };
    }
    
    async testLoadingPerformance() {
        console.log('\n=== 加载性能测试 ===');
        
        if (!this.mainPath) return;
        
        const performanceResults = {};
        
        // 测试模型文件加载时间
        const modelPath = this.mainPath + this.requiredFiles.model;
        try {
            const startTime = performance.now();
            const response = await fetch(modelPath);
            const content = await response.json();
            const loadTime = performance.now() - startTime;
            
            performanceResults.modelLoad = {
                time: loadTime,
                size: JSON.stringify(content).length,
                success: true
            };
            console.log(`模型加载: ${loadTime.toFixed(2)}ms`);
        } catch (error) {
            performanceResults.modelLoad = {
                time: -1,
                error: error.message,
                success: false
            };
            console.log(`模型加载: ❌ ${error.message}`);
        }
        
        // 测试纹理文件加载时间
        const texturePath = this.mainPath + this.requiredFiles.texture;
        try {
            const startTime = performance.now();
            const response = await fetch(texturePath);
            const blob = await response.blob();
            const loadTime = performance.now() - startTime;
            
            performanceResults.textureLoad = {
                time: loadTime,
                size: blob.size,
                success: true
            };
            console.log(`纹理加载: ${loadTime.toFixed(2)}ms (${blob.size} bytes)`);
        } catch (error) {
            performanceResults.textureLoad = {
                time: -1,
                error: error.message,
                success: false
            };
            console.log(`纹理加载: ❌ ${error.message}`);
        }
        
        this.checkResults.performance = performanceResults;
    }
    
    async checkMotionFiles() {
        console.log('\n=== 动作文件检查 ===');
        
        if (!this.mainPath) return;
        
        const motionsPath = this.mainPath + 'motions/';
        const motionResults = {
            directoryAccessible: false,
            motionFiles: []
        };
        
        try {
            // 尝试访问动作目录
            const dirResponse = await fetch(motionsPath, { method: 'HEAD' });
            motionResults.directoryAccessible = dirResponse.ok;
            console.log(`动作目录: ${dirResponse.ok ? '✅' : '❌'}`);
            
            if (dirResponse.ok) {
                // 尝试列出动作文件（这在浏览器中通常不可行）
                // 但我们可以通过尝试访问常见的动作文件来测试
                const commonMotions = [
                    'idle.motion3.json',
                    'tap_body.motion3.json',
                    'tap_head.motion3.json'
                ];
                
                for (const motionFile of commonMotions) {
                    try {
                        const response = await fetch(motionsPath + motionFile, { method: 'HEAD' });
                        motionResults.motionFiles.push({
                            name: motionFile,
                            exists: response.ok,
                            statusCode: response.status
                        });
                    } catch (error) {
                        motionResults.motionFiles.push({
                            name: motionFile,
                            exists: false,
                            error: error.message
                        });
                    }
                }
                
                const existingMotions = motionResults.motionFiles.filter(f => f.exists);
                console.log(`发现动作文件: ${existingMotions.length}/${commonMotions.length}`);
            }
        } catch (error) {
            console.log(`动作检查: ❌ ${error.message}`);
        }
        
        this.checkResults.motions = motionResults;
    }
    
    generateResourceReport() {
        console.log('\n' + '='.repeat(50));
        console.log('📊 模型资源检查报告');
        console.log('='.repeat(50));
        
        // 路径状态
        console.log('\n📁 路径状态:');
        Object.entries(this.checkResults.paths || {}).forEach(([name, result]) => {
            console.log(`  ${name}: ${result.accessible ? '✅' : '❌'} ${result.path}`);
        });
        
        // 必需文件状态
        console.log('\n📄 必需文件:');
        Object.entries(this.checkResults.requiredFiles || {}).forEach(([type, result]) => {
            const status = result.exists ? '✅' : '❌';
            console.log(`  ${type}: ${status} ${this.requiredFiles[type]}`);
        });
        
        // 可选资源状态
        console.log('\n📎 可选资源:');
        Object.entries(this.checkResults.optionalResources || {}).forEach(([type, result]) => {
            const status = result.accessible ? '✅' : '⚠️';
            console.log(`  ${type}: ${status} ${this.optionalFiles[type]}`);
        });
        
        // 完整性验证
        if (this.checkResults.integrity) {
            console.log('\n🔍 完整性验证:');
            const modelValid = this.checkResults.integrity.model?.valid;
            const textureValid = this.checkResults.integrity.texture?.valid;
            console.log(`  模型定义: ${modelValid ? '✅' : '❌'}`);
            console.log(`  纹理文件: ${textureValid ? '✅' : '❌'}`);
        }
        
        // 性能数据
        if (this.checkResults.performance) {
            console.log('\n⚡ 性能数据:');
            const modelTime = this.checkResults.performance.modelLoad?.time;
            const textureTime = this.checkResults.performance.textureLoad?.time;
            if (modelTime > 0) console.log(`  模型加载: ${modelTime.toFixed(2)}ms`);
            if (textureTime > 0) console.log(`  纹理加载: ${textureTime.toFixed(2)}ms`);
        }
        
        // 生成问题列表
        const issues = this.identifyIssues();
        if (issues.length > 0) {
            console.log('\n🚨 发现的问题:');
            issues.forEach((issue, index) => {
                console.log(`${index + 1}. ${issue}`);
            });
        } else {
            console.log('\n🎉 所有资源检查通过！');
        }
        
        // 保存报告
        const report = {
            timestamp: new Date().toISOString(),
            results: this.checkResults,
            issues: issues,
            mainPath: this.mainPath
        };
        
        window.resourceCheckReport = report;
        console.log('\n💾 资源检查报告已保存到 window.resourceCheckReport');
        
        return report;
    }
    
    identifyIssues() {
        const issues = [];
        
        // 检查路径问题
        if (this.checkResults.paths) {
            const inaccessiblePaths = Object.entries(this.checkResults.paths)
                .filter(([_, result]) => !result.accessible);
            if (inaccessiblePaths.length === Object.keys(this.checkResults.paths).length) {
                issues.push('所有模型路径都无法访问');
            }
        }
        
        // 检查关键文件缺失
        if (this.checkResults.requiredFiles) {
            const missingFiles = Object.entries(this.checkResults.requiredFiles)
                .filter(([type, result]) => !result.exists && ['model', 'texture'].includes(type));
            missingFiles.forEach(([type, _]) => {
                issues.push(`缺少关键文件: ${this.requiredFiles[type]}`);
            });
        }
        
        // 检查完整性问题
        if (this.checkResults.integrity) {
            if (this.checkResults.integrity.model && !this.checkResults.integrity.model.valid) {
                issues.push('模型定义文件格式不正确');
            }
            if (this.checkResults.integrity.texture && !this.checkResults.integrity.texture.valid) {
                issues.push('纹理文件损坏或格式不支持');
            }
        }
        
        // 检查性能问题
        if (this.checkResults.performance) {
            const modelTime = this.checkResults.performance.modelLoad?.time;
            const textureTime = this.checkResults.performance.textureLoad?.time;
            if (modelTime > 10000) {
                issues.push(`模型加载过慢: ${modelTime.toFixed(0)}ms`);
            }
            if (textureTime > 5000) {
                issues.push(`纹理加载过慢: ${textureTime.toFixed(0)}ms`);
            }
        }
        
        return issues;
    }
    
    async fixCommonIssues() {
        console.log('\n🔧 尝试修复常见问题...');
        
        const fixesApplied = [];
        
        // 如果没有可用路径，尝试创建符号链接或复制文件
        if (!this.mainPath) {
            console.log('尝试创建资源目录...');
            // 这里可以添加创建目录的逻辑
            fixesApplied.push('资源目录创建建议已记录');
        }
        
        // 如果模型文件缺失，建议下载或重新导出
        if (this.checkResults.requiredFiles && 
            !this.checkResults.requiredFiles.model?.exists) {
            fixesApplied.push('建议重新导出或下载模型文件');
        }
        
        // 如果纹理文件缺失，建议检查导出设置
        if (this.checkResults.requiredFiles && 
            !this.checkResults.requiredFiles.texture?.exists) {
            fixesApplied.push('建议检查纹理导出设置');
        }
        
        console.log('已应用的修复:');
        fixesApplied.forEach(fix => console.log(`  • ${fix}`));
        
        return fixesApplied;
    }
}

// 立即执行资源检查
(async () => {
    console.log('🚀 启动模型资源深度检查工具...');
    const checker = new ModelResourceChecker();
    window.modelResourceChecker = checker;
    
    await checker.runCompleteResourceCheck();
    
    console.log('\n🔧 资源检查工具已就绪');
    console.log('使用方法:');
    console.log('- 运行完整检查: await window.modelResourceChecker.runCompleteResourceCheck()');
    console.log('- 查看报告: window.resourceCheckReport');
    console.log('- 尝试修复: await window.modelResourceChecker.fixCommonIssues()');
})();

// 导出类
window.ModelResourceChecker = ModelResourceChecker;