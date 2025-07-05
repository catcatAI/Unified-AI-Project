import re
from typing import Dict, Any, Optional

# Assuming 'src' is in PYTHONPATH, making 'tools', 'core_ai', 'services' top-level packages
from tools.math_tool import calculate as math_calculate
from tools.logic_tool import evaluate_expression as logic_evaluate
from tools.translation_tool import translate as translate_text
from tools.code_understanding_tool import CodeUnderstandingTool # Added
from core_ai.language_models.daily_language_model import DailyLanguageModel
from services.llm_interface import LLMInterface # Added Optional import for type hint consistency

class ToolDispatcher:
    def __init__(self, llm_interface: Optional[LLMInterface] = None): # Allow passing LLMInterface
        # If DLM needs a non-default LLMInterface, it should be passed here
        # For now, DLM will create its own default LLMInterface if none is provided to it.
        self.dlm = DailyLanguageModel(llm_interface=llm_interface) # LLMInterface is correctly found by DLM due to its own imports
        self.code_understanding_tool_instance = CodeUnderstandingTool() # Added instance

        self.tools = {
            "calculate": self._execute_math_calculation,
            "evaluate_logic": self._execute_logic_evaluation,
            "translate_text": self._execute_translation, # Corrected from self.execute_translation
            "inspect_code": self._execute_code_inspection, # Added tool
        }
        self.tool_descriptions = {
            "calculate": "Performs arithmetic calculations. Example: 'calculate 10 + 5', or 'what is 20 / 4?'",
            "evaluate_logic": "Evaluates simple logical expressions (AND, OR, NOT, true, false, parentheses). Example: 'evaluate true AND (false OR NOT true)'",
            "translate_text": "Translates text between Chinese and English. Example: 'translate 你好 to English'",
            "inspect_code": "Describes the structure of available tools. Query examples: 'list_tools', or 'describe_tool math_tool'", # Added description
        }
        print("ToolDispatcher initialized.")
        print(f"Available tools: {list(self.tools.keys())}")

    def _execute_code_inspection(self, query: str, **kwargs) -> str:
        """
        Wrapper for the CodeUnderstandingTool.
        Parses action and tool_name from query if not provided in kwargs.
        """
        action = kwargs.get("action")
        tool_name_param = kwargs.get("tool_name")

        if not action: # Try to parse from query
            parts = query.strip().split(maxsplit=1)
            action = parts[0].lower() if parts else None # Ensure action is lowercase for consistent matching
            if len(parts) > 1:
                tool_name_param = parts[1]

        if not action:
            return "Error: No action specified for code inspection. Use 'list_tools' or 'describe_tool <tool_name>'."

        try:
            return self.code_understanding_tool_instance.execute(action=action, tool_name=tool_name_param)
        except Exception as e:
            print(f"Error executing code inspection tool: {e}")
            # It's good practice to log the full exception, e.g., import traceback; traceback.print_exc()
            return f"Sorry, I encountered an error trying to inspect code: {str(e)[:100]}" # Truncate error for brevity in response


    def _execute_math_calculation(self, query: str, **kwargs) -> str:
        """
        Wrapper for the math_tool.calculate function.
        'query' is expected to be the direct arithmetic expression.
        kwargs might include 'original_query'.
        """
        # The `query` parameter here is what DLM extracted as the math expression.
        # `math_calculate` expects the natural language query to parse itself,
        # or a direct expression. If DLM provides a clean expression in `query`,
        # it should work. If DLM provides the original text, `math_calculate` will parse.
        print(f"ToolDispatcher._execute_math_calculation: query='{query}', kwargs={kwargs}")
        try:
            # If DLM is good, 'query' is the expression. math_tool.calculate can handle direct expressions too.
            # If math_tool.calculate is enhanced to take only clean expressions, this is fine.
            # Current math_tool.calculate also tries to extract from natural language.
            return math_calculate(query)
        except Exception as e:
            print(f"Error executing math calculation tool: {e}")
            return "Sorry, I encountered an error trying to calculate that."

    def _execute_logic_evaluation(self, query: str, method: str = 'parser') -> str:
        """
        Wrapper for the logic_tool.evaluate_expression function.
        The query should be the logical expression string itself.
        The 'method' kwarg allows specifying 'parser' or 'nn'.
        """
        try:
            # logic_evaluate expects the expression string directly.
            # More advanced parsing to extract expression from natural language could be added here or in logic_tool.
            # For now, assume query IS the expression or pre-extracted.
            # If the query is "evaluate true AND false", we need to pass "true AND false"

            # Attempt to extract the core logical expression if prefixed
            # e.g., "evaluate true AND false" -> "true AND false"
            # e.g., "logic: (true OR false)" -> "(true OR false)"
            match_evaluate = re.match(r"(?:evaluate|logic:)\s*(.*)", query, re.IGNORECASE)
            if match_evaluate:
                expression_to_evaluate = match_evaluate.group(1).strip()
            else:
                expression_to_evaluate = query # Assume the query is the expression

            result = logic_evaluate(expression_to_evaluate, method=method)
            return f"Result: {result}" # Wrap boolean in a string for consistent tool output type
        except Exception as e:
            print(f"Error executing logic evaluation tool: {e}")
            return "Sorry, I encountered an error trying to evaluate that logical expression."

    def _execute_translation(self, query: str, **kwargs) -> str:
        """
        Wrapper for the translation_tool.translate function.
        Extracts text and target language from query.
        Example query: "translate 'Hello world' to Chinese"
        Can also be called with explicit text and target_language in kwargs.
        """
        try:
            # print(f"Debug TRANSLATE: _execute_translation called with query='{query}', kwargs={kwargs}") # REMOVED DEBUG
            text_to_translate = query # Default: query is the text
            target_lang_from_kwarg = kwargs.get("target_language")
            source_lang_from_kwarg = kwargs.get("source_language")
            # print(f"Debug TRANSLATE: target_lang_from_kwarg='{target_lang_from_kwarg}', source_lang_from_kwarg='{source_lang_from_kwarg}'") # REMOVED DEBUG

            resolved_target_lang = "en" # Overall default

            if target_lang_from_kwarg:
                resolved_target_lang = target_lang_from_kwarg
                # print(f"Debug TRANSLATE: Using target_language from kwargs: {resolved_target_lang}") # REMOVED DEBUG
                # text_to_translate is already query
            else:
                # No target_language in kwargs, parse from query string
                # Initial default for resolved_target_lang (if "to LANG" isn't found)
                # print(f"Debug TRANSLATE: Initial resolved_target_lang (before query parse) = {resolved_target_lang}") # REMOVED DEBUG

                # Pattern 1: "translate 'TEXT' to LANGUAGE" or "translate TEXT to LANGUAGE"
                pattern1_match = re.search(r"translate\s+(?:['\"](.+?)['\"]|(.+?))\s+to\s+([a-zA-Z\-]+)", query, re.IGNORECASE)
                if pattern1_match:
                    text_to_translate = pattern1_match.group(1) or pattern1_match.group(2)
                    text_to_translate = text_to_translate.strip()
                    lang_name_or_code = pattern1_match.group(3).lower()
                    if lang_name_or_code in ["chinese", "zh"]: resolved_target_lang = "zh"
                    elif lang_name_or_code in ["english", "en"]: resolved_target_lang = "en"
                    else: resolved_target_lang = lang_name_or_code
                else:
                    # Pattern 2: "'TEXT' in LANGUAGE" or "TEXT in LANGUAGE"
                    pattern2_match = re.search(r"(?:['\"](.+?)['\"]|(.+?))\s+in\s+([a-zA-Z\-]+)", query, re.IGNORECASE)
                    if pattern2_match:
                        text_to_translate = pattern2_match.group(1) or pattern2_match.group(2)
                        text_to_translate = text_to_translate.strip()
                        lang_name_or_code = pattern2_match.group(3).lower()
                        if lang_name_or_code in ["chinese", "zh"]: resolved_target_lang = "zh"
                        elif lang_name_or_code in ["english", "en"]: resolved_target_lang = "en"
                        else: resolved_target_lang = lang_name_or_code
                    else:
                        # Pattern 3: Fallback "translate TEXT"
                        # Here, `to_lang_match` was an attempt to find "to LANG" anywhere in the query.
                        # Let's use that if available, otherwise default.
                        to_lang_match_general = re.search(r"to\s+([a-zA-Z\-]+)", query, re.IGNORECASE)
                        if to_lang_match_general:
                            lang_name_or_code = to_lang_match_general.group(1).lower()
                            if lang_name_or_code in ["chinese", "zh"]: resolved_target_lang = "zh"
                            elif lang_name_or_code in ["english", "en"]: resolved_target_lang = "en"
                            else: resolved_target_lang = lang_name_or_code
                        # else resolved_target_lang remains its default ("en")

                        text_simple_match = re.match(r"translate\s+(.+)", query, re.IGNORECASE)
                        if text_simple_match:
                            text_to_translate = text_simple_match.group(1).strip()
                            # Remove "to lang" part if it was part of this simple match
                            if to_lang_match_general and text_to_translate.lower().endswith(f" to {to_lang_match_general.group(1).lower()}"):
                                text_to_translate = text_to_translate[:-(len(f" to {to_lang_match_general.group(1).lower()}"))].strip()

                        else: # Cannot determine text to translate from query string if not using kwargs
                             return "Sorry, I couldn't understand what text to translate from the query."

            if not text_to_translate: # Ensure text is not empty
                 return "Sorry, no text to translate was found."

            # Use source_lang_from_kwarg if provided, otherwise it's None (for auto-detect)
            # print(f"Debug TRANSLATE: Before calling translate_text: text='{text_to_translate}', resolved_target_lang='{resolved_target_lang}', source_language='{source_lang_from_kwarg}'") # REMOVED DEBUG
            return translate_text(text_to_translate, resolved_target_lang, source_language=source_lang_from_kwarg)

        except Exception as e:
            print(f"Error executing translation tool: {e}")
            return "Sorry, I encountered an error trying to translate that."


    # def _execute_another_tool(self, query: str, **kwargs) -> str:
    #     try:
    #         # Example: return run_another_tool(query)
    #         pass
    #     except Exception as e:
    #         print(f"Error executing another_tool: {e}")
    #         return "Error with another_tool."

    def dispatch(self, query: str, explicit_tool_name: str = None, **kwargs) -> str | None:
        """
        Dispatches a query to the appropriate tool.
        If explicit_tool_name is provided, it uses that tool.
        Otherwise, it tries to infer the tool from the query.
        """
        if explicit_tool_name:
            if explicit_tool_name in self.tools:
                print(f"Dispatching to explicitly named tool: {explicit_tool_name}")
                # print(f"Debug DISPATCH: kwargs before tool call = {kwargs}") # REMOVED DEBUG
                return self.tools[explicit_tool_name](query, **kwargs)
            else:
                return f"Sorry, I don't know the tool named '{explicit_tool_name}'."

        # Use DLM for intent recognition
        intent = self.dlm.recognize_intent(query)

        if intent and intent.get("tool_name") in self.tools:
            tool_name_from_dlm = intent["tool_name"]
            tool_params = intent.get("parameters", {})
            # The query for the tool methods might be different from the original user query.
            # DLM extracts a "query" parameter if it can isolate it.
            # Default to original user query if specific "query" param not extracted by DLM.
            tool_specific_query = tool_params.get("query", query)

            print(f"Dispatching to '{tool_name_from_dlm}' tool based on DLM intent. Effective query: '{tool_specific_query}'")

            # Special handling for logic tool's 'method' parameter if needed,
            # or assume DLM can provide it in tool_params.
            # For now, _execute_logic_evaluation default to 'parser'.
            # If DLM provides 'method' in params, it could be passed via **tool_params.
            if tool_name_from_dlm == "evaluate_logic":
                 return self.tools[tool_name_from_dlm](tool_specific_query, method=tool_params.get("method", "parser"))
            elif tool_name_from_dlm == "translate_text":
                # _execute_translation expects the full query string as its first positional argument 'query'.
                # Other extracted parameters by DLM (like 'target_language_hint', 'text_to_translate_hint')
                # can be passed as kwargs. We must avoid passing 'query' or 'original_query' also via **tool_params
                # if tool_specific_query is already the original query.
                kwargs_for_tool = {k: v for k, v in tool_params.items() if k not in ["query", "original_query"]}
                return self.tools[tool_name_from_dlm](tool_specific_query, **kwargs_for_tool)
            else: # For 'calculate' and other future tools that just take the query string
                return self.tools[tool_name_from_dlm](tool_specific_query)

        print(f"No specific tool inferred by DLM for query: '{query}'")
        return None

    def get_available_tools(self):
        """Returns a dictionary of available tools and their descriptions."""
        return self.tool_descriptions

