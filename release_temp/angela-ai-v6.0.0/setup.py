"""
Angela AI Setup and Installation Script

Creates Windows installer with:
- Desktop shortcut
- Start menu entry
- System tray icon
- Auto-start on boot (optional)
- File associations (optional)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import argparse


class AngelaInstaller:
    """Angela AI Installation Manager"""
    
    def __init__(self, install_dir: Optional[str] = None):
        self.install_dir = install_dir or self._get_default_install_dir()
        self.source_dir = Path(__file__).parent.parent.parent  # apps/backend
        self.resources_dir = Path(__file__).parent / "resources"
        
    def _get_default_install_dir(self) -> str:
        """Get default installation directory"""
        if sys.platform == "win32":
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "AngelaAI")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Applications/AngelaAI")
        else:
            return os.path.expanduser("~/.local/share/angela-ai")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 9):
            print("❌ Python 3.9+ required")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print("✅ pip available")
        except:
            print("❌ pip not available")
            return False
        
        # Check Git (optional)
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print("✅ Git available")
        except:
            print("⚠️  Git not found (optional)")
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("\n📦 Installing dependencies...")
        
        requirements_file = self.source_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
        
        try:
            # Install main requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file),
                "--user", "--upgrade"
            ], check=True)
            
            # Install optional audio dependencies
            print("🎵 Installing audio dependencies...")
            audio_deps = [
                "pyaudio", "sounddevice", "pydub", "edge-tts", "pyttsx3",
                "faster-whisper", "SpeechRecognition", "pygame"
            ]
            
            for dep in audio_deps:
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", dep, "--user"
                    ], check=True, capture_output=True)
                    print(f"  ✅ {dep}")
                except:
                    print(f"  ⚠️  {dep} (optional, failed)")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def copy_files(self) -> bool:
        """Copy application files"""
        print(f"\n📂 Copying files to {self.install_dir}...")
        
        try:
            os.makedirs(self.install_dir, exist_ok=True)
            
            # Copy source code
            src_backend = self.source_dir
            dst_backend = Path(self.install_dir) / "backend"
            
            if dst_backend.exists():
                shutil.rmtree(dst_backend)
            
            shutil.copytree(src_backend, dst_backend, 
                          ignore=shutil.ignore_patterns(
                              "__pycache__", "*.pyc", "*.pyo", ".git", ".env"
                          ))
            
            print(f"  ✅ Copied backend files")
            
            # Create necessary directories
            dirs_to_create = [
                "data/models",
                "data/memories",
                "data/cache",
                "logs",
                "temp",
                "resources/models",
                "resources/audio",
                "resources/images",
                "config"
            ]
            
            for dir_name in dirs_to_create:
                (Path(self.install_dir) / dir_name).mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Created {dir_name}/")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to copy files: {e}")
            return False
    
    def create_shortcuts(self) -> bool:
        """Create desktop and start menu shortcuts"""
        print("\n🎯 Creating shortcuts...")
        
        if sys.platform == "win32":
            return self._create_windows_shortcuts()
        elif sys.platform == "darwin":
            return self._create_macos_shortcuts()
        else:
            return self._create_linux_shortcuts()
    
    def _create_windows_shortcuts(self) -> bool:
        """Create Windows shortcuts"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            # Desktop shortcut
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Angela AI.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir}/backend/launcher.py"'
            shortcut.WorkingDirectory = self.install_dir
            shortcut.IconLocation = f"{self.install_dir}/resources/icon.ico"
            shortcut.save()
            
            print(f"  ✅ Desktop shortcut: {shortcut_path}")
            
            # Start Menu shortcut
            start_menu = winshell.start_menu()
            angela_folder = os.path.join(start_menu, "Angela AI")
            os.makedirs(angela_folder, exist_ok=True)
            
            shortcut_path = os.path.join(angela_folder, "Angela AI.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir}/backend/launcher.py"'
            shortcut.WorkingDirectory = self.install_dir
            shortcut.IconLocation = f"{self.install_dir}/resources/icon.ico"
            shortcut.save()
            
            print(f"  ✅ Start Menu shortcut")
            
            # Uninstaller shortcut
            shortcut_path = os.path.join(angela_folder, "Uninstall.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.install_dir}/uninstall.py"'
            shortcut.WorkingDirectory = self.install_dir
            shortcut.save()
            
            return True
            
        except ImportError:
            print("  ⚠️  pywin32 not installed, skipping shortcuts")
            return False
    
    def _create_macos_shortcuts(self) -> bool:
        """Create macOS aliases"""
        try:
            # Create Applications symlink
            app_path = os.path.expanduser("~/Applications/Angela AI")
            if os.path.exists(app_path):
                os.remove(app_path)
            os.symlink(self.install_dir, app_path)
            print(f"  ✅ Applications symlink: {app_path}")
            return True
        except Exception as e:
            print(f"  ⚠️  macOS shortcuts: {e}")
            return False
    
    def _create_linux_shortcuts(self) -> bool:
        """Create Linux .desktop files"""
        try:
            applications_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(applications_dir, exist_ok=True)
            
            desktop_file = os.path.join(applications_dir, "angela-ai.desktop")
            
            with open(desktop_file, 'w') as f:
                f.write(f"""[Desktop Entry]
Name=Angela AI
Comment=Your AI Desktop Companion
Exec={sys.executable} "{self.install_dir}/backend/launcher.py"
Icon={self.install_dir}/resources/icon.png
Type=Application
Terminal=false
Categories=AI;Companion;Desktop;
""")
            
            os.chmod(desktop_file, 0o755)
            print(f"  ✅ .desktop file: {desktop_file}")
            return True
            
        except Exception as e:
            print(f"  ⚠️  Linux shortcuts: {e}")
            return False
    
    def create_launcher(self) -> bool:
        """Create launcher script"""
        print("\n🚀 Creating launcher...")
        
        launcher_content = f'''#!/usr/bin/env python3
"""
Angela AI Launcher
Starts Angela on the desktop
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend", "src"))

from core.autonomous import AngelaDigitalLife
from core.autonomous import AngelaActionExecutor
from core.autonomous import create_live2d_manager
from core.autonomous import DesktopInteractionSystem
from core.autonomous import AudioIntegration
from core.autonomous import BrowserController
from core.autonomous import DesktopPresenceManager

def main():
    print("🌟 Starting Angela AI...")
    print("=" * 50)
    
    # Initialize all systems
    try:
        live2d = create_live2d_manager()
        print("✅ Live2D initialized")
        
        audio = AudioIntegration()
        print("✅ Audio system initialized")
        
        desktop = DesktopInteractionSystem()
        print("✅ Desktop interaction initialized")
        
        browser = BrowserController()
        print("✅ Browser controller initialized")
        
        # Create Angela
        angela = AngelaDigitalLife(
            window_handle=None,  # Will be set by Live2D window
            enable_wallpaper_mode=True
        )
        print("✅ Angela life system initialized")
        
        # Create action executor
        executor = AngelaActionExecutor(
            live2d_manager=live2d,
            desktop_interaction=desktop,
            audio_system=audio,
            browser_controller=browser
        )
        angela.action_executor = executor
        print("✅ Action executor connected")
        
        # Start desktop presence
        presence = DesktopPresenceManager(
            window_handle=live2d.window_handle if hasattr(live2d, 'window_handle') else None,
            enable_wallpaper_mode=True
        )
        print("✅ Desktop presence initialized")
        
        print("\\n" + "=" * 50)
        print("🎉 Angela is now alive on your desktop!")
        print("   She can:")
        print("   • Talk and sing with lip-sync")
        print("   • Organize your desktop files")
        print("   • Search the web for information")
        print("   • Respond to touches on her body")
        print("   • Change wallpapers and backgrounds")
        print("\\n   Right-click on her for options")
        print("   Say 'Hey Angela' to wake her up")
        print("=" * 50)
        
        # Run main loop
        import asyncio
        asyncio.run(life_loop(angela, executor, presence))
        
    except KeyboardInterrupt:
        print("\\n👋 Goodbye from Angela!")
    except Exception as e:
        print(f"\\n❌ Error: {{e}}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

async def life_loop(angela, executor, presence):
    """Main life loop"""
    import time
    
    while True:
        try:
            # Update biological systems
            angela.update(delta_time=1.0)
            
            # Update desktop presence
            presence.update()
            
            # Check for idle actions
            if angela.biological_system._calculate_wellbeing() > 0.7:
                # Happy - might sing or talk
                pass
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Loop error: {{e}}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    main()
'''
        
        launcher_path = Path(self.install_dir) / "backend" / "launcher.py"
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable on Unix
        if sys.platform != "win32":
            os.chmod(launcher_path, 0o755)
        
        print(f"  ✅ Launcher: {launcher_path}")
        return True
    
    def create_default_resources(self) -> bool:
        """Create default resource files"""
        print("\n🎨 Creating default resources...")
        
        # Create default icon (placeholder)
        icon_path = Path(self.install_dir) / "resources" / "icon.png"
        
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple Angela icon
            img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw a simple cute face
            draw.ellipse([30, 30, 226, 226], fill=(255, 182, 193, 255))  # Face
            draw.ellipse([70, 80, 110, 120], fill=(255, 255, 255, 255))  # Left eye white
            draw.ellipse([70, 80, 110, 120], fill=(0, 0, 0, 255))        # Left eye pupil
            draw.ellipse([146, 80, 186, 120], fill=(255, 255, 255, 255)) # Right eye white
            draw.ellipse([146, 80, 186, 120], fill=(0, 0, 0, 255))       # Right eye pupil
            draw.arc([80, 140, 176, 200], 0, 180, fill=(255, 105, 180, 255), width=5)  # Smile
            
            img.save(icon_path)
            print(f"  ✅ Default icon: {icon_path}")
            
        except ImportError:
            print(f"  ⚠️  PIL not available, skipping icon creation")
            # Create empty file as placeholder
            icon_path.touch()
        
        # Create default config
        config_path = Path(self.install_dir) / "config" / "angela_config.yaml"
        config_content = '''# Angela AI Configuration
name: Angela
version: 6.0.0

# Biological systems
biological:
  enable_endocrine: true
  enable_autonomic: true
  enable_neuroplasticity: true

# Desktop presence
desktop:
  wallpaper_mode: true
  enable_file_operations: true
  safety_confirm_delete: true

# Audio
audio:
  tts_engine: edge-tts  # or pyttsx3
  voice_emotion: neutral
  enable_speech_recognition: true
  microphone_device: default

# Live2D
live2d:
  model_path: resources/models/default
  enable_physics: true
  enable_lip_sync: true
  frame_rate: 60

# Browser
browser:
  default_engine: google
  headless_default: false
  enable_game_detection: true

# Personality
personality:
  autonomy_level: 0.8
  curiosity: 0.7
  social_drive: 0.8
'''
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"  ✅ Default config: {config_path}")
        
        return True
    
    def create_uninstaller(self) -> bool:
        """Create uninstaller script"""
        print("\n🗑️  Creating uninstaller...")
        
        uninstaller_content = f'''#!/usr/bin/env python3
"""
Angela AI Uninstaller
"""

import os
import sys
import shutil

install_dir = r"{self.install_dir}"

def uninstall():
    print("🗑️  Uninstalling Angela AI...")
    
    # Remove shortcuts
    if sys.platform == "win32":
        try:
            import winshell
            desktop = winshell.desktop()
            shortcut = os.path.join(desktop, "Angela AI.lnk")
            if os.path.exists(shortcut):
                os.remove(shortcut)
                print("✅ Removed desktop shortcut")
        except:
            pass
    
    # Remove installation directory
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
        print(f"✅ Removed {install_dir}")
    
    print("\\n👋 Angela AI has been uninstalled")
    input("Press Enter to exit...")

if __name__ == "__main__":
    uninstall()
'''
        
        uninstaller_path = Path(self.install_dir) / "uninstall.py"
        
        with open(uninstaller_path, 'w') as f:
            f.write(uninstaller_content)
        
        if sys.platform != "win32":
            os.chmod(uninstaller_path, 0o755)
        
        print(f"  ✅ Uninstaller: {uninstaller_path}")
        return True
    
    def install(self) -> bool:
        """Run full installation"""
        print("=" * 60)
        print("🌟 Angela AI Installer")
        print("=" * 60)
        print(f"\n📍 Install location: {self.install_dir}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met")
            return False
        
        # Install steps
        steps = [
            ("Installing dependencies", self.install_dependencies),
            ("Copying files", self.copy_files),
            ("Creating default resources", self.create_default_resources),
            ("Creating launcher", self.create_launcher),
            ("Creating shortcuts", self.create_shortcuts),
            ("Creating uninstaller", self.create_uninstaller),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*60}")
            if not step_func():
                print(f"\n❌ Failed at: {step_name}")
                return False
        
        # Success
        print("\n" + "=" * 60)
        print("🎉 Installation Complete!")
        print("=" * 60)
        print(f"\nAngela AI has been installed to:")
        print(f"  {self.install_dir}")
        print(f"\nStart Angela:")
        if sys.platform == "win32":
            print("  • Double-click 'Angela AI' on your desktop")
            print("  • Or find 'Angela AI' in Start Menu")
        else:
            print(f"  • Run: python3 {self.install_dir}/backend/launcher.py")
        print(f"\nRight-click Angela on your desktop for options!")
        print("=" * 60)
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Angela AI Installer")
    parser.add_argument("--dir", help="Installation directory")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall Angela")
    
    args = parser.parse_args()
    
    if args.uninstall:
        # Run uninstaller
        install_dir = args.dir or AngelaInstaller()._get_default_install_dir()
        uninstaller = os.path.join(install_dir, "uninstall.py")
        if os.path.exists(uninstaller):
            os.system(f'"{sys.executable}" "{uninstaller}"')
        else:
            print("❌ Angela AI not found")
    else:
        # Install
        installer = AngelaInstaller(install_dir=args.dir)
        success = installer.install()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
