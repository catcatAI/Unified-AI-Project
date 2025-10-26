"""
Atlassian API - 处理Atlassian集成请求
"""
from diagnose_base_agent import
from fastapi import APIRouter, HTTPException, Depends

# 修复导入路径
from ...integrations.atlassian_cli_bridge import
from ...integrations.enhanced_atlassian_bridge import
from ...integrations.rovo_dev_connector import
# 修复导入路径
from ...core_services import

# 配置日志
logger, Any = logging.getLogger(__name__)

# 创建路由器
atlassian_router == APIRouter(prefix = " / api / v1 / atlassian", tags = ["Atlassian"])


class AtlassianConfig(BaseModel):
    domain, str
    user_email, str
    api_token, str
    cloud_id, str


class ConfluencePageCreate(BaseModel):
    space_key, str
    title, str
    content, str


class JiraIssueCreate(BaseModel):
    project_key, str
    summary, str
    description, Optional[str] = None
    issue_type, str = "Task"


class TaskAssignment(BaseModel):
    task_id, str
    agent_id, str


# 全局变量存储配置和桥接器实例
atlassian_config, Optional[AtlassianConfig] = None
atlassian_bridge, Optional[AtlassianCLIBridge] = None
enhanced_bridge, Optional[EnhancedAtlassianBridge] = None


@atlassian_router.post(" / configure")
async def configure_atlassian(config, AtlassianConfig):
    """配置Atlassian集成"""
    global atlassian_config, atlassian_bridge, enhanced_bridge

    try,
        # 保存配置
        atlassian_config = config

        # 初始化Atlassian CLI桥接器
        acli_path = os.getenv("ACLIPATH", "acli.exe")
        atlassian_bridge == AtlassianCLIBridge(acli_path = acli_path)

        # 初始化增强版桥接器
        # 注意：在实际实现中, 这里需要传入一个有效的RovoDevConnector实例
        # 为了简化, 我们创建一个基本的连接器
        rovo_connector == RovoDevConnector({)}
            "atlassian": {}
                "domain": config.domain(),
                "user_email": config.user_email(),
                "api_token": config.api_token(),
                "cloud_id": config.cloud_id()
{            }
{(        })
        enhanced_bridge == EnhancedAtlassianBridge(rovo_connector)

        return {"success": True,
    "message": "Atlassian integration configured successfully"}
    except Exception as e, ::
        logger.exception("Failed to configure Atlassian integration"):::
        return {"success": False,
    "error": "An internal error occurred while configuring. Please contact support or \
    try again later."}:
@atlassian_router.get(" / status")
async def get_atlassian_status():
    """获取Atlassian服务状态"""
    if not atlassian_bridge, ::
        return {}
            "connected": False,
            "services": []
                {"name": "Confluence", "status": "disconnected", "lastSync": "Never",
    "health": 0}
                {"name": "Jira", "status": "disconnected", "lastSync": "Never",
    "health": 0}
                {"name": "Bitbucket", "status": "disconnected", "lastSync": "Never",
    "health": 0}
[            ]
{        }

    try,
        # 获取Atlassian CLI状态
        status = atlassian_bridge.get_status()
        # 构建服务状态
        services = []
            {"name": "Confluence",
    "status": "connected" if status["acli_available"] else "disconnected",
    "lastSync": "Just now", "health": 95}:
{                "name": "Jira",
    "status": "connected" if status["acli_available"] else "disconnected",
    "lastSync": "Just now", "health": 90}:
{"name": "Bitbucket", "status": "disconnected", "lastSync": "Never", "health": 0}
[        ]

        return {}
            "connected": status["acli_available"]
            "services": services
{        }
    except Exception as e, ::
        logger.error(f"Failed to get Atlassian status, {e}")
        return {}
            "connected": False,
            "services": []
                {"name": "Confluence", "status": "error", "lastSync": "Error",
    "health": 0}
                {"name": "Jira", "status": "error", "lastSync": "Error", "health": 0}
                {"name": "Bitbucket", "status": "error", "lastSync": "Error",
    "health": 0}
[            ]
{        }

