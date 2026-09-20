# Cubism SDK 集成使用指南

## 🎯 概述

我们已经成功集成了Live2D Cubism SDK的混合加载策略，包括本地部署和CDN备选方案。

## 📁 文件结构

```
apps/desktop-app/electron_app/
├── js/
│   ├── cubism-sdk-manager.js    # Cubism SDK管理器
│   ├── cubism-tester.js         # 集成测试工具
│   └── ... (其他JavaScript文件)
├── assets/
│   └── cubism/                  # 本地SDK存放目录
│       ├── live2dcubismcore.min.js
│       └── live2dcubismframework.min.js
└── index.html                   # 已更新引用
```

## 🚀 使用方法

### 1. 自动初始化

应用启动时会自动初始化Cubism SDK管理器。

### 2. 手动初始化

在浏览器控制台中执行：

```javascript
// 初始化SDK
await window.cubismSDKManager.initialize()

// 检查状态
window.cubismSDKManager.getStatus()

// 验证完整性
await window.cubismSDKManager.validateSDK()
```

### 3. 运行集成测试

```javascript
// 运行完整测试套件
await window.cubismTester.runAllTests()

// 导出测试报告
window.cubismTester.exportReport('json')
```

## 🔧 核心功能

### Cubism SDK管理器特性

1. **智能加载策略**
   - 优先使用本地SDK
   - CDN作为备选方案
   - 自动故障转移

2. **版本管理**
   - 支持多个SDK版本
   - 自动版本检测
   - 向下兼容

3. **性能优化**
   - 本地缓存机制
   - 并行加载优化
   - 内存管理

## 🧪 测试验证

### 在线测试命令

打开浏览器开发者工具(F12)，在控制台执行：

```javascript
// 1. 基础功能测试
console.log('SDK管理器状态:', window.cubismSDKManager.getStatus())

// 2. 完整集成测试
await window.cubismTester.runAllTests()

// 3. 性能基准测试
const startTime = performance.now()
await window.cubismSDKManager.initialize()
const loadTime = performance.now() - startTime
console.log(`SDK加载时间: ${loadTime.toFixed(2)}ms`)

// 4. 内存使用检查
if ('memory' in performance) {
  const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024
  console.log(`内存使用: ${memoryMB.toFixed(2)}MB`)
}
```

## 📊 预期结果

### 成功指标

- ✅ SDK管理器正确初始化
- ✅ 本地SDK文件可访问
- ✅ Core和Framework组件都加载成功
- ✅ 加载时间在合理范围内(<5秒)
- ✅ 内存使用在预期范围內(<300MB)

### 故障排除

如果遇到问题：

1. 检查网络连接(用于CDN备选)
2. 验证本地文件权限
3. 清理浏览器缓存
4. 重新启动应用

## 🔧 高级配置

### 自定义SDK路径

```javascript
window.cubismSDKManager.localPaths = [
  './custom-path/cubism/',
  '../alternative-location/',
]
```

### 设置首选版本

```javascript
window.cubismSDKManager.preferredVersion = '4.2'
```

### 强制使用CDN

```javascript
// 跳过本地检查，直接使用CDN
await window.cubismSDKManager.fallbackToCDN()
```

## 📈 性能监控

### 实时监控命令

```javascript
// 监控加载状态
setInterval(() => {
  const status = window.cubismSDKManager.getStatus()
  console.log('SDK状态:', status)
}, 5000)

// 内存泄漏检测
let lastMemory = 0
setInterval(() => {
  if ('memory' in performance) {
    const currentMemory = performance.memory.usedJSHeapSize
    const diff = currentMemory - lastMemory
    console.log(
      `内存变化: ${diff > 0 ? '+' : ''}${(diff / 1024 / 1024).toFixed(2)}MB`
    )
    lastMemory = currentMemory
  }
}, 10000)
```

## 🛠️ 维护建议

### 定期检查

- 每周运行一次完整测试
- 监控加载时间和内存使用
- 验证SDK版本兼容性

### 更新策略

- 定期检查官方SDK更新
- 测试新版本兼容性
- 备份当前工作版本

## 🆘 技术支持

如遇到问题，请提供以下信息：

1. 测试报告输出
2. 浏览器控制台错误信息
3. 系统硬件配置
4. 网络环境信息

---

_最后更新: 2026年2月6日_ _Angela AI Development Team_
