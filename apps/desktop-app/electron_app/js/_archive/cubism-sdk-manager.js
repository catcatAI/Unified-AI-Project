/**
 * Angela AI - Cubism SDK Manager
 * 
 * Manage local deployment and hybrid loading strategy for Live2D Cubism SDK
 */

class CubismSDKManager {
    constructor() {
        this.sdkVersions = {
            '4.2': {
                core: 'live2dcubismcore.min.js',
                framework: 'live2dcubismframework.min.js',
                version: '4.2.0'
            },
            '4.1': {
                core: 'live2dcubismcore.min.js',
                framework: 'live2dcubismframework.min.js', 
                version: '4.1.0'
            }
        };
        
        this.localPaths = [
            './assets/cubism/',
            '../assets/cubism/',
            './cubism-sdk/',
            '../cubism-sdk/'
        ];
        
        this.cdnUrls = {
            core: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
            framework: 'https://cubism.live2d.com/sdk-web/cubismframework/live2dcubismframework.min.js'
        };
        
        this.loadedComponents = {
            core: false,
            framework: false
        };
        
        this.preferredVersion = '4.2';
    }
    
    /**
     * Initialize Cubism SDK manager
     */
    async initialize() {
        console.log('🚀 Initializing Cubism SDK manager...');
        
        // 检查本地SDK是否存在
        const localAvailable = await this.checkLocalSDK();
        
        if (localAvailable) {
            console.log('✅ 检测到本地Cubism SDK');
            return await this.loadLocalSDK();
        } else {
            console.log('⚠️ 未找到本地SDK，尝试下载...');
            return await this.downloadAndSetupSDK();
        }
    }
    
    /**
     * 检查本地SDK是否存在
     */
    async checkLocalSDK() {
        console.log('🔍 检查本地Cubism SDK...');
        
        for (const basePath of this.localPaths) {
            try {
                const coreExists = await this.checkFileExists(`${basePath}${this.sdkVersions[this.preferredVersion].core}`);
                const frameworkExists = await this.checkFileExists(`${basePath}${this.sdkVersions[this.preferredVersion].framework}`);
                
                if (coreExists && frameworkExists) {
                    this.localBasePath = basePath;
                    console.log(`✅ 在 ${basePath} 找到完整SDK`);
                    return true;
                }
            } catch (error) {
                console.log(`🔍 检查路径 ${basePath} 失败:`, error.message);
            }
        }
        
        return false;
    }
    
    /**
     * 检查文件是否存在
     */
    async checkFileExists(filePath) {
        try {
            const response = await fetch(filePath, { method: 'HEAD' });
            return response.ok;
        } catch {
            return false;
        }
    }
    
    /**
     * 加载本地SDK
     */
    async loadLocalSDK() {
        console.log('📥 加载本地Cubism SDK...');
        
        try {
            // 加载Core
            const coreLoaded = await this.loadScript(
                `${this.localBasePath}${this.sdkVersions[this.preferredVersion].core}`,
                'Live2DCubismCore'
            );
            
            if (!coreLoaded) {
                throw new Error('Core SDK加载失败');
            }
            
            // 加载Framework
            const frameworkLoaded = await this.loadScript(
                `${this.localBasePath}${this.sdkVersions[this.preferredVersion].framework}`,
                'Live2DCubismFramework'
            );
            
            if (!frameworkLoaded) {
                throw new Error('Framework SDK加载失败');
            }
            
            this.loadedComponents.core = true;
            this.loadedComponents.framework = true;
            
            console.log('✅ 本地Cubism SDK加载成功');
            return true;
            
        } catch (error) {
            console.error('❌ 本地SDK加载失败:', error);
            return false;
        }
    }
    
    /**
     * 下载并设置SDK
     */
    async downloadAndSetupSDK() {
        console.log('🌐 尝试从CDN下载Cubism SDK...');
        
        try {
            // 创建本地目录
            await this.createLocalDirectories();
            
            // 下载Core SDK
            const coreSuccess = await this.downloadSDKComponent(
                this.cdnUrls.core,
                `./assets/cubism/${this.sdkVersions[this.preferredVersion].core}`
            );
            
            if (!coreSuccess) {
                throw new Error('Core SDK下载失败');
            }
            
            // 下载Framework SDK
            const frameworkSuccess = await this.downloadSDKComponent(
                this.cdnUrls.framework,
                `./assets/cubism/${this.sdkVersions[this.preferredVersion].framework}`
            );
            
            if (!frameworkSuccess) {
                throw new Error('Framework SDK下载失败');
            }
            
            console.log('✅ SDK下载完成，重新初始化...');
            this.localBasePath = './assets/cubism/';
            return await this.loadLocalSDK();
            
        } catch (error) {
            console.error('❌ SDK下载设置失败:', error);
            return await this.fallbackToCDN();
        }
    }
    
