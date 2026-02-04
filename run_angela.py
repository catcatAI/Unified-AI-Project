#!/usr/bin/env python3
"""
Angela AI Unified Launcher v6.0.4
一键启动：自动启动后端 API + 桌面应用

Usage:
    python run_angela.py                    # 启动全部
    python run_angela.py --api-only        # 只启动后端
    python run_angela.py --desktop-only    # 只启动桌面
    python run_angela.py --install-shortcut # 创建桌面快捷方式
"""

import sys
import os
import subprocess
import argparse
import time
import signal
from pathlib import Path


def wait_for_server(port=8000, timeout=30):
    """等待服务器启动"""
    import socket

    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


class Launcher:
    def __init__(self):
        self.project_root = Path(__file__).parent.resolve()
        self.backend_dir = self.project_root / "apps" / "backend"
        self.electron_dir = self.project_root / "apps" / "desktop-app" / "electron_app"

    def log(self, msg, status="✅"):
        print(f"   {status} {msg}")

    def start_backend(self):
        """启动后端"""
        self.log("启动后端 API...")

        try:
            python = sys.executable

            if sys.platform == "win32":
                proc = subprocess.Popen(
                    [
                        python,
                        "-m",
                        "uvicorn",
                        "src.services.main_api_server:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                    ],
                    cwd=str(self.backend_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                proc = subprocess.Popen(
                    [
                        python,
                        "-m",
                        "uvicorn",
                        "src.services.main_api_server:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                    ],
                    cwd=str(self.backend_dir),
                )

            self.log("后端启动中 (端口 8000)...")

            if wait_for_server(8000):
                self.log("后端已就绪")
                return proc
            else:
                self.log("后端启动超时", "❌")
                return None

        except Exception as e:
            self.log(f"后端启动失败: {e}", "❌")
            return None

    def start_desktop(self):
        """启动桌面应用"""
        self.log("启动桌面应用...")

        if not self.electron_dir.exists():
            self.log("桌面应用不存在", "⚠️")
            return None

        try:
            if sys.platform == "win32":
                electron = self.electron_dir / "node_modules" / ".bin" / "electron.cmd"
                if not electron.exists():
                    self.log("请先安装依赖: cd apps/desktop-app && npm install", "⚠️")
                    return None

                proc = subprocess.Popen(
                    [str(electron), str(self.electron_dir)],
                    cwd=str(self.electron_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                proc = subprocess.Popen(["npm", "start"], cwd=str(self.electron_dir))

            self.log("桌面应用已启动")
            return proc

        except Exception as e:
            self.log(f"桌面启动失败: {e}", "❌")
            return None

    def create_shortcut(self):
        """创建快捷方式"""
        self.log("创建快捷方式...")

        try:
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

            self.log(f"快捷方式已创建: {shortcut_path}")
            return True

        except Exception as e:
            self.log(f"快捷方式失败: {e}", "❌")
            return False

    def shutdown(self, backend_proc, desktop_proc):
        self.log("正在关闭...")
        for proc in [desktop_proc, backend_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        self.log("已关闭")


def main():
    parser = argparse.ArgumentParser(
        description="Angela AI 一键启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--api-only", action="store_true", help="只启动后端")
    parser.add_argument("--desktop-only", action="store_true", help="只启动桌面")
    parser.add_argument(
        "--install-shortcut", action="store_true", help="创建桌面快捷方式"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("🌟 Angela AI 一键启动器 v6.0.4")
    print("=" * 50)

    launcher = Launcher()

    if args.install_shortcut:
        launcher.create_shortcut()
        return 0

    backend_proc = None
    desktop_proc = None

    if not args.desktop_only:
        backend_proc = launcher.start_backend()

    if not args.api_only:
        desktop_proc = launcher.start_desktop()

    if backend_proc or desktop_proc:
        print("\n" + "=" * 50)
        print("✅ Angela 已启动!")
        print("=" * 50)
        print("💡 按 Ctrl+C 退出")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        launcher.shutdown(backend_proc, desktop_proc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
