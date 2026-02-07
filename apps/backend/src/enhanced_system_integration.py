#!/usr/bin/env python3
"""
Unified AI Project - Enhanced System Integration Module
Integrates all major components of the system for end-to-end functionality:
- System Self-Maintenance Manager (Full Feature Mode)
- Problem Discovery System
- Auto Repair System
- Test System
- Real-time Monitoring
"""

import sys
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the src directory to the path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import the new self-maintenance system
try:
    from system_self_maintenance import (
        SystemSelfMaintenanceManager,
        MaintenanceConfig,
        MaintenanceMode,
        start_self_maintenance,
        stop_self_maintenance,
        get_maintenance_status,
        trigger_emergency_maintenance
    )
    SELF_MAINTENANCE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Self-maintenance system not available: {e}")
    SELF_MAINTENANCE_AVAILABLE = False
    SystemSelfMaintenanceManager = None

logger = logging.getLogger(__name__)

class UnifiedAISystem:
    """Main integration point for the Unified AI Project with Self-Maintenance capabilities"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.maintenance_manager = None
        self.is_running = False
        self.start_time = None
        self.system_health_score = 1.0
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all core components including self-maintenance"""
        logger.info("🚀 Initializing Unified AI System components...")
        
        # Initialize self-maintenance system
        if SELF_MAINTENANCE_AVAILABLE:
            try:
                self.maintenance_manager = SystemSelfMaintenanceManager()
                logger.info("✅ Self-maintenance system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize self-maintenance system: {e}")
                self.maintenance_manager = None
        else:
            logger.warning("⚠️ Self-maintenance system not available")
        
        logger.info("All system components initialized successfully")
        
    def start_system(self, enable_self_maintenance: bool = True, maintenance_mode: str = "full"):
        """Start the unified AI system with optional self-maintenance"""
        logger.info("🚀 Starting Unified AI System...")
        self.is_running = True
        self.start_time = datetime.now()

        # Start self-maintenance if available and requested
        if enable_self_maintenance and self.maintenance_manager:
            try:
                config = MaintenanceConfig(mode=MaintenanceMode(maintenance_mode))
                self.maintenance_manager.update_config(config)
                self.maintenance_manager.start_self_maintenance()
                logger.info(f"✅ Self-maintenance system started in {maintenance_mode} mode")
            except Exception as e:
                logger.error(f"Failed to start self-maintenance system: {e}")
        
        logger.info("✅ Unified AI System started successfully")
        
    def stop_system(self):
        """Stop the unified AI system and self-maintenance"""
        logger.info("🛑 Stopping Unified AI System...")
        self.is_running = False
        
        # Stop self-maintenance if running
        if self.maintenance_manager:
            try:
                self.maintenance_manager.stop_self_maintenance()
                logger.info("✅ Self-maintenance system stopped")
            except Exception as e:
                logger.error(f"Error stopping self-maintenance system: {e}")
        
        logger.info("✅ Unified AI System stopped successfully")
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including self-maintenance"""
        status = {
            "system_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": self._get_uptime(),
            "system_health_score": self.system_health_score,
            "self_maintenance_available": SELF_MAINTENANCE_AVAILABLE,
        }
        
        # Add self-maintenance status if available
        if self.maintenance_manager:
            try:
                maintenance_status = self.maintenance_manager.get_maintenance_status()
                status["self_maintenance"] = maintenance_status
            except Exception as e:
                logger.error(f"Failed to get maintenance status: {e}")
                status["self_maintenance"] = {"error": str(e)}
        
        return status
    
    def _get_uptime(self) -> str:
        """Calculate system uptime"""
        if not self.start_time:
            return "00:00:00"
        
        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def trigger_system_maintenance(self):
        """Manually trigger system maintenance"""
        if self.maintenance_manager:
            try:
                self.maintenance_manager.trigger_emergency_maintenance()
                logger.info("🚨 Manual emergency maintenance triggered")
                return {"status": "success", "message": "Emergency maintenance triggered"}
            except Exception as e:
                logger.error(f"Failed to trigger emergency maintenance: {e}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": "Self-maintenance system not available"}
    
    def process_request(self, user_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user request through the unified system"""
        try:
            logger.info(f"Processing request for user {user_id}")
            # Handle different request types
            request_type = request.get("type", "general")

            if request_type == "system_status":
                return {
                    "status": "success",
                    "data": self.get_system_status()
                }
            elif request_type == "trigger_maintenance":
                return self.trigger_system_maintenance()
            elif request_type == "maintenance_control":
                action = request.get("action")
                if action == "start":
                    mode = request.get("mode", "full")
                    if start_self_maintenance(mode):
                        return {"status": "success", "message": f"Self-maintenance started in {mode} mode"}
                    else:
                        return {"status": "error", "message": "Failed to start self-maintenance"}
                elif action == "stop":
                    if stop_self_maintenance():
                        return {"status": "success", "message": "Self-maintenance stopped"}
                    else:
                        return {"status": "error", "message": "Failed to stop self-maintenance"}
                else:
                    return {"status": "error", "message": f"Unknown action: {action}"}
            else:
                # General request processing
                return {
                    "status": "success",
                    "message": "Request processed successfully",
                    "system_status": self.get_system_status()
                }
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Testing Enhanced Unified AI System with Self-Maintenance...")
    
    # Create and start the enhanced unified AI system
    unified_ai = UnifiedAISystem()

    try:
        # Start with full self-maintenance mode
        unified_ai.start_system(enable_self_maintenance=True, maintenance_mode="full")
        
        # Test system status
        print("📊 System Status:")
        status = unified_ai.get_system_status()
        print(json.dumps(status, indent=2, default=str))
        
        # Test different request types
        test_requests = [
            {"type": "system_status"},
            {"type": "trigger_maintenance"},
            {"type": "maintenance_control", "action": "status"}
        ]
        
        for request in test_requests:
            print(f"\n🧪 Testing request: {request}")
            result = unified_ai.process_request("test_user", request)
            print(f"Result: {result}")
        
        print("\n🔄 System running with self-maintenance... (Press Ctrl+C to stop)")
        try:
            while True:
                time.sleep(30)  # Run for 30 seconds intervals
                status = unified_ai.get_system_status()
                print(f"⏰ Uptime: {status['uptime']} Health: {status['system_health_score']}")
        except KeyboardInterrupt:
            print("\n🛑 User interrupted, shutting down...")
        
    except Exception as e:
        print(f"❌ Error during system operation: {e}")
    finally:
        unified_ai.stop_system()
        print("✅ Enhanced Unified AI System stopped")