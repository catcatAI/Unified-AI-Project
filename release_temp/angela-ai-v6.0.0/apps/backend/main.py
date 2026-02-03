import logging
from typing import Any, Optional
import sys
import os
import asyncio
import datetime
import ray

# Initialize Ray (address="auto" connects to an existing Ray cluster or starts one if none is found)
# ignore_reinit_error=True is useful for development where main.py might be reloaded
ray.init(ignore_reinit_error=True)

# Add project root to sys.path to allow imports from 'apps' when running from subdirectories
# We use insert(0) to ensure this path takes precedence
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Configure logger
logger = logging.getLogger(__name__)

# Import manager classes and other components
# Import API routers
from apps.backend.src.api.v1.endpoints import chat as v1_chat_router
from apps.backend.src.api.v1.endpoints import llm as v1_llm_router
from apps.backend.src.api.v1.endpoints import pet as v1_pet_router
from apps.backend.src.api.v1.endpoints import economy as v1_economy_router
from apps.backend.src.api.v1.endpoints import tools as v1_tools_router
from apps.backend.src.api.v1.endpoints import orchestrator as v1_orchestrator_router
from apps.backend.src.core.error.error_handler import register_exception_handlers


# --- Lifespan function for startup and shutdown events ---
from contextlib import asynccontextmanager
# Import Actor clients
from apps.backend.src.ai.agent_manager import AgentManager # Client for AgentManagerActor
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager # Client for HAMMemoryManagerActor
from apps.backend.src.core.managers.system_manager import SystemManager # Client for SystemManagerActor
from apps.backend.src.core.orchestrator import CognitiveOrchestrator # Client for CognitiveOrchestratorActor
from apps.backend.src.game.desktop_pet import DesktopPet # Client for DesktopPetActor
from apps.backend.src.game.economy_manager import EconomyManager # Client for EconomyManagerActor
from apps.backend.src.integrations.google_drive_service import GoogleDriveService # Client for GoogleDriveServiceActor
from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController 

# Global instances (will be actor handles or clients to actors)
system_manager_client: Optional[SystemManager] = None 
cognitive_orchestrator_client: Optional[CognitiveOrchestrator] = None
ham_memory_manager_client: Optional[HAMMemoryManager] = None
desktop_pet_client: Optional[DesktopPet] = None 
economy_manager_client: Optional[EconomyManager] = None 
agent_manager_client: Optional[AgentManager] = None 
drive_service_client: Optional[GoogleDriveService] = None 

