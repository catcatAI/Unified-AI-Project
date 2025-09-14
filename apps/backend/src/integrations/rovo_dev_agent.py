
"""
Rovo Dev Agent 核心实现
提供智能开发助手功能，集成 Atlassian 生态系统
"""

import asyncio
import logging
import pickle
import time
import traceback
import traceback
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from .enhanced_rovo_dev_connector import EnhancedRovoDevConnector
from .atlassian_bridge import AtlassianBridge
# Try to import from the full path first, fallback to relative import
try:
    from apps.backend.src.hsp.connector import HSPConnector
    from apps.backend.src.hsp.types import HSPMessage, HSPCapability, HSPTask
    from apps.backend.src.core_ai.agent_manager import AgentManager
except ImportError:
    # Fallback to relative imports
    try:
        from ...hsp.connector import HSPConnector
        from ...hsp.types import HSPMessage, HSPCapability, HSPTask
        from ...core_ai.agent_manager import AgentManager
    except ImportError:
        # If relative imports also fail, create mock classes
        class HSPConnector:
            def __init__(self, *args, **kwargs):
                pass
        
        class HSPMessage:
            pass
        
        class HSPCapability:
            pass
        
        class HSPTask:
            pass
        
        class AgentManager:
            pass

logger = logging.getLogger(__name__)

@dataclass
class TaskState:
    """任務狀態"""
    task_id: str
    task: HSPTask
    status: str  # 'pending', 'processing', 'completed', 'failed', 'retrying'
    start_time: datetime
    retry_count: int = 0
    last_error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

@dataclass
class AgentRecoveryState:
    """代理恢復狀態"""
    agent_id: str
    last_checkpoint: datetime
    active_tasks: List[str]
    completed_tasks: int
    failed_tasks: int
    recovery_mode: bool = False

