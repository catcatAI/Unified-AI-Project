"""
from __future__ import annotations
Atlassian 服务桥接层
提供统一的 Atlassian 服务接口, 包括 Confluence、Jira、Bitbucket
"""

import asyncio
import logging
import pickle
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import aiohttp

from datetime import datetime

# Assuming this is the correct import
from .enhanced_rovo_dev_connector import RovoDevConnector

logger = logging.getLogger(__name__)


@dataclass
class EndpointConfig:
    primary_url: str
    backup_urls: List[str]
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60


@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime
    ttl: int = 300


class AtlassianBridge:
    """Atlassian 服务统一桥接层 - SKELETON"""

    def __init__(self, connector: RovoDevConnector) -> None:
        self.connector = connector
        self.config = connector.config.get("atlassian", {})
        self.fallback_config = self.config.get("rovo_dev", {}).get("fallback", {})
        self.cache_dir = Path("data/atlassian_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.health_monitoring_task: Optional[asyncio.Task] = None
        self.endpoints: Dict[str, EndpointConfig] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self.offline_queue: List[Dict[str, Any]] = []
        self._running: bool = False
        self._loaded: bool = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._load_endpoint_configs()
        logger.info("AtlassianBridge Skeleton Initialized")

    async def start(self) -> None:
        """Start the component."""
        if self._running:
            logger.warning("[AtlassianBridge] start called but already running")
            return
        self._running = True
        self._loaded = True
        self._session = aiohttp.ClientSession()
        self._load_endpoint_configs()
        logger.info("[AtlassianBridge] Started — %d endpoints loaded", len(self.endpoints))

    async def close(self) -> None:
        """Close and release resources."""
        if not self._running:
            logger.warning("[AtlassianBridge] close called but not running")
            return
        self._running = False
        self._loaded = False
        if self.health_monitoring_task:
            self.health_monitoring_task.cancel()
            self.health_monitoring_task = None
        if self._session:
            await self._session.close()
            self._session = None
        self.cache.clear()
        self.offline_queue.clear()
        logger.info("[AtlassianBridge] Closed")

    async def __aenter__(self) -> 'AtlassianBridge':
        """Execute the   aenter   operation."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Execute the   aexit   operation."""
        await self.close()

    def _load_endpoint_configs(self) -> Dict[str, EndpointConfig]:
        """Load endpoint configs."""
        cfgs: Dict[str, EndpointConfig] = {}
        for service_name, svc_cfg in self.config.items():
            if not isinstance(svc_cfg, dict):
                continue
            primary = svc_cfg.get("url", "") or svc_cfg.get("primary_url", "") or svc_cfg.get("base_url", "")
            if not primary:
                continue
            backups = svc_cfg.get("backup_urls", [])
            timeout = svc_cfg.get("timeout", 30.0)
            max_retries = svc_cfg.get("max_retries", 3)
            retry_delay = svc_cfg.get("retry_delay", 1.0)
            health_interval = svc_cfg.get("health_check_interval", 60)
            cfgs[service_name] = EndpointConfig(
                primary_url=str(primary),
                backup_urls=list(backups) if isinstance(backups, list) else [],
                timeout=float(timeout),
                max_retries=int(max_retries),
                retry_delay=float(retry_delay),
                health_check_interval=int(health_interval),
            )
        return cfgs

    async def _make_request_with_fallback(
        self, service: str, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make request with fallback."""
        if service not in self.endpoints:
            logger.warning("No endpoint config for service '%s'", service)
            return {"error": f"No endpoint config for service '{service}'"}
        ep = self.endpoints[service]
        urls = [ep.primary_url] + ep.backup_urls
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Content-Type", "application/json")
        # Add auth token if available
        token = self.config.get("api_token") or self.config.get("token")
        if token:
            headers.setdefault("Authorization", f"Bearer {token}")
        last_error = None
        for url in urls:
            full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
            try:
                async with self._session.request(
                    method, full_url, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=ep.timeout), **kwargs
                ) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        logger.warning("HTTP %d from %s: %s", resp.status, full_url, text[:200])
                        last_error = f"HTTP {resp.status}: {text[:200]}"
                        continue
                    try:
                        data = await resp.json()
                    except Exception:
                        logger.warning("Failed to parse JSON response from %s, using raw text", full_url, exc_info=True)
                        data = {"raw": await resp.text()}
                    return {"success": True, "data": data, "url": full_url}
            except asyncio.TimeoutError:
                logger.warning("Timeout requesting %s", full_url)
                last_error = f"Timeout requesting {full_url}"
            except Exception as e:
                logger.warning("Request to %s failed: %s", full_url, e)
                last_error = str(e)
        return {"success": False, "error": last_error}

    async def create_confluence_page(
        self, space_key: str, title: str, content: str, parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a confluence page."""
        logger.info("create_confluence_page: space_key=%s title=%s parent_id=%s", space_key, title, parent_id)
        body = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": content, "representation": "storage"}},
        }
        if parent_id:
            body["ancestors"] = [{"id": parent_id}]
        result = await self._make_request_with_fallback(
            "confluence", "POST", "rest/api/content", json=body
        )
        return result

    async def update_confluence_page(
        self, page_id: str, title: str, content: str, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update the confluence page."""
        body = {
            "title": title,
            "body": {"storage": {"value": content, "representation": "storage"}},
            "version": {"number": version or 1},
        }
        return await self._make_request_with_fallback(
            "confluence", "PUT", f"rest/api/content/{page_id}", json=body
        )

    async def get_confluence_page(self, page_id: str) -> Dict[str, Any]:
        """Get the confluence page by self."""
        return await self._make_request_with_fallback("confluence", "GET", f"rest/api/content/{page_id}")

    async def search_confluence_pages(
        self, space_key: str, query: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for confluence pages."""
        result = await self._make_request_with_fallback(
            "confluence", "GET",
            f"rest/api/content?spaceKey={space_key}&cql={query}&limit={limit}"
        )
        if result.get("success"):
            return result["data"].get("results", [])
        return []

    async def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a jira issue."""
        body = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
            }
        }
        if assignee:
            body["fields"]["assignee"] = {"accountId": assignee}
        return await self._make_request_with_fallback("jira", "POST", "rest/api/3/issue", json=body)

    async def update_jira_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update the jira issue."""
        body = {"fields": fields}
        return await self._make_request_with_fallback("jira", "PUT", f"rest/api/3/issue/{issue_key}", json=body)

    async def get_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get the jira issue by self."""
        return await self._make_request_with_fallback("jira", "GET", f"rest/api/3/issue/{issue_key}")

    async def search_jira_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for jira issues."""
        result = await self._make_request_with_fallback("jira", "GET", f"rest/api/3/search?jql={jql}&maxResults={max_results}")
        if result.get("success"):
            return result["data"].get("issues", [])
        return []

    async def transition_jira_issue(
        self, issue_key: str, transition_id: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the transition jira issue operation."""
        body = {"transition": {"id": transition_id}}
        if comment:
            body["update"] = {"comment": [{"add": {"body": comment}}]}
        return await self._make_request_with_fallback("jira", "POST", f"rest/api/3/issue/{issue_key}/transitions", json=body)

    async def get_bitbucket_repositories(self, workspace: str) -> List[Dict[str, Any]]:
        """Get the bitbucket repositories by self."""
        result = await self._make_request_with_fallback("bitbucket", "GET", f"2.0/repositories/{workspace}")
        if result.get("success"):
            return result["data"].get("values", [])
        return []

    async def get_bitbucket_pull_requests(
        self, workspace: str, repo_slug: str, state: str = "OPEN"
    ) -> List[Dict[str, Any]]:
        """Get the bitbucket pull requests by self."""
        result = await self._make_request_with_fallback(
            "bitbucket", "GET",
            f"2.0/repositories/{workspace}/{repo_slug}/pullrequests?state={state}"
        )
        if result.get("success"):
            return result["data"].get("values", [])
        return []

    async def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """Get the confluence spaces by self."""
        result = await self._make_request_with_fallback("confluence", "GET", "rest/api/space")
        if result.get("success"):
            return result["data"].get("results", [])
        return []

    async def get_jira_projects(self) -> List[Dict[str, Any]]:
        """Get the jira projects by self."""
        result = await self._make_request_with_fallback("jira", "GET", "rest/api/3/project")
        if result.get("success"):
            return result["data"].get("values", result["data"])
        return []
