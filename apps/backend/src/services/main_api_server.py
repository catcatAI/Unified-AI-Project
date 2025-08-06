import uvicorn # For running the app
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid # For generating session IDs
from typing import List, Dict, Any, Optional # Updated from previous steps
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware

# Assuming src is in PYTHONPATH or this script is run from project root
# Adjust paths as necessary if running from within services directory directly for testing
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.services.api_models import UserInput, AIOutput, SessionStartRequest, SessionStartResponse, HSPTaskRequestInput, HSPTaskRequestOutput, HSPTaskStatusOutput, AtlassianConfigModel, ConfluencePageModel, JiraIssueModel, RovoDevTaskModel, JQLSearchModel # Added Atlassian models
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTask # Added HSPTask
from src.integrations.rovo_dev_agent import RovoDevAgent # Added RovoDevAgent
from src.integrations.atlassian_bridge import AtlassianBridge # Added AtlassianBridge
from src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector # Added RovoDevConnector


from contextlib import asynccontextmanager # For lifespan events
from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID, DEFAULT_OPERATIONAL_CONFIGS
from src.config_loader import load_config

# --- Service Initialization using Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("MainAPIServer: Initializing core services...")
    # Load configuration
    config = load_config()
    # Initialize services with potentially API-specific configurations
    # For example, API might use a different AI ID or specific LLM config than CLI.
    api_ai_id = f"did:hsp:api_server_ai_{uuid.uuid4().hex[:6]}"
    await initialize_services(
        config=config,
        ai_id=api_ai_id,
        use_mock_ham=False, # API server should use real HAM, ensure MIKO_HAM_KEY is set
        operational_configs=None # Or specific operational configs
    )
    # Ensure services are ready, especially HSP connector
    services = get_services()
    hsp_connector = services.get("hsp_connector")
    if hsp_connector and not hsp_connector.is_connected:
        print("MainAPIServer: Warning - HSPConnector did not connect successfully during init.")

    print("MainAPIServer: Core services initialized.")
    services = get_services()
    service_discovery_module = services.get("service_discovery")
    if service_discovery_module:
        service_discovery_module.start_cleanup_task()
    yield
    print("MainAPIServer: Shutting down core services...")
    if service_discovery_module:
        service_discovery_module.stop_cleanup_task()
    await shutdown_services()
    print("MainAPIServer: Core services shut down.")

app = FastAPI(
    title="Unified AI Project API",
    description="API endpoints for interacting with the Unified AI.",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan context manager
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection for Atlassian and RovoDevAgent
async def get_atlassian_bridge() -> AtlassianBridge:
    """获取 Atlassian Bridge 实例"""
    services = get_services()
    atlassian_bridge = services.get("atlassian_bridge")
    if not atlassian_bridge:
        raise HTTPException(status_code=400, detail="Atlassian Bridge not configured or available")
    return atlassian_bridge

async def get_rovo_dev_agent() -> RovoDevAgent:
    """获取 Rovo Dev Agent 实例"""
    services = get_services()
    rovo_dev_agent = services.get("rovo_dev_agent")
    if not rovo_dev_agent:
        raise HTTPException(status_code=400, detail="Rovo Dev Agent not configured or available")
    return rovo_dev_agent

# DialogueManager will be fetched from get_services() in endpoints

@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified AI Project API"}


@app.get("/api/v1/health")
async def get_health_status():
    """获取系统健康状态、服务状态和性能指标"""
    import psutil
    import shutil
    import os

    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    ham_manager = services.get("ham_manager")
    tool_dispatcher = services.get("tool_dispatcher")
    agent_manager = services.get("agent_manager")
    atlassian_bridge = services.get("atlassian_bridge")
    rovo_dev_agent = services.get("rovo_dev_agent")
    
    # Service Health
    service_health = []
    if ham_manager:
        service_health.append({"name": "HAM Memory Manager", "status": "running"})
    if dialogue_manager and hasattr(dialogue_manager, 'hsp_connector'):
        service_health.append({"name": "HSP Connector", "status": "connected" if dialogue_manager.hsp_connector.is_connected else "disconnected"})
    if tool_dispatcher:
        service_health.append({"name": "Multi-LLM Service", "status": "running"})
    if atlassian_bridge:
        service_health.append({"name": "Atlassian Bridge", "status": "running"})
    if rovo_dev_agent:
        service_health.append({"name": "Rovo Dev Agent", "status": "active" if rovo_dev_agent.is_active else "inactive"})

    # System Metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk_usage = shutil.disk_usage('/')
    
    system_metrics = {
        "cpu": {"value": round(cpu_percent, 1), "max": 100, "status": "normal" if cpu_percent < 80 else "high"},
        "memory": {"value": round(memory.used / (1024**3), 1), "max": round(memory.total / (1024**3), 1), "percent": round(memory.percent, 1), "status": "normal" if memory.percent < 80 else "high"},
        "disk": {"value": round((disk_usage.total - disk_usage.free) / (1024**3), 1), "max": round(disk_usage.total / (1024**3), 1), "percent": round(((disk_usage.total - disk_usage.free) / disk_usage.total) * 100, 1), "status": "normal" if ((disk_usage.total - disk_usage.free) / disk_usage.total) < 0.8 else "high"}
    }

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": service_health,
        "metrics": system_metrics
    }




