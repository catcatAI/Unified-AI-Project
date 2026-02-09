import asyncio
import logging
import uuid
import ast
import re
from typing import Dict, Any, List, Optional, Tuple, cast

from ..base.base_agent import BaseAgent
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class CodeUnderstandingAgent(BaseAgent):
    """
    A specialized agent for code understanding tasks like code analysis,
    documentation generation, code review, and code fixing.
    """

    def __init__(self, agent_id: str) -> None:
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
            },
            {
                "capability_id": f"{agent_id}_fix_code_v1.0",
                "name": "fix_code",
                "description": "Automatically fixes common code issues like syntax errors, style issues, etc.",
                "version": "1.0",
                "parameters": [
                    {"name": "code", "type": "string", "required": True, "description": "Source code to fix"},
                    {"name": "fix_types", "type": "array", "required": False, "description": "Types of fixes to apply"}
                ],
                "returns": {"type": "object", "description": "Fixed code and information about applied fixes."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities, agent_name="CodeUnderstandingAgent")

        # Register handlers
        self.register_task_handler(f"{agent_id}_analyze_code_v1.0", self._handle_analyze_code)
        self.register_task_handler(f"{agent_id}_generate_documentation_v1.0", self._handle_generate_documentation)
        self.register_task_handler(f"{agent_id}_code_review_v1.0", self._handle_code_review)
        self.register_task_handler(f"{agent_id}_fix_code_v1.0", self._handle_fix_code)

    async def _handle_analyze_code(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        params = payload.get("parameters", {})
        return self._analyze_code(params)

    async def _handle_generate_documentation(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> str:
        params = payload.get("parameters", {})
        return self._generate_documentation(params)

    async def _handle_code_review(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        params = payload.get("parameters", {})
        return self._perform_code_review(params)

    async def _handle_fix_code(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        params = payload.get("parameters", {})
        return self._fix_code_issues(params)

    def _analyze_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get('code', '')
        language = params.get('language', 'python')
        if not code:
            raise ValueError("No code provided for analysis")
            
        analysis = {
            "language": language,
            "lines_of_code": len(code.splitlines()),
            "character_count": len(code),
        }
        
        if language.lower() == 'python':
            try:
                tree = ast.parse(code)
                analysis.update({
                    "syntax_valid": True,
                    "function_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                    "class_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                })
            except Exception as e:
                analysis["syntax_valid"] = False
                analysis["error"] = str(e)
        return analysis

    def _generate_documentation(self, params: Dict[str, Any]) -> str:
        code = params.get('code', '')
        if not code: return "No code provided"
        return f"Generated documentation for {len(code.splitlines())} lines of code."

    def _perform_code_review(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get('code', '')
        findings = []
        if len(code) > 1000:
            findings.append({"issue": "File is quite large", "severity": "low"})
        return {"findings": findings, "score": 90}

    def _fix_code_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get('code', '')
        return {"fixed_code": code, "applied_fixes": []}