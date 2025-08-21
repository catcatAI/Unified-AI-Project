"""
DataAnalysisAgent - A specialized agent for data analysis tasks.
This agent is automatically available as a default agent in the system.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataAnalysisAgent:
    """A specialized agent for data analysis tasks."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.capabilities = [
            {
                "capability_id": "data_analysis_v1",
                "name": "CSV Data Analyzer",
                "description": "Analyze CSV content and provide summaries",
            }
        ]
        self.agent_name = "DataAnalysisAgent"
        self.hsp_connector = None
        self.tool_dispatcher = None
        self.is_running = False

    async def start(self) -> bool:
        """Start the agent."""
        self.is_running = True
        logger.info(f"DataAnalysisAgent {self.agent_id} started")
        return True

    async def stop(self) -> bool:
        """Stop the agent."""
        self.is_running = False
        logger.info(f"DataAnalysisAgent {self.agent_id} stopped")
        return True

    async def handle_task_request(self, payload: Dict[str, Any], sender_ai_id: str, envelope: Dict[str, Any]):
        """Handle incoming task requests."""
        try:
            request_id = payload.get("request_id")
            parameters = payload.get("parameters", {})
            callback_address = payload.get("callback_address", "")
            csv_content = parameters.get("csv_content", "")
            
            if not csv_content:
                await self._send_task_result(request_id, "failure", "No CSV content provided", callback_address)
                return

            # Simple CSV analysis
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:  # Need at least header + 1 data row
                await self._send_task_result(request_id, "failure", "CSV analysis failed: Invalid CSV format", callback_address)
                return

            # Check if all rows have the same number of columns
            header_cols = len(lines[0].split(','))
            for i, line in enumerate(lines[1:], 1):
                if len(line.split(',')) != header_cols:
                    await self._send_task_result(request_id, "failure", f"CSV analysis failed: Row {i+1} has {len(line.split(','))} columns, expected {header_cols}", callback_address)
                    return

            # Count data rows (excluding header)
            data_rows = len(lines) - 1
            result = f"Dummy analysis: Summarized {data_rows} lines of CSV data."
            
            await self._send_task_result(request_id, "success", result, callback_address)
            
        except Exception as e:
            logger.error(f"Error handling task request: {e}")
            await self._send_task_result(request_id, "failure", f"CSV analysis failed: {str(e)}", callback_address)

    async def _send_task_result(self, request_id: str, status: str, payload: str, callback_address: str):
        """Send task result back via HSP connector."""
        if not self.hsp_connector:
            logger.error("No HSP connector available")
            return

        try:
            result_payload = {
                "request_id": request_id,
                "status": status,
                "payload": payload
            }
            
            # Send via HSP connector
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)
            
        except Exception as e:
            logger.error(f"Error sending task result: {e}")


# For compatibility with AgentManager that expects a main function
if __name__ == "__main__":
    import asyncio
    import sys
    import os
    
    # Add the src directory to the path
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    
    from src.hsp.connector import HSPConnector
    from src.tools.tool_dispatcher import ToolDispatcher
    
    async def main():
        """Main function for running the agent as a standalone process."""
        agent_id = "data_analysis_agent_001"
        agent = DataAnalysisAgent(agent_id)
        
        # Initialize HSP connector
        hsp_connector = HSPConnector(agent_id, "127.0.0.1", 1883)
        tool_dispatcher = ToolDispatcher()
        
        agent.hsp_connector = hsp_connector
        agent.tool_dispatcher = tool_dispatcher
        
        await agent.start()
        
        # Connect to HSP
        await hsp_connector.connect()
        
        # Register task handler
        hsp_connector.register_on_task_request_callback(agent.handle_task_request)
        
        # Advertise capabilities
        for capability in agent.capabilities:
            await hsp_connector.advertise_capability(capability)
        
        print(f"DataAnalysisAgent {agent_id} is running...")
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await agent.stop()
            await hsp_connector.disconnect()
    
    asyncio.run(main())