#!/usr/bin/env python3
"""
Unified AI Project - System Integration Module
Integrates all major components of the system for end-to-end functionality
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import core components
from .core_ai.agent_manager import AgentManager
from .core_ai.execution_manager import ExecutionManager
from .core_ai.memory.ham_memory_manager import HAMMemoryManager
from .core_ai.learning.continuous_learning_manager import ContinuousLearningManager
from .core_ai.dialogue.dialogue_manager import DialogueManager

# Import services
from .services.multi_llm_service import MultiLLMService
from .services.ai_editor import AIEditorService
from .services.ai_virtual_input_service import AIVirtualInputService
from .services.resource_awareness_service import ResourceAwarenessService

# Import integrations
from .integrations.enhanced_atlassian_bridge import EnhancedAtlassianBridge
from .integrations.rovo_dev_agent import RovoDevAgent

# Import security
from .security.permission_control import PermissionControlSystem
from .security.audit_logger import AuditLogger
from .security.enhanced_sandbox import EnhancedSandboxExecutor

# Import tools
from .tools.tool_dispatcher import ToolDispatcher

logger = logging.getLogger(__name__)

class UnifiedAISystem:
    """Main integration point for the Unified AI Project"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all core components"""
        logger.info("Initializing Unified AI System components...")
        
        # Initialize core AI components
        self.agent_manager = AgentManager(self.config.get('agent_manager', {}))
        self.execution_manager = ExecutionManager(self.config.get('execution_manager', {}))
        self.ham_memory_manager = HAMMemoryManager(self.config.get('ham_memory', {}))
        self.continuous_learning_manager = ContinuousLearningManager(self.config.get('learning', {}))
        self.dialogue_manager = DialogueManager(self.config.get('dialogue', {}))
        
        # Initialize services
        self.multi_llm_service = MultiLLMService(self.config.get('llm_service', {}))
        self.ai_editor_service = AIEditorService(self.config.get('ai_editor', {}))
        self.ai_virtual_input_service = AIVirtualInputService(self.config.get('virtual_input', {}))
        self.resource_awareness_service = ResourceAwarenessService(self.config.get('resource_awareness', {}))
        
        # Initialize integrations
        self.atlassian_bridge = EnhancedAtlassianBridge(self.config.get('atlassian', {}))
        self.rovo_dev_agent = RovoDevAgent(self.config.get('rovo_dev', {}))
        
        # Initialize security
        self.permission_control = PermissionControlSystem()
        self.audit_logger = AuditLogger()
        self.sandbox_executor = EnhancedSandboxExecutor()
        
        # Initialize tools
        self.tool_dispatcher = ToolDispatcher()
        
        logger.info("All system components initialized successfully")
        
    def start_system(self):
        """Start the unified AI system"""
        logger.info("Starting Unified AI System...")
        
        # Start core services
        self.agent_manager.start()
        self.execution_manager.start()
        self.ham_memory_manager.start()
        self.continuous_learning_manager.start()
        self.dialogue_manager.start()
        
        # Start external services
        self.multi_llm_service.start()
        self.resource_awareness_service.start()
        
        # Start integrations
        self.atlassian_bridge.start()
        
        logger.info("Unified AI System started successfully")
        
    def stop_system(self):
        """Stop the unified AI system"""
        logger.info("Stopping Unified AI System...")
        
        # Stop integrations
        self.atlassian_bridge.stop()
        
        # Stop external services
        self.resource_awareness_service.stop()
        self.multi_llm_service.stop()
        
        # Stop core services
        self.dialogue_manager.stop()
        self.continuous_learning_manager.stop()
        self.ham_memory_manager.stop()
        self.execution_manager.stop()
        self.agent_manager.stop()
        
        logger.info("Unified AI System stopped successfully")
        
    def process_request(self, user_id: str, request: dict) -> dict:
        """Process a user request through the unified system"""
        try:
            # Log the request
            self.audit_logger.log_operation(
                user_id=user_id,
                operation="process_request",
                resource="system",
                action="execute",
                success=True,
                details={"request_type": request.get("type", "unknown")}
            )
            
            # Check permissions
            # For now, we'll allow all requests in this simplified implementation
            # In a real system, you would check specific permissions here
            
            # Route the request based on type
            request_type = request.get("type", "unknown")
            
            if request_type == "dialogue":
                return self._handle_dialogue_request(user_id, request)
            elif request_type == "tool_execution":
                return self._handle_tool_request(user_id, request)
            elif request_type == "atlassian_operation":
                return self._handle_atlassian_request(user_id, request)
            elif request_type == "ai_editor_operation":
                return self._handle_editor_request(user_id, request)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown request type: {request_type}"
                }
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.audit_logger.log_error(
                user_id=user_id,
                error_type="request_processing_error",
                resource="system",
                error_message=str(e)
            )
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }
            
    def _handle_dialogue_request(self, user_id: str, request: dict) -> dict:
        """Handle dialogue requests"""
        try:
            message = request.get("message", "")
            context = request.get("context", {})
            
            response = self.dialogue_manager.process_message(
                user_id=user_id,
                message=message,
                context=context
            )
            
            return {
                "status": "success",
                "response": response
            }
        except Exception as e:
            logger.error(f"Error handling dialogue request: {e}")
            return {
                "status": "error",
                "message": f"Error handling dialogue request: {str(e)}"
            }
            
    def _handle_tool_request(self, user_id: str, request: dict) -> dict:
        """Handle tool execution requests"""
        try:
            tool_name = request.get("tool_name", "")
            tool_params = request.get("tool_params", {})
            
            # Execute tool in sandbox for security
            result, error = self.sandbox_executor.execute(
                user_id=user_id,
                code_string="",  # In a real implementation, this would contain the tool code
                class_name="ToolExecutor",  # Placeholder
                method_name=tool_name,
                method_params=tool_params
            )
            
            if error:
                return {
                    "status": "error",
                    "message": error
                }
            else:
                return {
                    "status": "success",
                    "result": result
                }
        except Exception as e:
            logger.error(f"Error handling tool request: {e}")
            return {
                "status": "error",
                "message": f"Error handling tool request: {str(e)}"
            }
            
    def _handle_atlassian_request(self, user_id: str, request: dict) -> dict:
        """Handle Atlassian integration requests"""
        try:
            operation = request.get("operation", "")
            params = request.get("params", {})
            
            if operation == "get_jira_projects":
                result = self.atlassian_bridge.get_jira_projects()
                return {
                    "status": "success",
                    "result": result
                }
            elif operation == "get_confluence_spaces":
                result = self.atlassian_bridge.get_confluence_spaces()
                return {
                    "status": "success",
                    "result": result
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown Atlassian operation: {operation}"
                }
        except Exception as e:
            logger.error(f"Error handling Atlassian request: {e}")
            return {
                "status": "error",
                "message": f"Error handling Atlassian request: {str(e)}"
            }
            
    def _handle_editor_request(self, user_id: str, request: dict) -> dict:
        """Handle AI editor requests"""
        try:
            operation = request.get("operation", "")
            params = request.get("params", {})
            
            if operation == "process_data":
                data = params.get("data", {})
                result = self.ai_editor_service.process_data(data)
                return {
                    "status": "success",
                    "result": result
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown editor operation: {operation}"
                }
        except Exception as e:
            logger.error(f"Error handling editor request: {e}")
            return {
                "status": "error",
                "message": f"Error handling editor request: {str(e)}"
            }

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and start the unified AI system
    unified_ai = UnifiedAISystem()
    
    try:
        unified_ai.start_system()
        
        # Example request processing
        example_request = {
            "type": "dialogue",
            "message": "Hello, how can you help me today?",
            "context": {}
        }
        
        result = unified_ai.process_request("test_user", example_request)
        print(f"Request result: {result}")
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        unified_ai.stop_system()