import logging
import os
import json
import asyncio
from typing import Any, Dict, Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken

from .ham_types import HAMDataPackageInternal, HAMMemoryError

logger = logging.getLogger(__name__)

class HAMCoreStorage:
    def __init__(self, storage_dir: str, core_storage_filename: str, resource_awareness_service: Optional[Any] = None):
        self.storage_dir = storage_dir
        self.core_storage_filepath = os.path.join(self.storage_dir, core_storage_filename)
        self.resource_awareness_service = resource_awareness_service

    def _load_core_memory_from_file(self, core_memory_store: Dict[str, HAMDataPackageInternal], next_memory_id: int, fernet: Optional[Fernet]) -> Tuple[Dict[str, HAMDataPackageInternal], int]:
        if os.path.exists(self.core_storage_filepath):
            try:
                with open(self.core_storage_filepath, 'rb') as f:
                    encrypted_content = f.read()
                
                if fernet:
                    decrypted_content = fernet.decrypt(encrypted_content)
                else:
                    decrypted_content = encrypted_content # Assume unencrypted if no fernet

                loaded_data = json.loads(decrypted_content.decode('utf-8'))
                core_memory_store = {k: HAMDataPackageInternal(**v) for k, v in loaded_data.get("memories", {}).items()}
                next_memory_id = loaded_data.get("next_memory_id", 0)
                logger.info(f"Loaded {len(core_memory_store)} memories from {self.core_storage_filepath}")
            except InvalidToken:
                logger.error("Failed to decrypt core memory file. MIKO_HAM_KEY might be incorrect or file corrupted. Starting with empty memory.")
                core_memory_store = {}
                next_memory_id = 0
            except Exception as e:
                logger.error(f"Error loading core memory from file {self.core_storage_filepath}: {e}. Starting with empty memory.")
                core_memory_store = {}
                next_memory_id = 0
        else:
            logger.info("Core memory file not found. Starting with empty memory.")
        return core_memory_store, next_memory_id

    def _save_core_memory_to_file(self, core_memory_store: Dict[str, HAMDataPackageInternal], next_memory_id: int, fernet: Optional[Fernet]) -> bool:
        try:
            # Simulate I/O delay
            # await asyncio.sleep(self.BASE_SAVE_DELAY_SECONDS)

            # Check disk space before saving
            if self.resource_awareness_service:
                available_space_gb = self.resource_awareness_service.get_available_disk_space_gb()
                if available_space_gb < 0.1:  # Example: require at least 0.1 GB free
                    logger.warning("Insufficient disk space to save core memory. Skipping save.")
                    return False

            data_to_save = {
                "memories": {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in core_memory_store.items()},
                "next_memory_id": next_memory_id
            }
            json_data = json.dumps(data_to_save, indent=4).encode('utf-8')

            if fernet:
                encrypted_data = fernet.encrypt(json_data)
            else:
                encrypted_data = json_data # Save unencrypted if no fernet

            with open(self.core_storage_filepath, 'wb') as f:
                f.write(encrypted_data)
            logger.debug(f"Core memory saved to {self.core_storage_filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving core memory to file {self.core_storage_filepath}: {e}")
            return False

    def _get_current_disk_usage_gb(self) -> float:
        """
        Returns the current disk usage of the storage directory in GB.
        This is a placeholder for actual disk usage monitoring.
        """
        if self.resource_awareness_service:
            return self.resource_awareness_service.get_available_disk_space_gb(self.storage_dir)
        
        # Fallback / mock implementation if service is not provided
        # psutil is not available in the sandbox, so we'll mock it.
        # In a real environment, you would use:
        # total, used, free = psutil.disk_usage(self.storage_dir)
        # return used / (1024**3) # Convert bytes to GB
        return 0.0 # Mock value for sandbox environment
