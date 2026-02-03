import asyncio
import logging
from apps.backend.src.core.managers.system_manager import SystemManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting launcher.py - Initializing SystemManager.")

    system_manager_client = None
    try:
        # Instantiate the SystemManager client
        system_manager_client = SystemManager()
        
        # Initialize the system
        logger.info("Calling system_manager_client.initialize_system()...")
        init_success = await system_manager_client.initialize_system(config_path="apps/backend/configs/system_config.yaml")
        
        if init_success:
            logger.info("System initialized successfully via SystemManagerActor.")
            
            # Retrieve instances for specific components managed by the SystemManager
            cognitive_orchestrator = system_manager_client.cognitive_orchestrator
            desktop_pet = system_manager_client.desktop_pet

            # Example interaction: Simulate a chat with the pet via the orchestrator
            if cognitive_orchestrator:
                logger.info("Attempting a test interaction with CognitiveOrchestrator...")
                test_message = "Hello Angela, how are you today?"
                response = await cognitive_orchestrator.process_user_input(test_message)
                logger.info(f"Cognitive Orchestrator response: {response.get('response', 'No response')}")
            else:
                logger.warning("Cognitive Orchestrator not available for testing.")

            # Example interaction with desktop pet
            if desktop_pet:
                logger.info("Attempting a test interaction with DesktopPet...")
                pet_response = await desktop_pet.handle_user_input("message", {"text": "What do you think of async?"})
                logger.info(f"Desktop Pet response: {pet_response.get('pet_response', 'No response')}")
            else:
                logger.warning("Desktop Pet not available for testing.")

            # Keep the system running for a bit to allow background tasks to start
            logger.info("System running for 5 seconds...")
            await asyncio.sleep(5) 
            
        else:
            logger.error("System initialization failed.")
            
    except Exception as e:
        logger.error(f"An error occurred during system startup: {e}", exc_info=True)
    finally:
        if system_manager_client:
            logger.info("Calling system_manager_client.shutdown_system()...")
            await system_manager_client.shutdown_system()
            logger.info("System shutdown complete.")
        else:
            logger.warning("SystemManager client was not initialized, skipping shutdown.")
        
        

if __name__ == "__main__":
    asyncio.run(main())
