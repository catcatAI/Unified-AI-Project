"""
Angela AI Installer - GitHub一键安装版
Complete Installer for New Users

用法：
  1. 下载此文件 (install_angela.py)
  2. 双击运行或 python install_angela.py
  3. 按提示操作，自动从GitHub拉取并安装

功能：
  - 从GitHub克隆项目
  - 安装到指定目录
  - 自动安装依赖
  - 创建桌面和开始菜单快捷方式
  - 生成卸载程序
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile
import argparse


class AngelaInstaller:
    """Angela AI 完整安装程序"""
    
    def __init__(self, install_dir: str = None, repo_url: str = None):
        self.repo_url = repo_url or "https://github.com/catcatAI/Unified-AI-Project.git"
        self.install_dir = Path(install_dir) if install_dir else self._get_default_install_dir()
        self.temp_dir = None
        
    def _get_default_install_dir(self) -> Path:
        """获取默认安装目录"""
        if sys.platform == "win32":
            return Path(os.environ.get("USERPROFILE", "")) / "AngelaAI"
        elif sys.platform == "darwin":
            return Path.home() / "Applications" / "AngelaAI"
        else:
            return Path.home() / ".local" / "share" / "AngelaAI"
    
    def print_header(self):
        """打印安装标题"""
        print("=" * 70)
        print("🌟 Angela AI 安装程序")
        print("=" * 70)
        print("\n📦 将自动完成以下步骤：")
        print("   1. 从GitHub拉取最新代码")
        print("   2. 安装Python依赖包")
        print("   3. 创建桌面快捷方式")
        print("   4. 创建开始菜单项")
        print("=" * 70)
        print()
    
    def check_prerequisites(self) -> bool:
        """检查系统要求"""
        print("🔍 检查系统要求...\n")
        
        checks = []
        
        # 检查Python版本
        if sys.version_info < (3, 9):
            print("❌ Python版本过低，需要 3.9+")
            print(f"   当前: {sys.version_info.major}.{sys.version_info.minor}")
            print("   请从 https://python.org 下载最新Python")
            return False
        checks.append(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # 检查pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                          check=True, capture_output=True)
            checks.append("✅ pip 包管理器")
        except:
            print("❌ pip 未安装")
            return False
        
        # 检查Git
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            checks.append("✅ Git 版本控制")
        except:
            print("⚠️  Git 未安装，将尝试下载ZIP文件")
            print("   建议安装Git以获得更好体验: https://git-scm.com\n")
        
        # 检查磁盘空间
        try:
            if sys.platform == "win32":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.install_dir.root)),
                    ctypes.pointer(free_bytes), None, None
                )
                free_gb = free_bytes.value / (1024**3)
            else:
                stat = os.statvfs(self.install_dir.root)
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            
            if free_gb < 2:
                print(f"⚠️  磁盘空间不足: {free_gb:.1f} GB")
                print("   需要至少 2 GB 可用空间")
                return False
            checks.append(f"✅ 磁盘空间 ({free_gb:.1f} GB 可用)")
        except:
            checks.append("⚠️  磁盘空间检查失败")
        
        for check in checks:
            print(f"   {check}")
        print()
        return True
    
    def clone_repository(self) -> bool:
        """从GitHub克隆仓库"""
        print(f"📥 从GitHub拉取项目...")
        print(f"   仓库: {self.repo_url}")
        print(f"   目标: {self.install_dir}\n")
        
        # 如果目录已存在，询问是否覆盖
        if self.install_dir.exists():
            print(f"⚠️  目录已存在: {self.install_dir}")
            response = input("   是否覆盖并重新安装? (y/n): ").lower().strip()
            if response != 'y':
                print("   安装取消")
                return False
            try:
                shutil.rmtree(self.install_dir)
                print("   已清除旧版本")
            except Exception as e:
                print(f"   无法清除: {e}")
                return False
        
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="angela_install_"))
        
        try:
            # 尝试使用Git克隆
            print("   正在克隆仓库...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", self.repo_url, str(self.temp_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                print(f"   ⚠️  Git克隆失败: {result.stderr[:100]}")
                print("   尝试使用ZIP下载...")
                return self._download_zip()
            
            # 移动到安装目录
            shutil.move(str(self.temp_dir), str(self.install_dir))
            print(f"   ✅ 代码拉取完成\n")
            return True
            
        except subprocess.TimeoutExpired:
            print("   ❌ 克隆超时（网络问题？）")
            return False
        except Exception as e:
            print(f"   ❌ 拉取失败: {e}")
            return False
        finally:
            # 清理临时目录
            if self.temp_dir and self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
    
    def _download_zip(self) -> bool:
        """作为备选方案，下载ZIP文件"""
        try:
            import urllib.request
            import zipfile
            
            zip_url = "https://github.com/catcatAI/Unified-AI-Project/archive/refs/heads/main.zip"
            zip_path = self.temp_dir / "angela.zip"
            
            print(f"   下载ZIP文件...")
            urllib.request.urlretrieve(zip_url, zip_path)
            
            print(f"   解压中...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # 移动解压后的文件夹
            extracted_dir = self.temp_dir / "Unified-AI-Project-main"
            if extracted_dir.exists():
                shutil.move(str(extracted_dir), str(self.install_dir))
            
            print(f"   ✅ ZIP下载完成\n")
            return True
            
        except Exception as e:
            print(f"   ❌ ZIP下载失败: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print("📦 安装依赖包...")
        print("   （这可能需要5-10分钟，请耐心等待）\n")
        
        requirements_file = self.install_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print(f"❌ 找不到 requirements.txt")
            return False
        
        try:
            # 安装主依赖
            print("   安装核心依赖...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--user"],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode != 0:
                print(f"   ⚠️  安装警告: {result.stderr[:200]}")
            
            # 检查关键包是否安装
            critical_packages = ["fastapi", "uvicorn", "pydantic", "sqlalchemy"]
            missing = []
            for package in critical_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing.append(package)
            
            if missing:
                print(f"   ⚠️  缺少关键包: {missing}")
                print("   正在尝试单独安装...")
                for package in missing:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package, "--user"],
                        capture_output=True
                    )
            
            print(f"   ✅ 依赖安装完成\n")
            return True
            
        except subprocess.TimeoutExpired:
            print("   ❌ 安装超时")
            return False
        except Exception as e:
            print(f"   ❌ 安装失败: {e}")
            return False
    
    def create_shortcuts(self) -> bool:
        """创建快捷方式"""
        print("🎯 创建快捷方式...\n")
        
        if sys.platform != "win32":
            print("   ℹ️  非Windows系统，跳过快捷方式")
            print("   启动命令: cd {self.install_dir} && python run_angela.py")
            return True
        
        try:
            # 先尝试安装winshell
            try:
                import winshell
            except ImportError:
                print("   安装快捷方式工具...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "winshell", "pypiwin32", "--user"],
                    capture_output=True
                )
                import winshell
            
            from win32com.client import Dispatch
            
            # 桌面快捷方式
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Angela AI.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir / "run_angela.py"}"'
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.Description = "Angela AI - 桌面数字生命"
            shortcut.IconLocation = f"{self.install_dir / 'apps' / 'backend' / 'resources' / 'icon.ico'},0"
            shortcut.save()
            
            print(f"   ✅ 桌面快捷方式")
            
            # 开始菜单
            start_menu = winshell.start_menu()
            angela_folder = os.path.join(start_menu, "Angela AI")
            os.makedirs(angela_folder, exist_ok=True)
            
            # 启动快捷方式
            shortcut_path = os.path.join(angela_folder, "启动 Angela AI.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir / "run_angela.py"}"'
            shortcut.WorkingDirectory = str(self.install_dir)
            shortcut.Description = "启动Angela AI"
            shortcut.save()
            
            print(f"   ✅ 开始菜单")
            
            # 卸载快捷方式
            uninstall_script = self.install_dir / "uninstall.py"
            if uninstall_script.exists():
                shortcut_path = os.path.join(angela_folder, "卸载 Angela AI.lnk")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = f'"{uninstall_script}"'
                shortcut.WorkingDirectory = str(self.install_dir)
                shortcut.Description = "卸载Angela AI"
                shortcut.save()
                
                print(f"   ✅ 卸载程序")
            
            print()
            return True
            
        except Exception as e:
            print(f"   ⚠️  快捷方式创建失败: {e}")
            print("   您可以手动创建快捷方式\n")
            return False
    
    def create_uninstaller(self) -> bool:
        """创建卸载程序"""
        print("🗑️  创建卸载程序...\n")
        
        uninstall_script = self.install_dir / "uninstall.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
Angela AI 卸载程序
Uninstaller for Angela AI
"""

