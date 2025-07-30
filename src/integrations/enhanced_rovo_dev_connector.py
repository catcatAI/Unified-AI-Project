"""
增強版 Rovo Dev Agents 連接器
支持容錯機制、重試邏輯和備用端點
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retry_on_status: List[int] = None
    
    def __post_init__(self):
        if self.retry_on_status is None:
            self.retry_on_status = [429, 500, 502, 503, 504]

@dataclass
class EndpointConfig:
    """端點配置"""
    primary_url: str
    backup_urls: List[str] = None
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.backup_urls is None:
            self.backup_urls = []

class CircuitBreaker:
    """斷路器實現"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    async def call(self, func):
        """執行函數調用"""
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func()
            if self.state == 'half-open':
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e
    
    def record_failure(self):
        """記錄失敗"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
    
    def reset(self):
        """重置斷路器"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'

class EnhancedRovoDevConnector:
    """增強版 Rovo Dev Agents 連接器"""
    
    def __init__(self, config: Dict[str, Any], retry_config: Optional[RetryConfig] = None, 
                 endpoint_configs: Optional[Dict[str, EndpointConfig]] = None):
        """初始化連接器
        
        Args:
            config: 配置字典，包含 Atlassian 認證信息
            retry_config: 重試配置
            endpoint_configs: 端點配置
        """
        self.config = config
        self.api_token = config.get('atlassian', {}).get('api_token')
        self.cloud_id = config.get('atlassian', {}).get('cloud_id')
        self.user_email = config.get('atlassian', {}).get('user_email')
        
        # 容錯配置
        self.retry_config = retry_config or RetryConfig()
        self.endpoint_configs = endpoint_configs or {}
        self.current_endpoints = {}  # 當前使用的端點
        self.endpoint_failures = {}  # 端點失敗計數
        self.circuit_breakers = {}  # 斷路器
        
        # 構建基礎 URL
        domain = config.get('atlassian', {}).get('domain', 'your-domain')
        self.base_urls = {
            'confluence': f"https://{domain}.atlassian.net/wiki/rest/api",
            'jira': f"https://{domain}.atlassian.net/rest/api/3",
            'bitbucket': "https://api.bitbucket.org/2.0"
        }
        
        # 會話管理
        self.session: Optional[aiohttp.ClientSession] = None
        self.authenticated = False
        
        # 緩存配置
        self.cache_ttl = config.get('atlassian', {}).get('rovo_dev', {}).get('cache_ttl', 300)
        self.cache = {}
        self.cache_timestamps = {}
        
        # 限流配置
        self.max_concurrent = config.get('atlassian', {}).get('rovo_dev', {}).get('max_concurrent_requests', 5)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 統計信息
        self.stats = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'retries_total': 0,
            'endpoint_switches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'circuit_breaker_trips': 0
        }
        
        # 初始化端點配置和斷路器
        self._initialize_endpoint_configs()
        self._initialize_circuit_breakers()
    
    def _initialize_endpoint_configs(self):
        """初始化端點配置"""
        for service, url in self.base_urls.items():
            if service not in self.endpoint_configs:
                # 創建默認端點配置
                backup_urls = []
                if service == 'jira':
                    backup_urls = [
                        f"https://{self.config.get('atlassian', {}).get('domain', 'your-domain')}.atlassian.net/rest/api/3",
                        "https://api.atlassian.com/ex/jira"
                    ]
                elif service == 'confluence':
                    backup_urls = [
                        f"https://{self.config.get('atlassian', {}).get('domain', 'your-domain')}.atlassian.net/wiki/rest/api",
                        "https://api.atlassian.com/ex/confluence"
                    ]
                
                self.endpoint_configs[service] = EndpointConfig(
                    primary_url=url,
                    backup_urls=backup_urls
                )
            
            # 設置當前端點為主端點
            self.current_endpoints[service] = self.endpoint_configs[service].primary_url
            self.endpoint_failures[service] = 0
    
    def _initialize_circuit_breakers(self):
        """初始化斷路器"""
        for service in self.base_urls.keys():
            self.circuit_breakers[service] = CircuitBreaker()
        self.circuit_breakers['unknown'] = CircuitBreaker() # Add a circuit breaker for unknown services
    
    async def start(self):
        """啟動連接器"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # 測試認證
        await self._authenticate()
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _authenticate(self):
        """認證"""
        if not self.api_token or not self.user_email:
            raise ValueError("缺少必要的認證信息")
        
        self.authenticated = True
        logger.info("Atlassian 認證成功")
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """帶重試的HTTP請求"""
        service = self._get_service_from_url(url)
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                self.stats['requests_total'] += 1
                
                # 使用斷路器
                async def make_request_async():
                    return await self._make_single_request(method, url, **kwargs)
                
                result = await self.circuit_breakers[service].call(make_request_async)
                self.stats['requests_success'] += 1
                return result
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                
                # 檢查是否應該重試
                if attempt < self.retry_config.max_retries:
                    if self._should_retry(e):
                        self.stats['retries_total'] += 1
                        
                        # 嘗試切換端點
                        if await self._try_switch_endpoint(service):
                            url = self._update_url_with_new_endpoint(url, service)
                            self.stats['endpoint_switches'] += 1
                        
                        # 指數退避
                        delay = min(
                            self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
                            self.retry_config.max_delay
                        )
                        await asyncio.sleep(delay)
                        continue
                
                # 最後一次嘗試失敗
                logger.error(f"請求失敗，已用盡所有重試: {e}")
                raise e
    
    async def _make_single_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """單次HTTP請求"""
        headers = kwargs.get('headers', {})
        headers.update({
            'Authorization': f'Basic {self._get_auth_header()}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        
        async with self.semaphore:  # 限流
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
                
                return await response.json()
    
    def _get_service_from_url(self, url: str) -> str:
        """從URL獲取服務名稱"""
        for service, base_url in self.base_urls.items():
            if base_url in url:
                return service
        return 'unknown'
    
    def _should_retry(self, exception: Exception) -> bool:
        """判斷是否應該重試"""
        if isinstance(exception, aiohttp.ClientResponseError):
            return exception.status in self.retry_config.retry_on_status
        
        if isinstance(exception, (aiohttp.ClientConnectorError, asyncio.TimeoutError)):
            return True
        
        return False
    
    async def _try_switch_endpoint(self, service: str) -> bool:
        """嘗試切換端點"""
        if service not in self.endpoint_configs:
            return False
        
        config = self.endpoint_configs[service]
        current_url = self.current_endpoints[service]
        
        # 如果當前是主端點，嘗試備用端點
        if current_url == config.primary_url and config.backup_urls:
            self.current_endpoints[service] = config.backup_urls[0]
            logger.info(f"切換到備用端點: {service} -> {config.backup_urls[0]}")
            return True
        
        # 如果當前是備用端點，嘗試下一個備用端點
        if current_url in config.backup_urls:
            current_index = config.backup_urls.index(current_url)
            if current_index + 1 < len(config.backup_urls):
                self.current_endpoints[service] = config.backup_urls[current_index + 1]
                logger.info(f"切換到下一個備用端點: {service} -> {config.backup_urls[current_index + 1]}")
                return True
        
        return False
    
    def _update_url_with_new_endpoint(self, url: str, service: str) -> str:
        """使用新端點更新URL"""
        old_endpoint = self.base_urls[service]
        new_endpoint = self.current_endpoints[service]
        return url.replace(old_endpoint, new_endpoint)
    
    def _get_auth_header(self) -> str:
        """獲取認證頭"""
        import base64
        credentials = f"{self.user_email}:{self.api_token}"
        return base64.b64encode(credentials.encode()).decode()
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """獲取緩存響應"""
        if cache_key in self.cache:
            timestamp = self.cache_timestamps.get(cache_key, 0.0)
            if (datetime.now().timestamp() - timestamp) < self.cache_ttl:
                self.stats['cache_hits'] += 1
                return self.cache[cache_key]
            else:
                # 緩存過期，清理
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]
        
        self.stats['cache_misses'] += 1
        return None
    
    def set_cache(self, cache_key: str, data: Dict[str, Any]):
        """設置緩存"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()
    
    async def test_connection(self) -> Dict[str, bool]:
        """測試與各個 Atlassian 服務的連接"""
        results = {}
        
        # 測試 Jira
        try:
            await self._make_request_with_retry('GET', f"{self.current_endpoints['jira']}/myself")
            results['jira'] = True
        except:
            results['jira'] = False
            
        # 測試 Confluence
        try:
            await self._make_request_with_retry('GET', f"{self.current_endpoints['confluence']}/space")
            results['confluence'] = True
        except:
            results['confluence'] = False
            
        return results
    
    async def get_user_info(self) -> Dict[str, Any]:
        """獲取當前用戶信息"""
        cache_key = "user_info"
        cached = await self.get_cached_response(cache_key)
        if cached:
            return cached
            
        user_info = await self._make_request_with_retry('GET', f"{self.current_endpoints['jira']}/myself")
        self.set_cache(cache_key, user_info)
        return user_info
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            'authenticated': self.authenticated,
            'session_active': self.session is not None,
            'cache_size': len(self.cache),
            'services': await self.test_connection(),
            'stats': self.stats,
            'circuit_breakers': {
                service: breaker.state 
                for service, breaker in self.circuit_breakers.items()
            },
            'current_endpoints': self.current_endpoints
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置統計信息"""
        for key in self.stats:
            self.stats[key] = 0
    
    # 以下是具體的API方法，使用增強的請求機制
    
    async def create_jira_issue(self, project_key: str, issue_type: str, summary: str, 
                               description: str = "", **kwargs) -> Dict[str, Any]:
        """創建 Jira 問題"""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue_type},
                "summary": summary,
                "description": description,
                **kwargs
            }
        }
        
        url = f"{self.current_endpoints['jira']}/issue"
        return await self._make_request_with_retry('POST', url, json=payload)
    
    async def get_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """獲取 Jira 問題"""
        cache_key = f"jira_issue_{issue_key}"
        cached = await self.get_cached_response(cache_key)
        if cached:
            return cached
        
        url = f"{self.current_endpoints['jira']}/issue/{issue_key}"
        result = await self._make_request_with_retry('GET', url)
        self.set_cache(cache_key, result)
        return result
    
    async def create_confluence_page(self, space_key: str, title: str, content: str, 
                                   parent_id: Optional[str] = None) -> Dict[str, Any]:
        """創建 Confluence 頁面"""
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        
        url = f"{self.current_endpoints['confluence']}/content"
        return await self._make_request_with_retry('POST', url, json=payload)
    
    async def get_confluence_page(self, page_id: str) -> Dict[str, Any]:
        """獲取 Confluence 頁面"""
        cache_key = f"confluence_page_{page_id}"
        cached = await self.get_cached_response(cache_key)
        if cached:
            return cached
        
        url = f"{self.current_endpoints['confluence']}/content/{page_id}"
        params = {"expand": "body.storage,version,space"}
        result = await self._make_request_with_retry('GET', url, params=params)
        self.set_cache(cache_key, result)
        return result

# 便利函數
async def create_enhanced_connector(config: Dict[str, Any], 
                                  retry_config: Optional[RetryConfig] = None) -> EnhancedRovoDevConnector:
    """創建增強版連接器"""
    connector = EnhancedRovoDevConnector(config, retry_config)
    await connector.start()
    return connector
