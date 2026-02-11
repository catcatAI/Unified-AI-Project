#!/bin/bash

# Linux PulseAudio原生模块编译脚本
# 用于Unified-AI-Project

set -e  # 遇到错误立即退出

echo "========================================="
echo "  编译Linux PulseAudio原生模块"
echo "========================================="

# 进入模块目录
cd "$(dirname "$0")"

# 检查node-gyp
if ! command -v node-gyp &> /dev/null; then
    echo "❌ node-gyp未安装"
    echo "请运行: npm install -g node-gyp"
    exit 1
fi

echo "✅ node-gyp已安装"

# 检查PulseAudio开发库
if ! dpkg -l | grep -q libpulse-dev; then
    echo "❌ libpulse-dev未安装"
    echo "请运行: sudo apt-get install -y libpulse-dev libpulse-simple-dev"
    exit 1
fi

echo "✅ PulseAudio开发库已安装"

# 清理之前的构建
echo "🧹 清理之前的构建..."
rm -rf build node_modules

# 配置
echo "⚙️  配置构建..."
node-gyp configure

# 构建
echo "🔨 构建模块..."
node-gyp build

# 检查构建结果
if [ -f "build/Release/pulseaudio-capture.node" ]; then
    echo "✅ 构建成功！"
    echo "📦 模块位置: build/Release/pulseaudio-capture.node"
    echo ""
    echo "要使用此模块，请在audio-handler.js中添加："
    echo "import PulseAudioCapture from './native_modules/node-pulseaudio-capture/index.js';"
else
    echo "❌ 构建失败！"
    exit 1
fi