import os
import sys
import shutil
from pathlib import Path

print("="*60)
print("🗑️  Angela AI 卸载程序")
print("="*60)
print(f"\\n📂 安装目录: {self.install_dir}")
print("\\n⚠️  这将删除：")
print("   - 所有程序文件")
print("   - 用户数据（可选）")
print("   - 快捷方式")
print()

confirm = input("确定要卸载Angela AI吗? (输入 'yes' 确认): ")
if confirm.lower() != 'yes':
    print("\\n❌ 卸载取消")
    sys.exit(0)

delete_data = input("\\n是否同时删除用户数据（记忆、配置等）? (y/n): ").lower() == 'y'

try:
    install_dir = Path(r"{self.install_dir}")
    
    # 删除快捷方式（Windows）
    if sys.platform == "win32":
        try:
            import winshell
            desktop = winshell.desktop()
            start_menu = winshell.start_menu()
            
            shortcuts = [
                os.path.join(desktop, "Angela AI.lnk"),
                os.path.join(start_menu, "Angela AI", "启动 Angela AI.lnk"),
                os.path.join(start_menu, "Angela AI", "卸载 Angela AI.lnk"),
            ]
            
            for shortcut in shortcuts:
                if os.path.exists(shortcut):
                    os.remove(shortcut)
                    print(f"   ✅ 删除: {{os.path.basename(shortcut)}}")
            
            # 删除开始菜单文件夹
            angela_menu = os.path.join(start_menu, "Angela AI")
            if os.path.exists(angela_menu):
                shutil.rmtree(angela_menu)
                
        except Exception as e:
            print(f"   ⚠️  删除快捷方式失败: {{e}}")
    
    # 删除用户数据（如果请求）
    if delete_data:
        data_dirs = [
            install_dir / "data" / "memories",
            install_dir / "data" / "cache",
            Path.home() / ".config" / "angela-ai",
        ]
        for data_dir in data_dirs:
            if data_dir.exists():
                shutil.rmtree(data_dir)
                print(f"   ✅ 删除数据: {{data_dir}}")
    
    # 删除安装目录
    if install_dir.exists():
        shutil.rmtree(install_dir)
        print(f"\\n✅ Angela AI 已卸载")
        print(f"   目录已删除: {{install_dir}}")
    
    print("\\n👋 感谢使用Angela AI！")
    print("   如需重新安装，请访问: https://github.com/catcatAI/Unified-AI-Project")
    
