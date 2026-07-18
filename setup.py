"""
Angela AI Setup Script - 直接安装版
Direct Installation Script

使用方法:
1. 将项目文件夹复制/移动到想要安装的位置
2. 在该目录下运行: python setup.py
3. 安装依赖并创建快捷方式

或者:
python setup.py --install-dir "C:/Path/To/Install"
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
import logging
logger = logging.getLogger(__name__)


def check_prerequisites() -> bool:
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 10):
        print("❌ 需要 Python 3.10+")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # 检查pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip 可用")
    except Exception:
        print("❌ pip 不可用")
        return False
    
    return True


def install_dependencies(project_dir: Path) -> bool:
    """安装依赖"""
    print("\n📦 安装依赖...")
    
    requirements_file = project_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ 找不到 requirements.txt: {requirements_file}")
        return False
    
    try:
        # 安装主依赖
        print("📥 正在安装依赖包（这可能需要几分钟）...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file),
            "--user", "--upgrade"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  安装警告: {result.stderr[:200]}")
            print("   继续尝试...")
        
        print("✅ 依赖安装完成")
        
        # 安装音频依赖（可选，但推荐）
        print("\n🎵 安装音频支持（可选）...")
        audio_deps = ["pyaudio", "sounddevice", "pydub", "edge-tts", "pyttsx3"]
        for dep in audio_deps:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep, "--user"
                ], check=True, capture_output=True)
                print(f"  ✅ {dep}")
            except Exception:
                print(f"  ⚠️  {dep} (可选，跳过)")
        
        return True
        
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def create_shortcuts(project_dir: Path) -> bool:
    """创建快捷方式"""
    print("\n🎯 创建快捷方式...")
    
    if sys.platform != "win32":
        print("⚠️  非Windows系统，跳过快捷方式创建")
        print("   您可以手动创建快捷方式指向: python run_angela.py")
        return True
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        # 桌面快捷方式
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Angela AI.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{project_dir / "run_angela.py"}"'
        shortcut.WorkingDirectory = str(project_dir)
        shortcut.Description = "Angela AI - Desktop Digital Life"
        shortcut.save()
        
        print(f"  ✅ 桌面快捷方式: {shortcut_path}")
        
        # 开始菜单快捷方式
        start_menu = winshell.start_menu()
        angela_folder = os.path.join(start_menu, "Angela AI")
        os.makedirs(angela_folder, exist_ok=True)
        
        shortcut_path = os.path.join(angela_folder, "启动 Angela AI.lnk")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{project_dir / "run_angela.py"}"'
        shortcut.WorkingDirectory = str(project_dir)
        shortcut.Description = "启动 Angela AI"
        shortcut.save()
        
        print("  ✅ 开始菜单快捷方式")
        
        return True
        
    except ImportError:
        print("⚠️  无法创建快捷方式（缺少 winshell）")
        print("   您可以手动创建快捷方式")
        return False
    except Exception as e:
        print(f"⚠️  创建快捷方式失败: {e}")
        return False


def main():
    """主安装流程"""
    parser = argparse.ArgumentParser(description="Angela AI 安装程序")
    parser.add_argument(
        "--install-dir", 
        type=str,
        help="安装目录（可选，默认使用当前目录）"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖安装（只创建快捷方式）"
    )
    parser.add_argument(
        "--skip-shortcuts",
        action="store_true",
        help="跳过快捷方式创建"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌟 Angela AI 安装程序")
    print("=" * 60)
    
    # 确定安装目录
    if args.install_dir:
        project_dir = Path(args.install_dir).resolve()
        if not project_dir.exists():
            print(f"❌ 目录不存在: {project_dir}")
            print("   请先将项目复制到该位置")
            return 1
    else:
        project_dir = Path(__file__).parent.resolve()
    
    print(f"\n📍 项目目录: {project_dir}")
    
    # 检查必要文件
    required_files = ["run_angela.py", "requirements.txt", "apps"]
    missing = [f for f in required_files if not (project_dir / f).exists()]
    if missing:
        print(f"❌ 缺少必要文件: {missing}")
        print("   请确保在正确的项目目录中运行")
        return 1
    
    # 检查系统要求
    if not check_prerequisites():
        return 1
    
    # 安装依赖
    if not args.skip_deps:
        if not install_dependencies(project_dir):
            print("\n⚠️ 依赖安装可能不完整，但会继续...")
    else:
        print("\n⏩ 跳过依赖安装")
    
    # 创建快捷方式
    if not args.skip_shortcuts:
        create_shortcuts(project_dir)
    else:
        print("\n⏩ 跳过快捷方式创建")
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 安装完成!")
    print("=" * 60)
    print(f"\n📂 项目位置: {project_dir}")
    print("\n🚀 启动方式:")
    print("   1. 双击桌面快捷方式 'Angela AI'")
    print(f"   2. 或在终端运行: cd \"{project_dir}\" && python run_angela.py")
    print("\n📖 更多信息:")
    print(f"   - README: {project_dir / 'README.md'}")
    print(f"   - 文档: {project_dir / 'docs'}")
    print("\n💡 提示:")
    print("   - 第一次启动需要配置API密钥（Google Drive等）")
    print("   - 查看 apps/backend/config/credentials.example.json")
    print("   - 复制到 ~/.config/angela-ai/credentials.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
