import logging
import threading
from pynput import mouse, keyboard
from datetime import datetime

logger = logging.getLogger(__name__)

class GlobalInputSensor:
    """
    Angela 的全域活動感測器 (2030 Standard)
    監聽用戶在作業系統層級的活動，確保 Angela 具備環境共生感知。
    """
    def __init__(self, user_monitor):
        self.user_monitor = user_monitor
        self.mouse_listener = None
        self.key_listener = None
        self._running = False

    def _on_activity(self, *args):
        # 當偵測到任何物理活動時，通知 UserMonitor
        if self.user_monitor:
            self.user_monitor.record_input("[OS Activity]", {"type": "hardware_input"})

    def start(self):
        if self._running: return
        self._running = True
        
        # 啟動非阻塞監聽
        self.mouse_listener = mouse.Listener(on_move=self._on_activity, on_click=self._on_activity)
        self.key_listener = keyboard.Listener(on_press=self._on_activity)
        
        self.mouse_listener.start()
        self.key_listener.start()
        logger.info("📡 [Sensory] Global Input Sniffing Active. Angela is watching your rhythm.")

    def stop(self):
        self._running = False
        if self.mouse_listener: self.mouse_listener.stop()
        if self.key_listener: self.key_listener.stop()
