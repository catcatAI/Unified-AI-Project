# Native Audio Modules 编译指南

## 概述

Angela AI 支持三个原生音频捕获模块，用于在不同平台上捕获系统音频：

| 模块 | 平台 | 说明 |
|------|------|------|
| `node-wasapi-capture` | Windows | 使用 WASAPI (Windows Audio Session API) |
| `node-pulseaudio-capture` | Linux | 使用 PulseAudio |
| `node-coreaudio-capture` | macOS | 使用 CoreAudio |

## 验证状态

运行验证脚本检查当前状态：

```bash
python3 verify_native_audio_modules.py
```

## Linux (PulseAudio) 编译指南

### 1. 安装依赖

```bash
sudo apt-get update
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

### 2. 编译模块

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
bash build.sh
```

### 3. 验证编译

编译成功后，应该看到：
```
✅ 模块编译成功！
   位置: build/Release/pulseaudio-capture.node
   大小: XXX KB
```

### 4. 回退方案

如果编译失败或模块加载失败，`audio-handler.js` 会自动回退到 Web Audio API。

## macOS (CoreAudio) 编译指南

### 1. 安装 Xcode Command Line Tools

```bash
xcode-select --install
```

### 2. 编译模块

```bash
cd apps/desktop-app/native_modules/node-coreaudio-capture
bash build.sh
```

### 3. 验证编译

编译成功后，应该看到：
```
✅ 模块编译成功！
   位置: build/Release/coreaudio-capture.node
   大小: XXX KB
```

## Windows (WASAPI) 编译指南

### 1. 安装 Visual Studio Build Tools

下载并安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)，选择：
- Desktop development with C++
- Windows 10 SDK

### 2. 安装 node-gyp

```bash
npm install -g node-gyp
```

### 3. 编译模块

```cmd
cd apps\desktop-app\native_modules\node-wasapi-capture
build.bat
```

### 4. 验证编译

编译成功后，应该看到：
```
✅ 模块编译成功！
   位置: build\Release\wasapi-capture.node
   大小: XXX KB
```

## 常见问题

### Linux: "libpulse-dev not found"

**解决方案**:
```bash
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

### macOS: "xcrun: error: invalid active developer path"

**解决方案**:
```bash
xcode-select --install
```

### Windows: "MSBuild not found"

**解决方案**:
1. 安装 Visual Studio Build Tools
2. 确保已选择 "Desktop development with C++"
3. 重启命令行

### 所有平台: "node-gyp build failed"

**解决方案**:
1. 清理构建目录：
   ```bash
   rm -rf build node_modules
   npm install
   node-gyp rebuild
   ```
2. 检查 Node.js 版本（需要 >= 16.0.0）
3. 检查编译工具是否正确安装

## 回退方案

如果原生模块编译失败或加载失败，系统会自动回退到 Web Audio API：

**影响**:
- 系统音频捕获功能受限
- 应用仍可正常运行
- 某些音频相关功能可能不可用

**验证回退**:
在应用启动日志中查找：
```
[AudioHandler] Native module not available, using Web Audio API fallback
```

## 自动化脚本

### 一键验证

```bash
python3 verify_native_audio_modules.py
```

### 一键编译（Linux）

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
bash build.sh
```

## 技术细节

### 模块结构

每个原生模块包含：
- `src/` - C++ 源代码
- `binding.gyp` - 构建配置
- `package.json` - NPM 包配置
- `build.sh` / `build.bat` - 构建脚本
- `index.js` - JavaScript 接口

### 构建流程

1. `node-gyp configure` - 配置构建
2. `node-gyp build` - 编译模块
3. 生成 `.node` 文件 - 可在 Node.js 中加载的原生模块

### 加载机制

`audio-handler.js` 中的加载逻辑：

```javascript
try {
  const nativeModule = require('./native_modules/XXX-capture');
  // 使用原生模块
} catch (e) {
  console.warn('[AudioHandler] Native module not available, using Web Audio API fallback');
  // 使用 Web Audio API 回退
}
```

## 总结

- **必需**: 原生模块提供更好的音频捕获性能
- **可选**: 如果编译失败，系统会自动回退到 Web Audio API
- **推荐**: 在目标平台上编译对应的原生模块以获得最佳体验

---

**文档更新时间**: 2026-02-11
**版本**: 1.0.0