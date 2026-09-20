/**
 * Angela AI - Hardware Detection Enhancement Patch
 *
 * 运行时补丁，增强现有的硬件检测功能
 */

;(function () {
  'use strict'

  // 等待应用初始化完成
  function waitForAppInitialization() {
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (window.angelaApp && window.angelaApp.hardwareDetector) {
          clearInterval(checkInterval)
          resolve(window.angelaApp)
        }
      }, 500)

      // 超时保护
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve(null)
      }, 10000)
    })
  }

  // 增强硬件检测器原型
  function enhanceHardwareDetector(detector) {
    if (!detector) return

    // 保存原始方法
    const originalDetect = detector.detect.bind(detector)
    const originalAssessCapabilities = detector._assessCapabilities.bind(detector)

    // 增强检测方法
    detector.detect = async function () {
      console.log('🔍 Running enhanced hardware detection...')

      try {
        // 执行原始检测
        const profile = await originalDetect()

        // 应用增强分析
        const enhancedProfile = this._applyEnhancedAnalysis(profile)

        console.log('✅ Enhanced hardware detection completed:', enhancedProfile)
        return enhancedProfile
      } catch (error) {
        console.error('❌ Enhanced hardware detection failed:', error)
        // 回退到原始检测
        return await originalDetect()
      }
    }

    // 增强能力评估
    detector._assessCapabilities = function (profile) {
      const capabilities = originalAssessCapabilities(profile)

      // 应用核显优化
      return this._applyIntegratedGraphicsOptimization(capabilities, profile)
    }

    // 新增增强分析方法
    detector._applyEnhancedAnalysis = function (profile) {
      // 增强GPU信息分析
      if (profile.gpu_info) {
        profile.gpu_info.enhanced_type = this._classifyGPUMorePrecisely(profile.gpu_info.renderer)
        profile.gpu_info.performance_score = this._calculatePerformanceScore(profile)
        profile.gpu_info.optimization_suggestions = this._getOptimizationSuggestions(profile)
      }

      return profile
    }

    // 精确的GPU分类
    detector._classifyGPUMorePrecisely = function (renderer) {
      const r = (renderer || '').toUpperCase()

      // Intel核显精确分类
      if (r.includes('INTEL')) {
        if (r.includes('ARC')) return 'intel_arc_discrete'
        if (r.includes('IRIS XE')) return 'intel_iris_xe_integrated'
        if (r.includes('IRIS')) return 'intel_iris_integrated'
        if (r.includes('UHD')) return 'intel_uhd_integrated'
        if (r.includes('HD')) return 'intel_hd_integrated'
        return 'intel_unknown'
      }

      // AMD核显精确分类
      if (r.includes('AMD') || r.includes('ATI') || r.includes('RADEON')) {
        if (r.includes('VEGA')) return 'amd_vega_integrated'
        if (r.includes('RDNA')) return 'amd_rdna_integrated'
        if (r.includes('GCN')) return 'amd_gcn_integrated'
        return 'amd_unknown'
      }

      return 'unknown'
    }

    // 性能评分计算
    detector._calculatePerformanceScore = function (profile) {
      let score = 0

      // RAM贡献
      if (profile.ram_gb >= 32) score += 40
      else if (profile.ram_gb >= 16) score += 30
      else if (profile.ram_gb >= 8) score += 20
      else if (profile.ram_gb >= 4) score += 10

      // GPU贡献
      const gpuTypes = {
        intel_arc_discrete: 35,
        intel_iris_xe_integrated: 25,
        intel_iris_integrated: 20,
        intel_uhd_integrated: 15,
        intel_hd_integrated: 10,
        amd_vega_integrated: 30,
        amd_rdna_integrated: 28,
        amd_gcn_integrated: 22,
      }

      score += gpuTypes[profile.gpu_info?.enhanced_type] || 10

      // CPU贡献
      if (profile.cpu_cores >= 8) score += 20
      else if (profile.cpu_cores >= 4) score += 15
      else score += 10

      return Math.min(score, 100) // 最高100分
    }

    // 优化建议生成
    detector._getOptimizationSuggestions = function (profile) {
      const suggestions = []
      const gpuType = profile.gpu_info?.enhanced_type

      // 核显优化建议
      if (gpuType?.includes('intel')) {
        suggestions.push('启用Intel核显优化模式')
        suggestions.push('适当降低渲染分辨率以提升流畅度')
        suggestions.push('优先使用2D/2.5D壁纸模式')
      } else if (gpuType?.includes('amd')) {
        suggestions.push('启用AMD核显计算优化')
        suggestions.push('平衡性能与特效数量')
        suggestions.push('考虑开启计算着色器加速')
      }

      // 内存相关建议
      if (profile.ram_gb < 8) {
        suggestions.push('系统内存较低，建议减少同时运行的应用')
      } else if (profile.ram_gb >= 16) {
        suggestions.push('内存充足，可启用高质量渲染')
      }

      return suggestions
    }

    // 核显优化
    detector._applyIntegratedGraphicsOptimization = function (capabilities, profile) {
      const gpuType = profile.gpu_info?.enhanced_type

      if (gpuType?.includes('intel') || gpuType?.includes('amd')) {
        // 为核显调整设置
        capabilities.wallpaper_mode = this._optimizeWallpaperModeForIntegrated(
          capabilities.wallpaper_mode,
          gpuType
        )
        capabilities.render_quality = this._optimizeRenderQualityForIntegrated(
          capabilities.render_quality,
          gpuType
        )
        capabilities.effects = this._optimizeEffectsForIntegrated(capabilities.effects, gpuType)
        capabilities.battery_optimized = profile.device_type === 'laptop'
      }

      return capabilities
    }

    detector._optimizeWallpaperModeForIntegrated = function (currentMode, gpuType) {
      // Intel核显推荐2D/2.5D，避免3D
      if (gpuType.includes('intel')) {
        return currentMode === '3D' ? '2.5D' : currentMode
      }
      // AMD核显可以支持更好的2.5D
      if (gpuType.includes('amd')) {
        return currentMode
      }
      return currentMode
    }

    detector._optimizeRenderQualityForIntegrated = function (currentQuality, gpuType) {
      // 为核显适当降低质量设置
      if (currentQuality.resolution === '4K') {
        return { ...currentQuality, resolution: '1440p' }
      }
      if (currentQuality.resolution === '2160p') {
        return { ...currentQuality, resolution: '1080p' }
      }
      return currentQuality
    }

    detector._optimizeEffectsForIntegrated = function (currentEffects, gpuType) {
      // 核显限制特效数量
      const maxEffects = gpuType.includes('intel') ? 3 : 4
      return currentEffects.slice(0, maxEffects)
    }

    console.log('✅ Hardware detector enhanced successfully')
    return detector
  }

  // 主初始化函数
  async function initialize() {
    console.log('🚀 Initializing hardware detection enhancement...')

    // 等待应用初始化
    const app = await waitForAppInitialization()

    if (app && app.hardwareDetector) {
      // 增强现有的硬件检测器
      enhanceHardwareDetector(app.hardwareDetector)

      // 如果已经完成初始化，重新检测硬件
      if (app.isInitialized) {
        console.log('🔄 Re-running enhanced hardware detection...')
        const newProfile = await app.hardwareDetector.detect()
        app.hardwareDetector.profile = newProfile
        app.hardwareDetector.capabilities = app.hardwareDetector._assessCapabilities(newProfile)
        console.log('✅ Hardware profile updated with enhancements:', newProfile)
      }
    } else {
      console.warn('⚠️ Angela app not found or not initialized yet')
    }
  }

  // 页面加载完成后执行
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize)
  } else {
    // DOM已加载，直接执行
    setTimeout(initialize, 1000)
  }

  // 导出增强工具供调试使用
  window.HardwareEnhancementTools = {
    enhanceDetector: enhanceHardwareDetector,
    waitForApp: waitForAppInitialization,
  }
})()
