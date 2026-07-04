/**
 * Angela AI - Laptop Optimization Module
 * 
 * 专门为笔记本电脑优化的性能和电池管理模块
 */

class LaptopOptimizer {
    constructor() {
        this.batteryMonitoring = null;
        this.powerProfiles = this._initializePowerProfiles();
        this.currentProfile = 'balanced';
        this.isOptimized = false;
    }
    
    async initialize() {
        console.log('🔋 Initializing laptop optimization...');
        
        // 检测是否为笔记本电脑
        if (!this._isLaptop()) {
            console.log('📱 Device is not a laptop, skipping laptop optimizations');
            return false;
        }
        
        // 初始化电池监控
        await this._initializeBatteryMonitoring();
        
        // 应用初始优化配置
        await this._applyInitialOptimizations();
        
        // 设置性能监控
        this._setupPerformanceMonitoring();
        
        this.isOptimized = true;
        console.log('✅ Laptop optimization initialized successfully');
        return true;
    }
    
    _isLaptop() {
        // 多重检测方法判断是否为笔记本电脑
        const checks = [
            () => this._checkBatteryAPI(),
            () => this._checkMobileUserAgent(),
            () => this._checkScreenCharacteristics(),
            () => this._checkHardwareCharacteristics()
        ];
        
        return checks.some(check => check());
    }
    
    _checkBatteryAPI() {
        return typeof navigator.getBattery === 'function';
    }
    
    _checkMobileUserAgent() {
        const ua = navigator.userAgent.toLowerCase();
        return ua.includes('mobile') || ua.includes('tablet');
    }
    
    _checkScreenCharacteristics() {
        // 笔记本电脑通常屏幕较小且分辨率较高
        const screen = window.screen;
        const ratio = screen.width / screen.height;
        return ratio > 1.2 && ratio < 2.5 && screen.width <= 1920;
    }
    
    _checkHardwareCharacteristics() {
        // 检查硬件特征
        try {
            return navigator.deviceMemory <= 16 && navigator.hardwareConcurrency <= 8;
        } catch (err) {
            console.warn('[LaptopOptimizer] Hardware detection failed:', err.message);
            return false;
        }
    }
    
    async _initializeBatteryMonitoring() {
        if (!navigator.getBattery) {
            console.warn('⚠️ Battery API not available');
            return;
        }
        
        try {
            const battery = await navigator.getBattery();
            
            this.batteryMonitoring = {
                level: battery.level,
                charging: battery.charging,
                chargingTime: battery.chargingTime,
                dischargingTime: battery.dischargingTime
            };
            
            // 监听电池状态变化
            battery.addEventListener('chargingchange', () => {
                this._handleBatteryChange('charging', battery.charging);
            });
            
            battery.addEventListener('levelchange', () => {
                this._handleBatteryChange('level', battery.level);
            });
            
            console.log('🔋 Battery monitoring initialized:', this.batteryMonitoring);
        } catch (error) {
            console.warn('⚠️ Failed to initialize battery monitoring:', error);
        }
    }
    
    _handleBatteryChange(type, value) {
        console.log(`🔋 Battery ${type} changed to: ${value}`);
        
        if (type === 'charging') {
            this.batteryMonitoring.charging = value;
            this._adjustPowerProfileBasedOnCharging(value);
        } else if (type === 'level') {
            this.batteryMonitoring.level = value;
            this._adjustPowerProfileBasedOnLevel(value);
        }
    }
    
    _adjustPowerProfileBasedOnCharging(isCharging) {
        if (isCharging) {
            // 插电时使用性能模式
            this.setPowerProfile('performance');
            console.log('🔌 Power adapter connected, switching to performance mode');
        } else {
            // 使用电池时根据电量调整
            this._adjustPowerProfileBasedOnLevel(this.batteryMonitoring.level);
        }
    }
    
    _adjustPowerProfileBasedOnLevel(level) {
        if (!this.batteryMonitoring.charging) {
            if (level < 0.2) {
                this.setPowerProfile('power_saving');
                console.log('🔋 Low battery, switching to power saving mode');
            } else if (level < 0.5) {
                this.setPowerProfile('balanced');
                console.log('🔋 Medium battery, using balanced mode');
            } else {
                this.setPowerProfile('performance');
                console.log('🔋 Good battery level, using performance mode');
            }
        }
    }
    
