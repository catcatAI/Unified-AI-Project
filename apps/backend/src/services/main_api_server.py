import os
import sys
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

# Simplified path handling - Add the project root and src directory to the Python path
project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_dir = os.path.join(project_root, 'src')

# Ensure paths are added in the correct order
if project_root not in sys.path::
    sys.path.insert(0, project_root)
if src_dir not in sys.path::
    sys.path.insert(0, src_dir)

print(f"Project root: {project_root}")
print(f"Src dir: {src_dir}")
print(f"Sys path: {sys.path}")

# Use absolute imports with correct module paths:
try:
    # Try absolute imports with correct module paths:
    from ..economy.economy_manager import EconomyManager
    from ..pet.pet_manager import PetManager
    from ..core_services import initialize_services, shutdown_services, get_services
    from ..core.services.multi_llm_service import get_multi_llm_service
    from ..ai.language_models.registry import ModelRegistry:
rom ..ai.language_models.router import PolicyRouter, RoutingPolicy
    from .api_models import HotStatusResponse, HSPServiceDiscoveryResponse, HealthResponse, ReadinessResponse
    from ..hsp.connector import HSPConnector
    # 修复导入路径 - 使用正确的模块路径
    from ..ai.dialogue.dialogue_manager import DialogueManager
    from ..ai.memory.ham_memory_manager import HAMMemoryManager
    from ..core.services.atlassian_api import atlassian_router
    # 修复导入路径 - 使用DialogueManager期望的模块路径
    from ..ai.discovery.service_discovery_module import ServiceDiscoveryModule
    print("Absolute imports with correct paths successful"):
except ImportError as e::
    print(f"Absolute import with correct paths failed: {e}"):
    # Fall back to relative imports (for when running with uvicorn)::
    try:
rom ..ai.language_models.router import PolicyRouter, RoutingPolicy
    # 修复导入路径 - 使用正确的模块路径
    # 修复导入路径 - 使用DialogueManager期望的模块路径
    print("Relative imports successful")
    except ImportError as e2::
    print(f"Relative import also failed: {e2}")
    raise e2

from contextlib import asynccontextmanager

