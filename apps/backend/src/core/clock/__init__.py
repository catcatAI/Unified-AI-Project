"""Clock module — unified time base for all system components."""
from .global_system_clock import GlobalSystemClock, TickSubscription

__all__ = ["GlobalSystemClock", "TickSubscription"]
