import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiofiles
import asyncio
import ray

# Add the project root to sys.path to enable absolute imports
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from apps.backend.src.core.config.path_config import PathConfig
from apps.backend.src.core.config.system_config import SystemConfig
from apps.backend.src.core.orchestrator_actor import CognitiveOrchestratorActor # Import the Actor
from apps.backend.src.game.desktop_pet_actor import DesktopPetActor # Import the Actor
from apps.backend.src.game.economy_manager import EconomyDB # EconomyDB is not an actor
from apps.backend.src.game.economy_manager_actor import EconomyManagerActor # Import the Actor
from apps.backend.src.core.hsp.connector import HSPConnector
from apps.backend.src.ai.agent_manager_actor import AgentManagerActor # Import the Actor
from apps.backend.src.integrations.google_drive_service_actor import GoogleDriveServiceActor # Import the Actor
from apps.backend.src.ai.memory.ham_memory_manager_actor import HAMMemoryManagerActor # Import the Actor
from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController


@ray.remote
class SystemManagerActor:
    """Manages the overall system lifecycle, including initialization and shutdown, as a Ray Actor."""

    def __init__(self):
        """Initializes the SystemManagerActor and its components."""
        self.is_initialized: bool = False
        self.hsp_connector: Optional[HSPConnector] = None
        self.economy_db: Optional[EconomyDB] = None
        self.economy_manager: Optional[Any] = None # Will be an ActorHandle
        self.cognitive_orchestrator: Optional[Any] = None # Will be an ActorHandle
        self.agent_manager: Optional[Any] = None # Will be an ActorHandle
        self.desktop_pet: Optional[Any] = None # Will be an ActorHandle
        self.google_drive_service: Optional[Any] = None # Will be an ActorHandle
        self.ham_memory_manager: Optional[Any] = None # Will be an ActorHandle
        self.learning_controller: Optional[AdaptiveLearningController] = None # Added
        print("SystemManagerActor initialized.")

    async def initialize_system(self, config_path: str = None, learning_controller: Optional[AdaptiveLearningController] = None) -> bool:
        """Initializes core system components."""
        if self.is_initialized:
            print("System already initialized.")
            return True

        print("Initializing system...")

        # Load configurations
        if config_path:
            SystemConfig.load_from_file(config_path)
        
        system_config_data = SystemConfig.get_all()

        self.learning_controller = learning_controller # Assign the passed controller

        # Ensure necessary directories exist
        PathConfig.ensure_dirs_exist()

        # 1. Initialize HSPConnector
        self.hsp_connector = HSPConnector(
            client_id="system_manager_actor", # Changed client ID for clarity
            broker_host=system_config_data.get("HSP_BROKER_HOST", "localhost"),
            broker_port=system_config_data.get("HSP_BROKER_PORT", 1883)
        )
        await self.hsp_connector.connect()
        print("HSPConnector initialized and connected.")

        # 2. Initialize EconomyDB and EconomyManagerActor
        economy_db_path = PathConfig.ECONOMY_DB_DIR / "economy.db"
        self.economy_db = EconomyDB(db_path=str(economy_db_path)) # EconomyDB is not an actor
        self.economy_manager = EconomyManagerActor.remote(config=system_config_data, db=self.economy_db) # Create Actor
        print("EconomyManagerActor initialized.")

        # 3. Initialize HAMMemoryManagerActor
        self.ham_memory_manager = HAMMemoryManagerActor.remote() # Create Actor
        print("HAMMemoryManagerActor initialized.")
        
        print("--- Adding 2-second delay to prevent initialization race condition ---")
        await asyncio.sleep(2)

        # 4. Initialize CognitiveOrchestratorActor
        self.cognitive_orchestrator = CognitiveOrchestratorActor.remote(
            experience_buffer=None, # Experience buffer can be integrated later
            ham_memory_manager=self.ham_memory_manager, # Pass ActorHandle
            learning_controller=self.learning_controller # Pass the AdaptiveLearningController instance
        )
        print("CognitiveOrchestratorActor initialized.")

        # 5. Initialize AgentManagerActor
        self.agent_manager = AgentManagerActor.remote() # Create Actor
        print("AgentManagerActor initialized.")

        # 5. Initialize DesktopPetActor
        self.desktop_pet = DesktopPetActor.remote(
            name=system_config_data.get("PET_NAME", "Angela"),
            orchestrator=self.cognitive_orchestrator, # Pass ActorHandle
            economy_manager=self.economy_manager # Pass ActorHandle
        )
        print("DesktopPetActor initialized.")

        # 6. Initialize GoogleDriveServiceActor and authenticate
        print("Initializing GoogleDriveServiceActor...")
        google_credentials_path = str(Path(PathConfig.PROJECT_ROOT) / "apps" / "backend" / "config" / "credentials.json")
        google_token_path = str(PathConfig.DATA_DIR / "google_tokens.json")
        
        print(f"DEBUG SystemManagerActor: Google Credentials Path: {google_credentials_path}")
        print(f"DEBUG SystemManagerActor: Google Token Path: {google_token_path}")

        # Check if credentials file exists before proceeding
        if not Path(google_credentials_path).exists():
            print(f"ERROR SystemManagerActor: Google Drive credentials file not found at {google_credentials_path}. Skipping authentication.")
            self.google_drive_service = None # Ensure it's None if credentials are missing
        else:
            self.google_drive_service = GoogleDriveServiceActor.remote( # Create Actor
                credentials_path=google_credentials_path,
                token_path=google_token_path
            )
            # Only attempt to authenticate if service is created and not already authenticated
            if self.google_drive_service: # Check if service actor handle exists
                is_auth = await self.google_drive_service.is_authenticated.remote()
                if not is_auth:
                    print("Attempting GoogleDriveService authentication...")
                    auth_result = await self.google_drive_service.authenticate.remote() # Store the result
                    print(f"DEBUG SystemManagerActor: GoogleDriveService.authenticate() returned: {auth_result}")

                    if auth_result:
                        print("GoogleDriveService authenticated.")
                    else:
                        print("GoogleDriveService authentication failed. Manual intervention may be required.")
                else:
                    print("GoogleDriveService already authenticated (from existing token).")
            else:
                print("GoogleDriveServiceActor not instantiated due to previous error.")


        # Write status file
        async with aiofiles.open("system_status_actor.txt", mode="w") as f: # Changed filename for actor
            await f.write(f"System initialized at {datetime.now(timezone.utc).isoformat()}\n")
        print("System status file created.")

        self.is_initialized = True
        print("System initialization complete.")
        return True

    async def shutdown_system(self) -> bool:
        """Shuts down core system components."""
        if not self.is_initialized:
            print("System is not initialized.")
            return False

        print("Shutting down system...")

        # 1. Shutdown DesktopPetActor
        if self.desktop_pet:
            await self.desktop_pet.shutdown.remote() # Call remote shutdown
            print("DesktopPetActor shutdown initiated.")

        # 2. Shutdown AgentManagerActor
        if self.agent_manager:
            await self.agent_manager.shutdown.remote() # Call remote shutdown
            print("AgentManagerActor shut down.")

        # 3. Close EconomyDB connection (still local to this actor)
        if self.economy_db:
            self.economy_db.close()
            print("EconomyDB connection closed.")
        
        # 4. Disconnect HSPConnector (still local to this actor)
        if self.hsp_connector:
            await self.hsp_connector.disconnect()
            print("HSPConnector disconnected.")

        # 5. GoogleDriveServiceActor does not require explicit shutdown, but we can clear the instance
        if self.google_drive_service:
            await self.google_drive_service.__ray_terminate__.remote() # Terminate the actor
            self.google_drive_service = None
            print("GoogleDriveServiceActor instance terminated.")

        # 6. HAMMemoryManagerActor does not require explicit shutdown, but we can clear the instance
        if self.ham_memory_manager:
            await self.ham_memory_manager.__ray_terminate__.remote() # Terminate the actor
            self.ham_memory_manager = None
            print("HAMMemoryManagerActor instance terminated.")
        
        # 7. CognitiveOrchestratorActor needs to be terminated
        if self.cognitive_orchestrator:
            await self.cognitive_orchestrator.__ray_terminate__.remote() # Terminate the actor
            self.cognitive_orchestrator = None
            print("CognitiveOrchestratorActor instance terminated.")
        
        
        # Delete status file
        if Path("system_status_actor.txt").exists(): # Changed filename for actor
            Path("system_status_actor.txt").unlink()
            print("System status file deleted.")

        self.is_initialized = False
        print("System shut down.")
        return True
