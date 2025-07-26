import re
from typing import Dict, Any, Optional, Callable # Added Callable

# Assuming 'src' is in PYTHONPATH, making 'tools', 'core_ai', 'services' top-level packages
# Correcting imports to be absolute from project root (assuming /app is project root)
from src.tools.math_tool import calculate as math_calculate
from src.tools.logic_tool import evaluate_expression as logic_evaluate
from src.tools.translation_tool import translate as translate_text
from src.tools.code_understanding_tool import CodeUnderstandingTool
from src.tools.csv_tool import CsvTool
from src.tools.image_generation_tool import ImageGenerationTool
from src.core_ai.language_models.daily_language_model import DailyLanguageModel
from src.services.llm_interface import LLMInterface
from src.shared.types.common_types import ToolDispatcherResponse # Import new response type
from typing import Literal # For literal status types
# from src.core_ai.rag.rag_manager import RAGManager

class ToolDispatcher:
    def __init__(self, llm_interface: Optional[LLMInterface] = None):
        self.dlm = DailyLanguageModel(llm_interface=llm_interface)
        self.code_understanding_tool_instance = CodeUnderstandingTool()
        self.csv_tool_instance = CsvTool()
        self.image_generation_tool_instance = ImageGenerationTool()

        self.tools: Dict[str, Callable[..., ToolDispatcherResponse]] = { # type: ignore
            "calculate": self._execute_math_calculation,
            "evaluate_logic": self._execute_logic_evaluation,
            "translate_text": self._execute_translation,
            "inspect_code": self._execute_code_inspection,
            "rag_query": self._execute_rag_query,
            "analyze_csv": self._execute_csv_analysis,
            "create_image": self._execute_image_creation,
        }
        self.tool_descriptions = {
            "calculate": "Performs arithmetic calculations. Example: 'calculate 10 + 5', or 'what is 20 / 4?'",
            "evaluate_logic": "Evaluates simple logical expressions (AND, OR, NOT, true, false, parentheses). Example: 'evaluate true AND (false OR NOT true)'",
            "translate_text": "Translates text between Chinese and English. Example: 'translate 你好 to English'",
            "inspect_code": "Describes the structure of available tools. Query examples: 'list_tools', or 'describe_tool math_tool'",
            "rag_query": "Performs a retrieval-augmented generation query. Example: 'rag_query what is the main purpose of HAM?'",
            "analyze_csv": "Analyzes CSV data. Requires 'csv_content' and 'query' in parameters. Example: 'analyze_csv with query \"summarize\" and csv_content \"a,b\\n1,2\"'",
            "create_image": "Creates an image from a text prompt. Requires 'prompt' and optional 'style'. Example: 'create_image with prompt \"a cat wearing a hat\" and style \"cartoon\"'",
        }
        self.models = []
        print("ToolDispatcher initialized.")
        print(f"Available tools: {list(self.tools.keys())}")

    def _execute_csv_analysis(self, query: str, **kwargs) -> ToolDispatcherResponse:
        """
        Wrapper for the CsvTool.analyze function.
        Requires 'csv_content' and 'query' to be in kwargs.
        """
        csv_content = kwargs.get("csv_content")
        analysis_query = kwargs.get("query", query)

        if not csv_content:
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload=None,
                tool_name_attempted="analyze_csv",
                original_query_for_tool=query,
                error_message="Missing 'csv_content' parameter for analyze_csv tool."
            )

        try:
            result = self.csv_tool_instance.analyze(csv_content=csv_content, query=analysis_query)
            return ToolDispatcherResponse(
                status=result["status"],
                payload=result.get("result"),
                tool_name_attempted="analyze_csv",
                original_query_for_tool=query,
                error_message=result.get("error")
            )
        except Exception as e:
            error_msg = f"Error executing CSV analysis: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="analyze_csv",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_image_creation(self, query: str, **kwargs) -> ToolDispatcherResponse:
        """
        Wrapper for the ImageGenerationTool.create_image function.
        Requires 'prompt' and optional 'style' in kwargs.
        """
        prompt = kwargs.get("prompt", query)
        style = kwargs.get("style", "photorealistic")

        if not prompt:
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload=None,
                tool_name_attempted="create_image",
                original_query_for_tool=query,
                error_message="Missing 'prompt' parameter for create_image tool."
            )

        try:
            result = self.image_generation_tool_instance.create_image(prompt=prompt, style=style)
            return ToolDispatcherResponse(
                status=result["status"],
                payload=result.get("result"),
                tool_name_attempted="create_image",
                original_query_for_tool=query,
                error_message=result.get("error")
            )
        except Exception as e:
            error_msg = f"Error executing image creation: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="create_image",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_code_inspection(self, query: str, **kwargs) -> ToolDispatcherResponse:
        """
        Wrapper for the CodeUnderstandingTool.
        Returns ToolDispatcherResponse.
        """
        action = kwargs.get("action")
        tool_name_param = kwargs.get("tool_name")

        if not action:
            parts = query.strip().split(maxsplit=1)
            action = parts[0].lower() if parts else None
            if len(parts) > 1:
                tool_name_param = parts[1]

        if not action:
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload=None,
                tool_name_attempted="inspect_code",
                original_query_for_tool=query,
                error_message="No action specified for code inspection. Use 'list_tools' or 'describe_tool <tool_name>'."
            )

        try:
            result_payload = self.code_understanding_tool_instance.execute(action=action, tool_name=tool_name_param)
            return ToolDispatcherResponse(
                status="success",
                payload=result_payload,
                tool_name_attempted="inspect_code",
                original_query_for_tool=query
            )
        except Exception as e:
            error_msg = f"Error executing code inspection: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="inspect_code",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_rag_query(self, query: str, **kwargs) -> ToolDispatcherResponse:
        """
        Wrapper for the RAGManager.search function.
        """
        try:
            # Assuming the query is the text to search for.
            # The RAGManager might evolve to take more complex parameters.
            results = self.rag_manager.search(query)
            return ToolDispatcherResponse(
                status="success",
                payload=results,
                tool_name_attempted="rag_query",
                original_query_for_tool=query
            )
        except Exception as e:
            error_msg = f"Error in RAG query: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="rag_query",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_math_calculation(self, query: str, **kwargs) -> ToolDispatcherResponse:
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
            response = math_calculate(query)
            return response

        except Exception as e:
            error_msg = f"Error in math calculation: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="calculate",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_logic_evaluation(self, query: str, **kwargs) -> ToolDispatcherResponse:
        """
        Wrapper for the logic_tool.evaluate_expression function.
        The query should be the logical expression string itself.
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

            print(f"ToolDispatcher DEBUG (_execute_logic_evaluation): expression_to_evaluate='{expression_to_evaluate}'")
            result = logic_evaluate(expression_to_evaluate)
            # The logic_evaluate tool returns a boolean, or a string error message.
            if isinstance(result, bool):
                return ToolDispatcherResponse(
                    status="success",
                    payload=result,
                    tool_name_attempted="evaluate_logic",
                    original_query_for_tool=query
                )
            else: # It's an error string
                return ToolDispatcherResponse(
                    status="failure_tool_error",
                    payload=None,
                    tool_name_attempted="evaluate_logic",
                    original_query_for_tool=query,
                    error_message=result # The error message from logic_tool
                )
        except Exception as e:
            error_msg = f"Error in logic evaluation: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="evaluate_logic",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def _execute_translation(self, query: str, **kwargs) -> ToolDispatcherResponse:
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
                            return ToolDispatcherResponse(
                                status="error_dispatcher_issue",
                                payload=None,
                                tool_name_attempted="translate_text",
                                original_query_for_tool=query,
                                error_message="Sorry, I couldn't understand what text to translate from the query."
                            )

            if not text_to_translate: # Ensure text is not empty
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload=None,
                    tool_name_attempted="translate_text",
                    original_query_for_tool=query,
                    error_message="Sorry, no text to translate was found."
                )

            # Use source_lang_from_kwarg if provided, otherwise it's None (for auto-detect)
            result_payload = translate_text(text_to_translate, resolved_target_lang, source_language=source_lang_from_kwarg)
            # translate_text already returns a string like "Translation: ..." or error message
            # We need to check if it's an error message from the tool itself.
            if "Translation not available" in result_payload or "error" in result_payload.lower() or "not supported" in result_payload.lower(): # Simple check
                 return ToolDispatcherResponse(
                    status="failure_tool_error", # Or a more specific status if tool provides it
                    payload=None,
                    tool_name_attempted="translate_text",
                    original_query_for_tool=query,
                    error_message=result_payload
                )
            return ToolDispatcherResponse(
                status="success",
                payload=result_payload,
                tool_name_attempted="translate_text",
                original_query_for_tool=query
            )
        except Exception as e:
            error_msg = f"Error in translation tool: {str(e)[:100]}"
            print(f"ToolDispatcher: {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload=None,
                tool_name_attempted="translate_text",
                original_query_for_tool=query,
                error_message=error_msg
            )

    def dispatch(self, query: str, explicit_tool_name: Optional[str] = None, **kwargs) -> ToolDispatcherResponse:
        """
        Dispatches a query to the appropriate tool.
        If explicit_tool_name is provided, it uses that tool.
        Otherwise, it tries to infer the tool from the query.
        Returns a ToolDispatcherResponse or None if no tool is inferred.
        """
        if explicit_tool_name:
            if explicit_tool_name in self.tools:
                print(f"Dispatching to explicitly named tool: {explicit_tool_name}")
                kwargs_with_orig_query = {"original_query": query, **kwargs}
                # Explicit calls to translation need kwargs passed differently
                # All _execute_* methods now return ToolDispatcherResponse
                # So we can directly return the result of the tool call.
                # The kwargs_with_orig_query already contains the original query.
                return self.tools[explicit_tool_name](query, **kwargs_with_orig_query)
            else:
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload=None,
                    tool_name_attempted=explicit_tool_name,
                    original_query_for_tool=query,
                    error_message=f"Tool '{explicit_tool_name}' not found."
                )

        # Use DLM for intent recognition
        intent = self.dlm.recognize_intent(query, available_tools=self.get_available_tools())

        if intent and intent.get("tool_name") in self.tools:
            tool_name_from_dlm = intent["tool_name"]
            tool_params = intent.get("parameters", {})
            # The 'query' in parameters is the specific data for the tool
            # The top-level 'query' is the user's original full query
            tool_specific_query = tool_params.get("query", query)

            print(f"Dispatching to '{tool_name_from_dlm}' tool based on DLM intent. Effective query for tool: '{tool_specific_query}'")

            if "original_query" not in tool_params:
                tool_params["original_query"] = query

            # Special parameter mapping for translation
            if tool_name_from_dlm == 'translate_text':
                # The _execute_translation method expects the text to translate as the first argument,
                # and other details in kwargs. The DLM provides these in tool_params.
                text_to_translate = tool_params.get('text_to_translate', tool_specific_query)
                return self._execute_translation(text_to_translate, **tool_params)

            # Standard tool execution for others
            # We need to remove the 'query' and 'original_query' from tool_params if it exists to avoid sending it twice
            tool_params.pop('query', None)
            tool_params.pop('original_query', None)
            return self.tools[tool_name_from_dlm](tool_specific_query, **tool_params)
        # If no tool was dispatched by explicit name or DLM intent
        else:
            # This is the case where DLM returns "NO_TOOL" or tool not found
            print(f"No specific local tool inferred by DLM for query: '{query}'")
            return ToolDispatcherResponse(
                status="no_tool_inferred",
                payload=None,
                tool_name_attempted=None,
                original_query_for_tool=query,
                error_message="No specific tool could be inferred from the query."
            )

    def get_available_tools(self):
        """Returns a dictionary of available tools and their descriptions."""
        return self.tool_descriptions

    def add_model(self, model_code):
        """Adds a new model to the dispatcher."""
        exec(model_code, globals())
        model_name = re.search(r"class (\w+):", model_code).group(1)
        self.models.append(globals()[model_name]())

    def replace_model(self, old_model, new_model):
        """Replaces an existing model with a new one."""
        for i, model in enumerate(self.models):
            if model.name == old_model.name:
                self.models[i] = new_model
                break

    def add_tool(self, tool_code):
        """Adds a new tool to the dispatcher."""
        exec(tool_code, globals())
        tool_name = re.search(r"def (\w+)\(input\):", tool_code).group(1)
        self.tools[tool_name] = globals()[tool_name]

    def replace_tool(self, old_tool, new_tool):
        """Replaces an existing tool with a new one."""
        for tool_name, tool in self.tools.items():
            if tool == old_tool:
                self.tools[tool_name] = new_tool
                break

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
