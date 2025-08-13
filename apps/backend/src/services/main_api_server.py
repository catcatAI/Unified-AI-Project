import uvicorn # For running the app
from fastapi import FastAPI, HTTPException, Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import uuid # For generating session IDs
import time # For system uptime calculations
from typing import List, Dict, Any, Optional # Updated from previous steps
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware

# Assuming src is in PYTHONPATH or this script is run from project root
# Adjust paths as necessary if running from within services directory directly for testing
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.services.api_models import UserInput, AIOutput, SessionStartRequest, SessionStartResponse, HSPTaskRequestInput, HSPTaskRequestOutput, HSPTaskStatusOutput, AtlassianConfigModel, ConfluencePageModel, JiraIssueModel, RovoDevTaskModel, JQLSearchModel # Added Atlassian models
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTask # Added HSPTask
from src.integrations.rovo_dev_agent import RovoDevAgent # Added RovoDevAgent
from src.integrations.atlassian_bridge import AtlassianBridge # Added AtlassianBridge
from src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

# 导入Atlassian CLI Bridge
try:
    from src.integrations.atlassian_cli_bridge import AtlassianCLIBridge
    ATLASSIAN_CLI_AVAILABLE = True
except ImportError as e:
    print(f"Atlassian CLI Bridge not available: {e}")
    AtlassianCLIBridge = None
    ATLASSIAN_CLI_AVAILABLE = False # Added RovoDevConnector


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

# --- Hot Reload / Drain endpoints (minimal, non-breaking) ---
from src.services.hot_reload_service import get_hot_reload_service

async def reject_if_draining():
    """Dependency to reject new task-creating requests while draining."""
    svc = get_hot_reload_service()
    st = await svc.status()
    if st.get("draining"):
        raise HTTPException(status_code=503, detail="Service is draining; try again later.")

hot_router = APIRouter(prefix="/api/v1/hot", tags=["hot-reload"])
@hot_router.post("/drain/start")
async def hot_drain_start():
    svc = get_hot_reload_service()
    return await svc.begin_draining()

@hot_router.post("/drain/stop")
async def hot_drain_stop():
    svc = get_hot_reload_service()
    return await svc.end_draining()

@hot_router.get("/status")
async def hot_status():
    svc = get_hot_reload_service()
    return await svc.status()

@hot_router.post("/reload/llm")
async def hot_reload_llm():
    svc = get_hot_reload_service()
    return await svc.reload_llm()

@hot_router.post("/reload/tools")
async def hot_reload_tools(tool: Optional[str] = None):
    """Reload tool implementations. Optionally specify a tool key to reload only one."""
    from src.core_services import tool_dispatcher_instance
    if tool_dispatcher_instance is None:
        raise HTTPException(status_code=500, detail="ToolDispatcher not initialized")
    try:
        summary = tool_dispatcher_instance.reload_tools(only=tool)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tools reload failed: {e}")

@hot_router.post("/reload/personality")
async def hot_reload_personality(profile: Optional[str] = None):
    svc = get_hot_reload_service()
    return await svc.reload_personality(profile)

@hot_router.post("/reload/hsp")
async def hot_reload_hsp():
    svc = get_hot_reload_service()
    return await svc.reload_hsp()

