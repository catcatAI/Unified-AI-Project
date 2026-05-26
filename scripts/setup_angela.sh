#!/bin/bash
# Angela AI Quick Setup Script
# 快速設置和啟動腳本

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查系統要求
check_requirements() {
    log_info "檢查系統要求..."
    
    # 檢查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3.9+ 未安裝"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_success "Python 版本: $python_version"
    
    # 檢查Node.js
    if ! command -v node &> /dev/null; then
        log_warning "Node.js 未安裝，桌面應用將跳過"
        SKIP_DESKTOP=true
    else
        node_version=$(node --version)
        log_success "Node.js 版本: $node_version"
    fi
    
    # 檢查npm
    if ! command -v npm &> /dev/null; then
        log_warning "npm 未安裝，桌面應用將跳過"
        SKIP_DESKTOP=true
    else
        npm_version=$(npm --version)
        log_success "npm 版本: $npm_version"
    fi
    
    # 檢查Git
    if ! command -v git &> /dev/null; then
        log_error "Git 未安裝"
        exit 1
    fi
    
    git_version=$(git --version)
    log_success "Git 版本: $git_version"
}

# 安裝Python依賴
install_python_deps() {
    log_info "安裝Python依賴..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "找不到 requirements.txt"
        exit 1
    fi
    
    # 創建虛擬環境
    if [ ! -d "venv" ]; then
        log_info "創建Python虛擬環境..."
        python3 -m venv venv
    fi
    
    # 激活虛擬環境
    source venv/bin/activate
    
    # 升級pip
    pip install --upgrade pip
    
    # 安裝依賴
    pip install -r requirements.txt
    
    log_success "Python依賴安裝完成"
}

# 安裝桌面應用依賴
install_desktop_deps() {
    if [ "$SKIP_DESKTOP" = true ]; then
        log_warning "跳過桌面應用依賴安裝"
        return
    fi
    
    log_info "安裝桌面應用依賴..."
    
    cd apps/desktop-app/electron_app
    npm install
    cd ../../..
    
    # 構建原生模組
    log_info "構建原生音頻模組..."
    
    # Linux模組
    if command -v pkg-config &> /dev/null; then
        cd apps/desktop-app/native_modules/node-pulseaudio-capture
        npm install
        cd ../../..
    else
        log_warning "pkg-config未找到，跳過Linux音頻模組"
    fi
    
    log_success "桌面應用依賴安裝完成"
}

# 創建配置文件
setup_config() {
    log_info "設置配置文件..."
    
    # 複製環境配置模板
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "已創建 .env 配置文件"
    fi
    
    # 創建日誌目錄
    mkdir -p logs
    log_success "已創建日誌目錄"
    
    # 創建數據目錄
    mkdir -p data/{models,memories,cache,temp}
    log_success "已創建數據目錄"
}

# 啟動服務
start_services() {
    log_info "啟動Angela AI服務..."
    
    # 激活虛擬環境
    source venv/bin/activate
    
    # 設置測試模式
    export ANGELA_TESTING=true
    
    # 啟動後端
    log_info "啟動後端服務..."
    cd apps/backend
    python start_monitor.py &
    BACKEND_PID=$!
    cd ../..
    
    # 等待後端啟動
    sleep 3
    
    # 啟動桌面應用
    if [ "$SKIP_DESKTOP" != true ]; then
        log_info "啟動桌面應用..."
        cd apps/desktop-app/electron_app
        npm start &
        DESKTOP_PID=$!
        cd ../../..
    fi
    
    log_success "Angela AI 已啟動！"
    log_info "後端進程PID: $BACKEND_PID"
    if [ "$SKIP_DESKTOP" != true ]; then
        log_info "桌面應用進程PID: $DESKTOP_PID"
    fi
    
    # 保存PID以便清理
    echo $BACKEND_PID > .backend.pid
    if [ "$SKIP_DESKTOP" != true ]; then
        echo $DESKTOP_PID > .desktop.pid
    fi
}

# 停止服務
stop_services() {
    log_info "停止Angela AI服務..."
    
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
        log_success "後端服務已停止"
    fi
    
    if [ -f ".desktop.pid" ]; then
        DESKTOP_PID=$(cat .desktop.pid)
        kill $DESKTOP_PID 2>/dev/null || true
        rm .desktop.pid
        log_success "桌面應用已停止"
    fi
}

# 顯示幫助信息
show_help() {
    echo "Angela AI 快速設置腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  start     啟動Angela AI服務"
    echo "  stop      停止Angela AI服務"
    echo "  restart   重啟Angela AI服務"
    echo "  setup     設置環境和依賴"
    echo "  help      顯示此幫助信息"
    echo ""
}

# 主函數
main() {
    case "${1:-setup}" in
        "setup")
            log_info "開始設置Angela AI..."
            check_requirements
            install_python_deps
            install_desktop_deps
            setup_config
            log_success "Angela AI設置完成！運行 '$0 start' 啟動服務"
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_services
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
}

# 捕獲信號
trap 'stop_services; exit 1' INT TERM

# 執行主函數
main "$@"