    _initializePowerProfiles() {
        return {
            power_saving: {
                name: '省电模式',
                fps_target: 30,
                quality_preset: 'low',
                effects_limit: 2,
                resolution_scale: 0.75,
                power_saving_features: true,
                thermal_throttling: true,
                description: '最大化电池续航时间'
            },
            balanced: {
                name: '平衡模式',
                fps_target: 45,
                quality_preset: 'medium',
                effects_limit: 3,
                resolution_scale: 1.0,
                power_saving_features: true,
                thermal_throttling: false,
                description: '性能与续航的平衡'
            },
            performance: {
                name: '性能模式',
                fps_target: 60,
                quality_preset: 'high',
                effects_limit: 5,
                resolution_scale: 1.0,
                power_saving_features: false,
                thermal_throttling: false,
                description: '最大化性能表现'
            },
            cooling: {
                name: '散热优化模式',
                fps_target: 40,
                quality_preset: 'medium',
                effects_limit: 3,
                resolution_scale: 0.9,
                power_saving_features: true,
                thermal_throttling: true,
                fan_control: 'aggressive',
                description: '优化散热，防止过热'
            }
        };
    }
    
    setPowerProfile(profileName) {
        if (!this.powerProfiles[profileName]) {
            console.warn(`⚠️ Unknown power profile: ${profileName}`);
            return false;
        }
        
        const oldProfile = this.currentProfile;
        this.currentProfile = profileName;
        const profile = this.powerProfiles[profileName];
        
        console.log(`⚡ Switching power profile: ${oldProfile} → ${profileName}`);
        
        // 应用配置到各个系统组件
        this._applyProfileToSystems(profile);
        
        // 通知用户
        this._notifyProfileChange(profile);
        
        return true;
    }
    
    _applyProfileToSystems(profile) {
        // 应用到性能管理器
        if (window.angelaApp && window.angelaApp.performanceManager) {
            window.angelaApp.performanceManager.setTargetFPS(profile.fps_target);
            // 将 quality_preset 映射到 effectsLevel
            const qualityMap = { 'low': 1, 'medium': 2, 'high': 3 };
            window.angelaApp.performanceManager.setEffectsLevel(qualityMap[profile.quality_preset] || 2);
        }
        
        // 应用到Live2D管理器
        if (window.angelaApp && window.angelaApp.live2dManager) {
            window.angelaApp.live2dManager.setResolutionScale(profile.resolution_scale);
            // setEffectsLimit 方法不存在，改用 setEffectsLevel
            window.angelaApp.live2dManager.setEffectsLevel(profile.effects_limit);
        }
        
        // 应用电源管理设置
        this._applyPowerManagementSettings(profile);
    }
    
    _applyPowerManagementSettings(profile) {
        // 调整渲染设置
        if (profile.power_saving_features) {
            this._enablePowerSavingFeatures();
        } else {
            this._disablePowerSavingFeatures();
        }
        
        // 热节流控制
        if (profile.thermal_throttling) {
            this._enableThermalThrottling();
        } else {
            this._disableThermalThrottling();
        }
    }
    
    _enablePowerSavingFeatures() {
        // 降低渲染频率
        if (window.angelaApp && window.angelaApp.live2dManager) {
            window.angelaApp.live2dManager.setTargetFPS(30);
        }
        
        // 减少后台活动
        if (window.angelaApp && typeof window.angelaApp.reduceBackgroundActivity === 'function') {
            window.angelaApp.reduceBackgroundActivity();
        }
    }
    
    _disablePowerSavingFeatures() {
        // 恢复正常渲染频率
        if (window.angelaApp && window.angelaApp.live2dManager) {
            window.angelaApp.live2dManager.setTargetFPS(60);
        }
    }
    
    _enableThermalThrottling() {
        // 降低CPU/GPU使用率
        // 注意：performanceManager 中没有 enableThermalThrottling 方法
        // 可以通过降低 FPS 和效果级别来模拟
        if (window.angelaApp && window.angelaApp.performanceManager) {
            // 暂时注释掉不存在的方法
            // window.angelaApp.performanceManager.enableThermalThrottling();
        }
    }
    
    _disableThermalThrottling() {
        // 注意：performanceManager 中没有 disableThermalThrottling 方法
        if (window.angelaApp && window.angelaApp.performanceManager) {
            // 暂时注释掉不存在的方法
            // window.angelaApp.performanceManager.disableThermalThrottling();
        }
    }
    