app.include_router(hot_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified AI Project API"}

# Atlassian CLI集成端点
@app.get("/api/v1/atlassian/status")
async def get_atlassian_status():
    """获取Atlassian CLI状态"""
    try:
        acli_bridge = AtlassianCLIBridge()
        status = acli_bridge.get_status()
        return status
    except Exception as e:
        logging.error(f"Atlassian status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/atlassian/jira/projects")
async def get_jira_projects():
    """获取Jira项目列表"""
    try:
        acli_bridge = AtlassianCLIBridge()
        result = acli_bridge.get_jira_projects()
        return result
    except Exception as e:
        logging.error(f"Get Jira projects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/atlassian/jira/issues")
async def get_jira_issues(jql: str = "", limit: int = 50):
    """获取Jira问题列表"""
    try:
        acli_bridge = AtlassianCLIBridge()
        result = acli_bridge.get_jira_issues(jql, limit)
        return result
    except Exception as e:
        logging.error(f"Get Jira issues failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/atlassian/jira/issue")
async def create_jira_issue(request: dict):
    """创建Jira问题"""
    try:
        project_key = request.get("project_key")
        summary = request.get("summary")
        description = request.get("description", "")
        issue_type = request.get("issue_type", "Task")
        priority = request.get("priority")
        labels_raw = request.get("labels")  # comma separated string or list
        labels_list = []
        if isinstance(labels_raw, str):
            labels_list = [x.strip() for x in labels_raw.split(",") if x.strip()]
        elif isinstance(labels_raw, list):
            labels_list = [str(x).strip() for x in labels_raw if str(x).strip()]
        
        if not project_key or not summary:
            raise HTTPException(status_code=400, detail="project_key and summary are required")
        
        acli_bridge = AtlassianCLIBridge()
        result = acli_bridge.create_jira_issue(project_key, summary, description, issue_type, priority=priority, labels=labels_list)
        return result
    except Exception as e:
        logging.error(f"Create Jira issue failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/atlassian/confluence/spaces")
async def get_confluence_spaces():
    """获取Confluence空间列表"""
    try:
        acli_bridge = AtlassianCLIBridge()
        result = acli_bridge.get_confluence_spaces()
        return result
    except Exception as e:
        logging.error(f"Get Confluence spaces failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/atlassian/confluence/search")
async def search_confluence_content(query: str, limit: int = 25):
    """搜索Confluence内容"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="query parameter is required")
        
        acli_bridge = AtlassianCLIBridge()
        result = acli_bridge.search_confluence_content(query, limit)
        return result
    except Exception as e:
        logging.error(f"Search Confluence content failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/openapi")
async def get_openapi_spec():
    return app.openapi()

# ==== Models/Router Endpoints (Phase 1) ====
from src.services.multi_llm_service import get_multi_llm_service
from src.core_ai.language_models.registry import ModelRegistry
from src.core_ai.language_models.router import PolicyRouter, RoutingPolicy

@app.get("/api/v1/models/available")
async def get_models_available():
    m = get_multi_llm_service()
    registry = ModelRegistry(m.model_configs)
    return {"models": registry.profiles_dict()}

@app.post("/api/v1/models/route")
async def models_route(body: dict):
    m = get_multi_llm_service()
    registry = ModelRegistry(m.model_configs)
    router = PolicyRouter(registry)
    policy = RoutingPolicy(
        task_type=body.get('task_type', 'general'),
        input_chars=body.get('input_chars', 0),
        needs_tools=body.get('needs_tools', False),
        needs_vision=body.get('needs_vision', False),
        latency_target=body.get('latency_target'),
        cost_ceiling=body.get('cost_ceiling')
    )
    return router.route(policy)

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


@app.get("/api/v1/system/services")
async def get_system_services():
    """获取所有系统服务的详细状态"""
    services = get_services()
    
    service_details = []
    
    # Core AI Services
    core_services = [
        ("llm_interface", "LLM Interface", "AI語言模型接口服務"),
        ("ham_manager", "HAM Memory Manager", "分層記憶管理系統"),
        ("personality_manager", "Personality Manager", "AI個性管理系統"),
        ("trust_manager", "Trust Manager", "信任評估系統"),
        ("hsp_connector", "HSP Connector", "HSP協議連接器"),
        ("service_discovery", "Service Discovery", "服務發現模組"),
        ("fact_extractor", "Fact Extractor", "事實提取模組"),
        ("content_analyzer", "Content Analyzer", "內容分析模組"),
        ("learning_manager", "Learning Manager", "學習管理系統"),
        ("emotion_system", "Emotion System", "情感系統"),
        ("crisis_system", "Crisis System", "危機處理系統"),
        ("time_system", "Time System", "時間管理系統"),
        ("formula_engine", "Formula Engine", "公式引擎"),
        ("tool_dispatcher", "Tool Dispatcher", "工具調度器"),
        ("dialogue_manager", "Dialogue Manager", "對話管理系統"),
        ("agent_manager", "Agent Manager", "代理管理系統"),
        ("ai_virtual_input_service", "AI Virtual Input", "AI虛擬輸入服務"),
        ("audio_service", "Audio Service", "音頻處理服務"),
        ("vision_service", "Vision Service", "視覺處理服務"),
        ("resource_awareness_service", "Resource Awareness", "資源感知服務")
    ]
    
    for service_key, service_name, description in core_services:
        service_instance = services.get(service_key)
        if service_instance:
            # Check if service has specific status methods
            status = "running"
            last_check = datetime.now().isoformat()
            
            # Special status checks for specific services
            if service_key == "hsp_connector" and hasattr(service_instance, 'is_connected'):
                status = "connected" if service_instance.is_connected else "disconnected"
            elif service_key == "agent_manager" and hasattr(service_instance, 'get_active_agents'):
                try:
                    active_agents = service_instance.get_active_agents()
                    status = f"running ({len(active_agents)} agents)"
                except:
                    status = "running"
            
            service_details.append({
                "id": service_key,
                "name": service_name,
                "description": description,
                "status": status,
                "lastCheck": last_check,
                "type": "core"
            })
        else:
            service_details.append({
                "id": service_key,
                "name": service_name,
                "description": description,
                "status": "not_initialized",
                "lastCheck": datetime.now().isoformat(),
                "type": "core"
            })
    
    return {
        "services": service_details,
        "timestamp": datetime.now().isoformat(),
        "total_services": len(service_details),
        "running_services": len([s for s in service_details if s["status"] not in ["not_initialized", "disconnected"]])
    }


@app.get("/api/v1/system/metrics/detailed")
async def get_detailed_system_metrics():
    """获取详细的系统性能指标"""
    import psutil
    import shutil
    import os
    from datetime import datetime
    
    try:
        # CPU 詳細信息
        cpu_info = {
            "usage_percent": round(psutil.cpu_percent(interval=1), 1),
            "core_count": psutil.cpu_count(logical=False),
            "logical_count": psutil.cpu_count(logical=True),
            "frequency": {
                "current": round(psutil.cpu_freq().current, 1) if psutil.cpu_freq() else 0,
                "min": round(psutil.cpu_freq().min, 1) if psutil.cpu_freq() else 0,
                "max": round(psutil.cpu_freq().max, 1) if psutil.cpu_freq() else 0
            },
            "per_core_usage": [round(x, 1) for x in psutil.cpu_percent(percpu=True)]
        }
        
        # 記憶體詳細信息
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "free_gb": round(memory.free / (1024**3), 2),
            "percent": round(memory.percent, 1),
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percent": round(swap.percent, 1)
            }
        }
        
        # 磁碟詳細信息
        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": round((usage.used / usage.total) * 100, 1)
                })
            except PermissionError:
                continue
        
        # 網路詳細信息
        network_io = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network_io.bytes_sent,
            "bytes_recv": network_io.bytes_recv,
            "packets_sent": network_io.packets_sent,
            "packets_recv": network_io.packets_recv,
            "errin": network_io.errin,
            "errout": network_io.errout,
            "dropin": network_io.dropin,
            "dropout": network_io.dropout
        }
        
        # 進程信息
        process_info = {
            "total_processes": len(psutil.pids()),
            "running_processes": len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_RUNNING]),
            "sleeping_processes": len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_SLEEPING])
        }
        
        # 系統溫度（如果可用）
        temperature_info = {}
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    temperature_info[name] = [{
                        "label": entry.label or "Unknown",
                        "current": entry.current,
                        "high": entry.high,
                        "critical": entry.critical
                    } for entry in entries]
        except:
            temperature_info = {"note": "Temperature sensors not available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
            "processes": process_info,
            "temperature": temperature_info,
            "uptime_seconds": round(time.time() - psutil.boot_time(), 1)
        }
        
    except Exception as e:
        logging.error(f"Error getting detailed system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@app.get("/api/v1/agents")
async def get_agents():
    """获取所有AI代理的状态"""
    services = get_services()
    agent_manager = services.get("agent_manager")
    
    if not agent_manager:
        return {
            "agents": [],
            "timestamp": datetime.now().isoformat(),
            "total_agents": 0,
            "active_agents": 0
        }
    
    try:
        # Get active agents if method exists
        active_agents = []
        if hasattr(agent_manager, 'get_active_agents'):
            active_agents = agent_manager.get_active_agents()
        
        # Create agent list with mock data for demonstration
        agents = [
            {
                "id": "dialogue_agent",
                "name": "對話代理",
                "type": "dialogue",
                "status": "active" if "dialogue_agent" in [a.get('id', '') for a in active_agents] else "idle",
                "lastActivity": datetime.now().isoformat(),
                "capabilities": ["natural_language", "conversation", "context_awareness"],
                "performance": {
                    "responseTime": 1.2,
                    "accuracy": 0.95,
                    "uptime": 99.8
                }
            },
            {
                "id": "code_agent",
                "name": "代碼分析代理",
                "type": "code_analysis",
                "status": "active" if "code_agent" in [a.get('id', '') for a in active_agents] else "idle",
                "lastActivity": datetime.now().isoformat(),
                "capabilities": ["code_analysis", "debugging", "optimization"],
                "performance": {
                    "responseTime": 2.1,
                    "accuracy": 0.92,
                    "uptime": 98.5
                }
            },
            {
                "id": "vision_agent",
                "name": "視覺處理代理",
                "type": "vision",
                "status": "active" if services.get("vision_service") else "inactive",
                "lastActivity": datetime.now().isoformat(),
                "capabilities": ["image_analysis", "object_detection", "ocr"],
                "performance": {
                    "responseTime": 3.5,
                    "accuracy": 0.89,
                    "uptime": 97.2
                }
            },
            {
                "id": "audio_agent",
                "name": "音頻處理代理",
                "type": "audio",
                "status": "active" if services.get("audio_service") else "inactive",
                "lastActivity": datetime.now().isoformat(),
                "capabilities": ["speech_recognition", "audio_analysis", "tts"],
                "performance": {
                    "responseTime": 2.8,
                    "accuracy": 0.91,
                    "uptime": 96.8
                }
            }
        ]
        
        active_count = len([a for a in agents if a["status"] == "active"])
        
        return {
            "agents": agents,
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(agents),
            "active_agents": active_count
        }
        
    except Exception as e:
        logging.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")


@app.get("/api/v1/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """获取特定AI代理的详细信息"""
    services = get_services()
    agent_manager = services.get("agent_manager")
    
    # Mock agent details based on agent_id
    agent_details = {
        "dialogue_agent": {
            "id": "dialogue_agent",
            "name": "對話代理",
            "type": "dialogue",
            "status": "active",
            "version": "2.1.0",
            "created": "2024-01-15T10:30:00Z",
            "lastActivity": datetime.now().isoformat(),
            "capabilities": ["natural_language", "conversation", "context_awareness"],
            "configuration": {
                "max_context_length": 4096,
                "temperature": 0.7,
                "response_timeout": 30
            },
            "performance": {
                "responseTime": 1.2,
                "accuracy": 0.95,
                "uptime": 99.8,
                "totalRequests": 15420,
                "successfulRequests": 14649,
                "failedRequests": 771
            },
            "resources": {
                "memoryUsage": 512.5,
                "cpuUsage": 15.2,
                "networkIO": 1024.8
            }
        },
        "code_agent": {
            "id": "code_agent",
            "name": "代碼分析代理",
            "type": "code_analysis",
            "status": "active",
            "version": "1.8.3",
            "created": "2024-01-10T14:20:00Z",
            "lastActivity": datetime.now().isoformat(),
            "capabilities": ["code_analysis", "debugging", "optimization"],
            "configuration": {
                "supported_languages": ["python", "javascript", "typescript", "java"],
                "max_file_size": 10485760,
                "analysis_depth": "deep"
            },
            "performance": {
                "responseTime": 2.1,
                "accuracy": 0.92,
                "uptime": 98.5,
                "totalRequests": 8932,
                "successfulRequests": 8214,
                "failedRequests": 718
            },
            "resources": {
                "memoryUsage": 1024.2,
                "cpuUsage": 25.8,
                "networkIO": 512.4
            }
        }
    }
    
    if agent_id not in agent_details:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent_details[agent_id]


@app.post("/api/v1/agents/{agent_id}/action")
async def perform_agent_action(agent_id: str, action: dict):
    """对AI代理执行操作（启动、停止、重启等）"""
    services = get_services()
    agent_manager = services.get("agent_manager")
    
    action_type = action.get("type")
    if not action_type:
        raise HTTPException(status_code=400, detail="Action type is required")
    
    # Validate agent exists
    valid_agents = ["dialogue_agent", "code_agent", "vision_agent", "audio_agent"]
    if agent_id not in valid_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Simulate action execution
    if action_type == "start":
        result = {"status": "success", "message": f"Agent {agent_id} started successfully"}
    elif action_type == "stop":
        result = {"status": "success", "message": f"Agent {agent_id} stopped successfully"}
    elif action_type == "restart":
        result = {"status": "success", "message": f"Agent {agent_id} restarted successfully"}
    elif action_type == "configure":
        config = action.get("config", {})
        result = {"status": "success", "message": f"Agent {agent_id} configuration updated", "config": config}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
    
    return {
        "agentId": agent_id,
        "action": action_type,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/models")
async def get_neural_network_models():
    """获取所有神经网络模型的状态"""
    services = get_services()
    tool_dispatcher = services.get("tool_dispatcher")
    
    # Mock neural network models data
    models = [
        {
            "id": "gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "type": "language_model",
            "status": "active",
            "version": "2024.1",
            "provider": "OpenAI",
            "lastUsed": datetime.now().isoformat(),
            "performance": {
                "averageResponseTime": 2.1,
                "tokensPerSecond": 45.2,
                "accuracy": 0.94,
                "uptime": 99.5
            },
            "usage": {
                "totalRequests": 12450,
                "successfulRequests": 11728,
                "failedRequests": 722,
                "totalTokens": 2847392
            },
            "configuration": {
                "maxTokens": 4096,
                "temperature": 0.7,
                "topP": 0.9
            }
        },
        {
            "id": "claude-3-sonnet",
            "name": "Claude 3 Sonnet",
            "type": "language_model",
            "status": "active",
            "version": "3.0",
            "provider": "Anthropic",
            "lastUsed": datetime.now().isoformat(),
            "performance": {
                "averageResponseTime": 1.8,
                "tokensPerSecond": 52.1,
                "accuracy": 0.92,
                "uptime": 98.8
            },
            "usage": {
                "totalRequests": 8932,
                "successfulRequests": 8456,
                "failedRequests": 476,
                "totalTokens": 1923847
            },
            "configuration": {
                "maxTokens": 4096,
                "temperature": 0.7,
                "topP": 0.9
            }
        },
        {
            "id": "vision-transformer",
            "name": "Vision Transformer",
            "type": "vision_model",
            "status": "active" if services.get("vision_service") else "inactive",
            "version": "1.2.0",
            "provider": "Custom",
            "lastUsed": datetime.now().isoformat(),
            "performance": {
                "averageResponseTime": 3.2,
                "imagesPerSecond": 12.5,
                "accuracy": 0.89,
                "uptime": 97.2
            },
            "usage": {
                "totalRequests": 3421,
                "successfulRequests": 3045,
                "failedRequests": 376,
                "totalImages": 3421
            },
            "configuration": {
                "inputSize": "224x224",
                "batchSize": 32,
                "precision": "fp16"
            }
        },
        {
            "id": "whisper-large",
            "name": "Whisper Large",
            "type": "audio_model",
            "status": "active" if services.get("audio_service") else "inactive",
            "version": "3.0",
            "provider": "OpenAI",
            "lastUsed": datetime.now().isoformat(),
            "performance": {
                "averageResponseTime": 4.1,
                "audioMinutesPerSecond": 2.8,
                "accuracy": 0.91,
                "uptime": 96.8
            },
            "usage": {
                "totalRequests": 1847,
                "successfulRequests": 1682,
                "failedRequests": 165,
                "totalAudioMinutes": 5234.7
            },
            "configuration": {
                "language": "auto",
                "task": "transcribe",
                "temperature": 0.0
            }
        }
    ]
    
    active_models = len([m for m in models if m["status"] == "active"])
    
    return {
        "models": models,
        "timestamp": datetime.now().isoformat(),
        "total_models": len(models),
        "active_models": active_models
    }


@app.get("/api/v1/models/{model_id}/metrics")
async def get_model_metrics(model_id: str):
    """获取特定模型的详细性能指标"""
    import random
    from datetime import datetime, timedelta
    
    # Generate mock time series data for the last 24 hours
    now = datetime.now()
    time_points = []
    response_times = []
    throughput = []
    accuracy = []
    error_rates = []
    
    for i in range(24):
        time_point = now - timedelta(hours=23-i)
        time_points.append(time_point.isoformat())
        
        # Generate realistic mock data with some variation
        base_response_time = 2.0 if "gpt" in model_id else 1.8
        response_times.append(round(base_response_time + random.uniform(-0.5, 0.5), 2))
        
        base_throughput = 45.0 if "gpt" in model_id else 52.0
        throughput.append(round(base_throughput + random.uniform(-10, 10), 1))
        
        base_accuracy = 0.94 if "gpt" in model_id else 0.92
        accuracy.append(round(base_accuracy + random.uniform(-0.02, 0.02), 3))
        
        error_rates.append(round(random.uniform(0.01, 0.05), 3))
    
    # Model-specific metrics
    model_metrics = {
        "gpt-4-turbo": {
            "modelId": model_id,
            "timeRange": "24h",
            "metrics": {
                "responseTime": {
                    "current": response_times[-1],
                    "average": round(sum(response_times) / len(response_times), 2),
                    "min": min(response_times),
                    "max": max(response_times),
                    "timeSeries": list(zip(time_points, response_times))
                },
                "throughput": {
                    "current": throughput[-1],
                    "average": round(sum(throughput) / len(throughput), 1),
                    "min": min(throughput),
                    "max": max(throughput),
                    "timeSeries": list(zip(time_points, throughput))
                },
                "accuracy": {
                    "current": accuracy[-1],
                    "average": round(sum(accuracy) / len(accuracy), 3),
                    "min": min(accuracy),
                    "max": max(accuracy),
                    "timeSeries": list(zip(time_points, accuracy))
                },
                "errorRate": {
                    "current": error_rates[-1],
                    "average": round(sum(error_rates) / len(error_rates), 3),
                    "min": min(error_rates),
                    "max": max(error_rates),
                    "timeSeries": list(zip(time_points, error_rates))
                }
            },
            "resourceUsage": {
                "gpuUtilization": round(random.uniform(60, 85), 1),
                "memoryUsage": round(random.uniform(8, 12), 1),
                "powerConsumption": round(random.uniform(200, 300), 1)
            },
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Return default metrics if model not found
    if model_id not in model_metrics:
        return {
            "modelId": model_id,
            "timeRange": "24h",
            "metrics": {
                "responseTime": {"current": 0, "average": 0, "timeSeries": []},
                "throughput": {"current": 0, "average": 0, "timeSeries": []},
                "accuracy": {"current": 0, "average": 0, "timeSeries": []},
                "errorRate": {"current": 0, "average": 0, "timeSeries": []}
            },
            "resourceUsage": {"gpuUtilization": 0, "memoryUsage": 0, "powerConsumption": 0},
            "timestamp": datetime.now().isoformat()
        }
    
    return model_metrics[model_id]


@app.get("/api/v1/models/{model_id}/training")
async def get_model_training_status(model_id: str):
    """获取模型训练状态和历史"""
    import random
    from datetime import datetime, timedelta
    
    # Mock training data
    training_sessions = [
        {
            "id": "train_001",
            "startTime": (datetime.now() - timedelta(days=7)).isoformat(),
            "endTime": (datetime.now() - timedelta(days=6, hours=18)).isoformat(),
            "status": "completed",
            "dataset": "custom_dataset_v2",
            "epochs": 10,
            "batchSize": 32,
            "learningRate": 0.001,
            "finalLoss": 0.0234,
            "finalAccuracy": 0.945,
            "duration": "6h 12m"
        },
        {
            "id": "train_002",
            "startTime": (datetime.now() - timedelta(days=3)).isoformat(),
            "endTime": None,
            "status": "running",
            "dataset": "custom_dataset_v3",
            "epochs": 15,
            "batchSize": 64,
            "learningRate": 0.0005,
            "currentEpoch": 8,
            "currentLoss": 0.0189,
            "currentAccuracy": 0.952,
            "estimatedTimeRemaining": "2h 45m"
        }
    ]
    
    # Generate loss and accuracy curves for current training
    current_training = next((t for t in training_sessions if t["status"] == "running"), None)
    loss_curve = []
    accuracy_curve = []
    
    if current_training:
        for epoch in range(1, current_training["currentEpoch"] + 1):
            # Simulate decreasing loss and increasing accuracy
            loss = 0.1 * (1 / epoch) + random.uniform(-0.005, 0.005)
            acc = 0.8 + (0.15 * (1 - 1/epoch)) + random.uniform(-0.01, 0.01)
            loss_curve.append({"epoch": epoch, "loss": round(loss, 4)})
            accuracy_curve.append({"epoch": epoch, "accuracy": round(acc, 3)})
    
    return {
        "modelId": model_id,
        "currentTraining": current_training,
        "trainingHistory": training_sessions,
        "curves": {
            "loss": loss_curve,
            "accuracy": accuracy_curve
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/images/history")
async def get_image_generation_history():
    """获取图像生成历史记录"""
    import random
    from datetime import datetime, timedelta
    
    # Mock image generation history
    history = []
    
    # Generate mock history for the last 30 days
    for i in range(50):  # 50 recent generations
        created_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        prompts = [
            "A futuristic cityscape with flying cars",
            "Abstract art with vibrant colors",
            "Portrait of a robot in Renaissance style",
            "Landscape with mountains and aurora",
            "Steampunk mechanical device",
            "Underwater scene with coral reef",
            "Space station orbiting Earth",
            "Medieval castle in the clouds",
            "Cyberpunk street scene at night",
            "Fantasy forest with magical creatures"
        ]
        
        styles = ["realistic", "artistic", "cartoon", "photographic", "digital_art"]
        statuses = ["completed", "completed", "completed", "failed", "processing"]
        
        image_entry = {
            "id": f"img_{1000 + i}",
            "prompt": random.choice(prompts),
            "style": random.choice(styles),
            "model": random.choice(["dall-e-3", "midjourney", "stable-diffusion"]),
            "status": random.choice(statuses),
            "createdAt": created_time.isoformat(),
            "completedAt": (created_time + timedelta(seconds=random.randint(10, 120))).isoformat() if random.choice(statuses) == "completed" else None,
            "imageUrl": f"https://picsum.photos/512/512?random={i}" if random.choice(statuses) == "completed" else None,
            "thumbnailUrl": f"https://picsum.photos/256/256?random={i}" if random.choice(statuses) == "completed" else None,
            "parameters": {
                "width": 512,
                "height": 512,
                "steps": random.randint(20, 50),
                "guidance": round(random.uniform(7.0, 15.0), 1),
                "seed": random.randint(1000000, 9999999)
            },
            "metadata": {
                "fileSize": random.randint(500000, 2000000),  # bytes
                "format": "PNG",
                "generationTime": round(random.uniform(5.0, 30.0), 1)  # seconds
            }
        }
        
        history.append(image_entry)
    
    # Sort by creation time (newest first)
    history.sort(key=lambda x: x["createdAt"], reverse=True)
    
    # Calculate statistics
    total_images = len(history)
    completed_images = len([img for img in history if img["status"] == "completed"])
    failed_images = len([img for img in history if img["status"] == "failed"])
    processing_images = len([img for img in history if img["status"] == "processing"])
    
    return {
        "images": history,
        "statistics": {
            "total": total_images,
            "completed": completed_images,
            "failed": failed_images,
            "processing": processing_images,
            "successRate": round((completed_images / total_images) * 100, 1) if total_images > 0 else 0
        },
        "timestamp": datetime.now().isoformat()
    }


@app.delete("/api/v1/images/{image_id}")
async def delete_generated_image(image_id: str):
    """删除生成的图像"""
    # In a real implementation, this would:
    # 1. Verify the image exists and belongs to the user
    # 2. Delete the image file from storage
    # 3. Remove the record from the database
    
    # Mock deletion
    if not image_id.startswith("img_"):
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    
    return {
        "success": True,
        "message": f"Image {image_id} deleted successfully",
        "imageId": image_id,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/images/batch-delete")
async def batch_delete_images(image_ids: list[str]):
    """批量删除生成的图像"""
    if not image_ids:
        raise HTTPException(status_code=400, detail="No image IDs provided")
    
    # Mock batch deletion
    deleted_ids = []
    failed_ids = []
    
    for image_id in image_ids:
        if image_id.startswith("img_"):
            deleted_ids.append(image_id)
        else:
            failed_ids.append(image_id)
    
    return {
        "success": len(failed_ids) == 0,
        "deletedCount": len(deleted_ids),
        "failedCount": len(failed_ids),
        "deletedIds": deleted_ids,
        "failedIds": failed_ids,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/images/statistics")
async def get_image_generation_statistics():
    """获取图像生成统计信息"""
    import random
    from datetime import datetime, timedelta
    
    # Mock statistics for the last 30 days
    daily_stats = []
    
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        daily_count = random.randint(0, 15)
        
        daily_stats.append({
            "date": date.strftime("%Y-%m-%d"),
            "generated": daily_count,
            "completed": random.randint(int(daily_count * 0.7), daily_count),
            "failed": random.randint(0, int(daily_count * 0.3))
        })
    
    # Model usage statistics
    model_stats = [
        {"model": "dall-e-3", "count": 156, "percentage": 45.2},
        {"model": "stable-diffusion", "count": 134, "percentage": 38.8},
        {"model": "midjourney", "count": 55, "percentage": 16.0}
    ]
    
    # Style distribution
    style_stats = [
        {"style": "realistic", "count": 98, "percentage": 28.4},
        {"style": "artistic", "count": 87, "percentage": 25.2},
        {"style": "digital_art", "count": 76, "percentage": 22.0},
        {"style": "photographic", "count": 54, "percentage": 15.7},
        {"style": "cartoon", "count": 30, "percentage": 8.7}
    ]
    
    return {
        "dailyGeneration": daily_stats,
        "modelUsage": model_stats,
        "styleDistribution": style_stats,
        "totalGenerated": sum(stat["count"] for stat in model_stats),
        "averageGenerationTime": 18.5,  # seconds
        "timestamp": datetime.now().isoformat()
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
async def start_session_endpoint(session_start_request: SessionStartRequest, _=Depends(reject_if_draining)):
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
async def request_hsp_task(task_input: HSPTaskRequestInput, _=Depends(reject_if_draining)):
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
        # Handle both 'code' and 'query' parameters for flexibility
        code = request.get("code") or request.get("query", "")
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