# Example Usage
if __name__ == '__main__':
    # For ToolDispatcher __main__ test, we can use the PatchedLLMInterface from DLM's test
    # This requires some path adjustments or making PatchedLLMInterface more accessible.
    # For simplicity here, we'll rely on DLM using its default LLMInterface (which is mock).
    # The DLM's __main__ has a more sophisticated mock for testing intent recognition.
    # This ToolDispatcher __main__ will test the flow with whatever the default DLM->LLMInterface provides.

    print("--- ToolDispatcher Test ---")
    dispatcher = ToolDispatcher() # This will use default LLMInterface (mock) for its DLM

    print("\nAvailable tools:")
    for name, desc in dispatcher.get_available_tools().items():
        print(f"- {name}: {desc}")

    queries = [
        "calculate 123 + 456",
        "what is 7 * 6?",
        "compute 100 / 4",
        "What is the weather like?", # Should not be handled by math
        "Solve 2x + 5 = 10", # More complex, current math tool won't solve algebra
        "10 - 3"
    ]

    for q in queries:
        print(f"\nQuery: \"{q}\"")
        result = dispatcher.dispatch(q)
        if result:
            print(f"Tool Dispatcher Result: {result}")
        else:
            print("Tool Dispatcher: No tool could handle this query or no specific tool inferred.")

    print("\nTesting explicit tool dispatch:")
    explicit_query = "what is 50 + 50"
    print(f"Query: \"{explicit_query}\", Tool: calculate")
    result = dispatcher.dispatch(explicit_query, explicit_tool_name="calculate")
    print(f"Tool Dispatcher Result: {result}")

    non_tool_query = "hello world"
    print(f"\nQuery: \"{non_tool_query}\"")
    result = dispatcher.dispatch(non_tool_query)
    if result:
        print(f"Tool Dispatcher Result: {result}")
    else:
        print("Tool Dispatcher: No tool could handle this query or no specific tool inferred.")
