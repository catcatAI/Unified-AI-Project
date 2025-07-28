"""
Atlassian API 服务器
提供 REST API 接口供前端调用
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from ..integrations.rovo_dev_agent import RovoDevAgent
from ..integrations.atlassian_bridge import AtlassianBridge
from ..integrations.rovo_dev_connector import RovoDevConnector
from ..hsp.types import HSPTask

logger = logging.getLogger(__name__)

app = FastAPI(title="Atlassian API Server", version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储实例
rovo_dev_agent: Optional[RovoDevAgent] = None
atlassian_bridge: Optional[AtlassianBridge] = None

# 请求模型
class AtlassianConfigModel(BaseModel):
    domain: str
    userEmail: str
    apiToken: str
    cloudId: str

class ConfluencePageModel(BaseModel):
    spaceKey: str
    title: str
    content: str
    parentId: Optional[str] = None

class JiraIssueModel(BaseModel):
    projectKey: str
    summary: str
    description: str
    issueType: str = "Task"
    priority: str = "Medium"

class RovoDevTaskModel(BaseModel):
    capability: str
    parameters: Dict[str, Any]

class JQLSearchModel(BaseModel):
    jql: str

# 依赖注入
async def get_atlassian_bridge() -> AtlassianBridge:
    """获取 Atlassian Bridge 实例"""
    global atlassian_bridge
    if not atlassian_bridge:
        raise HTTPException(status_code=400, detail="Atlassian not configured")
    return atlassian_bridge

async def get_rovo_dev_agent() -> RovoDevAgent:
    """获取 Rovo Dev Agent 实例"""
    global rovo_dev_agent
    if not rovo_dev_agent:
        raise HTTPException(status_code=400, detail="Rovo Dev Agent not configured")
    return rovo_dev_agent

# 配置端点
@app.post("/api/atlassian/config")
async def configure_atlassian(config: AtlassianConfigModel):
    """配置 Atlassian 连接"""
    global rovo_dev_agent, atlassian_bridge
    
    try:
        # 构建配置字典
        config_dict = {
            'atlassian': {
                'domain': config.domain,
                'user_email': config.userEmail,
                'api_token': config.apiToken,
                'cloud_id': config.cloudId,
                'rovo_dev': {
                    'enabled': True,
                    'max_concurrent_requests': 5,
                    'timeout': 30,
                    'cache_ttl': 300,
                    'capabilities': [
                        {'name': 'code_analysis', 'description': '代码分析', 'enabled': True},
                        {'name': 'documentation_generation', 'description': '文档生成', 'enabled': True},
                        {'name': 'issue_tracking', 'description': '问题追踪', 'enabled': True},
                        {'name': 'project_management', 'description': '项目管理', 'enabled': True},
                        {'name': 'code_review', 'description': '代码审查', 'enabled': True}
                    ]
                }
            },
            'hsp_integration': {
                'agent_id': 'rovo-dev-agent'
            }
        }
        
        # 创建连接器和桥接器
        connector = RovoDevConnector(config_dict)
        await connector.start()
        
        atlassian_bridge = AtlassianBridge(connector)
        
        # 创建 Rovo Dev Agent
        rovo_dev_agent = RovoDevAgent(config_dict)
        await rovo_dev_agent.start()
        
        return {"status": "success", "message": "Atlassian configured successfully"}
        
    except Exception as e:
        logger.error(f"Failed to configure Atlassian: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/test-connection")
async def test_atlassian_connection(config: AtlassianConfigModel):
    """测试 Atlassian 连接"""
    try:
        # 创建临时连接器进行测试
        config_dict = {
            'atlassian': {
                'domain': config.domain,
                'user_email': config.userEmail,
                'api_token': config.apiToken,
                'cloud_id': config.cloudId
            }
        }
        
        connector = RovoDevConnector(config_dict)
        await connector.start()
        
        results = await connector.test_connection()
        await connector.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {"confluence": False, "jira": False, "error": str(e)}

# Confluence 端点
@app.get("/api/atlassian/confluence/spaces")
async def get_confluence_spaces(bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Confluence 空间列表"""
    try:
        spaces = await bridge.get_confluence_spaces()
        return spaces
    except Exception as e:
        logger.error(f"Failed to get spaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atlassian/confluence/spaces/{space_key}/pages")
async def get_confluence_pages(space_key: str, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Confluence 空间中的页面"""
    try:
        pages = await bridge.search_confluence_pages(space_key, "")
        return pages
    except Exception as e:
        logger.error(f"Failed to get pages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/confluence/pages")
async def create_confluence_page(page: ConfluencePageModel, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """创建 Confluence 页面"""
    try:
        result = await bridge.create_confluence_page(
            space_key=page.spaceKey,
            title=page.title,
            content=page.content,
            parent_id=page.parentId
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Jira 端点
@app.get("/api/atlassian/jira/projects")
async def get_jira_projects(bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Jira 项目列表"""
    try:
        projects = await bridge.get_jira_projects()
        return projects
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atlassian/jira/projects/{project_key}/issues")
async def get_jira_issues(project_key: str, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Jira 项目中的问题"""
    try:
        jql = f"project = {project_key} ORDER BY created DESC"
        issues = await bridge.search_jira_issues(jql)
        return issues
    except Exception as e:
        logger.error(f"Failed to get issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/jira/issues")
async def create_jira_issue(issue: JiraIssueModel, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """创建 Jira 问题"""
    try:
        result = await bridge.create_jira_issue(
            project_key=issue.projectKey,
            summary=issue.summary,
            description=issue.description,
            issue_type=issue.issueType,
            priority=issue.priority
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/jira/search")
async def search_jira_issues(search: JQLSearchModel, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """搜索 Jira 问题"""
    try:
        issues = await bridge.search_jira_issues(search.jql)
        return {"issues": issues}
    except Exception as e:
        logger.error(f"Failed to search issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rovo Dev Agent 端点
@app.get("/api/rovo-dev/status")
async def get_rovo_dev_status(agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """获取 Rovo Dev Agent 状态"""
    try:
        status = agent.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rovo-dev/tasks")
async def submit_rovo_dev_task(task: RovoDevTaskModel, agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """提交 Rovo Dev 任务"""
    try:
        # 创建 HSP 任务
        hsp_task = HSPTask(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            capability=task.capability,
            parameters=task.parameters,
            requester_id="web_ui"
        )
        
        await agent.submit_task(hsp_task)
        
        return {
            "taskId": hsp_task.task_id,
            "status": "submitted",
            "message": "Task submitted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rovo-dev/tasks")
async def get_rovo_dev_tasks(agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """获取 Rovo Dev 任务列表"""
    try:
        # 获取活动任务
        status = agent.get_status()
        active_tasks = list(status.get('active_tasks', {}).values())
        
        return active_tasks
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rovo-dev/tasks/history")
async def get_rovo_dev_task_history(limit: int = 50, agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """获取 Rovo Dev 任务历史"""
    try:
        history = agent.get_task_history(limit)
        return history
    except Exception as e:
        logger.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "atlassian_bridge": atlassian_bridge is not None,
            "rovo_dev_agent": rovo_dev_agent is not None and rovo_dev_agent.is_active
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)