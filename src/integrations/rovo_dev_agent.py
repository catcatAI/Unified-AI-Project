"""
Rovo Dev Agent 核心实现
提供智能开发助手功能，集成 Atlassian 生态系统
"""

import asyncio
import logging
import pickle
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from .enhanced_rovo_dev_connector import EnhancedRovoDevConnector
from .atlassian_bridge import AtlassianBridge
from ..hsp.types import HSPMessage, HSPCapability, HSPTask
from ..core_ai.agent_manager import AgentManager

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
        
        # 代理状态
        self.agent_id = config.get('hsp_integration', {}).get('agent_id', 'rovo-dev-agent')
        self.is_active = False
        self.capabilities = self._load_capabilities()
        
        # 任务队列和处理状态
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.task_history = []
        self.task_states = {}  # 任務狀態追蹤
        
        # 錯誤恢復配置
        self.recovery_config = config.get('hsp_integration', {}).get('task_persistence', {})
        self.recovery_enabled = self.recovery_config.get('enabled', True)
        self.max_retry_attempts = self.recovery_config.get('max_retry_attempts', 5)
        self.retry_delay = self.recovery_config.get('retry_delay', 60)
        self.auto_recovery = self.recovery_config.get('auto_recovery', True)
        
        # 持久化存儲
        self.storage_path = Path(self.recovery_config.get('storage_path', 'data/task_queue'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_path / f"{self.agent_id}_state.pkl"
        self.tasks_file = self.storage_path / f"{self.agent_id}_tasks.pkl"
        
        # 降級模式配置
        self.degraded_mode = False
        self.degraded_capabilities = set()
        self.critical_capabilities = {'issue_tracking', 'documentation_generation'}
        
        # 性能指标
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
            capability_name: 能力名称
            
        Returns:
            Dict: 参数定义
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
            self.is_active = True
            
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
                logger.error(f"任务处理循环错误: {e}")
                
    async def _process_task(self, task: HSPTask):
        """处理单个任务
        
        Args:
            task: HSP 任务对象
        """
        start_time = datetime.now()
        task_id = task['task_id']
        
        try:
            self.active_tasks[task_id] = {
                'task': task,
                'start_time': start_time,
                'status': 'processing'
            }
            
            # 根据任务类型调用相应的处理方法
            result = await self._dispatch_task(task)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新指标
            self._update_metrics(processing_time, success=True)
            
            # 记录任务历史
            self.task_history.append({
                'task_id': task_id,
                'capability': task['capability'],
                'status': 'completed',
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'result_summary': str(result)[:100] + '...' if len(str(result)) > 100 else str(result)
            })
            
            # 发送结果（如果有 agent_manager）
            if self.agent_manager:
                await self.agent_manager.send_task_result(task_id, result)
                
            logger.info(f"任务 {task_id} 处理完成，耗时 {processing_time:.2f}s")
            
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
            
        finally:
            # 清理活动任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
    async def _dispatch_task(self, task: HSPTask) -> Dict[str, Any]:
        """分发任务到相应的处理方法
        
        Args:
            task: HSP 任务对象
            
        Returns:
            Dict: 任务处理结果
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
        """处理代码分析任务
        
        Args:
            parameters: 任务参数
            
        Returns:
            Dict: 分析结果
        """
        repository_url = parameters['repository_url']
        analysis_type = parameters.get('analysis_type', 'quality')
        output_format = parameters.get('output_format', 'markdown')
        
        # 模拟代码分析过程
        await asyncio.sleep(2)  # 模拟分析时间
        
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
                '增加单元测试覆盖率',
                '重构复杂度较高的函数',
                '修复发现的安全漏洞'
            ],
            'output_format': output_format
        }
        
        # 如果需要，创建 Confluence 页面
        confluence_space = parameters.get('confluence_space')
        if confluence_space:
            page_content = self._format_analysis_report(analysis_result)
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"代码分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
                content=page_content
            )
            analysis_result['confluence_page'] = page_result
            
        return analysis_result
        
    async def _handle_documentation_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理文档生成任务
        
        Args:
            parameters: 任务参数
            
        Returns:
            Dict: 生成结果
        """
        source_path = parameters['source_path']
        doc_type = parameters.get('doc_type', 'technical')
        confluence_space = parameters.get('confluence_space')
        template = parameters.get('template')
        
        # 模拟文档生成过程
        await asyncio.sleep(3)
        
        # 生成文档内容
        doc_content = self._generate_documentation_content(source_path, doc_type, template)
        
        result = {
            'source_path': source_path,
            'doc_type': doc_type,
            'timestamp': datetime.now().isoformat(),
            'content_length': len(doc_content),
            'content': doc_content
        }
        
        # 如果指定了 Confluence 空间，创建页面
        if confluence_space:
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"{doc_type.title()} 文档 - {Path(source_path).name}",
                content=doc_content
            )
            result['confluence_page'] = page_result
            
        return result
        
    async def _handle_issue_tracking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理问题追踪任务
        
        Args:
            parameters: 任务参数
            
        Returns:
            Dict: 创建结果
        """
        project_key = parameters['project_key']
        issue_type = parameters.get('issue_type', 'Task')
        priority = parameters.get('priority', 'Medium')
        assignee = parameters.get('assignee')
        
        # 创建 Jira 问题
        issue_data = {
            'summary': parameters.get('summary', '自动创建的问题'),
            'description': parameters.get('description', '由 Rovo Dev Agent 自动创建'),
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
        """处理项目管理任务
        
        Args:
            parameters: 任务参数
            
        Returns:
            Dict: 管理结果
        """
        project_key = parameters['project_key']
        report_type = parameters.get('report_type', 'status')
        time_period = parameters.get('time_period', 'week')
        
        # 获取项目数据
        issues = await self.bridge.search_jira_issues(
            jql=f"project = {project_key} AND updated >= -{time_period}"
        )
        
        # 生成报告
        report = self._generate_project_report(issues, report_type, time_period)
        
        # 如果需要，创建 Confluence 页面
        confluence_space = parameters.get('confluence_space')
        if confluence_space:
            report_content = self._format_project_report(report)
            page_result = await self.bridge.create_confluence_page(
                space_key=confluence_space,
                title=f"项目报告 - {project_key} - {datetime.now().strftime('%Y-%m-%d')}",
                content=report_content
            )
            report['confluence_page'] = page_result
            
        return report
        
    async def _handle_code_review(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理代码审查任务
        
        Args:
            parameters: 任务参数
            
        Returns:
            Dict: 审查结果
        """
        pull_request_url = parameters['pull_request_url']
        review_type = parameters.get('review_type', 'automated')
        focus_areas = parameters.get('focus_areas', ['security', 'performance', 'style'])
        
        # 模拟代码审查过程
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
                    'description': '发现潜在的 SQL 注入风险',
                    'file': 'src/database.py',
                    'line': 45
                },
                {
                    'type': 'performance',
                    'severity': 'low',
                    'description': '可以优化循环性能',
                    'file': 'src/utils.py',
                    'line': 123
                }
            ],
            'overall_score': 8.5,
            'recommendation': 'approve_with_suggestions'
        }
        
        return review_result
        
    def _update_metrics(self, processing_time: float, success: bool):
        """更新性能指标
        
        Args:
            processing_time: 处理时间
            success: 是否成功
        """
        if success:
            self.metrics['tasks_completed'] += 1
        else:
            self.metrics['tasks_failed'] += 1
            
        # 更新平均响应时间
        total_tasks = self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        if total_tasks > 0:
            current_avg = self.metrics['average_response_time']
            self.metrics['average_response_time'] = (
                (current_avg * (total_tasks - 1) + processing_time) / total_tasks
            )
            
        self.metrics['last_activity'] = datetime.now().isoformat()
        
    def _format_analysis_report(self, analysis_result: Dict[str, Any]) -> str:
        """格式化分析报告为 Markdown
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            str: Markdown 格式的报告
        """
        metrics = analysis_result['metrics']
        recommendations = analysis_result['recommendations']
        
        report = f"""# 代码分析报告

## 基本信息
- **仓库**: {analysis_result['repository_url']}
- **分析类型**: {analysis_result['analysis_type']}
- **分析时间**: {analysis_result['timestamp']}

## 质量指标
- **代码质量评分**: {metrics['code_quality_score']}/100
- **测试覆盖率**: {metrics['test_coverage']}%
- **复杂度**: {metrics['complexity_score']}
- **安全问题**: {metrics['security_issues']} 个
- **性能问题**: {metrics['performance_issues']} 个

## 改进建议
"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
            
        return report
        
    def _generate_documentation_content(self, source_path: str, doc_type: str, template: Optional[str]) -> str:
        """生成文档内容
        
        Args:
            source_path: 源代码路径
            doc_type: 文档类型
            template: 模板名称
            
        Returns:
            str: 生成的文档内容
        """
        # 这里应该实现实际的文档生成逻辑
        # 目前返回模拟内容
        
        return f"""# {doc_type.title()} 文档

