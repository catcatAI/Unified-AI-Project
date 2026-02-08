#!/bin/bash
# Angela AI 全自動安裝和啟動腳本
# 自動處理所有前置條件、依賴安裝和系統啟動

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 檢測操作系統
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            PKG_MANAGER="apt"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            PKG_MANAGER="yum"
        elif [ -f /etc/arch-release ]; then
            OS="arch"
            PKG_MANAGER="pacman"
        else
            OS="linux"
            PKG_MANAGER="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        PKG_MANAGER="choco"
    else
        OS="unknown"
        PKG_MANAGER="unknown"
    fi
    
    log_info "檢測到操作系統: $OS (包管理器: $PKG_MANAGER)"
}

# 安裝系統依賴
install_system_deps() {
    log_step "安裝系統依賴..."
    
    case $OS in
        "debian")
            log_info "更新系統包列表..."
            sudo apt update || { log_error "無法更新包列表"; exit 1; }
            
            log_info "安裝基礎依賴..."
            sudo apt install -y \
                curl \
                wget \
                git \
                build-essential \
                python3 \
                python3-venv \
                python3-pip \
                nodejs \
                npm \
                pkg-config \
                libpulse-dev \
                libasound2-dev \
                libx11-dev \
                libxi-dev \
                libgl1-mesa-dev \
                libglu1-mesa-dev \
                libxrandr-dev \
                libxinerama-dev \
                libxcursor-dev \
                libxcomposite-dev \
                libxtst-dev \
                libssl-dev \
                libffi-dev \
                libbz2-dev \
                libreadline-dev \
                libsqlite3-dev \
                llvm \
                clang \
                || { log_error "系統依賴安裝失敗"; exit 1; }
            ;;
            
        "macos")
            # 檢查 Homebrew
            if ! command -v brew &> /dev/null; then
                log_info "安裝 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            log_info "安裝基礎依賴..."
            brew install \
                git \
                python@3.12 \
                node \
                pkg-config \
                pulseaudio \
                || { log_error "系統依賴安裝失敗"; exit 1; }
            ;;
            
        "windows")
            # 檢查 Chocolatey
            if ! command -v choco &> /dev/null; then
                log_info "安裝 Chocolatey..."
                powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
            fi
            
            log_info "安裝基礎依賴..."
            choco install -y \
                git \
                python3 \
                nodejs \
                visualstudio2019buildtools \
                || { log_error "系統依賴安裝失敗"; exit 1; }
            ;;
            
        *)
            log_error "不支持的作業系統: $OS"
            exit 1
            ;;
    esac
    
    log_success "系統依賴安裝完成"
}

# 設置 Python 環境
setup_python_env() {
    log_step "設置 Python 環境..."
    
    # 檢查 Python 版本
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 升級 pip
    log_info "升級 pip..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    # 安裝系統級的關鍵包（如果需要）
    python3 -m pip install --user virtualenv
    
    log_success "Python 環境設置完成"
}

# 創建並激活虛擬環境
create_venv() {
    log_step "創建虛擬環境..."
    
    VENV_DIR="./venv"
    
    if [ -d "$VENV_DIR" ]; then
        log_warning "虛擬環境已存在，將重新創建..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    
    # 激活虛擬環境
    source "$VENV_DIR/bin/activate"
    
    # 升級虛擬環境中的 pip
    pip install --upgrade pip setuptools wheel
    
    log_success "虛擬環境創建完成"
}

