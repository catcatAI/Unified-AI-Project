"""Daily Language Model Module - Fixed Version

Provides daily conversation language model capabilities.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class InteractionRecord:
    """记录用户交互的数据类"""
    timestamp: datetime
    user_input: str
    intent: Dict[str, Any]
    response: str
    feedback: Optional[Dict[str, Any]] = None


class DailyLanguageModel:
    """Daily conversation language model"""
    
    def __init__(self, llm_service=None, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.llm_service = llm_service
        self.dna_chains: Dict[str, Any] = {}  # DNA数据链存储
        self.interaction_history: List[InteractionRecord] = []  # 交互历史记录
        self.intent_accuracy = 0.0  # 意图识别准确率
        self.total_interactions = 0  # 总交互次数
        
        if llm_service is None:
            print("DailyLanguageModel: No LLM Service provided, will use mock responses.")
        else:
            print("DailyLanguageModel: Initialized with LLMInterface.")
    
    def set_llm_service(self, llm_service):
        """Inject or replace the LLM service at runtime (used by hot reload)."""
        self.llm_service = llm_service
    
    def _construct_tool_selection_prompt(self, text: str, available_tools: Dict[str, str]) -> str:
        """构建工具选择提示词"""
        prompt = "You are an expert at routing user queries to the correct tool.\n"
        prompt += "Given the user query and a list of available tools, "
        prompt += "select the most appropriate tool and extract necessary parameters.\n"
        prompt += 'If no tool is appropriate, respond with "NO_TOOL".\n\n'
        
        prompt += "Available tools:\n"
        for i, (tool_name, description) in enumerate(available_tools.items()):
            prompt += f"{i + 1}. {tool_name}: {description}\n"
        
        prompt += f'\nUser Query: "{text}"\n\n'
        prompt += "Respond ONLY with a valid JSON object adhering to the following structure:\n"
        prompt += '{\n'
        prompt += '  "tool_name": "<selected_tool_name_or_NO_TOOL>",\n'
        prompt += '  "parameters": {<parameters_object_for_the_tool_OR_null_OR_empty_object>}\n'
        prompt += '}\n\n'
        
        prompt += "Specific instructions for the 'parameters' object based on 'tool_name':\n"
        prompt += "- If 'NO_TOOL' is selected, 'parameters' should be null or an empty object.\n"
        prompt += "- For 'calculate': 'parameters' must be an object like {\"query\": \"<arithmetic_expression>\"}.\n"
        prompt += "- For 'evaluate_logic': 'parameters' must be an object like {\"query\": \"<logical_expression>\"}.\n"
        prompt += "- For 'translate_text': 'parameters' must contain {\"text\": \"...\", \"target\": \"...\"}.\n\n"
        prompt += "Only include parameters relevant to the selected tool."
        
        return prompt
    
    async def recognize_intent(self, text: str, available_tools: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Recognizes intent (primarily for tool dispatching) from input text using an LLM.
        Returns a dictionary like {"tool_name": "...", "parameters": {"query": "...", ...}}
        or {"tool_name": None, "parameters": None} if no tool is suitable.
        """
        if not available_tools:
            return {"tool_name": None, "parameters": None, "confidence": 0.0}
        
        prompt = self._construct_tool_selection_prompt(text, available_tools)
        
        # If no LLM service, use simple keyword matching
        if self.llm_service is None:
            return self._simple_intent_recognition(text, available_tools)
        
        try:
            # Call LLM to recognize intent
            response = await self.llm_service.generate(prompt)
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response)
                if result.get("tool_name") == "NO_TOOL":
                    result["tool_name"] = None
                return result
            except json.JSONDecodeError:
                # Fallback to simple matching
                return self._simple_intent_recognition(text, available_tools)
        
        except Exception as e:
            print(f"Error in recognize_intent: {e}")
            return self._simple_intent_recognition(text, available_tools)
    
    def _simple_intent_recognition(self, text: str, available_tools: Dict[str, str]) -> Dict[str, Any]:
        """Simple keyword-based intent recognition as fallback"""
        text_lower = text.lower()
        
        # Simple keyword matching
        for tool_name in available_tools.keys():
            if tool_name.lower() in text_lower:
                return {
                    "tool_name": tool_name,
                    "parameters": {"query": text},
                    "confidence": 0.5
                }
        
        # Check for common patterns
        if any(word in text_lower for word in ['calculate', 'compute', 'math', 'add', 'subtract', 'multiply', 'divide']):
            if 'calculate' in available_tools:
                return {"tool_name": "calculate", "parameters": {"query": text}, "confidence": 0.6}
        
        if any(word in text_lower for word in ['translate', 'translation', 'language']):
            if 'translate' in available_tools:
                return {"tool_name": "translate", "parameters": {"text": text}, "confidence": 0.6}
        
        return {"tool_name": None, "parameters": None, "confidence": 0.0}
    
    async def chat(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Main chat interface"""
        context = context or {}
        
        # Record interaction
        record = InteractionRecord(
            timestamp=datetime.now(),
            user_input=user_input,
            intent={},
            response="",
            feedback=None
        )
        
        if self.llm_service:
            try:
                response = await self.llm_service.chat_completion([{
                    "role": "user",
                    "content": user_input
                }])
                record.response = response
            except Exception as e:
                record.response = f"Sorry, I encountered an error: {str(e)}"
        else:
            record.response = "I'm listening, but I don't have a language model connected yet."
        
        self.interaction_history.append(record)
        self.total_interactions += 1
        
        return record.response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "total_interactions": self.total_interactions,
            "intent_accuracy": self.intent_accuracy,
            "history_size": len(self.interaction_history),
            "dna_chains": len(self.dna_chains)
        }