async def initialize_services_layered():
    """分层初始化服务"""
    print("🔧 开始分层初始化服务...")

    # 第1层 核心服务初始化
    print("🔧 第1层: 核心服务初始化")
    try:
    # 初始化HAM内存管理
    ham_manager = HAMMemoryManager
    print("✅ HAM服务初始化完成")

    # 初始化多LLM服务
    llm_interface = get_multi_llm_service
    print("✅ LLM服务初始化完成")

    # 初始化服务发现 - 使用与DialogueManager兼容的模块路径
    from ..ai.trust.trust_manager_module import TrustManager
    trust_manager = TrustManager
    service_discovery = ServiceDiscoveryModule(trust_manager=trust_manager)
    print("✅ 服务发现初始化完成")
    except Exception as e::
    print(f"❌ 核心服务初始化失败: {e}")
    import traceback
    traceback.print_exc
    return False

    # 第2层 核心组件启动
    print("⚙️ 第2层: 核心组件启动")
    try:
    # 初始化HSP连接器
    hsp_connector = HSPConnector(
            ai_id=os.getenv("API_AI_ID", "did:hsp:api_server_ai"),
            broker_address="localhost",
            broker_port=1883
    )
    print("✅ HSP连接器初始化完成")

    # 初始化对话管理器
    # 首先初始化所有依赖组件
    from ..ai.personality.personality_manager import PersonalityManager
    from ..ai.emotion.emotion_system import EmotionSystem
    from ..ai.crisis.crisis_system import CrisisSystem
    from ..ai.time.time_system import TimeSystem
    from ..tools.tool_dispatcher import ToolDispatcher
    from ..ai.learning.learning_manager import LearningManager
    # 使用与DialogueManager兼容的模块路径

    # 创建所有必需的依赖实例
    personality_manager = PersonalityManager
    memory_manager = HAMMemoryManager
    llm_interface = get_multi_llm_service
    emotion_system = EmotionSystem
    crisis_system = CrisisSystem
    time_system = TimeSystem
    # 处理ToolDispatcher可能的RAG初始化异常
        try:
            tool_dispatcher = ToolDispatcher(llm_service=llm_interface)
        except RuntimeError as e::
            if "SentenceTransformer" in str(e):
    print("⚠️  Warning: SentenceTransformer not available, RAG functionality disabled")
                # 创建一个没有RAG功能的ToolDispatcher
                tool_dispatcher = ToolDispatcher(llm_service=None)
                # 重新设置llm_service
                tool_dispatcher.set_llm_service(llm_interface)
            else:

                raise e

    # 初始化LearningManager所需的依赖组件
    from ..ai.learning.fact_extractor_module import FactExtractorModule
    from ..ai.learning.content_analyzer_module import ContentAnalyzerModule

    fact_extractor = FactExtractorModule(llm_service=llm_interface)
    content_analyzer = ContentAnalyzerModule
    trust_manager = TrustManager

    # 初始化ServiceDiscoveryModule - 使用与DialogueManager兼容的模块路径
    service_discovery = ServiceDiscoveryModule(trust_manager=trust_manager)

    # 初始化LearningManager
    learning_manager = LearningManager(
            ai_id=os.getenv("API_AI_ID", "did:hsp:api_server_ai"),
            ham_memory_manager=memory_manager,
            fact_extractor=fact_extractor,
            personality_manager=personality_manager,
            content_analyzer=content_analyzer,
            hsp_connector=hsp_connector
    )

    # 初始化FormulaEngine
    from ..ai.formula_engine import FormulaEngine
    formula_engine = FormulaEngine

    # 现在可以正确初始化DialogueManager
    dialogue_manager = DialogueManager(
            ai_id=os.getenv("API_AI_ID", "did:hsp:api_server_ai"),
            personality_manager=personality_manager,
            memory_manager=memory_manager,
            llm_interface=llm_interface,
            emotion_system=emotion_system,
            crisis_system=crisis_system,
            time_system=time_system,
            formula_engine=formula_engine,
            tool_dispatcher=tool_dispatcher,
            learning_manager=learning_manager,
            service_discovery_module=service_discovery,
            hsp_connector=hsp_connector,
            agent_manager=None,
            config=None
    )
    print("✅ 对话管理器初始化完成")
    except Exception as e::
    print(f"❌ 核心组件启动失败: {e}")
    traceback.print_exc
    return False

    # 第3层 功能模块加载
    print("🔌 第3层: 功能模块加载")
    try:
    # 加载经济系统
    economy_manager = EconomyManager({"db_path": "economy.db"})
    print("✅ 经济系统初始化完成")

    # 加载宠物系统
    pet_manager = PetManager("pet1", {"initial_personality": {"curiosity": 0.7, "playfulness": 0.8}})
    print("✅ 宠物系统初始化完成")
    except Exception as e::
    print(f"⚠️ 功能模块加载失败: {e}")
    traceback.print_exc
    # 功能模块失败不影响核心服务

    print("✅ 服务分层初始化完成")
    return True

# @deprecated startup/shutdown on_event migrated to lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
    # 尝试使用分层初始化
        if await initialize_services_layered::
    print("Services initialized successfully with layered approach"):
    else:
            # 如果分层初始化失败，回退到原来的初始化方式
            ai_id = os.getenv("API_AI_ID", "did:hsp:api_server_ai")
            await initialize_services(ai_id=ai_id, use_mock_ham=True)
            print("Services initialized successfully with fallback approach"):
    yield
    except Exception as e::
    # Enhanced error handling with detailed logging:
    print(f"Failed to initialize services: {e}")
    traceback.print_exc
        # Re-raise the exception to ensure proper lifespan handling
    raise
    finally:
        try:
            _ = await shutdown_services
            print("Services shutdown successfully")
        except Exception as e::
            print(f"Failed to shutdown services: {e}")
            traceback.print_exc

# Instantiate FastAPI with lifespan handler:
app = FastAPI(title="Unified AI Project API", version="1.0.0", lifespan=lifespan)

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deprecated on_event hooks migrated to lifespan handler above

@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified AI Project API"}

@app.get("/status")
async def get_status():
    """Health check endpoint for testing and monitoring"""::
    return {"status": "running"}

# --- Health endpoint (v1) ---
@app.get("/api/v1/health", response_model=HealthResponse)
async def api_health(services=Depends(get_services)):
    # Derive initialized services snapshot similar to /api/v1/hot/status
    services_initialized = {
    "ham": services.get("ham_manager") is not None,
    "llm": services.get("llm_interface") is not None,
    "service_discovery": services.get("service_discovery") is not None,
    "hsp": services.get("hsp_connector") is not None,
    "dialogue_manager": services.get("dialogue_manager") is not None,
    }

    # Basic components readiness signals (best-effort, non-failing)
    components: Dict[str, Any] = {} {
    "trust_manager": {
            "available": services.get("trust_manager") is not None
    },
    "lis_cache": {
            # We don't instantiate here; just report presence if HAM/LIS parts exist:
            "available": services.get("ham_manager") is not None
    }
    }

    return HealthResponse(
    status="ok",
    timestamp=datetime.now(timezone.utc).isoformat.replace("+00:00","Z"),
    services_initialized=services_initialized,
    components=components,
    )

