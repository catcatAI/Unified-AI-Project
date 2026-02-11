#!/bin/bash

# Linux PulseAudio原生模块编译脚本
# 用于Unified-AI-Project
# 改进版：包含依赖检查、自动安装建议、详细错误处理

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
LOG_FILE="${SCRIPT_DIR}/build.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"
}

# 清空日志
echo "" > "$LOG_FILE"

log "========================================="
log "  编译Linux PulseAudio原生模块"
log "========================================="

# 检查是否为Linux系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    log_error "此脚本仅适用于Linux系统"
    log_error "当前系统: $OSTYPE"
    exit 1
fi

log_success "系统检查通过: Linux"

# 检查Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js未安装"
    log "请访问 https://nodejs.org/ 下载安装"
    exit 1
fi

NODE_VERSION=$(node -v)
log_success "Node.js已安装: $NODE_VERSION"

# 检查npm
if ! command -v npm &> /dev/null; then
    log_error "npm未安装"
    exit 1
fi

NPM_VERSION=$(npm -v)
log_success "npm已安装: $NPM_VERSION"

# 检查node-gyp
if ! command -v node-gyp &> /dev/null; then
    log_warning "node-gyp未安装"
    log "正在安装node-gyp..."
    if npm install -g node-gyp >> "$LOG_FILE" 2>&1; then
        log_success "node-gyp安装成功"
    else
        log_error "node-gyp安装失败"
        log "请手动运行: sudo npm install -g node-gyp"
        exit 1
    fi
else
    NODE_GYP_VERSION=$(node-gyp -v)
    log_success "node-gyp已安装: $NODE_GYP_VERSION"
fi

# 检查PulseAudio开发库
MISSING_DEPS=()

if ! dpkg -l | grep -q "libpulse-dev"; then
    MISSING_DEPS+=("libpulse-dev")
fi

if ! dpkg -l | grep -q "libpulse-simple-dev"; then
    MISSING_DEPS+=("libpulse-simple-dev")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_error "缺少PulseAudio开发库: ${MISSING_DEPS[*]}"
    log ""
    log "请运行以下命令安装:"
    log "  sudo apt-get update"
    log "  sudo apt-get install -y ${MISSING_DEPS[*]}"
    log ""
    log "或者运行以下一键安装命令:"
    log "  sudo apt-get update && sudo apt-get install -y ${MISSING_DEPS[*]}"
    log ""
    
    # 询问是否自动安装
    read -p "是否自动安装依赖? (需要sudo权限) [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "正在安装依赖..."
        if sudo apt-get update >> "$LOG_FILE" 2>&1 && \
           sudo apt-get install -y ${MISSING_DEPS[*]} >> "$LOG_FILE" 2>&1; then
            log_success "依赖安装成功"
        else
            log_error "依赖安装失败"
            log "请查看日志: $LOG_FILE"
            exit 1
        fi
    else
        log "请手动安装依赖后重新运行此脚本"
        exit 1
    fi
else
    log_success "PulseAudio开发库已安装"
fi

# 检查是否安装了编译工具
if ! command -v g++ &> /dev/null; then
    log_warning "g++编译器未安装"
    log "正在安装build-essential..."
    if sudo apt-get install -y build-essential >> "$LOG_FILE" 2>&1; then
        log_success "build-essential安装成功"
    else
        log_error "build-essential安装失败"
        exit 1
    fi
else
    log_success "g++编译器已安装"
fi

# 进入模块目录
cd "$SCRIPT_DIR"

# 检查package.json
if [ ! -f "package.json" ]; then
    log_error "package.json不存在"
    exit 1
fi

# 安装npm依赖
log "正在安装npm依赖..."
if npm install >> "$LOG_FILE" 2>&1; then
    log_success "npm依赖安装成功"
else
    log_error "npm依赖安装失败"
    log "请查看日志: $LOG_FILE"
    exit 1
fi

# 清理之前的构建
log "清理之前的构建..."
rm -rf "$BUILD_DIR"
rm -rf node_modules/.build
log_success "清理完成"

# 配置构建
log "配置构建..."
if node-gyp configure >> "$LOG_FILE" 2>&1; then
    log_success "配置成功"
else
    log_error "配置失败"
    log "请查看日志: $LOG_FILE"
    log ""
    log "常见问题:"
    log "1. 确保已安装libpulse-dev和libpulse-simple-dev"
    log "2. 确保Node.js版本 >= 16.0.0"
    log "3. 尝试清理缓存: rm -rf ~/.node-gyp"
    exit 1
fi

# 构建
log "正在构建模块..."
BUILD_START=$(date +%s)
if node-gyp build >> "$LOG_FILE" 2>&1; then
    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))
    log_success "构建成功 (耗时: ${BUILD_TIME}秒)"
else
    log_error "构建失败"
    log "请查看日志: $LOG_FILE"
    log ""
    log "调试步骤:"
    log "1. 查看详细错误: cat $LOG_FILE"
    log "2. 尝试清理并重新构建:"
    log "   rm -rf build node_modules && npm install && node-gyp rebuild"
    log "3. 检查Node.js版本: node -v"
    log "4. 检查PulseAudio库: dpkg -l | grep pulse"
    exit 1
fi

# 检查构建结果
MODULE_PATH="${BUILD_DIR}/Release/pulseaudio-capture.node"
if [ -f "$MODULE_PATH" ]; then
    MODULE_SIZE=$(du -h "$MODULE_PATH" | cut -f1)
    log_success "✅ 模块编译成功！"
    log "   位置: $MODULE_PATH"
    log "   大小: $MODULE_SIZE"
    log ""
    log "验证模块..."
    
    # 尝试加载模块验证
    if node -e "try { require('./${MODULE_PATH}'); console.log('模块加载成功'); } catch(e) { console.error('模块加载失败:', e.message); process.exit(1); }" >> "$LOG_FILE" 2>&1; then
        log_success "模块验证成功"
    else
        log_warning "模块验证失败，但文件已生成"
        log "这可能是正常的，模块可能在运行时加载"
    fi
    
    log ""
    log "========================================="
    log "  编译完成！"
    log "========================================="
    log ""
    log "模块已准备就绪，可以在audio-handler.js中使用"
    log ""
    log "回退方案："
    log "如果模块加载失败，audio-handler.js会自动回退到Web Audio API"
    log "这意味着系统音频捕获功能可能受限，但应用仍可正常运行"
    log ""
    log "日志文件: $LOG_FILE"
    exit 0
else
    log_error "构建失败：未找到输出文件"
    log "预期位置: $MODULE_PATH"
    log ""
    log "请检查:"
    log "1. 构建目录内容: ls -la $BUILD_DIR/"
    log "2. 构建日志: cat $LOG_FILE"
    exit 1
fi