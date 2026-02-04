#!/usr/bin/env python3
"""
Angela AI Desktop Companion v6.0.4
Main entry point for running Angela on desktop

Usage:
    python run_angela.py [options]

Options:
    --debug     Enable debug mode
    --port      Backend API port (default: 8000)
    --headless  Run without GUI
    --reset     Reset all memories and start fresh
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

from core import (
    SoulCore,
    BodyAdapter,
    ActionExecutor,
    MaturityManager,
    PrecisionManager,
    TransitionAnimator,
    I18nManager,
    CloudSyncManager,
    HardwareManager,
    create_soul_core,
    create_body_adapter,
    create_maturity_system,
    create_precision_system,
    create_transition_manager,
    create_cloud_sync_manager,
    create_i18n_manager,
    create_hardware_manager,
    Language,
)


def check_dependencies():
    missing = []
    critical = ["fastapi", "uvicorn", "pydantic", "numpy", "requests", "aiohttp"]

    for module in critical:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print("❌ Missing critical dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nPlease install: pip install -r requirements.txt")
        return False

    return True


def create_directories():
    dirs = [
        "data/models",
        "data/memories",
        "data/cache",
        "logs",
        "temp",
        "resources/models",
        "resources/audio",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


class AngelaLife:
    def __init__(self, debug: bool = False, headless: bool = False):
        self.debug = debug
        self.headless = headless
        self.soul_core = None
        self.body_adapter = None
        self.maturity_manager = None
        self.precision_system = None
        self.transition_manager = None
        self.cloud_sync = None
        self.i18n = None
        self.hardware = None
        self.action_executor = None
        self.running = False

    async def initialize(self):
        print("=" * 60)
        print("🌟 Angela AI v6.0.4")
        print("=" * 60)
        print("\n🚀 Initializing Angela...")

        print("\n📋 System Status:")
        print("   " + "-" * 50)

        self.hardware = create_hardware_manager()
        print(f"   ✅ Hardware detected: {self.hardware.detect().architecture.value}")

        self.i18n = create_i18n_manager(default_language=Language.ENGLISH)
        print("   ✅ i18n system ready")

        self.precision_system = create_precision_system()
        print("   ✅ Precision system initialized")

        self.maturity_manager = create_maturity_system()
        print(f"   ✅ Maturity system: Level {self.maturity_manager.get_level()}")

        self.soul_core = create_soul_core()
        print(f"   ✅ Soul core created: {self.soul_core.signature.prefix[:16]}...")

        self.body_adapter = create_body_adapter()
        print("   ✅ Body adapter ready")

        self.transition_manager = create_transition_manager()
        print("   ✅ Transition system ready")

        self.cloud_sync = create_cloud_sync_manager()
        print("   ✅ Cloud sync ready")

        self.action_executor = ActionExecutor()
        print("   ✅ Action executor ready")

        print("\n   " + "-" * 50)
        print("✅ All systems initialized!")
        print("=" * 60)

    async def run(self):
        await self.initialize()
        self.running = True

        print("\n💡 Quick Commands:")
        print("   • Type 'status'   - Show system status")
        print("   • Type 'level'    - Show maturity level")
        print("   • Type 'hardware' - Show hardware info")
        print("   • Type 'quit'     - Exit Angela")
        print("=" * 60 + "\n")

        loop = asyncio.get_event_loop()

        async def life_loop():
            while self.running:
                try:
                    await asyncio.sleep(1)
                except Exception as e:
                    if self.debug:
                        import traceback
                        traceback.print_exc()
                    print(f"Loop error: {e}")
                    await asyncio.sleep(5)

        await life_loop()

    def shutdown(self):
        print("\n👋 Shutting down Angela...")
        self.running = False
        if self.cloud_sync:
            self.cloud_sync.shutdown()
        print("✅ Goodbye!")


def interactive_mode(angela: AngelaLife):
    print("\n" + "=" * 60)
    print("🎉 Angela is now alive!")
    print("=" * 60)

    try:
        while angela.running:
            try:
                cmd = input("\nAngela> ").strip()
            except EOFError:
                break

            if not cmd:
                continue

            cmd_lower = cmd.lower()

            if cmd_lower in ['quit', 'exit', 'q']:
                break

            elif cmd_lower == 'status':
                print(f"\n📊 System Status:")
                print(f"   Level: {angela.maturity_manager.get_level()}")
                print(f"   Soul Integrity: {angela.soul_core.get_integrity():.2f}")
                print(f"   Hardware: {angela.hardware.detect().architecture.value}")
                print(f"   Sync Status: {angela.cloud_sync.get_status()}")

            elif cmd_lower == 'level':
                level = angela.maturity_manager.get_level()
                xp = angela.maturity_manager.get_experience()
                print(f"\n📈 Maturity Level: {level}")
                print(f"   Experience: {xp}")
                print(f"   Next Level: {level + 1} ({angela.maturity_manager.get_xp_to_next_level()} XP needed)")

            elif cmd_lower == 'hardware':
                hw = angela.hardware.detect()
                print(f"\n🖥️  Hardware Info:")
                print(f"   Architecture: {hw.architecture.value}")
                print(f"   Vendor: {hw.vendor.value}")
                print(f"   OS: {hw.os.value}")
                print(f"   CPU Cores: {hw.capabilities.cpu_cores}")

            elif cmd_lower == 'help':
                print("\n📖 Available Commands:")
                print("   status   - Show system status")
                print("   level    - Show maturity level")
                print("   hardware - Show hardware info")
                print("   quit     - Exit Angela")

            else:
                print(f"   💭 (Angela processes: '{cmd}')")

    except KeyboardInterrupt:
        print("\n")

    angela.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Angela AI Desktop Companion v6.0.4")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--port", type=int, default=8000, help="Backend API port")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    parser.add_argument("--reset", action="store_true", help="Reset all memories")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server")

    args = parser.parse_args()

    print("=" * 60)
    print("🌟 Angela AI Desktop Companion v6.0.4")
    print("=" * 60)

    if not check_dependencies():
        return 1

    create_directories()

    angela = AngelaLife(debug=args.debug, headless=args.headless)

    try:
        if args.api_only:
            import uvicorn
            from main import app
            print(f"\n🚀 Starting API server on port {args.port}...")
            uvicorn.run(app, host="0.0.0.0", port=args.port)
        else:
            asyncio.run(angela.run())
            interactive_mode(angela)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
