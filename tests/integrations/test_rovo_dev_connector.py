"""
Rovo Dev Connector 测试用例
"""

import pytest
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector


class TestRovoDevConnector:
    """Rovo Dev Connector 测试类"""
    
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
                    'cache_ttl': 300,
                    'max_concurrent_requests': 5
                }
            }
        }
    
    @pytest.fixture
    def connector(self, mock_config):
        """创建测试连接器实例"""
        return EnhancedRovoDevConnector(mock_config)
    
    def test_connector_initialization(self, connector, mock_config):
        """测试连接器初始化"""
        assert connector.api_token == 'test_token'
        assert connector.cloud_id == 'test_cloud_id'
        assert connector.user_email == 'test@example.com'
        assert 'test-domain.atlassian.net' in connector.base_urls['jira']
        assert connector.cache_ttl == 300
        assert connector.max_concurrent == 5
    
    def test_auth_headers(self, connector):
        """测试认证头生成"""
        auth_header_value = connector._get_auth_header()
        import base64
        decoded_credentials = base64.b64decode(auth_header_value).decode()
        assert decoded_credentials == f"{connector.user_email}:{connector.api_token}"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, connector):
        """测试异步上下文管理器"""
        with patch.object(connector, 'start') as mock_start:
            with patch.object(connector, 'close') as mock_close:
                async with connector:
                    pass
                
                mock_start.assert_called_once()
                mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, connector):
        """测试认证成功"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'displayName': 'Test User'})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value = AsyncMock(spec_set=aiohttp.ClientResponse)
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            result = await connector.authenticate()
            
            assert result is True
            assert connector.authenticated is True
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, connector):
        """测试认证失败"""
        mock_response = Mock()
        mock_response.status = 401
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value = AsyncMock(spec_set=aiohttp.ClientResponse)
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            result = await connector.authenticate()
            
            assert result is False
            assert connector.authenticated is False
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, connector):
        """测试成功的 API 请求"""
        mock_response_data = {'result': 'success'}
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.request.return_value = AsyncMock(spec_set=aiohttp.ClientResponse)
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            result = await connector._make_request_with_retry('GET', 'https://test.com/api')
            
            assert result == mock_response_data
    
    @pytest.mark.asyncio
    async def test_make_request_error(self, connector):
        """测试 API 请求错误"""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='Internal Server Error')
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            with pytest.raises(Exception, match="API 错误: 500"):
                await connector._make_request('GET', 'https://test.com/api')
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, connector):
        """测试缓存机制"""
        test_data = {'cached': 'data'}
        cache_key = 'test_key'
        
        # Test cache miss
        cached = await connector.get_cached_response(cache_key)
        assert cached is None
        
        # Set cache
        connector.set_cache(cache_key, test_data)
        
        # Test cache hit
        cached = await connector.get_cached_response(cache_key)
        assert cached == test_data
        
        # Test cache expiration
        connector.cache_timestamps[cache_key] = datetime.now() - timedelta(seconds=400)  # Expired
        cached = await connector.get_cached_response(cache_key)
        assert cached is None
        assert cache_key not in connector.cache  # Should be cleaned up
    
    @pytest.mark.asyncio
    async def test_connection_testing(self, connector):
        """测试连接测试功能"""
        # Mock successful responses
        with patch.object(connector, '_make_request_with_retry') as mock_request:
            mock_request.return_value = {'success': True}
            
            results = await connector.test_connection()
            
            assert 'jira' in results
            assert 'confluence' in results
            assert results['jira'] is True
            assert results['confluence'] is True
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_connection_testing_with_failures(self, connector):
        """测试连接测试失败情况"""
        with patch.object(connector, '_make_request_with_retry') as mock_request:
            # First call (Jira) succeeds, second call (Confluence) fails
            mock_request.side_effect = [{'success': True}, Exception('Connection failed')]
            
            results = await connector.test_connection()
            
            assert results['jira'] is True
            assert results['confluence'] is False
    
    @pytest.mark.asyncio
    async def test_user_info_with_caching(self, connector):
        """测试用户信息获取和缓存"""
        user_data = {
            'accountId': 'test_account_id',
            'displayName': 'Test User',
            'emailAddress': 'test@example.com'
        }
        
        with patch.object(connector, '_make_request_with_retry') as mock_request:
            mock_request.return_value = user_data
            
            # First call should hit the API
            result1 = await connector.get_user_info()
            assert result1 == user_data
            assert mock_request.call_count == 1
            
            # Second call should use cache
            result2 = await connector.get_user_info()
            assert result2 == user_data
            assert mock_request.call_count == 1  # No additional API call
    
    @pytest.mark.asyncio
    async def test_health_check(self, connector):
        """测试健康检查"""
        connector.authenticated = True
        connector.session = Mock()
        
        with patch.object(connector, 'test_connection') as mock_test:
            mock_test.return_value = {'jira': True, 'confluence': True}
            
            health = await connector.health_check()
            
            assert health['authenticated'] is True
            assert health['session_active'] is True
            assert health['cache_size'] == 0
            assert health['services']['jira'] is True
            assert health['services']['confluence'] is True
    
    @pytest.mark.asyncio
    async def test_session_management(self, connector):
        """测试会话管理"""
        # Test start
        await connector.start()
        assert connector.session is not None
        assert isinstance(connector.session, aiohttp.ClientSession)
        
        # Test close
        await connector.close()
        assert connector.session is None
    
    def test_semaphore_initialization(self, connector):
        """测试信号量初始化"""
        assert connector.semaphore._value == 5  # max_concurrent_requests
    
    @pytest.mark.asyncio
    async def test_concurrent_request_limiting(self, connector):
        """测试并发请求限制"""
        # This test would be more complex in a real scenario
        # but we can at least verify the semaphore is used
        assert hasattr(connector, 'semaphore')
        assert connector.semaphore._value == connector.max_concurrent
    
    def test_base_url_construction(self, connector):
        """测试基础 URL 构建"""
        expected_urls = {
            'confluence': 'https://test-domain.atlassian.net/wiki/rest/api',
            'jira': 'https://test-domain.atlassian.net/rest/api/3',
            'bitbucket': 'https://api.bitbucket.org/2.0'
        }
        
        assert connector.base_urls == expected_urls
    
    def test_missing_credentials(self):
        """测试缺少凭证的情况"""
        config = {
            'atlassian': {
                # Missing api_token and user_email
                'domain': 'test-domain'
            }
        }
        
        connector = EnhancedRovoDevConnector(config)
        assert connector.api_token is None
        assert connector.user_email is None