# Other non-actor related global instances
experience_buffer = None
task_evaluator = None
learning_controller = None
consolidation_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Initializes core components and Ray Actors.
    """
    logger.info("Application startup event triggered...")

    global system_manager_client, cognitive_orchestrator_client, ham_memory_manager_client, \
           desktop_pet_client, economy_manager_client, agent_manager_client, drive_service_client, \
           experience_buffer, task_evaluator, learning_controller, consolidation_service

    try:
        # Initialize non-actor components first
        logger.info("Initializing ExperienceReplayBuffer...")
        try:
            from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
            experience_buffer = ExperienceReplayBuffer(capacity=1000)
        except Exception as e:
            logger.error(f"Failed to initialize ExperienceReplayBuffer: {e}")

        logger.info("Initializing TaskExecutionEvaluator...")
        try:
            from apps.backend.src.ai.evaluation.task_evaluator import TaskExecutionEvaluator
            task_evaluator = TaskExecutionEvaluator()
        except Exception as e:
            logger.error(f"Failed to initialize TaskExecutionEvaluator: {e}")

        logger.info("Initializing AdaptiveLearningController...")
        try:
            learning_controller = AdaptiveLearningController() 
        except Exception as e:
            logger.error(f"Failed to initialize AdaptiveLearningController: {e}")

        # Instantiate SystemManager client, which creates the SystemManagerActor
        logger.info("Initializing SystemManager client (which creates SystemManagerActor)...")
        system_manager_client = SystemManager()
        
        # Call the remote initialize_system on the actor
        init_success = await system_manager_client.initialize_system(
            config_path="apps/backend/configs/system_config.yaml", 
            learning_controller=learning_controller
        )
        if not init_success:
            raise Exception("SystemManagerActor initialization failed.")

        # Retrieve actor handles/clients from the SystemManagerClient
        cognitive_orchestrator_client = await system_manager_client.cognitive_orchestrator
        ham_memory_manager_client = await system_manager_client.ham_memory_manager
        economy_manager_client = await system_manager_client.economy_manager
        desktop_pet_client = await system_manager_client.desktop_pet
        agent_manager_client = await system_manager_client.agent_manager
        drive_service_client = await system_manager_client.google_drive_service
        
        # Store clients in app.state for FastAPI endpoint dependency injection
        app.state.system_manager = system_manager_client
        app.state.cognitive_orchestrator = cognitive_orchestrator_client
        app.state.ham_memory_manager = ham_memory_manager_client
        app.state.economy_manager = economy_manager_client
        app.state.desktop_pet = desktop_pet_client
        app.state.agent_manager = agent_manager_client
        app.state.drive_service = drive_service_client
        app.state.learning_controller = learning_controller 

        logger.info("Initializing NocturnalConsolidationService...")
        try:
            from apps.backend.src.services.consolidation_service import NocturnalConsolidationService
            missing = []
            if experience_buffer is None: missing.append("experience_buffer")
            if task_evaluator is None: missing.append("task_evaluator")
            if learning_controller is None: missing.append("learning_controller")
            if ham_memory_manager_client is None: missing.append("ham_memory_manager_client")
            
            if not missing:
                consolidation_service = NocturnalConsolidationService(
                    buffer=experience_buffer,
                    evaluator=task_evaluator,
                    controller=learning_controller,
                    memory_manager=ham_memory_manager_client 
                )
                sys.stderr.write("DEBUG: ConsolidationService successfully initialized.\n")
            else:
                sys.stderr.write(f"DEBUG: ConsolidationService skipped. Missing: {', '.join(missing)}\n")
        except Exception as e:
            sys.stderr.write(f"DEBUG: ConsolidationService failed with exception: {e}\n")
            logger.error(f"Failed to initialize NocturnalConsolidationService: {e}")
        
        # Register agent types with the manager client
        try:
            from apps.backend.src.ai.agents.base_agent import BaseAgent
            from apps.backend.src.ai.agents.tool_using_agent import ToolUsingAgent
            
            # The agent_manager_client is now a client to an Actor, so use remote calls
            if agent_manager_client:
                await agent_manager_client.register_agent_type.remote("BaseAgent", BaseAgent)
                await agent_manager_client.register_agent_type.remote("ToolUsingAgent", ToolUsingAgent)
                logger.info("BaseAgent and ToolUsingAgent registered with AgentManagerActor.")
            else:
                logger.error("AgentManager client not initialized, skipping agent registration.")
        except Exception as e:
            logger.error(f"Failed to register agents: {e}")

        # === Background Maintenance Loops (Phase 2.1) ===
        # These loops will now interact with the Actor clients
        
        async def personality_heartbeat():
            """Decays energy and updates mood periodically."""
            logger.info("Starting Personality Heartbeat Loop...")
            while True:
                try:
                    await asyncio.sleep(60) # Every minute
                    if desktop_pet_client:
                        # desktop_pet_client is a client to an Actor, so call remote methods
                        # Accessing direct properties like 'personality' would need a remote method
                        # For now, let's assume update_state handles this or expose remote methods.
                        # As per DesktopPetActor, it has `personality` directly.
                        # This needs adjustment: properties are not directly available on ActorHandles.
                        # For now, I'll comment out the personality access.
                        
                        # await desktop_pet_client.personality.decay_energy.remote(delta=0.01) # Needs remote property access
                        # await desktop_pet_client.personality.decay_needs.remote(delta=0.01) # Needs remote property access
                        await desktop_pet_client.check_and_queue_proactive_messages.remote() # This method exists
                        # logger.debug(f"Heartbeat: Energy={{desktop_pet_client.personality.emotion.energy:.2f}}")
                except Exception as e:
                    logger.error(f"Error in personality_heartbeat: {e}")

        async def nocturnal_consolidation_loop():
            """Runs ICE consolidation periodically (e.g., every 10 minutes in simulation)."""
            logger.info("Starting ICE Consolidation Loop...")
            while True:
                try:
                    await asyncio.sleep(600) # Every 10 minutes
                    if consolidation_service:
                        await consolidation_service.consolidate(batch_size=5) # ConsolidationService is local
                except Exception as e:
                    logger.error(f"Error in nocturnal_consolidation_loop: {e}")

        async def self_reflection_loop():
            """Runs Cognitive Orchestrator's self-reflection periodically."""
            logger.info("Starting Self-Reflection Loop...")
            while True:
                try:
                    await asyncio.sleep(3600) # Every hour (e.g.)
                    if cognitive_orchestrator_client:
                        await cognitive_orchestrator_client._perform_self_reflection.remote()
                except Exception as e:
                    logger.error(f"Error in self_reflection_loop: {e}")

        asyncio.create_task(personality_heartbeat())
        asyncio.create_task(nocturnal_consolidation_loop())
        asyncio.create_task(self_reflection_loop())
        
        logger.info("Lifespan background tasks initiated.")
        
    except Exception as e:
        logger.error(f"Critical error during startup: {e}", exc_info=True)
        # We don't raise here to allow the server to start in a degraded state

    yield

    # --- Shutdown logic ---
    logger.info("Application shutdown event triggered.")
    # Call shutdown on the SystemManagerClient, which will terminate the Actor
    if system_manager_client:
        await system_manager_client.shutdown_system()
        # Optionally, explicitly shut down Ray if this is the only process using it.
        # ray.shutdown()
        logger.info("Ray shutdown initiated (if it was started by this process).")