# 安裝 Python 依賴
install_python_deps() {
    log_step "安裝 Python 依賴..."
    
    # 激活虛擬環境
    source ./venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        log_info "從 requirements.txt 安裝依賴..."
        pip install -r requirements.txt
    else
        log_warning "requirements.txt 不存在，安裝基礎依賴..."
        
        # 安裝基礎依賴
        pip install \
            fastapi>=0.109.0 \
            uvicorn[standard]>=0.27.0 \
            pydantic>=2.6.0 \
            python-multipart>=0.0.9 \
            aiohttp>=3.9.3 \
            requests>=2.31.0 \
            websockets>=13.0 \
            numpy>=1.26.4 \
            python-dotenv>=1.0.1 \
            cryptography>=42.0.0 \
            psutil>=5.9.8 \
            loguru>=0.7.2 \
            || { log_error "Python 依賴安裝失敗"; exit 1; }
    fi
    
    log_success "Python 依賴安裝完成"
}

# 設置 Node.js 環境
setup_nodejs_env() {
    log_step "設置 Node.js 環境..."
    
    # 檢查 Node.js 版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_info "Node.js 版本: $NODE_VERSION"
        
        # 檢查是否需要升級
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
        if [ "$NODE_MAJOR" -lt "16" ]; then
            log_warning "Node.js 版本過低，建議升級到 16+"
        fi
        
        # 檢查 npm
        if command -v npm &> /dev/null; then
            NPM_VERSION=$(npm --version)
            log_info "npm 版本: $NPM_VERSION"
        else
            log_error "npm 未安裝"
            exit 1
        fi
    else
        log_error "Node.js 未安裝"
        exit 1
    fi
    
    # 安裝桌面應用依賴
    if [ -d "apps/desktop-app/electron_app" ]; then
        log_info "安裝桌面應用依賴..."
        cd apps/desktop-app/electron_app
        
        # 檢查 package.json
        if [ -f "package.json" ]; then
            npm install
            cd ../../..
        else
            log_warning "package.json 不存在，跳過桌面應用依賴"
            cd ../../..
        fi
    fi
    
    # 安裝移動端依賴
    if [ -d "apps/mobile-app" ]; then
        log_info "安裝移動端依賴..."
        cd apps/mobile-app
        
        # 檢查 package.json
        if [ -f "package.json" ]; then
            npm install
            cd ../..
        else
            log_warning "package.json 不存在，跳過移動端依賴"
            cd ../..
        fi
    fi
    
    log_success "Node.js 環境設置完成"
}

# 創建配置文件
create_configs() {
    log_step "創建配置文件..."
    
    # 創建 .env 文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已創建 .env 配置文件"
        else
            cat > .env << 'EOF'
# Angela AI Environment Configuration
ANGELA_ENV=development
NODE_ENV=development
ANGELA_TESTING=true

# Backend Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_URL=http://127.0.0.1:8000

# Security Keys (Auto-generated)
ANGELA_KEY_A=$(openssl rand -hex 32)
ANGELA_KEY_B=$(openssl rand -hex 32)
ANGELA_KEY_C=$(openssl rand -hex 32)

# Performance Settings
PERFORMANCE_MODE=auto
TARGET_FPS=60
ENABLE_HARDWARE_ACCELERATION=true

# Logging
LOG_LEVEL=info
DEBUG_MODE=true
EOF
            log_info "已創建默認 .env 配置文件"
        fi
    fi
    
    # 創建必要的目錄
    mkdir -p logs data/{models,memories,cache,temp}
    log_info "已創建必要目錄"
    
    log_success "配置文件創建完成"
}

# 生成安全密鑰
generate_security_keys() {
    log_step "生成安全密鑰..."
    
    # 嘗試使用 openssl 生成密鑰
    if command -v openssl &> /dev/null; then
        KEY_A=$(openssl rand -hex 32)
        KEY_B=$(openssl rand -hex 32)
        KEY_C=$(openssl rand -hex 32)
    else
        # 使用 Python 生成密鑰
        KEY_A=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        KEY_B=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        KEY_C=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    fi
    
    # 更新 .env 文件中的密鑰
    if [ -f ".env" ]; then
        sed -i.tmp "s/ANGELA_KEY_A=.*/ANGELA_KEY_A=$KEY_A/" .env
        sed -i.tmp "s/ANGELA_KEY_B=.*/ANGELA_KEY_B=$KEY_B/" .env
        sed -i.tmp "s/ANGELA_KEY_C=.*/ANGELA_KEY_C=$KEY_C/" .env
        rm .env.tmp
    fi
    
    log_success "安全密鑰生成完成"
}

