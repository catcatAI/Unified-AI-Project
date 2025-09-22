import asyncio
import uuid
import logging
import ast
import json
from typing import Dict, Any, List
from pathlib import Path

from .base_agent import BaseAgent
from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class CodeUnderstandingAgent(BaseAgent):
    """
    A specialized agent for code understanding tasks like code analysis,
    documentation generation, and code review.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_analyze_code_v1.0",
                "name": "analyze_code",
                "description": "Analyzes source code and provides insights about structure, complexity, and potential issues.",
                "version": "1.0",
                "parameters": [
                    {"name": "code", "type": "string", "required": True, "description": "Source code to analyze"},
                    {"name": "language", "type": "string", "required": False, "description": "Programming language of the code"}
                ],
                "returns": {"type": "object", "description": "Code analysis results including structure and metrics."}
            },
            {
                "capability_id": f"{agent_id}_generate_documentation_v1.0",
                "name": "generate_documentation",
                "description": "Generates documentation for the provided source code.",
                "version": "1.0",
                "parameters": [
                    {"name": "code", "type": "string", "required": True, "description": "Source code to document"},
                    {"name": "style", "type": "string", "required": False, "description": "Documentation style (e.g., 'technical', 'user')"}
                ],
                "returns": {"type": "string", "description": "Generated documentation."}
            },
            {
                "capability_id": f"{agent_id}_code_review_v1.0",
                "name": "code_review",
                "description": "Performs a code review and suggests improvements.",
                "version": "1.0",
                "parameters": [
                    {"name": "code", "type": "string", "required": True, "description": "Source code to review"},
                    {"name": "review_criteria", "type": "array", "required": False, "description": "Specific criteria for the review"}
                ],
                "returns": {"type": "object", "description": "Code review results with suggestions."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logger.info(f"[{self.agent_id}] CodeUnderstandingAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logger.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "analyze_code" in capability_id:
                result = self._analyze_code(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "generate_documentation" in capability_id:
                result = self._generate_documentation(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "code_review" in capability_id:
                result = self._perform_code_review(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logger.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _analyze_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes source code and provides insights."""
        code = params.get('code', '')
        language = params.get('language', 'python')
        
        if not code:
            raise ValueError("No code provided for analysis")
        
        analysis = {
            "language": language,
            "lines_of_code": len(code.splitlines()),
            "character_count": len(code),
            "has_comments": '#' in code or '//' in code or '/*' in code
        }
        
        # Language-specific analysis
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                analysis["syntax_valid"] = True
                analysis["function_count"] = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                analysis["class_count"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                analysis["import_count"] = len([node for node in ast.walk(tree) if isinstance(node, ast.Import)])
                analysis["import_from_count"] = len([node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)])
                
                # Calculate complexity (simple approximation)
                complexity = 1  # Base complexity
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                analysis["cyclomatic_complexity"] = complexity
                
            except SyntaxError as e:
                analysis["syntax_valid"] = False
                analysis["syntax_error"] = str(e)
            except Exception as e:
                analysis["analysis_error"] = str(e)
        
        return analysis

    def _generate_documentation(self, params: Dict[str, Any]) -> str:
        """Generates documentation for the provided source code."""
        code = params.get('code', '')
        style = params.get('style', 'technical')
        
        if not code:
            raise ValueError("No code provided for documentation")
        
        # Simple documentation generation based on code analysis
        lines = code.splitlines()
        doc_lines = []
        
        # Add header
        doc_lines.append(f"# {'Technical' if style == 'technical' else 'User'} Documentation")
        doc_lines.append("")
        
        # Analyze code structure
        if 'def ' in code:
            doc_lines.append("## Functions")
            for line in lines:
                if line.strip().startswith('def '):
                    func_name = line.strip().split('(')[0].replace('def ', '')
                    doc_lines.append(f"- `{func_name}`: Function description")
            doc_lines.append("")
        
        if 'class ' in code:
            doc_lines.append("## Classes")
            for line in lines:
                if line.strip().startswith('class '):
                    class_name = line.strip().split('(')[0].replace('class ', '')
                    doc_lines.append(f"- `{class_name}`: Class description")
            doc_lines.append("")
        
        # Add general information
        doc_lines.append("## Code Statistics")
        doc_lines.append(f"- Lines of code: {len(lines)}")
        doc_lines.append(f"- Characters: {len(code)}")
        doc_lines.append("")
        
        # Add usage examples (generic)
        doc_lines.append("## Usage Examples")
        doc_lines.append("```python")
        doc_lines.append("# Example usage:")
        doc_lines.append("# result = function_name(parameters)")
        doc_lines.append("```")
        
        return "\n".join(doc_lines)

    def _perform_code_review(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs a code review and suggests improvements."""
        code = params.get('code', '')
        review_criteria = params.get('review_criteria', [])
        
        if not code:
            raise ValueError("No code provided for review")
        
        review = {
            "review_date": str(uuid.uuid4().hex[:8]),
            "code_lines": len(code.splitlines()),
            "findings": [],
            "score": 100  # Start with perfect score
        }
        
        lines = code.splitlines()
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            line_strip = line.strip()
            
            # Check for lines too long (PEP 8)
            if len(line) > 79:
                review["findings"].append({
                    "line": i,
                    "issue": "Line too long",
                    "severity": "medium",
                    "suggestion": "Break line into multiple lines (< 79 characters)"
                })
                review["score"] -= 1
            
            # Check for TODO comments
            if "TODO" in line:
                review["findings"].append({
                    "line": i,
                    "issue": "TODO comment found",
                    "severity": "low",
                    "suggestion": "Address TODO or create a task for it"
                })
            
            # Check for print statements (in production code)
            if line_strip.startswith("print("):
                review["findings"].append({
                    "line": i,
                    "issue": "Print statement found",
                    "severity": "medium",
                    "suggestion": "Use logging instead of print for production code"
                })
                review["score"] -= 1
            
            # Check for commented out code
            if line_strip.startswith("#") and any(c.isalnum() for c in line_strip[1:]) and "=" in line_strip:
                review["findings"].append({
                    "line": i,
                    "issue": "Possibly commented out code",
                    "severity": "low",
                    "suggestion": "Remove commented out code or add explanation"
                })
        
        # Check for missing docstrings
        if "def " in code and '"""' not in code and "'''" not in code:
            review["findings"].append({
                "line": None,
                "issue": "Missing docstrings",
                "severity": "medium",
                "suggestion": "Add docstrings to functions and classes"
            })
            review["score"] -= 5
        
        # Ensure score doesn't go below 0
        review["score"] = max(0, review["score"])
        
        return review

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
        agent_id = f"did:hsp:code_understanding_agent_{uuid.uuid4().hex[:6]}"
        agent = CodeUnderstandingAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCodeUnderstandingAgent manually stopped.")