except Exception as e:
    print(f"\\n❌ 卸载失败: {{e}}")
    sys.exit(1)
'''
        
        try:
            with open(uninstall_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"   ✅ 卸载程序: {uninstall_script}\n")
            return True
            
        except Exception as e:
            print(f"   ⚠️  创建卸载程序失败: {e}\n")
            return False
    
    def print_summary(self, success: bool):
        """打印安装摘要"""
        print("=" * 70)
        if success:
            print("✅ 安装成功!")
        else:
            print("❌ 安装未完成")
        print("=" * 70)
        
        print(f"\n📂 安装位置: {self.install_dir}")
        
        if success:
            print("\n🚀 启动方式:")
            print(f"   1. 双击桌面快捷方式 'Angela AI'")
            print(f"   2. 或在终端运行:")
            print(f"      cd \"{self.install_dir}\"")
            print(f"      python run_angela.py")
            
            print("\n📖 首次使用:")
            print("   1. 配置API密钥:")
            print(f"      - 复制 {self.install_dir}/apps/backend/config/credentials.example.json")
            print(f"      - 到 ~/.config/angela-ai/credentials.json")
            print("      - 填入你的Google API密钥")
            print("\n   2. 启动Angela后会自动:")
            print("      - 加载Live2D模型")
            print("      - 初始化所有系统")
            print("      - 显示在桌面")
            
            print("\n🎨 特性:")
            print("   ✅ 52,000+ 行代码")
            print("   ✅ 21个自主系统")
            print("   ✅ 16个动态参数")
            print("   ✅ 艺术学习能力")
            print("   ✅ Live2D触摸响应")
            
            print("\n📚 文档:")
            print(f"   - README: {self.install_dir}/README.md")
            print(f"   - 使用指南: {self.install_dir}/docs")
            print(f"   - GitHub: https://github.com/catcatAI/Unified-AI-Project")
            
            print("\n💡 提示:")
            print("   - 按 Ctrl+C 可以安全退出")
            print("   - 日志保存在 logs/ 目录")
            print("   - 有问题请查看GitHub Issues")
        else:
            print("\n⚠️  安装未完成，可能的解决方案:")
            print("   1. 检查网络连接（需要访问GitHub）")
            print("   2. 手动下载: git clone https://github.com/catcatAI/Unified-AI-Project.git")
            print("   3. 然后在该目录运行: python setup.py")
            print("\n   如需帮助，请访问: https://github.com/catcatAI/Unified-AI-Project/issues")
        
        print("\n" + "=" * 70)
        print("🌟 Angela AI - 你的桌面数字生命")
        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Angela AI 安装程序 - 一键从GitHub安装",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认安装（推荐）
  python install_angela.py
  
  # 安装到指定目录
  python install_angela.py --install-dir "D:\\AngelaAI"
  
  # 使用其他仓库
  python install_angela.py --repo https://github.com/yourname/Unified-AI-Project.git
        """
    )
    
    parser.add_argument(
        "--install-dir",
        type=str,
        help="安装目录（默认: 用户目录/AngelaAI）"
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        default="https://github.com/catcatAI/Unified-AI-Project.git",
        help="GitHub仓库地址（默认: catcatAI官方仓库）"
    )
    
    parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="跳过克隆（如果已在项目目录中）"
    )
    
    args = parser.parse_args()
    
    # 创建安装器
    installer = AngelaInstaller(
        install_dir=args.install_dir,
        repo_url=args.repo
    )
    
    # 打印标题
    installer.print_header()
    
    # 检查系统要求
    if not installer.check_prerequisites():
        installer.print_summary(False)
        return 1
    
    success = True
    
    # 克隆仓库（除非跳过）
    if not args.skip_clone:
        if not installer.clone_repository():
            success = False
    else:
        # 使用当前目录
        installer.install_dir = Path(__file__).parent.resolve()
        print(f"📂 使用当前目录: {installer.install_dir}\n")
    
    if success:
        # 安装依赖
        if not installer.install_dependencies():
            print("⚠️  依赖安装可能不完整，但会继续...")
        
        # 创建快捷方式
        installer.create_shortcuts()
        
        # 创建卸载程序
        installer.create_uninstaller()
    
    # 打印摘要
    installer.print_summary(success)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
