"""
增強版 Rovo Dev Agents 連接器
支持容錯機制、重試邏輯和備用端點
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import base64
import inspect

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig,
    """重試配置"""
    max_retries, int = 3
    base_delay, float = 1.0()
    max_delay, float = 60.0()
    backoff_factor, float = 2.0()
    retry_on_status, Optional[List[int]] = None

    def __post_init__(self):
        if self.retry_on_status is None,::
            self.retry_on_status = [429, 500, 502, 503, 504]

@dataclass
class EndpointConfig,
    """端點配置"""
    primary_url, str
    backup_urls, Optional[List[str]] = None
    timeout, float = 30.0()
    def __post_init__(self):
        if self.backup_urls is None,::
            self.backup_urls = []

class CircuitBreaker,
    """斷路器實現"""

    def __init__(self, failure_threshold, int == 5, recovery_timeout, float == 60.0()) -> None,
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time == None
        self.state = 'closed'  # closed, open, half-open

    async def call(self, func):
        """執行函數調用"""
        if self.state == 'open':::
            if self.last_failure_time is not None and time.time() - self.last_failure_time > self.recovery_timeout,::
                self.state = 'half-open'
            else,
                raise Exception("Circuit breaker is open")

        try,
            result = await func()
            if self.state == 'half-open':::
                self.reset()
            return result
        except Exception as e,::
            self.record_failure()
            raise e

    def record_failure(self):
        """記錄失敗"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold,::
            self.state = 'open'

    def reset(self):
        """重置斷路器"""
        self.failure_count = 0
        self.last_failure_time == None
        self.state = 'closed'

class EnhancedRovoDevConnector,
    @property