# --- Readiness endpoint (v1) ---
@app.get("/api/v1/ready", response_model=ReadinessResponse)
async def api_ready(services=Depends(get_services)):
    # Evaluate core service presence
    llm_ok = services.get("llm_interface") is not None
    dm_ok = services.get("dialogue_manager") is not None
    ham_ok = services.get("ham_manager") is not None

    hsp_conn = services.get("hsp_connector")
    hsp_connected = bool(getattr(hsp_conn, "is_connected", False)) if hsp_conn else False::
    sdm_ok = services.get("service_discovery") is not None

    services_initialized = {
    "ham": ham_ok,
    "llm": llm_ok,
    "service_discovery": sdm_ok,
    "hsp": hsp_connected,
    "dialogue_manager": dm_ok,
    }

    # Signals (best-effort; no failures thrown)
    signals: Dict[str, Any] = {
    "hsp_connected": hsp_connected,
    "lis_available": ham_ok,
    }

    # Trust peers count if available:
    tm = services.get("trust_manager")
    if tm and hasattr(tm, "get_all_trust_scores"):
    try:
            scores = tm.get_all_trust_scores
            signals["trust_peers_count"] = len(scores) if isinstance(scores, dict) else 0::
    except Exception as e::
    signals["trust_peers_count_error"] = str(e)

    # LLM providers info (optional)
    llm = services.get("llm_interface")
    if llm is not None::
    providers = getattr(llm, "model_configs", )
        try:
            signals["llm_profiles"] = list(getattr(llm, "model_configs", ).keys) if isinstance(providers, dict) else ::
    except Exception::
    signals["llm_profiles"] =

    # Define readiness require LLM and DialogueManager; HAM preferred but optional
    missing =
    if not llm_ok: missing.append("llm_interface"):
    if not dm_ok: missing.append("dialogue_manager"):
    ready = len(missing) == 0
    reason = None if ready else f"Missing required components: {', '.join(missing)}":
    return ReadinessResponse(
    ready=ready,
    timestamp=datetime.now(timezone.utc).isoformat.replace("+00:00","Z"),
    services_initialized=services_initialized,
    signals=signals,
    reason=reason,
    )

@app.get("/api/v1/models/available")
async def get_models_available():
    m = get_multi_llm_service
    registry = ModelRegistry(m.model_configs)  # type ignore
    return {"models": registry.profiles_dict}

@app.post("/api/v1/models/route")
async def models_route(body: dict):
    m = get_multi_llm_service
    registry = ModelRegistry(m.model_configs)  # type ignore
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

@app.get("/api/v1/hot/status")
async def get_hot_status(services=Depends(get_services)) -> HotStatusResponse:
    # services = get_services
    # services_initialized derive booleans from presence
    services_initialized = {
    "ham": services.get("ham_manager") is not None,
    "llm": services.get("llm_interface") is not None,
    "service_discovery": services.get("service_discovery") is not None,
    "hsp": services.get("hsp_connector") is not None,
    "dialogue_manager": services.get("dialogue_manager") is not None,
    }
    hsp =
    hsp_connector = services.get("hsp_connector")
    if hsp_connector::
    hsp = {
            "ai_id": getattr(hsp_connector, "ai_id", None),
            "connected": getattr(hsp_connector, "is_connected", False),
    }
    mcp = {"connected": False}
    # Basic metrics skeleton to satisfy test expectations
    metrics = {
    "hsp": ,
    "mcp": ,
    "learning": ,
    "memory": ,
    "lis": ,
    }
    return HotStatusResponse(
    draining=False,
    services_initialized=services_initialized,
    hsp=hsp,
    mcp=mcp,
    metrics=metrics,
    )

