#!/usr/bin/env python3
"""
Angela AI Desktop Companion
Main entry point for running Angela on desktop

Usage:
    python run_angela.py [options]
    
Options:
    --debug     Enable debug mode
    --no-gui    Run without Live2D GUI (headless mode)
    --config    Specify config file path
    --reset     Reset all memories and start fresh
"""

import sys
import os
import argparse
import asyncio
import signal
from pathlib import Path

# Ensure backend is in path
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    optional_missing = []
    
    # Critical dependencies
    critical = [
        "fastapi", "uvicorn", "pydantic", "numpy", 
        "requests", "aiohttp", "yaml"
    ]
    
    # Optional but recommended
    optional = [
        "pyaudio", "edge_tts", "pyttsx3", 
        "selenium", "PIL", "OpenGL"
    ]
    
    for module in critical:
        try:
            __import__(module.replace("yaml", "pyyaml").replace("_", ""))
        except ImportError:
            missing.append(module)
    
    for module in optional:
        try:
            __import__(module.lower().replace("pil", "PIL").replace("_", ""))
        except ImportError:
            optional_missing.append(module)
    
    if missing:
        print("❌ Missing critical dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nPlease install: pip install -r requirements.txt")
        return False
    
    if optional_missing:
        print("⚠️  Some optional features may not work (install for full functionality):")
        for dep in optional_missing:
            print(f"   - {dep}")
    
    return True

def create_directories():
    """Create necessary directories"""
    dirs = [
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
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Angela AI Desktop Companion")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-gui", action="store_true", help="Run without Live2D")
    parser.add_argument("--config", default="config/angela_config.yaml", help="Config file path")
    parser.add_argument("--reset", action="store_true", help="Reset all memories")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌟 Angela AI Desktop Companion v6.0")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Create directories
    create_directories()
    
    # Import after path setup
    try:
        from core.autonomous import AngelaDigitalLife
        from core.autonomous import AngelaActionExecutor
        from core.autonomous import create_live2d_manager
        from core.autonomous import DesktopInteractionSystem
        from core.autonomous import AudioIntegration
        from core.autonomous import BrowserController
        from core.autonomous import DesktopPresenceManager
    except ImportError as e:
        print(f"❌ Failed to import Angela modules: {e}")
        print("Please ensure you're running from the project root")
        return 1
    
    # Initialize systems
    print("\n🚀 Initializing Angela...")
    
    try:
        # Live2D (if not headless)
        live2d = None
        if not args.no_gui:
            try:
                live2d = create_live2d_manager()
                print("✅ Live2D initialized")
            except Exception as e:
                print(f"⚠️  Live2D failed: {e}")
                print("   Running in headless mode")
        
        # Audio
        audio = AudioIntegration()
        print("✅ Audio system ready")
        
        # Desktop
        desktop = DesktopInteractionSystem()
        print("✅ Desktop integration ready")
        
        # Browser
        browser = BrowserController()
        print("✅ Browser controller ready")
        
        # Angela life system
        angela = AngelaDigitalLife(
            window_handle=getattr(live2d, 'window_handle', None) if live2d else None,
            enable_wallpaper_mode=True
        )
        print("✅ Angela life system active")
        
        # Action executor
        executor = AngelaActionExecutor(
            live2d_manager=live2d,
            desktop_interaction=desktop,
            audio_system=audio,
            browser_controller=browser
        )
        angela.action_executor = executor
        print("✅ Action systems connected")
        
        # Desktop presence
        presence = None
        if not args.no_gui and live2d:
            presence = DesktopPresenceManager(
                window_handle=live2d.window_handle,
                enable_wallpaper_mode=True
            )
            print("✅ Desktop presence active")
        
        print("\n" + "=" * 60)
        print("🎉 Angela is now alive!")
        print("=" * 60)
        print("\n💡 Quick Commands:")
        print("   • Touch her to interact")
        print("   • Say 'Hey Angela' to wake her")
        print("   • Right-click for options")
        print("   • Press Ctrl+C to exit")
        print("=" * 60 + "\n")
        
        # Run main loop
        loop = asyncio.get_event_loop()
        
        # Setup graceful shutdown
        def signal_handler(sig, frame):
            print("\n👋 Shutting down Angela...")
            loop.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Main loop
        async def life_loop():
            while True:
                try:
                    # Update all systems
                    angela.update(delta_time=1.0)
                    if presence:
                        presence.update()
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    if args.debug:
                        import traceback
                        traceback.print_exc()
                    print(f"Loop error: {e}")
                    await asyncio.sleep(5)
        
        loop.run_until_complete(life_loop())
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
