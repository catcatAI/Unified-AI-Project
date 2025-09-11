import asyncio
import uuid
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
import pandas as pd

from apps.backend.src.ai.agents.base.base_agent import BaseAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for data analysis tasks like statistical analysis,
    data visualization, and pattern recognition.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_statistical_analysis_v1.0",
                "name": "statistical_analysis",
                "description": "Performs statistical analysis on numerical data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True, "description": "Numerical data array for analysis"},
                    {"name": "analysis_type", "type": "string", "required": False, "description": "Type of analysis (mean, median, std, correlation)"}
                ],
                "returns": {"type": "object", "description": "Statistical analysis results."}
            },
            {
                "capability_id": f"{agent_id}_data_summary_v1.0",
                "name": "data_summary",
                "description": "Generates a summary of the provided dataset.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "object", "required": True, "description": "Dataset in JSON format"}
                ],
                "returns": {"type": "object", "description": "Dataset summary including basic statistics."}
            },
            {
                "capability_id": f"{agent_id}_pattern_recognition_v1.0",
                "name": "pattern_recognition",
                "description": "Identifies patterns and trends in the provided data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True, "description": "Time series or sequential data"},
                    {"name": "pattern_type", "type": "string", "required": False, "description": "Type of pattern to detect (trend, seasonality, anomaly)"}
                ],
                "returns": {"type": "object", "description": "Identified patterns and insights."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] DataAnalysisAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "statistical_analysis" in capability_id:
                result = self._perform_statistical_analysis(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "data_summary" in capability_id:
                result = self._generate_data_summary(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "pattern_recognition" in capability_id:
                result = self._identify_patterns(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _perform_statistical_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs statistical analysis on numerical data."""
        data = params.get('data', [])
        analysis_type = params.get('analysis_type', 'basic')
        
        if not data:
            raise ValueError("No data provided for analysis")
        
        # Convert to numpy array for easier manipulation
        try:
            np_data = np.array(data, dtype=float)
        except ValueError:
            raise ValueError("Data must be numerical")
        
        results = {
            "data_points": len(np_data),
            "analysis_type": analysis_type
        }
        
        if analysis_type == "mean" or analysis_type == "basic":
            results["mean"] = float(np.mean(np_data))
        
        if analysis_type == "median" or analysis_type == "basic":
            results["median"] = float(np.median(np_data))
        
        if analysis_type == "std" or analysis_type == "basic":
            results["std_deviation"] = float(np.std(np_data))
        
        if analysis_type == "min_max" or analysis_type == "basic":
            results["min"] = float(np.min(np_data))
            results["max"] = float(np.max(np_data))
        
        if analysis_type == "correlation" and len(np_data) > 1:
            # For correlation, we need pairs of data
            if len(np_data) % 2 == 0:
                x = np_data[:len(np_data)//2]
                y = np_data[len(np_data)//2:]
                correlation = np.corrcoef(x, y)[0, 1]
                results["correlation"] = float(correlation)
            else:
                results["correlation"] = "Insufficient data for correlation analysis"
        
        return results

    def _generate_data_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a summary of the provided dataset."""
        data = params.get('data', {})
        
        if not data:
            raise ValueError("No data provided for summary")
        
        # Convert to pandas DataFrame for easier manipulation
        try:
            df = pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Invalid data format: {e}")
        
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_types": {col: str(df[col].dtype) for col in df.columns}
        }
        
        # Add basic statistics for numerical columns
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        if len(numerical_cols) > 0:
            summary["numerical_summary"] = {}
            for col in numerical_cols:
                summary["numerical_summary"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max())
                }
        
        # Add value counts for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            summary["categorical_summary"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts().head(5)  # Top 5 values
                summary["categorical_summary"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": value_counts.to_dict()
                }
        
        return summary

    def _identify_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Identifies patterns and trends in the provided data."""
        data = params.get('data', [])
        pattern_type = params.get('pattern_type', 'trend')
        
        if not data:
            raise ValueError("No data provided for pattern recognition")
        
        # Convert to numpy array
        try:
            np_data = np.array(data, dtype=float)
        except ValueError:
            raise ValueError("Data must be numerical")
        
        results = {
            "data_points": len(np_data),
            "pattern_type": pattern_type
        }
        
        if pattern_type == "trend" or pattern_type == "basic":
            # Simple linear trend detection
            x = np.arange(len(np_data))
            slope, intercept = np.polyfit(x, np_data, 1)
            results["trend_slope"] = float(slope)
            results["trend_intercept"] = float(intercept)
            
            if slope > 0:
                results["trend_direction"] = "increasing"
            elif slope < 0:
                results["trend_direction"] = "decreasing"
            else:
                results["trend_direction"] = "stable"
        
        if pattern_type == "seasonality" or pattern_type == "basic":
            # Simple seasonality detection (check for repeating patterns)
            if len(np_data) >= 4:
                # Calculate differences between consecutive points
                diffs = np.diff(np_data)
                # Check if there's a repeating pattern in differences
                if len(diffs) >= 4:
                    # Simple check: see if first and third differences are similar
                    # and second and fourth differences are similar
                    if len(diffs) >= 4:
                        pattern_score = abs(diffs[0] - diffs[2]) + abs(diffs[1] - diffs[3])
                        results["seasonality_score"] = float(pattern_score)
                        results["has_seasonality"] = pattern_score < np.std(diffs) * 0.5
        
        if pattern_type == "anomaly" or pattern_type == "basic":
            # Simple anomaly detection using z-scores
            mean = np.mean(np_data)
            std = np.std(np_data)
            z_scores = np.abs((np_data - mean) / std)
            
            # Anomalies are points with z-score > 2
            anomalies = np.where(z_scores > 2)[0]
            results["anomalies"] = anomalies.tolist()
            results["anomaly_count"] = len(anomalies)
            results["anomaly_percentage"] = float(len(anomalies) / len(np_data) * 100)
        
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
    async def main():
        agent_id = f"did:hsp:data_analysis_agent_{uuid.uuid4().hex[:6]}"
        agent = DataAnalysisAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDataAnalysisAgent manually stopped.")