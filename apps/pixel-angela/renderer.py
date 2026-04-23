import sys
import numpy as np
import ctypes
import json
import asyncio
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRect, QPoint, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QGuiApplication, QImage
import websockets

from ui_config import UIConfig
from dna_body import AngelaDNA

def make_window_transparent(hwnd):
    margins = (ctypes.c_int * 4)(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, margins)

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
            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError, Exception) as e:
                print(f"🔄 [Network] Connection lost: {e}. Retrying in {UIConfig.WS_RECONNECT_DELAY}s...")
                time.sleep(UIConfig.WS_RECONNECT_DELAY)

    async def _listen(self):
        async with websockets.connect("ws://127.0.0.1:8000/ws", open_timeout=30) as ws:
            print("🟢 [Network] Connection established.")
            self.ws = ws
            while self._running:
                msg = await ws.recv()
                self.state_updated.emit(json.loads(msg))

    async def send_msg(self, text):
        if hasattr(self, 'ws'):
            payload = {
                "type": "chat_message",
                "data": {
                    "content": text,
                    "user_name": "User",
                    "timestamp": datetime.now().isoformat()
                }
            }
            await self.ws.send(json.dumps(payload))

class AngelaRenderer(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {"stress": 0.0, "emotion": "neutral"}
        self.bubble_stack = []
        self.dna = AngelaDNA()
        self.breath_phase = 0.0
        
        # 1. 幾何校準
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.screen_w, self.screen_h = screen.width(), screen.height()
        self.ground_y = screen.y() + screen.height() - UIConfig.ANGELA_HEIGHT
        
        # 2. 視窗設置 (全螢幕透明)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        hwnd = int(self.winId())
        make_window_transparent(hwnd)
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        
        # 3. 初始座標
        self.angela_pos = QPointF(200, self.ground_y)
        self.target_pos = QPointF(200, self.ground_y)
        self.current_y = self.ground_y
        
        # 4. 服務啟動
        self.client = AngelaClient()
        self.client.state_updated.connect(self.update_state)
        self.client.start()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.physics_and_render_loop)
        self.timer.start(UIConfig.RENDER_INTERVAL)

    def update_state(self, new_state):
        msg_type = new_state.get("type")
        if msg_type == "state_update":
            data = new_state.get("data", {})
            if "gamma" in data: self.state["emotion"] = data["gamma"].get("emotion", "neutral")
            if "alpha" in data: self.state["stress"] = data["alpha"].get("stress", 0.0)
            if "spatial" in data: self.target_pos.setX(float(data["spatial"].get("x", self.angela_pos.x())))
        elif msg_type == "biological_feedback":
            reflex = new_state.get("reflex", {})
            expr = reflex.get("expression", self.state["emotion"])
            self.state["emotion"] = expr
            self.add_new_bubble(f"({expr}!)", "Angela")
        self.update()

    def add_new_bubble(self, text, origin):
        new_bubble = {
            "text": text,
            "origin": origin,
            "current_pos": QPointF(self.angela_pos.x(), self.current_y)
        }
        self.bubble_stack.append(new_bubble)
        if len(self.bubble_stack) > 3: self.bubble_stack.pop(0)

    def physics_and_render_loop(self):
        # 1. 呼吸動畫 (正弦波)
        self.breath_phase += 0.1
        breath_offset = np.sin(self.breath_phase) * 3.0
        self.current_y = self.ground_y + breath_offset

        # 2. 水平座標追隨
        dx = (self.target_pos.x() - self.angela_pos.x()) * 0.2
        self.angela_pos.setX(self.angela_pos.x() + dx)
        
        # 3. 氣泡追隨
        for bubble in self.bubble_stack:
            target_bubble_x = self.angela_pos.x() + (UIConfig.ANGELA_WIDTH // 2)
            target_bubble_y = self.current_y - 40
            diff = QPointF(target_bubble_x, target_bubble_y) - bubble["current_pos"]
            bubble["current_pos"] += diff * 0.1
        self.update()

    def mousePressEvent(self, event):
        p = event.position()
        if QRect(int(self.angela_pos.x()), int(self.current_y), UIConfig.ANGELA_WIDTH, UIConfig.ANGELA_HEIGHT).contains(int(p.x()), int(p.y())):
            self.show_native_input()

    def show_native_input(self):
        self.input_win = QWidget()
        self.input_win.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.input_win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.input_win.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled)
        layout = QVBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("輸入訊息...")
        self.entry.setStyleSheet("background: white; color: black; border: 2px solid #2A4B8C; border-radius: 8px; padding: 8px; font-weight: bold;")
        self.entry.returnPressed.connect(self.confirm_user_input)
        layout.addWidget(self.entry)
        self.input_win.setLayout(layout)
        self.input_win.move(int(self.angela_pos.x() - 50), int(self.current_y - 70))
        self.input_win.show()
        self.input_win.activateWindow()
        self.entry.setFocus()

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
        
        ax = int(self.angela_pos.x())
        ay = int(self.current_y)
        
        # 1. 獲取 DNA 與生物狀態
        pixel_data = self.dna.get_render_ready_matrix()
        h, w, c = pixel_data.shape
        emotion = self.state.get("emotion", "neutral")
        stress = self.state.get("stress", 0.0)
        
        # 2030 細節：根據生物狀態進行「濾鏡級」處理
        if emotion == "pained" or stress > 0.8:
            # 痛覺/極高壓：矩陣整體泛紅
            pixel_data[:, :, 0] = np.clip(pixel_data[:, :, 0] * 1.5, 0, 255)
        
        qimg = QImage(pixel_data.data, w, h, w * c, QImage.Format.Format_RGB888)
        painter.drawImage(ax, ay, qimg)
        
        # 2030 細節：流汗模擬 (像素液滴)
        if stress > 0.7:
            painter.setBrush(QColor(100, 200, 255, 180)) # 淡藍色汗水
            import random
            for _ in range(3):
                px = ax + random.randint(10, UIConfig.ANGELA_WIDTH - 10)
                py = ay + random.randint(50, 150)
                painter.drawRect(px, py, 4, 8)

        # 2. 氣泡渲染
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
            painter.setBrush(bg_color)
            painter.drawRoundedRect(QRect(bx, by, bw, bh), UIConfig.BUBBLE_CORNER_RADIUS, UIConfig.BUBBLE_CORNER_RADIUS)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, bubble["text"])
            offset_y += bh + 10

if __name__ == "__main__":
    app = QApplication(sys.argv)
    renderer = AngelaRenderer()
    renderer.show()
    sys.exit(app.exec())
