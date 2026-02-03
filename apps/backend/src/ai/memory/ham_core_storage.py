import os
import os
import json
import logging
import psutil
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class HAMCoreStorage:
    def __init__(self, storage_dir: str, core_storage_filename: str, resource_awareness_service: Optional[Any] = None):
        self.storage_dir = storage_dir
        self.core_storage_filepath = os.path.join(self.storage_dir, core_storage_filename)
        self.resource_awareness_service = resource_awareness_service
        self.core_memory_store: Dict[str, Any] = {} # This will be passed from HAMMemoryManager
        self.next_memory_id = 1 # This will be passed from HAMMemoryManager

    def _get_current_disk_usage_gb(self) -> float:
        """Returns the current size of the core_storage_filepath in GB."""
        try:
            if os.path.exists(self.core_storage_filepath):
                file_size_bytes = os.path.getsize(self.core_storage_filepath)
                return file_size_bytes / (1024**3) # Bytes to GB
        except OSError as e:
            logger.error(f"HAM: Error getting file size for {self.core_storage_filepath}: {e}")
        return 0.0 # Default to 0 if file doesn't exist or error

    def _simulate_disk_lag_and_check_limit(self) -> bool:
        """
        Checks simulated disk usage against limits and simulates lag if thresholds are met.
        Returns True if it's okay to save, False if disk full limit is hit.
        """
        if not self.resource_awareness_service:
            return True # No service, no simulated limits to check

        disk_config = self.resource_awareness_service.get_simulated_disk_config()
        if not disk_config:
            return True # No disk config in service, no limits to check

        current_usage_gb = self._get_current_disk_usage_gb()
        total_simulated_disk_gb = disk_config.get('space_gb', float('inf'))

        # Hard Limit Check
        if current_usage_gb >= total_simulated_disk_gb:
            logger.critical(f"HAM: Simulated disk full! Usage: {current_usage_gb:.2f}GB, Limit: {total_simulated_disk_gb:.2f}GB. Save operation aborted.")
            return False # Prevent save

        # Lag Simulation
        warning_thresh_gb = total_simulated_disk_gb * (disk_config.get('warning_threshold_percent', 80) / 100.0)
        critical_thresh_gb = total_simulated_disk_gb * (disk_config.get('critical_threshold_percent', 95) / 100.0)

        lag_to_apply_seconds = 0.0
        base_delay = 0.1 # A small base delay for I/O simulation
        if current_usage_gb >= critical_thresh_gb:
            lag_factor = disk_config.get('lag_factor_critical', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            logger.warning(f"HAM: Simulated disk usage ({current_usage_gb:.2f}GB) is at CRITICAL level ( > {critical_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")
        elif current_usage_gb >= warning_thresh_gb:
            lag_factor = disk_config.get('lag_factor_warning', 1.0)
            lag_to_apply_seconds = base_delay * lag_factor
            logger.info(f"HAM: Simulated disk usage ({current_usage_gb:.2f}GB) is at WARNING level ( > {warning_thresh_gb:.2f}GB). Simulating {lag_to_apply_seconds:.2f}s lag.")

        if lag_to_apply_seconds > 0:
            # Instead of sleeping, we just indicate that the operation should be retried
            return False

        return True # OK to save

    def _save_core_memory_to_file(self, core_memory_store: Dict[str, Any], next_memory_id: int, fernet: Optional[Any]) -> bool:
        """Saves the core memory store to a JSON file, respecting simulated disk limits."""

        if not self._simulate_disk_lag_and_check_limit():
            # If _simulate_disk_lag_and_check_limit returns False, it means disk is full.
            # store_experience should handle this by returning None.
            return False # Indicate save was prevented

        try:
            with open(self.core_storage_filepath, 'w', encoding='utf-8') as f:
                serializable_store = {}
                for mem_id, data_pkg in core_memory_store.items():
                    serializable_store[mem_id] = {
                        "timestamp": data_pkg["timestamp"],
                        "data_type": data_pkg["data_type"],
                        "encrypted_package_b64": data_pkg["encrypted_package"].decode('latin-1'), # latin-1 for bytes
                        "metadata": data_pkg.get("metadata")
                    }
                json.dump({"next_memory_id": next_memory_id, "store": serializable_store}, f, indent=2)
            return True # Save successful
        except Exception as e:
            logger.error(f"Error saving core memory to file: {e}")
            return False # Save failed

    def _load_core_memory_from_file(self, core_memory_store: Dict[str, Any], next_memory_id: int, fernet: Optional[Any]) -> Tuple[Dict[str, Any], int]:
        if not os.path.exists(self.core_storage_filepath):
            logger.info("Core memory file not found. Initializing an empty store and saving.")
            return {}, 1

        try:
            with open(self.core_storage_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                next_memory_id = data.get("next_memory_id", 1)
                serializable_store = data.get("store", {})
                core_memory_store = {}
                for mem_id, data_pkg_b64 in serializable_store.items():
                    core_memory_store[mem_id] = {
                        "timestamp": data_pkg_b64["timestamp"],
                        "data_type": data_pkg_b64["data_type"],
                        "encrypted_package": data_pkg_b64["encrypted_package_b64"].encode('latin-1'),
                        "metadata": data_pkg_b64.get("metadata"),
                        "relevance": 0.5,  # Default relevance score
                        "protected": False  # Default protection flag
                    }
            logger.info(f"Core memory loaded from {self.core_storage_filepath}. Next ID: {next_memory_id}")
            return core_memory_store, next_memory_id
        except Exception as e:
            logger.error(f"Error loading core memory from file: {e}. Starting with an empty store.")
            return {}, 1
