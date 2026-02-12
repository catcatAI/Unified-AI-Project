#!/usr/bin/env python3
"""
Angela AI Unified Launcher v6.2.0
一键启动：自动启动后端 API + 桌面应用

Usage:
    python run_angela.py                    # 启动全部
    python run_angela.py --api-only        # 只启动后端
    python run_angela.py --desktop-only    # 只启动桌面
    python run_angela.py --install-shortcut # 创建桌面快捷方式
    python run_angela.py --health-check    # 健康检查
"""

import sys
import os
import subprocess
import argparse
import time
import signal
import json
from pathlib import Path
from typing import Optional, Tuple, List


# ============================================
# 进度显示工具
# ============================================

class ProgressDisplay:
    """进度显示器"""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
    
    def update(self, step: int, message: str, status: str = "info") -> None:
        """更新进度"""
        self.current_step = step
        spinner = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
        self.spinner_index += 1
        
        # 计算进度百分比
        percent = min(100, int((step / self.total_steps) * 100))
        
        # 选择状态图标
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "loading": spinner,
            "pending": "⏳",
        }
        icon = icons.get(status, "ℹ️")
        
        # 清除当前行并显示进度
        progress_bar = "█" * (percent // 2) + "░" * (50 - percent // 2)
        print(f"\r[{progress_bar}] {percent:3d}%  {icon} {message}", end="", flush=True)
        
        if status in ["success", "error"]:
            print()  # 完成或错误时换行
    
    def finish(self, message: str) -> None:
        """完成进度显示"""
        print(f"\r[█████████████████████████████████████████████████] 100%  ✅ {message}")
        print()
    
    def error(self, message: str) -> None:
        """显示错误"""
        print(f"\r[█████████████████████████████████████████████████] ERROR  ❌ {message}")
        print()


# ============================================
# 错误恢复工具
# ============================================

class ErrorRecovery:
    """错误恢复管理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.log_file = project_root / "logs" / "launcher.log"
        self.error_log_file = project_root / "logs" / "launcher_errors.json"
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_error(self, component: str, error: Exception, context: dict = None) -> None:
        """记录错误"""
        error_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }
        
        # 写入错误日志文件
        errors = self._load_errors()
        errors.append(error_entry)
        
        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(errors[-100:], f, indent=2, ensure_ascii=False)
        
        # 写入详细日志
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"ERROR at {error_entry['timestamp']}\n")
            f.write(f"Component: {component}\n")
            f.write(f"Error: {error_entry['error_type']}: {error_entry['error_message']}\n")
            f.write(f"Context: {json.dumps(context, indent=2)}\n")
            import traceback
            f.write(traceback.format_exc())
    
    def _load_errors(self) -> List[dict]:
        """加载错误历史"""
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def suggest_recovery(self, component: str) -> List[str]:
        """建议恢复方案"""
        suggestions = {
            "backend": [
                "检查 Python 依赖是否已安装",
                "运行: pip install -r requirements.txt",
                "检查端口 8000 是否被占用",
                "尝试单独启动后端: python run_angela.py --api-only",
            ],
            "desktop": [
                "检查 Node.js 依赖是否已安装",
                "运行: cd apps/desktop-app/electron_app && npm install",
                "检查 Electron 是否正确安装",
                "尝试单独启动桌面: python run_angela.py --desktop-only",
            ],
            "dependencies": [
                "运行: python install_angela.py",
                "确保 Python 版本 >= 3.8",
                "检查虚拟环境是否激活",
            ],
            "port": [
                "检查端口 8000 是否被占用",
                "关闭占用端口的程序",
                "或修改配置文件中的端口号",
            ],
        }
        return suggestions.get(component, ["检查日志文件获取更多信息", "尝试重启系统", "联系技术支持"])


# ============================================
# 启动器
# ============================================

def wait_for_server(port=8000, timeout=60, progress: Optional[ProgressDisplay] = None) -> bool:
    """等待服务器启动"""
    import socket

    start = time.time()
    check_interval = 0.5
    
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        
        if progress:
            elapsed = time.time() - start
            progress.update(int((elapsed / timeout) * 30), f"等待后端启动 ({elapsed:.1f}s/{timeout}s)", "loading")
        
        time.sleep(check_interval)
    
    return False


class Launcher:
    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.backend_dir = self.project_root / "apps" / "backend"
        self.electron_dir = self.project_root / "apps" / "desktop-app" / "electron_app"
        self.mode = "user"  # Default mode
        self.progress = ProgressDisplay(total_steps=100)
        self.recovery = ErrorRecovery(self.project_root)
    
    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result != 0
        except Exception:
            return False
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """检查核心依赖是否安装"""
        self.progress.update(5, "检查环境依赖...")
        
        missing = []
        required_packages = {
            "fastapi": "FastAPI",
            "uvicorn": "Uvicorn",
            "psutil": "psutil",
            "yaml": "PyYAML",
        }
        
        for module, name in required_packages.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(name)
        
        if missing:
            self.progress.error(f"缺失关键组件: {', '.join(missing)}")
            return False, missing
        
        self.progress.update(10, "环境依赖检查完成", "success")
        return True, []
    
    def check_python_version(self) -> bool:
        """检查 Python 版本"""
        version = sys.version_info
        if version < (3, 8):
            self.progress.error(f"Python 版本过低: {version.major}.{version.minor}, 需要 >= 3.8")
            return False
        return True
    
    def check_node_installed(self) -> bool:
        """检查 Node.js 是否安装"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def start_backend(self) -> Optional[subprocess.Popen]:
        """启动后端"""
        self.progress.update(20, "启动后端 API...")
        
        try:
            python = sys.executable
            cmd = [
                python,
                "-m",
                "uvicorn",
                "src.services.main_api_server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
            
            if self.mode == "user":
                cmd.extend(["--log-level", "warning"])
            
            env = os.environ.copy()
            src_path = str(self.backend_dir / "src")
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"]
            else:
                env["PYTHONPATH"] = src_path
            
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_CONSOLE if self.mode == "dev" else 0
            else:
                creation_flags = 0
            
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.backend_dir),
                creationflags=creation_flags,
                env=env,
            )
            
            self.progress.update(30, "后端启动中...", "loading")
            
            if wait_for_server(8000, progress=self.progress):
                self.progress.update(50, "后端已就绪", "success")
                return proc
            else:
                self.progress.error("后端启动超时")
                self.recovery.log_error("backend", Exception("Backend startup timeout"))
                return None
            
        except Exception as e:
            self.progress.error(f"后端启动失败: {e}")
            self.recovery.log_error("backend", e, {"mode": self.mode})
            return None
    
    def start_desktop(self) -> Optional[subprocess.Popen]:
        """启动桌面应用"""
        self.progress.update(60, "启动桌面应用...")
        
        if not self.electron_dir.exists():
            self.progress.update(70, "桌面应用不存在", "warning")
            return None
        
        # 检查 Node.js
        if not self.check_node_installed():
            self.progress.error("Node.js 未安装")
            self.recovery.log_error("desktop", Exception("Node.js not installed"))
            return None
        
        try:
            if sys.platform == "win32":
                electron = self.electron_dir / "node_modules" / ".bin" / "electron.cmd"
                if not electron.exists():
                    self.progress.update(70, "请先安装桌面依赖", "warning")
                    return None
                
                creation_flags = subprocess.CREATE_NEW_CONSOLE if self.mode == "dev" else subprocess.CREATE_NO_WINDOW
                
                proc = subprocess.Popen(
                    [str(electron), str(self.electron_dir)],
                    cwd=str(self.electron_dir),
                    creationflags=creation_flags,
                )
            else:
                proc = subprocess.Popen(["npm", "start"], cwd=str(self.electron_dir))
            
            self.progress.update(80, "桌面应用已启动", "success")
            return proc
            
        except Exception as e:
            self.progress.error(f"桌面启动失败: {e}")
            self.recovery.log_error("desktop", e)
            return None
    
    def create_shortcut(self) -> bool:
        """创建快捷方式"""
        self.progress.update(20, "创建桌面快捷方式...")
        
        try:
            if sys.platform != "win32":
                self.progress.update(30, "快捷方式仅支持 Windows", "warning")
                return False
            
            from win32com.client import Dispatch

            desktop = os.path.join(os.path.expandvars("%USERPROFILE%"), "Desktop")
            shortcut_path = os.path.join(desktop, "Angela AI.lnk")

            shell = Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(shortcut_path)
            sc.Targetpath = sys.executable
            sc.Arguments = f'"{self.project_root / "run_angela.py"}'
            sc.WorkingDirectory = str(self.project_root)
            sc.Description = "Angela AI - 桌面数字生命"
            sc.save()

            self.progress.finish(f"快捷方式已创建: {shortcut_path}")
            return True

        except Exception as e:
            self.progress.error(f"快捷方式创建失败: {e}")
            self.recovery.log_error("shortcut", e)
            return False
    
    def shutdown(self, backend_proc: Optional[subprocess.Popen], desktop_proc: Optional[subprocess.Popen]) -> None:
        """关闭所有进程"""
        self.progress.update(95, "正在关闭...", "loading")
        
        for proc in [desktop_proc, backend_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        
        self.progress.finish("已关闭")
    
    def run_health_check(self) -> bool:
        """运行健康检查"""
        print("\n" + "=" * 60)
        print("🔍 Angela AI 健康检查")
        print("=" * 60)
        
        checks = [
            ("Python 版本", self.check_python_version, True),
            ("Python 依赖", lambda: self.check_dependencies()[0], True),
            ("Node.js 安装", self.check_node_installed, True),
            ("端口 8000 可用", lambda: self.check_port_available(8000), True),
            ("后端目录存在", lambda: self.backend_dir.exists(), True),
            ("桌面目录存在", lambda: self.electron_dir.exists(), False),
        ]
        
        all_pass = True
        for name, check_func, required in checks:
            try:
                result = check_func()
                icon = "✅" if result else "❌"
                print(f"{icon} {name}")
                if required and not result:
                    all_pass = False
            except Exception as e:
                print(f"❌ {name} (检查失败: {e})")
                if required:
                    all_pass = False
        
        print("=" * 60)
        if all_pass:
            print("✅ 所有检查通过！")
        else:
            print("⚠️  发现问题，请根据上述提示进行修复")
        
        print()
        return all_pass


def main():
    parser = argparse.ArgumentParser(
        description="Angela AI 一键启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--api-only", action="store_true", help="只启动后端")
    parser.add_argument("--desktop-only", action="store_true", help="只启动桌面")
    parser.add_argument("--install-shortcut", action="store_true", help="创建桌面快捷方式")
    parser.add_argument("--health-check", action="store_true", help="运行健康检查")
    parser.add_argument(
        "--mode", type=str, choices=["user", "dev"], default="user",
        help="运行模式: user (简洁/普通用户), dev (详细/开发者)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🌟 Angela AI 一键启动器 v6.2.0")
    print("=" * 60)

    launcher = Launcher()
    launcher.mode = args.mode

    if args.health_check:
        return 0 if launcher.run_health_check() else 1
    
    if args.install_shortcut:
        return 0 if launcher.create_shortcut() else 1
    
    # 检查 Python 版本
    if not launcher.check_python_version():
        return 1
    
    # 检查依赖
    deps_ok, missing = launcher.check_dependencies()
    if not deps_ok:
        print(f"\n⚠️  缺失依赖: {', '.join(missing)}")
        print("请运行: python install_angela.py")
        return 1

    # 安全检查: 验证密钥
    print("\n🔒 安全检查: 验证系统密钥...")
    try:
        # 添加 src 到路径
        sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend"))
        from src.core.security.key_validator import validate_system_keys

        keys_valid, key_results = validate_system_keys()
        if not keys_valid:
            print("\n⚠️  密钥安全检查失败！")
            print("请确保:")
            print("1. 复制 .env.example 为 .env")
            print("2. 使用强随机生成器创建密钥")
            print("3. 运行: python -m src.core.security.key_generator")
            print("4. 不要使用占位符或默认值")
            print()
            print("详细报告:")
            for result in key_results:
                if not result.is_valid:
                    for issue in result.issues:
                        print(f"  - {issue}")
            print("\n是否继续启动? (不推荐 - 安全风险) [y/N]: ", end="")
            try:
                response = input().strip().lower()
                if response != 'y':
                    print("启动已取消。")
                    return 1
                print("⚠️  警告: 使用不安全的密钥启动系统！")
            except (EOFError, KeyboardInterrupt):
                print("\n启动已取消。")
                return 1
        else:
            print("✅ 密钥安全检查通过")
    except Exception as e:
        print(f"⚠️  密钥验证模块加载失败: {e}")
        print("将跳过密钥验证继续启动（不推荐）")

    backend_proc = None
    desktop_proc = None

    if not args.desktop_only:
        backend_proc = launcher.start_backend()
        if backend_proc is None:
            # 后端启动失败，显示恢复建议
            print("\n❌ 后端启动失败")
            print("建议恢复方案:")
            for suggestion in launcher.recovery.suggest_recovery("backend"):
                print(f"  • {suggestion}")
            return 1

    if not args.api_only:
        desktop_proc = launcher.start_desktop()
        if desktop_proc is None and not args.desktop_only:
            print("\n⚠️  桌面应用启动失败，但后端仍在运行")
            print("建议恢复方案:")
            for suggestion in launcher.recovery.suggest_recovery("desktop"):
                print(f"  • {suggestion}")

    if backend_proc or desktop_proc:
        launcher.progress.finish("Angela AI 启动完成！")
        print("\n" + "=" * 60)
        print("💡 按 Ctrl+C 退出")
        print("=" * 60)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        launcher.shutdown(backend_proc, desktop_proc)

    return 0


if __name__ == "__main__":
    sys.exit(main())