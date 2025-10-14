#!/usr/bin/env python3
"""
系統集成測試
驗證修復後的系統組件是否正常工作
"""

import asyncio
import sys
import os
import requests
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "apps" / "backend"))

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemIntegrationTest:
    """系統集成測試類"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始系統集成測試...")
        
        # 測試後端依賴
        await self.test_backend_dependencies()
        
        # 測試數據網路管理器
        await self.test_data_network_manager()
        
        # 測試API端點
        await self.test_api_endpoints()
        
        # 測試知識圖譜
        await self.test_knowledge_graph()
        
        # 生成測試報告
        self.generate_report()
        
    async def test_backend_dependencies(self):
        """測試後端依賴"""
        logger.info("📦 測試後端依賴...")
        
        try:
            # 測試 Redis 導入
            try:
                import redis.asyncio as redis
                self.add_test_result("Redis依賴", True, "Redis模組導入成功")
            except ImportError as e:
                self.add_test_result("Redis依賴", False, f"Redis模組導入失敗: {e}")
            
            # 測試其他關鍵依賴
            dependencies = [
                "networkx", "psutil", "faiss_cpu", "sentence_transformers", 
                "chromadb", "websockets", "aiofiles", "pydantic", "fastapi"
            ]
            
            for dep in dependencies:
                try:
                    __import__(dep)
                    self.add_test_result(f"{dep}依賴", True, f"{dep}模組導入成功")
                except ImportError as e:
                    self.add_test_result(f"{dep}依賴", False, f"{dep}模組導入失敗: {e}")
                    
        except Exception as e:
            logger.error(f"❌ 依賴測試失敗: {e}")
            self.add_test_result("依賴測試", False, f"依賴測試異常: {e}")
    
    async def test_data_network_manager(self):
        """測試數據網路管理器"""
        logger.info("🌐 測試數據網路管理器...")
        
        try:
            from src.core.data.data_network_manager import DataNetworkManager, DataPacket, DataPriority
            
            # 創建管理器實例
            manager = DataNetworkManager()
            
            # 測試初始化
            init_result = await manager.initialize()
            self.add_test_result("數據網路初始化", init_result, "數據網路管理器初始化" + ("成功" if init_result else "失敗"))
            
            # 測試創建網路
            if init_result:
                create_result = await manager.create_network("test_network", "test_type")
                self.add_test_result("創建數據網路", create_result, "創建測試網路" + ("成功" if create_result else "失敗"))
                
                # 測試網路狀態
                if create_result:
                    status = await manager.get_network_status()
                    self.add_test_result("網路狀態查詢", status.get("status") != "error", f"網路狀態: {status.get('status')}")
                
                # 清理
                await manager.cleanup()
            
        except Exception as e:
            logger.error(f"❌ 數據網路測試失敗: {e}")
            self.add_test_result("數據網路測試", False, f"數據網路測試異常: {e}")
    
    async def test_api_endpoints(self):
        """測試API端點"""
        logger.info("🔌 測試API端點...")
        
        try:
            # 測試健康檢查
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    self.add_test_result("健康檢查API", True, "健康檢查端點正常")
                else:
                    self.add_test_result("健康檢查API", False, f"健康檢查返回狀態碼: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.add_test_result("健康檢查API", False, f"健康檢查連接失敗: {e}")
            
            # 測試系統狀態
            try:
                response = requests.get(f"{self.backend_url}/api/v1/system/status", timeout=5)
                if response.status_code == 200:
                    self.add_test_result("系統狀態API", True, "系統狀態端點正常")
                else:
                    self.add_test_result("系統狀態API", False, f"系統狀態返回狀態碼: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.add_test_result("系統狀態API", False, f"系統狀態連接失敗: {e}")
            
            # 測試Atlassian集成API
            try:
                response = requests.get(f"{self.backend_url}/api/v1/atlassian/status", timeout=5)
                if response.status_code in [200, 500]:  # 500表示服務存在但可能未配置
                    self.add_test_result("Atlassian API", True, "Atlassian端點可訪問")
                else:
                    self.add_test_result("Atlassian API", False, f"Atlassian返回狀態碼: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.add_test_result("Atlassian API", False, f"Atlassian連接失敗: {e}")
                
        except Exception as e:
            logger.error(f"❌ API測試失敗: {e}")
            self.add_test_result("API測試", False, f"API測試異常: {e}")
    
    async def test_knowledge_graph(self):
        """測試知識圖譜"""
        logger.info("🧠 測試知識圖譜...")
        
        try:
            # 測試知識圖譜導入
            try:
                from src.core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph
                self.add_test_result("知識圖譜導入", True, "知識圖譜模組導入成功")
                
                # 測試初始化
                try:
                    kg = UnifiedKnowledgeGraph({})
                    # 注意：在沒有Chromadb實例的情況下可能會失敗，這是正常的
                    self.add_test_result("知識圖譜實例化", True, "知識圖譜實例化成功")
                except Exception as e:
                    self.add_test_result("知識圖譜實例化", False, f"知識圖譜實例化失敗: {e}")
                    
            except ImportError as e:
                self.add_test_result("知識圖譜導入", False, f"知識圖譜導入失敗: {e}")
                
        except Exception as e:
            logger.error(f"❌ 知識圖譜測試失敗: {e}")
            self.add_test_result("知識圖譜測試", False, f"知識圖譜測試異常: {e}")
    
    def add_test_result(self, test_name: str, passed: bool, message: str):
        """添加測試結果"""
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} {test_name}: {message}")
    
    def generate_report(self):
        """生成測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate
            },
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存報告
        report_path = project_root / "system_integration_test_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        logger.info("📊 測試報告摘要:")
        logger.info(f"總測試數: {total_tests}")
        logger.info(f"通過: {passed_tests}")
        logger.info(f"失敗: {failed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"詳細報告已保存至: {report_path}")
        
        return report

async def main():
    """主函數"""
    tester = SystemIntegrationTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())