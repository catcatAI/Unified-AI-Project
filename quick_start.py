#!/usr/bin/env python3
# Angela AI Quick Start - Minimal Version
import os
import sys
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 設置環境變量
os.environ['ANGELA_TESTING'] = 'true'
os.environ['ANGELA_ENV'] = 'development'

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print('🌟 Angela AI - Minimal Backend')
print('=' * 50)
print('📋 Environment Variables:')
print(f'   ANGELA_TESTING: {os.environ.get("ANGELA_TESTING")}')
print(f'   ANGELA_ENV: {os.environ.get("ANGELA_ENV")}')
print('=' * 50)

# 嘗試基本的服務器功能
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    import threading
    import time
    
    class AngelaHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if self.path == '/health':
                response = {'status': 'ok', 'service': 'angela-ai', 'mode': 'minimal'}
            elif self.path == '/api/v1/system/status':
                response = {
                    'system_level': 'Level 5 AGI',
                    'status': 'operational', 
                    'components': {'backend': 'active'},
                    'timestamp': time.time()
                }
            else:
                response = {'error': 'Endpoint not found'}
                
            self.wfile.write(json.dumps(response).encode())
        
        def log_message(self, format, *args):
            print(f'🌐 {format % args}')
    
    # 啟動服務器
    server = HTTPServer(('127.0.0.1', 8000), AngelaHandler)
    print('🚀 Starting minimal backend server...')
    print('📍 Server: http://127.0.0.1:8000')
    print('🔗 Health: http://127.0.0.1:8000/health')
    print('📊 Status: http://127.0.0.1:8000/api/v1/system/status')
    print('=' * 50)
    print('🛑 按 Ctrl+C 停止服務器')
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print('\n🛑 Shutting down Angela AI...')
        print('✅ Angela AI stopped')
        
except Exception as e:
    print(f'❌ Failed to start minimal backend: {e}')
    sys.exit(1)