import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiofiles
import asyncio
import ray # Import ray

# Add the project root to sys.path to enable absolute imports
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from apps.backend.src.core.config.path_config import PathConfig
from apps.backend.src.core.config.system_config import SystemConfig
from apps.backend.src.core.orchestrator import CognitiveOrchestrator
from apps.backend.src.game.desktop_pet import DesktopPet
from apps.backend.src.game.economy_manager import EconomyDB, EconomyManager
from apps.backend.src.core.hsp.connector import HSPConnector
from apps.backend.src.ai.agent_manager import AgentManager
from apps.backend.src.integrations.google_drive_service import GoogleDriveService
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController
from apps.backend.src.core.managers.system_manager_actor import SystemManagerActor # Import the Actor

class SystemManager:
    """
    Client for the SystemManagerActor.
    Delegates calls to the remote SystemManagerActor instance.
    """

    def __init__(self):
        """Initializes the SystemManager client and creates the remote actor."""
        # Initialize Ray if not already done (for safety, though main.py should do it)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
        self.actor = SystemManagerActor.remote() # Create the remote actor
        print("SystemManager client initialized, SystemManagerActor created.")

    async def initialize_system(self, config_path: str = None, learning_controller: Optional[AdaptiveLearningController] = None) -> bool:
        """Initializes core system components via the remote actor."""
        return await self.actor.initialize_system.remote(config_path, learning_controller)

    async def shutdown_system(self) -> bool:
        """Shuts down core system components via the remote actor."""
        return await self.actor.shutdown_system.remote()

    @property
    async def is_initialized(self) -> bool:
        return await self.actor.is_initialized.remote()

    @property
    async def hsp_connector(self) -> Optional[HSPConnector]:
        return await self.actor.hsp_connector.remote()

    @property
    async def economy_db(self) -> Optional[EconomyDB]:
        return await self.actor.economy_db.remote()

    @property
    async def economy_manager(self) -> Optional[EconomyManager]:
        return await self.actor.economy_manager.remote()

    @property
    async def cognitive_orchestrator(self) -> Optional[CognitiveOrchestrator]:
        return await self.actor.cognitive_orchestrator.remote()

    @property
    async def agent_manager(self) -> Optional[AgentManager]:
        return await self.actor.agent_manager.remote()

    @property
    async def desktop_pet(self) -> Optional[DesktopPet]:
        return await self.actor.desktop_pet.remote()

    @property
    async def google_drive_service(self) -> Optional[GoogleDriveService]:
        return await self.actor.google_drive_service.remote()

    @property
    async def ham_memory_manager(self) -> Optional[HAMMemoryManager]:
        return await self.actor.ham_memory_manager.remote()

    @property
    async def learning_controller(self) -> Optional[AdaptiveLearningController]:
        return await self.actor.learning_controller.remote()