# Initialize FastAPI app
app = FastAPI(
    title="Unified AI Project - Backend",
    description="Core backend service for the Unified AI Project, managing AI agents, core services, and data pipelines.",
    version="2.2.0",
    lifespan=lifespan
)

# Register custom exception handlers and API routers
register_exception_handlers(app)
app.include_router(v1_tools_router.router, prefix="/api/v1")
app.include_router(v1_orchestrator_router.router, prefix="/api/v1") # Will use client
app.include_router(v1_llm_router.router, prefix="/api/v1")
app.include_router(v1_chat_router.router, prefix="/api/v1") # Will use client
app.include_router(v1_pet_router.router, prefix="/api/v1") # Will use client
app.include_router(v1_economy_router.router, prefix="/api/v1") # Will use client

# Phase 3.1: Google Drive Integration
try:
    from apps.backend.src.api.v1.endpoints import drive as v1_drive_router
    app.include_router(v1_drive_router.router, prefix="/api/v1") # Will use client
    logger.info("Google Drive API routes registered")
except Exception as e:
    logger.warning(f"Failed to register Drive API routes: {e}")


@app.get("/")
async def read_root():
    """Root endpoint to confirm the server is running."""
    return {"message": "Unified AI Project API is running"}


@app.post("/api/v1/ai/dream")
async def trigger_dream(batch_size: int = 10):
    """Triggers the nocturnal consolidation process (ICE Model)."""
    if not consolidation_service:
        return {"status": "error", "message": "ConsolidationService not initialized."}
    
    try:
        # ConsolidationService is a local instance, not an actor
        summary = await consolidation_service.consolidate(batch_size=batch_size)
        return summary
    except Exception as e:
        logger.error(f"Consolidation error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/ai/self_reflect")
async def trigger_self_reflection_endpoint():
    """
    Triggers the Cognitive Orchestrator to perform a self-reflection process.
    """
    # Use the client
    if cognitive_orchestrator_client is None:
        raise HTTPException(status_code=503, detail="Cognitive Orchestrator not initialized.")
    
    try:
        reflection_report = await cognitive_orchestrator_client._perform_self_reflection()
        return {"status": "success", "report": reflection_report}
    except Exception as e:
        logger.error(f"Error during self-reflection: {e}")
        raise HTTPException(status_code=500, detail=f"Self-reflection failed: {str(e)}")

