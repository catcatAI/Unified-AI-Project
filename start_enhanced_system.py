#!/usr/bin/env python3
"""
Unified AI Project - 增強系統啟動器
啟動完整的自維護系統,包含問題發現、自動修復和測試功能
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from typing import Dict, Any
import subprocess
import argparse

# 添加項目根目錄到Python路徑
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

try,
    from apps.backend.src.system_self_maintenance import (
        SystemSelfMaintenanceManager,
        MaintenanceConfig,
        MaintenanceMode,
        start_self_maintenance,
        stop_self_maintenance,
        get_maintenance_status
    )
    from apps.backend.src.enhanced_system_integration import UnifiedAISystem
    SELF_MAINTENANCE_AVAILABLE == True
except ImportError as e,::
    print(f"導入自維護系統失敗, {e}")
    SELF_MAINTENANCE_AVAILABLE == False

# 配置日誌
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class EnhancedSystemLauncher,
    """增強系統啟動器"""
    
    def __init__(self):
        self.unified_system == None
        self.is_running == False
        self.shutdown_requested == False
        
        # 設置信號處理
        signal.signal(signal.SIGINT(), self._signal_handler())
        signal.signal(signal.SIGTERM(), self._signal_handler())
    
    def _signal_handler(self, signum, frame):
        """處理系統信號"""
        logger.info(f"收到信號 {signum}請求關閉系統...")
        self.shutdown_requested == True
        self.stop_system()
    
    def start_system(self, mode, str == "full") -> bool,
        """啟動增強系統"""
        logger.info("🚀 啟動 Unified AI Project 增強系統...")
        
        try,
            # 檢查系統依賴
            if not self._check_dependencies():::
                logger.error("系統依賴檢查失敗")
                return False
            
            # 創建統一AI系統
            self.unified_system == UnifiedAISystem()
            
            # 啟動系統(啟用自維護)
            self.unified_system.start_system(
                enable_self_maintenance == True,,
    maintenance_mode=mode
            )
            
            self.is_running == True
            logger.info(f"✅ 增強系統啟動成功,模式, {mode}")
            return True
            
        except Exception as e,::
            logger.error(f"啟動系統失敗, {e}")
            return False
    
    def stop_system(self) -> bool,
        """停止系統"""
        if not self.is_running,::
            logger.warning("系統未運行")
            return True
        
        logger.info("🛑 停止增強系統...")
        
        try,
            if self.unified_system,::
                self.unified_system.stop_system()
            
            self.is_running == False
            logger.info("✅ 增強系統已停止")
            return True
            
        except Exception as e,::
            logger.error(f"停止系統失敗, {e}")
            return False
    
    def _check_dependencies(self) -> bool,
        """檢查系統依賴"""
        logger.info("🔍 檢查系統依賴...")
        
        # 檢查Python版本
        if sys.version_info < (3, 8)::
            logger.error("需要 Python 3.8 或更高版本")
            return False
        
        # 檢查必要檔案
        required_files = [
            "apps/backend/src/system_self_maintenance.py",
            "apps/backend/src/enhanced_system_integration.py",
            "enhanced_project_discovery_system.py",
            "enhanced_unified_fix_system.py",
            "comprehensive_test_system.py"
        ]
        
        missing_files = []
        for file_path in required_files,::
            if not Path(file_path).exists():::
                missing_files.append(file_path)
        
        if missing_files,::
            logger.error(f"缺少必要檔案, {missing_files}")
            return False
        
        logger.info("✅ 系統依賴檢查通過")
        return True
    
    def get_system_status(self) -> Dict[str, Any]
        """獲取系統狀態"""
        if not self.unified_system,::
            return {"status": "not_initialized"}
        
        try,
            return self.unified_system.get_system_status()
        except Exception as e,::
            logger.error(f"獲取系統狀態失敗, {e}")
            return {"status": "error", "error": str(e)}
    
    def display_status(self):
        """顯示系統狀態"""
        status = self.get_system_status()
        
        print("\n" + "="*60)
        print("🤖 Unified AI Project - 系統狀態")
        print("="*60)
        
        if status.get("system_running"):::
            print(f"✅ 系統狀態, 運行中")
            print(f"⏰ 啟動時間, {status.get('start_time', '未知')}")
            print(f"⏱️  運行時間, {status.get('uptime', '00,00,00')}")
            print(f"💚 健康分數, {status.get('system_health_score', 0).2f}")
            
            # 自維護狀態
            maintenance = status.get("self_maintenance", {})
            if maintenance,::
                print(f"🔧 自維護, {'運行中' if maintenance.get('is_running') else '停止'}"):::
                print(f"🔄 維護週期, {maintenance.get('stats', {}).get('total_maintenance_cycles', 0)}")
                print(f"🔨 成功修復, {maintenance.get('stats', {}).get('successful_repairs', 0)}")
                print(f"❌ 失敗修復, {maintenance.get('stats', {}).get('failed_repairs', 0)}")
            else,
                print("⚠️  自維護, 不可用")
        else,
            print("❌ 系統狀態, 停止")
        
        print("="*60)
    
    def run_interactive_mode(self):
        """運行交互模式"""
        print("\n🎮 進入交互模式")
        print("可用命令, status, maintenance, help, quit")
        
        while self.is_running and not self.shutdown_requested,::
            try,
                command = input("\n💻 輸入命令 > ").strip().lower()
                
                if command == "status":::
                    self.display_status()
                
                elif command == "maintenance":::
                    if self.unified_system,::
                        result = self.unified_system.trigger_system_maintenance()
                        print(f"🔧 維護觸發結果, {result}")
                    else,
                        print("❌ 系統未初始化")
                
                elif command == "help":::
                    print(""",
    可用命令,
