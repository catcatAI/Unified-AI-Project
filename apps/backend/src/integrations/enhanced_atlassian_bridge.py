"""
增強版 Atlassian Bridge - 集成演示學習管理器
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from .atlassian_bridge import AtlassianBridge
from .rovo_dev_connector import RovoDevConnector
from apps.backend.src.core_ai.demo_learning_manager import demo_learning_manager

logger = logging.getLogger(__name__)

class EnhancedAtlassianBridge(AtlassianBridge):
    """增強版 Atlassian Bridge，支持演示學習功能"""
    
    def __init__(self, connector: RovoDevConnector):
        """初始化增強版橋接層
        
        Args:
            connector: Rovo Dev 連接器實例
        """
        super().__init__(connector)
        self.demo_manager = demo_learning_manager
        self.demo_mode_active = False
        
        # 檢查是否為演示模式
        asyncio.create_task(self._check_demo_mode())
    
    async def _check_demo_mode(self):
        """檢查並激活演示模式"""
        try:
            # 獲取認證信息
            credentials = {
                'api_token': self.config.get('api_token', ''),
                'cloud_id': self.config.get('cloud_id', ''),
                'user_email': self.config.get('user_email', ''),
                'domain': self.config.get('domain', '')
            }
            
            # 檢測演示金鑰
            if self.demo_manager.detect_demo_credentials(credentials):
                logger.info("檢測到演示金鑰，激活演示模式")
                await self.demo_manager.activate_demo_mode(credentials)
                self.demo_mode_active = True
                
                # 初始化演示數據
                await self._initialize_demo_data()
                
        except Exception as e:
            logger.error(f"檢查演示模式失敗: {e}")
    
    async def _initialize_demo_data(self):
        """初始化演示數據"""
        try:
            demo_config = self.demo_manager.config.get('demo_credentials', {})
            auto_init = demo_config.get('auto_initialization', {})
            
            if auto_init.get('enabled', False):
                steps = auto_init.get('steps', [])
                
                for step in steps:
                    if step == "create_demo_spaces":
                        await self._create_demo_spaces()
                    elif step == "setup_test_projects":
                        await self._setup_test_projects()
                    elif step == "initialize_agents":
                        await self._initialize_agents()
                    elif step == "configure_fallbacks":
                        await self._configure_fallbacks()
                    elif step == "setup_monitoring":
                        await self._setup_monitoring()
                
                logger.info("演示數據初始化完成")
                
        except Exception as e:
            logger.error(f"初始化演示數據失敗: {e}")
    
    async def _create_demo_spaces(self):
        """創建演示 Confluence 空間"""
        if not self.demo_mode_active:
            return
        
        try:
            demo_config = self.demo_manager.config.get('demo_credentials', {})
            spaces_config = demo_config.get('auto_initialization', {}).get('demo_data', {}).get('confluence_spaces', [])
            
            for space_config in spaces_config:
                # 在演示模式下，這裡會創建模擬的空間
                logger.info(f"創建演示空間: {space_config['name']} ({space_config['key']})")
                
                # 記錄學習數據
                await self.demo_manager.record_user_interaction(
                    action="create_demo_space",
                    context=space_config,
                    result="success"
                )
                
        except Exception as e:
            logger.error(f"創建演示空間失敗: {e}")
            await self.demo_manager.record_error_pattern(
                error_type="demo_initialization",
                error_message=str(e),
                context={"step": "create_demo_spaces"},
                resolution="logged_for_analysis"
            )
    
    async def _setup_test_projects(self):
        """設置測試 Jira 項目"""
        if not self.demo_mode_active:
            return
        
        try:
            demo_config = self.demo_manager.config.get('demo_credentials', {})
            projects_config = demo_config.get('auto_initialization', {}).get('demo_data', {}).get('jira_projects', [])
            
            for project_config in projects_config:
                logger.info(f"創建演示項目: {project_config['name']} ({project_config['key']})")
                
                # 記錄學習數據
                await self.demo_manager.record_user_interaction(
                    action="create_demo_project",
                    context=project_config,
                    result="success"
                )
                
        except Exception as e:
            logger.error(f"設置測試項目失敗: {e}")
            await self.demo_manager.record_error_pattern(
                error_type="demo_initialization",
                error_message=str(e),
                context={"step": "setup_test_projects"},
                resolution="logged_for_analysis"
            )
    
    async def _initialize_agents(self):
        """初始化代理"""
        logger.info("初始化演示代理")
        # 這裡可以初始化演示用的代理配置
    
    async def _configure_fallbacks(self):
        """配置備用機制"""
        logger.info("配置演示備用機制")
        # 確保備用機制在演示模式下正常工作
    
    async def _setup_monitoring(self):
        """設置監控"""
        logger.info("設置演示監控")
        # 設置演示模式下的監控
    
    # 重寫父類方法以添加學習功能
    
    async def create_confluence_page(
        self, 
        space_key: str, 
        title: str, 
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """創建 Confluence 頁面（增強版）"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await super().create_confluence_page(space_key, title, content, parent_id)
            
            # 記錄成功的用戶交互
            if self.demo_mode_active:
                await self.demo_manager.record_user_interaction(
                    action="create_confluence_page",
                    context={
                        "space_key": space_key,
                        "title": title,
                        "has_parent": parent_id is not None,
                        "content_length": len(content)
                    },
                    result="success"
                )
            
            return result
            
        except Exception as e:
            # 記錄錯誤
            if self.demo_mode_active:
                await self.demo_manager.record_error_pattern(
                    error_type="confluence_operation",
                    error_message=str(e),
                    context={
                        "operation": "create_page",
                        "space_key": space_key,
                        "title": title
                    },
                    resolution="fallback_attempted"
                )
                
                await self.demo_manager.record_user_interaction(
                    action="create_confluence_page",
                    context={
                        "space_key": space_key,
                        "title": title,
                        "error": str(e)
                    },
                    result="error"
                )
            
            raise
        
        finally:
            # 記錄性能指標
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            if self.demo_mode_active and hasattr(self.demo_manager, 'learning_data'):
                performance_metric = {
                    'operation': 'create_confluence_page',
                    'duration': duration,
                    'success': True,
                    'timestamp': asyncio.get_event_loop().time()
                }
                self.demo_manager.learning_data.setdefault('performance_metrics', []).append(performance_metric)
    
    async def create_jira_issue(
        self, 
        project_key: str, 
        summary: str, 
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """創建 Jira 問題（增強版）"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await super().create_jira_issue(project_key, summary, description, issue_type, priority, assignee)
            
            # 記錄成功的用戶交互
            if self.demo_mode_active:
                await self.demo_manager.record_user_interaction(
                    action="create_jira_issue",
                    context={
                        "project_key": project_key,
                        "issue_type": issue_type,
                        "priority": priority,
                        "has_assignee": assignee is not None,
                        "summary_length": len(summary)
                    },
                    result="success"
                )
            
            return result
            
        except Exception as e:
            # 記錄錯誤
            if self.demo_mode_active:
                await self.demo_manager.record_error_pattern(
                    error_type="jira_operation",
                    error_message=str(e),
                    context={
                        "operation": "create_issue",
                        "project_key": project_key,
                        "issue_type": issue_type
                    },
                    resolution="fallback_attempted"
                )
                
                await self.demo_manager.record_user_interaction(
                    action="create_jira_issue",
                    context={
                        "project_key": project_key,
                        "error": str(e)
                    },
                    result="error"
                )
            
            raise
        
        finally:
            # 記錄性能指標
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            if self.demo_mode_active and hasattr(self.demo_manager, 'learning_data'):
                performance_metric = {
                    'operation': 'create_jira_issue',
                    'duration': duration,
                    'success': True,
                    'timestamp': asyncio.get_event_loop().time()
                }
                self.demo_manager.learning_data.setdefault('performance_metrics', []).append(performance_metric)
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """獲取學習洞察"""
        if not self.demo_mode_active:
            return {"demo_mode": False, "message": "演示模式未激活"}
        
        return await self.demo_manager.get_learning_insights()
    
    def get_demo_status(self) -> Dict[str, Any]:
        """獲取演示狀態"""
        return {
            "demo_mode_active": self.demo_mode_active,
            "demo_manager_active": self.demo_manager.demo_mode,
            "storage_path": str(self.demo_manager.storage_path),
            "config_loaded": bool(self.demo_manager.config)
        }
    
    async def shutdown(self):
        """關閉增強版橋接層"""
        if self.demo_mode_active:
            await self.demo_manager.shutdown()
        
        # 調用父類的關閉方法（如果有的話）
        if hasattr(super(), 'shutdown'):
            await super().shutdown()