# Linux PulseAudio原生模块

## 概述

这是一个用于在Linux系统上捕获系统音频的Node.js原生模块，使用PulseAudio API实现。

## 系统要求

- **操作系统**: Linux
- **Node.js**: >= 16.0.0
- **PulseAudio**: 已安装
- **开发库**: libpulse-dev, libpulse-simple-dev

## 安装依赖

### 1. 安装PulseAudio开发库

```bash
sudo apt-get update
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

### 2. 安装node-gyp

```bash
npm install -g node-gyp
```

## 编译模块

### 方法1：使用编译脚本（推荐）

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
./build.sh
```

### 方法2：手动编译

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
npm install
node-gyp configure
node-gyp build
```

## 使用方法

在`audio-handler.js`中导入并使用：

```javascript
import PulseAudioCapture from './native_modules/node-pulseaudio-capture/index.js';

// 创建捕获实例
const capture = new PulseAudioCapture({
    device: 'default',
    sampleRate: 44100,
    channels: 2
});

// 开始捕获
capture.start();

// 获取音频数据
capture.on('data', (buffer) => {
    // 处理音频数据
    console.log('Received audio data:', buffer.length, 'bytes');
});

// 停止捕获
capture.stop();
```

## 故障排除

### 编译错误：找不到pulse/pulseaudio.h

```bash
sudo apt-get install -y libpulse-dev libpulse-simple-dev
```

### 编译错误：找不到node-gyp

```bash
npm install -g node-gyp
```

### 运行时错误：模块未找到

确保编译产物在正确的位置：
- `build/Release/pulseaudio-capture.node`

## 测试

运行测试脚本：

```bash
node test.js
```

## 项目结构

```
node-pulseaudio-capture/
├── src/
│   └── pulseaudio-capture.cpp  # C++源代码
├── binding.gyp                  # node-gyp配置
├── package.json                 # NPM配置
├── index.js                     # JavaScript接口
├── test.js                      # 测试脚本
├── build.sh                     # 编译脚本
└── README.md                    # 本文档
```

## 许可证

MIT

## 作者

Angela AI Project