@atlassian_router.get(" / health")
async def get_atlassian_health():
    """获取Atlassian系统健康状态"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        # 这里可以实现更详细的健康检查逻辑
        status = atlassian_bridge.get_status()
        return {}
            "status": "healthy" if status["acli_available"] else "unhealthy", :::
                details": status
{        }
    except Exception as e, ::
        logger.error(f"Failed to get Atlassian health, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

# Confluence相关端点
@atlassian_router.get(" / confluence / spaces")
async def get_confluence_spaces():
    """获取Confluence空间列表"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        result = atlassian_bridge.get_confluence_spaces()
        if result["success"]::
            return {"spaces": result["spaces"] "count": result["count"]}
        else,
            raise HTTPException(status_code = 500, detail = result.get("error",
    "Failed to get Confluence spaces"))
    except Exception as e, ::
        logger.error(f"Failed to get Confluence spaces, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.post(" / confluence / page")
async def create_confluence_page(page_data, ConfluencePageCreate):
    """创建Confluence页面"""
    if not enhanced_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Enhanced Atlassian integration not configured")
    
    try,
        # 注意：在实际实现中, 这里需要调用增强桥接器的相应方法
        # 由于我们没有完整的实现, 这里只是模拟成功响应
        return {}
            "success": True,
            "page": {}
                "id": "12345",
                "title": page_data.title(),
                "space_key": page_data.space_key()
{            }
{        }
    except Exception as e, ::
        logger.error(f"Failed to create Confluence page, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.get(" / confluence / search")
async def search_confluence_content(q, str):
    """搜索Confluence内容"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        # 注意：AtlassianCLIBridge可能没有直接的搜索方法
        # 这里需要根据实际实现进行调整
        result = atlassian_bridge.search_confluence_content(q)
        if result["success"]::
            return {"results": result["content"] "count": result["count"]}
        else,
            raise HTTPException(status_code = 500, detail = result.get("error",
    "Failed to search Confluence content"))
    except Exception as e, ::
        logger.error(f"Failed to search Confluence content, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

# Jira相关端点
@atlassian_router.get(" / jira / projects")
async def get_jira_projects():
    """获取Jira项目列表"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        result = atlassian_bridge.get_jira_projects()
        if result["success"]::
            return {"projects": result["projects"] "count": result["count"]}
        else,
            raise HTTPException(status_code = 500, detail = result.get("error",
    "Failed to get Jira projects"))
    except Exception as e, ::
        logger.error(f"Failed to get Jira projects, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.get(" / jira / issues")
async def get_jira_issues(jql, Optional[str] = None, limit, int == 50):
    """获取Jira问题列表"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        result = atlassian_bridge.get_jira_issues(jql = jql, limit = limit)
        if result["success"]::
            return {"issues": result["issues"] "count": result["count"]}
        else,
            raise HTTPException(status_code = 500, detail = result.get("error",
    "Failed to get Jira issues"))
    except Exception as e, ::
        logger.error(f"Failed to get Jira issues, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.post(" / jira / issue")
async def create_jira_issue(issue_data, JiraIssueCreate):
    """创建Jira问题"""
    if not atlassian_bridge, ::
        raise HTTPException(status_code = 400,
    detail = "Atlassian integration not configured")
    
    try,
        result = atlassian_bridge.create_jira_issue()
    project_key = issue_data.project_key(),
            summary = issue_data.summary(),
            description = issue_data.description(),
(            issue_type = issue_data.issue_type())
        if result["success"]::
            return {"success": True, "issue": result["issue"] "key": result["key"]}
        else,
            raise HTTPException(status_code = 500, detail = result.get("error",
    "Failed to create Jira issue"))
    except Exception as e, ::
        logger.error(f"Failed to create Jira issue, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

# Rovo Dev Agents相关端点
@atlassian_router.get(" / rovo / agents")
async def get_rovo_agents(services == Depends(get_services))
    """获取Rovo Dev Agents列表"""
    try,
        # 从服务中获取Rovo Dev Agents信息
        # 这里需要根据实际的服务实现进行调整
        agents = []
            {"id": "agent_1", "name": "Code Analysis Agent", "status": "active",
    "capabilities": ["code_analysis", "bug_detection"]}
            {"id": "agent_2", "name": "Documentation Agent", "status": "active",
    "capabilities": ["doc_generation", "content_creation"]}
            {"id": "agent_3", "name": "Project Management Agent", "status": "busy",
    "capabilities": ["task_planning", "progress_tracking"]}
[        ]
        return {"agents": agents}
    except Exception as e, ::
        logger.error(f"Failed to get Rovo Dev agents, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.get(" / rovo / tasks")
async def get_rovo_tasks():
    """获取Rovo Dev任务列表"""
    try,
        # 模拟任务数据
        tasks = []
            {"id": "task_1", "agentId": "agent_1", "title": "Analyze login module",
    "status": "completed", "createdAt": "2023 - 01 - 01T10, 00, 00Z",
    "updatedAt": "2023 - 01 - 01T10, 30, 00Z"}
            {"id": "task_2", "agentId": "agent_2",
    "title": "Generate API documentation", "status": "in_progress",
    "createdAt": "2023 - 01 - 01T11, 00, 00Z", "updatedAt": "2023 - 01 - 01T11, 15, 00Z"}
            {"id": "task_3", "agentId": "agent_3", "title": "Plan sprint tasks",
    "status": "pending", "createdAt": "2023 - 01 - 01T12, 00, 00Z",
    "updatedAt": "2023 - 01 - 01T12, 00, 00Z"}
[        ]
        return {"tasks": tasks}
    except Exception as e, ::
        logger.error(f"Failed to get Rovo Dev tasks, {e}")
        raise HTTPException(status_code = 500, detail = str(e))

@atlassian_router.post(" / rovo / assign")
async def assign_task_to_agent(assignment, TaskAssignment):
    """分配任务给Agent"""
    try,
        # 模拟任务分配成功
        return {"success": True,
    "message": f"Task {assignment.task_id} assigned to agent {assignment.agent_id}"}
    except Exception as e, ::
        logger.error(f"Failed to assign task to agent, {e}")
        raise HTTPException(status_code = 500, detail = str(e))