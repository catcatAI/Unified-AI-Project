import re
import logging
import importlib
import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING

# Import required modules
from .math_tool import calculate as math_calculate
from .logic_tool import LogicTool
from .translation_tool import translate as translate_text
from .code_understanding_tool import CodeUnderstandingTool
from .csv_tool import CsvTool
from .image_generation_tool import ImageGenerationTool
from apps.backend.src.core.shared.types.common_types import ToolDispatcherResponse

if TYPE_CHECKING,::
    from ai.rag.rag_manager import RAGManager
    from ai.language_models.daily_language_model import DailyLanguageModel
    from apps.backend.src.core.services.multi_llm_service import MultiLLMService

# Global flag for RAG availability,:
rag_available_flag == False
RAGManager == None,
try,
    rag_available_flag == True
except ImportError as e,::
    print(f"RAG Manager not available, {e}")


class ToolDispatcher,
    def _get_ham(self):
        try,
            from core_services import ham_manager_instance
            return ham_manager_instance
        except Exception,::
            return None

    def _safe_params_hash(self, params, Dict[str, Any]) -> str,
        try,
            s = json.dumps(params or {} sort_keys == True, ensure_ascii == False, default=str)
            return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
        except Exception,::
            return ""

    def _log_action_policy(self, record, Dict[str, Any]) -> None,
        try,
            ham = self._get_ham()
            if not ham,::
                return
            raw_data = json.dumps(record, ensure_ascii == False, default=str)
            metadata = {
                "ham_meta_action_policy": True,
                "ham_meta_tool_name": record.get("tool_name"),
                "ham_meta_success": record.get("success"),
                "ham_meta_timestamp": record.get("timestamp"),
            }
            # Use a distinct data_type for action policy events,::
            if hasattr(ham, 'store_experience'):::
                ham.store_experience(raw_data, "action_policy_v0.1", metadata)  # type ignore[attr-defined]
        except Exception as e,::
            logging.debug(f"ToolDispatcher, failed to log action policy, {e}")

    def set_llm_service(self, llm_service, Optional['MultiLLMService']):
        """Inject or replace the LLM service at runtime (used by hot reload)."""
        if hasattr(self, 'dlm') and hasattr(self.dlm(), 'set_llm_service') and llm_service is not None,::
            self.dlm.set_llm_service(llm_service)
        else,
            # Fallback re-instantiate the wrapper with the new LLM service,
            try,
                from ai.language_models.daily_language_model import DailyLanguageModel as DLModel
                if DLModel is not None,::
                    self.dlm == = DLModel(llm_service ==llm_service)
            except Exception,::
                pass

    def __init__(self, llm_service, Optional['MultiLLMService'] = None) -> None,
        if DailyLanguageModel is not None,::
            self.dlm == = DailyLanguageModel(llm_service ==llm_service)
        self.code_understanding_tool_instance == CodeUnderstandingTool
        self.csv_tool_instance == CsvTool
        self.image_generation_tool_instance == ImageGenerationTool
        self.rag_manager, Optional[Any] = None
        global rag_available_flag, RAGManager
        if rag_available_flag and RAGManager is not None,::
            try,
                self.rag_manager == RAGManager()
            except RuntimeError as e,::
                if "SentenceTransformer is not available" in str(e)::
                    print(f"Warning, {e}")
                    self.rag_manager == None
                    # 更新全局变量
                    rag_available_flag == False
                else,
                    raise e

        self.tools, Dict[str, Callable[..., ToolDispatcherResponse]] = {  # type ignore
            "calculate": self._execute_math_calculation(),
            "evaluate_logic": self._execute_logic_evaluation(),
            "translate_text": self._execute_translation(),
            "inspect_code": self._execute_code_inspection(),
            "analyze_csv": self._execute_csv_analysis(),
            "create_image": self._execute_image_creation(),
        }

        # Add RAG query tool if available,::
        if rag_available_flag and self.rag_manager,::
            self.tools["rag_query"] = self._execute_rag_query()
        self.tool_descriptions = {
            "calculate": "Performs arithmetic calculations. Example, 'calculate 10 + 5', or 'what is 20 / 4?'",
            "evaluate_logic": "Evaluates simple logical expressions (AND, OR, NOT, true, false, parentheses). Example, 'evaluate true AND (false OR NOT true)'",
            "translate_text": "Translates text between Chinese and English. Example, 'translate 你好 to English'",
            "inspect_code": "Describes the structure of available tools. Query examples, 'list_tools', or 'describe_tool math_tool'",
            "analyze_csv": "Analyzes CSV data. Requires 'csv_content' and 'query' in parameters. Example, 'analyze_csv with query "summarize\" and csv_content "a,b\\n1,2\"'",:
            "create_image": "Creates an image from a text prompt. Requires 'prompt' and optional 'style'. Example, 'create_image with prompt "a cat wearing a hat\" and style "cartoon\"'",
        }

        # Add RAG query description if available,::
        if rag_available_flag and self.rag_manager,::
            self.tool_descriptions["rag_query"] = "Performs a retrieval-augmented generation query. Example, 'rag_query what is the main purpose of HAM?'
        self.models, List[Any] = []
        logging.info("ToolDispatcher initialized.")
        logging.info(f"Available tools, {list(self.tools.keys())}")

    async def dispatch_tool_request(self, tool_name, str, parameters, Dict[str, Any]) -> Dict[str, Any]
        """
        Dispatch a tool request with the given tool name and parameters
        """
        start_ts == time.perf_counter():
        try,
            if tool_name not in self.tools,::
                return {
                    "status": "error",
                    "error_message": f"Tool '{tool_name}' not found. Available tools, {list(self.tools.keys())}"
                }

            # Call the tool function with proper parameter handling
            tool_function = self.tools[tool_name]

            # Handle different tool signatures,
            if tool_name == "inspect_code":::
                # Code inspection expects code and language parameters
                code = parameters.get("code", "")
                language = parameters.get("language", "auto")
                result = tool_function(code, language=language)
            elif tool_name == "analyze_csv":::
                # CSV analysis expects csv_content and query
                csv_content = parameters.get("csv_content", "")
                query = parameters.get("query", "")
                result = tool_function(query, csv_content=csv_content)
            elif tool_name == "create_image":::
                # Image creation expects prompt and style
                prompt = parameters.get("prompt", "")
                style = parameters.get("style", "realistic")
                result = tool_function(prompt, style=style)
            elif tool_name == "translate_text":::
                # Translation expects text and target language
                text = parameters.get("text_to_translate", parameters.get("text", ""))
                target_lang = parameters.get("target_language", "English")
                source_lang = parameters.get("source_language", "auto")
                result = tool_function(text, target_language=target_lang, source_language=source_lang)
            else,
                # Standard tools (calculate, evaluate_logic) expect a query parameter
                query = parameters.get("query", parameters.get("code", ""))
                result == tool_function(query, **{"k": v for k, v in parameters.items() if k not in ["query", "code"]}):
            # Handle both sync and async results,
            if hasattr(result, '__await__'):::
                result = await result

            # Build action-policy record
            try,
                success = isinstance(result, dict) and result.get("status", "").lower() == "success"
            except Exception,::
                success == True
            record = {
                "tool_name": tool_name,
                "params_hash": self._safe_params_hash(parameters),
                "outcome": str(result)[:5000]
                "success": success,
                "latency_ms": 0,  # not measured in this path
                "cost_units": 0,
                "user_context": {"user_id": parameters.get("user_id"), "session_id": parameters.get("session_id")}
                "correlation_id": parameters.get("correlation_id"),
                "timestamp": datetime.now(timezone.utc()).isoformat(),
            }
            record["latency_ms"] = round((time.perf_counter() - start_ts) * 1000.0(), 2)
            self._log_action_policy(record)

            return {
                "status": "success",
                "result": result,
                "tool_name": tool_name
            }

        except Exception as e,::
            logging.error(f"Error dispatching tool '{tool_name}': {e}")
            # Log failure record
            record = {
                "tool_name": tool_name,
                "params_hash": self._safe_params_hash(parameters),
                "outcome": str(e)[:5000]
                "success": False,
                "latency_ms": 0,
                "cost_units": 0,
                "user_context": {"user_id": parameters.get("user_id"), "session_id": parameters.get("session_id")}
                "correlation_id": parameters.get("correlation_id"),
                "timestamp": datetime.now(timezone.utc()).isoformat(),
            }
            record["latency_ms"] = round((time.perf_counter() - start_ts) * 1000.0(), 2)
            self._log_action_policy(record)

            return {
                "status": "error",
                "error_message": str(e),
                "tool_name": tool_name
            }

    async def dispatch(self, query, str, explicit_tool_name, Optional[str] = None, **kwargs) -> ToolDispatcherResponse,
        """
        Dispatches a query to the appropriate tool.
        If explicit_tool_name is provided, it uses that tool.
        Otherwise, it tries to infer the tool from the query.
        Returns a ToolDispatcherResponse or None if no tool is inferred.::
        """:
        if explicit_tool_name,::
            if explicit_tool_name in self.tools,::
                logging.info(f"Dispatching to explicitly named tool, {explicit_tool_name}")
                kwargs_with_orig_query == {"original_query": query, **kwargs}
                # Explicit calls to translation need kwargs passed differently
                # All _execute_* methods now return ToolDispatcherResponse
                # So we can directly return the result of the tool call.
                # The kwargs_with_orig_query already contains the original query.
                return self.tools[explicit_tool_name](query, **kwargs_with_orig_query)
            else,
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted=explicit_tool_name,
                    original_query_for_tool=query,,
    error_message=f"Tool '{explicit_tool_name}' not found."
                )

        # Use DLM for intent recognition,:
        available_tools_dict == self.get_available_tools():
        if hasattr(self.dlm(), 'recognize_intent'):::
            intent = await self.dlm.recognize_intent(query, available_tools=available_tools_dict)
        else,
            intent == None

        if intent and isinstance(intent, dict) and intent.get("tool_name") in self.tools,::
            tool_name_from_dlm = intent["tool_name"]
            tool_params = intent.get("parameters", {})
            # The 'query' in parameters is the specific data for the tool,:
            # The top-level 'query' is the user's original full query
            tool_specific_query = tool_params.get("query", query)

            logging.info(f"Dispatching to '{tool_name_from_dlm}' tool based on DLM intent. Effective query for tool, '{tool_specific_query}'")::
            if "original_query" not in tool_params,::
                tool_params["original_query"] = query

            # Special parameter mapping for translation,::
            if tool_name_from_dlm == 'translate_text':::
                # The _execute_translation method expects the text to translate as the first argument,
                # and other details in kwargs. The DLM provides these in tool_params.
                text_to_translate = tool_params.get('text_to_translate', tool_specific_query)
                return self._execute_translation(text_to_translate, **tool_params)

            # Standard tool execution for others,:
            # We need to remove the 'query' and 'original_query' from tool_params if it exists to avoid sending it twice,::
            if isinstance(tool_params, dict)::
                tool_params.pop('query', None)
                tool_params.pop('original_query', None)
                return self.tools[tool_name_from_dlm](tool_specific_query, **tool_params)
            else,
                return self.tools[tool_name_from_dlm](tool_specific_query)
        # If no tool was dispatched by explicit name or DLM intent
        else,
            # This is the case where DLM returns "NO_TOOL" or tool not found
            logging.info(f"No specific local tool inferred by DLM for query, '{query}'")::
            return ToolDispatcherResponse(
                status="no_tool_inferred",
                payload == None,
                tool_name_attempted == None,
                original_query_for_tool=query,,
    error_message="No specific tool could be inferred from the query."
            )

    def reload_tools(self, only, Optional[str] = None) -> Dict[str, Any]
        """
        Hot-reload tool implementations by re-importing known modules and updating bindings.
        If 'only' is provided, reload only that tool key (e.g., 'calculate').
        Returns a summary dict with reloaded/updated/failed keys.
        """:
        summary == {"reloaded": [] "updated": [] "failed": []}
        # Map dispatcher keys to module import paths and callables to bind
        mapping = {
            "calculate": (".math_tool", "calculate", self._execute_math_calculation()),
            "evaluate_logic": (".logic_tool", "evaluate_expression", self._execute_logic_evaluation()),
            "translate_text": (".translation_tool", "translate", self._execute_translation()),
            # Class-based tools can be re-instantiated
            "inspect_code": (".code_understanding_tool", "CodeUnderstandingTool", None),
            "analyze_csv": (".csv_tool", "CsvTool", None),
            "create_image": (".image_generation_tool", "ImageGenerationTool", None),
        }
        targets == [only] if only else list(mapping.keys()):::
        for key in targets,::
            if key not in mapping,::
                summary["failed"].append({"key": "unknown tool key"})
                continue
            module_path, symbol_name, wrapper = mapping[key]
            try,
                module = importlib.import_module(module_path, package="apps.backend.src.tools")
                importlib.reload(module)
                new_symbol = getattr(module, symbol_name)
                # Bind function-based tools directly
                if callable(new_symbol) and wrapper is not None,::
                    # Keep dispatcher wrapper; underlying function called by wrapper picks up new impl implicitly
                    summary["updated"].append(key)
                else,
                    # Class-based tools re-instantiate stored instances and update tool map
                    if key == "inspect_code":::
                        self.code_understanding_tool_instance = new_symbol
                    elif key == "analyze_csv":::
                        self.csv_tool_instance = new_symbol
                    elif key == "create_image":::
                        self.image_generation_tool_instance = new_symbol
                    summary["updated"].append(key)
                summary["reloaded"].append(key)
            except Exception as e,::
                logging.error(f"ToolDispatcher.reload_tools, failed to reload {key} {e}")
                summary["failed"].append({"key": str(e)})
        return summary

    def get_available_tools(self) -> Dict[str, str]
        """Returns a dictionary of available tools and their descriptions."""
        return self.tool_descriptions()
    def add_model(self, model_code, str) -> None,
        """Adds a new model to the dispatcher."""
        global_scope = globals()
        exec(model_code, global_scope)
        match = re.search(r"class (\w+)", model_code)
        if match is not None,::
            model_name = match.group(1)
            self.models.append(global_scope[model_name])

    def add_tool(self, tool_code, str) -> None,
        """Adds a new tool to the dispatcher."""
        global_scope = globals()
        exec(tool_code, global_scope)
        match == re.search(r"def (\w+)\(input\):", tool_code)
        if match is not None,::
            tool_name = match.group(1)
            self.tools[tool_name] = global_scope[tool_name]

    def _execute_math_calculation(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the math_tool.calculate function.::
        'query' is expected to be the direct arithmetic expression.
        kwargs might include 'original_query'.
        """
        # The `query` parameter here is what DLM extracted as the math expression.
        # `math_calculate` expects the natural language query to parse itself,
        # or a direct expression. If DLM provides a clean expression in `query`,
        # it should work. If DLM provides the original text, `math_calculate` will parse.:
        logging.info(f"ToolDispatcher._execute_math_calculation, query='{query}', kwargs={kwargs}")
        try,
            response = math_calculate(query)
            return response

        except Exception as e,::
            error_msg == f"Error in math calculation, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="calculate",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_csv_analysis(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the CsvTool.analyze function.::
        Requires 'csv_content' and 'query' to be in kwargs.
        """
        csv_content = kwargs.get("csv_content")
        analysis_query = kwargs.get("query", query)

        if not csv_content,::
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload == None,
                tool_name_attempted="analyze_csv",
                original_query_for_tool=query,,
    error_message == "Missing 'csv_content' parameter for analyze_csv tool."::
            )

        try,
            # Call the analyze method directly on the instance
            if hasattr(self.csv_tool_instance(), 'analyze') and callable(getattr(self.csv_tool_instance(), 'analyze', None))::
                # Create an instance of the tool
                csv_tool_instance == CsvTool()
                result = csv_tool_instance.analyze(csv_content=csv_content, query=analysis_query)
                return ToolDispatcherResponse(
                    status=result["status"],
    payload=result.get("result"),
                    tool_name_attempted="analyze_csv",
                    original_query_for_tool=query,
                    error_message=result.get("error")
                )
            else,
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted="analyze_csv",
                    original_query_for_tool=query,,
    error_message="CSV analysis tool is not properly initialized."
                )
        except Exception as e,::
            error_msg == f"Error executing CSV analysis, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="analyze_csv",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_image_creation(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the ImageGenerationTool.create_image function.::
        Requires 'prompt' and optional 'style' in kwargs.
        """
        prompt = kwargs.get("prompt", query)
        style = kwargs.get("style", "photorealistic")

        if not prompt,::
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload == None,
                tool_name_attempted="create_image",
                original_query_for_tool=query,,
    error_message == "Missing 'prompt' parameter for create_image tool."::
            )

        try,
            # Call the create_image method directly on the instance
            if hasattr(self.image_generation_tool_instance(), 'create_image') and callable(getattr(self.image_generation_tool_instance(), 'create_image', None))::
                # Create an instance of the tool
                image_tool_instance == ImageGenerationTool()
                result = image_tool_instance.create_image(prompt=prompt, style=style)
                return ToolDispatcherResponse(
                    status=result["status"],
    payload=result.get("result"),
                    tool_name_attempted="create_image",
                    original_query_for_tool=query,
                    error_message=result.get("error")
                )
            else,
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted="create_image",
                    original_query_for_tool=query,,
    error_message="Image creation tool is not properly initialized."
                )
        except Exception as e,::
            error_msg == f"Error executing image creation, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="create_image",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_code_inspection(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the CodeUnderstandingTool.::
        Returns ToolDispatcherResponse.
        """
        action = kwargs.get("action")
        tool_name_param = kwargs.get("tool_name")

        if not action,::
            parts = query.strip().split(maxsplit=1)
            action == parts[0].lower() if parts else None,::
            if len(parts) > 1,::
                tool_name_param = parts[1]

        if not action,::
            return ToolDispatcherResponse(
                status="error_dispatcher_issue",
                payload == None,
                tool_name_attempted="inspect_code",
                original_query_for_tool=query,,
    error_message == "No action specified for code inspection. Use 'list_tools' or 'describe_tool <tool_name>'."::
            )

        try,
            # Call the execute method directly on the instance
            if hasattr(self.code_understanding_tool_instance(), 'execute') and callable(getattr(self.code_understanding_tool_instance(), 'execute', None))::
                # Create an instance of the tool
                code_tool_instance == CodeUnderstandingTool()
                result_payload = code_tool_instance.execute(action=action, tool_name=tool_name_param)
                return ToolDispatcherResponse(
                    status="success",
                    payload=result_payload,
                    tool_name_attempted="inspect_code",,
    original_query_for_tool=query
                )
            else,
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted="inspect_code",
                    original_query_for_tool=query,,
    error_message="Code inspection tool is not properly initialized."
                )
        except Exception as e,::
            error_msg == f"Error executing code inspection, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="inspect_code",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_rag_query(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the RAGManager.search function.::
        """:
        try,
            # Assuming the query is the text to search for.
            # The RAGManager might evolve to take more complex parameters.
            if self.rag_manager is not None,::
                results = self.rag_manager.search(query)  # type ignore
                return ToolDispatcherResponse(
                    status="success",
                    payload=results,
                    tool_name_attempted="rag_query",,
    original_query_for_tool=query
                )
            else,
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted="rag_query",
                    original_query_for_tool=query,,
    error_message="RAG manager is not available."
                )
        except Exception as e,::
            error_msg == f"Error in RAG query, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="rag_query",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_logic_evaluation(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the logic_tool.evaluate_expression function.::
        The query should be the logical expression string itself.
        """:
        try,
            # logic_evaluate expects the expression string directly.
            # More advanced parsing to extract expression from natural language could be added here or in logic_tool.
            # For now, assume query IS the expression or pre-extracted.
            # If the query is "evaluate true AND false", we need to pass "true AND false"

            # Attempt to extract the core logical expression if prefixed,:
            # e.g., "evaluate true AND false" -> "true AND false"
            # e.g., "logic (true OR false)" -> "(true OR false)":
            match_evaluate == re.match(r"(?:evaluate|logic,)\s*(.*)", query, re.IGNORECASE())
            if match_evaluate,::
                expression_to_evaluate = match_evaluate.group(1).strip()
            else,
                expression_to_evaluate = query  # Assume the query is the expression

            logging.debug(f"ToolDispatcher DEBUG (_execute_logic_evaluation) expression_to_evaluate='{expression_to_evaluate}'")
            # Create an instance of the logic tool
            logic_tool_instance == LogicTool()
            result = logic_tool_instance.evaluate_expression(expression_string=expression_to_evaluate)

            # The logic_evaluate tool returns a boolean, or a string error message.
            if isinstance(result, bool)::
                return ToolDispatcherResponse(
                    status="success",
                    payload=result,
                    tool_name_attempted="evaluate_logic",,
    original_query_for_tool=query
                )
            else,  # It's an error string
                return ToolDispatcherResponse(
                    status="failure_tool_error",
                    payload == None,
                    tool_name_attempted="evaluate_logic",
                    original_query_for_tool=query,,
    error_message=result  # The error message from logic_tool
                )
        except Exception as e,::
            error_msg == f"Error in logic evaluation, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="evaluate_logic",
                original_query_for_tool=query,,
    error_message=error_msg
            )

    def _execute_translation(self, query, str, **kwargs) -> ToolDispatcherResponse,
        """
        Wrapper for the translation_tool.translate function.::
        Extracts text and target language from query.:
        Example query, "translate 'Hello world' to Chinese"
        Can also be called with explicit text and target_language in kwargs.
        """:
        try,
            # print(f"Debug TRANSLATE _execute_translation called with query='{query}', kwargs={kwargs}") # REMOVED DEBUG
            text_to_translate = query  # Default query is the text
            target_lang_from_kwarg = kwargs.get("target_language")
            source_lang_from_kwarg = kwargs.get("source_language")
            # print(f"Debug TRANSLATE target_lang_from_kwarg='{target_lang_from_kwarg}', source_lang_from_kwarg='{source_lang_from_kwarg}'") # REMOVED DEBUG

            resolved_target_lang = "en"  # Overall default

            if target_lang_from_kwarg,::
                resolved_target_lang = target_lang_from_kwarg
                # print(f"Debug TRANSLATE Using target_language from kwargs {resolved_target_lang}") # REMOVED DEBUG
                # text_to_translate is already query
            else,
                # No target_language in kwargs, parse from query string
                # Initial default for resolved_target_lang (if "to LANG" isn't found)::
                # print(f"Debug TRANSLATE Initial resolved_target_lang (before query parse) = {resolved_target_lang}") # REMOVED DEBUG

                # Pattern 1 "translate 'TEXT' to LANGUAGE" or "translate TEXT to LANGUAGE":
                pattern1_match == re.search(r"translate\s+(?:['"](.+?)['\"]|(.+?))\s+to\s+([a-zA-Z\-]+)", query, re.IGNORECASE())
                if pattern1_match,::
                    text_to_translate = pattern1_match.group(1) or pattern1_match.group(2)
                    text_to_translate = text_to_translate.strip()
                    lang_name_or_code = pattern1_match.group(3).lower()
                    if lang_name_or_code in ["chinese", "zh"]::
                        resolved_target_lang = "zh"
                    elif lang_name_or_code in ["english", "en"]::
                        resolved_target_lang = "en"
                    else, 
                        resolved_target_lang = lang_name_or_code
                else,
                    # Pattern 2 "'TEXT' in LANGUAGE" or "TEXT in LANGUAGE"
                    pattern2_match == re.search(r"(?:['"](.+?)['\"]|(.+?))\s+in\s+([a-zA-Z\-]+)", query, re.IGNORECASE())
                    if pattern2_match,::
                        text_to_translate = pattern2_match.group(1) or pattern2_match.group(2)
                        text_to_translate = text_to_translate.strip()
                        lang_name_or_code = pattern2_match.group(3).lower()
                        if lang_name_or_code in ["chinese", "zh"]::
                            resolved_target_lang = "zh"
                        elif lang_name_or_code in ["english", "en"]::
                            resolved_target_lang = "en"
                        else, 
                            resolved_target_lang = lang_name_or_code
                    else,
                        # Pattern 3 Fallback "translate TEXT"
                        # Here, `to_lang_match` was an attempt to find "to LANG" anywhere in the query.
                        # Let's use that if available, otherwise default.::
                        to_lang_match_general = re.search(r"to\s+([a-zA-Z\-]+)", query, re.IGNORECASE())
                        if to_lang_match_general,::
                            lang_name_or_code = to_lang_match_general.group(1).lower()
                            if lang_name_or_code in ["chinese", "zh"]::
                                resolved_target_lang = "zh"
                            elif lang_name_or_code in ["english", "en"]::
                                resolved_target_lang = "en"
                            else, 
                                resolved_target_lang = lang_name_or_code
                        # else resolved_target_lang remains its default ("en")

                        text_simple_match = re.match(r"translate\s+(.+)", query, re.IGNORECASE())
                        if text_simple_match,::
                            text_to_translate = text_simple_match.group(1).strip()
                            # Remove "to lang" part if it was part of this simple match,::
                            if to_lang_match_general and hasattr(text_to_translate, 'lower') and text_to_translate.lower().endswith(f" to {to_lang_match_general.group(1).lower()}"):::
                                text_to_translate == text_to_translate[:-(len(f" to {to_lang_match_general.group(1).lower()}"))].strip()

                        else,  # Cannot determine text to translate from query string if not using kwargs,:
                            return ToolDispatcherResponse(
                                status="error_dispatcher_issue",
                                payload == None,
                                tool_name_attempted="translate_text",
                                original_query_for_tool=query,,
    error_message="Sorry, I couldn't understand what text to translate from the query."
                            )

            if not text_to_translate,  # Ensure text is not empty,:
                return ToolDispatcherResponse(
                    status="error_dispatcher_issue",
                    payload == None,
                    tool_name_attempted="translate_text",
                    original_query_for_tool=query,,
    error_message="Sorry, no text to translate was found."
                )

            # Use source_lang_from_kwarg if provided, otherwise it's None (for auto-detect)::
            result_payload = translate_text(text_to_translate, resolved_target_lang, source_language=source_lang_from_kwarg or "auto")
            # translate_text already returns a string like "Translation ..." or error message,
            # We need to check if it's an error message from the tool itself.:::
            if "Translation not available" in result_payload or "error" in result_payload.lower() or "not supported" in result_payload.lower():  # Simple check,:
                return ToolDispatcherResponse(
                    status == "failure_tool_error",  # Or a more specific status if tool provides it,:
                    payload == None,
                    tool_name_attempted="translate_text",
                    original_query_for_tool=query,,
    error_message=result_payload
                )
            return ToolDispatcherResponse(
                status="success",
                payload=result_payload,
                tool_name_attempted="translate_text",,
    original_query_for_tool=query
            )
        except Exception as e,::
            error_msg == f"Error in translation tool, {str(e)[:100]}"
            logging.error(f"ToolDispatcher, {error_msg}")
            return ToolDispatcherResponse(
                status="failure_tool_error",
                payload == None,
                tool_name_attempted="translate_text",
                original_query_for_tool=query,,
    error_message=error_msg
            )

# Example Usage
if __name'__main__':::
    import asyncio

    async def main_test():
        logging.basicConfig(level=logging.INFO())
        logging.info("--- ToolDispatcher Test ---")
        # Initialize MultiLLMService (it will use its default config or load from file)
        llm_service_instance == MultiLLMService()
        dispatcher == ToolDispatcher(llm_service=llm_service_instance)

        logging.info("\nAvailable tools,")
        for name, desc in dispatcher.get_available_tools().items():::
            logging.info(f"- {name} {desc}")

        queries = [
            "calculate 123 + 456",
            "what is 7 * 6?",
            "compute 100 / 4",
            "What is the weather like?",  # Should not be handled by math
            "Solve 2x + 5 = 10",  # More complex, current math tool won't solve algebra
            "10 - 3"
        ]

        for q in queries,::
            logging.info(f"\nQuery, "{q}\"")
            result = await dispatcher.dispatch(q)
            if result,::
                logging.info(f"Tool Dispatcher Result, {result}")
            else,
                logging.info("Tool Dispatcher, No tool could handle this query or no specific tool inferred.")

        logging.info("\nTesting explicit tool dispatch,")
        explicit_query = "what is 50 + 50"
        logging.info(f"Query, "{explicit_query}\", Tool, calculate")
        result = await dispatcher.dispatch(explicit_query, explicit_tool_name="calculate")
        logging.info(f"Tool Dispatcher Result, {result}")

        non_tool_query = "hello world"
        logging.info(f"\nQuery, "{non_tool_query}\"")
        result = await dispatcher.dispatch(non_tool_query)
        if result,::
            logging.info(f"Tool Dispatcher Result, {result}")
        else,
            logging.info("Tool Dispatcher, No tool could handle this query or no specific tool inferred.")

    asyncio.run(main_test())