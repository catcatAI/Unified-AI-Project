"""
Rovo Dev Agents 连接器
负责与 Atlassian Rovo Dev Agents 建立连接和通信
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

class RovoDevConnector:
    """Rovo Dev Agents 连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化连接器
        
        Args:
            config: 配置字典，包含 Atlassian 认证信息
        """
        self.config = config
        self.api_token = config.get('atlassian', {}).get('api_token')
        self.cloud_id = config.get('atlassian', {}).get('cloud_id')
        self.user_email = config.get('atlassian', {}).get('user_email')
        
        # 构建基础 URL
        domain = config.get('atlassian', {}).get('domain', 'your-domain')
        self.base_urls = {
            'confluence': f"https://{domain}.atlassian.net/wiki/rest/api",
            'jira': f"https://{domain}.atlassian.net/rest/api/3",
            'bitbucket': "https://api.bitbucket.org/2.0"
        }
        
        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None
        self.authenticated = False
        
        # 缓存配置
        self.cache_ttl = config.get('atlassian', {}).get('rovo_dev', {}).get('cache_ttl', 300)
        self.cache = {}
        
        # 限流配置
        self.max_concurrent = config.get('atlassian', {}).get('rovo_dev', {}).get('max_concurrent_requests', 5)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        
    async def start(self):
        """启动连接器"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
        await self.authenticate()
        
    async def close(self):
        """关闭连接器"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def authenticate(self) -> bool:
        """验证 Atlassian API 凭证
        
        Returns:
            bool: 认证是否成功
        """
        if not self.api_token or not self.user_email:
            logger.error("缺少必要的认证信息")
            return False
            
        headers = self._get_auth_headers()
        
        try:
            # 测试 Jira 认证
            async with self.session.get(
                f"{self.base_urls['jira']}/myself",
                headers=headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    logger.info(f"Jira 认证成功: {user_info.get('displayName')}")
                    self.authenticated = True
                    return True
                else:
                    logger.error(f"Jira 认证失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"认证过程中发生错误: {e}")
            return False
            
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        import base64
        
        # 使用基本认证
        auth_string = f"{self.user_email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发起 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            data: 请求数据
            params: 查询参数
            
        Returns:
            Dict: 响应数据
        """
        async with self.semaphore:
            headers = self._get_auth_headers()
            
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                ) as response:
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"API 请求失败: {response.status} - {error_text}")
                        raise Exception(f"API 错误: {response.status}")
                        
                    return await response.json()
                    
            except Exception as e:
                logger.error(f"请求失败: {e}")
                raise
                
    async def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """获取缓存响应
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[Dict]: 缓存的响应数据
        """
        if cache_key in self.cache:
            timestamp, data = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return data
            else:
                # 清理过期缓存
                del self.cache[cache_key]
        return None
        
    def set_cache(self, cache_key: str, data: Dict):
        """设置缓存
        
        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        self.cache[cache_key] = (datetime.now(), data)
        
    async def test_connection(self) -> Dict[str, bool]:
        """测试与各个 Atlassian 服务的连接
        
        Returns:
            Dict[str, bool]: 各服务的连接状态
        """
        results = {}
        
        # 测试 Jira
        try:
            await self._make_request('GET', f"{self.base_urls['jira']}/myself")
            results['jira'] = True
        except:
            results['jira'] = False
            
        # 测试 Confluence
        try:
            await self._make_request('GET', f"{self.base_urls['confluence']}/space")
            results['confluence'] = True
        except:
            results['confluence'] = False
            
        return results
        
    async def get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息
        
        Returns:
            Dict: 用户信息
        """
        cache_key = "user_info"
        cached = await self.get_cached_response(cache_key)
        if cached:
            return cached
            
        user_info = await self._make_request('GET', f"{self.base_urls['jira']}/myself")
        self.set_cache(cache_key, user_info)
        return user_info
        
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        return {
            'authenticated': self.authenticated,
            'session_active': self.session is not None,
            'cache_size': len(self.cache),
            'services': await self.test_connection()
        }