import sys
import time
import logging
import traceback
import threading
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 導入智能驗證器 (可選)
try:
    from enhanced_smart_repair_validator import EnhancedSmartRepairValidator

    HAS_SMART_VALIDATOR = True
except ImportError:
    print("⚠️ 智能驗證器不可用")
    EnhancedSmartRepairValidator = None
    HAS_SMART_VALIDATOR = False

# 导入新的统一自动修复系统集成管理器
try:
    from auto_repair_integration_manager import AutoRepairIntegrationManager, RepairSystemType

    HAS_INTEGRATION_MANAGER = True
    print("✅ 成功导入自动修复系统集成管理器")
except ImportError as e:
    print(f"⚠️ 自动修复系统集成管理器不可用, {e}")
    HAS_INTEGRATION_MANAGER = False

USE_ENHANCED_SYSTEMS = False
EnhancedProjectDiscoverySystem = None
EnhancedIntelligentRepairSystem = None
EnhancedUnifiedFixSystem = None
ComprehensiveTestSystem = None

# 首先嘗試導入增強版完整修復系統
try:
    from enhanced_complete_repair_system import EnhancedCompleteRepairSystem

    HAS_ENHANCED_REPAIR = True
    print("✅ 成功導入增強版完整修復系統")
except ImportError as e:
    print(f"⚠️ 增強版完整修復系統不可用, {e}")
    HAS_ENHANCED_REPAIR = False

try:
    # 嘗試導入增強版完整系統
    from enhanced_project_discovery_system import EnhancedProjectDiscoverySystem
    from enhanced_intelligent_repair_system import EnhancedIntelligentRepairSystem
    from comprehensive_test_system import ComprehensiveTestSystem
    from enhanced_complete_detection_engine import EnhancedCompleteDetectionEngine

    # 確保導入成功
    if (
        EnhancedProjectDiscoverySystem
        and EnhancedIntelligentRepairSystem
        and ComprehensiveTestSystem
    ):
        print("✅ 成功導入增換版完整系統")
        USE_ENHANCED_SYSTEMS = True
    else:
        print("⚠️ 增強版系統導入不完整, 使用標準系統")
        from enhanced_unified_fix_system import EnhancedUnifiedFixSystem

        USE_ENHANCED_SYSTEMS = False

except ImportError as e:
    print(f"導入增強版系統失敗, {e}")
    print("嘗試導入標準系統...")

    try:
        USE_ENHANCED_SYSTEMS = False
        print("✅ 使用標準系統")
    except ImportError as e2:
        print(f"導入標準系統也失敗, {e2}")
        print("❌ 所有系統都無法導入, 這是一個嚴重問題")
        EnhancedProjectDiscoverySystem = None
        EnhancedIntelligentRepairSystem = None
        EnhancedUnifiedFixSystem = None
        ComprehensiveTestSystem = None
        USE_ENHANCED_SYSTEMS = False


class MaintenanceMode(Enum):
    """維護模式"""

    FULL = "full"  # 完整功能模式
    LIGHT = "light"  # 輕量模式
    EMERGENCY = "emergency"  # 緊急模式
    MANUAL = "manual"  # 手動模式


@dataclass
class MaintenanceConfig:
    """維護配置"""

    mode: MaintenanceMode = MaintenanceMode.FULL
    discovery_interval: int = 300  # 5分鐘
    repair_interval: int = 600  # 10分鐘
    test_interval: int = 900  # 15分鐘
    max_repair_time: int = 3600  # 1小時
    enable_real_time_monitoring: bool = True
    enable_auto_backup: bool = True
    max_concurrent_repairs: int = 3
    repair_success_threshold: float = 0.85


