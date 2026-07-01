"""Global System Clock — unified time base with tick subscription.

Provides a centralized clock that all system components can use
instead of independent asyncio.sleep() loops. Supports:
- Configurable tick rate (Hz)
- Tick subscription (callbacks at regular intervals)
- Wall clock time reference
- Start/stop lifecycle
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TickSubscription:
    """A registered tick subscription."""
    interval_ticks: int
    callback: Callable[[int], Any]
    last_tick: int = 0
    enabled: bool = True


class GlobalSystemClock:
    """Unified system clock with tick subscription.

    Usage:
        clock = GlobalSystemClock(tick_rate_hz=10.0)
        await clock.start()

        # Subscribe to fire every 100 ticks (10s at 10Hz)
        clock.subscribe(100, my_callback)

        await clock.stop()
    """

    def __init__(
        self,
        tick_rate_hz: float = 10.0,
        auto_start: bool = False,
    ):
        self._tick_rate_hz = max(0.1, min(1000.0, tick_rate_hz))
        self._tick_interval = 1.0 / self._tick_rate_hz
        self._tick_count: int = 0
        self._start_time: float = 0.0
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._subscriptions: List[TickSubscription] = []
        self._lock = asyncio.Lock()
        self._tick_event = asyncio.Event()

    @property
    def tick_rate_hz(self) -> float:
        return self._tick_rate_hz

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def elapsed_seconds(self) -> float:
        if self._start_time == 0.0:
            return 0.0
        return time.monotonic() - self._start_time

    @property
    def is_running(self) -> bool:
        return self._running

    def now(self) -> float:
        """Current wall clock time (monotonic, seconds since start)."""
        return time.monotonic()

    def subscribe(
        self,
        interval_ticks: int,
        callback: Callable[[int], Any],
    ) -> TickSubscription:
        """Register a callback to fire every `interval_ticks` ticks.

        Args:
            interval_ticks: Fire callback every N ticks (>= 1).
            callback: Async callable receiving current tick count.

        Returns:
            TickSubscription (can be disabled or used to unsubscribe).
        """
        if interval_ticks < 1:
            interval_ticks = 1
        sub = TickSubscription(
            interval_ticks=interval_ticks,
            callback=callback,
            last_tick=self._tick_count,
        )
        self._subscriptions.append(sub)
        logger.debug(
            f"[GlobalSystemClock] Subscribed callback every {interval_ticks} ticks"
        )
        return sub

    def unsubscribe(self, subscription: TickSubscription) -> None:
        """Remove a subscription."""
        if subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

    def disable_subscription(self, subscription: TickSubscription) -> None:
        """Temporarily disable a subscription without removing it."""
        subscription.enabled = False

    def enable_subscription(self, subscription: TickSubscription) -> None:
        """Re-enable a disabled subscription."""
        subscription.enabled = True

    async def start(self) -> None:
        """Start the clock tick loop."""
        if self._running:
            logger.warning("[GlobalSystemClock] Already running")
            return
        self._running = True
        self._tick_count = 0
        self._start_time = time.monotonic()
        self._task = asyncio.create_task(self._tick_loop())
        logger.info(
            f"[GlobalSystemClock] Started at {self._tick_rate_hz:.1f} Hz "
            f"(interval={self._tick_interval*1000:.1f}ms)"
        )

    async def stop(self) -> None:
        """Stop the clock tick loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(
            f"[GlobalSystemClock] Stopped after {self._tick_count} ticks "
            f"({self.elapsed_seconds:.1f}s elapsed)"
        )

    async def force_tick(self) -> int:
        """Manually advance one tick (for testing)."""
        self._tick_count += 1
        current_tick = self._tick_count
        await self._fire_subscriptions(current_tick)
        self._tick_event.set()
        return current_tick

    async def wait_for_ticks(self, n: int) -> int:
        """Wait for n ticks to elapse (event-driven, no polling).

        The caller's execution is suspended until the clock has advanced
        by at least n ticks from the current count. Returns the tick count
        at the time of wake-up.

        Args:
            n: Number of ticks to wait (must be >= 1).

        Returns:
            The tick count when the wait completed.
        """
        if n < 1:
            n = 1
        target = self._tick_count + n
        while self._tick_count < target:
            self._tick_event.clear()
            await self._tick_event.wait()
        return self._tick_count

    async def _tick_loop(self) -> None:
        """Main tick loop — runs at configured frequency."""
        while self._running:
            tick_start = time.monotonic()
            self._tick_count += 1
            current_tick = self._tick_count

            # Fire matching subscriptions
            await self._fire_subscriptions(current_tick)

            # Signal waiters that a tick has elapsed
            self._tick_event.set()

            # Sleep until next tick (accounting for callback execution time)
            elapsed = time.monotonic() - tick_start
            sleep_time = max(0.0, self._tick_interval - elapsed)
            await asyncio.sleep(sleep_time)

    async def _fire_subscriptions(self, current_tick: int) -> None:
        """Fire all subscriptions whose interval has elapsed."""
        async with self._lock:
            for sub in self._subscriptions:
                if not sub.enabled:
                    continue
                if current_tick - sub.last_tick >= sub.interval_ticks:
                    sub.last_tick = current_tick
                    try:
                        if asyncio.iscoroutinefunction(sub.callback):
                            await sub.callback(current_tick)
                        else:
                            sub.callback(current_tick)
                    except Exception as e:
                        logger.error(
                            f"[GlobalSystemClock] Subscription callback failed: {e}",
                            exc_info=True,
                        )
