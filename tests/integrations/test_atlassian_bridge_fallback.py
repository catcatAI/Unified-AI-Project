"""
測試 AtlassianBridge 備用機制
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from src.integrations.atlassian_bridge import AtlassianBridge, EndpointConfig, CacheEntry
from src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector


class TestAtlassianBridgeFallback:
    """AtlassianBridge 備用機制測試"""

    @pytest.fixture
    def mock_config(self):
        """模擬配置"""
        return {
            'atlassian': {
                'confluence': {
                    'base_url': 'https://primary.atlassian.net/wiki',
                    'backup_urls': [
                        'https://backup1.atlassian.net/wiki',
                        'https://backup2.atlassian.net/wiki'
                    ],
                    'timeout': 30.0,
                    'max_retries': 3,
                    'retry_delay': 1.0
                },
                'jira': {
                    'base_url': 'https://primary.atlassian.net',
                    'backup_urls': [
                        'https://backup1.atlassian.net',
                        'https://backup2.atlassian.net'
                    ],
                    'timeout': 30.0,
                    'max_retries': 3,
                    'retry_delay': 1.0
                },
                'rovo_dev': {
                    'fallback': {
                        'enabled': True,
                        'max_fallback_attempts': 5,
                        'fallback_delay': 2.0,
                        'offline_mode': True,
                        'local_cache_enabled': True
                    }
                }
            }
        }

    @pytest.fixture
    def mock_connector(self, mock_config):
        """模擬連接器"""
        connector = Mock(spec=EnhancedRovoDevConnector)
        connector.config = mock_config
        connector._make_request_with_retry = AsyncMock()
        return connector

    @pytest.fixture
    async def bridge(self, mock_connector):
        """創建 AtlassianBridge 實例"""
        bridge = AtlassianBridge(mock_connector)
        # 手動設置配置以避免異步初始化問題
        bridge.config = mock_connector.config.get('atlassian', {})
        bridge.fallback_config = bridge.config.get('rovo_dev', {}).get('fallback', {})
        bridge.fallback_enabled = bridge.fallback_config.get('enabled', True)
        await bridge.start()
        return bridge

    @pytest.mark.asyncio
    async def test_endpoint_config_loading(self, bridge):
        """測試端點配置加載"""
        assert 'confluence' in bridge.endpoints
        assert 'jira' in bridge.endpoints
        
        confluence_config = bridge.endpoints['confluence']
        assert confluence_config.primary_url == 'https://primary.atlassian.net/wiki'
        assert len(confluence_config.backup_urls) == 2
        assert confluence_config.timeout == 30.0

    @pytest.mark.asyncio
    async def test_successful_primary_endpoint(self, bridge):
        """測試主端點成功請求"""
        expected_result = {'id': '123', 'title': 'Test Page'}
        bridge.connector._make_request_with_retry.return_value = expected_result

        result = await bridge._make_request_with_fallback(
            'confluence', 'GET', 'rest/api/content/123'
        )

        assert result == expected_result
        bridge.connector._make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_backup_endpoint(self, bridge):
        """測試備用端點切換"""
        expected_result = {'id': '123', 'title': 'Test Page'}
        
        # 主端點失敗，備用端點成功
        bridge.connector._make_request_with_retry.side_effect = [
            aiohttp.ClientError("Primary failed"),
            expected_result
        ]

        result = await bridge._make_request_with_fallback(
            'confluence', 'GET', 'rest/api/content/123'
        )

        assert result == expected_result
        assert bridge.connector._make_request_with_retry.call_count == 2

    @pytest.mark.asyncio
    async def test_all_endpoints_fail(self, bridge):
        """測試所有端點都失敗"""
        bridge.connector._make_request.side_effect = aiohttp.ClientError("All failed")

        with pytest.raises(aiohttp.ClientError):
            await bridge._make_request_with_fallback(
                'confluence', 'GET', 'rest/api/content/123'
            )

        # 應該嘗試所有端點
        assert bridge.connector._make_request.call_count == 3  # 主端點 + 2個備用端點

    @pytest.mark.asyncio
    async def test_cache_functionality(self, bridge):
        """測試緩存功能"""
        test_data = {'id': '123', 'title': 'Cached Page'}
        cache_key = 'test_key'

        # 保存到緩存
        await bridge._save_to_cache(cache_key, test_data, ttl=300)

        # 從緩存讀取
        cached_result = await bridge._get_from_cache(cache_key)
        assert cached_result == test_data

    @pytest.mark.asyncio
    async def test_expired_cache(self, bridge):
        """測試過期緩存"""
        test_data = {'id': '123', 'title': 'Expired Page'}
        cache_key = 'test_key'

        # 保存到緩存，設置很短的TTL
        await bridge._save_to_cache(cache_key, test_data, ttl=1)

        # 等待過期
        await asyncio.sleep(2)

        # 應該返回None
        cached_result = await bridge._get_from_cache(cache_key)
        assert cached_result is None

    @pytest.mark.asyncio
    async def test_offline_queue(self, bridge):
        """測試離線隊列"""
        # 添加到離線隊列
        await bridge._add_to_offline_queue(
            'confluence', 'POST', 'rest/api/content', {'title': 'Test'}
        )

        assert len(bridge.offline_queue) == 1
        queue_item = bridge.offline_queue[0]
        assert queue_item['service'] == 'confluence'
        assert queue_item['method'] == 'POST'

    @pytest.mark.asyncio
    async def test_offline_queue_processing(self, bridge):
        """測試離線隊列處理"""
        # 添加項目到隊列
        await bridge._add_to_offline_queue(
            'confluence', 'POST', 'rest/api/content', {'title': 'Test'}
        )

        # 模擬成功處理
        bridge.connector._make_request.return_value = {'id': '123'}

        # 處理隊列
        await bridge.process_offline_queue()

        # 隊列應該為空
        assert len(bridge.offline_queue) == 0

    @pytest.mark.asyncio
    async def test_health_monitoring(self, bridge):
        """測試健康監控"""
        # 模擬健康檢查
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            await bridge._check_endpoint_health('confluence', 'https://test.atlassian.net')

            # 檢查健康狀態
            health_key = 'confluence_https://test.atlassian.net'
            assert health_key in bridge.endpoint_health
            assert bridge.endpoint_health[health_key]['status'] == 'healthy'

    @pytest.mark.asyncio
    async def test_force_endpoint_switch(self, bridge):
        """測試強制端點切換"""
        # 初始狀態
        assert bridge.current_endpoints.get('confluence') is None

        # 強制切換
        bridge.force_endpoint_switch('confluence')

        # 應該切換到第一個備用端點
        expected_backup = bridge.endpoints['confluence'].backup_urls[0]
        assert bridge.current_endpoints['confluence'] == expected_backup

    def test_health_status(self, bridge):
        """測試健康狀態獲取"""
        status = bridge.get_health_status()

        assert 'endpoints' in status
        assert 'current_endpoints' in status
        assert 'offline_queue_size' in status
        assert 'cache_size' in status
        assert 'offline_mode' in status

    @pytest.mark.asyncio
    async def test_confluence_operations_with_fallback(self, bridge):
        """測試 Confluence 操作使用備用機制"""
        expected_result = {'id': '123', 'title': 'Test Page'}
        bridge.connector._make_request_with_retry.return_value = expected_result

        # 測試創建頁面
        result = await bridge.create_confluence_page(
            'TEST', 'Test Page', '# Test Content'
        )

        assert result == expected_result

    @pytest.mark.asyncio
    async def test_jira_operations_with_fallback(self, bridge):
        """測試 Jira 操作使用備用機制"""
        expected_result = {'id': '10001', 'key': 'TEST-1'}
        
        # 模擬備用機制：主端點失敗，備用端點成功
        bridge.connector._make_request_with_retry.side_effect = [
            aiohttp.ClientError("Primary failed"),
            expected_result
        ]

        result = await bridge.create_jira_issue(
            'TEST', 'Test Issue', 'Test Description'
        )

        assert result == expected_result
        assert bridge.connector._make_request_with_retry.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_with_get_requests(self, bridge):
        """測試GET請求的緩存機制"""
        test_data = {'id': '123', 'title': 'Cached Page'}
        
        # 第一次請求，應該調用API並緩存
        bridge.connector._make_request.return_value = test_data
        
        result1 = await bridge._make_request_with_fallback(
            'confluence', 'GET', 'rest/api/content/123'
        )
        
        # 第二次請求，應該從緩存返回
        result2 = await bridge._make_request_with_fallback(
            'confluence', 'GET', 'rest/api/content/123'
        )
        
        assert result1 == test_data
        assert result2 == test_data
        # API只應該被調用一次
        bridge.connector._make_request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_offline_mode_with_expired_cache(self, bridge):
        """測試離線模式下使用過期緩存"""
        test_data = {'id': '123', 'title': 'Offline Page'}
        cache_key = 'https://primary.atlassian.net/wiki/rest/api/content/123'
        
        # 保存過期緩存
        await bridge._save_to_cache(cache_key, test_data, ttl=1)
        await asyncio.sleep(2)  # 等待過期
        
        # 設置離線模式
        bridge.offline_mode = True
        
        # 模擬所有端點失敗
        bridge.connector._make_request.side_effect = aiohttp.ClientError("All failed")
        
        # 應該返回過期緩存
        result = await bridge._make_request_with_fallback(
            'confluence', 'GET', 'rest/api/content/123'
        )
        
        assert result == test_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])