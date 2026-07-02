"""Deadlock detection and loop detection for tests."""

import asyncio
import functools
import inspect
import logging
import signal
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    DEADLOCK = "deadlock"
    INFINITE_LOOP = "infinite_loop"
    RESOURCE_LEAK = "resource_leak"
    THREAD_LEAK = "thread_leak"
    ASYNC_LEAK = "async_leak"


@dataclass
class DetectionResult:
    detection_type: DetectionType
    detected: bool
    details: str
    stack_trace: Optional[str] = None
    thread_info: Optional[Dict] = None
    resource_info: Optional[Dict] = None


class DeadlockDetector:
    def __init__(
        self,
        check_interval: float = 1.0,
        max_detection_time: float = 30.0
    ) -> None:
        self.check_interval = check_interval
        self.max_detection_time = max_detection_time
        self.active_threads: Set[threading.Thread] = set()
        self.thread_states: Dict[int, Dict] = {}
        self.detection_active = False
        self._detection_thread: Optional[threading.Thread] = None

    def start_detection(self) -> None:
        if self.detection_active:
            return
        self.detection_active = True
        self._detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self._detection_thread.start()
        logger.debug("Deadlock detection started")

    def stop_detection(self) -> None:
        self.detection_active = False
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=1.0)
        logger.debug("Deadlock detection stopped")

    def _detection_loop(self) -> None:
        start_time = time.time()
        while self.detection_active and (time.time() - start_time) < self.max_detection_time:
            try:
                self._check_for_deadlocks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in deadlock detection: {e}")
                break

    def _check_for_deadlocks(self) -> None:
        current_threads = threading.enumerate()
        for thread in current_threads:
            if thread == threading.current_thread():
                continue
            thread_id = thread.ident
            if thread_id is None:
                continue
            if thread_id not in self.thread_states:
                self.thread_states[thread_id] = {
                    'first_seen': time.time(),
                    'last_frame': None,
                    'stuck_count': 0
                }
            frame = sys._current_frames().get(thread_id)
            if frame:
                current_frame_info = (frame.f_code.co_filename, frame.f_lineno)
                if self.thread_states[thread_id]['last_frame'] == current_frame_info:
                    self.thread_states[thread_id]['stuck_count'] += 1
                else:
                    self.thread_states[thread_id]['stuck_count'] = 0
                self.thread_states[thread_id]['last_frame'] = current_frame_info
                if self.thread_states[thread_id]['stuck_count'] > 5:
                    logger.warning(f"Potential deadlock detected in thread {thread_id}")
                    self._report_potential_deadlock(thread, frame)

    def _report_potential_deadlock(self, thread: threading.Thread, frame: Any) -> None:
        import traceback
        stack_trace = ''.join(traceback.format_stack(frame))
        logger.error(f"Deadlock detected in thread {thread.name}\n{stack_trace}")


class LoopDetector:
    def __init__(self, max_iterations: int = 10000, check_interval: int = 100) -> None:
        self.max_iterations = max_iterations
        self.check_interval = check_interval
        self.iteration_counts: Dict[str, int] = {}

    def check_iteration(self, location: str) -> bool:
        if location not in self.iteration_counts:
            self.iteration_counts[location] = 0
        self.iteration_counts[location] += 1
        if self.iteration_counts[location] % self.check_interval == 0:
            logger.debug(f"Loop at {location}: {self.iteration_counts[location]} iterations")
        if self.iteration_counts[location] > self.max_iterations:
            logger.error(f"Infinite loop detected at {location}: {self.iteration_counts[location]} iterations")
            return True
        return False

    def reset(self) -> None:
        self.iteration_counts.clear()


class ResourceLeakDetector:
    def __init__(self) -> None:
        self.initial_thread_count = 0
        self.initial_file_descriptors = 0
        self.initial_memory_usage = 0

    def start_monitoring(self) -> None:
        self.initial_thread_count = threading.active_count()
        try:
            import psutil
            process = psutil.Process()
            self.initial_file_descriptors = process.num_fds() if hasattr(process, 'num_fds') else 0
            self.initial_memory_usage = process.memory_info().rss
        except ImportError:
            logger.warning("psutil not available, limited resource monitoring")

    def check_leaks(self) -> List[DetectionResult]:
        results: List[DetectionResult] = []
        current_thread_count = threading.active_count()
        if current_thread_count > self.initial_thread_count + 2:
            results.append(DetectionResult(
                detection_type=DetectionType.THREAD_LEAK,
                detected=True,
                details=f"Thread leak: {current_thread_count} vs {self.initial_thread_count}",
                thread_info={'current': current_thread_count, 'initial': self.initial_thread_count}
            ))
        try:
            import psutil
            process = psutil.Process()
            current_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            if current_fds > self.initial_file_descriptors + 10:
                results.append(DetectionResult(
                    detection_type=DetectionType.RESOURCE_LEAK,
                    detected=True,
                    details=f"File descriptor leak: {current_fds} vs {self.initial_file_descriptors}",
                    resource_info={'current_fds': current_fds, 'initial_fds': self.initial_file_descriptors}
                ))
        except ImportError:
            logger.debug("psutil not available — skipping file descriptor leak detection")
        return results


class AsyncLoopDetector:
    def __init__(self, max_pending_tasks: int = 100) -> None:
        self.max_pending_tasks = max_pending_tasks
        self.initial_task_count = 0

    def start_monitoring(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            self.initial_task_count = len([task for task in asyncio.all_tasks(loop) if not task.done()])
        except RuntimeError:
            self.initial_task_count = 0

    def check_async_leaks(self) -> List[DetectionResult]:
        results: List[DetectionResult] = []
        try:
            loop = asyncio.get_running_loop()
            current_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
            if len(current_tasks) > self.max_pending_tasks:
                results.append(DetectionResult(
                    detection_type=DetectionType.ASYNC_LEAK,
                    detected=True,
                    details=f"Too many pending async tasks: {len(current_tasks)}",
                    resource_info={'pending_tasks': len(current_tasks), 'max_allowed': self.max_pending_tasks}
                ))
        except RuntimeError:
            pass
        return results


@contextmanager
def deadlock_detection(timeout: float = 30.0, check_interval: float = 1.0):
    detector = DeadlockDetector(check_interval=check_interval, max_detection_time=timeout)
    resource_detector = ResourceLeakDetector()
    async_detector = AsyncLoopDetector()
    try:
        detector.start_detection()
        resource_detector.start_monitoring()
        async_detector.start_monitoring()
        yield detector
    finally:
        detector.stop_detection()
        leaks = resource_detector.check_leaks()
        async_leaks = async_detector.check_async_leaks()
        for leak in leaks + async_leaks:
            if leak.detected:
                logger.warning(f"Resource leak detected: {leak.details}")


def loop_detection(max_iterations: int = 10000):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            detector = LoopDetector(max_iterations=max_iterations)
            try:
                return func(*args, **kwargs)
            finally:
                detector.reset()
        return wrapper
    return decorator


if __name__ == "__main__":
    print("Deadlock detector module loaded")