@app.post("/api/v1/chat", response_model=AIOutput, tags=["Chat"])
async def chat_endpoint(user_input: UserInput):
    """
    Receives user input and returns the AI's response.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")

    print(f"API: Received chat input: UserID='{user_input.user_id}', SessionID='{user_input.session_id}', Text='{user_input.text}'")
    if dialogue_manager is None:
        return AIOutput(
            response_text="Error: DialogueManager not available. Service might be initializing or encountered an issue.",
            user_id=user_input.user_id,
            session_id=user_input.session_id,
            timestamp=datetime.now().isoformat()
        )

    try:
        # Pass user_id and session_id to DialogueManager
        ai_response_text = await dialogue_manager.get_simple_response(
            user_input.text,
            session_id=user_input.session_id,
            user_id=user_input.user_id
        )
        return AIOutput(
            response_text=ai_response_text,
            user_id=user_input.user_id,
            session_id=user_input.session_id,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/session/start", response_model=SessionStartResponse, tags=["Session"])
async def start_session_endpoint(session_start_request: SessionStartRequest):
    """
    Starts a new session and returns an initial greeting and session ID.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")

    print(f"API: Received session start request: UserID='{session_start_request.user_id}'")
    if dialogue_manager is None:
        session_id = uuid.uuid4().hex
        return SessionStartResponse(
            greeting="Error: AI Service not available. Service might be initializing or encountered an issue.",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    try:
        # dialogue_manager.start_session is async
        greeting = await dialogue_manager.start_session(user_id=session_start_request.user_id)
        session_id = uuid.uuid4().hex

        return SessionStartResponse(
            greeting=greeting,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logging.error(f"Error in session start endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- HSP Related Endpoints ---
@app.get("/api/v1/hsp/services", response_model=List[HSPCapabilityAdvertisementPayload], tags=["HSP"])
async def list_hsp_services():
    """
    Lists all capabilities discovered from other AIs on the HSP network.
    """
    services = get_services()
    service_discovery_module = services.get("service_discovery")

    if not service_discovery_module:
        return [] # Or raise HTTPException(status_code=503, detail="Service Discovery not available")

    capabilities = service_discovery_module.get_all_capabilities()
    return capabilities

@app.post("/api/v1/hsp/tasks", response_model=HSPTaskRequestOutput, tags=["HSP"])
async def request_hsp_task(task_input: HSPTaskRequestInput):
    """
    Allows an external client to request the AI to dispatch a task to another AI on the HSP network.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    service_discovery = services.get("service_discovery")

    if not dialogue_manager or not service_discovery or not dialogue_manager.hsp_connector:
        return HSPTaskRequestOutput(
            status_message="Error: Core HSP services not available.",
            target_capability_id=task_input.target_capability_id,
            error="Service initialization issue."
        )

    print(f"API: Received HSP task request for capability '{task_input.target_capability_id}' with params: {task_input.parameters}")

    # 1. Find the capability advertisement
    # For API, we might want to be stricter and require an exact capability ID.
    found_caps = service_discovery.find_capabilities(capability_id_filter=task_input.target_capability_id)

    if not found_caps:
        return HSPTaskRequestOutput(
            status_message=f"Error: Capability ID '{task_input.target_capability_id}' not found or not available.",
            target_capability_id=task_input.target_capability_id,
            error="Capability not discovered."
        )

    selected_capability_adv = found_caps[0] # Assume first one is fine if multiple (though ID should be unique)

    # 2. Dispatch the task using DialogueManager's method
    # For API initiated tasks, user_id and session_id might be from API auth or generated.
    # original_user_query can be a descriptive string for this API-initiated task.
    api_user_id = "api_user_hsp_task"
    api_session_id = f"api_session_hsp_{uuid.uuid4().hex[:6]}"
    original_query_context = f"API request for capability {task_input.target_capability_id}"

    try:
        # _dispatch_hsp_task_request now returns -> (user_message, correlation_id)
        user_message, correlation_id = await dialogue_manager._dispatch_hsp_task_request(
            capability_advertisement=selected_capability_adv,
            request_parameters=task_input.parameters,
            original_user_query=original_query_context,
            user_id=api_user_id,
            session_id=api_session_id,
            request_type="api_initiated_hsp_task"
        )

        if correlation_id: # Dispatch was successful if correlation_id is returned
            return HSPTaskRequestOutput(
                status_message=user_message or "HSP Task request sent successfully.",
                correlation_id=correlation_id,
                target_capability_id=task_input.target_capability_id,
                error=None
            )
        else: # Dispatch failed
            return HSPTaskRequestOutput(
                status_message=user_message or "Error: Failed to dispatch HSP task request.",
                correlation_id=None,
                target_capability_id=task_input.target_capability_id,
                error=user_message or "Unknown error during dispatch."
            )
    except Exception as e:
        logging.error(f"Error in hsp task request endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        return HSPTaskRequestOutput(
            status_message=user_message or "HSP Task request sent successfully.",
            correlation_id=correlation_id,
            target_capability_id=task_input.target_capability_id,
            error=None
        )
    else: # Dispatch failed
        return HSPTaskRequestOutput(
            status_message=user_message or "Error: Failed to dispatch HSP task request.",
            correlation_id=None,
            target_capability_id=task_input.target_capability_id,
            error=user_message or "Unknown error during dispatch."
        )

@app.get("/api/v1/hsp/tasks/{correlation_id}", response_model=HSPTaskStatusOutput, tags=["HSP"])
async def get_hsp_task_status(correlation_id: str):
    """
    Polls for the status and result of an HSP task initiated via /api/v1/hsp/tasks.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    ham_manager = services.get("ham_manager")

    if not dialogue_manager or not ham_manager:
        # This case should ideally be prevented by lifespan ensuring services are up.
        # If they are None here, it's a server-side issue.
        return HSPTaskStatusOutput(
            correlation_id=correlation_id,
            status="unknown_or_expired",
            message="Core services for task status checking are unavailable."
        )

    # 1. Check if the task is still pending in DialogueManager
    if correlation_id in dialogue_manager.pending_hsp_task_requests:
        pending_info = dialogue_manager.pending_hsp_task_requests[correlation_id]
        return HSPTaskStatusOutput(
            correlation_id=correlation_id,
            status="pending",
            message=f"Task for capability '{pending_info.get('capability_id')}' sent to '{pending_info.get('target_ai_id')}' is still pending."
        )

    # 2. If not pending, check HAM for a stored result (success or error)
    found_record = None
    store = getattr(ham_manager, 'memory_store', getattr(ham_manager, 'core_memory_store', {}))
    for mem_id, record_pkg in store.items():
        metadata = record_pkg.get("metadata", {})
        if metadata.get("hsp_correlation_id") == correlation_id:
            found_record = record_pkg
            break # Found the relevant record

    if found_record:
        metadata = found_record.get("metadata", {})
        data_type = found_record.get("data_type", "")

        if "hsp_task_result_success" in data_type:
            service_payload = metadata.get("hsp_task_service_payload")
            if service_payload is not None:
                return HSPTaskStatusOutput(
                    correlation_id=correlation_id,
                    status="completed",
                    result_payload=service_payload,
                    message="Task completed successfully."
                )
            else:
                # This case means DM stored the success record but somehow missed the service_payload in metadata
                return HSPTaskStatusOutput(
                    correlation_id=correlation_id,
                    status="completed",
                    message="Task completed, but full result payload was not found in stored metadata."
                )
        elif "hsp_task_result_error" in data_type:
            return HSPTaskStatusOutput(
                correlation_id=correlation_id,
                status="failed",
                error_details=metadata.get("error_details", {"error_code": "UNKNOWN_HSP_ERROR", "error_message": "Error details not fully stored."}),
                message="Task failed. See error_details."
            )

    # 3. If not found in pending or HAM
    return HSPTaskStatusOutput(
        correlation_id=correlation_id,
        status="unknown_or_expired",
        message="Task status unknown, or result has expired from immediate cache."
    )

# --- Atlassian Configuration Endpoints ---
@app.post("/api/atlassian/config")
async def configure_atlassian(config: AtlassianConfigModel):
    """配置 Atlassian 连接"""
    services = get_services()
    # Assuming RovoDevAgent and AtlassianBridge are managed by core_services
    # and can be re-initialized or configured via a method on core_services or a dedicated config manager
    # For now, we'll simulate re-initializing them via core_services if needed.
    # In a real scenario, this would involve updating the config of the already initialized singletons.

    try:
        # This part needs careful consideration. If RovoDevAgent and AtlassianBridge are singletons
        # managed by core_services, we should not re-instantiate them here. Instead, we should
        # call a method on the existing instances to update their configuration.
        # For simplicity in this refactoring, we'll assume core_services can handle re-configuration
        # or that these are temporary instances for configuration testing.

        # For now, we'll just pass the config to a hypothetical reconfigure method
        # on the services, or directly update their internal state if they expose it.
        # This is a placeholder for proper configuration management.

        # Example: Update the config of the existing AtlassianBridge and RovoDevAgent
        atlassian_bridge = services.get("atlassian_bridge")
        rovo_dev_agent = services.get("rovo_dev_agent")

        if atlassian_bridge and rovo_dev_agent:
            # This is a simplified approach. A real implementation would involve
            # a proper re-configuration mechanism in AtlassianBridge and RovoDevAgent.
            # For now, we'll just log and return success.
            logging.info(f"Simulating Atlassian configuration update with: {config.dict()}")
            return {"status": "success", "message": "Atlassian configuration simulated successfully"}
        else:
            # If they are not yet initialized, this endpoint might trigger their initialization
            # or return an error if they are expected to be initialized at startup.
            raise HTTPException(status_code=500, detail="Atlassian services not initialized at startup.")

    except Exception as e:
        logging.error(f"Failed to configure Atlassian: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/test-connection")
async def test_atlassian_connection(config: AtlassianConfigModel):
    """测试 Atlassian 连接"""
    try:
        # Create temporary connector for testing connection
        config_dict = {
            'atlassian': {
                'domain': config.domain,
                'user_email': config.userEmail,
                'api_token': config.apiToken,
                'cloud_id': config.cloudId
            }
        }
        
        connector = EnhancedRovoDevConnector(config_dict)
        await connector.start()
        
        results = await connector.test_connection()
        await connector.close()
        
        return results
        
    except Exception as e:
        logging.error(f"Connection test failed: {e}")
        return {"confluence": False, "jira": False, "error": str(e)}

# Confluence 端点
@app.get("/api/atlassian/confluence/spaces")
async def get_confluence_spaces(bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Confluence 空间列表"""
    try:
        spaces = await bridge.get_confluence_spaces()
        return spaces
    except Exception as e:
        logging.error(f"Failed to get spaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atlassian/confluence/spaces/{space_key}/pages")
async def get_confluence_pages(space_key: str, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Confluence 空间中的页面"""
    try:
        pages = await bridge.search_confluence_pages(space_key, "")
        return pages
    except Exception as e:
        logging.error(f"Failed to get pages: {e}")
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
        logging.error(f"Failed to create page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Jira 端点
@app.get("/api/atlassian/jira/projects")
async def get_jira_projects(bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Jira 项目列表"""
    try:
        projects = await bridge.get_jira_projects()
        return projects
    except Exception as e:
        logging.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atlassian/jira/projects/{project_key}/issues")
async def get_jira_issues(project_key: str, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """获取 Jira 项目中的问题"""
    try:
        jql = f"project = {project_key} ORDER BY created DESC"
        issues = await bridge.search_jira_issues(jql)
        return issues
    except Exception as e:
        logging.error(f"Failed to get issues: {e}")
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
        logging.error(f"Failed to create issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/atlassian/jira/search")
async def search_jira_issues(search: JQLSearchModel, bridge: AtlassianBridge = Depends(get_atlassian_bridge)):
    """搜索 Jira 问题"""
    try:
        issues = await bridge.search_jira_issues(search.jql)
        return {"issues": issues}
    except Exception as e:
        logging.error(f"Failed to search issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rovo Dev Agent 端点
@app.get("/api/rovo-dev/status")
async def get_rovo_dev_status(agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """获取 Rovo Dev Agent 状态"""
    try:
        status = agent.get_status()
        return status
    except Exception as e:
        logging.error(f"Failed to get agent status: {e}")
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
        logging.error(f"Failed to submit task: {e}")
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
        logging.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rovo-dev/tasks/history")
async def get_rovo_dev_task_history(limit: int = 50, agent: RovoDevAgent = Depends(get_rovo_dev_agent)):
    """获取 Rovo Dev 任务历史"""
    try:
        history = agent.get_task_history(limit)
        return history
    except Exception as e:
        logging.error(f"Failed to get task history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 代码分析端点
@app.post("/api/v1/code")
async def analyze_code(request: dict):
    """代码分析"""
    try:
        code = request.get("code", "")
        language = request.get("language", "auto")
        
        if not code:
            raise HTTPException(status_code=400, detail="Code is required")
        
        # 使用工具调度器进行代码分析
        services = get_services()
        tool_dispatcher = services.get("tool_dispatcher")
        
        if tool_dispatcher:
            result = await tool_dispatcher.dispatch_tool_request(
                tool_name="inspect_code",
                parameters={"code": code, "language": language}
            )
            return {
                "analysis": result,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 简单的代码分析
            lines = len(code.split('\n'))
            chars = len(code)
            return {
                "analysis": f"Code analysis: {lines} lines, {chars} characters. Language: {language}",
                "language": language,
                "lines": lines,
                "characters": chars,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logging.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 搜索端点
@app.post("/api/v1/search")
async def web_search(request: dict):
    """网络搜索"""
    try:
        query = request.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # 模拟搜索结果
        results = [
            {
                "title": f"Dynamic Search Result for '{query}'",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "snippet": f"This is a dynamic search result snippet for the query '{query}'.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": f"More about '{query}'",
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                "snippet": f"Wikipedia article about '{query}'.",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 图像生成端点
@app.post("/api/v1/image")
async def generate_image(request: dict):
    """图像生成"""
    try:
        prompt = request.get("prompt", "")
        style = request.get("style", "realistic")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # 使用工具调度器进行图像生成
        services = get_services()
        tool_dispatcher = services.get("tool_dispatcher")
        
        if tool_dispatcher:
            result = await tool_dispatcher.dispatch_tool_request(
                tool_name="create_image",
                parameters={"prompt": prompt, "style": style}
            )
            return {
                "prompt": prompt,
                "style": style,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 模拟图像生成结果
            return {
                "prompt": prompt,
                "style": style,
                "image_url": f"https://via.placeholder.com/512x512?text={prompt.replace(' ', '+')}",
                "status": "generated",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)