"""
System Tray Manager - Cross-Platform

Provides system tray icon with context menu for Angela AI.
Supports: Windows (pystray), macOS (rumps), Linux (AppIndicator)

Features:
- Show Angela status
- Mode switching (Lite/Standard/Extended)
- Key management GUI
- Settings/Configuration
- Exit
"""

import os
import sys
import platform
import logging
import threading
import asyncio
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TrayMenuItem:
    """Menu item definition"""

    label: str
    callback: Optional[Callable] = None
    checked: bool = False
    enabled: bool = True
    submenu: Optional[list] = None
    separator: bool = False


class BaseTrayManager:
    """Base class for system tray managers"""

    def __init__(self, angela_core=None):
        self.angela = angela_core
        self.icon = None
        self.menu = []
        self._callbacks: Dict[str, Callable] = {}

    def setup_menu(self) -> dict:
        """Setup menu structure - to be implemented by subclasses"""
        logger.warning("[BaseTrayManager.setup_menu] Not implemented — stub")
        return {"stub": True, "message": "setup_menu not implemented"}

    def show_notification(self, title: str, message: str) -> dict:
        """Show notification balloon"""
        logger.warning("[BaseTrayManager.show_notification] Not implemented — stub")
        return {"stub": True, "message": "show_notification not implemented"}

    def run(self) -> dict:
        """Run the tray manager"""
        logger.warning("[BaseTrayManager.run] Not implemented — stub")
        return {"stub": True, "message": "run not implemented"}

    def stop(self) -> dict:
        """Stop the tray manager"""
        logger.warning("[BaseTrayManager.stop] Not implemented — stub")
        return {"stub": True, "message": "stop not implemented"}