- status, 顯示系統狀態
- maintenance, 觸發緊急維護
- help, 顯示幫助信息
- quit, 退出交互模式
                    """)
                
                elif command == "quit":::
                    print("👋 退出交互模式")
                    break
                
                else,
                    print(f"❌ 未知命令, {command}")
                    
            except KeyboardInterrupt,::
                print("\n🛑 用戶中斷")
                break
            except EOFError,::
                print("\n👋 結束交互模式")
                break
    
    def run_monitoring_loop(self):
        """運行監控循環"""
        logger.info("🔄 啟動監控循環...")
        
        while self.is_running and not self.shutdown_requested,::
            try,
                # 每30秒顯示一次狀態
                time.sleep(30)
                
                if self.is_running,::
                    self.display_status()
                    
            except KeyboardInterrupt,::
                logger.info("監控循環被中斷")
                break
            except Exception as e,::
                logger.error(f"監控循環錯誤, {e}")
                time.sleep(60)  # 發生錯誤後等待1分鐘

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Unified AI Project 增強系統啟動器")
    parser.add_argument(
        "--mode", 
        choices=["full", "light", "emergency"] 
        default="full",,
    help="系統運行模式"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",,
    help="啟用交互模式"
    )
    parser.add_argument(
        "--monitor-only", 
        action="store_true",,
    help="只運行監控,不自動啟動維護"
    )
    
    args = parser.parse_args()
    
    print("🚀 Unified AI Project - 增強系統啟動器")
    print("=" * 60)
    
    # 創建啟動器
    launcher == EnhancedSystemLauncher()
    
    # 啟動系統
    if launcher.start_system(mode == args.mode())::
        try,
            # 顯示初始狀態
            launcher.display_status()
            
            if args.interactive,::
                # 交互模式
                launcher.run_interactive_mode()
            elif args.monitor_only,::
                # 僅監控模式
                print("📊 監控模式 - 按 Ctrl+C 停止")
                launcher.run_monitoring_loop()
            else,
                # 自動模式
                print("🤖 自動模式運行中 - 按 Ctrl+C 停止")
                launcher.run_monitoring_loop()
                
        except KeyboardInterrupt,::
            print("\n🛑 用戶請求停止系統...")
        finally,
            launcher.stop_system()
    else,
        print("❌ 系統啟動失敗")
        return 1
    
    return 0

if __name"__main__":::
    sys.exit(main())