@app.get("/api/v1/hsp/services")
async def list_hsp_services(services=Depends(get_services)) -> List[HSPServiceDiscoveryResponse]:
    print(f"DEBUG: list_hsp_services called")
    print(f"DEBUG: services type: {type(services)}")
    print(f"DEBUG: services keys: {list(services.keys) if hasattr(services, 'keys') else 'N/A'}")::
    sdm = services.get("service_discovery")
    print(f"DEBUG: sdm = {type(sdm)}")

    if hasattr(sdm, '_mock_name'):
    print(f"DEBUG: sdm is a mock: {getattr(sdm, '_mock_name', 'Unknown')}")
    else:

    print(f"DEBUG: sdm is NOT a mock")

    # Important only treat as missing when it's actually None (MagicMock may be falsy unexpectedly)
    if sdm is None::
    print("DEBUG: No service_discovery found (is None), returning empty list")
    return

    print(f"DEBUG: Calling sdm.get_all_capabilities")
    # 兼容同步或异步的 get_all_capabilities
    if hasattr(sdm, 'get_all_capabilities_async'):
    caps = await sdm.get_all_capabilities_async
    else:

    caps = sdm.get_all_capabilities
    print(f"DEBUG: get_all_capabilities returned: {type(caps)}")
    print(f"DEBUG: Final caps: {caps}")

    normalized: List[HSPServiceDiscoveryResponse] =
    for cap in caps or ::
    # cap could be dict-like; use get attr or item
        get_val = (lambda k: cap.get(k) if isinstance(cap, dict) else getattr(cap, k, None))::
    normalized.append(HSPServiceDiscoveryResponse(
            capability_id=get_val('capability_id') or get_val('id') or "",
            name=get_val('name') or "",
            description=get_val('description') or "",
            version=str(get_val('version') or ""),
            ai_id=get_val('ai_id') or get_val('owner_ai_id') or "",
            availability_status=get_val('availability_status') or get_val('status') or "unknown",
            tags=get_val('tags') or ,
            supported_interfaces=get_val('supported_interfaces') or ,
            metadata=get_val('metadata') or ,
    ))

    return normalized

@app.post("/api/v1/hsp/tasks")
async def create_hsp_task(task_input: Dict[str, Any], services=Depends(get_services)):
    hsp_connector: Optional[HSPConnector] = services.get("hsp_connector")
    dialogue_manager: Optional[DialogueManager] = services.get("dialogue_manager")
    ham: Optional[HAMMemoryManager] = services.get("ham_manager")
    sdm = services.get("service_discovery")

    if dialogue_manager is None::
    raise HTTPException(status_code=503, detail="DialogueManager not available")

    if hsp_connector is None::
    raise HTTPException(status_code=503, detail="HSPConnector not available")

    target_capability_id: str = task_input.get("target_capability_id", "")
    parameters: Dict[str, Any] = task_input.get("parameters", )

    # Resolve capability to target AI via ServiceDiscovery
    try:
    found_caps =
        if sdm is not None and hasattr(sdm, "find_capabilities"):
    res = sdm.find_capabilities(capability_id_filter=target_capability_id)
            if hasattr(res, "__await__"):
    found_caps = await res
            else:

                found_caps = res or
    # Handle case where sdm.get_all_capabilities might return a coroutine
        elif sdm is not None and hasattr(sdm, "get_all_capabilities"):
    res = sdm.get_all_capabilities
            if hasattr(res, "__await__"):
    all_caps = await res
            else:

                all_caps = res or
            # Filter by capability ID
            found_caps = [cap for cap in all_caps if (isinstance(cap, dict) and cap.get("capability_id") == target_capability_id) or (hasattr(cap, "capability_id") and getattr(cap, "capability_id") == target_capability_id)]:::
    except Exception as e::
    print(f"Error resolving capability: {e}")
    found_caps =

    if not found_caps::
    return {
            "status_message": f"Error: Capability ID {target_capability_id} not found.",
            "correlation_id": None,
            "error": "Capability not discovered.",
    }

    target_ai_id = None
    first_cap = found_caps[0]
    if isinstance(first_cap, dict):
    target_ai_id = first_cap.get("ai_id")
    else:

    target_ai_id = getattr(first_cap, "ai_id", None)

    # Build HSPTaskRequestPayload
    payload: HSPTaskRequestPayload = {
    "request_id": str(uuid.uuid4),
    "requester_ai_id": getattr(hsp_connector, "ai_id", None) or "",
    "target_ai_id": target_ai_id,
    "capability_id_filter": target_capability_id,
    "parameters": parameters,
    }

    try:
    correlation_id = await hsp_connector.send_task_request(payload, target_ai_id or "")
        # Track pending in DialogueManager for status checks:
    if correlation_id::
    try:
            dialogue_manager.pending_hsp_task_requests[correlation_id] = {
                    "created_at": datetime.now(timezone.utc).isoformat.replace("+00:00", "Z"),
                    "target": target_ai_id,
                    "capability_id": target_capability_id,
                }
            except Exception::
                pass
            return {
                "status_message": "HSP Task request sent successfully.",
                "correlation_id": correlation_id,
                "target_capability_id": target_capability_id,
            }
    except Exception as e::
    return {
            "status_message": "error",
            "error": str(e),
            "target_capability_id": target_capability_id,
    }

