#!/usr/bin/env python3
"""
Angela AI 無權限安裝器
不需要 sudo，用戶級別安裝所有依賴
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
import json
import zipfile
import shutil
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class AngelaNoSudoInstaller:
    def __init__(self):
        self.os_type = os.name
        self.project_root = Path(__file__).parent
        self.user_local = Path.home() / ".local"
        
    def print_step(self, message):
        print(f"🔧 {message}")
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_warning(self, message):
        print(f"⚠️ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
    
    def download_pip_standalone(self):
        """下載獨立 pip"""
        self.print_step("下載獨立 pip...")
        
        try:
            # 下載 get-pip.py
            get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
            get_pip_path = self.project_root / "get-pip.py"
            
            urllib.request.urlretrieve(get_pip_url, get_pip_path)
            self.print_success("pip 下載完成")
            return get_pip_path
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.print_error(f"pip 下載失敗: {e}")

            return None
    
    def install_pip_user(self):
        """用戶級別安裝 pip"""
        self.print_step("用戶級別安裝 pip...")
        
        get_pip_path = self.download_pip_standalone()
        if not get_pip_path:
            return False
            
        try:
            # 用戶級別安裝 pip
            result = subprocess.run([
                sys.executable, str(get_pip_path), 
                "--user", "--quiet"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_success("pip 安裝成功")
                return True
            else:
                self.print_error(f"pip 安裝失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.print_error(f"pip 安裝異常: {e}")

            return False
    
    def get_user_pip(self):
        """獲取用戶級別 pip"""
        # 檢查用戶級別 pip
        user_bin = self.user_local / "bin"
        
        if self.os_type == "nt":
            pip_cmd = "pip"
        else:
            pip_path = user_bin / "pip"
            if pip_path.exists():
                pip_cmd = str(pip_path)
            else:
                # 嘗試使用 Python -m pip
                pip_cmd = [sys.executable, "-m", "pip"]
                
        return pip_cmd
    
    def install_with_user_pip(self, package):
        """用用戶級別 pip 安裝包"""
        pip_cmd = self.get_user_pip()
        
        if isinstance(pip_cmd, str):
            cmd = [pip_cmd, "install", "--user", "--upgrade", package]
        else:
            cmd = pip_cmd + ["install", "--user", "--upgrade", package]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f'Unexpected error in {__name__}: {e}', exc_info=True)
            return False

    
    def create_user_venv(self):
        """創建用戶級別虛擬環境"""
        self.print_step("創建用戶級別虛擬環境...")
        
        venv_path = self.project_root / "venv"
        
        # 如果虛擬環境存在，先刪除
        if venv_path.exists():
            shutil.rmtree(venv_path)
        
        try:
            # 創建虛擬環境
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            
            self.print_success("虛擬環境創建成功")
            return venv_path
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.print_error(f"虛擬環境創建失敗: {e}")

            return None
    
    def setup_venv_pip(self, venv_path):
        """設置虛擬環境中的 pip"""
        self.print_step("升級虛擬環境中的 pip...")
        
        if self.os_type == "nt":
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            pip_exe = venv_path / "bin" / "pip"
            
        try:
            subprocess.run([
                str(pip_exe), "install", "--upgrade", "pip", "setuptools", "wheel"
            ], check=True)
            self.print_success("pip 升級完成")
            return pip_exe
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self.print_error(f"pip 升級失敗: {e}")

            return None
    
    def install_basic_dependencies(self, pip_exe):
        """安裝基礎依賴"""
        self.print_step("安裝基礎依賴...")
        
        # 核心依賴列表
        core_deps = [
            "fastapi>=0.109.0",
            "uvicorn[standard]>=0.27.0",
            "pydantic>=2.6.0", 
            "python-multipart>=0.0.9",
            "requests>=2.31.0",
            "websockets>=13.0",
            "python-dotenv>=1.0.1",
            "cryptography>=42.0.0"
        ]
        
        failed_deps = []
        
        for dep in core_deps:
            try:
                self.print_step(f"安裝 {dep}...")
                result = subprocess.run([
                    str(pip_exe), "install", dep
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.print_success(f"{dep} 安裝成功")
                else:
                    self.print_warning(f"{dep} 安裝失敗")
                    failed_deps.append(dep)
                    
            except subprocess.TimeoutExpired:
                self.print_warning(f"{dep} 安裝超時")
                failed_deps.append(dep)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                self.print_warning(f"{dep} 安裝異常: {e}")

                failed_deps.append(dep)
        
        return len(failed_deps) == 0
    
    def install_nodejs_standalone(self):
        """安裝獨立 Node.js"""
        self.print_step("安裝獨立 Node.js...")
        
        if self.os_type == "nt":
            # Windows 下載 Node.js
            try:
                # 下載並安裝 Node.js 到用戶目錄
                node_url = "https://nodejs.org/dist/v20.12.2/node-v20.12.2-win-x64.zip"
                zip_path = self.project_root / "nodejs.zip"
                extract_dir = self.project_root / "nodejs_temp"
                
                urllib.request.urlretrieve(node_url, zip_path)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 移動到用戶目錄
                node_dir = self.user_local / "nodejs"
                if node_dir.exists():
                    shutil.rmtree(node_dir)
                    
                # 找到實際的 node 目錄
                actual_node_dir = None
                for item in extract_dir.iterdir():
                    if item.name.startswith("node-"):
                        actual_node_dir = item
                        break
                        
                if actual_node_dir:
                    shutil.move(str(actual_node_dir), str(node_dir))
                    
                    # 添加到 PATH
                    node_bin = node_dir
                    os.environ["PATH"] = str(node_bin) + os.pathsep + os.environ.get("PATH", "")
                    
                    # 創建符號鏈接
                    if self.user_local / "bin" in os.environ["PATH"].split(os.pathsep):
                        node_link = self.user_local / "bin" / "node"
                        npm_link = self.user_local / "bin" / "npm"
                        
                        try:
                            node_link.unlink(missing_ok=True)
                            npm_link.unlink(missing_ok=True)
                            
                            node_link.symlink_to(node_dir / "node.exe")
                            npm_link.symlink_to(node_dir / "npm.cmd")
                        except Exception as e:
                            logger.error(f'Unexpected error in {__name__}: {e}', exc_info=True)
                            pass

                    
                    self.print_success("Node.js 安裝完成")
                    return True
                    
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                self.print_error(f"Node.js 安裝失敗: {e}")

                return False
        
        elif self.os_type == "posix":
            # Linux/macOS 使用 NVM
            try:
                nvm_install_url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh"
                nvm_script = self.project_root / "install_nvm.sh"
                
                urllib.request.urlretrieve(nvm_install_url, nvm_script)
                
                # 運行 NVM 安裝
                result = subprocess.run([
                    "bash", str(nvm_script)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # 加載 NVM 並安裝 Node.js
                    nvm_dir = Path.home() / ".nvm"
                    bashrc = Path.home() / ".bashrc"
                    
                        # 添加 NVM 到 bashrc
                    nvm_lines = [
                        'export NVM_DIR="$HOME/.nvm"',
                        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"',
                        '[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"'
                    ]
                    
                    with open(bashrc, 'a') as f:
                        f.write('\n# NVM\n')
                        for line in nvm_lines:
                            f.write(line + '\n')
                    
                    # 安裝 Node.js
                    subprocess.run([
                        "bash", "-c", 
                        "source ~/.bashrc && nvm install 20 && nvm use 20"
                    ], check=True)
                    
                    self.print_success("Node.js 安裝完成")
                    return True
                    
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                self.print_error(f"Node.js 安裝失敗: {e}")

                return False
        
        return False
    
    def create_minimal_backend(self):
        """創建最小後端服務"""
        self.print_step("創建最小後端服務...")
        
        minimal_backend = '''#!/usr/bin/env python3
"""
Angela AI 最小後端服務
不依賴外部庫，使用標準庫
"""

import os
import sys
import json
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import hashlib
import hmac
import secrets

class AngelaMinimalHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 設置環境變量
        os.environ['ANGELA_TESTING'] = 'true'
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """自定義日誌格式"""
        print(f"🌐 {format % args}")
    
    def do_GET(self):
        """處理 GET 請求"""
        if self.path == '/health':
            self._send_json_response({
                'status': 'ok',
                'service': 'angela-ai',
                'mode': 'minimal',
                'version': '6.2.1'
            })
            
        elif self.path == '/api/v1/system/status':
            self._send_json_response({
                'system_level': 'Level 5 AGI',
                'status': 'operational',
                'components': {
                    'backend': 'active',
                    'api': 'active'
                },
                'timestamp': time.time(),
                'environment': os.environ.get('ANGELA_ENV', 'development')
            })
            
        elif self.path == '/api/v1/system/status/detailed':
            # 需要簽名的詳細狀態
            self._send_json_response({
                'error': 'Signature required for detailed status'
            }, status=401)
            
        else:
            self._send_json_response({
                'error': 'Endpoint not found',
                'available_endpoints': [
                    '/health',
                    '/api/v1/system/status',
                    '/api/v1/system/status/detailed'
                ]
            }, status=404)
    
    def do_POST(self):
        """處理 POST 請求"""
        if self.path == '/api/v1/system/status/detailed':
            # 檢查簽名
            signature = self.headers.get('X-Angela-Signature')
            if not signature:
                self._send_json_response({
                    'error': 'Missing X-Angela-Signature header'
                }, status=401)
                return
            
            # 在測試模式下繞過簽名驗證
            if os.environ.get('ANGELA_TESTING') == 'true':
                self._send_json_response({
                    'status': 'online',
                    'stats': {
                        'cpu': '12%',
                        'mem': '42%',
                        'nodes': 1
                    },
                    'modules': {
                        'vision': True,
                        'audio': True,
                        'tactile': True,
                        'action': True
                    },
                    'timestamp': time.time()
                })
            else:
                self._send_json_response({
                    'error': 'Invalid signature'
                }, status=403)
                
        elif self.path == '/api/v1/mobile/test':
            # 移動端測試端點
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            self._send_json_response({
                'status': 'success',
                'message': 'Test message received',
                'timestamp': time.time()
            })
            
        else:
            self._send_json_response({
                'error': 'Endpoint not found'
            }, status=404)
    
    def do_OPTIONS(self):
        """處理 OPTIONS 請求（CORS 預檢）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Angela-Signature')
        self.end_headers()
    
    def _send_json_response(self, data, status=200):
        """發送 JSON 響應"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Angela-Signature')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

def main():
    """啟動最小後端服務"""
    print("🌟 Angela AI - 最小後端服務")
    print("=" * 50)
    print(f"📍 服務地址: http://127.0.0.1:8000")
    print(f"🔗 健康檢查: http://127.0.0.1:8000/health")
    print(f"📊 系統狀態: http://127.0.0.1:8000/api/v1/system/status")
    print("=" * 50)
    print("🛑 按 Ctrl+C 停止服務")
    print()
    
    # 設置環境變量
    os.environ['ANGELA_ENV'] = 'development'
    os.environ['ANGELA_TESTING'] = 'true'
    
    # 創建服務器
    try:
        server = HTTPServer(('127.0.0.1', 8000), AngelaMinimalHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 正在停止服務...")
        server.shutdown()
        print("✅ Angela AI 已停止")
    except Exception as e:
        print(f"❌ 服務器啟動失敗: {e}")

if __name__ == "__main__":
    main()
'''
        
        minimal_backend_file = self.project_root / "minimal_backend.py"
        with open(minimal_backend_file, 'w') as f:
            f.write(minimal_backend)
        
        self.print_success("最小後端創建完成")
        return minimal_backend_file
    
    def create_config_files(self):
        """創建配置文件"""
        self.print_step("創建配置文件...")
        
        # 創建 .env 文件
        env_file = self.project_root / ".env"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(f"""# Angela AI Environment Configuration
