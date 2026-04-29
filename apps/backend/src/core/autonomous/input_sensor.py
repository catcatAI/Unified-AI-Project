import logging
import time
import threading
from pynput import mouse, keyboard
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GlobalInputSensor:
    """
    Angela 的全域活動感測器 (2030 Standard).
    負責監聽用戶活躍度節律與應用環境，並將其注入生物與意識流。
    """
    def __init__(self, user_monitor=None):
        self.user_monitor = user_monitor
        self.last_activity_time = time.time()
        self.activity_count = 0
        self.running = False
        
        self.mouse_listener = None
        self.key_listener = None
        
        # 2030 Standard: OS Bridge Integration
        from integrations.os_bridge_adapter import OSBridgeAdapter
        self.os_bridge = OSBridgeAdapter()
        
        # 活躍度與環境分析
        self.active_category = "neutral"
        self.active_window_title = ""
        self._lock = threading.Lock()
        
        # 類別映射表 (Category Mapping)
        self.category_map = {
            "gaming": ["steam", "game", "unity", "genshin", "minecraft", "overwatch"],
            "coding": ["vscode", "visual studio", "intellij", "pycharm", "github", "powershell", "cmd", "terminal"],
            "media": ["youtube", "netflix", "spotify", "vlc", "player"],
            "social": ["discord", "telegram", "whatsapp", "line", "messenger", "slack"],
            "browsing": ["chrome", "edge", "firefox", "safari", "google"]
        }

    def _on_activity(self, *args):
        """通用活動回饋"""
        with self._lock:
            self.last_activity_time = time.time()
            self.activity_count += 1
        
        if self.user_monitor:
            # 2030 Standard: Real-time user presence pulse
            self.user_monitor.record_input("[Hardware Pulse]", {"type": "activity_event"})

    def start(self):
        if self.running: return
        self.running = True
        
        # 啟動非阻塞監聽
        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity, 
            on_click=self._on_activity, 
            on_scroll=self._on_activity
        )
        self.key_listener = keyboard.Listener(on_press=self._on_activity)
        
        self.mouse_listener.start()
        self.key_listener.start()
        
        logger.info("📡 [Sensory] Global Input Sensor active. Angela is feeling your pace.")

    def stop(self):
        self.running = False
        if self.mouse_listener: self.mouse_listener.stop()
        if self.key_listener: self.key_listener.stop()

    def sniff_environment(self):
        """
        [N.6.1] 嗅探環境：識別用戶目前所在的應用類別。
        這將直接影響 Angela 的生物平衡。
        """
        summary = self.os_bridge.get_summary()
        if summary.get("status") == "success":
            active_info = summary.get("active_window", {})
            title = active_info.get("title", "").lower()
            
            with self._lock:
                self.active_window_title = title
                # 識別類別
                found_category = "neutral"
                for category, keywords in self.category_map.items():
                    if any(kw in title for kw in keywords):
                        found_category = category
                        break
                self.active_category = found_category
                
            logger.debug(f"🔍 [Sensory] Sniffed environment: {self.active_category} ({title[:30]}...)")

    def get_activity_metrics(self) -> Dict[str, Any]:
        """獲取目前的活躍度指標與環境氣氛，供大腦與心跳查詢"""
        with self._lock:
            elapsed = time.time() - self.last_activity_time
            # 修正計算：使用滾動視窗或防抖動處理
            bpm = (self.activity_count / max(1, elapsed)) * 60.0 # 動作頻率
            
            return {
                "seconds_since_last_input": elapsed,
                "input_density_bpm": bpm,
                "is_user_active": elapsed < 300, # 5分鐘判定
                "active_category": self.active_category,
                "window_title": self.active_window_title
            }
