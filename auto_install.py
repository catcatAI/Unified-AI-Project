#!/usr/bin/env python3
"""
Angela AI 自動安裝器 - Python 版本
自動處理所有前置條件和依賴
"""

import os
import sys
import subprocess
import platform
import urllib.request
import json
import time
from pathlib import Path

class AngelaAutoInstaller:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        
    def print_step(self, message):
        print(f"🔧 {message}")
        
    def print_success(self, message):
        print(f"✅ {message}")
        
    def print_warning(self, message):
        print(f"⚠️ {message}")
        
    def print_error(self, message):
        print(f"❌ {message}")
        
    def run_command(self, command, check=True, shell=False):
        """執行命令並返回結果"""
        try:
            if shell:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(command, capture_output=True, text=True)
            
            if check and result.returncode != 0:
                self.print_error(f"命令失敗: {' '.join(command) if isinstance(command, list) else command}")
                self.print_error(f"錯誤信息: {result.stderr}")
                return False, result.stderr
            return True, result.stdout
            
        except Exception as e:
            self.print_error(f"命令執行異常: {e}")
            return False, str(e)
    
    def detect_os(self):
        """檢測操作系統"""
        self.print_step("檢測操作系統...")
        
        if self.os_type == "linux":
            # 檢測 Linux 發行版
            try:
                with open("/etc/os-release", "r") as f:
                    os_info = f.read()
                    if "ubuntu" in os_info.lower():
                        self.distro = "ubuntu"
                    elif "debian" in os_info.lower():
                        self.distro = "debian"
                    elif "centos" in os_info.lower() or "rhel" in os_info.lower():
                        self.distro = "rhel"
                    elif "arch" in os_info.lower():
                        self.distro = "arch"
                    else:
                        self.distro = "unknown"
            except:
                self.distro = "unknown"
                
            self.print_success(f"Linux ({self.distro})")
            
        elif self.os_type == "darwin":
            self.distro = "macos"
            self.print_success("macOS")
            
        elif self.os_type == "windows":
            self.distro = "windows"
            self.print_success("Windows")
            
        else:
            self.distro = "unknown"
            self.print_warning(f"未知操作系統: {self.os_type}")
    
    def check_python(self):
        """檢查 Python 環境"""
        self.print_step("檢查 Python 環境...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.print_error(f"Python 版本過低: {version.major}.{version.minor}，需要 3.9+")
            return False
            
        self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def install_pip_if_needed(self):
        """安裝 pip 如果需要"""
        self.print_step("檢查 pip...")
        
        try:
            import pip
            self.print_success("pip 已安裝")
            return True
        except ImportError:
            self.print_warning("pip 未安裝，嘗試安裝...")
            
            if self.os_type == "linux":
                if self.distro in ["ubuntu", "debian"]:
                    success, _ = self.run_command([
                        "sudo", "apt", "update"
                    ], shell=False)
                    if success:
                        success, _ = self.run_command([
                            "sudo", "apt", "install", "-y", "python3-pip"
                        ], shell=False)
                        
            elif self.os_type == "windows":
                success, _ = self.run_command([
                    "python", "-m", "ensurepip", "--default-pip"
                ], shell=False)
                
            return success
    
    def create_virtual_env(self):
        """創建虛擬環境"""
        self.print_step("創建虛擬環境...")
        
        if self.venv_path.exists():
            self.print_warning("虛擬環境已存在，將重新創建...")
            import shutil
            shutil.rmtree(self.venv_path)
        
        success, _ = self.run_command([
            sys.executable, "-m", "venv", str(self.venv_path)
        ])
        
        if success:
            self.print_success("虛擬環境創建成功")
            return True
        return False
    
    def activate_venv(self):
        """獲取虛擬環境的路徑"""
        if self.os_type == "windows":
            python_exe = self.venv_path / "Scripts" / "python.exe"
            pip_exe = self.venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"
            pip_exe = self.venv_path / "bin" / "pip"
            
        return str(python_exe), str(pip_exe)
    
    def install_python_dependencies(self):
        """安裝 Python 依賴"""
        self.print_step("安裝 Python 依賴...")
        
        python_exe, pip_exe = self.activate_venv()
        
        # 升級 pip
        success, _ = self.run_command([pip_exe, "install", "--upgrade", "pip", "setuptools", "wheel"])
        if not success:
            self.print_warning("pip 升級失敗，繼續安裝...")
        
        # 檢查 requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            self.print_step("從 requirements.txt 安裝依賴...")
            success, _ = self.run_command([pip_exe, "install", "-r", str(requirements_file)])
        else:
            self.print_step("安裝基礎依賴...")
            
            # 基礎依賴列表
            basic_deps = [
                "fastapi>=0.109.0",
                "uvicorn[standard]>=0.27.0", 
                "pydantic>=2.6.0",
                "python-multipart>=0.0.9",
                "aiohttp>=3.9.3",
                "requests>=2.31.0",
                "websockets>=13.0",
                "python-dotenv>=1.0.1",
                "cryptography>=42.0.0",
                "psutil>=5.9.8",
                "loguru>=0.7.2"
            ]
            
            for dep in basic_deps:
                self.print_step(f"安裝 {dep}...")
                success, _ = self.run_command([pip_exe, "install", dep])
                if not success:
                    self.print_warning(f"{dep} 安裝失敗，繼續安裝其他依賴...")
        
        return success
    
    def check_nodejs(self):
        """檢查 Node.js"""
        self.print_step("檢查 Node.js...")
        
        success, output = self.run_command(["node", "--version"], check=False)
        if success:
            self.print_success(f"Node.js {output.strip()}")
            return True
        else:
            self.print_warning("Node.js 未安裝，將嘗試安裝...")
            return self.install_nodejs()
    
    def install_nodejs(self):
        """安裝 Node.js"""
        if self.os_type == "linux":
            if self.distro in ["ubuntu", "debian"]:
                success, _ = self.run_command([
                    "sudo", "apt", "install", "-y", "nodejs", "npm"
                ])
            elif self.distro == "arch":
                success, _ = self.run_command([
                    "sudo", "pacman", "-S", "--noconfirm", "nodejs", "npm"
                ])
            elif self.distro in ["centos", "rhel"]:
                success, _ = self.run_command([
                    "sudo", "yum", "install", "-y", "nodejs", "npm"
                ])
            else:
                self.print_warning("無法自動安裝 Node.js，請手動安裝")
                return False
                
        elif self.os_type == "windows":
            self.print_warning("請手動安裝 Node.js: https://nodejs.org/")
            return False
            
        elif self.os_type == "macos":
            success, _ = self.run_command(["brew", "install", "node"], check=False)
            if not success:
                success, _ = self.run_command([
                    "sudo", "port", "install", "nodejs"
                ], check=False)
                
        return success
    
    def install_npm_dependencies(self):
        """安裝 npm 依賴"""
        self.print_step("安裝 npm 依賴...")
        
        # 桌面應用依賴
        desktop_app = self.project_root / "apps" / "desktop-app" / "electron_app"
        if desktop_app.exists():
            package_json = desktop_app / "package.json"
            if package_json.exists():
                self.print_step("安裝桌面應用依賴...")
                success, _ = self.run_command(["npm", "install"], cwd=desktop_app)
                if not success:
                    self.print_warning("桌面應用依賴安裝失敗")
        
        # 移動端應用依賴
        mobile_app = self.project_root / "apps" / "mobile-app"
        if mobile_app.exists():
            package_json = mobile_app / "package.json"
            if package_json.exists():
                self.print_step("安裝移動端依賴...")
                success, _ = self.run_command(["npm", "install"], cwd=mobile_app)
                if not success:
                    self.print_warning("移動端依賴安裝失敗")
    
    def create_config_files(self):
        """創建配置文件"""
        self.print_step("創建配置文件...")
        
        # 創建 .env 文件
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
                self.print_success("已複製 .env.example 到 .env")
            else:
                # 創建默認配置
                import secrets
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
ANGELA_KEY_A={secrets.token_hex(32)}
ANGELA_KEY_B={secrets.token_hex(32)}
ANGELA_KEY_C={secrets.token_hex(32)}

# Performance Settings
PERFORMANCE_MODE=auto
TARGET_FPS=60
ENABLE_HARDWARE_ACCELERATION=true

# Logging
LOG_LEVEL=info
DEBUG_MODE=true
""")
                self.print_success("已創建默認 .env 配置文件")
        
        # 創建必要目錄
        dirs_to_create = [
            "logs",
            "data/models",
            "data/memories", 
            "data/cache",
            "data/temp"
        ]
        
        for dir_path in dirs_to_create:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        self.print_success("配置文件創建完成")
    
    def create_startup_scripts(self):
        """創建啟動腳本"""
        self.print_step("創建啟動腳本...")
        
        # 啟動腳本
        start_script = self.project_root / "start.py"
        with open(start_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Angela AI 啟動腳本
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    
    # 設置環境變量
    os.environ['ANGELA_ENV'] = 'development'
    os.environ['ANGELA_TESTING'] = 'true'
    
    print("🌟 啟動 Angela AI...")
    print("📍 後端地址: http://127.0.0.1:8000")
    print("🔗 健康檢查: http://127.0.0.1:8000/health")
    print("")
    
    # 激活虛擬環境並啟動
    venv_python = project_root / "venv" / ("Scripts" if os.name == 'nt' else "bin") / "python"
    
    if venv_python.exists():
        # 嘗試啟動完整後端
        backend_main = project_root / "apps" / "backend" / "main.py"
        if backend_main.exists():
            print("🚀 啟動完整後端服務...")
            subprocess.run([str(venv_python), str(backend_main)])
        else:
            # 啟動最小後端
            quick_start = project_root / "quick_start.py"
            if quick_start.exists():
                print("🚀 啟動最小後端服務...")
                subprocess.run([str(venv_python), str(quick_start)])
            else:
                print("❌ 找不到後端服務")
                return 1
    else:
        print("❌ 虛擬環境不存在，請先運行安裝程序")
        return 1

if __name__ == "__main__":
    main()
''')
        
        # 停止腳本
        stop_script = self.project_root / "stop.py"
        with open(stop_script, 'w') as f:
            f.write('''#!/usr/bin/env python3
"""
Angela AI 停止腳本
"""

import os
import signal
import psutil

def main():
    print("🛑 停止 Angela AI...")
    
    # 查找並停止 Angela 相關進程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('angela' in str(cmd).lower() or 'quick_start.py' in str(cmd) for cmd in cmdline):
                pid = proc.info['pid']
                os.kill(pid, signal.SIGTERM)
                print(f"✅ 已停止進程 {pid}")
        except:
            pass
    
    print("👋 Angela AI 已停止")

if __name__ == "__main__":
    main()
''')
        
        if os.name != 'nt':
            os.chmod(start_script, 0o755)
            os.chmod(stop_script, 0o755)
        
        self.print_success("啟動腳本創建完成")
    
    def test_installation(self):
        """測試安裝"""
        self.print_step("測試安裝...")
        
        python_exe, _ = self.activate_venv()
        
        # 測試 Python 依賴
        try:
            success, _ = self.run_command([
                python_exe, "-c", 
                "import fastapi, uvicorn, pydantic; print('✅ Python 依賴測試通過')"
            ])
        except:
            self.print_warning("Python 依賴測試失敗")
    
    def start_angela(self):
        """啟動 Angela"""
        print("\n🎉 安裝完成！")
        print("🚀 自動啟動 Angela AI...")
        print()
        
        python_exe, _ = self.activate_venv()
        
        # 啟動最小後端
        quick_start = self.project_root / "quick_start.py"
        if quick_start.exists():
            success, _ = self.run_command([python_exe, str(quick_start)], check=False)
            if success:
                print("✅ Angela AI 已啟動！")
                print("📍 後端地址: http://127.0.0.1:8000")
                print("🔗 健康檢查: http://127.0.0.1:8000/health")
                print("🛑 按 Ctrl+C 停止服務")
            else:
                self.print_error("啟動失敗")
    
    def run(self):
        """運行完整安裝流程"""
        print("🌟 Angela AI - 全自動安裝器")
        print("=" * 50)
        print()
        
        # 檢測操作系統
        self.detect_os()
        
        # 檢查 Python
        if not self.check_python():
            self.print_error("Python 環境不滿足要求")
            return False
        
        # 安裝 pip
        if not self.install_pip_if_needed():
            self.print_warning("pip 安裝失敗，可能會影響後續安裝")
        
        # 創建虛擬環境
        if not self.create_virtual_env():
            self.print_error("虛擬環境創建失敗")
            return False
        
        # 安裝 Python 依賴
        if not self.install_python_dependencies():
            self.print_error("Python 依賴安裝失敗")
            return False
        
        # 檢查並安裝 Node.js
        node_available = self.check_nodejs()
        if node_available:
            self.install_npm_dependencies()
        
        # 創建配置文件
        self.create_config_files()
        
        # 創建啟動腳本
        self.create_startup_scripts()
        
        # 測試安裝
        self.test_installation()
        
        # 啟動應用
        self.start_angela()
        
        return True

if __name__ == "__main__":
    installer = AngelaAutoInstaller()
    installer.run()