import sys
import numpy as np
import ctypes
import json
import asyncio
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QMenu, QSystemTrayIcon
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QGuiApplication, QImage, QIcon, QPixmap
import websockets

from ui_config import UIConfig
from dna_body import AngelaDNA

# 移除 make_window_transparent，因為在 Windows 11 下 DwmExtendFrameIntoClientArea 會產生額外的玻璃/黑色背景，
# 造成「兩個背景」的視覺異常。PyQt 的 WA_TranslucentBackground 已經足夠實現完全透明。

class AngelaClient(QThread):
    state_updated = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.event_loop = None
        self._running = True

    def run(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        while self._running:
            try:
                self.event_loop.run_until_complete(self._listen())
            except Exception as e:
                print(f"🔄 [Network] Reconnecting: {e}")
                time.sleep(UIConfig.WS_RECONNECT_DELAY)

    async def _listen(self):
        async with websockets.connect("ws://127.0.0.1:8000/ws", open_timeout=30) as ws:
            print("🟢 [Network] Connection established.")
            self.ws = ws
            asyncio.create_task(self._send_heartbeat())
            while self._running:
                msg = await ws.recv()
                self.state_updated.emit(json.loads(msg))

    async def _send_heartbeat(self):
        while self._running and hasattr(self, 'ws'):
            try:
                await self.ws.send(json.dumps({"type": "heartbeat"}))
                await asyncio.sleep(30)
            except: break

    async def send_msg(self, text):
        if hasattr(self, 'ws'):
            payload = {"type": "chat_message", "data": {"content": text, "user_name": "User"}}
            await self.ws.send(json.dumps(payload))



class AngelaRenderer(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {"stress": 0.0, "emotion": "neutral"}
        self.bubble_stack = []
        self.dna = AngelaDNA()
        self.breath_phase = 0.0
        
        # 1. 系統幾何
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.screen_w, self.screen_h = screen.width(), screen.height()
        self.ground_y = screen.y() + screen.height() - UIConfig.ANGELA_HEIGHT
        
        # 2. 全螢幕透明設置 (開啟點擊穿透)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        # 移除 WA_TransparentForMouseEvents，讓主視窗負責所有事件，
        # 依靠 Windows 預設的 alpha 通道穿透機制，達成「點擊透明處穿透」的效果！
        
        # 取消調用 DWM API，避免產生系統級的第二重背景
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        
        self.angela_pos = QPointF(200, self.ground_y)
        self.target_pos = QPointF(200, self.ground_y)
        self.current_y = self.ground_y
        
        self._init_system_tray()
        self._init_tiered_menu()
        
        self.client = AngelaClient()
        self.client.state_updated.connect(self.update_state)
        self.client.start()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.physics_and_render_loop)
        self.timer.start(UIConfig.RENDER_INTERVAL)

    def _init_system_tray(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setBrush(QColor(42, 75, 140)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(4, 4, 24, 24)
        p.setPen(QColor(255, 255, 255)); p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        p.end()
        self.tray.setIcon(QIcon(pixmap))
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _init_tiered_menu(self):
        self.menu = QMenu()
        ai = self.menu.addMenu("AI"); ai.addAction("LLM Control"); ai.addAction("RAG Knowledge")
        al = self.menu.addMenu("AL"); al.addAction("Bionics Dynamics"); al.addAction("Pixel Physics")
        soul = self.menu.addMenu("Soul"); soul.addAction("Angela Core")
        ui = self.menu.addMenu("UI"); ui.addAction("Default Render")
        self.menu.addSeparator()
        self.menu.addAction("Exit").triggered.connect(QApplication.instance().quit)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.show_native_input()

    def mousePressEvent(self, event):
        pos = event.position()
        ax, ay = int(self.angela_pos.x()), int(self.current_y)
        
        # 1. 座標轉換：計算相對於體素矩陣(128x384)的局部座標
        local_x = int(pos.x() - ax)
        local_y = int(pos.y() - ay)
        
        # 2. [Task N.9.3] 體素探針檢測 (Voxel Hit-Test)
        is_hit = False
        if 0 <= local_x < 128 and 0 <= local_y < 384:
            stiffness = self.dna.get_stiffness_at(local_x, local_y)
            if stiffness > 0:
                is_hit = True
                print(f"💖 [Tactile] Precision hit! Stiffness: {stiffness:.2f}")

        # 3. 處理交互
        if is_hit:
            if event.button() == Qt.MouseButton.LeftButton:
                self.add_new_bubble("(觸摸反應)", "Angela")
                # 發送觸覺事件到後端
                asyncio.run_coroutine_threadsafe(
                    self.client.ws.send(json.dumps({
                        "type": "tactile_event",
                        "data": {"x": local_x, "y": local_y, "stiffness": stiffness}
                    })), 
                    self.client.event_loop
                )
            elif event.button() == Qt.MouseButton.RightButton:
                self.menu.exec(event.globalPosition().toPoint())
        else:
            # 點擊了透明區域：手動轉發點擊事件，實現 Windows 穿透 (由 OS 處理)
            # 在 PyQt 中，如果我們不 accept 事件，它通常會自動傳給下層窗口
            event.ignore()

    def update_state(self, new_state):
        msg_type = new_state.get("type")
        if msg_type == "state_update":
            data = new_state.get("data", {})
            if "gamma" in data: self.state["emotion"] = data["gamma"].get("dominant_emotion", "neutral")
            if "alpha" in data: self.state["stress"] = data["alpha"].get("stress", 0.0)
            if "spatial" in data: 
                spatial = data["spatial"]
                self.target_pos.setX(float(spatial.get("x", self.angela_pos.x())))
                # 2030 Standard: Dynamic Posture Sync
                self.state["theta_matrix"] = spatial.get("posture", {}).get("theta_matrix")
                self.state["finger_matrix"] = spatial.get("posture", {}).get("finger_matrix")
        self.update()

    def add_new_bubble(self, text, origin):
        new_bubble = {"text": text, "origin": origin, "current_pos": QPointF(self.angela_pos.x(), self.current_y)}
        self.bubble_stack.append(new_bubble)
        if len(self.bubble_stack) > 3: self.bubble_stack.pop(0)

    def physics_and_render_loop(self):
        self.breath_phase += 0.1
        self.current_y = self.ground_y + np.sin(self.breath_phase) * 3.0
        dx = (self.target_pos.x() - self.angela_pos.x()) * 0.2
        self.angela_pos.setX(self.angela_pos.x() + dx)
        
        # [Task N.12.9/10] 驅動精細解剖動態 (脊椎與五指)
        self.dna.apply_dynamics(
            self.breath_phase, 
            theta_matrix=self.state.get("theta_matrix"),
            finger_matrix=self.state.get("finger_matrix")
        )
        
        for bubble in self.bubble_stack:
            target_bubble_x = self.angela_pos.x() + (UIConfig.ANGELA_WIDTH // 2)
            target_bubble_y = self.current_y - 40
            diff = QPointF(target_bubble_x, target_bubble_y) - bubble["current_pos"]
            bubble["current_pos"] += diff * 0.1
        self.update()

    def show_native_input(self):
        self.input_win = QWidget()
        self.input_win.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.input_win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.input_win.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
        layout = QVBoxLayout(); self.entry = QLineEdit()
        self.entry.setPlaceholderText("意識通訊中...")
        self.entry.setStyleSheet("background: white; color: black; border: 2px solid #2A4B8C; border-radius: 8px; padding: 8px; font-weight: bold;")
        self.entry.returnPressed.connect(self.confirm_user_input)
        layout.addWidget(self.entry); self.input_win.setLayout(layout)
        self.input_win.move(int(self.screen_w // 2 - 100), int(self.screen_h - 150))
        self.input_win.show(); self.input_win.activateWindow(); self.entry.setFocus()

    def confirm_user_input(self):
        text = self.entry.text().strip()
        if text:
            self.add_new_bubble(text, "Human")
            asyncio.run_coroutine_threadsafe(self.client.send_msg(text), self.client.event_loop)
        self.input_win.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        ax, ay = int(self.angela_pos.x()), int(self.current_y)
        pixel_data = self.dna.get_render_ready_matrix()
        h, w, c = pixel_data.shape
        # 新的 dna_body.py 支援透明描邊，回傳的陣列是 4 通道 (RGBA)
        # 所以這裡必須使用 Format_RGBA8888 來避免渲染錯位
        qimg = QImage(pixel_data.data, w, h, w * c, QImage.Format.Format_RGBA8888)
        painter.drawImage(ax, ay, qimg)
        
        offset_y = 0
        for bubble in reversed(self.bubble_stack):
            is_human = bubble["origin"] == "Human"
            bg_color = UIConfig.USER_BUBBLE_BG if is_human else UIConfig.ANGELA_BUBBLE_BG
            font = QFont()
            font.setWeight(UIConfig.USER_FONT_WEIGHT if is_human else UIConfig.ANGELA_FONT_WEIGHT)
            font.setUnderline(UIConfig.USER_UNDERLINE if is_human else UIConfig.ANGELA_UNDERLINE)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(bubble["text"])
            bw, bh = text_rect.width() + 24, text_rect.height() + 14
            bx, by = int(bubble["current_pos"].x() - (bw // 2)), int(bubble["current_pos"].y() - bh - offset_y)
            painter.setBrush(bg_color); painter.drawRoundedRect(QRect(bx, by, bw, bh), UIConfig.BUBBLE_CORNER_RADIUS, UIConfig.BUBBLE_CORNER_RADIUS)
            painter.setPen(QColor(0, 0, 0)); painter.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, bubble["text"])
            offset_y += bh + 10

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    renderer = AngelaRenderer()
    renderer.show()
    sys.exit(app.exec())
