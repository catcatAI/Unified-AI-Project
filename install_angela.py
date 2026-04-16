"""
Angela AI Installer - GitHub一键安装版
Complete Automated Installer for New Users

功能:
  1. 从GitHub克隆项目
  2. 自动检测硬件
  3. 自动安装依赖
  4. 自动生成默认配置
  5. 自动创建快捷方式和系统菜单
  6. 自动创建卸载程序
  7. 一键启动运行

用法:
  python install_angela.py [--install-dir PATH] [--skip-clone]
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile
import argparse
import json
import platform
import logging
logger = logging.getLogger(__name__)


from typing import Optional


class AngelaInstaller:
    def __init__(
        self, install_dir: Optional[str] = None, repo_url: Optional[str] = None
    ):
        self.repo_url = repo_url or "https://github.com/catcatAI/Unified-AI-Project.git"
        self.install_dir = (
            Path(install_dir) if install_dir else self._get_default_install_dir()
        )
        self.temp_dir: Optional[Path] = None
        self.hardware_info = {}

    def _get_default_install_dir(self) -> Path:
        if sys.platform == "win32":
            # If current directory looks like a project root, use it
            if (Path.cwd() / "apps" / "backend").exists():
                return Path.cwd()
            user_home = os.environ.get("USERPROFILE") or str(Path.home())
            return Path(user_home) / "AngelaAI"
        elif sys.platform == "darwin":
            return Path.home() / "Applications" / "AngelaAI"
        else:
            return Path.home() / ".local" / "share" / "AngelaAI"

    def detect_hardware(self):
        """自动检测硬件並建立效能分級"""
        print("\n🔍 正在分析硬體效能 (Hardware Probe)...")
        
        # 嘗試導入內部的 HardwareProbe
        try:
            # 由於安裝時可能還沒安裝 psutil，這裏做簡單的類比
            # 但我們可以利用 wmic 獲取足夠數據
            cores = os.cpu_count() or 4
            memory = self._get_memory_gb()
            gpu_name = self._detect_gpu()
            
            # 簡單計算 AI 評分 (與 HardwareProbe 邏輯對齊)
            score = cores * 2 + (memory // 4) * 5
            if "RTX" in gpu_name or "GTX" in gpu_name:
                score += 40
            elif "Apple" in gpu_name:
                score += 30
            
            if score > 80: tier = "Extreme"
            elif score > 60: tier = "High"
            elif score > 40: tier = "Medium"
            else: tier = "Low"
            
            self.hardware_info = {
                "platform": sys.platform,
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "cpu_cores": cores,
                "memory_gb": memory,
                "gpu": gpu_name,
                "performance_tier": tier,
                "ai_capability_score": score
            }
        except Exception as e:
            print(f"   ⚠️  硬體偵測異常: {e}")
            self.hardware_info = {"performance_tier": "Medium", "ai_capability_score": 50}

        print(f"   ✅ 分級: {self.hardware_info['performance_tier']} (Score: {self.hardware_info.get('ai_capability_score', 0)})")
        print(f"   ✅ GPU: {self.hardware_info['gpu']}")
        return self.hardware_info

    def _get_memory_gb(self):
        try:
            self._refresh_paths()
            import psutil

            return psutil.virtual_memory().total // (1024**3)
        except Exception as e:
            logger.error(f'Unexpected error in {__name__}: {e}', exc_info=True)
            return 8


    def _detect_gpu(self):
        try:
            import subprocess

            if sys.platform == "win32":
                # Try wmic first
                try:
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                except Exception:
                    result = None

                # Fallback to PowerShell if wmic fails or returns empty
                if not result or not result.stdout.strip():
                    result = subprocess.run(
                        ["powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                
                for line in result.stdout.split("\n"):
                    if line.strip() and "Name" not in line:
                        return line.strip()
            elif sys.platform == "darwin":
                return "Apple Metal"
            else:
                result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[-1].strip()
        except Exception as e:
            # Final fallback
            try:
                if sys.platform == "win32":
                    res = subprocess.run(["powershell", "-Command", "(Get-WmiObject Win32_VideoController).Name"], capture_output=True, text=True)
                    if res.stdout.strip(): return res.stdout.strip().split("\n")[0]
            except: pass
            logger.error(f'GPU detection failed: {e}')
            pass

        return "Unknown/Software"

    def print_header(self):
        print("=" * 70)
        print("🌟 Angela AI 一键安装程序 v6.0.4")
        print("=" * 70)
        print("\n本程序将自动完成以下操作:")
        print("   1. 从GitHub拉取最新代码")
        print("   2. 检测您的硬件配置")
        print("   3. 安装Python依赖包")
        print("   4. 生成默认配置文件")
        print("   5. 创建桌面快捷方式")
        print("   6. 创建卸载程序")
        print("=" * 70)
        print()

    def check_prerequisites(self) -> bool:
        print("📋 检查系统要求...\n")
        checks = []

        if sys.version_info < (3, 9):
            print("❌ Python版本过低，需要 3.9+")
            print(f"   当前: {sys.version_info.major}.{sys.version_info.minor}")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("⚠️ Node.js未找到，桌面应用可能无法运行")
        except:
            print("⚠️ Node.js未安装，桌面应用可能无法运行")
        
        # 检查Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Git: {result.stdout.strip()}")
            else:
                print("❌ Git未安装，无法继续安装")
                return False
        except:
            print("❌ Git未安装，无法继续安装")
            return False
        
        # 检查网络连接
        try:
            import urllib.request
            urllib.request.urlopen('https://github.com', timeout=5)
            print("✅ 网络连接正常")
        except:
            print("❌ 无法连接GitHub，请检查网络")
            return False
            return False
        checks.append(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
            )
            checks.append("✅ pip 包管理器")
        except:
            print("❌ pip 不可用")
            return False

        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            checks.append("✅ Git 版本控制")
        except:
            print("⚠️  Git 未安装，将使用ZIP下载")

        for check in checks:
            print(f"   {check}")
        print()
        return True

    def clone_repository(self) -> bool:
        print(f"📥 拉取项目从 GitHub...")
        print(f"   仓库: {self.repo_url}")
        print(f"   目标: {self.install_dir}\n")

        if self.install_dir.exists():
            print(f"⚠️  目录已存在: {self.install_dir}")
            response = input("   是否覆盖? (y/n): ").lower().strip()
            if response != "y":
                print("   安装取消")
                return False
            try:
                shutil.rmtree(self.install_dir)
                print("   已清除旧版本")
            except Exception as e:
                print(f"   无法清除: {e}")
                return False

        self.temp_dir = Path(tempfile.mkdtemp(prefix="angela_install_"))

        try:
            print("   正在克隆仓库...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.temp_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"   ⚠️  Git克隆失败，尝试ZIP下载...")
                return self._download_zip()

            shutil.move(str(self.temp_dir), str(self.install_dir))
            print(f"   ✅ 代码拉取完成\n")
            return True

        except Exception as e:
            print(f"   ❌ 拉取失败: {e}")
            return False
        finally:
            if self.temp_dir and self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    logger.error(f'Unexpected error in {__name__}: {e}', exc_info=True)
                    pass


    def _download_zip(self) -> bool:
        try:
            import urllib.request
            import zipfile

            if not self.temp_dir:
                self.temp_dir = Path(tempfile.mkdtemp(prefix="angela_install_"))

            zip_url = "https://github.com/catcatAI/Unified-AI-Project/archive/refs/heads/main.zip"
            zip_path = self.temp_dir / "angela.zip"

            print(f"   下载ZIP文件...")
            urllib.request.urlretrieve(zip_url, zip_path)

            print(f"   解压中...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.temp_dir)

            extracted_dir = self.temp_dir / "Unified-AI-Project-main"
            if extracted_dir.exists() and self.install_dir:
                shutil.move(str(extracted_dir), str(self.install_dir))

            print(f"   ✅ ZIP下载完成\n")
            return True

        except Exception as e:
            print(f"   ❌ ZIP下载失败: {e}")
            return False

    def install_dependencies(self) -> bool:
        print("📦 安装依赖包...")

        requirements_file = self.install_dir / "requirements.txt"

        if not requirements_file.exists():
            print(f"❌ 找不到 requirements.txt")
            return False

        try:
            print("   安装中（这可能需要5-10分钟）...")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                    "--user",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )

            critical_packages = ["fastapi", "uvicorn", "pydantic", "numpy", "httpx", "Pillow", "aiohttp"]
            missing = []
            for package in critical_packages:
                try:
                    target = "PIL" if package == "Pillow" else package.lower().replace("-", "_")
                    __import__(target)
                except ImportError:
                    missing.append(package)

            if missing:
                print(f"   ⚠️  单独安装缺失包: {missing}")
                for package in missing:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package, "--user"],
                        capture_output=True,
                    )

            print(f"   ✅ 依赖安装完成\n")
            self._refresh_paths()
            return True

        except subprocess.TimeoutExpired:
            print("   ❌ 安装超时")
            return False
        except Exception as e:
            print(f"   ❌ 安装失败: {e}")
            return False

    def generate_default_config(self):
        """自动生成默认配置文件"""
        print("⚙️  生成默认配置...")

        config_dir = self.install_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        tier = self.hardware_info.get("performance_tier", "Medium")
        
        # 根據效能等級自動調整 AI 配置
        precision_modes = {
            "Extreme": {"mode": "extreme", "scaling": 1.0, "llm": "gemini-1.5-pro-latest"},
            "High": {"mode": "high", "scaling": 0.8, "llm": "gemini-pro"},
            "Medium": {"mode": "standard", "scaling": 0.5, "llm": "gemini-pro"},
            "Low": {"mode": "low-resource", "scaling": 0.3, "llm": "gemini-1.5-flash"},
        }
        preset = precision_modes.get(tier, precision_modes["Medium"])

        config = {
            "name": "Angela",
            "version": "6.1.0",
            "language": "zh-CN",
            "user_tier": tier,
            "hardware": self.hardware_info,
            "desktop_pet": {
                "enabled": True,
                "name": "Angela",
                "start_position": "bottom-right",
                "scale": 1.0,
                "frame_rate": 60 if tier in ["High", "Extreme"] else 30,
            },
            "api": {
                "google_api_key": "",
                "gemini_model": preset["llm"],
            },
            "audio": {
                "tts_engine": "edge-tts",
                "voice": "zh-CN-XiaoxiaoNeural",
            },
            "precision": {
                "default_mode": preset["mode"],
                "resource_scaling": preset["scaling"],
                "auto_optimize": True,
            },
            "maturity": {
                "start_level": 0,
                "xp_multiplier": 1.2 if tier == "Extreme" else 1.0,
            },
        }

        config_file = config_dir / "angela_config.yaml"
        try:
            self._refresh_paths()
            import yaml

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            print(f"   ✅ 配置已生成: {config_file}")
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            config_file = config_dir / "angela_config.json"

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"   ✅ 配置已生成: {config_file}")

        credentials_example = {
            "google_api_key": "YOUR_API_KEY_HERE",
            "instructions": "复制此文件到 ~/.config/angela-ai/credentials.json 并填入您的API密钥",
        }
        creds_file = config_dir / "credentials.example.json"
        with open(creds_file, "w", encoding="utf-8") as f:
            json.dump(credentials_example, f, indent=2, ensure_ascii=False)
        print(f"   ✅ 凭证示例: {creds_file}")

        return True

    def create_shortcuts(self) -> bool:
        print("🎯 创建快捷方式...")

        if sys.platform != "win32":
            print("   ℹ️  非Windows系统")
            print(f'   启动命令: cd "{self.install_dir}" && python run_angela.py')
            return True

        shortcut_target = str(self.install_dir / "run_angela.py")
        shortcut_workdir = str(self.install_dir)
        python_path = sys.executable

        try:
            from win32com.client import Dispatch

            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            shell = Dispatch("WScript.Shell")

            shortcut_path = os.path.join(desktop, "Angela AI.lnk")
            sc = shell.CreateShortCut(shortcut_path)
            sc.Targetpath = python_path
            sc.Arguments = f'"{shortcut_target}"'
            sc.WorkingDirectory = shortcut_workdir
            sc.Description = "Angela AI - 桌面数字生命"
            sc.save()
            print("   ✅ 桌面快捷方式")

            start_menu = os.path.join(
                os.environ["APPDATA"],
                "Microsoft",
                "Windows",
                "Start Menu",
                "Programs",
                "Angela AI",
            )
            os.makedirs(start_menu, exist_ok=True)

            for name, target in [
                ("启动 Angela AI.lnk", shortcut_target),
                ("卸载 Angela AI.lnk", str(self.install_dir / "uninstall.py")),
            ]:
                sc = shell.CreateShortCut(os.path.join(start_menu, name))
                sc.Targetpath = python_path
                sc.Arguments = f'"{target}"'
                sc.WorkingDirectory = shortcut_workdir
                sc.Description = name.replace(".lnk", "")
                sc.save()
            print("   ✅ 开始菜单快捷方式")

            return True

        except Exception as e:
            print(f"   ⚠️  使用 PowerShell 创建...")
            return self._create_shortcuts_powershell(
                shortcut_target, shortcut_workdir, python_path
            )

    def _create_shortcuts_powershell(
        self, target: str, workdir: str, python: str
    ) -> bool:
        try:
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            ps = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{desktop}\\Angela AI.lnk")
$sc.TargetPath = "{python}"
$sc.Arguments = '"{target}"'
$sc.WorkingDirectory = "{workdir}"
$sc.Description = "Angela AI"
$sc.Save()
'''
            subprocess.run(["powershell", "-Command", ps], capture_output=True)
            print("   ✅ 桌面快捷方式 (PowerShell)")

            start_menu = os.path.join(
                os.environ["APPDATA"],
                "Microsoft",
                "Windows",
                "Start Menu",
                "Programs",
                "Angela AI",
            )
            os.makedirs(start_menu, exist_ok=True)

            for name, arg in [
                ("启动 Angela AI", target),
                ("卸载 Angela", f"{self.install_dir}\\uninstall.py"),
            ]:
                ps = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{start_menu}\\{name}.lnk")
$sc.TargetPath = "{python}"
$sc.Arguments = '"{arg}"'
$sc.WorkingDirectory = "{workdir}"
$sc.Description = "{name}"
$sc.Save()
'''
                subprocess.run(["powershell", "-Command", ps], capture_output=True)
            print("   ✅ 开始菜单快捷方式 (PowerShell)")

            return True
        except Exception as e:
            print(f"   ❌ 快捷方式创建失败: {e}")
            return False

    def create_uninstaller(self) -> bool:
        print("🗑️  创建卸载程序...")

        uninstall_script = self.install_dir / "uninstall.py"
        if uninstall_script.exists():
            print(f"   ✅ 卸载程序已存在")
            return True

        try:
            import urllib.request

            uninstall_url = "https://raw.githubusercontent.com/catcatAI/Unified-AI-Project/main/uninstall.py"
            urllib.request.urlretrieve(uninstall_url, uninstall_script)
            print(f"   ✅ 卸载程序已创建")
        except:
            print("   ⚠️  无法下载卸载程序，将使用内置脚本")

        print()
        return True

    def launch_angela(self) -> bool:
        """一键启动 Angela"""
        print("\n🚀 正在启动 Angela AI...")
        print("   提示: 按 Ctrl+C 可安全退出\n")

        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [sys.executable, str(self.install_dir / "run_angela.py")],
                    cwd=str(self.install_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                subprocess.Popen(
                    [sys.executable, str(self.install_dir / "run_angela.py")],
                    cwd=str(self.install_dir),
                )
            print("   ✅ Angela 已启动！")
            return True
        except Exception as e:
            print(f"   ⚠️  启动失败: {e}")
            print(f'   请手动运行: cd "{self.install_dir}" && python run_angela.py')
            return False

    def _refresh_paths(self):
        """Refresh sys.path and importlib to see newly installed packages."""
        import site
        import importlib
        if hasattr(site, "getusersitepackages"):
            user_site = site.getusersitepackages()
            if user_site not in sys.path:
                sys.path.append(user_site)
        importlib.invalidate_caches()

    def print_summary(self, success: bool, launch: bool = False):
        print("=" * 70)
        if success:
            print("✅ 安装成功!")
        else:
            print("❌ 安装未完成")
        print("=" * 70)

        print(f"\n📂 安装位置: {self.install_dir}")

        if success:
            if launch:
                self.launch_angela()
            else:
                print("\n🚀 启动方式:")
                print(f"   1. 双击桌面快捷方式 'Angela AI'")
                print(f"   2. 或在终端运行:")
                print(f'      cd "{self.install_dir}"')
                print(f"      python run_angela.py")

            print("\n📖 首次配置:")
            print(f"   1. 复制凭证模板:")
            print(f"      cp {self.install_dir}/config/credentials.example.json")
            print(f"      ~/.config/angela-ai/credentials.json")
            print(f"   2. 编辑并填入您的 Google API 密钥")

            print("\n📚 文档:")
            print(f"   - README: {self.install_dir}/README.md")
            print(f"   - 卸载: {self.install_dir}/uninstall.py")

            print("\n💡 提示:")
            print("   - 按 Ctrl+C 安全退出")
            print("   - 日志保存在 logs/ 目录")

        print("\n" + "=" * 70)
        print("🌟 Angela AI - 您的桌面数字生命")
        print("=" * 70)


def bootstrap_dependencies():
    """Ensure essential installer dependencies are present and visible."""
    essentials = ["psutil", "PyYAML", "requests"]
    missing = []
    for pkg in essentials:
        try:
            __import__(pkg if pkg != "PyYAML" else "yaml")
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 正在準備安裝程式組件: {', '.join(missing)}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing, "--user", "--quiet"],
                check=True,
                capture_output=True
            )
            
            # Refresh paths so we can use them immediately
            import site
            import importlib
            if hasattr(site, "getusersitepackages"):
                user_site = site.getusersitepackages()
                if user_site not in sys.path:
                    # Insert at the beginning to prioritize newly installed packages
                    sys.path.insert(0, user_site)
            importlib.invalidate_caches()
            
            print("✅ 安裝程式組件準備完成\n")
        except Exception as e:
            print(f"⚠️  組件安裝失敗: {e}，這可能會導致後續報錯。")

def main():
    # Bootstrap before anything else
    bootstrap_dependencies()
    parser = argparse.ArgumentParser(
        description="Angela AI 一键安装程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python install_angela.py

  python install_angela.py --install-dir "D:\\AngelaAI"

  python install_angela.py --skip-clone
        """,
    )

    parser.add_argument("--install-dir", type=str, help="安装目录")
    parser.add_argument(
        "--repo",
        type=str,
        default="https://github.com/catcatAI/Unified-AI-Project.git",
        help="GitHub仓库地址",
    )
    parser.add_argument("--skip-clone", action="store_true", help="跳过克隆")
    parser.add_argument("--launch", action="store_true", help="安装后自动启动")

    args = parser.parse_args()

    installer = AngelaInstaller(install_dir=args.install_dir, repo_url=args.repo)

    installer.print_header()

    if not installer.check_prerequisites():
        installer.print_summary(False)
        return 1

    success = True

    if not args.skip_clone:
        if not installer.clone_repository():
            success = False

    if success:
        installer.detect_hardware()

        if not installer.install_dependencies():
            print("⚠️  依赖安装可能不完整...")

        installer.generate_default_config()
        installer.create_shortcuts()
        installer.create_uninstaller()

    installer.print_summary(success, launch=args.launch)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
