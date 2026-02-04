#!/usr/bin/env python3
"""
Angela AI Uninstall Program
Angela AI 卸载程序

Modes:
  1. Light Uninstall  - Keep memories, personality, configs
  2. Full Uninstall   - Remove all data
  3. Selective        - Choose what to remove

Usage:
  python uninstall.py [--mode light|full|selective]
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


class AngelaUninstaller:
    def __init__(self, mode: str = "selective"):
        self.project_dir = Path(__file__).parent.resolve()
        self.mode = mode
        self.data_dirs = [
            self.project_dir / "data",
            self.project_dir / "logs",
            self.project_dir / "temp",
            self.project_dir / "cache",
        ]
        self.config_files = [
            self.project_dir / "config",
            self.project_dir / "angela_config.yaml",
        ]
        self.memory_files = [
            self.project_dir / "apps" / "backend" / "src" / "core" / "memories",
            self.project_dir / "apps" / "backend" / "src" / "core" / "personality",
        ]
        self.shortcuts = []
        self.backup_path = None

    def get_user_choice(self) -> str:
        print("\n" + "=" * 60)
        print("🗑️  Angela AI Uninstall Program / 卸载程序")
        print("=" * 60)
        print(f"\n📂 Project Directory: {self.project_dir}")
        print("\nSelect uninstall mode:")
        print("  1️⃣  Light Uninstall  - Keep memories, personality, configs")
        print("  2️⃣  Full Uninstall   - Remove ALL data (memories, configs, etc.)")
        print("  3️⃣  Selective        - Choose what to remove")
        print("  4️⃣  Backup First     - Backup before uninstalling")
        print("  5️⃣  Cancel           - Exit")
        print()
        choice = input("Enter choice (1-5): ").strip()
        return {"1": "light", "2": "full", "3": "selective", "4": "backup", "5": "cancel"}.get(choice, "cancel")

    def detect_shortcuts(self):
        if sys.platform == "win32":
            try:
                import winshell
                desktop = winshell.desktop()
                start_menu = winshell.start_menu()
                self.shortcuts = [
                    os.path.join(desktop, "Angela AI.lnk"),
                    os.path.join(start_menu, "Angela AI", "启动 Angela AI.lnk"),
                    os.path.join(start_menu, "Angela AI", "卸载 Angela AI.lnk"),
                ]
            except:
                pass

    def delete_shortcuts(self):
        if not self.shortcuts:
            self.detect_shortcuts()
        for shortcut in self.shortcuts:
            if os.path.exists(shortcut):
                try:
                    os.remove(shortcut)
                    print(f"  ✅ Deleted: {os.path.basename(shortcut)}")
                except Exception as e:
                    print(f"  ⚠️  Could not delete {shortcut}: {e}")

    def delete_start_menu_folder(self):
        if sys.platform == "win32":
            try:
                import winshell
                start_menu = winshell.start_menu()
                angela_folder = os.path.join(start_menu, "Angela AI")
                if os.path.exists(angela_folder):
                    shutil.rmtree(angela_folder)
                    print(f"  ✅ Deleted Start Menu folder")
            except:
                pass

    def backup_data(self) -> bool:
        print("\n📦 Creating backup...")
        self.backup_path = self.project_dir / "angela_backup"
        if self.backup_path.exists():
            print(f"  ⚠️  Backup already exists: {self.backup_path}")
            response = input("  Overwrite? (y/n): ").lower().strip()
            if response != 'y':
                self.backup_path = None
                return False
            shutil.rmtree(self.backup_path)

        try:
            dirs_to_backup = ["data", "apps/backend/src/core/memories", "apps/backend/src/core/personality"]
            for d in dirs_to_backup:
                src = self.project_dir / d
                if src.exists():
                    dst = self.backup_path / d
                    shutil.copytree(src, dst)
                    print(f"  ✅ Backed up: {d}")

            files_to_backup = ["config", "angela_config.yaml"]
            for f in files_to_backup:
                src = self.project_dir / f
                if src.exists() and src.is_file():
                    dst = self.backup_path / f
                    shutil.copy2(src, dst)
                    print(f"  ✅ Backed up: {f}")

            print(f"\n📁 Backup saved to: {self.backup_path}")
            return True
        except Exception as e:
            print(f"  ❌ Backup failed: {e}")
            self.backup_path = None
            return False

    def show_selective_menu(self):
        print("\n" + "=" * 60)
        print("📋 Selective Uninstall")
        print("=" * 60)
        print("\nSelect items to remove (y/n):")
        items = [
            ("data/", "All application data (memories, cache, logs)"),
            ("logs/", "Log files"),
            ("temp/", "Temporary files"),
            ("config/", "Configuration files"),
            ("apps/backend/src/core/memories/", "Memory files"),
            ("apps/backend/src/core/personality/", "Personality files"),
            ("Desktop shortcuts", "Desktop shortcut"),
            ("Start Menu", "Start Menu entries"),
        ]
        selected = {}
        for i, (name, desc) in enumerate(items, 1):
            response = input(f"  {i}. {name:<30} ({desc}) [y/n]: ").lower().strip()
            selected[name] = response == 'y'
        return selected

    def uninstall_light(self) -> bool:
        print("\n🟢 Light Uninstall (keeping memories and configs)...")
        print("  Items to delete:")
        print("    - Desktop shortcuts")
        print("    - Start Menu entries")
        print("    - Temporary files")

        self.delete_shortcuts()
        self.delete_start_menu_folder()

        temp_dirs = [self.project_dir / "temp", self.project_dir / "cache"]
        for d in temp_dirs:
            if d.exists():
                shutil.rmtree(d)
                print(f"  ✅ Deleted: {d.name}")

        print("\n✅ Light uninstall complete!")
        print(f"   Memories and configs preserved at: {self.project_dir}")
        return True

    def uninstall_full(self) -> bool:
        print("\n🔴 Full Uninstall (removing ALL data)...")
        print("  ⚠️  WARNING: This will delete ALL data including:")
        print("     - All memories")
        print("     - Personality settings")
        print("     - Configuration files")
        print("     - All application data")
        print()

        confirm = input("Type 'yes' to confirm full uninstall: ").strip()
        if confirm.lower() != 'yes':
            print("   Cancelled.")
            return False

        self.delete_shortcuts()
        self.delete_start_menu_folder()

        for d in self.data_dirs:
            if d.exists():
                shutil.rmtree(d)
                print(f"  ✅ Deleted: {d.name}")

        for f in self.config_files:
            if f.exists():
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    os.remove(f)
                print(f"  ✅ Deleted: {f.name}")

        for d in self.memory_files:
            if d.exists():
                shutil.rmtree(d)
                print(f"  ✅ Deleted: {d.name}")

        if self.project_dir.exists():
            try:
                remaining = list(self.project_dir.iterdir())
                if not any(f for f in remaining if not f.name.startswith(".")):
                    print(f"\n   Project directory is empty, you may delete it manually:")
                    print(f"   {self.project_dir}")
            except:
                pass

        print("\n✅ Full uninstall complete!")
        print("   All data has been deleted.")
        return True

    def uninstall_selective(self, selected: dict) -> bool:
        print("\n🔵 Selective Uninstall...")
        self.delete_shortcuts()
        self.delete_start_menu_folder()

        if selected.get("data/"):
            for d in self.data_dirs:
                if d.exists():
                    shutil.rmtree(d)
                    print(f"  ✅ Deleted: {d.name}")

        if selected.get("logs/"):
            logs = self.project_dir / "logs"
            if logs.exists():
                shutil.rmtree(logs)
                print(f"  ✅ Deleted: logs/")

        if selected.get("temp/"):
            temp = self.project_dir / "temp"
            if temp.exists():
                shutil.rmtree(temp)
                print(f"  ✅ Deleted: temp/")

        if selected.get("config/"):
            for f in self.config_files:
                if f.exists():
                    if f.is_dir():
                        shutil.rmtree(f)
                    else:
                        os.remove(f)
                    print(f"  ✅ Deleted: {f.name}")

        if selected.get("apps/backend/src/core/memories/"):
            mem = self.project_dir / "apps" / "backend" / "src" / "core" / "memories"
            if mem.exists():
                shutil.rmtree(mem)
                print(f"  ✅ Deleted: memories/")

        if selected.get("apps/backend/src/core/personality/"):
            pers = self.project_dir / "apps" / "backend" / "src" / "core" / "personality"
            if pers.exists():
                shutil.rmtree(pers)
                print(f"  ✅ Deleted: personality/")

        print("\n✅ Selective uninstall complete!")
        return True

    def run(self):
        mode = self.mode

        if mode == "selective":
            mode = self.get_user_choice()

        if mode == "cancel":
            print("\n👋 Cancelled.")
            return 0

        if mode == "backup":
            self.backup_data()
            return 0

        success = False
        if mode == "light":
            success = self.uninstall_light()
        elif mode == "full":
            success = self.uninstall_full()
        elif mode == "selective":
            selected = self.show_selective_menu()
            success = self.uninstall_selective(selected)

        if success:
            print("\n" + "=" * 60)
            print("👋 Thank you for using Angela AI!")
            print("   To reinstall, visit: https://github.com/catcatAI/Unified-AI-Project")
            print("=" * 60)

        return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        description="Angela AI Uninstall Program",
        epilog="""
Examples:
  python uninstall.py                    # Interactive mode
  python uninstall.py --mode light       # Keep memories
  python uninstall.py --mode full        # Remove everything
  python uninstall.py --mode selective    # Choose what to remove
  python uninstall.py --mode backup      # Backup first
        """
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["light", "full", "selective", "backup"],
        default="selective",
        help="Uninstall mode (default: selective)"
    )
    args = parser.parse_args()

    uninstaller = AngelaUninstaller(mode=args.mode)
    return uninstaller.run()


if __name__ == "__main__":
    sys.exit(main())