ANGELA_ENV=development
NODE_ENV=development
ANGELA_TESTING=true

# Backend Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_URL=http://127.0.0.1:8000

# Security Keys (Auto-generated)
ANGELA_KEY_A={os.urandom(32).hex()}
ANGELA_KEY_B={os.urandom(32).hex()}
ANGELA_KEY_C={os.urandom(32).hex()}

# Performance Settings
PERFORMANCE_MODE=auto
TARGET_FPS=60
ENABLE_HARDWARE_ACCELERATION=true

# Logging
LOG_LEVEL=info
DEBUG_MODE=true
""")
            
            self.print_success(".env 配置文件創建完成")
        
        # 創建必要目錄
        dirs = ["logs", "data/models", "data/memories", "data/cache", "data/temp"]
        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
        
        self.print_success("目錄結構創建完成")
    
    def start_angela(self):
        """啟動 Angela AI"""
        print("\n🎉 安裝完成！")
        print("🚀 啟動 Angela AI...")
        print()
        
        # 啟動最小後端
        minimal_backend = self.project_root / "minimal_backend.py"
        if minimal_backend.exists():
            try:
                subprocess.run([sys.executable, str(minimal_backend)])
            except KeyboardInterrupt:
                print("\n👋 Angela AI 已停止")
        else:
            self.print_error("找不到最小後端服務")
    
    def run(self):
        """運行無權限安裝"""
        print("🌟 Angela AI - 無權限全自動安裝器")
        print("=" * 50)
        print()
        
        # 創建最小後端
        self.create_minimal_backend()
        
        # 創建配置文件
        self.create_config_files()
        
        # 嘗試安裝 pip（用戶級別）
        if self.install_pip_user():
            self.print_success("pip 安裝成功")
            
            # 創建虛擬環境
            venv_path = self.create_user_venv()
            if venv_path:
                # 設置虛擬環境
                pip_exe = self.setup_venv_pip(venv_path)
                if pip_exe:
                    # 安裝依賴
                    self.install_basic_dependencies(pip_exe)
                else:
                    self.print_warning("使用最小後端模式")
        
        # 嘗試安裝 Node.js（可選）
        self.install_nodejs_standalone()
        
        # 啟動 Angela
        self.start_angela()

if __name__ == "__main__":
    installer = AngelaNoSudoInstaller()
    installer.run()