@app.get("/api/v1/debug/memory/retrieve")
async def debug_retrieve_memory_endpoint(query: str, limit: int = 5):
    """
    Debug endpoint to retrieve memories directly from HAMMemoryManager.
    """
    # Use the client
    if ham_memory_manager_client is None:
        raise HTTPException(status_code=503, detail="HAMMemoryManager not initialized.")
    
    try:
        memories = await ham_memory_manager_client.retrieve_relevant_memories(
            query=query,
            limit=limit
        )
        return {"status": "success", "memories": memories}
    except Exception as e:
        logger.error(f"Failed to retrieve memories for debug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for frontend."""
    # Check if the SystemManagerActor is initialized
    if system_manager_client is None or not await system_manager_client.is_initialized:
         raise HTTPException(status_code=503, detail="Backend system not fully initialized.")
    return {"status": "ok", "services": {"backend": "running"}}


@app.get("/api/v1/debug/vars")
async def debug_vars():
    """Debug endpoint to check status of all global managers."""
    # Use clients here
    return {
        "agent_manager": agent_manager_client is not None,
        "ham_memory_manager": ham_memory_manager_client is not None,
        "system_manager": system_manager_client is not None,
        "cognitive_orchestrator": cognitive_orchestrator_client is not None,
        "desktop_pet": desktop_pet_client is not None,
        "economy_manager": economy_manager_client is not None,
        "experience_buffer": experience_buffer is not None,
        "task_evaluator": task_evaluator is not None,
        "learning_controller": learning_controller is not None,
        "consolidation_service": consolidation_service is not None,
        "drive_service": drive_service_client is not None,
        "experience_buffer_len": len(experience_buffer) if experience_buffer else 0
    }


# --- Endpoint Definitions ---
# Note: These endpoints will likely fail if they depend on managers
# that are not initialized (because lifespan is disabled).
# This is expected during this phase of debugging.


class LaunchAgentRequest(BaseModel):
    agent_type: str
    agent_id: str | None = None
    name: str | None = None
    kwargs: dict[str, Any] = {}


@app.post("/api/v1/agents/launch")
async def launch_agent_endpoint(request: LaunchAgentRequest):
    # Use the client
    if agent_manager_client is None:
        raise HTTPException(status_code=503, detail="AgentManager not initialized.")
    
    try:
        agent = await agent_manager_client.launch_agent(
            agent_type_name=request.agent_type,
            agent_id=request.agent_id,
            name=request.name,
            **request.kwargs
        )
        return {"status": "success", "agent_id": agent.agent_id, "name": agent.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to launch agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class StoreMemoryRequest(BaseModel):
    experience: dict[str, Any]


@app.post("/api/v1/memory/store")
async def store_memory_endpoint(request: StoreMemoryRequest):
    if ham_memory_manager_client is None:
        raise HTTPException(status_code=503, detail="HAMMemoryManager not initialized.")
    
    try:
        memory_id = await ham_memory_manager_client.store_experience(request.experience)
        return {"status": "success", "memory_id": memory_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RetrieveMemoryRequest(BaseModel):
    query: str
    limit: int = 5


@app.post("/api/v1/memory/retrieve")
async def retrieve_memory_endpoint(request: RetrieveMemoryRequest):
    if ham_memory_manager_client is None:
        raise HTTPException(status_code=503, detail="HAMMemoryManager not initialized.")
    
    try:
        memories = await ham_memory_manager_client.retrieve_relevant_memories(
            query=request.query,
            limit=request.limit
        )
        return {"status": "success", "memories": memories}
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ... (all other endpoints are effectively disabled for now)

class MSCUChatRequest(BaseModel):
    message: str

@app.post("/api/v1/chat/mscu")
async def mscu_chat_endpoint(request: MSCUChatRequest):
    """
    Endpoint for the Mixed-Strategy Cognitive Unit (MSCU).
    Uses Behavior Trees and VDAF for governance.
    """
    if cognitive_orchestrator_client is None:
        raise HTTPException(status_code=503, detail="Cognitive Orchestrator not initialized.")
    
    try:
        result = await cognitive_orchestrator_client.process_user_input(request.message)
        return result
    except Exception as e:
        logger.error(f"Error during self-reflection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.backend.main:app", host="0.0.0.0", port=8000, reload=False)