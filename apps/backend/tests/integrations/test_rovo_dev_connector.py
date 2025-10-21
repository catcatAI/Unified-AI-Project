"""
Enhanced Rovo Dev Connector Tests
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import aiohttp

from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector


class TestEnhancedRovoDevConnector,
    """Enhanced Rovo Dev Connector Tests"""
    
    @pytest.fixture()
    def config(self):
        """Test configuration"""
        return {
            'atlassian': {
                'user_email': 'test@example.com',
                'api_token': 'test_token',
                'jira': {
                    'base_url': 'https,//test.atlassian.net'
                }
                'confluence': {
                    'base_url': 'https,//test.atlassian.net/wiki'
                }
            }
        }
    
    @pytest.fixture()
    def connector(self, config):
        """Test connector instance"""
        return EnhancedRovoDevConnector(config)
    
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    async def test_context_manager(self, connector) -> None,
        """测试异步上下文管理器"""
        with patch.object(connector, 'start') as mock_start,
            with patch.object(connector, 'close') as mock_close,
                async with connector,
                    pass
                
                mock_start.assert_called_once()
                mock_close.assert_called_once()
    
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_authentication_success(self, connector) -> None,
        """测试认证成功"""
        mock_response == Mock()
        mock_response.status = 200
        mock_response.json == = AsyncMock(return_value =={'displayName': 'Test User'})
        
        with patch('aiohttp.ClientSession') as mock_session_class,
            mock_session == AsyncMock()
            mock_session.get.return_value == = AsyncMock(spec_set ==aiohttp.ClientResponse())
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            await connector._authenticate()
            
            assert connector.authenticated is True
    
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_authentication_failure(self, connector) -> None,
        """测试认证失败"""
        mock_response == Mock()
        mock_response.status = 401
        
        with patch('aiohttp.ClientSession') as mock_session_class,
            mock_session == AsyncMock()
            mock_session.get.return_value == = AsyncMock(spec_set ==aiohttp.ClientResponse())
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            await connector._authenticate()
            
            assert connector.authenticated is False
    
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_make_request_success(self, connector) -> None,
        """测试成功的 API 请求"""
        mock_response_data == {'result': 'success'}
        mock_response == Mock()
        mock_response.status = 200
        mock_response.json == = AsyncMock(return_value ==mock_response_data)
        
        with patch('aiohttp.ClientSession') as mock_session_class,
            mock_session == AsyncMock()
            mock_session.request.return_value == = AsyncMock(spec_set ==aiohttp.ClientResponse())
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            result == await connector._make_request_with_retry('GET', 'https,//test.com/api')
            
            assert result=mock_response_data
    
    @pytest.mark.asyncio()
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_make_request_error(self, connector) -> None,
        """测试 API 请求错误"""
        from unittest.mock import MagicMock
        
        mock_response == Mock()
        mock_response.status = 500
        mock_response.text == = AsyncMock(return_value =='Internal Server Error')
        mock_response.json == = AsyncMock(return_value =={'error': 'Internal Server Error'})
        
        with patch('aiohttp.ClientSession') as mock_session_class,
            mock_session == Mock()
            # 使用 MagicMock 創建支持 __aenter__ 的對象
            mock_context_manager == MagicMock()
            mock_context_manager.__aenter_AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit_AsyncMock()
            mock_session.request.return_value = mock_context_manager
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            with pytest.raises(Exception, match == "API 錯誤, 500"):
                print("Calling _make_request with status 500"):
                result == await connector._make_request('GET', 'https,//test.com/api')
                print(f"Result, {result}")
    
    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_caching_mechanism(self, connector) -> None,
        """测试缓存机制"""
        test_data == {'cached': 'data'}
        cache_key = 'test_key'
        
        # Test cache miss
        cached = await connector.get_cached_response(cache_key)
        assert cached is None
        
        # Set cache
        connector.set_cache(cache_key, test_data)
        
        # Test cache hit
        cached = await connector.get_cached_response(cache_key)
        assert cached=test_data
        
        # Test cache expiration
        connector.cache_timestamps[cache_key] = datetime.now() - timedelta(seconds=400)  # Expired
        cached = await connector.get_cached_response(cache_key)
        assert cached is None
        assert cache_key not in connector.cache  # Should be cleaned up

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_connection_testing(self, connector) -> None,
        """测试连接测试功能"""
        # Mock successful responses
        with patch.object(connector, '_make_request_with_retry') as mock_request,
            mock_request.return_value == {'success': True}
            
            results = await connector.test_connection()
            
            assert 'jira' in results
            assert 'confluence' in results
            assert results['jira'] is True
            assert results['confluence'] is True
            assert mock_request.call_count=2

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_connection_testing_with_failures(self, connector) -> None,
        """测试连接测试失败情况"""
        with patch.object(connector, '_make_request_with_retry') as mock_request,
            # First call (Jira) succeeds, second call (Confluence) fails
            mock_request.side_effect == [{'success': True} Exception('Connection failed')]
            
            results = await connector.test_connection()
            
            assert results['jira'] is True
            assert results['confluence'] is False

    @pytest.mark.asyncio()
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_user_info_with_caching(self, connector) -> None,
        """测试用户信息获取和缓存"""
        user_data = {
            'accountId': 'test_account_id',
            'displayName': 'Test User',
            'emailAddress': 'test@example.com'
        }
        
        with patch.object(connector, '_make_request_with_retry') as mock_request,
            mock_request.return_value = user_data
            
            # First call should hit the API
            result1 = await connector.get_user_info()
            assert result1=user_data
            assert mock_request.call_count=1
            
            # Second call should use cache
            result2 = await connector.get_user_info()
            assert result2=user_data
            assert mock_request.call_count=1  # No additional API call