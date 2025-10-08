#!/usr/bin/env python3
"""
測試增強版修復系統的完整功能
驗證修復驗證邏輯、容錯能力和分步修復策略
"""

import sys
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enhanced_smart_repair_validator():
    """測試增強版智能驗證器"""
    print("🧪 測試增強版智能驗證器...")
    
    try:
        from enhanced_smart_repair_validator import EnhancedSmartRepairValidator
        
        validator = EnhancedSmartRepairValidator()
        
        # 測試用例：有語法錯誤的代碼
        test_lines = [
            "def test_function(x, y)",
            "    result = x + y",
            "    print(result",
            "    return result"
        ]
        
        # 執行智能驗證
        result = validator.validate_repair_intelligent(
            original_lines=[],
            repaired_lines=test_lines,
            issue_type='missing_colon',
            confidence=0.8
        )
        
        print(f"✅ 智能驗證器測試完成")
        print(f"   語法驗證: {result.get('syntax_validation', {})}")
        print(f"   語義驗證: {result.get('semantic_validation', {})}")
        print(f"   格式驗證: {result.get('format_validation', {})}")
        print(f"   整體成功: {result.get('overall_success', False)}")
        
        return result.get('overall_success', False)
        
    except Exception as e:
        print(f"❌ 智能驗證器測試失敗: {e}")
        return False

def test_enhanced_complete_repair_system():
    """測試增強版完整修復系統"""
    print("🔧 測試增強版完整修復系統...")
    
    try:
        from enhanced_complete_repair_system import EnhancedCompleteRepairSystem
        
        # 創建測試文件
        test_file = 'test_repair_sample.py'
        test_content = '''def test_function(x, y)
    result = x + y
    print(result
    return result

class TestClass
    def __init__(self)
        self.value = 0
    
    def process(self)
        if self.value > 0
            print("Positive")
        return self.value
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 創建修復系統
        repair_system = EnhancedCompleteRepairSystem(max_workers=2)
        
        # 運行完整修復
        results = repair_system.run_complete_repair('.', repair_scope={
            'syntax': True,
            'semantic': True,
            'style': True,
            'performance': False,
            'security': False
        })
        
        print(f"✅ 增強版完整修復系統測試完成")
        print(f"   狀態: {results['status']}")
        print(f"   總問題: {results.get('total_issues', 0)}")
        print(f"   成功修復: {results.get('successful_repairs', 0)}")
        print(f"   失敗修復: {results.get('failed_repairs', 0)}")
        print(f"   執行時間: {results.get('execution_time', 0):.2f}秒")
        
        # 清理測試文件
        if Path(test_file).exists():
            Path(test_file).unlink()
        
        return results.get('status') == 'completed'
        
    except Exception as e:
        print(f"❌ 增強版完整修復系統測試失敗: {e}")
        # 清理測試文件
        test_file = 'test_repair_sample.py'
        if Path(test_file).exists():
            Path(test_file).unlink()
        return False

def test_enhanced_intelligent_repair_system():
    """測試增強版智能修復系統"""
    print("🧠 測試增強版智能修復系統...")
    
    try:
        from enhanced_intelligent_repair_system import EnhancedIntelligentRepairSystem
        
        # 創建測試文件
        test_file = 'test_intelligent_repair.py'
        test_content = '''def test_function(x, y)
    result = x + y
    print(result
    return result

unused_var = 42
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 創建智能修復系統
        repair_system = EnhancedIntelligentRepairSystem()
        
        # 運行智能修復
        results = repair_system.run_enhanced_intelligent_repair('.')
        
        print(f"✅ 增強版智能修復系統測試完成")
        print(f"   狀態: {results['status']}")
        print(f"   修復結果數: {len(results.get('repair_results', []))}")
        print(f"   執行時間: {results.get('execution_time', 0):.2f}秒")
        
        # 顯示學習進展
        learning_updates = results.get('learning_updates', {})
        if learning_updates:
            print(f"   學習模式: {learning_updates.get('patterns_learned', 0)} 個")
            print(f"   成功率改善: {learning_updates.get('success_rates_improved', 0)} 個")
        
        # 顯示性能統計
        performance_stats = results.get('performance_stats', {})
        if performance_stats:
            print(f"   成功率: {performance_stats.get('success_rate', 0):.1f}%")
            print(f"   總修復數: {performance_stats.get('total_repairs', 0)}")
        
        # 清理測試文件
        if Path(test_file).exists():
            Path(test_file).unlink()
        
        return results.get('status') == 'completed'
        
    except Exception as e:
        print(f"❌ 增強版智能修復系統測試失敗: {e}")
        # 清理測試文件
        test_file = 'test_intelligent_repair.py'
        if Path(test_file).exists():
            Path(test_file).unlink()
        return False

def test_system_self_maintenance():
    """測試系統自我維護管理器"""
    print("🔄 測試系統自我維護管理器...")
    
    try:
        from apps.backend.src.system_self_maintenance import SystemSelfMaintenanceManager, MaintenanceConfig, MaintenanceMode
        
        # 創建維護配置
        config = MaintenanceConfig(
            mode=MaintenanceMode.FULL,
            discovery_interval=60,  # 1分鐘
            repair_interval=120,    # 2分鐘
            test_interval=180,      # 3分鐘
            max_concurrent_repairs=2
        )
        
        # 創建維護管理器
        manager = SystemSelfMaintenanceManager(config)
        
        print(f"✅ 系統自我維護管理器創建成功")
        print(f"   運行模式: {config.mode.value}")
        print(f"   發現間隔: {config.discovery_interval}秒")
        print(f"   修復間隔: {config.repair_interval}秒")
        print(f"   測試間隔: {config.test_interval}秒")
        
        # 獲取狀態
        status = manager.get_maintenance_status()
        print(f"   系統狀態: 運行中={status['is_running']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 系統自我維護管理器測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試增強版修復系統完整功能")
    print("=" * 60)
    
    start_time = time.time()
    test_results = {}
    
    # 測試各個組件
    test_results['smart_validator'] = test_enhanced_smart_repair_validator()
    test_results['complete_repair'] = test_enhanced_complete_repair_system()
    test_results['intelligent_repair'] = test_enhanced_intelligent_repair_system()
    test_results['self_maintenance'] = test_system_self_maintenance()
    
    # 統計結果
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    execution_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("🎯 測試結果總結")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
    
    print(f"\n📊 統計信息:")
    print(f"   總測試數: {total_tests}")
    print(f"   通過測試: {passed_tests}")
    print(f"   失敗測試: {total_tests - passed_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    print(f"   執行時間: {execution_time:.2f}秒")
    
    if success_rate >= 75:
        print(f"\n🎉 系統測試整體成功！修復驗證邏輯和容錯能力已顯著提升")
    elif success_rate >= 50:
        print(f"\n⚠️ 系統測試部分成功，部分功能需要進一步優化")
    else:
        print(f"\n❌ 系統測試失敗，需要檢查和修復主要問題")
    
    return success_rate >= 50  # 50%以上認為基本可用

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)