"""
Atlassian 服务桥接层
提供统一的 Atlassian 服务接口，包括 Confluence、Jira、Bitbucket
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re

from .rovo_dev_connector import RovoDevConnector

logger = logging.getLogger(__name__)

class AtlassianBridge:
    """Atlassian 服务统一桥接层"""
    
    def __init__(self, connector: RovoDevConnector):
        """初始化桥接层
        
        Args:
            connector: Rovo Dev 连接器实例
        """
        self.connector = connector
        self.config = connector.config.get('atlassian', {})
        
    # ==================== Confluence 操作 ====================
    
    async def create_confluence_page(
        self, 
        space_key: str, 
        title: str, 
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """在 Confluence 中创建页面
        
        Args:
            space_key: 空间键
            title: 页面标题
            content: 页面内容 (Markdown 格式)
            parent_id: 父页面 ID (可选)
            
        Returns:
            Dict: 创建的页面信息
        """
        # 转换 Markdown 到 Confluence 存储格式
        storage_content = self._markdown_to_confluence_storage(content)
        
        payload = {
            'type': 'page',
            'title': title,
            'space': {'key': space_key},
            'body': {
                'storage': {
                    'value': storage_content,
                    'representation': 'storage'
                }
            }
        }
        
        if parent_id:
            payload['ancestors'] = [{'id': parent_id}]
            
        url = f"{self.connector.base_urls['confluence']}/content"
        result = await self.connector._make_request('POST', url, data=payload)
        
        logger.info(f"创建 Confluence 页面成功: {result.get('id')} - {title}")
        return result
        
    async def update_confluence_page(
        self, 
        page_id: str, 
        title: str, 
        content: str,
        version: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新 Confluence 页面
        
        Args:
            page_id: 页面 ID
            title: 新标题
            content: 新内容 (Markdown 格式)
            version: 版本号 (如果不提供会自动获取)
            
        Returns:
            Dict: 更新后的页面信息
        """
        if not version:
            # 获取当前版本
            page_info = await self.get_confluence_page(page_id)
            version = page_info['version']['number'] + 1
            
        storage_content = self._markdown_to_confluence_storage(content)
        
        payload = {
            'version': {'number': version},
            'title': title,
            'type': 'page',
            'body': {
                'storage': {
                    'value': storage_content,
                    'representation': 'storage'
                }
            }
        }
        
        url = f"{self.connector.base_urls['confluence']}/content/{page_id}"
        result = await self.connector._make_request('PUT', url, data=payload)
        
        logger.info(f"更新 Confluence 页面成功: {page_id} - {title}")
        return result
        
    async def get_confluence_page(self, page_id: str) -> Dict[str, Any]:
        """获取 Confluence 页面信息
        
        Args:
            page_id: 页面 ID
            
        Returns:
            Dict: 页面信息
        """
        url = f"{self.connector.base_urls['confluence']}/content/{page_id}"
        params = {'expand': 'body.storage,version,space'}
        
        return await self.connector._make_request('GET', url, params=params)
        
    async def search_confluence_pages(
        self, 
        space_key: str, 
        query: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """搜索 Confluence 页面
        
        Args:
            space_key: 空间键
            query: 搜索查询
            limit: 结果限制
            
        Returns:
            List[Dict]: 搜索结果
        """
        cql = f'space = "{space_key}" AND text ~ "{query}"'
        url = f"{self.connector.base_urls['confluence']}/content/search"
        params = {
            'cql': cql,
            'limit': limit,
            'expand': 'version,space'
        }
        
        result = await self.connector._make_request('GET', url, params=params)
        return result.get('results', [])
        
    # ==================== Jira 操作 ====================
    
    async def create_jira_issue(
        self, 
        project_key: str, 
        summary: str, 
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """在 Jira 中创建问题
        
        Args:
            project_key: 项目键
            summary: 问题摘要
            description: 问题描述
            issue_type: 问题类型
            priority: 优先级
            assignee: 指派人 (账户 ID)
            
        Returns:
            Dict: 创建的问题信息
        """
        payload = {
            'fields': {
                'project': {'key': project_key},
                'summary': summary,
                'description': {
                    'type': 'doc',
                    'version': 1,
                    'content': [
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': description
                                }
                            ]
                        }
                    ]
                },
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
        }
        
        if assignee:
            payload['fields']['assignee'] = {'accountId': assignee}
            
        url = f"{self.connector.base_urls['jira']}/issue"
        result = await self.connector._make_request('POST', url, data=payload)
        
        logger.info(f"创建 Jira 问题成功: {result.get('key')} - {summary}")
        return result
        
    async def update_jira_issue(
        self, 
        issue_key: str, 
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Jira 问题
        
        Args:
            issue_key: 问题键
            fields: 要更新的字段
            
        Returns:
            Dict: 更新结果
        """
        payload = {'fields': fields}
        url = f"{self.connector.base_urls['jira']}/issue/{issue_key}"
        
        result = await self.connector._make_request('PUT', url, data=payload)
        logger.info(f"更新 Jira 问题成功: {issue_key}")
        return result
        
    async def get_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """获取 Jira 问题信息
        
        Args:
            issue_key: 问题键
            
        Returns:
            Dict: 问题信息
        """
        url = f"{self.connector.base_urls['jira']}/issue/{issue_key}"
        params = {'expand': 'names,schema,operations,editmeta,changelog,renderedFields'}
        
        return await self.connector._make_request('GET', url, params=params)
        
    async def search_jira_issues(
        self, 
        jql: str, 
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """使用 JQL 搜索 Jira 问题
        
        Args:
            jql: JQL 查询语句
            max_results: 最大结果数
            
        Returns:
            List[Dict]: 搜索结果
        """
        payload = {
            'jql': jql,
            'maxResults': max_results,
            'fields': ['summary', 'status', 'assignee', 'created', 'updated']
        }
        
        url = f"{self.connector.base_urls['jira']}/search"
        result = await self.connector._make_request('POST', url, data=payload)
        
        return result.get('issues', [])
        
    async def transition_jira_issue(
        self, 
        issue_key: str, 
        transition_id: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """转换 Jira 问题状态
        
        Args:
            issue_key: 问题键
            transition_id: 转换 ID
            comment: 评论 (可选)
            
        Returns:
            Dict: 转换结果
        """
        payload = {
            'transition': {'id': transition_id}
        }
        
        if comment:
            payload['update'] = {
                'comment': [
                    {
                        'add': {
                            'body': {
                                'type': 'doc',
                                'version': 1,
                                'content': [
                                    {
                                        'type': 'paragraph',
                                        'content': [
                                            {
                                                'type': 'text',
                                                'text': comment
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
            
        url = f"{self.connector.base_urls['jira']}/issue/{issue_key}/transitions"
        result = await self.connector._make_request('POST', url, data=payload)
        
        logger.info(f"转换 Jira 问题状态成功: {issue_key}")
        return result
        
    # ==================== Bitbucket 操作 ====================
    
    async def get_bitbucket_repositories(
        self, 
        workspace: str
    ) -> List[Dict[str, Any]]:
        """获取 Bitbucket 仓库列表
        
        Args:
            workspace: 工作空间名称
            
        Returns:
            List[Dict]: 仓库列表
        """
        url = f"{self.connector.base_urls['bitbucket']}/repositories/{workspace}"
        result = await self.connector._make_request('GET', url)
        
        return result.get('values', [])
        
    async def get_bitbucket_pull_requests(
        self, 
        workspace: str, 
        repo_slug: str,
        state: str = "OPEN"
    ) -> List[Dict[str, Any]]:
        """获取 Bitbucket Pull Request 列表
        
        Args:
            workspace: 工作空间名称
            repo_slug: 仓库名称
            state: PR 状态 (OPEN, MERGED, DECLINED)
            
        Returns:
            List[Dict]: PR 列表
        """
        url = f"{self.connector.base_urls['bitbucket']}/repositories/{workspace}/{repo_slug}/pullrequests"
        params = {'state': state}
        
        result = await self.connector._make_request('GET', url, params=params)
        return result.get('values', [])
        
    # ==================== 辅助方法 ====================
    
    def _markdown_to_confluence_storage(self, markdown: str) -> str:
        """将 Markdown 转换为 Confluence 存储格式
        
        Args:
            markdown: Markdown 内容
            
        Returns:
            str: Confluence 存储格式内容
        """
        # 简单的 Markdown 到 Confluence 转换
        # 在实际应用中，可能需要更复杂的转换逻辑
        
        # 转换标题
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', markdown, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        
        # 转换粗体和斜体
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        
        # 转换代码块
        content = re.sub(r'```(\w+)?\n(.*?)\n```', r'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">\1</ac:parameter><ac:plain-text-body><![CDATA[\2]]></ac:plain-text-body></ac:structured-macro>', content, flags=re.DOTALL)
        
        # 转换行内代码
        content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
        
        # 转换链接
        content = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', content)
        
        # 转换段落
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        for p in paragraphs:
            if p.strip() and not p.strip().startswith('<'):
                formatted_paragraphs.append(f'<p>{p.strip()}</p>')
            else:
                formatted_paragraphs.append(p)
                
        return '\n'.join(formatted_paragraphs)
        
    async def link_jira_to_confluence(
        self, 
        jira_key: str, 
        confluence_page_id: str
    ) -> bool:
        """将 Jira 问题链接到 Confluence 页面
        
        Args:
            jira_key: Jira 问题键
            confluence_page_id: Confluence 页面 ID
            
        Returns:
            bool: 链接是否成功
        """
        try:
            # 在 Jira 问题中添加 Confluence 页面链接
            comment = f"相关文档: [Confluence 页面|{self.connector.base_urls['confluence']}/content/{confluence_page_id}]"
            
            await self.connector._make_request(
                'POST',
                f"{self.connector.base_urls['jira']}/issue/{jira_key}/comment",
                data={
                    'body': {
                        'type': 'doc',
                        'version': 1,
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': comment
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
            
            logger.info(f"成功链接 Jira {jira_key} 到 Confluence 页面 {confluence_page_id}")
            return True
            
        except Exception as e:
            logger.error(f"链接失败: {e}")
            return False
    
    def _format_content_for_confluence(self, content: str) -> str:
        """格式化内容为 Confluence 存储格式
        
        Args:
            content: 原始内容
            
        Returns:
            str: Confluence 存储格式内容
        """
        return self._markdown_to_confluence_storage(content)
    
    def _map_jira_fields(self, project_key: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """映射 Jira 字段
        
        Args:
            project_key: 项目键
            issue_data: 问题数据
            
        Returns:
            Dict: 映射后的字段
        """
        fields = {
            'project': {'key': project_key},
            'summary': issue_data.get('summary', ''),
            'issuetype': {'name': issue_data.get('issue_type', 'Task')},
            'priority': {'name': issue_data.get('priority', 'Medium')}
        }
        
        # 处理描述
        description = issue_data.get('description', '')
        if description:
            fields['description'] = {
                'type': 'doc',
                'version': 1,
                'content': [
                    {
                        'type': 'paragraph',
                        'content': [
                            {
                                'type': 'text',
                                'text': description
                            }
                        ]
                    }
                ]
            }
        
        # 处理分配人
        assignee = issue_data.get('assignee')
        if assignee:
            fields['assignee'] = {'accountId': assignee}
        
        return {'fields': fields}
    
    async def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """获取 Confluence 空间列表
        
        Returns:
            List[Dict]: 空间列表
        """
        url = f"{self.connector.base_urls['confluence']}/space"
        response = await self.connector._make_request('GET', url)
        return response.get('results', [])
    
    async def get_jira_projects(self) -> List[Dict[str, Any]]:
        """获取 Jira 项目列表
        
        Returns:
            List[Dict]: 项目列表
        """
        url = f"{self.connector.base_urls['jira']}/project"
        return await self.connector._make_request('GET', url)