    /**
     * 创建本地目录
     */
    async createLocalDirectories() {
        // 在实际环境中，这里需要使用Node.js fs模块
        // 浏览器环境下我们只能通过动态创建来处理
        console.log('📁 准备本地SDK目录结构...');
    }
    
    /**
     * 下载SDK组件
     */
    async downloadSDKComponent(url, localPath) {
        try {
            console.log(`📥 下载: ${url}`);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const scriptContent = await response.text();
            
            // 在浏览器环境中，我们将内容保存到localStorage作为缓存
            localStorage.setItem(`cubism_sdk_${localPath}`, scriptContent);
            console.log(`✅ 已缓存: ${localPath}`);
            
            return true;
        } catch (error) {
            console.error(`❌ 下载失败 ${url}:`, error);
            return false;
        }
    }
    
    /**
     * 回退到CDN加载
     */
    async fallbackToCDN() {
        console.log('🔄 回退到CDN加载模式...');
        
        try {
            const coreLoaded = await this.loadScript(
                this.cdnUrls.core,
                'Live2DCubismCore'
            );
            
            if (!coreLoaded) {
                throw new Error('CDN Core加载失败');
            }
            
            const frameworkLoaded = await this.loadScript(
                this.cdnUrls.framework,
                'Live2DCubismFramework'
            );
            
            if (!frameworkLoaded) {
                throw new Error('CDN Framework加载失败');
            }
            
            this.loadedComponents.core = true;
            this.loadedComponents.framework = true;
            
            console.log('✅ CDN模式加载成功');
            return true;
            
        } catch (error) {
            console.error('❌ CDN加载也失败:', error);
            return false;
        }
    }
    
    /**
     * 加载脚本文件
     */
    async loadScript(src, globalVar) {
        return new Promise((resolve) => {
            // 首先检查是否已经加载
            if (globalVar && typeof window[globalVar] !== 'undefined') {
                console.log(`✅ ${globalVar} 已经加载`);
                resolve(true);
                return;
            }
            
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            
            script.onload = () => {
                console.log(`✅ 脚本加载成功: ${src}`);
                resolve(true);
            };
            
            script.onerror = (error) => {
                console.error(`❌ 脚本加载失败: ${src}`, error);
                resolve(false);
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * 获取SDK状态
     */
    getStatus() {
        return {
            loaded: this.loadedComponents.core && this.loadedComponents.framework,
            components: { ...this.loadedComponents },
            version: this.preferredVersion,
            basePath: this.localBasePath || 'CDN',
            sdkInfo: this.sdkVersions[this.preferredVersion]
        };
    }
    
    /**
     * 验证SDK完整性
     */
    async validateSDK() {
        const status = this.getStatus();
        
        if (!status.loaded) {
            return {
                valid: false,
                issues: ['SDK未完全加载']
            };
        }
        
        const issues = [];
        
        // 检查必要的全局对象
        if (typeof window.Live2DCubismCore === 'undefined') {
            issues.push('缺少Live2DCubismCore');
        }
        
        if (typeof window.Live2DCubismFramework === 'undefined') {
            issues.push('缺少Live2DCubismFramework');
        }
        
        // 检查版本信息
        try {
            if (window.Live2DCubismCore && window.Live2DCubismCore.Version) {
                const version = window.Live2DCubismCore.Version;
                console.log(`🔍 检测到Cubism Core版本: ${version}`);
            }
        } catch (error) {
            issues.push('无法获取版本信息');
        }
        
        return {
            valid: issues.length === 0,
            issues: issues,
            status: status
        };
    }
    
    /**
     * 清理和重置
     */
    async cleanup() {
        console.log('🧹 清理Cubism SDK管理器...');
        
        // 移除可能添加的script标签
        const scripts = document.querySelectorAll('script[src*="cubism"]');
        scripts.forEach(script => script.remove());
        
        // 重置状态
        this.loadedComponents = {
            core: false,
            framework: false
        };
        
        console.log('✅ 清理完成');
    }
}

// 创建全局实例
const cubismSDKManager = new CubismSDKManager();
window.cubismSDKManager = cubismSDKManager;

// 自动初始化
(async () => {
    console.log('🚀 Cubism SDK管理器准备就绪');
    console.log('使用方法:');
    console.log('- 初始化: await window.cubismSDKManager.initialize()');
    console.log('- 检查状态: window.cubismSDKManager.getStatus()');
    console.log('- 验证完整性: await window.cubismSDKManager.validateSDK()');
})();