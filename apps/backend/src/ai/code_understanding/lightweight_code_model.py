import ast
import os
import glob
import logging # Added logging
from datetime import datetime

# Import DNADataChain from alpha_deep_model
from ..compression.alpha_deep_model import DNADataChain

logger: Any = logging.getLogger(__name__)

@dataclass
class CodeAnalysisResult:
    """代码分析结果数据类"""
    filepath: str
    analysis_timestamp: datetime
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    dependencies: List[str]
    complexity_score: float
    dna_chain_id: Optional[str] = None

class LightweightCodeModel:
    """
    A model to perform lightweight static analysis of Python code,
    focusing on understanding the structure of tools.
    Enhanced with DNA衍生数据链技术和代码复杂度 analysis.
    """

    def __init__(self, tools_directory: str = "src/tools/") -> None:
        """
        Initializes the LightweightCodeModel.

        Args:
            _ = tools_directory (str): The root directory where tool files are located.
        """
        self.tools_directory = tools_directory
        self.dna_chains: Dict[str, DNADataChain] = {}  # DNA数据链存储
        self.analysis_history: List[CodeAnalysisResult] = []  # 分析历史记录
        self.code_complexity_cache: Dict[str, float] = {}  # 代码复杂度缓存

        if not os.path.isdir(tools_directory):
            logger.warning(f"Tools directory '{tools_directory}' does not exist or is not a directory.")
            # Consider raising an error or ensuring tools_directory is always valid upon instantiation.
            # For now, behavior relies on later checks in methods using this directory.

    def list_tool_files(self) -> List[str]:
        """
        Lists potential Python tool files in the specified tools directory.
        Excludes __init__.py and tool_dispatcher.py.
        """
        if not os.path.isdir(self.tools_directory):
            return 

        # Search for .py files recursively in the tools_directory
        pattern = os.path.join(self.tools_directory, "**", "*.py")
        py_files = glob.glob(pattern, recursive=True)

        excluded_files = ["__init__.py", "tool_dispatcher.py"] # Basenames to exclude

        tool_files = 
        for f_path in py_files:
            if os.path.basename(f_path) not in excluded_files:
                tool_files.append(f_path)

        return tool_files

    def _extract_method_parameters(self, method_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """
        Helper to extract parameter details from an ast.FunctionDef node.
        """
        params_details = 
        args = method_node.args

        # Positional and keyword-only arguments
        all_args = args.posonlyargs + args.args + args.kwonlyargs
        all_defaults = args.defaults + args.kw_defaults

        # Defaults for positional/keyword arguments are at the end of args.defaults
        # For kwonlyargs, kw_defaults is a list of values, some can be None if no default

        num_pos_args = len(args.posonlyargs) + len(args.args)
        pos_defaults_start_idx = num_pos_args - len(args.defaults)

        for i, arg_node in enumerate(all_args):
            param_info = {"name": arg_node.arg, "annotation": None, "default": None}
            if arg_node.annotation:
                param_info["annotation"] = ast.unparse(arg_node.annotation) if hasattr(ast, 'unparse') else "TypeHint"

            # Determine default value
            if i >= pos_defaults_start_idx and i < num_pos_args: # Positional/regular arg with default
                default_val_node = args.defaults[i - pos_defaults_start_idx]
                if default_val_node: # Can be None if there's a default of None literally
                     param_info["default"] = ast.unparse(default_val_node) if hasattr(ast, 'unparse') else "DefaultValue"
            elif arg_node in args.kwonlyargs:
                # For kwonlyargs, kw_defaults is a list of default values, matching kwonlyargs by position.
                # Some values in kw_defaults can be None (for args without defaults).
                try:
                    kwonly_idx = args.kwonlyargs.index(arg_node)
                    if kwonly_idx < len(args.kw_defaults) and args.kw_defaults[kwonly_idx] is not None:
                        default_val_node = args.kw_defaults[kwonly_idx]
                        param_info["default"] = ast.unparse(default_val_node) if hasattr(ast, 'unparse') else "DefaultValue" # type: ignore
                except ValueError:
                    pass # Should not happen if arg_node is from args.kwonlyargs

            params_details.append(param_info)

        if args.vararg:
            vararg_info = {"name": f"*{args.vararg.arg}", "annotation": None, "default": None}
            if args.vararg.annotation:
                vararg_info["annotation"] = ast.unparse(args.vararg.annotation) if hasattr(ast, 'unparse') else "TypeHint"
            params_details.append(vararg_info)

        if args.kwarg:
            kwarg_info = {"name": f"**{args.kwarg.arg}", "annotation": None, "default": None}
            if args.kwarg.annotation:
                kwarg_info["annotation"] = ast.unparse(args.kwarg.annotation) if hasattr(ast, 'unparse') else "TypeHint"
            params_details.append(kwarg_info)

        return params_details

    def _calculate_complexity(self, node: ast.AST) -> float:
        """
        Calculate code complexity score based on AST node.
        """
        complexity = 0

        # Count control flow statements
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 0.5
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 0.2
            elif isinstance(child, ast.FunctionDef):
                complexity += 2  # Functions add complexity
            elif isinstance(child, ast.ClassDef):
                complexity += 3  # Classes add more complexity

        return complexity

    def analyze_tool_file(self, filepath: str, dna_chain_id: Optional[str] = None) -> Optional[CodeAnalysisResult]:
        """
        Analyzes a single Python tool file to extract its structure and complexity.
        Enhanced with DNA数据链支持.

        Args:
            _ = filepath (str): The absolute or relative path to the Python tool file.
            _ = dna_chain_id (Optional[str]): DNA链ID，用于关联分析结果

        Returns:
            Optional[CodeAnalysisResult]: A dataclass containing structural information
                                          and analysis results, or None if the file cannot
                                          be parsed or analyzed.
        """
        if not os.path.isfile(filepath):
            logger.error(f"File not found at '{filepath}' for analysis.")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as source_file:
                source_code = source_file.read
            tree = ast.parse(source_code, filename=filepath)
        except Exception as e:
            logger.error(f"Error parsing Python file '{filepath}': {e}", exc_info=True)
            return None

        # Calculate complexity
        complexity_score = self._calculate_complexity(tree)

        # Extract dependencies
        dependencies = 
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)

        file_structure: Dict[str, Any] = {
            "filepath": filepath,
            "classes": ,
            "functions":   # For module-level functions
        }

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": 
                }
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = {
                            "name": item.name,
                            "docstring": ast.get_docstring(item),
                            "parameters": self._extract_method_parameters(item),
                            "returns": None,
                            "complexity": self._calculate_complexity(item)
                        }
                        # Basic return type hint
                        if item.returns:
                            method_info["returns"] = ast.unparse(item.returns) if hasattr(ast, 'unparse') else "TypeHint (unparse unavailable)"
                        _ = class_info["methods"].append(method_info)
                _ = file_structure["classes"].append(class_info)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): # Module-level functions
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "parameters": self._extract_method_parameters(node),
                    "returns": None,
                    "complexity": self._calculate_complexity(node)
                }
                if node.returns:
                     func_info["returns"] = ast.unparse(node.returns) if hasattr(ast, 'unparse') else "TypeHint (unparse unavailable)"
                _ = file_structure["functions"].append(func_info)

        # Create analysis result
        analysis_result = CodeAnalysisResult(
            filepath=filepath,
            analysis_timestamp=datetime.now,
            classes=file_structure["classes"],
            functions=file_structure["functions"],
            dependencies=list(set(dependencies)),  # Remove duplicates
            complexity_score=complexity_score,
            dna_chain_id=dna_chain_id
        )

        # Add to analysis history
        self.analysis_history.append(analysis_result)

        # Update complexity cache
        self.code_complexity_cache[filepath] = complexity_score

        # Add to DNA chain if provided
        if dna_chain_id:
            if dna_chain_id not in self.dna_chains:
                self.dna_chains[dna_chain_id] = DNADataChain(dna_chain_id)
            self.dna_chains[dna_chain_id].add_node(filepath)

        return analysis_result

    def get_tool_structure(self, tool_name_or_filepath: str, dna_chain_id: Optional[str] = None) -> Optional[CodeAnalysisResult]:
        """
        Main interface method to get the structure of a specific tool.
        Enhanced with DNA数据链支持.

        The `tool_name_or_filepath` can be:
        1. A direct absolute or relative path to a Python tool file.
        2. A tool name (e.g., "my_tool" or "my_tool.py"). If a name is provided:
           - It first looks for an exact match (e.g., "my_tool.py") in `self.tools_directory`.
           - If not found, it searches for common patterns like "tool_my_tool.py" or
             "my_tool_tool.py" in `self.tools_directory`.
           - Resolution fails if the name is ambiguous (multiple pattern matches) or no match is found.

        Args:
            _ = tool_name_or_filepath (str): The name of the tool or direct filepath to the tool's Python file.
            _ = dna_chain_id (Optional[str]): DNA链ID，用于关联分析结果

        Returns:
            Optional[CodeAnalysisResult]: A dataclass containing structural information and analysis results
                                          if resolved and parsed, otherwise None.
        """
        resolved_path: Optional[str] = None

        # 1. Check if tools_directory is valid for name resolution
        # This check is more critical if we are about to list its contents for name search
        # If input is a direct path, tools_directory might not be used.

        # 2. Determine if input is a path or a name
        is_potential_path = os.sep in tool_name_or_filepath or \
                            (os.altsep and os.altsep in tool_name_or_filepath)

        if is_potential_path:
            if os.path.isfile(tool_name_or_filepath):
                resolved_path = tool_name_or_filepath
                logger.debug(f"Input '{tool_name_or_filepath}' is a direct file path.")
            else:
                logger.warning(f"Input '{tool_name_or_filepath}' appears to be a path but was not found or is not a file.")
                return None
        else:
            # Input is a name.
            if not os.path.isdir(self.tools_directory):
                logger.warning(f"Tools directory '{self.tools_directory}' is not valid. Cannot resolve tool by name: {tool_name_or_filepath}")
                return None

            tool_name_input = tool_name_or_filepath

            name_to_check_direct = tool_name_input
            if not name_to_check_direct.endswith(".py"):
                name_to_check_direct += ".py"

            potential_path_direct = os.path.join(self.tools_directory, name_to_check_direct)
            if os.path.isfile(potential_path_direct):
                resolved_path = potential_path_direct
                logger.info(f"Tool name '{tool_name_input}' resolved to '{resolved_path}' by direct match in {self.tools_directory}.")
            else:
                base_name = os.path.splitext(tool_name_input)[0]
                found_pattern_matches: List[str] = 

                try:
                    for filename in os.listdir(self.tools_directory):
                        if not filename.endswith(".py"):
                            continue

                        module_part = os.path.splitext(filename)[0]
                        full_candidate_path = os.path.join(self.tools_directory, filename)

                        if module_part == f"tool_{base_name}" or \
                           module_part == f"{base_name}_tool":
                            found_pattern_matches.append(full_candidate_path)
                except OSError as e:
                    logger.error(f"Error listing tools directory '{self.tools_directory}': {e}", exc_info=True)
                    return None

                if len(found_pattern_matches) == 1:
                    resolved_path = found_pattern_matches[0]
                    logger.info(f"Tool name '{tool_name_input}' (base: '{base_name}') resolved to '{resolved_path}' by pattern search in {self.tools_directory}.")
                elif len(found_pattern_matches) > 1:
                    logger.warning(f"Ambiguous tool name '{tool_name_input}' (base: '{base_name}'). Found multiple pattern matches in {self.tools_directory}: {found_pattern_matches}. Please provide a more specific name or direct path.")
                    return None

        if resolved_path:
            # 如果dna_chain_id为None，则不传递该参数
            if dna_chain_id is not None:
                return self.analyze_tool_file(resolved_path, dna_chain_id)
            else:
                return self.analyze_tool_file(resolved_path)
        else:
            logger.warning(f"Could not resolve tool '{tool_name_or_filepath}' to a Python file in '{self.tools_directory}' using supported conventions, nor as a direct path.")
            return None

    def get_analysis_history(self) -> List[CodeAnalysisResult]:
        """获取代码分析历史记录"""
        return self.analysis_history.copy

    def get_code_complexity(self, filepath: str) -> Optional[float]:
        """获取文件的代码复杂度"""
        return self.code_complexity_cache.get(filepath)

    def create_dna_chain(self, chain_id: str) -> DNADataChain:
        """创建新的DNA数据链"""
        if chain_id not in self.dna_chains:
            self.dna_chains[chain_id] = DNADataChain(chain_id)
        return self.dna_chains[chain_id]

    def get_dna_chain(self, chain_id: str) -> Optional[DNADataChain]:
        """获取DNA数据链"""
        return self.dna_chains.get(chain_id)

