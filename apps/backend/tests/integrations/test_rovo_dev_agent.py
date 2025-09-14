"""
Rovo Dev Agent 测试用例
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from apps.backend.src.integrations.rovo_dev_agent import RovoDevAgent
from apps.backend.src.hsp.types import HSPTask, HSPCapability


class TestRovoDevAgent:
    """Rovo Dev Agent 测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            'atlassian': {
                'api_token': 'test_token',
                'cloud_id': 'test_cloud_id',
                'user_email': 'test@example.com',
                'domain': 'test-domain',
                'rovo_dev': {
                    'enabled': True,
                    'max_concurrent_requests': 5,
                    'timeout': 30,
                    'cache_ttl': 300,
                    'capabilities': [
                        {
                            'name': 'code_analysis',
                            'description': '代码分析',
                            'enabled': True
                        },
                        {
                            'name': 'documentation_generation',
                            'description': '文档生成',
                            'enabled': True
                        }
                    ]
                }
            },
            'hsp_integration': {
                'agent_id': 'test-rovo-agent'
            }
        }
    
    @pytest.fixture
    def agent(self, mock_config):
        """创建测试代理实例"""
        with patch('src.integrations.enhanced_rovo_dev_connector.EnhancedRovoDevConnector'):
            with patch('src.integrations.rovo_dev_agent.AtlassianBridge'):
                return RovoDevAgent(mock_config)
    
    def test_agent_initialization(self, agent, mock_config):
        """测试代理初始化"""
        assert agent.agent_id == 'test-rovo-agent'
        assert not agent.is_active
        assert len(agent.capabilities) == 2
        assert agent.capabilities[0]['name'] == 'code_analysis'
        assert agent.capabilities[1]['name'] == 'documentation_generation'
    
    def test_capability_parameters(self, agent):
        """测试能力参数定义"""
        code_analysis_params = agent._get_capability_parameters('code_analysis')
        assert 'repository_url' in code_analysis_params
        assert code_analysis_params['repository_url']['required'] is True
        
        doc_gen_params = agent._get_capability_parameters('documentation_generation')
        assert 'source_path' in doc_gen_params
        assert doc_gen_params['source_path']['required'] is True
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_agent_start_stop(self, agent):
        """测试代理启动和停止"""
        # Mock connector methods
        agent.connector.start = AsyncMock()
        agent.connector.close = AsyncMock()
        
        await agent.start()
        assert agent.is_active
        agent.connector.start.assert_called_once()
        
        await agent.stop()
        assert not agent.is_active
        agent.connector.close.assert_called_once()
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_code_analysis_task(self, agent):
        """测试代码分析任务"""
        # Mock bridge method
        agent.bridge.create_confluence_page = AsyncMock(return_value={'id': 'test_page_id'})
        
        parameters = {
            'repository_url': 'https://github.com/test/repo',
            'analysis_type': 'quality',
            'confluence_space': 'DEV'
        }
        
        result = await agent._handle_code_analysis(parameters)
        
        assert result['repository_url'] == parameters['repository_url']
        assert result['analysis_type'] == 'quality'
        assert 'metrics' in result
        assert 'recommendations' in result
        assert 'confluence_page' in result
        
        agent.bridge.create_confluence_page.assert_called_once()
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_documentation_generation_task(self, agent):
        """测试文档生成任务"""
        agent.bridge.create_confluence_page = AsyncMock(return_value={'id': 'test_doc_page'})
        
        parameters = {
            'source_path': '/path/to/source',
            'doc_type': 'api',
            'confluence_space': 'DOCS'
        }
        
        result = await agent._handle_documentation_generation(parameters)
        
        assert result['source_path'] == parameters['source_path']
        assert result['doc_type'] == 'api'
        assert 'content' in result
        assert 'confluence_page' in result
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_issue_tracking_task(self, agent):
        """测试问题追踪任务"""
        agent.bridge.create_jira_issue = AsyncMock(return_value={
            'key': 'TEST-123',
            'id': '12345'
        })
        
        parameters = {
            'project_key': 'TEST',
            'summary': 'Test issue',
            'description': 'Test description',
            'issue_type': 'Bug',
            'priority': 'High'
        }
        
        result = await agent._handle_issue_tracking(parameters)
        
        assert result['project_key'] == 'TEST'
        assert result['issue_key'] == 'TEST-123'
        assert result['issue_id'] == '12345'
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_task_submission_and_processing(self, agent):
    """测试任务提交和处理"""
    # Mock the dispatch method
    agent._dispatch_task = AsyncMock(return_value={'status': 'completed'})
    
    task = HSPTask(
        task_id='test_task_001',
        capability='code_analysis',
        parameters={'repository_url': 'https://github.com/test/repo'},
        requester_id='test_requester'
    )
    
    # Start the agent
    agent.is_active = True
    
    # Submit task
    await agent.submit_task(task)
        
        # Process the task manually (since we're not running the loop)
        await agent._process_task(task)
        
        # Check metrics
        assert agent.metrics['tasks_completed'] == 1
        assert len(agent.task_history) == 1
        assert agent.task_history[0]['task_id'] == 'test_task_001'
        assert agent.task_history[0]['status'] == 'completed'
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_task_error_handling(self, agent):
        """测试任务错误处理"""
        # Mock dispatch to raise an error
        agent._dispatch_task = AsyncMock(side_effect=Exception("Test error"))
        
        task = HSPTask(
            task_id='error_task_001',
            capability='code_analysis',
            parameters={'repository_url': 'invalid_url'},
            requester_id='test_requester'
        )
        
        agent.is_active = True
        
        # Process the task
        await agent._process_task(task)
        
        # Check error handling
        assert agent.metrics['tasks_failed'] == 1
        assert len(agent.task_history) == 1
        assert agent.task_history[0]['status'] == 'failed'
        assert 'error' in agent.task_history[0]
    
    def test_metrics_update(self, agent):
        """测试指标更新"""
        # Test successful task
        agent._update_metrics(2.5, success=True)
        assert agent.metrics['tasks_completed'] == 1
        assert agent.metrics['tasks_failed'] == 0
        assert agent.metrics['average_response_time'] == 2.5
        
        # Test failed task
        agent._update_metrics(1.0, success=False)
        assert agent.metrics['tasks_completed'] == 1
        assert agent.metrics['tasks_failed'] == 1
        assert agent.metrics['average_response_time'] == 1.75  # (2.5 + 1.0) / 2
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_status_reporting(self, agent):
        """测试状态报告"""
        agent.is_active = True
        status = await agent.get_status()
        
        assert status['agent_id'] == 'test-rovo-agent'
        assert status['is_active'] is True
        assert 'code_analysis' in status['capabilities']
        assert 'documentation_generation' in status['capabilities']
        assert 'metrics' in status
    
    def test_task_history(self, agent):
        """测试任务历史记录"""
        # Add some mock history
        agent.task_history = [
            {
                'task_id': f'task_{i}',
                'capability': 'code_analysis',
                'status': 'completed',
                'processing_time': 1.0 + i,
                'timestamp': datetime.now().isoformat()
            }
            for i in range(10)
        ]
        
        # Test default limit
        history = agent.get_task_history()
        assert len(history) == 10
        
        # Test custom limit
        history = agent.get_task_history(limit=5)
        assert len(history) == 5
        assert history[0]['task_id'] == 'task_5'  # Should get the last 5
    
    def test_report_formatting(self, agent):
        """测试报告格式化"""
        analysis_result = {
            'repository_url': 'https://github.com/test/repo',
            'analysis_type': 'quality',
            'timestamp': '2025-01-01T12:00:00',
            'metrics': {
                'code_quality_score': 85,
                'test_coverage': 78,
                'complexity_score': 'Medium',
                'security_issues': 2,
                'performance_issues': 1
            },
            'recommendations': [
                '增加单元测试覆盖率',
                '重构复杂度较高的函数'
            ]
        }
        
        report = agent._format_analysis_report(analysis_result)
        
        assert '# 程式碼分析報告' in report
        assert 'https://github.com/test/repo' in report
        assert '85/100' in report
        assert '78%' in report
        assert '增加单元测试覆盖率' in report
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_unsupported_capability(self, agent):
        """测试不支持的能力"""
        task = HSPTask(
            task_id='unsupported_task',
            capability='unsupported_capability',
            parameters={},
            requester_id='test_requester'
        )
        
        with pytest.raises(ValueError, match="不支持的能力"):
            await agent._dispatch_task(task)


class TestRovoDevAgentIntegration:
    """Rovo Dev Agent 集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_full_workflow(self):
        """测试完整工作流程"""
        # This test would require actual Atlassian credentials
        # and should only run in integration test environment
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_real_confluence_integration(self):
        """测试真实 Confluence 集成"""
        # This test would create actual Confluence pages
        # and should only run in integration test environment
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_real_jira_integration(self):
        """测试真实 Jira 集成"""
        # This test would create actual Jira issues
        # and should only run in integration test environment
        pass