class SystemSelfMaintenanceManager:  # Added missing class definition
    """系統自維護管理器"""

    def __init__(self, config: Optional[MaintenanceConfig] = None):  # Fixed type hint
        self.config = config or MaintenanceConfig()
        self.logger = self._setup_logging()
        self.is_running = False  # Fixed assignment
        self.maintenance_thread = None  # Fixed assignment
        self.last_maintenance_time = None  # Fixed assignment
        self.maintenance_stats = {  # Fixed dictionary initialization
            "total_maintenance_cycles": 0,
            "successful_repairs": 0,
            "failed_repairs": 0,
            "issues_discovered": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "last_maintenance_time": None,
            "system_health_score": 1.0,  # Fixed function call
        }

        # 添加問題快取機制
        self.last_discovery_results = None  # Fixed assignment
        self.last_repair_results = None  # Fixed assignment

        # 初始化核心系統
        self.discovery_system = None
        self.fix_system = None
        self.test_system = None
        self._initialize_core_systems()

        # 維護循環控制
        self.maintenance_cycle_active = False
        self.emergency_repair_needed = False

    def _setup_logging(self) -> logging.Logger:
        """設置日誌系統"""
        # 創建日誌目錄
        log_dir = Path("logs/self_maintenance")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 配置日誌
        logger = logging.getLogger("SystemSelfMaintenance")
        logger.setLevel(logging.INFO)

        # 文件日誌處理器
        log_file = log_dir / f"self_maintenance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # 控制台日誌處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 日誌格式
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _initialize_core_systems(self):
        """初始化核心系統 - 完整版實現"""
        self.logger.info("🚀 初始化核心系統 (完整版)...")

        try:
            # 初始化問題發現系統 - 使用增強版
            if EnhancedProjectDiscoverySystem:
                self.discovery_system = EnhancedProjectDiscoverySystem()
                self.logger.info("✅ 增強版問題發現系統初始化成功")
            else:
                self.logger.error("❌ 問題發現系統不可用")
                raise RuntimeError("問題發現系統初始化失敗")

            # 初始化修復系統 - 根據可用性選擇最佳系統
            if USE_ENHANCED_SYSTEMS and "EnhancedIntelligentRepairSystem" in globals():
                self.fix_system = EnhancedIntelligentRepairSystem()
                self.logger.info("✅ 增強版智能修復系統初始化成功 (AGI Level 3)")
            elif EnhancedUnifiedFixSystem:
                self.fix_system = EnhancedUnifiedFixSystem()
                self.logger.info("✅ 標準自動修復系統初始化成功")
            else:
                self.logger.error("❌ 自動修復系統不可用")
                raise RuntimeError("自動修復系統初始化失敗")

            # 初始化測試系統
            if ComprehensiveTestSystem:
                self.test_system = ComprehensiveTestSystem()
                self.logger.info("✅ 綜合測試系統初始化成功")
            else:
                self.logger.error("❌ 測試系統不可用")
                raise RuntimeError("測試系統初始化失敗")

            # 初始化增強檢測引擎(如果可用)
            if "EnhancedCompleteDetectionEngine" in globals():
                try:
                    self.detection_engine = EnhancedCompleteDetectionEngine(max_workers=8)
                    self.logger.info("✅ 增強版完整檢測引擎初始化成功")
                except Exception as e:
                    self.logger.warning(f"⚠️ 增強檢測引擎初始化失敗, {e}")
                    self.detection_engine = None
            else:
                self.detection_engine = None
                self.logger.info("ℹ️ 增強檢測引擎不可用, 使用標準檢測")

            self.logger.info("🎉 所有核心系統初始化完成")

        except Exception as e:
            self.logger.error(f"初始化核心系統失敗, {e}")
            # 不要自動降級到簡化模式, 而是報告錯誤
            raise RuntimeError(f"核心系統初始化失敗, {e}")

    def _create_simplified_discovery_system(self):
        """創建簡化版問題發現系統"""

        class SimplifiedDiscovery:
            def __init__(self, logger):
                self.logger = logger

            def run_complete_discovery(self):
                self.logger.info("使用簡化問題發現系統")
                return {"status": "simplified", "issues_found": [], "system_health": "unknown"}

        return SimplifiedDiscovery(self.logger)

    def _create_simplified_fix_system(self):
        """創建簡化版修復系統"""

        class SimplifiedFix:
            def __init__(self, logger):
                self.logger = logger

            def run_enhanced_fix(self, issues):
                self.logger.info("使用簡化修復系統")
                return {"status": "simplified", "repairs_completed": 0, "repairs_failed": 0}

        return SimplifiedFix(self.logger)

    def _create_simplified_test_system(self):
        """創建簡化版測試系統"""

        class SimplifiedTest:
            def __init__(self, logger):
                self.logger = logger

            def run_comprehensive_test_update(self):
                self.logger.info("使用簡化測試系統")
                return {
                    "status": "simplified",
                    "tests_run": 0,
                    "tests_passed": 0,
                    "tests_failed": 0,
                }

        return SimplifiedTest(self.logger)

    def start_self_maintenance(self) -> bool:
        """啟動自維護系統"""
        if self.is_running:
            self.logger.warning("自維護系統已經在運行中")
            return False

        self.logger.info("🚀 啟動系統自維護管理器...")
        self.logger.info(f"運行模式: {self.config.mode.value}")
        self.logger.info(f"發現間隔: {self.config.discovery_interval}秒")
        self.logger.info(f"修復間隔: {self.config.repair_interval}秒")
        self.logger.info(f"測試間隔: {self.config.test_interval}秒")

        self.is_running = True
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()

        self.logger.info("✅ 系統自維護管理器啟動成功")
        return True

    def stop_self_maintenance(self) -> bool:
        """停止自維護系統"""
        if not self.is_running:
            self.logger.warning("自維護系統未運行")
            return False

        self.logger.info("🛑 停止系統自維護管理器...")
        self.is_running = False

        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=30)

        self.logger.info("✅ 系統自維護管理器已停止")
        return True

    def _maintenance_loop(self):
        """維護循環主邏輯"""
        self.logger.info("🔄 維護循環已啟動")

        last_discovery = time.time()
        last_repair = time.time()
        last_test = time.time()

        while self.is_running:
            try:
                current_time = time.time()

                # 問題發現循環
                if current_time - last_discovery >= self.config.discovery_interval:
                    self._run_discovery_cycle()
                    last_discovery = current_time

                # 修復循環
                if current_time - last_repair >= self.config.repair_interval:
                    self._run_repair_cycle()
                    last_repair = current_time

                # 測試循環
                if current_time - last_test >= self.config.test_interval:
                    self._run_test_cycle()
                    last_test = current_time

                # 檢查是否需要緊急維護
                if self.emergency_repair_needed:
                    self._run_emergency_maintenance()
                    self.emergency_repair_needed = False

                time.sleep(10)  # 每10秒檢查一次

            except Exception as e:
                self.logger.error(f"維護循環錯誤, {e}")
                time.sleep(60)  # 發生錯誤後等待1分鐘再繼續

    def _run_discovery_cycle(self):
        """運行問題發現循環 - 完整版實現"""
        self.logger.info("🔍 開始問題發現循環 (完整版)...")
        self.maintenance_cycle_active = True

        try:
            start_time = time.time()

            # 優先使用增強版檢測引擎
            if hasattr(self, "detection_engine") and self.detection_engine:
                self.logger.info("使用增強版完整檢測引擎...")

                # 獲取或創建新的事件循環
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # 運行異步檢測
                detection_result = loop.run_until_complete(
                    self.detection_engine.run_enhanced_complete_detection(".")
                )

                # 提取問題列表並快取
                issues = detection_result.get("detection_results", {}).get("issues", [])
                issues_found = len(issues)

                # 快取發現結果供修復階段使用
                self.last_discovery_results = detection_result
                self.logger.info(f"快取發現結果, {issues_found} 個問題")

            else:
                # 使用標準發現系統並快取
                self.logger.info("使用標準問題發現系統...")
                discovery_result = self.discovery_system.run_complete_discovery()
                issues = discovery_result.get("issues_found", [])
                issues_found = len(issues)

                # 快取發現結果
                self.last_discovery_results = discovery_result
                self.logger.info(f"快取發現結果, {issues_found} 個問題")

            # 更新統計信息
            self.maintenance_stats["issues_discovered"] += issues_found

            elapsed_time = time.time() - start_time
            self.logger.info(
                f"✅ 問題發現完成, 耗時 {elapsed_time:.2f} 秒, 發現 {issues_found} 個問題"
            )

            # 如果發現嚴重問題, 觸發緊急修復
            if issues_found > 0:
                self.emergency_repair_needed = True
                self.logger.info(f"🚨 發現 {issues_found} 個問題, 將觸發緊急修復")

        except Exception as e:
            self.logger.error(f"問題發現循環錯誤, {e}")
            self.logger.error(f"詳細錯誤, {traceback.format_exc()}")
        finally:
            self.maintenance_cycle_active = False

    def _run_repair_cycle(self):
        """運行修復循環 - 完整版實現"""
        self.logger.info("🔧 開始修復循環 (完整版)...")
        self.maintenance_cycle_active = True

        try:
            start_time = time.time()

            # 獲取待修復問題
            issues_to_repair = self._get_issues_for_repair()

            if issues_to_repair:
                self.logger.info(f"發現 {len(issues_to_repair)} 個待修復問題")

                # 優先使用新的统一自动修复 system 集成管理器(如果可用)
                if HAS_INTEGRATION_MANAGER:
                    self.logger.info("使用统一自动修复系统集成管理器...")

                    # 获取集成管理器
                    from auto_repair_integration_manager import (
                        get_auto_repair_manager,
                        RepairSystemType,
                    )

                    integration_manager = get_auto_repair_manager()

                    # 使用默认的统一系统
                    repair_result = integration_manager.run_auto_repair(
                        ".", RepairSystemType.UNIFIED
                    )

                    # 提取修复统计
                    completed = repair_result.get("successful_repairs", 0)
                    failed = repair_result.get("failed_repairs", 0)
                    total_attempts = repair_result.get("total_issues", 0)

                    self.logger.info(
                        f"📊 统一修复統計, 嘗試 {total_attempts} 個, 成功 {completed} 個, 失敗 {failed} 個"
                    )

                    # 记录系统使用信息
                    system_used = repair_result.get("system_used", "unknown")
                    self.logger.info(f"使用的修复系统, {system_used}")

                # 如果集成管理器不可用, 使用增强版完整修复系统
                elif HAS_ENHANCED_REPAIR:
                    self.logger.info("使用增强版完整修复系统...")

                    # 创建修复系统实例
                    repair_system = EnhancedCompleteRepairSystem(max_workers=4)

                    # 运行完整修复
                    repair_result = repair_system.run_complete_repair(".")

                    # 提取修复统计
                    completed = repair_result.get("successful_repairs", 0)
                    failed = repair_result.get("failed_repairs", 0)
                    total_attempts = repair_result.get("total_issues", 0)

                    self.logger.info(
                        f"📊 增强版修复统计, 尝试 {total_attempts} 個, 成功 {completed} 個, 失敗 {failed} 個"
                    )

                elif hasattr(self.fix_system, "run_enhanced_intelligent_repair"):
                    # 使用增強版智能修復系統 (AGI Level 3)
                    self.logger.info("使用增強版智能修復系統 (AGI Level 3)...")
                    repair_result = self.fix_system.run_enhanced_intelligent_repair(".")

                    # 提取修復統計
                    repair_results = repair_result.get("repair_results", [])
                    completed = sum(1 for r in repair_results if r.get("success"))
                    failed = sum(1 for r in repair_results if not r.get("success"))

                    # 記錄學習進展
                    learning_updates = repair_result.get("learning_updates", {})
                    if learning_updates:
                        self.logger.info(
                            f"🧠 學習進展: {learning_updates.get('patterns_learned', 0)} 個模式"
                        )

                elif hasattr(self.fix_system, "run_enhanced_fix"):
                    # 使用標準修復系統
                    self.logger.info("使用標準自動修復系統...")
                    repair_result = self.fix_system.run_enhanced_fix(issues_to_repair)
                    completed = repair_result.get("repairs_completed", 0)
                    failed = repair_result.get("repairs_failed", 0)
                else:
                    self.logger.error("❌ 沒有可用的修復系統")
                    completed = 0
                    failed = len(issues_to_repair)

                # 更新統計信息
                self.maintenance_stats["successful_repairs"] += completed
                self.maintenance_stats["failed_repairs"] += failed

                elapsed_time = time.time() - start_time
                self.logger.info(
                    f"✅ 修復完成, 耗時 {elapsed_time:.2f} 秒, 成功 {completed} 個, 失敗 {failed} 個"
                )

                # 記錄性能統計
                if "performance_stats" in repair_result:
                    perf_stats = repair_result.get("performance_stats")
                    self.logger.info(
                        f"📊 性能統計, 成功率 {perf_stats.get('success_rate', 0):.1f}%"
                    )

                # 使用增強版智能驗證器進行二次驗證
                if completed > 0:
                    self._perform_intelligent_validation(repair_result, completed, failed)

            else:
                self.logger.info("沒有需要修復的問題")

        except Exception as e:
            self.logger.error(f"修復循環錯誤, {e}")
            self.logger.error(f"詳細錯誤, {traceback.format_exc()}")
        finally:
            self.maintenance_cycle_active = False

    def _run_test_cycle(self):
        """運行測試循環"""
        self.logger.info("🧪 開始測試循環...")
        self.maintenance_cycle_active = True

        try:
            start_time = time.time()

            # 根據模式選擇測試策略
            if self.config.mode == MaintenanceMode.FULL:
                test_result = self.test_system.run_comprehensive_test_update()
            else:
                test_result = self.test_system.run_comprehensive_test_update()

            # 更新統計信息
            tests_run = test_result.get("tests_run", 0)
            tests_passed = test_result.get("tests_passed", 0)
            self.maintenance_stats["tests_run"] += tests_run
            self.maintenance_stats["tests_passed"] += tests_passed

            elapsed_time = time.time() - start_time
            self.logger.info(
                f"✅ 測試完成, 耗時 {elapsed_time:.2f} 秒, 運行 {tests_run} 個測試, 通過 {tests_passed} 個"
            )

        except Exception as e:
            self.logger.error(f"測試循環錯誤, {e}")
        finally:
            self.maintenance_cycle_active = False

    def _run_emergency_maintenance(self):
        """運行緊急維護"""
        self.logger.info("🚨 開始緊急維護...")

        try:
            # 緊急維護邏輯
            self._run_discovery_cycle()
            self._run_repair_cycle()
            self._run_test_cycle()

            self.logger.info("✅ 緊急維護完成")

        except Exception as e:
            self.logger.error(f"緊急維護錯誤: {e}")

    def _get_issues_for_repair(self) -> List[Dict[str, Any]]:
        """獲取待修復問題 - 完整實現"""
        self.logger.info("🔍 獲取待修復問題列表...")

        try:
            # 從最近的問題發現結果中獲取問題
            if hasattr(self, "last_discovery_results") and self.last_discovery_results:
                discovery_data = self.last_discovery_results
                if isinstance(discovery_data, dict):
                    # 從增強版檢測引擎獲取
                    if "detection_results" in discovery_data:
                        issues = discovery_data["detection_results"].get("issues", [])
                        self.logger.info(f"從增強檢測引擎獲取 {len(issues)} 個問題")
                        return issues

                    # 從標準發現系統獲取
                    elif "issues_found" in discovery_data:
                        issues = discovery_data.get("issues_found", [])
                        self.logger.info(f"從標準發現系統獲取 {len(issues)} 個問題")
                        return issues

            # 如果沒有快取的發現結果, 執行新的發現
            self.logger.info("沒有快取的發現結果, 執行新的問題發現...")

            # 執行快速問題發現
            if hasattr(self, "discovery_system") and self.discovery_system:
                if (
                    USE_ENHANCED_SYSTEMS
                    and hasattr(self, "detection_engine")
                    and self.detection_engine
                ):
                    # 使用增強版檢測引擎
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    discovery_result = loop.run_until_complete(
                        self.detection_engine.run_enhanced_complete_detection(".")
                    )

                    issues = discovery_result.get("detection_results", {}).get("issues", [])
                    self.logger.info(f"新發現 {len(issues)} 個問題")

                    # 快取結果
                    self.last_discovery_results = discovery_result
                    return issues

                else:
                    # 使用標準發現系統
                    discovery_result = self.discovery_system.run_complete_discovery()
                    issues = discovery_result.get("issues_found", [])
                    self.logger.info(f"新發現 {len(issues)} 個問題")

                    # 快取結果
                    self.last_discovery_results = discovery_result
                    return issues

            self.logger.warning("沒有可用的問題發現系統")
            return []

        except Exception as e:
            self.logger.error(f"獲取待修復問題失敗, {e}")
            self.logger.error(f"詳細錯誤, {traceback.format_exc()}")
            return []

    async def auto_repair_dependencies(self, module_names: List[str]):
        """自動修復缺失的依賴"""
        self.logger.info(f"嘗試自動修復依賴: {module_names}")
        import subprocess

        for module in module_names:
            try:
                # 建立模塊名到 pip 包名的映射 (簡單邏輯)
                package_map = {
                    "cv2": "opencv-python",
                    "yaml": "pyyaml",
                    "psutil": "psutil",
                    "numpy": "numpy",
                    "fastapi": "fastapi",
                    "uvicorn": "uvicorn",
                }
                package_name = package_map.get(module, module)

                self.logger.info(f"正在安裝 {package_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                self.logger.info(f"✅ {package_name} 安裝成功")
            except Exception as e:
                self.logger.error(f"❌ 無法安裝 {module}: {e}")

    def get_maintenance_status(self) -> Dict[str, Any]:
        """獲取維護狀態"""
        return {
            "is_running": self.is_running,
            "mode": self.config.mode.value,
            "stats": self.maintenance_stats.copy(),
            "last_maintenance_time": self.last_maintenance_time,
            "cycle_active": self.maintenance_cycle_active,
            "emergency_needed": self.emergency_repair_needed,
        }

    def trigger_emergency_maintenance(self):
        """手動觸發緊急維護"""
        self.emergency_repair_needed == True
        self.logger.info("🚨 手動觸發緊急維護")

    def _perform_intelligent_validation(self, repair_result: Dict, completed: int, failed: int):
        """執行增強版智能驗證"""
        if not HAS_SMART_VALIDATOR or not EnhancedSmartRepairValidator:
            self.logger.info("⚠️ 智能驗證器不可用，跳過驗證")
            return

        self.logger.info("🔍 使用增強版智能驗證器進行修復質量驗證...")
        try:
            # 創建智能驗證器實例
            validator = EnhancedSmartRepairValidator()

            # 獲取修復結果列表
            repair_results = repair_result.get("repair_results", [])

            # 對修復結果進行智能驗證
            validation_results = []
            for result in repair_results:
                if result.get("success") and "file" in result:
                    file_path = result["file"]
                    if Path(file_path).exists():
                        # 獲取原始問題信息
                        issue_type = result.get("issue_type", "unknown")
                        confidence = result.get("confidence", 0.5)

                        # 執行智能驗證
                        validation_result = validator.validate_repair_intelligent(
                            file_path=file_path, issue_type=issue_type, confidence=confidence
                        )

                        validation_results.append(
                            {
                                "file": file_path,
                                "validation_result": validation_result,
                                "original_repair": result,
                            }
                        )

            # 分析驗證結果
            valid_repairs = sum(
                1
                for vr in validation_results
                if vr["validation_result"].get("overall_success", False)
            )
            total_validated = len(validation_results)

            self.logger.info(
                f"📊 智能驗證完成, {valid_repairs} / {total_validated} 個修復通過二次驗證"
            )

            # 如果驗證成功率過低, 發出警告
            if total_validated > 0:
                validation_success_rate = (valid_repairs / total_validated) * 100
                if validation_success_rate < 50:
                    self.logger.warning(
                        f"🚨 智能驗證成功率過低 ({validation_success_rate:.1f}%), 建議檢查修復策略"
                    )
                elif validation_success_rate < 80:
                    self.logger.info(
                        f"⚠️ 智能驗證成功率中等 ({validation_success_rate:.1f}%), 可考慮優化"
                    )
                else:
                    self.logger.info(f"✅ 智能驗證成功率良好 ({validation_success_rate:.1f}%)")

        except Exception as e:
            self.logger.error(f"智能驗證器執行失敗, {e}")
            self.logger.error(f"詳細錯誤, {traceback.format_exc()}")

    def update_config(self, new_config: MaintenanceConfig):
        """更新維護配置"""
        self.config = new_config
        self.logger.info(f"維護配置已更新, 新模式: {new_config.mode.value}")


# 全局實例
_maintenance_manager = None


def get_maintenance_manager() -> SystemSelfMaintenanceManager:
    """獲取全局維護管理器實例"""
    global _maintenance_manager
    if _maintenance_manager is None:
        _maintenance_manager = SystemSelfMaintenanceManager()
    return _maintenance_manager


def start_self_maintenance(mode: str = "full") -> bool:
    """啟動自維護系統 (全局函數)"""
    manager = get_maintenance_manager()

    # 設置模式
    if mode == "full":
        config = MaintenanceConfig(mode=MaintenanceMode.FULL)
    elif mode == "light":
        config = MaintenanceConfig(mode=MaintenanceMode.LIGHT)
    elif mode == "emergency":
        config = MaintenanceConfig(mode=MaintenanceMode.EMERGENCY)
    else:
        config = MaintenanceConfig(mode=MaintenanceMode.FULL)

    manager.update_config(config)
    return manager.start_self_maintenance()


def stop_self_maintenance() -> bool:
    """停止自維護系統 (全局函數)"""
    manager = get_maintenance_manager()
    return manager.stop_self_maintenance()


def get_maintenance_status() -> Dict[str, Any]:
    """獲取維護狀態 (全局函數)"""
    manager = get_maintenance_manager()
    return manager.get_maintenance_status()


def trigger_emergency_maintenance():
    """觸發緊急維護 (全局函數)"""
    manager = get_maintenance_manager()
    manager.emergency_repair_needed = True
    manager.logger.info("🚨 手動觸發緊急維護")


if __name__ == "__main__":
    # 測試自維護系統
    logging.basicConfig(level=logging.INFO)

    print("🚀 測試系統自維護管理器...")

    # 啟動完整功能模式
    if start_self_maintenance("full"):
        print("✅ 自維護系統已啟動")

        # 運行一段時間
        try:
            print("🔄 系統自維護運行中... (按 Ctrl + C 停止)")
            while True:
                status = get_maintenance_status()
                print(
                    f"狀態: 運行中 = {status['is_running']} | 任務週期 = {status['stats']['total_maintenance_cycles']} | 修復成功 = {status['stats']['successful_repairs']}"
                )
                time.sleep(30)  # 每30秒報告一次狀態
        except KeyboardInterrupt:
            print("\n🛑 用戶中斷, 停止自維護系統...")

        # 停止系統
        stop_self_maintenance()
        print("✅ 自維護系統已停止")
    else:
        print("❌ 無法啟動自維護系統")
