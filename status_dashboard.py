#!/usr/bin/env python3
# Angela AI Status Dashboard
import requests
import json
import time
import sys
from datetime import datetime

def get_server_status():
    """獲取服務器狀態"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_system_status():
    """獲取系統狀態"""
    try:
        response = requests.get('http://127.0.0.1:8000/api/v1/system/status', timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def show_dashboard():
    """顯示狀態儀表板"""
    while True:
        try:
            # 清屏
            print('\033[2J\033[H', end='')
            
            # 獲取狀態
            server_status = get_server_status()
            system_status = get_system_status()
            
            # 顯示標題
            print('🌟 Angela AI - 狀態儀表板')
            print('=' * 50)
            print(f'🕒 時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            print()
            
            # 服務器狀態
            status_icon = '🟢' if server_status.get('status') == 'ok' else '🔴'
            print(f'{status_icon} 後端服務器: {server_status.get("status", "未知")}')
            if 'service' in server_status:
                print(f'   服務: {server_status["service"]}')
            if 'mode' in server_status:
                print(f'   模式: {server_status["mode"]}')
            print()
            
            # 系統狀態
            if system_status.get('status') == 'operational':
                print('🟢 系統狀態: 運行中')
                print(f'   級別: {system_status.get("system_level", "未知")}')
                
                components = system_status.get('components', {})
                print('   組件:')
                for component, status in components.items():
                    icon = '🟢' if status == 'active' else '🔴'
                    print(f'     {icon} {component}: {status}')
            else:
                print('🔴 系統狀態: 離線')
                if 'message' in system_status:
                    print(f'   錯誤: {system_status["message"]}')
            
            print()
            print('📍 服務端點:')
            print('   健康檢查: http://127.0.0.1:8000/health')
            print('   系統狀態: http://127.0.0.1:8000/api/v1/system/status')
            print()
            print('🛑 按 Ctrl+C 離開')
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print('\n👋 再見！')
            break
        except Exception as e:
            print(f'❌ 錯誤: {e}')
            time.sleep(5)

if __name__ == '__main__':
    print('🌟 Angela AI - 狀態監控器')
    print('正在連接到後端服務器...')
    print()
    
    # 檢查是否安裝了 requests
    try:
        import requests
    except ImportError:
        print('❌ 需要 requests 庫，安裝命令:')
        print('   python3 -m pip install requests')
        sys.exit(1)
    
    show_dashboard()