# 構建原生模組
build_native_modules() {
    log_step "構建原生模組..."
    
    if [ -d "apps/desktop-app/native_modules" ]; then
        # 構建 Linux 音頻模組
        if [ "$OS" == "linux" ] && [ -d "apps/desktop-app/native_modules/node-pulseaudio-capture" ]; then
            log_info "構建 Linux PulseAudio 模組..."
            cd apps/desktop-app/native_modules/node-pulseaudio-capture
            npm install || log_warning "PulseAudio 模組構建失敗"
            cd ../../..
        fi
        
        # 構建 macOS CoreAudio 模組
        if [ "$OS" == "macos" ] && [ -d "apps/desktop-app/native_modules/node-coreaudio-capture" ]; then
            log_info "構建 macOS CoreAudio 模組..."
            cd apps/desktop-app/native_modules/node-coreaudio-capture
            npm install || log_warning "CoreAudio 模組構建失敗"
            cd ../../..
        fi
        
        # 構建 Windows WASAPI 模組
        if [ "$OS" == "windows" ] && [ -d "apps/desktop-app/native_modules/node-wasapi-capture" ]; then
            log_info "構建 Windows WASAPI 模組..."
            cd apps/desktop-app/native_modules/node-wasapi-capture
            npm install || log_warning "WASAPI 模組構建失敗"
            cd ../../..
        fi
    fi
    
    log_success "原生模組構建完成"
}

