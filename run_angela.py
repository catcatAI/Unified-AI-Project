#!/usr/bin/env python3
"""
Angela AI Unified Launcher v6.0.4
一键启动：自动启动后端 API + 桌面应用

Usage:
    python run_angela.py           # 启动全部（推荐）
    python run_angela.py --api-only    # 只启动后端
    python run_angela.py --desktop-only # 只启动桌面
    python run_angela.py --install-shortcut # 创建桌面快捷方式

Options:
    --port      后端 API 端口 (默认: 8000)
    --desktop-port  桌面应用端口 (默认: 3001)
    --no-backend    跳过启动后端
    --no-desktop    跳过启动桌面
"""

import sys
import os
import asyncio
import subprocess
import argparse
import time
import signal
from pathlib import Path
from threading import Thread

try:
    from http.client import HTTPConnection
except ImportError:
    from http.client import HTTPConnection

HTTPConnection.timeout = 5


def find_free_port(start=8000, max_trials=100):
    """查找可用端口"""
    import socket

    for port in range(start, start + max_trials):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return start


def wait_for_server(host="localhost", port=8000, timeout=30):
    """等待服务器启动"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


class UnifiedLauncher:
    def __init__(
        self,
        port=8000,
        desktop_port=3001,
        no_backend=False,
        no_desktop=False,
        debug=False,
    ):
        self.port = port
        self.desktop_port = desktop_port
        self.no_backend = no_backend
        self.no_desktop = no_desktop
        self.debug = debug
        self.processes = []
        self.project_root = Path(__file__).parent.resolve()
        self.backend_process = None
        self.desktop_process = None

    def log(self, msg):
        print(f"   {msg}")

    def start_backend(self):
        """启动后端 API 服务器"""
        if self.no_backend:
            self.log("⏭️  跳过后端启动")
            return True

        self.log("🚀 启动后端 API...")

        backend_path = self.project_root / "apps" / "backend"

        try:
            python_exe = sys.executable

            if sys.platform == "win32":
                self.backend_process = subprocess.Popen(
                    [
                        python_exe,
                        "-m",
                        "uvicorn",
                        "src.services.main_api_server:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(self.port),
                    ],
                    cwd=str(backend_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                self.backend_process = subprocess.Popen(
                    [
                        python_exe,
                        "-m",
                        "uvicorn",
                        "src.services.main_api_server:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(self.port),
                    ],
                    cwd=str(backend_path),
                )

            self.log(f"   后端端口: {self.port}")

            if wait_for_server(port=self.port):
                self.log("   ✅ 后端已就绪")
                return True
            else:
                self.log("   ❌ 后端启动超时")
                return False

        except Exception as e:
            self.log(f"   ❌ 后端启动失败: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()
            return False

    def start_desktop(self):
        """启动桌面应用"""
        if self.no_desktop:
            self.log("⏭️  跳过桌面启动")
            return True

        self.log("🚀 启动桌面应用...")

        electron_path = self.project_root / "apps" / "desktop-app" / "electron_app"

        if not electron_path.exists():
            self.log(f"   ⚠️  桌面应用不存在: {electron_path}")
            return False

        try:
            if sys.platform == "win32":
                electron_exe = electron_path / "node_modules" / ".bin" / "electron.cmd"

                if electron_exe.exists():
                    self.desktop_process = subprocess.Popen(
                        [str(electron_exe), str(electron_path)],
                        cwd=str(electron_path),
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                else:
                    self.log(
                        "   ⚠️  未找到 electron，请先运行: cd apps/desktop-app && npm install"
                    )
                    return False
            else:
                self.desktop_process = subprocess.Popen(
                    ["npm", "start"], cwd=str(electron_path)
                )

            self.log("   ✅ 桌面应用已启动")
            return True

        except Exception as e:
            self.log(f"   ❌ 桌面应用启动失败: {e}")
            self.log("   💡 提示: 需要先安装 node_modules")
            return False

    def create_shortcut_windows(self):
        """创建 Windows 桌面快捷方式"""
        try:
            from winshell import shortcut
            from win32com.client import Dispatch

            desktop = os.path.join(os.path.expandvars("%USERPROFILE%"), "Desktop")
            shortcut_path = os.path.join(desktop, "Angela AI.lnk")

            shell = Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(shortcut_path)
            sc.Targetpath = sys.executable
            sc.Arguments = f'"{self.project_root / "run_angela.py"}"'
            sc.WorkingDirectory = str(self.project_root)
            sc.Description = "Angela AI - 桌面数字生命"
            sc.save()

            self.log(f"✅ 快捷方式已创建: {shortcut_path}")
            return True

        except Exception as e:
            self.log(f"❌ 快捷方式创建失败: {e}")
            return False

    def shutdown(self):
        """关闭所有进程"""
        self.log("\n👋 正在关闭...")
        for proc in [self.desktop_process, self.backend_process]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        self.log("✅ 已关闭")


def main():
    parser = argparse.ArgumentParser(
        description="Angela AI 一键启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_angela.py              # 启动全部
  python run_angela.py --api-only   # 只启动后端
  python run_angela.py --no-backend # 跳过启动后端
  python run_angela.py --install-shortcut  # 创建快捷方式
        """,
    )
    parser.add_argument("--port", type=int, default=8000, help="后端端口")
    parser.add_argument("--desktop-port", type=int, default=3001, help="桌面端口")
    parser.add_argument("--no-backend", action="store_true", help="不启动后端")
    parser.add_argument("--no-desktop", action="store_true", help="不启动桌面")
    parser.add_argument("--api-only", action="store_true", help="只启动后端 API")
    parser.add_argument(
        "--install-shortcut", action="store_true", help="创建桌面快捷方式"
    )
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    print("=" * 60)
    print("🌟 Angela AI 一键启动器 v6.0.4")
    print("=" * 60)

    launcher = UnifiedLauncher(
        port=args.port,
        desktop_port=args.desktop_port,
        no_backend=args.api_only or args.no_backend,
        no_desktop=args.no_desktop,
        debug=args.debug,
    )

    if args.install_shortcut:
        launcher.create_shortcut_windows()
        return 0

    success = True

    if not args.api_only:
        if not launcher.start_backend():
            success = False

    if success:
        if not args.no_desktop:
            launcher.start_desktop()

    if success:
        print("\n" + "=" * 60)
        print("✅ Angela 已启动!")
        print("=" * 60)
        print("\n💡 使用提示:")
        print("   • 桌面应用会自动打开")
        print("   • 在对话框中与 Angela 聊天")
        print("   • 按 Ctrl+C 退出")
        print("=" * 60)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        launcher.shutdown()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