class RovoDevAgent:
    """Rovo Dev Agent 主要实现类"""
    
    def __init__(self, config: Dict[str, Any], agent_manager: Optional[AgentManager] = None):
        """初始化 Rovo Dev Agent
        
        Args:
            config: 配置字典
            agent_manager: 代理管理器实例
        """
        self.config = config
        self.agent_manager = agent_manager
        self.connector = EnhancedRovoDevConnector(config)
        self.bridge = AtlassianBridge(self.connector)
        self.hsp_connector = HSPConnector(
            ai_id=config.get('hsp_integration', {}).get('agent_id', 'rovo-dev-agent'),
            broker_address=config.get('hsp_integration', {}).get('broker_address', '127.0.0.1'),
            broker_port=config.get('hsp_integration', {}).get('broker_port', 1883),
            mock_mode=config.get('hsp_integration', {}).get('mock_mode', False)
        )
        
        # 代理狀態
        self.agent_id = config.get('hsp_integration', {}).get('agent_id', 'rovo-dev-agent')
        self.is_active = False
        self.capabilities = self._load_capabilities()
        self.capabilities_dict = {cap['name']: cap for cap in self.capabilities}
        
        # 任務佇列和處理狀態
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.task_history = []
        self.task_states = {}  # 任務狀態追蹤
        
        # 錯誤恢復配置
        self.recovery_config = config.get('hsp_integration', {}).get('task_persistence', {})
        self.recovery_enabled = False # Temporarily disabled for debugging
        self.max_retry_attempts = config.get('hsp_integration', {}).get('task_persistence', {}).get('max_retry_attempts', 5)
        self.retry_delay = config.get('hsp_integration', {}).get('task_persistence', {}).get('retry_delay', 60)
        self.auto_recovery = False # Temporarily disabled for debugging
        
        # 持久化存儲
        self.storage_path = Path(self.recovery_config.get('storage_path', 'data/task_queue'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_path / f"{self.agent_id}_state.pkl"
        self.tasks_file = self.storage_path / f"{self.agent_id}_tasks.pkl"
        
        # 降級模式配置
        self.degraded_mode = False
        self.degraded_capabilities = set()
        self.critical_capabilities = {'issue_tracking', 'documentation_generation'}
        
        # 性能指標
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_retried': 0,
            'average_response_time': 0.0,
            'last_activity': None,
            'recovery_events': 0,
            'degraded_mode_activations': 0
        }
        
        # 恢復狀態
        self.recovery_state = AgentRecoveryState(
            agent_id=self.agent_id,
            last_checkpoint=datetime.now(),
            active_tasks=[],
            completed_tasks=0,
            failed_tasks=0
        )
        
    def _load_capabilities(self) -> List[HSPCapability]:
        """加载代理能力配置
        
        Returns:
            List[HSPCapability]: 能力列表
        """
        capabilities_config = self.config.get('atlassian', {}).get('rovo_dev', {}).get('capabilities', [])
        capabilities = []
        
        for cap_config in capabilities_config:
            if cap_config.get('enabled', False):
                capability = {
                    'name': cap_config['name'],
                    'description': cap_config['description'],
                    'version': "1.0.0",
                    'parameters': self._get_capability_parameters(cap_config['name'])
                }
                capabilities.append(capability)
                
        return capabilities
        
    def _get_capability_parameters(self, capability_name: str) -> Dict[str, Any]:
        """获取能力参数定义
        
        Args:
            capability_name: 能力名稱
            
        Returns:
            Dict: 參數定義
        """
        parameter_schemas = {
            'code_analysis': {
                'repository_url': {'type': 'string', 'required': True},
                'analysis_type': {'type': 'string', 'enum': ['quality', 'security', 'performance'], 'default': 'quality'},
                'output_format': {'type': 'string', 'enum': ['markdown', 'json'], 'default': 'markdown'}
            },
            'documentation_generation': {
                'source_path': {'type': 'string', 'required': True},
                'doc_type': {'type': 'string', 'enum': ['api', 'technical', 'user'], 'default': 'technical'},
                'confluence_space': {'type': 'string', 'required': False},
                'template': {'type': 'string', 'required': False}
            },
            'issue_tracking': {
                'project_key': {'type': 'string', 'required': True},
                'issue_type': {'type': 'string', 'enum': ['Bug', 'Task', 'Story', 'Epic'], 'default': 'Task'},
                'priority': {'type': 'string', 'enum': ['Highest', 'High', 'Medium', 'Low', 'Lowest'], 'default': 'Medium'},
                'assignee': {'type': 'string', 'required': False}
            },
            'project_management': {
                'project_key': {'type': 'string', 'required': True},
                'report_type': {'type': 'string', 'enum': ['status', 'progress', 'metrics'], 'default': 'status'},
                'time_period': {'type': 'string', 'enum': ['week', 'month', 'quarter'], 'default': 'week'}
            },
            'code_review': {
                'pull_request_url': {'type': 'string', 'required': True},
                'review_type': {'type': 'string', 'enum': ['automated', 'assisted'], 'default': 'automated'},
                'focus_areas': {'type': 'array', 'items': {'type': 'string'}, 'default': ['security', 'performance', 'style']}
            }
        }
        
        return parameter_schemas.get(capability_name, {})
        
    async def start(self):
        """启动 Rovo Dev Agent"""
        try:
            await self.connector.start()
            await self.hsp_connector.connect()
            self.is_active = True
            
            # Register capabilities with HSPConnector for post-connect synchronization
            self.hsp_connector.register_capability_provider(self._load_capabilities)

            # 恢復之前的狀態
            if self.recovery_enabled:
                await self._recover_state()
            
            # 启动任务处理循环
            asyncio.create_task(self._task_processing_loop())

            # 啟動恢復監控
            if self.auto_recovery:
                asyncio.create_task(self._recovery_monitoring_loop())
            
            # 啟動狀態檢查點
            asyncio.create_task(self._checkpoint_loop())
            
            logger.info(f"Rovo Dev Agent {self.agent_id} 启动成功")
            
        except Exception as e:
            logger.error(f"启动 Rovo Dev Agent 失败: {e}")
            await self._handle_startup_failure(e)
            raise
            
    async def stop(self):
        """停止 Rovo Dev Agent"""
        self.is_active = False
        
        # 保存當前狀態
        if self.recovery_enabled:
            await self._save_state()
        
        await self.connector.close()
        logger.info(f"Rovo Dev Agent {self.agent_id} 已停止")
        
    async def _task_processing_loop(self):
        """任务处理循环"""
        while self.is_active:
            try:
                # 等待任务，超时时间为1秒
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._process_task(task)
                
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                logger.error(f"任务处理循环错误: {e}\n{traceback.format_exc()}")
                
    async def _process_task(self, task: HSPTask):
        """处理单个任务
        
        Args:
            task: HSP 任務物件
        """
        start_time = datetime.now()
        task_id = task['task_id']
        
        try:
            self.active_tasks[task_id] = {
                'task': task,
                'start_time': start_time,
                'status': 'processing'
            }
            
            # 根據任務類型呼叫相應的處理方法
            result = await self._dispatch_task(task)
            
            # 計算處理時間
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新指標
            self._update_metrics(processing_time, success=True)
            
            # 記錄任務歷史
            self.task_history.append({
                'task_id': task_id,
                'capability': task['capability'],
                'status': 'completed',
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'result_summary': str(result)[:100] + '...' if len(str(result)) > 100 else str(result)
            })
            
            # 發送結果（如果有 agent_manager）
            if self.agent_manager:
                await self.agent_manager.send_task_result(task_id, result)
                
            logger.info(f"任務 {task_id} 處理完成，耗時 {processing_time:.2f}s")
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(processing_time, success=False)
            
            error_result = {
                'error': str(e),
                'task_id': task_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.task_history.append({
                'task_id': task_id,
                'capability': task['capability'],
                'status': 'failed',
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            
            if self.agent_manager:
                await self.agent_manager.send_task_error(task_id, error_result)
                
            logger.error(f"任务 {task_id} 处理失败: {e}")
            traceback.print_exc()
            
        finally:
            # 清理活動任務
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
    async def _dispatch_task(self, task: HSPTask) -> Dict[str, Any]:
        """分發任務到相應的處理方法
        
        Args:
            task: HSP 任務物件
            
        Returns:
            Dict: 任務處理結果
        """
        capability = task['capability']
        parameters = task['parameters']
        
        if capability == 'code_analysis':
            return await self._handle_code_analysis(parameters)
        elif capability == 'documentation_generation':
            return await self._handle_documentation_generation(parameters)
        elif capability == 'issue_tracking':
            return await self._handle_issue_tracking(parameters)
        elif capability == 'project_management':
            return await self._handle_project_management(parameters)
        elif capability == 'code_review':
            return await self._handle_code_review(parameters)
        else:
            raise ValueError(f"不支持的能力: {capability}")
            
    async def _handle_code_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理程式碼分析任務
        
        Args:
            parameters: 任務參數
            
        Returns:
            Dict: 分析結果
        """
        repository_url = parameters['repository_url']
        analysis_type = parameters.get('analysis_type', 'quality')
        output_format = parameters.get('output_format', 'markdown')
        
        # 模擬程式碼分析過程
        await asyncio.sleep(2)  # 模擬分析時間
        
        analysis_result = {
            'repository_url': repository_url,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'code_quality_score': 85,
                'test_coverage': 78,
                'complexity_score': 'Medium',
                'security_issues': 2,
                'performance_issues': 1
            },
            'recommendations': [
                '增加單元測試覆蓋率',
                '重構複雜度較高的函數',
                '修復發現的安全漏洞'
            ],
            'output_format': output_format
        }
        
        # 如果需要，創建 Confluence 頁面
        confluence_space = parameters.get('confluence_space')
        if confluence_space:
            page_content = self._format_analysis_report(analysis_result)
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"程式碼分析報告 - {datetime.now().strftime('%Y-%m-%d')}",
                content=page_content
            )
            analysis_result['confluence_page'] = page_result
            
        return analysis_result
        
    async def _handle_documentation_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理文件生成任務
        
        Args:
            parameters: 任務參數
            
        Returns:
            Dict: 生成結果
        """
        source_path = parameters['source_path']
        doc_type = parameters.get('doc_type', 'technical')
        confluence_space = parameters.get('confluence_space')
        template = parameters.get('template')
        
        # 模擬文件生成過程
        await asyncio.sleep(3)
        
        # 生成文件內容
        doc_content = self._generate_documentation_content(source_path, doc_type, template)
        
        result = {
            'source_path': source_path,
            'doc_type': doc_type,
            'timestamp': datetime.now().isoformat(),
            'content_length': len(doc_content),
            'content': doc_content
        }
        
        # 如果指定了 Confluence 空間，創建頁面
        if confluence_space:
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"{doc_type.title()} 文件 - {Path(source_path).name}",
                content=doc_content
            )
            result['confluence_page'] = page_result
            
        return result
        
    async def _handle_issue_tracking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理問題追蹤任務
        
        Args:
            parameters: 任務參數
            
        Returns:
            Dict: 創建結果
        """
        project_key = parameters['project_key']
        issue_type = parameters.get('issue_type', 'Task')
        priority = parameters.get('priority', 'Medium')
        assignee = parameters.get('assignee')
        
        # 創建 Jira 問題
        issue_data = {
            'summary': parameters.get('summary', '自動創建的問題'),
            'description': parameters.get('description', '由 Rovo Dev Agent 自動創建'),
            'issue_type': issue_type,
            'priority': priority,
            'assignee': assignee
        }
        
        jira_result = await self.bridge.create_jira_issue(
            project_key=project_key,
            **issue_data
        )
        
        return {
            'project_key': project_key,
            'issue_key': jira_result.get('key'),
            'issue_id': jira_result.get('id'),
            'timestamp': datetime.now().isoformat(),
            'jira_result': jira_result
        }
        
    async def _handle_project_management(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理專案管理任務
        
        Args:
            parameters: 任務參數
            
        Returns:
            Dict: 管理結果
        """
        project_key = parameters['project_key']
        report_type = parameters.get('report_type', 'status')
        time_period = parameters.get('time_period', 'week')
        
        # 獲取專案資料
        issues = await self.bridge.search_jira_issues(
            jql=f"project = {project_key} AND updated >= -{time_period}"
        )
        
        # 生成報告
        report = self._generate_project_report(issues, report_type, time_period)
        
        # 如果需要，創建 Confluence 頁面
        confluence_space = parameters.get('confluence_space')
        if confluence_space:
            report_content = self._format_project_report(report)
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"專案報告 - {project_key} - {datetime.now().strftime('%Y-%m-%d')}",
                content=report_content
            )
            report['confluence_page'] = page_result
            
        return report
        
    async def _handle_code_review(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理程式碼審查任務
        
        Args:
            parameters: 任務參數
            
        Returns:
            Dict: 審查結果
        """
        pull_request_url = parameters['pull_request_url']
        review_type = parameters.get('review_type', 'automated')
        focus_areas = parameters.get('focus_areas', ['security', 'performance', 'style'])
        
        # 模擬程式碼審查過程
        await asyncio.sleep(4)
        
        review_result = {
            'pull_request_url': pull_request_url,
            'review_type': review_type,
            'focus_areas': focus_areas,
            'timestamp': datetime.now().isoformat(),
            'findings': [
                {
                    'type': 'security',
                    'severity': 'medium',
                    'description': '發現潛在的 SQL 注入風險',
                    'file': 'src/database.py',
                    'line': 45
                },
                {
                    'type': 'performance',
                    'severity': 'low',
                    'description': '可以優化循環性能',
                    'file': 'src/utils.py',
                    'line': 123
                }
            ],
            'overall_score': 8.5,
            'recommendation': 'approve_with_suggestions'
        }
        
        return review_result
        
    def _update_metrics(self, processing_time: float, success: bool):
        """更新性能指標
        
        Args:
            processing_time: 處理時間
            success: 是否成功
        """
        if success:
            self.metrics['tasks_completed'] += 1
        else:
            self.metrics['tasks_failed'] += 1
            
        # 更新平均響應時間
        total_tasks = self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        if total_tasks > 0:
            current_avg = self.metrics['average_response_time']
            self.metrics['average_response_time'] = (
                (current_avg * (total_tasks - 1) + processing_time) / total_tasks
            )
            
        self.metrics['last_activity'] = datetime.now().isoformat()
        
    def _format_analysis_report(self, analysis_result: Dict[str, Any]) -> str:
        """格式化分析報告為 Markdown
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            str: Markdown 格式的報告
        """
        metrics = analysis_result['metrics']
        recommendations = analysis_result['recommendations']
        
        report = f"""# 程式碼分析報告

## 基本資訊
- **倉庫**: {analysis_result['repository_url']}
- **分析類型**: {analysis_result['analysis_type']}
- **分析時間**: {analysis_result['timestamp']}

## 品質指標
- **程式碼品質評分**: {metrics['code_quality_score']}/100
- **測試覆蓋率**: {metrics['test_coverage']}%
- **複雜度**: {metrics['complexity_score']}
- **安全問題**: {metrics['security_issues']} 個
- **性能問題**: {metrics['performance_issues']} 個

## 改進建議
"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
            
        return report
        
    def _generate_documentation_content(self, source_path: str, doc_type: str, template: Optional[str]) -> str:
        """生成文件內容
        
        Args:
            source_path: 原始碼路徑
            doc_type: 文件類型
            template: 模板名稱
            
        Returns:
            str: 生成的文件內容
        """
        # 這裡應該實現實際的文件生成邏輯
        # 目前返回模擬內容
        
        return f"""# {doc_type.title()} 文件

## 概述
本文檔基於 `{source_path}` 自動生成。

## 功能說明
[自動生成的功能說明]

## API 參考
[自動生成的 API 文件]

## 使用範例
[自動生成的使用範例]

---
*本文檔由 Rovo Dev Agent 自動生成於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _generate_project_report(self, issues: List[Dict], report_type: str, time_period: str) -> Dict[str, Any]:
        """生成專案報告
        
        Args:
            issues: 問題列表
            report_type: 報告類型
            time_period: 時間週期
            
        Returns:
            Dict: 專案報告
        """
        total_issues = len(issues)
        completed_issues = len([i for i in issues if i.get('status') == 'Done'])
        in_progress_issues = len([i for i in issues if i.get('status') == 'In Progress'])
        
        return {
            'report_type': report_type,
            'time_period': time_period,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': total_issues,
                'completed_issues': completed_issues,
                'in_progress_issues': in_progress_issues,
                'completion_rate': (completed_issues / total_issues * 100) if total_issues > 0 else 0
            },
            'issues': issues
        }
        
    def _format_project_report(self, report: Dict[str, Any]) -> str:
        """格式化專案報告為 Markdown
        
        Args:
            report: 專案報告資料
            
        Returns:
            str: Markdown 格式的報告
        """
        summary = report['summary']
        
        return f"""# 專案報告

## 報告資訊
- **報告類型**: {report['report_type']}
- **時間週期**: {report['time_period']}
- **生成時間**: {report['timestamp']}

## 專案概況
- **總問題數**: {summary['total_issues']}
- **已完成**: {summary['completed_issues']}
- **進行中**: {summary['in_progress_issues']}
- **完成率**: {summary['completion_rate']:.1f}%

## 詳細資訊
[詳細的問題列表和分析]

---
*本報告由 Rovo Dev Agent 自動生成*
"""

    async def submit_task(self, task: HSPTask):
        """提交任務到處理佇列
        
        Args:
            task: HSP 任務物件
        """
        await self.task_queue.put(task)
        logger.info(f"任務 {task['task_id']} 已提交到佇列")
        
    async def get_status(self) -> Dict[str, Any]:
        """獲取代理狀態"""
        health_check_result = await self.connector.health_check() if self.is_active else None
        return {
            'agent_id': self.agent_id,
            'is_active': self.is_active,
            'capabilities': [cap['name'] for cap in self.capabilities],
            'queue_size': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'metrics': self.metrics,
            'connector_health': health_check_result
        }
        
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取任務歷史
        
        Args:
            limit: 返回記錄數限制
            
        Returns:
            List: 任務歷史記錄
        """
        return self.task_history[-limit:] if self.task_history else []
    
    # ==================== 錯誤恢復機制 ====================
    
    async def _recover_state(self):
        """恢復代理狀態"""
        try:
            # 恢復代理狀態
            if self.state_file.exists():
                with open(self.state_file, 'rb') as f:
                    saved_state = pickle.load(f)
                    self.recovery_state = saved_state
                    self.metrics.update(saved_state.__dict__)
                    logger.info(f"恢復代理狀態: {self.agent_id}")
            
            # 恢復未完成的任務
            if self.tasks_file.exists():
                with open(self.tasks_file, 'rb') as f:
                    saved_tasks = pickle.load(f)
                    for task_state in saved_tasks:
                        if task_state.status in ['pending', 'processing', 'retrying']:
                            # 重新提交任務
                            await self.task_queue.put(task_state.task)
                            self.task_states[task_state.task_id] = task_state
                            logger.info(f"恢復任務: {task_state.task_id}")
                    
                    self.metrics['recovery_events'] += 1
                    
        except Exception as e:
            logger.error(f"狀態恢復失敗: {e}")
    
    async def _save_state(self):
        """保存代理狀態"""
        try:
            # 更新恢復狀態
            self.recovery_state.last_checkpoint = datetime.now()
            self.recovery_state.active_tasks = list(self.active_tasks.keys())
            self.recovery_state.completed_tasks = self.metrics['tasks_completed']
            self.recovery_state.failed_tasks = self.metrics['tasks_failed']
            
            # 保存代理狀態
            with open(self.state_file, 'wb') as f:
                pickle.dump(self.recovery_state, f)
            
            # 保存任務狀態
            task_states_list = list(self.task_states.values())
            with open(self.tasks_file, 'wb') as f:
                pickle.dump(task_states_list, f)
                
            logger.debug(f"保存代理狀態: {self.agent_id}")
            
        except Exception as e:
            logger.error(f"狀態保存失敗: {e}")
    
    async def _checkpoint_loop(self):
        """定期檢查點循環"""
        while self.is_active:
            try:
                await asyncio.sleep(300)  # 每5分鐘保存一次
                await self._save_state()
            except Exception as e:
                logger.error(f"檢查點錯誤: {e}")
    
    async def _recovery_monitoring_loop(self):
        """恢復監控循環"""
        while self.is_active:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                await self._check_task_health()
                await self._check_system_health()
            except Exception as e:
                logger.error(f"恢復監控錯誤: {e}")
    
    async def _check_task_health(self):
        """檢查任務健康狀態"""
        current_time = datetime.now()
        
        for task_id, task_info in list(self.active_tasks.items()):
            # 檢查任務是否超時
            if (current_time - task_info['start_time']).seconds > 600:  # 10分鐘超時
                logger.warning(f"任務超時: {task_id}")
                await self._handle_task_timeout(task_id)
        
        # 檢查失敗任務重試
        for task_id, task_state in list(self.task_states.items()):
            if (task_state.status == 'failed' and 
                task_state.retry_count < self.max_retry_attempts and
                (current_time - task_state.start_time).seconds > self.retry_delay):
                
                logger.info(f"重試失敗任務: {task_id} (第 {task_state.retry_count + 1} 次)")
                await self._retry_task(task_state)
    
    async def _check_system_health(self):
        """檢查系統健康狀態"""
        # 檢查連接器健康狀態
        try:
            health = await self.connector.health_check()
            if not health.get('healthy', False):
                logger.warning("連接器不健康，啟動降級模式")
                await self._enter_degraded_mode()
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            await self._enter_degraded_mode()
        
        # 檢查錯誤率
        total_tasks = self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        if total_tasks > 10:  # 至少處理10個任務後才檢查
            error_rate = self.metrics['tasks_failed'] / total_tasks
            if error_rate > 0.3:  # 錯誤率超過30%
                logger.warning(f"錯誤率過高: {error_rate:.2%}")
                await self._enter_degraded_mode()
    
    async def _handle_task_timeout(self, task_id: str):
        """處理任務超時"""
        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            task_state = self.task_states.get(task_id)
            
            if task_state:
                task_state.status = 'failed'
                task_state.last_error = 'Task timeout'
                
                # 如果還有重試機會，標記為重試
                if task_state.retry_count < self.max_retry_attempts:
                    task_state.status = 'retrying'
                    logger.info(f"任務超時，將重試: {task_id}")
                else:
                    logger.error(f"任務最終超時失敗: {task_id}")
                    self.metrics['tasks_failed'] += 1
            
            # 清理活動任務
            del self.active_tasks[task_id]
    
    async def _retry_task(self, task_state: TaskState):
        """重試任務"""
        task_state.retry_count += 1
        task_state.status = 'retrying'
        task_state.start_time = datetime.now()
        
        # 重新提交任務
        await self.task_queue.put(task_state.task)
        self.metrics['tasks_retried'] += 1
        
        logger.info(f"重試任務: {task_state.task_id} (第 {task_state.retry_count} 次)")
    
    async def _enter_degraded_mode(self):
        """進入降級模式"""
        if not self.degraded_mode:
            self.degraded_mode = True
            self.metrics['degraded_mode_activations'] += 1
            
            # 禁用非關鍵能力
            for capability in self.capabilities:
                if capability['name'] not in self.critical_capabilities:
                    self.degraded_capabilities.add(capability['name'])
            
            logger.warning(f"進入降級模式，禁用能力: {self.degraded_capabilities}")
    
    async def _exit_degraded_mode(self):
        """退出降級模式"""
        if self.degraded_mode:
            self.degraded_mode = False
            self.degraded_capabilities.clear()
            logger.info("退出降級模式，恢復所有能力")
    
    async def _handle_startup_failure(self, error: Exception):
        """處理啟動失敗"""
        logger.error(f"代理啟動失敗: {error}")
        
        # 嘗試降級啟動
        try:
            logger.info("嘗試降級模式啟動")
            await self._enter_degraded_mode()
            
            # 只啟動基本功能
            self.is_active = True
            # asyncio.create_task(self._task_processing_loop())
            
            logger.info("降級模式啟動成功")
            
        except Exception as e:
            logger.error(f"降級模式啟動也失敗: {e}")
            raise
    
    def handle_task_error(self, task_id: str, error: Exception) -> bool:
        """處理任務錯誤
        
        Args:
            task_id: 任務ID
            error: 錯誤資訊
            
        Returns:
            bool: 是否應該重試
        """
        task_state = self.task_states.get(task_id)
        if not task_state:
            return False
        
        task_state.last_error = str(error)
        task_state.status = 'failed'
        
        # 判斷是否應該重試
        if task_state.retry_count < self.max_retry_attempts:
            # 檢查錯誤類型
            if self._is_retryable_error(error):
                task_state.status = 'retrying'
                logger.info(f"任務錯誤可重試: {task_id} - {error}")
                return True
        
        # 不重試，標記為最終失敗
        logger.error(f"任務最終失敗: {task_id} - {error}")
        self.metrics['tasks_failed'] += 1
        return False
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判斷錯誤是否可重試"""
        retryable_errors = [
            'ConnectionError',
            'TimeoutError',
            'HTTPError',
            'NetworkError',
            'ServiceUnavailable'
        ]
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # 檢查錯誤類型
        if error_type in retryable_errors:
            return True
        
        # 檢查錯誤消息
        retryable_keywords = ['timeout', 'connection', 'network', 'unavailable', '503', '502', '504']
        return any(keyword in error_message for keyword in retryable_keywords)
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """獲取恢復狀態"""
        return {
            'recovery_enabled': self.recovery_enabled,
            'degraded_mode': self.degraded_mode,
            'degraded_capabilities': list(self.degraded_capabilities),
            'active_tasks_count': len(self.active_tasks),
            'pending_tasks_count': self.task_queue.qsize(),
            'recovery_state': {
                'last_checkpoint': self.recovery_state.last_checkpoint.isoformat(),
                'recovery_events': self.metrics['recovery_events'],
                'degraded_mode_activations': self.metrics['degraded_mode_activations']
            },
            'task_states': {
                task_id: {
                    'status': state.status,
                    'retry_count': state.retry_count,
                    'last_error': state.last_error
                }
                for task_id, state in self.task_states.items()
            }
        }