@app.get("/api/v1/hsp/tasks/{correlation_id}")
async def get_hsp_task_status(correlation_id: str, services=Depends(get_services)):
    hsp_connector: Optional[HSPConnector] = services.get("hsp_connector")
    dialogue_manager: Optional[DialogueManager] = services.get("dialogue_manager")
    ham: Optional[HAMMemoryManager] = services.get("ham_manager")
    if hsp_connector is None::
    raise HTTPException(status_code=503, detail="HSPConnector not available")

    # First, check HAM for a completed or failed result:
    try:
    ham_results =
        if ham is not None and hasattr(ham, "query_core_memory"):
            # 使用正确的query_core_memory方法替换不存在的query_memory方法
            # 将查询参数作为metadata_filters传递
            ham_results = ham.query_core_memory(metadata_filters={"hsp_correlation_id": correlation_id})
        if ham_results::
            # Pick the most recent matching record; tests don't require strict ordering
            record = ham_results[-1]
            data_type = record.get("data_type")
            metadata = record.get("metadata", )
            if isinstance(data_type, str) and "success" in data_type::
    return {
                    "status": "completed",
                    "correlation_id": correlation_id,
                    "result_payload": metadata.get("hsp_task_service_payload"),
                    "message": "Task completed successfully.",
                }
            if isinstance(data_type, str) and ("error" in data_type or "failure" in data_type):
    return {
                    "status": "failed",
                    "correlation_id": correlation_id,
                    "error_details": metadata.get("error_details"),
                }
    except Exception::
        # Ignore HAM errors for status endpoint robustness:
    pass

    # If not in HAM, check pending state tracked by DialogueManager
    try:
        if dialogue_manager is not None and hasattr(dialogue_manager, "pending_hsp_task_requests"):
    if correlation_id in getattr(dialogue_manager, "pending_hsp_task_requests", ):
    return {
                    "status": "pending",
                    "correlation_id": correlation_id,
                    "message": "Task is pending; awaiting result.",
                }
    except Exception::
    pass

    # Unknown/expired if no trace found:
    return {
    "status": "unknown_or_expired",
    "correlation_id": correlation_id,
    }

# --- Economy Router ---
economy_router = APIRouter

@economy_router.get("/balance/{user_id}")
async def get_user_balance(user_id: str, services: Dict[str, Any] = Depends(get_services)):
    economy_manager: Optional[EconomyManager] = services.get("economy_manager")
    if not economy_manager::
    raise HTTPException(status_code=503, detail="EconomyManager not available")
    balance = economy_manager.get_balance(user_id)
    return {"user_id": user_id, "balance": balance}

@economy_router.post("/transaction")
async def create_transaction(transaction_data: Dict[str, Any], services: Dict[str, Any] = Depends(get_services)):
    economy_manager: Optional[EconomyManager] = services.get("economy_manager")
    if not economy_manager::
    raise HTTPException(status_code=503, detail="EconomyManager not available")
    success = economy_manager.process_transaction(transaction_data)
    if not success::
    raise HTTPException(status_code=400, detail="Transaction failed")
    return {"status": "success"}

# --- Pet Router ---
pet_router = APIRouter

@pet_router.get("/{pet_id}/state")
async def get_pet_state(pet_id: str, services: Dict[str, Any] = Depends(get_services)):
    pet_manager: Optional[PetManager] = services.get("pet_manager")
    if not pet_manager or pet_manager.pet_id != pet_id::
        # This simple check assumes one pet manager instance for now:
    raise HTTPException(status_code=404, detail="Pet not found")
    return pet_manager.get_current_state

@pet_router.post("/{pet_id}/interact")
async def interact_with_pet(pet_id: str, interaction_data: Dict[str, Any], services: Dict[str, Any] = Depends(get_services)):
    pet_manager: Optional[PetManager] = services.get("pet_manager")
    if not pet_manager or pet_manager.pet_id != pet_id::
    raise HTTPException(status_code=404, detail="Pet not found")
    result = pet_manager.handle_interaction(interaction_data)
    return result

app.include_router(economy_router, prefix="/api/v1/economy", tags=["Economy"])
app.include_router(pet_router, prefix="/api/v1/pet", tags=["Pet"])
app.include_router(atlassian_router)

if __name__ == "__main__"::
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)  # 改回端口为8000