import asyncio
import logging
import ray
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any
import datetime

# Add project root to sys.path to allow imports from 'apps'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.backend.src.core.managers.system_manager import SystemManager
from apps.backend.scripts.performance_benchmark_framework import PerformanceBenchmarkFramework, SystemResourceMonitor
from apps.backend.src.core.config.system_config import SystemConfig
from apps.backend.src.core.config.path_config import PathConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mocking for SystemConfig and PathConfig ---
# To ensure the benchmark can run independently without requiring actual config files
class MockSystemConfig(SystemConfig):
    _config_data = {
        "HSP_BROKER_HOST": "localhost",
        "HSP_BROKER_PORT": 1883,
        "PET_NAME": "TestAngela",
    }

    @staticmethod
    def get_all():
        return MockSystemConfig._config_data

    @staticmethod
    def load_from_file(path):
        logger.debug(f"MockSystemConfig loading from {path}")
        pass

class MockPathConfig(PathConfig):
    PROJECT_ROOT = project_root
    DATA_DIR = Path(project_root) / "data" / "benchmark_data"
    ECONOMY_DB_DIR = DATA_DIR
    
    @staticmethod
    def ensure_dirs_exist():
        os.makedirs(MockPathConfig.DATA_DIR, exist_ok=True)
        os.makedirs(MockPathConfig.ECONOMY_DB_DIR, exist_ok=True)
        logger.debug(f"MockPathConfig ensuring dirs exist: {MockPathConfig.DATA_DIR}, {MockPathConfig.ECONOMY_DB_DIR}")

# Overwrite the actual classes with mocks for benchmarking
# Note: In a real Pytest environment, fixtures would handle this more elegantly.
# For a standalone script, direct patching before SystemManager import is an option,
# or passing mocks explicitly. Here, we'll try to patch before any SystemManager instantiation.
# This direct patching might be problematic depending on import order.
# A cleaner way is to pass these as constructor arguments if SystemManager supports it,
# or to mock them in the benchmark function itself.
# For simplicity in this standalone script, let's proceed with direct patching assumptions
# and add a note about the proper way in tests.
import apps.backend.src.core.managers.system_manager as actual_system_manager_module
import apps.backend.src.core.managers.system_manager_actor as actual_system_manager_actor_module
actual_system_manager_module.SystemConfig = MockSystemConfig
actual_system_manager_module.PathConfig = MockPathConfig
actual_system_manager_actor_module.SystemConfig = MockSystemConfig
actual_system_manager_actor_module.PathConfig = MockPathConfig


async def benchmark_startup_and_basic_interaction(test_name: str = "RaySystemStartupAndInteraction", iterations: int = 1, warmup: int = 0) -> Dict[str, Any]:
    """
    Benchmarks the startup time and a basic interaction of the Ray-based system.
    """
    logger.info(f"Running benchmark: {test_name}")
    
    framework = PerformanceBenchmarkFramework(project_root=project_root)
    
    async def _run_single_iteration():
        system_manager_client = None
        start_time = time.perf_counter()
        try:
            # Re-initialize Ray for each iteration to get a clean startup measure
            if ray.is_initialized():
                ray.shutdown()
            ray.init(ignore_reinit_error=True)
            
            system_manager_client = SystemManager()
            
            init_success = await system_manager_client.initialize_system(
                config_path="apps/backend/configs/system_config.yaml"
            )
            if not init_success:
                raise Exception("SystemManagerActor initialization failed during benchmark.")

            # Basic interaction: simulate a chat message
            cognitive_orchestrator_client = await system_manager_client.cognitive_orchestrator
            if cognitive_orchestrator_client:
                test_message = "Hello, perform a simple task."
                # We need to ensure the remote method is callable for a benchmark.
                # In a real test, mock the remote method's return. Here, we assume it works.
                # For a true benchmark, consider a mock that simulates actual work.
                await cognitive_orchestrator_client.process_user_input.remote(test_message)
            else:
                logger.warning("Cognitive Orchestrator client not available for interaction benchmark.")

        except Exception as e:
            logger.error(f"Error in benchmark iteration: {e}", exc_info=True)
            raise
        finally:
            if system_manager_client:
                await system_manager_client.shutdown_system()
            if ray.is_initialized():
                ray.shutdown()
        
        return time.perf_counter() - start_time

    # Run actual benchmark iterations
    execution_times = []
    for i in range(iterations + warmup):
        if i < warmup:
            logger.info(f"Warmup iteration {i+1}/{warmup}...")
        else:
            logger.info(f"Benchmark iteration {i-warmup+1}/{iterations}...")
        
        try:
            # Run the asynchronous benchmark iteration
            loop = asyncio.get_event_loop()
            if loop.is_running(): # If there's an existing loop (e.g., from pytest-asyncio)
                task = loop.create_task(_run_single_iteration())
                result = await task
            else:
                result = asyncio.run(_run_single_iteration())
                
            if i >= warmup:
                execution_times.append(result)
        except Exception as e:
            logger.error(f"Benchmark run failed for iteration {i+1}: {e}")
            return {
                "name": test_name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        # Add a small delay between iterations to ensure Ray resources are released/reset
        await asyncio.sleep(0.1)

    # Calculate statistics using the framework's helper
    resource_monitor = SystemResourceMonitor() # Placeholder, will return default zeroes
    resource_stats = resource_monitor.get_statistics()
    benchmark_result = framework._calculate_benchmark_stats(test_name, execution_times, resource_stats)
    
    framework._save_benchmark_result(benchmark_result)

    return benchmark_result

async def main():
    logger.info("Starting performance benchmarking for Ray-based system.")
    
    # Run the benchmark
    results = await benchmark_startup_and_basic_interaction(iterations=3, warmup=1) # Reduced iterations for quick test
    
    logger.info("\n--- Benchmark Results ---")
    logger.info(f"Test: {results['name']}")
    logger.info(f"Status: {results['status']}")
    if results['status'] == 'completed':
        logger.info(f"Iterations: {results['iterations']}")
        logger.info(f"Mean Time: {results['mean_time']:.4f} seconds")
        logger.info(f"Median Time: {results['median_time']:.4f} seconds")
        logger.info(f"Std Dev: {results['std_dev']:.4f} seconds")
        logger.info(f"Ops/Second: {results['ops_per_second']:.4f}")
        logger.info(f"CPU Usage (mock): {results['cpu_usage']:.2f}%")
        logger.info(f"Memory Usage (mock): {results['memory_usage']:.2f}MB")
    else:
        logger.error(f"Error: {results.get('error', 'Unknown error')}")
    
    # Optionally, retrieve history and compare
    framework = PerformanceBenchmarkFramework(project_root=project_root)
    history = framework.get_benchmark_history(name="RaySystemStartupAndInteraction", limit=5)
    logger.info("\n--- Recent History ---")
    for r in history:
        logger.info(f"  {r['timestamp']} - Mean: {r['mean_time']:.4f}s, Std: {r['std_dev']:.4f}s, Status: {r['status']}")


if __name__ == "__main__":
    asyncio.run(main())
