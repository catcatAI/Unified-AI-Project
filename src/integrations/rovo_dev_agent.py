"""
Rovo Dev Agent 核心实现
提供智能开发助手功能，集成 Atlassian 生态系统
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
from pathlib import Path

from .rovo_dev_connector import RovoDevConnector
from .atlassian_bridge import AtlassianBridge
from ..hsp.types import HSPMessage, HSPCapability, HSPTask
from ..core_ai.agent_manager import AgentManager

logger = logging.getLogger(__name__)

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
        self.connector = RovoDevConnector(config)
        self.bridge = AtlassianBridge(self.connector)
        
        # 代理状态
        self.agent_id = config.get('hsp_integration', {}).get('agent_id', 'rovo-dev-agent')
        self.is_active = False
        self.capabilities = self._load_capabilities()
        
        # 任务队列和处理状态
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.task_history = []
        
        # 性能指标
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'average_response_time': 0.0,
            'last_activity': None
        }
        
    def _load_capabilities(self) -> List[HSPCapability]:
        """加载代理能力配置
        
        Returns:
            List[HSPCapability]: 能力列表
        """
        capabilities_config = self.config.get('atlassian', {}).get('rovo_dev', {}).get('capabilities', [])
        capabilities = []
        
        for cap_config in capabilities_config:
            if cap_config.get('enabled', False):
                capability = HSPCapability(
                    name=cap_config['name'],
                    description=cap_config['description'],
                    version="1.0.0",
                    parameters=self._get_capability_parameters(cap_config['name'])
                )
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
            
            # 启动任务处理循环
            asyncio.create_task(self._task_processing_loop())
            
            logger.info(f"Rovo Dev Agent {self.agent_id} 启动成功")
            
        except Exception as e:
            logger.error(f"启动 Rovo Dev Agent 失败: {e}")
            raise
            
    async def stop(self):
        """停止 Rovo Dev Agent"""
        self.is_active = False
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
        task_id = task.task_id
        
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
                'capability': task.capability,
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
                'capability': task.capability,
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
        capability = task.capability
        parameters = task.parameters
        
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
            'capabilities': [cap.name for cap in self.capabilities],
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