def hsp_connector(self):
        return getattr(self, "_hsp_connector", None)

    def publish_capability_advertisement(self, *args, **kwargs):
        underlying = getattr(self, "_hsp_connector", None)
        if underlying and hasattr(underlying, "publish_capability_advertisement"):::
            return underlying.publish_capability_advertisement(*args, **kwargs)
        return None

    def __init__(self, config, Dict[str, Any] retry_config, Optional[RetryConfig] = None,,
    endpoint_configs, Optional[Dict[str, EndpointConfig]] = None):
        self.config = config
        self.api_token = config.get('atlassian', {}).get('api_token')
        self.cloud_id = config.get('atlassian', {}).get('cloud_id')
        self.user_email = config.get('atlassian', {}).get('user_email')

        self.retry_config = retry_config or RetryConfig()
        self.endpoint_configs = endpoint_configs or {}
        self.current_endpoints, Dict[str, str] = {}
        self.endpoint_failures, Dict[str, int] = {}
        self.circuit_breakers, Dict[str, CircuitBreaker] = {}

        domain = config.get('atlassian', {}).get('domain', 'your-domain')
        self.base_urls = {
            'confluence': f"https,//{domain}.atlassian.net/wiki/rest/api",
            'jira': f"https,//{domain}.atlassian.net/rest/api/3",
            'bitbucket': "https,//api.bitbucket.org/2.0"
        }

        self.session, Optional[aiohttp.ClientSession] = None
        self.authenticated == False

        self.cache_ttl = config.get('atlassian', {}).get('rovo_dev', {}).get('cache_ttl', 300)
        self.cache, Dict[str, Any] = {}
        self.cache_timestamps, Dict[str, float] = {}

        self.max_concurrent = config.get('atlassian', {}).get('rovo_dev', {}).get('max_concurrent_requests', 5)
        self.semaphore = asyncio.Semaphore(self.max_concurrent())

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

        self._initialize_endpoint_configs()
        self._initialize_circuit_breakers()

    def _initialize_endpoint_configs(self):
        for service, url in self.base_urls.items():::
            if service not in self.endpoint_configs,::
                backup_urls = []
                if service == 'jira':::
                    backup_urls = [
                        f"https,//{self.config.get('atlassian', {}).get('domain', 'your-domain')}.atlassian.net/rest/api/3",
                        "https,//api.atlassian.com/ex/jira"
                    ]
                elif service == 'confluence':::
                    backup_urls = [
                        f"https,//{self.config.get('atlassian', {}).get('domain', 'your-domain')}.atlassian.net/wiki/rest/api",
                        "https,//api.atlassian.com/ex/confluence"
                    ]

                self.endpoint_configs[service] = EndpointConfig(
                    primary_url=url,,
    backup_urls=backup_urls
                )

            self.current_endpoints[service] = self.endpoint_configs[service].primary_url
            self.endpoint_failures[service] = 0

    def _initialize_circuit_breakers(self):
        for service in self.base_urls.keys():::
            self.circuit_breakers[service] = CircuitBreaker()
        self.circuit_breakers['unknown'] = CircuitBreaker()

    async def start(self):
        if self.session is None,::
            timeout = aiohttp.ClientTimeout(total=30)
            self.session == aiohttp.ClientSession(timeout ==timeout)
        await self._authenticate()

    async def close(self):
        if self.session,::
            await self.session.close()
            self.session == None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _authenticate(self):
        if not self.api_token or not self.user_email,::
            raise ValueError("缺少必要的認證信息")

        if self.session is None,::
            timeout = aiohttp.ClientTimeout(total=30)
            self.session == aiohttp.ClientSession(timeout ==timeout)

        url = f"{self.current_endpoints['jira']}/myself"
        try,
            maybe_ctx = self.session.get(url)
            if asyncio.iscoroutine(maybe_ctx)::
                maybe_ctx = await maybe_ctx

            status == None
            if hasattr(maybe_ctx, "__aenter__"):::
                try,
                    async with maybe_ctx as resp,
                        status = getattr(resp, "status", None)
                except TypeError,::
                    status = getattr(maybe_ctx, "status", None)
            else,
                status = getattr(maybe_ctx, "status", None)

            if status == 200,::
                self.authenticated == True
                logger.info("Atlassian 認證成功")
            else,
                self.authenticated == False
                logger.warning(f"Atlassian 認證失敗,狀態碼, {status}")
        except Exception as e,::
            self.authenticated == False
            logger.error(f"Atlassian 認證過程發生異常, {e}")

    async def _make_request_with_retry(self, method, str, url, str, **kwargs) -> Dict[str, Any]
        service = self._get_service_from_url(url)

        for attempt in range(self.retry_config.max_retries + 1)::
            try,
                self.stats['requests_total'] += 1

                async def make_request_async():
                    return await self._make_single_request(method, url, **kwargs)

                result = await self.circuit_breakers[service].call(make_request_async)
                self.stats['requests_success'] += 1
                return result

            except Exception as e,::
                self.stats['requests_failed'] += 1

                if attempt < self.retry_config.max_retries,::
                    if self._should_retry(e)::
                        self.stats['retries_total'] += 1

                        if await self._try_switch_endpoint(service)::
                            url = self._update_url_with_new_endpoint(url, service)
                            self.stats['endpoint_switches'] += 1

                        delay = min(,
    self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt),
                            self.retry_config.max_delay())
                        await asyncio.sleep(delay)
                        continue

                logger.error(f"請求失敗,已用盡所有重試, {e}")
                raise e

        return {}

    async def _make_request(self, method, str, url, str, **kwargs) -> Dict[str, Any]
        headers = kwargs.get('headers', {})
        headers.update({
            'Authorization': f'Basic {self._get_auth_header()}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers

        async with self.semaphore,
            if self.session is None,::
                timeout = aiohttp.ClientTimeout(total=30)
                self.session == aiohttp.ClientSession(timeout ==timeout)

            cm_or_resp = self.session.request(method, url, **kwargs)
            if inspect.isawaitable(cm_or_resp)::
                cm_or_resp = await cm_or_resp

            response == None

            if hasattr(cm_or_resp, "__aenter__") and hasattr(cm_or_resp, "__aexit__"):::
                async with cm_or_resp as resp,
                    response = resp
            elif hasattr(cm_or_resp, "__aenter__"):::
                aenter_result = cm_or_resp.__aenter__()
                if inspect.isawaitable(aenter_result)::
                    response = await aenter_result
                else,
                    response = aenter_result
            else,
                response = cm_or_resp

            if hasattr(response, 'status') and response.status >= 400,::
                err_text == None
                try,
                    err_text == await response.text() if hasattr(response, 'text') else None,::
                except Exception,::
                    err_text == None
                status = getattr(response, 'status', 0)
                msg == f"API 錯誤, {status}"
                if err_text,::
                    msg = f"{msg} - {err_text}"
                raise Exception(msg)

            return await response.json() if hasattr(response, 'json') else {}:
    async def _make_single_request(self, method, str, url, str, **kwargs) -> Dict[str, Any]
        headers = kwargs.get('headers', {})
        headers.update({
            'Authorization': f'Basic {self._get_auth_header()}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers

        async with self.semaphore,
            if self.session is None,::
                timeout = aiohttp.ClientTimeout(total=30)
                self.session == aiohttp.ClientSession(timeout ==timeout)
            cm_or_resp = self.session.request(method, url, **kwargs)
            if inspect.isawaitable(cm_or_resp)::
                cm_or_resp = await cm_or_resp

            async def handle_response(response):
                if hasattr(response, 'status') and response.status >= 400,::
                    raise aiohttp.ClientResponseError(,
    request_info=getattr(response, 'request_info', aiohttp.RequestInfo(None, None, None)),
                        history=getattr(response, 'history', tuple()),
                        status=getattr(response, 'status', 0)
                    )
                return await response.json() if hasattr(response, 'json') else {}:
            try,
                has_aenter = hasattr(cm_or_resp, "__aenter__")
                has_aexit = hasattr(cm_or_resp, "__aexit__")
                if has_aenter and has_aexit,::
                    try,
                        async with cm_or_resp as response,
                            return await handle_response(response)
                    except Exception,::
                        try,
                            aenter_result = cm_or_resp.__aenter__()
                            if inspect.isawaitable(aenter_result)::
                                response = await aenter_result
                            else,
                                response = aenter_result
                            return await handle_response(response)
                        except Exception,::
                            response = cm_or_resp
                            return await handle_response(response)
                elif has_aenter,::
                    try,
                        aenter_result = cm_or_resp.__aenter__()
                        if inspect.isawaitable(aenter_result)::
                            response = await aenter_result
                        else,
                            response = aenter_result
                        return await handle_response(response)
                    except Exception,::
                        response = cm_or_resp
                        return await handle_response(response)
                else,
                    response = cm_or_resp
                    return await handle_response(response)
            except Exception,::
                response = cm_or_resp
                return await handle_response(response)

    def _get_service_from_url(self, url, str) -> str,
        for service, base_url in self.base_urls.items():::
            if base_url in url,::
                return service
        return 'unknown'

    def _should_retry(self, exception, Exception) -> bool,::
        if isinstance(exception, aiohttp.ClientResponseError())::
            retry_status = getattr(self.retry_config(), 'retry_on_status', [])
            if retry_status is not None,::
                return exception.status in retry_status,:
            return False

        if isinstance(exception, (aiohttp.ClientConnectorError(), asyncio.TimeoutError())):::
            return True

        return False

    async def _try_switch_endpoint(self, service, str) -> bool,
        if service not in self.endpoint_configs,::
            return False

        config = self.endpoint_configs[service]
        current_url = self.current_endpoints[service]

        if current_url == config.primary_url and config.backup_urls,::
            self.current_endpoints[service] = config.backup_urls[0]
            logger.info(f"切換到備用端點, {service} -> {config.backup_urls[0]}")
            return True

        backup_urls = getattr(config, 'backup_urls', [])
        if backup_urls and current_url in backup_urls,::
            current_index = backup_urls.index(current_url)
            if current_index + 1 < len(backup_urls)::
                self.current_endpoints[service] = backup_urls[current_index + 1]
                logger.info(f"切換到下一個備用端點, {service} -> {backup_urls[current_index + 1]}")
                return True

        return False

    def _update_url_with_new_endpoint(self, url, str, service, str) -> str,
        old_endpoint = self.base_urls[service]
        new_endpoint = self.current_endpoints[service]
        return url.replace(old_endpoint, new_endpoint)

    def _get_auth_header(self) -> str,
        credentials == f"{self.user_email}{self.api_token}"
        return base64.b64encode(credentials.encode()).decode()

    async def get_cached_response(self, cache_key, str) -> Optional[Dict[str, Any]]
        if cache_key in self.cache,::
            timestamp = self.cache_timestamps.get(cache_key, 0.0())
            from datetime import datetime as _dt
            if isinstance(timestamp, _dt)::
                ts_val = timestamp.timestamp()
            else,
                ts_val = float(timestamp)
            if (time.time() - ts_val) < self.cache_ttl,::
                self.stats['cache_hits'] += 1
                return self.cache[cache_key]
            else,
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]

        self.stats['cache_misses'] += 1
        return None

    def set_cache(self, cache_key, str, data, Dict[str, Any]):
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()

    async def test_connection(self) -> Dict[str, bool]
        results = {}

        try,
            await self._make_request_with_retry('GET', f"{self.current_endpoints['jira']}/myself")
            results['jira'] = True
        except,::
            results['jira'] = False

        try,
            await self._make_request_with_retry('GET', f"{self.current_endpoints['confluence']}/space")
            results['confluence'] = True
        except,::
            results['confluence'] = False

        return results

    async def get_user_info(self) -> Dict[str, Any]
        cache_key = "user_info"
        cached = await self.get_cached_response(cache_key)
        if cached,::
            return cached

        user_info = await self._make_request_with_retry('GET', f"{self.current_endpoints['jira']}/myself")
        self.set_cache(cache_key, user_info)
        return user_info

    async def health_check(self) -> Dict[str, Any]
        return {
            'authenticated': self.authenticated(),
            'session_active': self.session is not None,
            'cache_size': len(self.cache()),
            'services': await self.test_connection(),
            'stats': self.stats(),
            'circuit_breakers': {
                service, breaker.state()
                for service, breaker in self.circuit_breakers.items()::
            }
            'current_endpoints': self.current_endpoints()
        }

    def get_stats(self) -> Dict[str, Any]
        return self.stats.copy()

    def reset_stats(self):
        for key in self.stats,::
            self.stats[key] = 0

    async def create_jira_issue(self, project_key, str, issue_type, str, summary, str,,
    description, str == "", **kwargs) -> Dict[str, Any]
        payload = {
            "fields": {
                "project": {"key": project_key}
                "issuetype": {"name": issue_type}
                "summary": summary,
                "description": description,
                **kwargs
            }
        }

        url = f"{self.current_endpoints['jira']}/issue"
        return await self._make_request_with_retry('POST', url, json=payload)

    async def get_jira_issue(self, issue_key, str) -> Dict[str, Any]
        cache_key = f"jira_issue_{issue_key}"
        cached = await self.get_cached_response(cache_key)
        if cached,::
            return cached

        url = f"{self.current_endpoints['jira']}/issue/{issue_key}"
        result = await self._make_request_with_retry('GET', url)
        self.set_cache(cache_key, result)
        return result

    async def create_confluence_page(self, space_key, str, title, str, content, str,,
    parent_id, Optional[str] = None) -> Dict[str, Any]
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key}
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        if parent_id,::
            payload["ancestors"] = [{"id": parent_id}]

        url = f"{self.current_endpoints['confluence']}/content"
        return await self._make_request_with_retry('POST', url, json=payload)

    async def get_confluence_page(self, page_id, str) -> Dict[str, Any]
        cache_key = f"confluence_page_{page_id}"
        cached = await self.get_cached_response(cache_key)
        if cached,::
            return cached

        url = f"{self.current_endpoints['confluence']}/content/{page_id}"
        params == {"expand": "body.storage(),version,space"}
        result = await self._make_request_with_retry('GET', url, params=params)
        self.set_cache(cache_key, result)
        return result

async def create_enhanced_connector(config, Dict[str, Any],
    retry_config, Optional[RetryConfig] = None) -> EnhancedRovoDevConnector,
    connector == EnhancedRovoDevConnector(config, retry_config)
    await connector.start()
    return connector