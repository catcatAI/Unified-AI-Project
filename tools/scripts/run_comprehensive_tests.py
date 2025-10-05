#!/usr/bin/env python3
"""
綜合測試運行器 - 運行項目中的所有測試
"""

import subprocess
import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """測試運行器"""

    def __init__(self, project_root: Path = None) -> None:
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.test_results = {}
        self.failed_tests = []

    def setup_environment(self) -> None:
        """設置測試環境"""
        logger.info("設置測試環境...")

        # 設置演示模式環境變量
        demo_env = {
            'ATLASSIAN_API_TOKEN': 'DEMO_ATLASSIAN_TOKEN_2025',
            'ATLASSIAN_CLOUD_ID': 'demo-cloud-12345',
            'ATLASSIAN_USER_EMAIL': 'demo@catcatai.dev',
            'ATLASSIAN_DOMAIN': 'catcatai-demo',
            'GEMINI_API_KEY': 'DEMO_GEMINI_KEY_2025',
            'OPENAI_API_KEY': 'DEMO_OPENAI_KEY_2025',
            'MIKO_HAM_KEY': 'DEMO_HAM_KEY_2025',
            'PYTHONPATH': str(self.project_root)
        }

        for key, value in demo_env.items():
            os.environ[key] = value

        # 創建必要的目錄
        test_dirs = [
            'data/demo_learning',
            'data/task_queue',
            'data/atlassian_cache',
            'logs',
            'test_data'
        ]

        for dir_path in test_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

        logger.info("測試環境設置完成")

    def run_test_category(self, category: str, test_paths: List[str]) -> Dict[str, Any]:
        """運行特定類別的測試

        Args:
            category: 測試類別名稱
            test_paths: 測試文件路徑列表

        Returns:
            Dict: 測試結果
        """
        logger.info(f"運行 {category} 測試...")
        results = {
            'category': category,
            'total': len(test_paths),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

        for test_path in test_paths:
            full_path = self.project_root / test_path
            if not full_path.exists():
                logger.warning(f"測試文件不存在: {test_path}")
                results['skipped'] += 1
                continue

            try:
                # 運行單個測試文件
                cmd = [
                    sys.executable, '-m', 'pytest',
                    str(full_path),
                    '-v',
                    '--tb=short',
                    '--timeout=30'
                ]

                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    results['passed'] += 1
                    logger.info(f"✅ {test_path} - 通過")
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': test_path,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                    logger.error(f"❌ {test_path} - 失敗")
                    self.failed_tests.append(test_path)

            except subprocess.TimeoutExpired:
                results['failed'] += 1
                results['errors'].append({
                    'test': test_path,
                    'error': 'Test timeout'
                })
                logger.error(f"⏰ {test_path} - 超時")
                self.failed_tests.append(test_path)

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': test_path,
                    'error': str(e)
                })
                logger.error(f"💥 {test_path} - 異常: {e}")
                self.failed_tests.append(test_path)

        return results

    def run_all_tests(self) -> None:
        """運行所有測試"""
        logger.info("開始運行綜合測試套件")

        # 定義測試類別和對應的測試文件
        test_categories = {
            'Core AI': [
                'apps/backend/tests/core_ai/test_agent_manager.py',
                'apps/backend/tests/core_ai/test_emotion_system.py',
                'apps/backend/tests/core_ai/test_time_system.py',
                'apps/backend/tests/core_ai/memory/test_ham_memory_manager.py',
                'apps/backend/tests/core_ai/dialogue/test_dialogue_manager.py'
            ],
            'Integrations': [
                'apps/backend/tests/integrations/test_atlassian_bridge.py',
                'apps/backend/tests/integrations/test_atlassian_bridge_fallback.py',
                'apps/backend/tests/integrations/test_rovo_dev_agent.py',
                'apps/backend/tests/integrations/test_rovo_dev_agent_recovery.py',
                'apps/backend/tests/integrations/test_rovo_dev_connector.py'
            ],
            'HSP Protocol': [
                'apps/backend/tests/hsp/test_hsp_connector.py',
                'apps/backend/tests/hsp/test_hsp_integration.py'
            ],
            'Services': [
                'apps/backend/tests/services/test_main_api_server.py',
                'apps/backend/tests/services/test_llm_interface.py',
                'apps/backend/tests/services/test_resource_awareness_service.py'
            ],
            'Tools': [
                'apps/backend/tests/tools/test_math_model.py',
                'apps/backend/tests/tools/test_logic_model.py',
                'apps/backend/tests/tools/test_parameter_extractor.py'
            ],
            'Game': [
                'apps/backend/tests/game/test_main.py',
                'apps/backend/tests/game/test_npcs.py'
            ]
        }

        # 運行每個類別的測試
        for category, test_paths in test_categories.items():
            result = self.run_test_category(category, test_paths)
            self.test_results[category] = result

    def generate_report(self) -> str:
        """生成測試報告"""
        logger.info("生成測試報告...")

        total_tests = sum(r['total'] for r in self.test_results.values())
        total_passed = sum(r['passed'] for r in self.test_results.values())
        total_failed = sum(r['failed'] for r in self.test_results.values())
        total_skipped = sum(r['skipped'] for r in self.test_results.values())

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        report = f"""
# 🧪 綜合測試報告

## 📊 總體統計
- **總測試數**: {total_tests}
- **通過**: {total_passed} ✅
- **失敗**: {total_failed} ❌
- **跳過**: {total_skipped} ⏭️
- **成功率**: {success_rate:.1f}%

## 📋 各類別詳情
"""

        for category, results in self.test_results.items():
            category_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
            report += f"""
### {category}
- 總數: {results['total']}
- 通過: {results['passed']} ✅
- 失敗: {results['failed']} ❌
- 跳過: {results['skipped']} ⏭️
- 通過率: {category_rate:.1f}%
"""

        if self.failed_tests:
            report += "\n## ❌ 失敗的測試\n"
            for test in self.failed_tests:
                report += f"- {test}\n"

        report += f"""
## 📝 詳細日誌
報告生成時間: {self._get_current_time()}
"""
        return report

    def _get_current_time(self) -> str:
        """獲取當前時間字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, report: str, filename: str = "comprehensive_test_report.md") -> None:
        """保存測試報告"""
        report_path = self.project_root / "test_reports" / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"測試報告已保存到: {report_path}")

    def save_results_json(self, filename: str = "test_results.json") -> None:
        """保存測試結果為JSON格式"""
        results_path = self.project_root / "test_reports" / filename
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 轉換不可序列化的對象
        serializable_results = self._make_serializable(self.test_results)
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"測試結果已保存到: {results_path}")

    def _make_serializable(self, obj: Any) -> Any:
        """將對象轉換為可序列化格式"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        else:
            return str(obj)

def main():
    """主函數"""
    runner = ComprehensiveTestRunner()
    
    # 設置測試環境
    runner.setup_environment()
    
    # 運行所有測試
    runner.run_all_tests()
    
    # 生成並保存報告
    report = runner.generate_report()
    runner.save_report(report)
    runner.save_results_json()
    
    # 輸出摘要
    total_tests = sum(r['total'] for r in runner.test_results.values())
    total_passed = sum(r['passed'] for r in runner.test_results.values())
    total_failed = sum(r['failed'] for r in runner.test_results.values())
    
    print(f"\n{'='*50}")
    print(f"綜合測試運行完成")
    print(f"總測試數: {total_tests}")
    print(f"通過: {total_passed} ✅")
    print(f"失敗: {total_failed} ❌")
    print(f"成功率: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    print(f"{'='*50}")
    
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())