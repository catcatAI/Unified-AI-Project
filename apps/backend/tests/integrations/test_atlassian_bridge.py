"""
Atlassian Bridge 测试用例
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from apps.backend.src.integrations.atlassian_bridge import AtlassianBridge
from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector


class TestAtlassianBridge:
    """Atlassian Bridge 测试类"""
    
    @pytest.fixture
    def mock_connector(self):
        """模擬連接器"""
        connector = Mock(spec=EnhancedRovoDevConnector)
        connector._make_request_with_retry = AsyncMock()
        connector.config = {
            'atlassian': {
                'confluence': {
                    'base_url': 'https://primary.atlassian.net/wiki',
                    'backup_urls': [
                        'https://backup1.atlassian.net/wiki',
                        'https://backup2.atlassian.net/wiki'
                    ],
                },
                'jira': {
                    'base_url': 'https://primary.atlassian.net',
                    'backup_urls': [
                        'https://backup1.atlassian.net',
                        'https://backup2.atlassian.net'
                    ],
                },
                'rovo_dev': {
                    'fallback': {
                        'enabled': True,
                    }
                }
            }
        }
        return connector
    
    @pytest.fixture
    async def bridge(self, mock_connector):
        """創建測試橋接器實例"""
        bridge = AtlassianBridge(mock_connector)
        await bridge.start()
        yield bridge
        # 確保在測試完成後關閉 bridge
        await bridge.close()
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_create_confluence_page(self, bridge, mock_connector):
        """测试创建 Confluence 页面"""
        # Mock response
        mock_response = {
            'id': '123456',
            'key': 'TEST-123',
            'title': 'Test Page',
            '_links': {
                'webui': '/spaces/TEST/pages/123456'
            }
        }
        mock_connector._make_request_with_retry.return_value = mock_response
        
        result = await bridge.create_confluence_page(
            space_key='TEST',
            title='Test Page',
            content='# Test Content'
        )
        
        assert result['id'] == '123456'
        assert result['title'] == 'Test Page'
        mock_connector._make_request_with_retry.assert_called_once()
    
    

    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_search_jira_issues(self, bridge, mock_connector):
        """测试搜索 Jira 问题"""
        mock_response = {
            'issues': [
                {
                    'id': '10001',
                    'key': 'TEST-123',
                    'fields': {
                        'summary': 'Test Issue 1',
                        'status': {'name': 'Done'}
                    }
                },
                {
                    'id': '10002',
                    'key': 'TEST-124',
                    'fields': {
                        'summary': 'Test Issue 2',
                        'status': {'name': 'In Progress'}
                    }
                }
            ],
            'total': 2
        }
        mock_connector._make_request_with_retry.return_value = mock_response
        
        result = await bridge.search_jira_issues('project = TEST')
        
        assert len(result) == 2
        assert result[0]['key'] == 'TEST-123'
        assert result[1]['key'] == 'TEST-124'
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_update_confluence_page(self, bridge, mock_connector):
        """测试更新 Confluence 页面"""
        mock_response = {
            'id': '123456',
            'version': {'number': 2},
            'title': 'Updated Test Page'
        }
        mock_connector._make_request_with_retry.return_value = mock_response
        
        result = await bridge.update_confluence_page(
            page_id='123456',
            title='Updated Test Page',
            content='# Updated Content',
            version=1
        )
        
        assert result['id'] == '123456'
        assert result['version']['number'] == 2
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    # @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_get_confluence_spaces(self, bridge, mock_connector):
        """测试获取 Confluence 空间"""
        mock_response = {
            'results': [
                {
                    'id': 1,
                    'key': 'DEV',
                    'name': 'Development',
                    'type': 'global'
                },
                {
                    'id': 2,
                    'key': 'DOCS',
                    'name': 'Documentation',
                    'type': 'global'
                }
            ]
        }
        mock_connector._make_request_with_retry.return_value = mock_response
        
        result = await bridge.get_confluence_spaces()
        
        assert len(result) == 2
        assert result[0]['key'] == 'DEV'
        assert result[1]['key'] == 'DOCS'
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_get_jira_projects(self, bridge, mock_connector):
    """测试获取 Jira 项目"""
    mock_response = [
        {
            'id': '10000',
            'key': 'TEST',
            'name': 'Test Project'
        },
        {
            'id': '10001',
            'key': 'ANOTHER',
            'name': 'Another Project'
        }
    ]
    mock_connector._make_request_with_retry.return_value = mock_response

    result = await bridge.get_jira_projects()

    assert len(result) == 2
    assert result[0]['key'] == 'TEST'
    assert result[1]['key'] == 'ANOTHER'

    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_error_handling(self, bridge, mock_connector):
        """测试错误处理"""
        # Mock connector to raise an exception
        mock_connector._make_request_with_retry.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await bridge.create_confluence_page(
                space_key='TEST',
                title='Test Page',
                content='Content'
            )
    
    @pytest.mark.asyncio
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_content_formatting(self, bridge):
        """测试内容格式化"""
        
        # Test markdown to Confluence storage format conversion
        markdown_content = """# Title
        
## Subtitle

- Item 1
- Item 2

**Bold text** and *italic text*
        """
        
        formatted = bridge._format_content_for_confluence(markdown_content)
        
        # Should contain Confluence storage format elements
        assert '<h1>' in formatted or 'h1.' in formatted
        assert '<h2>' in formatted or 'h2.' in formatted
        assert '<ul>' in formatted or '*' in formatted
    
    def test_jira_field_mapping(self, bridge):
        """测试 Jira 字段映射"""
        
        issue_data = {
            'summary': 'Test Summary',
            'description': 'Test Description',
            'issue_type': 'Bug',
            'priority': 'High',
            'assignee': 'test@example.com'
        }
        
        mapped_fields = bridge._map_jira_fields('TEST', issue_data)
        
        assert mapped_fields['fields']['project']['key'] == 'TEST'
        assert mapped_fields['fields']['summary'] == 'Test Summary'
        assert mapped_fields['fields']['issuetype']['name'] == 'Bug'
        assert mapped_fields['fields']['priority']['name'] == 'High'