if __name__ == '__main__':
    # Example Usage (for testing during development)
    # Ensure this runs from the project root or PYTHONPATH is set for src.
    # Assuming this file is in src/core_ai/code_understanding/

    # Construct path to 'src/tools/' relative to this file's location for standalone testing
    # This is a bit fragile and depends on script location vs. project structure.
    # For proper usage, the module should be imported and used from a context aware of the project root.

    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root_guess = os.path.abspath(os.path.join(current_dir, "..", "..", "..")) # Up three levels from src/core_ai/code_understanding
    # tools_dir_test = os.path.join(project_root_guess, "src", "tools")

    # print(f"Attempting to use tools directory: {tools_dir_test}")
    # model = LightweightCodeModel(tools_directory=tools_dir_test)

    # A more direct way if running script from project root:
    model = LightweightCodeModel # Uses default "src/tools/"

    print("LightweightCodeModel initialized (enhanced version).")
    print(f"Looking for tools in: {model.tools_directory}")

    # The following will print warnings or return None as methods are placeholders.
    # tool_files = model.list_tool_files
    # print(f"Found tool files (enhanced): {tool_files}")

    # math_tool_path_rel = "src/tools/math_tool.py" # Relative to project root
    # if os.path.exists(math_tool_path_rel):
    #     print(f"\nAnalyzing (enhanced): {math_tool_path_rel}")
    #     structure = model.get_tool_structure(math_tool_path_rel)
    #     if structure:
    #         print(json.dumps(asdict(structure), indent=2, default=str))
    #     else:
    #         print("Could not analyze tool structure (enhanced).")
    # else:
    #     print(f"Test math_tool.py not found at {math_tool_path_rel} from current working directory.")

    # # Example for a non-existent tool
    # print("\nAnalyzing non-existent tool (enhanced):")
    # non_existent_structure = model.get_tool_structure("non_existent_tool.py")
    # if not non_existent_structure:
    #     print("Correctly returned None for non-existent tool (enhanced).")

    # Note: The __main__ block is primarily for very basic smoke testing of the class structure.
    # Proper testing will be done with unittest.
    pass # Placeholder to avoid syntax error on empty __main__