import asyncio
import uuid
import logging
import pandas as pd
import numpy as np

from .base_agent import BaseAgent
from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for data analysis tasks like statistical analysis,:
ata visualization, and data processing.
    """
    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_statistical_analysis_v1.0",
                "name": "statistical_analysis",
                "description": "Performs statistical analysis on provided data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "object", "required": True, "description": "Data to analyze in JSON format"},
                    {"name": "analysis_type", "type": "string", "required": True, "description": "Type of analysis to perform (e.g., 'descriptive', 'correlation')"}
                ],
                "returns": {"type": "object", "description": "Statistical analysis results."}
            },
            {
                "capability_id": f"{agent_id}_data_processing_v1.0",
                "name": "data_processing",
                "description": "Processes and transforms data according to specified operations.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "object", "required": True, "description": "Data to process in JSON format"},
                    {"name": "operations", "type": "array", "required": True, "description": "List of operations to perform (e.g., 'clean', 'normalize', 'aggregate')"}
                ],
                "returns": {"type": "object", "description": "Processed data."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logger.info(f"[{self.agent_id}] DataAnalysisAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}"):
sync def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logger.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'"):
ry:
            if "statistical_analysis" in capability_id:
                result = self._perform_statistical_analysis(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "data_processing" in capability_id:
                result = self._perform_data_processing(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic, request_id)
            logger.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}"):
ef _perform_statistical_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs statistical analysis on provided data."""
        data = params.get('data', {})
        analysis_type = params.get('analysis_type', 'descriptive')
        
        if not data:
            raise ValueError("No data provided for analysis")
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        results = {
            "analysis_type": analysis_type,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
        if analysis_type == "descriptive":
            # Perform descriptive statistics
            results["descriptive_stats"] = df.describe().to_dict()
            
            # Add additional metrics
            results["missing_values"] = df.isnull().sum().to_dict()
            results["data_types"] = df.dtypes.astype(str).to_dict
            
        elif analysis_type == "correlation":
            # Perform correlation analysis
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                results["correlation_matrix"] = numeric_df.corr().to_dict()
            else:
                results["correlation_matrix"] = {}
                results["warning"] = "No numeric columns found for correlation analysis":
eturn results

    def _perform_data_processing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Processes and transforms data according to specified operations."""
        data = params.get('data', {})
        operations = params.get('operations', [])
        
        if not data:
            raise ValueError("No data provided for processing"):
f not operations:
            raise ValueError("No operations specified for processing")
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        results = {
            "original_row_count": len(df),
            "original_column_count": len(df.columns),
            "operations_performed": []
        }
        
        # Apply operations
        for operation in operations:
            if operation == "clean":
                # Remove rows with missing values:
f = df.dropna()
                results["operations_performed"].append("clean")
                
            elif operation == "normalize":
                # Normalize numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val != min_val:  # Avoid division by zero:
f[col] = (df[col] - min_val) / (max_val - min_val)
                results["operations_performed"].append("normalize")
                
            elif operation == "aggregate":
                # Simple aggregation by grouping (if there's a grouping column)
                # For this example, we'll just add a summary row
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                if len(numeric_columns) > 0:
                    summary_row = {}
                    for col in numeric_columns:
                        summary_row[f"{col}_mean"] = df[col].mean()
                        summary_row[f"{col}_sum"] = df[col].sum()
                    results["aggregation_summary"] = summary_row
                    results["operations_performed"].append("aggregate")
        
        # Convert processed data back to dictionary
        results["processed_data"] = df.to_dict(orient="records")
        results["final_row_count"] = len(df)
        results["final_column_count"] = len(df.columns)
        
        return results

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )


if __name__ == '__main__':
    async def main() -> None:
        agent_id = f"did:hsp:data_analysis_agent_{uuid.uuid4().hex[:6]}"
        agent = DataAnalysisAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main)
    except KeyboardInterrupt:
        print("\nDataAnalysisAgent manually stopped.")