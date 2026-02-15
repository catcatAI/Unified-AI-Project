import asyncio
import logging
import time
from ai.integration.unified_control_center import UnifiedControlCenter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_concurrency():
    logger.info("Starting Concurrency Test for UnifiedControlCenter...")
    
    # Initialize UCC with 4 workers
    config = {
        'max_workers': 4,
        'system_id': 'test_concurrency_ucc'
    }
    ucc = UnifiedControlCenter(config)
    ucc.start()
    
    tasks = []
    num_tasks = 10
    
    logger.info(f"Submitting {num_tasks} tasks to UCC...")
    start_time = time.time()
    
    # Submit tasks
    task_ids = []
    for i in range(num_tasks):
        task = {
            'id': f'task_{i}',
            'name': f'Concurrent Task {i}',
            'type': 'reasoning'
        }
        tid = await ucc.submit_task(task)
        task_ids.append(tid)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*[ucc.get_task_result(tid) for tid in task_ids])
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"All {num_tasks} tasks finished in {duration:.2f} seconds.")
    
    # Validate results
    success_count = sum(1 for r in results if r.get('status') == 'success')
    logger.info(f"Success Count: {success_count}/{num_tasks}")
    
    # In a sequential world with 0.05s dispatch + other overhead, 10 tasks would take > 0.5s.
    # With 4 workers, it should be significantly faster (around 0.15s - 0.2s).
    if duration < 0.4:
        logger.info("✅ Concurrency confirmed! Total time is much less than sequential execution.")
    else:
        logger.warning(f"⚠️ Concurrency marginal. Duration: {duration:.2f}s")
        
    await ucc.stop()
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(test_concurrency())