class WindowsTrayManager(BaseTrayManager):
    """Windows system tray implementation using pystray"""

    def __init__(self, angela_core=None):
        super().__init__(angela_core)
        self._tray_icon = None

    def setup_menu(self) -> None:
        """Setup Windows tray menu"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Create or load icon
            icon_path = Path(__file__).parent.parent.parent / "resources" / "angela_icon.png"
            if icon_path.exists():
                self.icon = Image.open(icon_path)
            else:
                # Generate default icon
                self.icon = self._create_default_icon()

            # Build menu
            menu_items = self._build_menu_items()

            self._tray_icon = pystray.Icon(
                "AngelaAI", self.icon, "Angela AI", menu=pystray.Menu(*menu_items)
            )

        except ImportError as e:
            logger.error(f"pystray not installed: {e}", exc_info=True)
            raise

    def _create_default_icon(self) -> str:
        """Create default Angela icon"""
        from PIL import Image, ImageDraw

        # Create a simple colored circle as icon
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)

        # Draw a nice gradient circle
        for i in range(width // 2, 0, -1):
            color = (
                int(255 * (1 - i / (width / 2))),
                int(100 + 155 * (1 - i / (width / 2))),
                int(200),
                255,
            )
            dc.ellipse(
                [width // 2 - i, height // 2 - i, width // 2 + i, height // 2 + i], fill=color
            )

        return image

    def _build_menu_items(self) -> str:
        """Build menu items for pystray"""
        import pystray

        items = [
            # Status
            pystray.MenuItem(
                lambda text: f"🎭 {self._get_status_text()}", lambda: None, enabled=False
            ),
            pystray.Menu.SEPARATOR,
            # Mode submenu
            pystray.MenuItem(
                "Switch Mode",
                pystray.Menu(
                    pystray.MenuItem(
                        lambda text: "✓ Lite" if self._get_current_mode() == "lite" else "  Lite",
                        lambda: self._switch_mode("lite"),
                    ),
                    pystray.MenuItem(
                        lambda text: (
                            "✓ Standard"
                            if self._get_current_mode() == "standard"
                            else "  Standard"
                        ),
                        lambda: self._switch_mode("standard"),
                    ),
                    pystray.MenuItem(
                        lambda text: (
                            "✓ Extended"
                            if self._get_current_mode() == "extended"
                            else "  Extended"
                        ),
                        lambda: self._switch_mode("extended"),
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            # Key management
            pystray.MenuItem("🔑 API Keys...", lambda: self._open_key_manager()),
            # Settings
            pystray.MenuItem("⚙️ Settings...", lambda: self._open_settings()),
            pystray.Menu.SEPARATOR,
            # Exit
            pystray.MenuItem("Exit Angela", lambda: self._exit()),
        ]

        return items

    def _get_status_text(self) -> str:
        """Get current status text"""
        if self.angela:
            mode = getattr(self.angela, "current_mode", "unknown")
            return f"Angela ({mode.title()})"
        return "Angela (Not connected)"

    def _get_current_mode(self) -> str:
        """Get current mode"""
        if self.angela:
            return getattr(self.angela, "current_mode", "standard")
        return "standard"

    def _switch_mode(self, mode: str) -> None:
        """Switch Angela mode"""
        logger.info(f"User requested mode switch to: {mode}")
        if self.angela and hasattr(self.angela, "switch_mode"):
            try:
                # Run in thread to avoid blocking tray
                threading.Thread(target=lambda: asyncio.run(self.angela.switch_mode(mode))).start()
                self.show_notification("Angela AI", f"Switching to {mode.title()} mode...")
            except Exception as e:  # broad exception acceptable: mode switching may fail with asyncio or callback errors
                logger.error(f"Error switching mode: {e}", exc_info=True)
                self.show_notification("Angela AI", f"Failed to switch mode: {e}")

    def _open_key_manager(self) -> None:
        """Open key management window"""
        logger.info("Opening key manager")
        try:
            # Launch key manager in separate process
            import subprocess

            script_path = Path(__file__).parent / "key_manager_gui.py"
            if script_path.exists():
                subprocess.Popen([sys.executable, str(script_path)])
            else:
                logger.warning("Key manager GUI script not found", exc_info=True)
                self.show_notification("Angela AI", "Key manager not yet implemented")
        except Exception as e:  # broad exception acceptable: key manager launch may fail with subprocess or file system errors
            logger.error(f"Error opening key manager: {e}", exc_info=True)

    def _open_settings(self) -> None:
        """Open settings window"""
        logger.info("Opening settings")
        try:
            import subprocess

            script_path = Path(__file__).parent / "settings_gui.py"
            if script_path.exists():
                subprocess.Popen([sys.executable, str(script_path)])
            else:
                logger.warning("Settings GUI script not found", exc_info=True)
                self.show_notification("Angela AI", "Settings GUI not yet implemented")
        except Exception as e:  # broad exception acceptable: settings GUI launch may fail with subprocess or file system errors
            logger.error(f"Error opening settings: {e}", exc_info=True)

    def _exit(self) -> None:
        """Exit Angela"""
        logger.info("User requested exit")
        if self.angela and hasattr(self.angela, "shutdown"):
            try:
                asyncio.run(self.angela.shutdown())
            except Exception as e:  # broad exception acceptable: shutdown may fail with asyncio or process termination errors
                logger.error(f"Error during shutdown: {e}", exc_info=True)

        if self._tray_icon:
            self._tray_icon.stop()

        sys.exit(0)

    def show_notification(self, title: str, message: str) -> None:
        """Show notification balloon"""
        if self._tray_icon:
            self._tray_icon.notify(message, title)

    def run(self) -> None:
        """Run the tray icon"""
        if self._tray_icon:
            self._tray_icon.run()

    def stop(self) -> None:
        """Stop the tray icon"""
        if self._tray_icon:
            self._tray_icon.stop()


class MacOSTrayManager(BaseTrayManager):
    """macOS menu bar implementation using rumps"""

    def __init__(self, angela_core=None):
        super().__init__(angela_core)
        self._app = None

    def setup_menu(self) -> None:
        """Setup macOS menu bar"""
        try:
            import rumps

            # Build menu
            menu_items = [
                rumps.MenuItem("Status", callback=None),
                None,  # Separator
                rumps.MenuItem("Switch Mode", callback=None),
                rumps.MenuItem("Lite", callback=lambda _: self._switch_mode("lite")),
                rumps.MenuItem("Standard", callback=lambda _: self._switch_mode("standard")),
                rumps.MenuItem("Extended", callback=lambda _: self._switch_mode("extended")),
                None,  # Separator
                rumps.MenuItem("API Keys...", callback=lambda _: self._open_key_manager()),
                rumps.MenuItem("Settings...", callback=lambda _: self._open_settings()),
                None,  # Separator
                rumps.MenuItem("Exit", callback=lambda _: self._exit()),
            ]

            self._app = rumps.App(
                "Angela AI",
                icon=str(Path(__file__).parent.parent.parent / "resources" / "angela_icon.png"),
                menu=menu_items,
            )

        except ImportError:
            logger.error("rumps not installed", exc_info=True)
            raise

    def _switch_mode(self, mode: str) -> None:
        """Switch mode"""
        logger.info(f"Switching to mode: {mode}")
        if self.angela and hasattr(self.angela, "switch_mode"):
            threading.Thread(target=lambda: asyncio.run(self.angela.switch_mode(mode))).start()
            rumps.notification("Angela AI", "Mode Switch", f"Switching to {mode.title()} mode...")

    def _open_key_manager(self) -> None:
        """Open key manager"""
        logger.info("Opening key manager")
        # Similar to Windows implementation

    def _open_settings(self) -> None:
        """Open settings"""
        logger.info("Opening settings")
        # Similar to Windows implementation

    def _exit(self) -> None:
        """Exit"""
        if self.angela and hasattr(self.angela, "shutdown"):
            asyncio.run(self.angela.shutdown())
        rumps.quit_application()

    def show_notification(self, title: str, message: str) -> None:
        """Show notification"""
        import rumps

        rumps.notification(title, "", message)

    def run(self) -> None:
        """Run the app"""
        if self._app:
            self._app.run()

    def stop(self) -> None:
        """Stop the app"""
        import rumps

        rumps.quit_application()


class LinuxTrayManager(BaseTrayManager):
    """Linux system tray using AppIndicator3 (GTK)"""

    def __init__(self, angela_core=None):
        super().__init__(angela_core)
        self._indicator = None

    def setup_menu(self) -> None:
        """Setup Linux system tray"""
        try:
            from gi.repository import Gtk, AppIndicator3

            # Create indicator
            self._indicator = AppIndicator3.Indicator.new(
                "AngelaAI", "angela-icon", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

            # Create menu
            menu = Gtk.Menu()

            # Status item
            item_status = Gtk.MenuItem(label="Angela AI - Ready")
            item_status.set_sensitive(False)
            menu.append(item_status)

            menu.append(Gtk.SeparatorMenuItem())

            # Mode submenu
            item_mode = Gtk.MenuItem(label="Switch Mode")
            submenu = Gtk.Menu()

            item_lite = Gtk.MenuItem(label="Lite")
            item_lite.connect("activate", lambda _: self._switch_mode("lite"))
            submenu.append(item_lite)

            item_standard = Gtk.MenuItem(label="Standard")
            item_standard.connect("activate", lambda _: self._switch_mode("standard"))
            submenu.append(item_standard)

            item_extended = Gtk.MenuItem(label="Extended")
            item_extended.connect("activate", lambda _: self._switch_mode("extended"))
            submenu.append(item_extended)

            item_mode.set_submenu(submenu)
            menu.append(item_mode)

            menu.append(Gtk.SeparatorMenuItem())

            # Settings
            item_keys = Gtk.MenuItem(label="API Keys...")
            item_keys.connect("activate", lambda _: self._open_key_manager())
            menu.append(item_keys)

            item_settings = Gtk.MenuItem(label="Settings...")
            item_settings.connect("activate", lambda _: self._open_settings())
            menu.append(item_settings)

            menu.append(Gtk.SeparatorMenuItem())

            # Exit
            item_exit = Gtk.MenuItem(label="Exit")
            item_exit.connect("activate", lambda _: self._exit())
            menu.append(item_exit)

            menu.show_all()
            self._indicator.set_menu(menu)

        except ImportError:
            logger.error("GTK3/GI not available", exc_info=True)
            raise

    def _switch_mode(self, mode: str) -> None:
        """Switch mode"""
        logger.info(f"Switching to mode: {mode}")
        if self.angela and hasattr(self.angela, "switch_mode"):
            threading.Thread(target=lambda: asyncio.run(self.angela.switch_mode(mode))).start()

    def _open_key_manager(self) -> None:
        """Open key manager"""
        logger.warning(f"{type(self).__name__}._open_key_manager not implemented")

    def _open_settings(self) -> None:
        """Open settings"""
        logger.warning(f"{type(self).__name__}._open_settings not implemented")

    def _exit(self) -> None:
        """Exit"""
        if self.angela and hasattr(self.angela, "shutdown"):
            asyncio.run(self.angela.shutdown())
        Gtk.main_quit()

    def show_notification(self, title: str, message: str) -> None:
        """Show notification"""
        try:
            from gi.repository import Notify

            Notify.init("Angela AI")
            notification = Notify.Notification.new(title, message, "dialog-information")
            notification.show()
        except (ImportError, AttributeError, Exception) as e:
            # 通知系統不可用，使用日志記錄
            logger.debug(f"通知顯示失敗（可忽略）: {e}")
            logger.info(f"通知: {title} - {message}")

    def run(self) -> None:
        """Run the tray"""
        from gi.repository import Gtk

        Gtk.main()

    def stop(self) -> None:
        """Stop the tray"""
        from gi.repository import Gtk

        Gtk.main_quit()


class AngelaTrayManager:
    """
    Unified Tray Manager - Factory pattern

    Automatically selects the appropriate platform-specific implementation
    """

    def __init__(self, angela_core=None):
        self.angela = angela_core
        self._manager: Optional[BaseTrayManager] = None
        self._init_manager()

    def _init_manager(self) -> None:
        """Initialize platform-specific manager"""
        system = platform.system()

        if system == "Windows":
            try:
                self._manager = WindowsTrayManager(self.angela)
                logger.info("Initialized Windows tray manager")
            except ImportError:
                logger.warning("pystray not available, falling back to console mode", exc_info=True)

        elif system == "Darwin":  # macOS
            try:
                self._manager = MacOSTrayManager(self.angela)
                logger.info("Initialized macOS tray manager")
            except ImportError:
                logger.warning("rumps not available, falling back to console mode", exc_info=True)

        else:  # Linux and others
            try:
                self._manager = LinuxTrayManager(self.angela)
                logger.info("Initialized Linux tray manager")
            except ImportError:
                logger.warning("GTK not available, falling back to console mode", exc_info=True)

    def setup(self) -> None:
        """Setup the tray menu"""
        if self._manager:
            self._manager.setup_menu()

    def run(self) -> None:
        """Run the tray manager"""
        if self._manager:
            self._manager.run()
        else:
            logger.warning("No tray manager available, running in console mode", exc_info=True)
            # Keep the program alive
            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Interrupted by user")

    def stop(self) -> None:
        """Stop the tray manager"""
        if self._manager:
            self._manager.stop()

    def notify(self, title: str, message: str) -> None:
        """Show notification"""
        if self._manager:
            self._manager.show_notification(title, message)



