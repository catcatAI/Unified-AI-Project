# Angela Matrix: Demo Learning - α=β=0.8, γ=0.4, δ=0.3 (V×L×P×M)
"""
演示學習管理器
當檢測到演示金鑰時自動啟動學習、初始化、清除功能
"""

# TODO: Fix import - module 'asyncio' not found
import asyncio
import logging
import json
import re
# from tests.tools.test_tool_dispatcher_logging import
# from tests.test_json_fix import
# TODO: Fix import - module 'yaml' not found
# import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
# from tests.core_ai import
# from ...core.shared.utils.cleanup_utils import

logger: Any = logging.getLogger(__name__)


class DemoLearningManager:
    """演示學習管理器"""

    def __init__(self, config_path: str = "configs/demo_credentials.yaml") -> None:
        """初始化演示學習管理器

        Args:
            config_path: 演示配置文件路徑
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.demo_mode = False
        self.learning_data: Dict[str, Any] = {
            'user_interactions': [],
            'error_patterns': {},
            'performance_metrics': [],
            'system_events': [],
            'initialized_at': ''
        }
        self.initialized = False

        # 學習數據存儲路徑
        self.storage_path = Path(self.config.get('demo_credentials')
                                .get('auto_learning')
                                .get('storage')
                                .get('path', 'data/demo_learning'))
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """加載配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"加載配置文件失敗: {e}")
            return {}

    def detect_demo_credentials(self, credentials: Dict[str, Any]) -> bool:
        """檢測是否為演示金鑰

        Args:
            credentials: 認證信息字典

        Returns:
            bool 是否為演示金鑰
        """
        demo_patterns = self.config.get('key_detection').get('demo_patterns')

        # 檢查所有認證信息
        for key, value in credentials.items():
            if isinstance(value, str):
                for pattern in demo_patterns:
                    if re.match(pattern, value):
                        logger.info(f"檢測到演示金鑰: {key} = {value}")
                        return True

        return False

    async def activate_demo_mode(self, credentials: Dict[str, Any]):
        """激活演示模式

        Args:
            credentials: 認證信息
        """
        if not self.detect_demo_credentials(credentials):
            return

        logger.info("激活演示模式")
        self.demo_mode = True

        # 執行演示模式激活步驟
        actions = self.config.get('key_detection').get('on_demo_key_detected')
        actions.sort(key=lambda x: x.get('priority', 999))

        for action in actions:
            action_name = action.get('action')
            try:
                await self._execute_action(action_name)
            except Exception as e:
                logger.error(f"執行動作失敗 {action_name}: {e}")

    async def _execute_action(self, action_name: str):
        """執行指定動作

        Args:
            action_name: 動作名稱
        """
        if action_name == "enable_demo_mode":
            await self._enable_demo_mode()
        elif action_name == "initialize_learning":
            await self._initialize_learning()
        elif action_name == "setup_mock_services":
            await self._setup_mock_services()
        elif action_name == "configure_auto_cleanup":
            await self._configure_auto_cleanup()
        else:
            logger.warning(f"未知動作: {action_name}")

    async def _enable_demo_mode(self):
        """啟用演示模式"""
        logger.info("啟用演示模式")

        # 創建演示模式標記文件
        demo_flag = self.storage_path / "demo_mode.flag"
        with open(demo_flag, 'w') as f:
            json.dump({
                'enabled': True,
                'activated_at': datetime.now().isoformat(),
                'config': self.config.get('demo_credentials').get('demo_mode')
            }, f, indent=2)

    async def _initialize_learning(self):
        """初始化學習系統"""
        logger.info("初始化學習系統")

        learning_config = self.config.get('demo_credentials').get('auto_learning')
        if not learning_config.get('enabled', False):
            return

        # 初始化學習數據結構
        self.learning_data['initialized_at'] = datetime.now().isoformat()
        # 保存初始學習數據
        await self._save_learning_data()
        # 啟動學習監控
        asyncio.create_task(self._learning_monitor_loop())

        logger.info("學習系統初始化完成")

    async def _setup_mock_services(self):
        """設置模擬服務"""
        logger.info("設置模擬服務")

        mock_config = self.config.get('mock_services')
        if not mock_config.get('enabled', False):
            return

        # 創建模擬服務配置文件
        mock_config_file = self.storage_path / "mock_services.json"
        with open(mock_config_file, 'w') as f:
            json.dump(mock_config, f, indent=2)

        logger.info("模擬服務設置完成")

    async def _configure_auto_cleanup(self):
        """配置自動清除"""
        logger.info("配置自動清除")

        cleanup_config = self.config.get('demo_credentials').get('auto_cleanup')
        if not cleanup_config.get('enabled', False):
            return

        # 啟動清除監控
        asyncio.create_task(self._cleanup_monitor_loop())

        logger.info("自動清除配置完成")

    async def _learning_monitor_loop(self):
        """學習監控循環"""
        while self.demo_mode:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                await self._collect_learning_data()
            except Exception as e:
                logger.error(f"學習監控錯誤: {e}")

    async def _cleanup_monitor_loop(self):
        """清除監控循環"""
        cleanup_config = self.config.get('demo_credentials').get('auto_cleanup')

        while self.demo_mode:
            try:
                await asyncio.sleep(3600)  # 每小時檢查一次
                await self._perform_cleanup(cleanup_config)
            except Exception as e:
                logger.error(f"清除監控錯誤: {e}")

    async def _collect_learning_data(self):
        """收集學習數據"""
        try:
            # 收集系統指標
            system_metrics = {
                'timestamp': datetime.now().isoformat(),
                'memory_usage': self._get_memory_usage(),
                'storage_usage': self._get_storage_usage(),
                'active_connections': self._get_active_connections()
            }

            # 確保 performance_metrics 是列表
            if 'performance_metrics' not in self.learning_data:
                self.learning_data['performance_metrics'] = []
            elif not isinstance(self.learning_data['performance_metrics'], list):
                self.learning_data['performance_metrics'] = []

            self.learning_data['performance_metrics'].append(system_metrics)

            # 限制數據大小
            if isinstance(self.learning_data['performance_metrics'], list):
                if len(self.learning_data['performance_metrics']) > 1000:
                    self.learning_data['performance_metrics'] = \
                        self.learning_data['performance_metrics'][-500:]

            await self._save_learning_data()
        except Exception as e:
            logger.error(f"收集學習數據失敗: {e}")

    async def _perform_cleanup(self, cleanup_config: Dict[str, Any]):
        """執行清除操作

        Args:
            cleanup_config: 清除配置
        """
        try:
            targets = cleanup_config.get('cleanup_targets')
            retention = cleanup_config.get('retention')

            for target in targets:
                if target == "temporary_files":
                    cleanup_temp_files()
                elif target == "cache_data":
                    cleanup_cache_data(retention.get('cache_data', 1))
                elif target == "log_files":
                    cleanup_log_files(retention.get('important_logs', 7))
                elif target == "demo_artifacts":
                    cleanup_demo_artifacts(retention.get('demo_data', 30), self.storage_path())

            logger.info("清除操作完成")

        except Exception as e:
            logger.error(f"清除操作失敗: {e}")

    def _get_memory_usage(self) -> Dict[str, Any]:
        """獲取內存使用情況"""
        try:
            # TODO: Fix import - module 'psutil' not found
            # import psutil
            process = psutil.Process()
            return {
                'rss': process.memory_info().rss,
                'vms': process.memory_info().vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}

    def _get_storage_usage(self) -> Dict[str, Any]:
        """獲取存儲使用情況"""
        try:
            total_size = 0
            for file_path in self.storage_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return {
                'total_bytes': total_size,
                'total_mb': total_size / (1024 * 1024),
                'file_count': len(list(self.storage_path.rglob("*")))
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_active_connections(self) -> int:
        """獲取活躍連接數"""
        # 這裡可以實現實際的連接計數邏輯
        return 0

    async def _save_learning_data(self):
        """保存學習數據"""
        try:
            learning_file = self.storage_path / "learning_data.json"
            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存學習數據失敗: {e}")

    async def record_user_interaction(self, action: str, context: Dict[str, Any], result: str, feedback: Optional[str] = None):
        """記錄用戶交互

        Args:
            action: 動作名稱
            context: 上下文信息
            result: 結果
            feedback: 用戶反饋
        """
        if not self.demo_mode:
            return

        interaction = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'context': context,
            'result': result,
            'feedback': feedback
        }

        # 確保 user_interactions 是列表
        if 'user_interactions' not in self.learning_data:
            self.learning_data['user_interactions'] = []
        elif not isinstance(self.learning_data['user_interactions'], list):
            self.learning_data['user_interactions'] = []

        self.learning_data['user_interactions'].append(interaction)

        # 限制數據大小
        if isinstance(self.learning_data['user_interactions'], list):
            if len(self.learning_data['user_interactions']) > 1000:
                self.learning_data['user_interactions'] = \
                    self.learning_data['user_interactions'][-500:]

        await self._save_learning_data()

    async def record_error_pattern(self, error_type: str, error_message: str, context: Dict[str, Any], resolution: str):
        """記錄錯誤模式

        Args:
            error_type: 錯誤類型
            error_message: 錯誤消息
            context: 上下文
            resolution: 解決方案
        """
        if not self.demo_mode:
            return

        error_key = f"{error_type}{error_message}"

        # 確保 error_patterns 是字典
        if 'error_patterns' not in self.learning_data:
            self.learning_data['error_patterns'] = {}
        elif not isinstance(self.learning_data['error_patterns'], dict):
            self.learning_data['error_patterns'] = {}

        if error_key in self.learning_data['error_patterns']:
            if isinstance(self.learning_data['error_patterns'][error_key], dict):
                current_frequency = self.learning_data['error_patterns'][error_key].get('frequency', 0)
                self.learning_data['error_patterns'][error_key]['frequency'] = current_frequency + 1
                self.learning_data['error_patterns'][error_key]['last_seen'] = datetime.now().isoformat()
        else:
            self.learning_data['error_patterns'][error_key] = {
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'resolution': resolution,
                'frequency': 1,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }

        await self._save_learning_data()

    async def get_learning_insights(self) -> Dict[str, Any]:
        """獲取學習洞察

        Returns:
            Dict: 學習洞察數據
        """
        if not self.demo_mode:
            return {}

        try:
            # 分析用戶交互模式
            interaction_analysis = self._analyze_interactions()
            # 分析錯誤模式
            error_analysis = self._analyze_errors()
            # 分析性能趨勢
            performance_analysis = self._analyze_performance()
            return {
                'demo_mode': self.demo_mode,
                'data_collection_period': self._get_collection_period(),
                'interactions': interaction_analysis,
                'errors': error_analysis,
                'performance': performance_analysis,
                'recommendations': self._generate_recommendations()
            }

        except Exception as e:
            logger.error(f"獲取學習洞察失敗: {e}")
            return {'error': str(e)}

    def _analyze_interactions(self) -> Dict[str, Any]:
        """分析用戶交互"""
        interactions = self.learning_data.get('user_interactions')

        if not interactions:
            return {'total': 0}

        # 統計動作頻率
        action_counts: Dict[str, int] = {}
        for interaction in interactions:
            if isinstance(interaction, dict):
                action = interaction.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1

        # 計算成功率
        success_count = sum(1 for i in interactions if isinstance(i, dict) and i.get('result') == 'success')
        success_rate = success_count / len(interactions) if interactions else 0
        return {
            'total': len(interactions),
            'success_rate': success_rate,
            'most_common_actions': sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'recent_activity': interactions[-10:] if len(interactions) > 10 else interactions
        }

    def _analyze_errors(self) -> Dict[str, Any]:
        """分析錯誤模式"""
        errors = self.learning_data.get('error_patterns')

        if not errors:
            return {'total': 0}

        # 按頻率排序
        sorted_errors = sorted(errors.items(), key=lambda x: x[1].get('frequency', 0) if isinstance(x[1], dict) else 0, reverse=True)
        return {
            'total': len(errors),
            'most_frequent': sorted_errors[:5],
            'total_occurrences': sum(e[1].get('frequency', 0) if isinstance(e[1], dict) else 0 for e in errors.items())
        }

    def _analyze_performance(self) -> Dict[str, Any]:
        """分析性能趨勢"""
        metrics = self.learning_data.get('performance_metrics')

        if not metrics:
            return {'samples': 0}

        # 計算平均值
        if metrics:
            avg_memory = sum(m.get('memory_usage', {}).get('percent', 0) if isinstance(m, dict) and isinstance(m.get('memory_usage'), dict) else 0 for m in metrics) / len(metrics)
            avg_storage = sum(m.get('storage_usage', {}).get('total_mb', 0) if isinstance(m, dict) and isinstance(m.get('storage_usage'), dict) else 0 for m in metrics) / len(metrics)
        else:
            avg_memory = avg_storage = 0

        return {
            'samples': len(metrics),
            'avg_memory_percent': avg_memory,
            'avg_storage_mb': avg_storage,
            'latest_metrics': metrics[-1] if metrics else None
        }

    def _generate_recommendations(self) -> List[str]:
        """生成建議"""
        recommendations: List[str] = []

        # 基於錯誤模式的建議
        errors = self.learning_data.get('error_patterns')
        if len(errors) > 5:
            recommendations.append("檢測到多種錯誤模式, 建議檢查系統配置")

        # 基於性能的建議
        metrics = self.learning_data.get('performance_metrics')
        if metrics:
            latest = metrics[-1]
            if isinstance(latest, dict):
                memory_usage = latest.get('memory_usage')
                if isinstance(memory_usage, dict):
                    memory_percent = memory_usage.get('percent', 0)
                    if memory_percent > 80:
                        recommendations.append("內存使用率較高, 建議優化內存使用")

        # 基於交互的建議
        interactions = self.learning_data.get('user_interactions')
        if interactions:
            success_count = sum(1 for i in interactions if isinstance(i, dict) and i.get('result') == 'success')
            success_rate = success_count / len(interactions) if len(interactions) > 0 else 0
            if success_rate < 0.8:
                recommendations.append("操作成功率較低, 建議檢查用戶體驗")

        return recommendations

    def _get_collection_period(self) -> Dict[str, str]:
        """獲取數據收集週期"""
        interactions = self.learning_data.get('user_interactions')
        if not interactions:
            return {}

        timestamps = [i.get('timestamp') for i in interactions if isinstance(i, dict) and i.get('timestamp')]
        # 過濾掉 None 值和非字符串值
        filtered_timestamps: List[str] = [t for t in timestamps if isinstance(t, str)]

        if len(filtered_timestamps) >= 2:  # 需要至少兩個時間戳才能計算範圍
            return {
                'start': min(filtered_timestamps),
                'end': max(filtered_timestamps)
            }
        elif len(filtered_timestamps) == 1:  # 只有一個時間戳
            return {
                'start': filtered_timestamps[0],
                'end': filtered_timestamps[0]
            }

        return {}

    async def shutdown(self):
        """關閉演示學習管理器"""
        if self.demo_mode:
            logger.info("關閉演示學習管理器")

            # 執行最終清除
            cleanup_config = self.config.get('demo_credentials').get('auto_cleanup')
            if cleanup_config.get('enabled', False):
                triggers = cleanup_config.get('triggers')
                if 'session_end' in triggers:
                    await self._perform_cleanup(cleanup_config)

            # 保存最終學習數據
            await self._save_learning_data()
            # 生成學習報告
            insights = await self.get_learning_insights()
            report_file = self.storage_path / \
                f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)

            self.demo_mode = False
            logger.info("演示學習管理器已關閉")


# 全局實例
demo_learning_manager = DemoLearningManager()


# 占位函数
def cleanup_temp_files():
    pass

def cleanup_cache_data(days):
    pass

def cleanup_log_files(days):
    pass

def cleanup_demo_artifacts(days, path):
    pass