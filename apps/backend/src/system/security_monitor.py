"""
Angela AI v6.0 - Security & Communication Monitor
密鑰生成與加密通訊監控器

實現 A/B/C 密鑰體系：
- Key A: 後端控制密鑰 (Backend Control)
- Key B: 行動端通訊密鑰 (Mobile-Backend Comm)
- Key C: 桌面端/跨裝置同步密鑰 (Desktop/Sync)

包含系統匣監控功能，可常駐並啟停後端服務。
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
import pystray
from PIL import Image, ImageDraw

import subprocess
import sys

logger = logging.getLogger(__name__)

class ABCKeyManager:
    """A/B/C 密鑰管理器"""
    def __init__(self, key_dir: Optional[Path] = None):
        self.key_dir = key_dir or Path(__file__).parent.parent.parent / "data" / "security"
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.key_dir / "abc_keys.json"
        self.keys = self._load_or_generate_keys()

    def _load_or_generate_keys(self) -> Dict[str, str]:
        if self.key_file.exists():
            try:
                with open(self.key_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"讀取密鑰文件失敗: {e}")

        # 生成新密鑰
        keys = {
            "KeyA": Fernet.generate_key().decode(),
            "KeyB": Fernet.generate_key().decode(),
            "KeyC": Fernet.generate_key().decode(),
            "created_at": time.time()
        }
        
        with open(self.key_file, "w") as f:
            json.dump(keys, f, indent=4)
        
        logger.info(f"✅ 已生成全新 A/B/C 密鑰體系: {self.key_file}")
        return keys

    def get_key(self, name: str) -> str:
        return self.keys.get(name, "")

class SecurityTrayMonitor:
    """系統匣監控器：常駐並管理後端狀態"""
    def __init__(self, key_manager: ABCKeyManager):
        self.km = key_manager
        self.backend_process = None
        self.icon = None
        self._running = True
        self.backend_script = Path(__file__).parent.parent.parent / "main.py"

    def _create_image(self, width=64, height=64, color1='blue', color2='white'):
        # 創建一個簡單的 Angela 圖示
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill=color2)
        return image

    def on_start_backend(self):
        if self.backend_process and self.backend_process.poll() is None:
            logger.info("後端服務已在運行中。")
            return
        
        logger.info(f"正在啟動後端服務: {self.backend_script}")
        try:
            # 確保日誌目錄存在
            log_dir = self.backend_script.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "backend.log"
            
            # 使用當前 Python 解釋器執行 main.py
            # 改進：使用日誌文件並添加啟動檢查
            self.log_stream = open(log_file, "a", encoding="utf-8")
            
            self.backend_process = subprocess.Popen(
                [sys.executable, "-u", str(self.backend_script)], 
                cwd=str(self.backend_script.parent),
                stdout=self.log_stream,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # 啟動後等待一小段時間檢查是否立即崩潰
            time.sleep(2)
            if self.backend_process.poll() is not None:
                raise RuntimeError(f"進程啟動後立即退出，退出碼: {self.backend_process.poll()}")

            logger.info(f"✅ 後端服務已啟動 (PID: {self.backend_process.pid})")
            if self.icon:
                self.icon.notify(f"Angela 後端服務已啟動 (PID: {self.backend_process.pid})", "系統狀態")
        except Exception as e:
            logger.error(f"啟動後端服務失敗: {e}")
            if self.icon:
                self.icon.notify(f"啟動失敗: {e}", "錯誤")
            if self.backend_process:
                self.on_stop_backend()

    def on_stop_backend(self):
        if not self.backend_process:
            logger.info("後端服務未運行。")
            return
        
        poll = self.backend_process.poll()
        if poll is not None:
            logger.info(f"後端服務已處於停止狀態 (退出碼: {poll})")
            self.backend_process = None
            return

        logger.info(f"正在關閉後端服務 (PID: {self.backend_process.pid})...")
        try:
            # 在 Windows 上使用 taskkill 確保清理整個進程樹
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.backend_process.pid)], 
                             capture_output=True)
            else:
                self.backend_process.terminate()
                try:
                    self.backend_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.backend_process.kill()
            
            logger.info("✅ 後端服務已關閉")
            if self.icon:
                self.icon.notify("Angela 後端服務已停止", "系統狀態")
        except Exception as e:
            logger.error(f"關閉後端服務失敗: {e}")
        finally:
            if hasattr(self, 'log_stream') and self.log_stream:
                try:
                    self.log_stream.close()
                except:
                    pass
            self.backend_process = None

    def on_restart_backend(self):
        logger.info("正在重啟後端服務...")
        self.on_stop_backend()
        time.sleep(1)
        self.on_start_backend()

    def on_exit(self, icon, item):
        self.on_stop_backend()
        self._running = False
        icon.stop()

    def on_show_key_b(self, icon, item):
        key_b = self.km.get_key('KeyB')
        # 顯示更詳細的說明
        msg = f"行動端通訊密鑰 (Key B):\n{key_b}\n\n請在手機 App 設置中輸入此金鑰以啟用加密通訊。"
        icon.notify(msg, "Angela 安全金鑰")
        print("\n" + "="*50)
        print("📱 Angela Mobile Pairing Key (Key B)")
        print(f"Key: {key_b}")
        print("="*50 + "\n")

    def on_generate_qr(self, icon, item):
        try:
            import qrcode
            key_b = self.km.get_key('KeyB')
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(key_b)
            qr.make(fit=True)
            
            print("\n" + " " * 10 + "📱 SCAN TO PAIR MOBILE APP")
            # 在終端打印 QR Code
            qr.print_ascii(invert=True)
            print("\n" + " " * 10 + f"Key B: {key_b}\n")
            
            icon.notify("已在終端生成配對 QR Code", "Angela 行動端配對")
        except ImportError:
            icon.notify("請先安裝 qrcode 庫: pip install qrcode", "功能受限")
        except Exception as e:
            logger.error(f"生成 QR Code 失敗: {e}")

    def update_menu(self):
        def get_status():
            if self.backend_process:
                poll = self.backend_process.poll()
                if poll is None:
                    return "🟢 運行中"
                else:
                    return f"🔴 已停止 (代碼: {poll})"
            return "⚪ 未啟動"
        
        return pystray.Menu(
            pystray.MenuItem(lambda text: f"Angela 狀態: {get_status()}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🚀 啟動後端", self.on_start_backend),
            pystray.MenuItem("🔄 重啟後端", self.on_restart_backend),
            pystray.MenuItem("🛑 停止後端", self.on_stop_backend),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🔑 查看 Key B (行動端)", self.on_show_key_b),
            pystray.MenuItem("📱 生成行動端配對 QR", self.on_generate_qr),
            pystray.MenuItem("📂 打開日誌目錄", lambda: os.startfile(self.backend_script.parent)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ 結束監控", self.on_exit)
        )

    def run(self):
        """啟動系統匣圖示"""
        self.icon = pystray.Icon("AngelaSecurity", self._create_image(), "Angela 安全監控", self.update_menu())
        self.icon.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    km = ABCKeyManager()
    monitor = SecurityTrayMonitor(km)
    monitor.run()