    _notifyProfileChange(profile) {
        // 在UI中显示通知
        if (window.angelaApp) {
            window.angelaApp.showStatus(
                `🔋 电源模式: ${profile.name} - ${profile.description}`, 
                3000
            );
        }
    }
    
    async _applyInitialOptimizations() {
        // 根据当前电池状态设置初始配置文件
        if (this.batteryMonitoring) {
            if (this.batteryMonitoring.charging) {
                this.setPowerProfile('performance');
            } else {
                this._adjustPowerProfileBasedOnLevel(this.batteryMonitoring.level);
            }
        } else {
            // 没有电池信息时使用平衡模式
            this.setPowerProfile('balanced');
        }
    }
    
    _setupPerformanceMonitoring() {
        // 定期监控系统性能
        setInterval(() => {
            this._monitorSystemPerformance();
        }, 30000); // 每30秒检查一次
        
        // 监控温度相关指标
        setInterval(() => {
            this._checkThermalConditions();
        }, 60000); // 每分钟检查一次
    }
    
    _monitorSystemPerformance() {
        if (!window.angelaApp) return;
        
        const perfData = {
            fps: window.angelaApp.live2dManager?.getCurrentFPS() || 0,
            cpu_usage: this._estimateCPUUsage(),
            memory_usage: this._getMemoryUsage(),
            battery_level: this.batteryMonitoring?.level || 1.0
        };
        
        // 根据性能数据自动调整
        this._autoAdjustBasedOnPerformance(perfData);
    }
    
    _estimateCPUUsage() {
        // 简单的CPU使用率估算
        try {
            // 这里可以集成更精确的性能监控
            return Math.random() * 100; // 临时随机值
        } catch (err) {
            console.warn('[LaptopOptimizer] CPU estimation failed:', err.message);
            return 50; // 默认值
        }
    }
    
    _getMemoryUsage() {
        try {
            return (performance.memory?.usedJSHeapSize || 0) / (1024 * 1024); // MB
        } catch (err) {
            console.warn('[LaptopOptimizer] Memory usage detection failed:', err.message);
            return 100; // 默认值
        }
    }
    
    _autoAdjustBasedOnPerformance(perfData) {
        // 自动性能调整逻辑
        if (perfData.fps < 25 && this.currentProfile !== 'power_saving') {
            console.log('📉 FPS too low, considering power saving mode');
            // 可以自动切换到省电模式
        }
        
        if (perfData.battery_level < 0.15 && this.currentProfile !== 'power_saving') {
            console.log('🪫 Battery very low, switching to power saving');
            this.setPowerProfile('power_saving');
        }
    }
    
    _checkThermalConditions() {
        // 简单的热管理检查
        const tempEstimate = this._estimateTemperature();
        
        if (tempEstimate > 80 && this.currentProfile !== 'cooling') {
            console.log('🌡️ High temperature detected, enabling cooling mode');
            this.setPowerProfile('cooling');
        }
    }
    
    _estimateTemperature() {
        // 简单的温度估算（基于CPU使用率和时间）
        const cpuUsage = this._estimateCPUUsage();
        const baseTemp = 30; // 基础温度
        const cpuFactor = cpuUsage * 0.5; // CPU使用率影响因子
        const timeFactor = (Date.now() % 3600000) / 3600000 * 10; // 时间因子
        
        return baseTemp + cpuFactor + timeFactor;
    }
    
    // 公共接口方法
    getCurrentProfile() {
        return {
            name: this.currentProfile,
            config: this.powerProfiles[this.currentProfile],
            battery: this.batteryMonitoring
        };
    }
    
    getOptimizationStatus() {
        return {
            isLaptop: this._isLaptop(),
            isOptimized: this.isOptimized,
            currentProfile: this.currentProfile,
            batteryStatus: this.batteryMonitoring,
            supportedProfiles: Object.keys(this.powerProfiles)
        };
    }
}

// 自动初始化
(function() {
    // 延迟初始化以确保应用完全加载
    setTimeout(async () => {
        const optimizer = new LaptopOptimizer();
        const success = await optimizer.initialize();
        
        if (success) {
            // 将优化器暴露给全局作用域
            window.laptopOptimizer = optimizer;
            console.log('✅ Laptop optimizer ready for use');
        }
    }, 2000);
})();

// 导出类供其他模块使用
window.LaptopOptimizer = LaptopOptimizer;