## 概述
本文档基于 `{source_path}` 自动生成。

## 功能说明
[自动生成的功能说明]

## API 参考
[自动生成的 API 文档]

## 使用示例
[自动生成的使用示例]

---
*本文档由 Rovo Dev Agent 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    def _generate_project_report(self, issues: List[Dict], report_type: str, time_period: str) -> Dict[str, Any]:
        """生成项目报告
        
        Args:
            issues: 问题列表
            report_type: 报告类型
            time_period: 时间周期
            
        Returns:
            Dict: 项目报告
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
        """格式化项目报告为 Markdown
        
        Args:
            report: 项目报告数据
            
        Returns:
            str: Markdown 格式的报告
        """
        summary = report['summary']
        
        return f"""# 项目报告

## 报告信息
- **报告类型**: {report['report_type']}
- **时间周期**: {report['time_period']}
- **生成时间**: {report['timestamp']}

## 项目概况
- **总问题数**: {summary['total_issues']}
- **已完成**: {summary['completed_issues']}
- **进行中**: {summary['in_progress_issues']}
- **完成率**: {summary['completion_rate']:.1f}%

## 详细信息
[详细的问题列表和分析]

---
*本报告由 Rovo Dev Agent 自动生成*
"""

    async def submit_task(self, task: HSPTask):
        """提交任务到处理队列
        
        Args:
            task: HSP 任务对象
        """
        await self.task_queue.put(task)
        logger.info(f"任务 {task.task_id} 已提交到队列")
        
    def get_status(self) -> Dict[str, Any]:
        """获取代理状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            'agent_id': self.agent_id,
            'is_active': self.is_active,
            'capabilities': [cap['name'] for cap in self.capabilities],
            'queue_size': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'metrics': self.metrics,
            'connector_health': asyncio.create_task(self.connector.health_check()) if self.is_active else None
        }
        
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务历史
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            List: 任务历史记录
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
                    self.degraded_capabilities.add(capability.name)
            
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
            asyncio.create_task(self._task_processing_loop())
            
            logger.info("降級模式啟動成功")
            
        except Exception as e:
            logger.error(f"降級模式啟動也失敗: {e}")
            raise
    
    def handle_task_error(self, task_id: str, error: Exception) -> bool:
        """處理任務錯誤
        
        Args:
            task_id: 任務ID
            error: 錯誤信息
            
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