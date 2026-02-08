import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class AngelaMinimalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"🌐 {format % args}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/health':
            response = {
                'status': 'ok',
                'service': 'angela-ai',
                'mode': 'minimal',
                'version': '6.2.1',
                'environment': os.environ.get('ANGELA_ENV', 'development')
            }
        elif self.path == '/api/v1/system/status':
            response = {
                'system_level': 'Level 5 AGI',
                'status': 'operational',
                'components': {
                    'backend': 'active',
                    'api': 'active',
                    'security': 'active',
                    'ai_core': 'active'
                },
                'modules': {
                    'vision': True,
                    'audio': True,
                    'tactile': True,
                    'action': True,
                    'cognition': True,
                    'evolution': True
                },
                'performance': {
                    'cpu': '12%',
                    'memory': '38%',
                    'fps': 60,
                    'render_time': '16.67ms'
                },
                'features': {
                    'live2d': 'ready',
                    'voice_recognition': 'ready',
                    'text_to_speech': 'ready',
                    'mobile_bridge': 'ready',
                    'desktop_integration': 'ready'
                },
                'timestamp': time.time()
            }
        else:
            response = {
                'error': 'Endpoint not found',
                'available_endpoints': [
                    '/health',
                    '/api/v1/system/status'
                ]
            }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Angela-Signature')
        self.end_headers()

def start_service():
    os.environ['ANGELA_ENV'] = 'development'
    os.environ['ANGELA_TESTING'] = 'true'
    
    try:
        server = HTTPServer(('127.0.0.1', 8000), AngelaMinimalHandler)
        return server
    except Exception as e:
        print(f"❌ 服務器創建失敗: {e}")
        return None

if __name__ == '__main__':
    server = start_service()
    if server:
        print("🌟 Angela AI - 最小後端服務")
        print("=" * 50)
        print("📍 服務地址: http://127.0.0.1:8000")
        print("🔗 健康檢查: http://127.0.0.1:8000/health") 
        print("📊 系統狀態: http://127.0.0.1:8000/api/v1/system/status")
        print("=" * 50)
        print("🛑 按 Ctrl+C 停止服務")
        print()
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 正在停止服務...")
            server.shutdown()
            print("✅ Angela AI 已停止")
