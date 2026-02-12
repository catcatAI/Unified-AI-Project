#!/usr/bin/env python3
"""
Angela AI 最小後端服務
不依賴外部庫，使用標準庫
"""

import os
import sys
import json
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import hashlib
import hmac
import secrets
import logging
logger = logging.getLogger(__name__)

class AngelaMinimalHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 設置環境變量
        os.environ['ANGELA_TESTING'] = 'true'
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """自定義日誌格式"""
        print(f"🌐 {format % args}")
    
    def do_GET(self):
        """處理 GET 請求"""
        if self.path == '/health':
            self._send_json_response({
                'status': 'ok',
                'service': 'angela-ai',
                'mode': 'minimal',
                'version': '6.2.1'
            })
            
        elif self.path == '/api/v1/system/status':
            self._send_json_response({
                'system_level': 'Level 5 AGI',
                'status': 'operational',
                'components': {
                    'backend': 'active',
                    'api': 'active'
                },
                'timestamp': time.time(),
                'environment': os.environ.get('ANGELA_ENV', 'development')
            })
            
        elif self.path == '/api/v1/system/status/detailed':
            # 需要簽名的詳細狀態
            self._send_json_response({
                'error': 'Signature required for detailed status'
            }, status=401)
            
        else:
            self._send_json_response({
                'error': 'Endpoint not found',
                'available_endpoints': [
                    '/health',
                    '/api/v1/system/status',
                    '/api/v1/system/status/detailed'
                ]
            }, status=404)
    
    def do_POST(self):
        """處理 POST 請求"""
        if self.path == '/api/v1/system/status/detailed':
            # 檢查簽名
            signature = self.headers.get('X-Angela-Signature')
            if not signature:
                self._send_json_response({
                    'error': 'Missing X-Angela-Signature header'
                }, status=401)
                return
            
            # 在測試模式下繞過簽名驗證
            if os.environ.get('ANGELA_TESTING') == 'true':
                self._send_json_response({
                    'status': 'online',
                    'stats': {
                        'cpu': '12%',
                        'mem': '42%',
                        'nodes': 1
                    },
                    'modules': {
                        'vision': True,
                        'audio': True,
                        'tactile': True,
                        'action': True
                    },
                    'timestamp': time.time()
                })
            else:
                self._send_json_response({
                    'error': 'Invalid signature'
                }, status=403)
                
        elif self.path == '/api/v1/mobile/test':
            # 移動端測試端點
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            self._send_json_response({
                'status': 'success',
                'message': 'Test message received',
                'timestamp': time.time()
            })
            
        else:
            self._send_json_response({
                'error': 'Endpoint not found'
            }, status=404)
    
    def do_OPTIONS(self):
        """處理 OPTIONS 請求（CORS 預檢）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Angela-Signature')
        self.end_headers()
    
    def _send_json_response(self, data, status=200):
        """發送 JSON 響應"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Angela-Signature')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

def main():
    """啟動最小後端服務"""
    print("🌟 Angela AI - 最小後端服務")
    print("=" * 50)
    print(f"📍 服務地址: http://127.0.0.1:8000")
    print(f"🔗 健康檢查: http://127.0.0.1:8000/health")
    print(f"📊 系統狀態: http://127.0.0.1:8000/api/v1/system/status")
    print("=" * 50)
    print("🛑 按 Ctrl+C 停止服務")
    print()
    
    # 設置環境變量
    os.environ['ANGELA_ENV'] = 'development'
    os.environ['ANGELA_TESTING'] = 'true'
    
    # 創建服務器
    try:
        server = HTTPServer(('127.0.0.1', 8000), AngelaMinimalHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 正在停止服務...")
        server.shutdown()
        print("✅ Angela AI 已停止")
    except Exception as e:
        print(f"❌ 服務器啟動失敗: {e}")

if __name__ == "__main__":
    main()
