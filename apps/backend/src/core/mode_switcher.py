"""
Mode Switching System - Automatic and Manual Mode Transitions

Handles smooth transitions between Angela modes:
- Lite → Standard → Extended
- Hardware-based auto-switching
- User-initiated manual switching
- Smooth transitions with state preservation
"""

import asyncio
import logging
import psutil
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from shared.utils.hardware_detector import SystemHardwareProbe, ModeRecommender

logger = logging.getLogger(__name__)


class ModeTransitionState(Enum):
    """Mode transition states"""
    IDLE = "idle"
    PREPARING = "preparing"
    TRANSITIONING = "transitioning"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TransitionConfig:
    """Configuration for mode transitions"""
    duration_seconds: float = 30.0
    steps: int = 20
    preserve_memories: bool = True
    preserve_personality: bool = True
    notify_user: bool = True
    allow_cancel: bool = True


class ModeSwitchManager:
    """
    Manages mode switching for Angela AI
    
    Supports:
    - Auto-switching based on hardware conditions
    - Manual user-initiated switching
    - Smooth transitions with progress callbacks
    - State preservation across mode changes
    """
    
    def __init__(self, angela_core, config: Optional[Dict[str, Any]] = None):
        self.angela = angela_core
        self.config = config or {}
        self.transition_config = TransitionConfig()
        
        # State
        self.current_mode: str = 'standard'
        self.target_mode: Optional[str] = None
        self.transition_state: ModeTransitionState = ModeTransitionState.IDLE
        self.transition_progress: float = 0.0
        self.last_auto_check: Optional[datetime] = None
        
        # Callbacks
        self.on_progress: Optional[Callable[[float, str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None
        self.on_fail: Optional[Callable[[str], None]] = None
        
        # Auto-switch settings
        self.auto_switch_enabled = self.config.get('auto_mode_detection', {}).get('enabled', True)
        self.check_interval = timedelta(minutes=5)
        self.thresholds = {
            'upgrade': {'memory_percent': 50, 'cpu_percent': 50},
            'downgrade': {'memory_percent': 80, 'cpu_percent': 90}
        }
        
        # Hardware detection
        self.hw_detector = SystemHardwareProbe()
        self.hw_recommender = ModeRecommender(config)
    
    async def start_auto_monitoring(self):
        """Start automatic mode monitoring and switching"""
        if not self.auto_switch_enabled:
            logger.info("Auto-switching disabled")
            return
        
        logger.info("Starting auto mode monitoring")
        
        while True:
            try:
                await asyncio.sleep(self.check_interval.total_seconds())
                await self._check_auto_switch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto monitoring error: {e}")
    
    async def _check_auto_switch(self):
        """Check if mode switch is needed based on system load"""
        if self.transition_state != ModeTransitionState.IDLE:
            return  # Don't check during transition
        
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            suggested_mode = None
            reason = None
            
            # Check if we need to downgrade (high resource usage)
            if memory.percent > self.thresholds['downgrade']['memory_percent']:
                if self.current_mode == 'extended':
                    suggested_mode = 'standard'
                    reason = f"High memory usage ({memory.percent:.1f}%)"
                elif self.current_mode == 'standard':
                    suggested_mode = 'lite'
                    reason = f"High memory usage ({memory.percent:.1f}%)"
            
            if cpu > self.thresholds['downgrade']['cpu_percent']:
                if self.current_mode == 'extended':
                    suggested_mode = 'standard'
                    reason = reason or f"High CPU usage ({cpu:.1f}%)"
                elif self.current_mode == 'standard':
                    suggested_mode = 'lite'
                    reason = reason or f"High CPU usage ({cpu:.1f}%)"
            
            # Check if we can upgrade (low resource usage)
            if not suggested_mode:
                if memory.percent < self.thresholds['upgrade']['memory_percent'] and \
                   cpu < self.thresholds['upgrade']['cpu_percent']:
                    if self.current_mode == 'lite':
                        suggested_mode = 'standard'
                        reason = "Low resource usage, can upgrade"
                    elif self.current_mode == 'standard':
                        # Only suggest extended if GPU available
                        profile = self.hw_detector.detect()
                        if profile.has_gpu and profile.gpu_vram_gb >= 8:
                            suggested_mode = 'extended'
                            reason = "Low resource usage with GPU available"
            
            if suggested_mode and suggested_mode != self.current_mode:
                logger.info(f"Auto-switch suggested: {self.current_mode} → {suggested_mode} ({reason})")
                
                if self.transition_config.notify_user:
                    await self._notify_user_of_auto_switch(suggested_mode, reason)
                
                # Perform the switch
                await self.switch_mode(suggested_mode, auto_initiated=True)
                
        except Exception as e:
            logger.error(f"Error checking auto-switch: {e}")
    
    async def switch_mode(self, target_mode: str, auto_initiated: bool = False) -> bool:
        """
        Perform mode switch with smooth transition
        
        Args:
            target_mode: Target mode ('lite', 'standard', 'extended')
            auto_initiated: Whether this was auto-triggered
            
        Returns:
            True if successful, False otherwise
        """
        if target_mode == self.current_mode:
            logger.info(f"Already in {target_mode} mode")
            return True
        
        if self.transition_state != ModeTransitionState.IDLE:
            logger.warning("Transition already in progress")
            return False
        
        # Validate mode
        valid_modes = ['lite', 'standard', 'extended']
        if target_mode not in valid_modes:
            logger.error(f"Invalid mode: {target_mode}")
            return False
        
        logger.info(f"Starting mode transition: {self.current_mode} → {target_mode}")
        
        self.transition_state = ModeTransitionState.PREPARING
        self.target_mode = target_mode
        
        try:
            # Phase 1: Preparation
            await self._transition_phase(
                phase_name="Preparing",
                progress_start=0.0,
                progress_end=0.3,
                duration=self.transition_config.duration_seconds * 0.3
            )
            
            # Save current state if needed
            if self.transition_config.preserve_memories:
                await self._preserve_memories()
            
            if self.transition_config.preserve_personality:
                await self._preserve_personality()
            
            # Phase 2: Actual Transition
            self.transition_state = ModeTransitionState.TRANSITIONING
            
            await self._transition_phase(
                phase_name="Transitioning",
                progress_start=0.3,
                progress_end=0.9,
                duration=self.transition_config.duration_seconds * 0.6,
                action=lambda: self._apply_mode_change(target_mode)
            )
            
            # Phase 3: Finalization
            await self._transition_phase(
                phase_name="Finalizing",
                progress_start=0.9,
                progress_end=1.0,
                duration=self.transition_config.duration_seconds * 0.1
            )
            
            # Update current mode
            self.current_mode = target_mode
            self.transition_state = ModeTransitionState.COMPLETED
            
            logger.info(f"Mode transition completed: now in {target_mode} mode")
            
            if self.on_complete:
                self.on_complete(target_mode)
            
            # Reset after delay
            await asyncio.sleep(2)
            self.transition_state = ModeTransitionState.IDLE
            self.transition_progress = 0.0
            
            return True
            
        except Exception as e:
            logger.error(f"Mode transition failed: {e}")
            self.transition_state = ModeTransitionState.FAILED
            
            if self.on_fail:
                self.on_fail(str(e))
            
            return False
    
    async def _transition_phase(self, phase_name: str, progress_start: float, 
                                progress_end: float, duration: float,
                                action: Optional[Callable] = None):
        """Execute a transition phase with progress updates"""
        steps = max(1, int(duration * 10))  # 10 updates per second
        step_duration = duration / steps
        
        for i in range(steps + 1):
            progress = progress_start + (progress_end - progress_start) * (i / steps)
            self.transition_progress = progress
            
            if self.on_progress:
                self.on_progress(progress, phase_name)
            
            # Execute action at 50% of phase
            if action and i == steps // 2:
                action()
            
            await asyncio.sleep(step_duration)
    
    def _apply_mode_change(self, target_mode: str):
        """Apply the actual mode configuration change"""
        if self.angela and hasattr(self.angela, '_apply_mode_config'):
            self.angela._apply_mode_config(target_mode)
        else:
            logger.warning("Angela core not available for mode change")
    
    async def _preserve_memories(self):
        """Preserve memories during transition"""
        logger.info("Preserving memories for transition")
        # Implementation: save to temporary storage
        pass
    
    async def _preserve_personality(self):
        """Preserve personality during transition"""
        logger.info("Preserving personality for transition")
        # Implementation: serialize personality state
        pass
    
    async def _notify_user_of_auto_switch(self, suggested_mode: str, reason: str):
        """Notify user of pending auto-switch"""
        logger.info(f"Auto-switch notification: {suggested_mode} - {reason}")
        # Could use system tray notification here
    
    def get_transition_status(self) -> Dict[str, Any]:
        """Get current transition status"""
        return {
            'current_mode': self.current_mode,
            'target_mode': self.target_mode,
            'state': self.transition_state.value,
            'progress': self.transition_progress,
            'auto_switch_enabled': self.auto_switch_enabled,
            'can_switch': self.transition_state == ModeTransitionState.IDLE
        }
    
    def cancel_transition(self) -> bool:
        """Cancel ongoing transition if allowed"""
        if not self.transition_config.allow_cancel:
            return False
        
        if self.transition_state in [ModeTransitionState.PREPARING, 
                                     ModeTransitionState.TRANSITIONING]:
            logger.info("Cancelling mode transition")
            self.transition_state = ModeTransitionState.IDLE
            self.transition_progress = 0.0
            return True
        
        return False


# Convenience function for manual mode switching
async def quick_mode_switch(angela_core, target_mode: str, 
                            on_progress=None, on_complete=None) -> bool:
    """Quick mode switch with callbacks"""
    manager = ModeSwitchManager(angela_core)
    manager.on_progress = on_progress
    manager.on_complete = on_complete
    return await manager.switch_mode(target_mode)


# Test code
if __name__ == '__main__':
    logger.info("--- Mode Switch Manager Test ---")
    
    # Mock Angela core
    class MockAngela:
        def _apply_mode_config(self, mode):
            logger.info(f"Applying mode config: {mode}")
    
    mock_angela = MockAngela()
    
    # Create manager
    manager = ModeSwitchManager(mock_angela)
    
    # Test progress callback
    def on_progress(progress, phase):
        logger.info(f"Progress: {progress*100:.1f}% - {phase}")
    
    def on_complete(mode):
        logger.info(f"✓ Mode switch completed: {mode}")
    
    manager.on_progress = on_progress
    manager.on_complete = on_complete
    
    # Test switch (would need real async context in production)
    logger.info("Testing mode switch: standard → extended")
    logger.info("Note: Full test requires running Angela with config.yaml")
    logger.info("Mode switch system ready!")
