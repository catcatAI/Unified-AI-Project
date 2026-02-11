# PulseAudio原生模块编译指南

## 快速开始

### 一键编译（推荐）

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
./build.sh
```

此脚本会：
1. ✅ 检查系统环境（Node.js, npm, node-gyp）
2. ✅ 检查并安装PulseAudio开发库
3. ✅ 清理之前的构建
4. ✅ 编译模块
5. ✅ 验证编译结果

## 详细步骤

### 1. 系统要求检查

```bash
# 检查Node.js版本（需要 >= 16.0.0）
node -v

# 检查npm版本
npm -v

# 检查PulseAudio
pulseaudio --version

# 检查开发库
dpkg -l | grep libpulse-dev
```

### 2. 安装依赖

#### 安装PulseAudio开发库

```bash
sudo apt-get update
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

#### 安装构建工具

```bash
sudo apt-get install -y build-essential
```

#### 安装node-gyp

```bash
npm install -g node-gyp
```

### 3. 编译模块

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture

# 安装npm依赖
npm install

# 配置构建
node-gyp configure

# 编译
node-gyp build
```

## 常见问题

### 问题1：找不到pulse/pulseaudio.h

**错误信息**：
```
fatal error: pulse/pulseaudio.h: No such file or directory
```

**解决方案**：
```bash
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

### 问题2：node-gyp未安装

**错误信息**：
```
sh: node-gyp: command not found
```

**解决方案**：
```bash
npm install -g node-gyp
```

### 问题3：编译失败，缺少Python

**错误信息**：
```
gyp: Call to 'python' failed
```

**解决方案**：
```bash
# 检查Python版本
python3 --version

# 确保Python 3可用
sudo apt-get install -y python3 python3-pip
```

### 问题4：权限问题

**错误信息**：
```
EACCES: permission denied
```

**解决方案**：
```bash
# 不要使用sudo运行npm
# 确保目录权限正确
chmod -R 755 .
```

### 问题5：缓存问题

**错误信息**：
```
Previous build artifacts detected
```

**解决方案**：
```bash
# 清理构建缓存
rm -rf build node_modules
rm -rf ~/.node-gyp

# 重新安装和编译
npm install
node-gyp rebuild
```

## 验证编译

### 检查编译产物

```bash
ls -lh build/Release/pulseaudio-capture.node
```

应该看到一个.so文件（例如：~2MB）

### 运行测试

```bash
node test.js
```

### 在应用中测试

1. 确保模块已编译
2. 启动Electron应用
3. 检查控制台日志，确认模块加载成功

## 回退方案

如果模块编译失败或加载失败，应用会自动回退到Web Audio API：

```javascript
// audio-handler.js中的回退逻辑
try {
    const module = await this._loadNativeModule();
    if (module) {
        this.systemAudioCapture = new module();
        console.log('Native system audio capture module loaded');
    }
} catch (error) {
    console.warn('Failed to load native audio module:', error.message);
    // 回退到Web Audio API
}
```

## 平台差异

### Linux (本模块)
- 使用PulseAudio API
- 编译产物：`pulseaudio-capture.node`

### Windows
- 使用WASAPI
- 模块位置：`node-wasapi-capture/`

### macOS
- 使用CoreAudio
- 模块位置：`node-coreaudio-capture/`

## 性能优化

### 1. 调整缓冲区大小

在`pulseaudio-capture.cpp`中修改：

```cpp
bufferAttr.fragsize = pa_usec_to_bytes(20000, &sampleSpec);  // 20ms
```

### 2. 调整采样率

在构造函数中修改：

```cpp
sampleSpec.rate = 48000;  // 默认48000Hz
```

### 3. 禁用不必要的特性

如果不需要某些功能，可以在编译时通过宏定义禁用：

```javascript
// 在binding.gyp中添加
"defines": [
    "NAPI_DISABLE_CPP_EXCEPTIONS",
    "DISABLE_ANALYZER"  // 自定义宏
]
```

## 调试

### 启用详细日志

```bash
# 设置环境变量
export NODE_GYP_DEBUG=1

# 重新编译
node-gyp rebuild
```

### 查看编译日志

```bash
cat build.log
```

### 使用GDB调试

```bash
gdb node
(gdb) run test.js
```

## 贡献

如果发现问题或有改进建议，请：

1. 检查现有issue
2. 创建新issue并附上：
   - 系统信息（`uname -a`）
   - Node.js版本（`node -v`）
   - 错误日志
   - 重现步骤

## 相关资源

- [PulseAudio文档](https://www.freedesktop.org/wiki/Software/PulseAudio/)
- [node-gyp文档](https://github.com/nodejs/node-gyp)
- [Node.js N-API](https://nodejs.org/api/n-api.html)