# 啟動 Angela AI
start_angela() {
    log_step "啟動 Angela AI..."
    
    # 設置環境變量
    export ANGELA_ENV=development
    export ANGELA_TESTING=true
    
    # 創建啟動腳本
    cat > start_angela.sh << 'EOF'
#!/bin/bash
# Angela AI 啟動腳本
cd "$(dirname "$0")"

# 設置環境變量
export ANGELA_ENV=development
export ANGELA_TESTING=true

# 激活虛擬環境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虛擬環境已激活"
fi

# 創建日誌目錄
mkdir -p logs

echo "🌟 啟動 Angela AI..."
echo "📍 後端地址: http://127.0.0.1:8000"
echo "🔗 健康檢查: http://127.0.0.1:8000/health"
echo "📊 系統狀態: http://127.0.0.1:8000/api/v1/system/status"
echo ""

# 啟動後端服務
if [ -f "quick_start.py" ]; then
    echo "🚀 啟動最小後端服務..."
    python3 quick_start.py &
    BACKEND_PID=$!
    echo "🔄 後端進程 PID: $BACKEND_PID"
elif [ -d "apps/backend" ]; then
    echo "🚀 啟動完整後端服務..."
    cd apps/backend
    python3 start_monitor.py &
    BACKEND_PID=$!
    cd ..
    echo "🔄 後端進程 PID: $BACKEND_PID"
else
    echo "❌ 找不到後端服務"
    exit 1
fi

# 等待後端啟動
sleep 3

# 啟動桌面應用
if [ -d "apps/desktop-app/electron_app" ] && command -v npm &> /dev/null; then
    echo "🖥️ 啟動桌面應用..."
    cd apps/desktop-app/electron_app
    npm start &
    DESKTOP_PID=$!
    cd ../..
    echo "🔄 桌面應用進程 PID: $DESKTOP_PID"
else
    echo "⚠️ 桌面應用跳過（Node.js 未安裝或缺少依賴）"
fi

# 保存 PID
echo $BACKEND_PID > .backend.pid
if [ ! -z "$DESKTOP_PID" ]; then
    echo $DESKTOP_PID > .desktop.pid
fi

echo ""
echo "✅ Angela AI 已啟動！"
echo "🛑 要停止服務，請運行: ./stop_angela.sh"
echo "📈 要查看狀態，請運行: ./status_angela.sh"
EOF
    
    chmod +x start_angela.sh
    
    # 創建停止腳本
    cat > stop_angela.sh << 'EOF'
#!/bin/bash
# Angela AI 停止腳本
cd "$(dirname "$0")"

echo "🛑 停止 Angela AI..."

# 停止後端服務
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ 後端服務已停止"
    else
        echo "⚠️ 後端服務進程不存在"
    fi
    rm .backend.pid
fi

# 停止桌面應用
if [ -f ".desktop.pid" ]; then
    DESKTOP_PID=$(cat .desktop.pid)
    if kill -0 $DESKTOP_PID 2>/dev/null; then
        kill $DESKTOP_PID
        echo "✅ 桌面應用已停止"
    else
        echo "⚠️ 桌面應用進程不存在"
    fi
    rm .desktop.pid
fi

echo "👋 Angela AI 已完全停止"
EOF
    
    chmod +x stop_angela.sh
    
    # 創建狀態腳本
    cat > status_angela.sh << 'EOF'
#!/bin/bash
# Angela AI 狀態檢查腳本
cd "$(dirname "$0")"

echo "🌟 Angela AI - 服務狀態"
echo "================================="

# 檢查後端服務
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🟢 後端服務: 運行中 (PID: $BACKEND_PID)"
    else
        echo "🔴 後端服務: 離線"
        rm .backend.pid
    fi
else
    echo "🔴 後端服務: 未啟動"
fi

# 檢查桌面應用
if [ -f ".desktop.pid" ]; then
    DESKTOP_PID=$(cat .desktop.pid)
    if kill -0 $DESKTOP_PID 2>/dev/null; then
        echo "🟢 桌面應用: 運行中 (PID: $DESKTOP_PID)"
    else
        echo "🔴 桌面應用: 離線"
        rm .desktop.pid
    fi
else
    echo "🔴 桌面應用: 未啟動"
fi

echo ""
echo "📍 服務端點:"
echo "   健康檢查: http://127.0.0.1:8000/health"
echo "   系統狀態: http://127.0.0.1:8000/api/v1/system/status"

# 嘗試連接健康檢查
if command -v curl &> /dev/null; then
    echo ""
    echo "🔗 連接測試:"
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "   🟢 後端連接: 正常"
    else
        echo "   🔴 後端連接: 失敗"
    fi
fi

echo ""
echo "🛑 管理命令:"
echo "   啟動: ./start_angela.sh"
echo "   停止: ./stop_angela.sh"
echo "   狀態: ./status_angela.sh"
EOF
    
    chmod +x status_angela.sh
    
    log_success "啟動腳本創建完成"
    
    # 自動啟動
    echo ""
    echo "🚀 自動啟動 Angela AI..."
    ./start_angela.sh
}

# 主函數
main() {
    echo -e "${CYAN}🌟 Angela AI - 全自動安裝和啟動${NC}"
    echo "========================================"
    echo ""
    
    # 檢測操作系統
    detect_os
    
    # 檢查是否以 root 權限運行
    if [[ $EUID -eq 0 ]]; then
        log_warning "檢測到 root 權限，建議使用普通用戶權限運行"
    fi
    
    # 執行安裝步驟
    install_system_deps
    setup_python_env
    create_venv
    install_python_deps
    setup_nodejs_env
    create_configs
    generate_security_keys
    build_native_modules
    
    echo ""
    echo -e "${GREEN}✅ Angela AI 安裝完成！${NC}"
    echo ""
    
    # 啟動應用
    start_angela
}

# 捕獲信號
trap 'echo -e "\n${RED}安裝被中斷${NC}"; exit 1' INT TERM

# 執行主函數
main "$@"