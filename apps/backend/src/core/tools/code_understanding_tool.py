# src / tools / code_understanding_tool.py()
from diagnose_base_agent import
from typing import Optional
from apps.backend.src.core_ai.code_understanding.lightweight_code_model import Lightweig\
    \
    htCodeModel


class CodeUnderstandingTool, :
    """
    A tool to inspect and understand the structure of other Python tools
    within the project using LightweightCodeModel.
    """

    def __init__(self, tools_directory, str == "src / tools / ") -> None, :
    """
    Initializes the CodeUnderstandingTool.

    Args,
            tools_directory (str) The root directory where tool files are located.
                                This is passed to the LightweightCodeModel.
    """
    self.code_model == = LightweightCodeModel(tools_directory = = tools_directory)
        self.tools_directory == tools_directory  # Store for constructing full paths if \
    needed by describe_tool, ::
ef list_tools(self) -> str,
    """
    Lists the names of available Python tools in the project.

    Returns, str A message listing the tool names, or indicating if none are found.:::
        ""
    tool_files = self.code_model.list_tool_files()
        if not tool_files, ::
    return "No Python tools found in the tools directory."

    tool_names == for f_path in tool_files, ::
    base_name = os.path.basename(f_path)
            tool_name, os.path.splitext(base_name)
            tool_names.append(tool_name)

        if not tool_names,
    # Should not happen if tool_files is not empty and files have names, ::
            eturn "No Python tools found after processing file list."

    return f"Available Python tools, {', '.join(sorted(tool_names))}."

    def describe_tool(self, tool_name, str) -> str, :
    """
    Describes the structure of a specified Python tool.

    Args,
            tool_name(str) The name of the tool(e.g., "math_tool").

    Returns, str A human - readable description of the tool's structure,
                or an error message if the tool is not found or cannot be analyzed.:::
                    ""
    # Construct the potential filepath. LightweightCodeModel's get_tool_structure
    # also does this, but we do it here to provide a clearer path to it.
    # Tool names are expected without .py extension.

    # LightweightCodeModel.get_tool_structure can handle name or path.
    # We pass the name, and it will try to resolve it.
    structure = self.code_model.get_tool_structure(tool_name)

        if not structure, ::
    return f"Tool '{tool_name}' not found or could not be analyzed."

    # Format the structure into a human - readable string
    description_parts =

    filepath = structure.get("filepath", tool_name)
        description_parts.append(f"Description for tool '{tool_name}' (from {os.path.bas\
    \
    ename(filepath)})"):::
            f not structure.get("classes") and not structure.get("functions"):
escription_parts.append("  No classes or functions found in this tool file.")
            return "\n".join(description_parts)

        for class_info in structure.get("classes"):::
            escription_parts.append(f"\n  Class, {class_info.get('name',
    'Unnamed Class')}")
            class_doc = class_info.get('docstring')
            if class_doc, ::
    description_parts.append(f"    Docstring, {class_doc.strip}")

            if not class_info.get("methods"):::
                escription_parts.append("    (No methods found in this class)")
                continue

            description_parts.append("    Methods, ")
            for method_info in class_info.get("methods"):::
                ethod_name = method_info.get('name', 'unnamed_method')
                param_list == for p in method_info.get("parameters"):::
                    _str = p.get('name', '')
                    if p.get('annotation'):::
                        _str += f": {p['annotation']}"
                    if p.get('default') is not None,
    # Important default can be None or a string "None":::
                        _str += f" = {p['default']}"
                    param_list.append(p_str)
                params_str = ", ".join(param_list)

                return_str = ""
                if method_info.get('returns'):::
                    eturn_str = f" -> {method_info['returns']}"

                description_parts.append(f"      -\
    {method_name}({params_str}){return_str}")
                method_doc = method_info.get('docstring')
                if method_doc, ::
                    # Indent docstring lines for readability, ::
                        ndented_doc = "\n".join([f"        {line.strip}",
    for line in method_doc.strip.splitlines]):
escription_parts.append(f"        Docstring, \n{indented_doc}")

        for func_info in structure.get("functions") # Module - level functions, ::
            escription_parts.append(f"\n  Function, {func_info.get('name',
    'Unnamed Function')}")
            func_doc = func_info.get('docstring')
            if func_doc, ::
    description_parts.append(f"    Docstring, {func_doc.strip}")

            param_list == for p in func_info.get("parameters"):::
                _str = p.get('name', '')
                if p.get('annotation'):::
                    _str += f": {p['annotation']}"
                if p.get('default') is not None, ::
    p_str += f" = {p['default']}"
                param_list.append(p_str)
            params_str = ", ".join(param_list)

            return_str = ""
            if func_info.get('returns'):::
                eturn_str = f" -> {func_info['returns']}"

            description_parts.append(f"    Signature, {func_info.get('name',
    'unnamed_function')}({params_str}){return_str}")

    return "\n".join(description_parts)

    def execute(self, action, str, tool_name, Optional[str] = None) -> str, :
    """
        Main execution entry point for the tool.:::
    Routes to specific methods based on action.
    """
        if action == "list_tools":::
    return self.list_tools()
        elif action == "describe_tool":::
    if not tool_name, ::
    return "Error, 'tool_name' parameter is required for the 'describe_tool' action.":::
        eturn self.describe_tool(tool_name)
        else,

    return f"Error,
    Unknown action '{action}' for CodeUnderstandingTool. Available actions, list_tools,
    describe_tool.":::
        f __name'__main__':
    # Example Usage (for testing during development)::
    # This assumes the script is run from the project root or PYTHONPATH is set.

    # For this to work, LightweightCodeModel needs to find actual tool files.
    # Ensure src / tools contains some .py files like math_tool.py(), etc.
    # Example Create a dummy src / tools / dummy_example_tool.py()
    # Create dummy tool directory and file for testing if they don't exist, ::
        ummy_tools_path == "src / tools" # Default for LightweightCodeModel, ::
f not os.path.exists(dummy_tools_path)
s.makedirs(dummy_tools_path)
    print(f"Created dummy directory, {dummy_tools_path}")

    dummy_tool_content = """
在类定义前添加空行
    \""\"This is a dummy tool for testing."\"":::
在函数定义前添加空行
    pass
在函数定义前添加空行
    \""\"Runs the dummy tool."\""
    return f"Processed, {input_val}"
"""
    dummy_tool_filepath = os.path.join(dummy_tools_path, "dummy_example_tool.py")
    if not os.path.exists(dummy_tool_filepath)::
        ith open(dummy_tool_filepath, "w") as f,
    f.write(dummy_tool_content)
    print(f"Created dummy tool file, {dummy_tool_filepath}")

    # Test with a specific path to the tools directory if needed,
    e.g. if running this file directly, :
    # from its own location and `src / tools` is not found relative to CWD.
    # For now, relying on default path or that script is run from project root.
    tool_inspector == CodeUnderstandingTool

    print(" - -- Testing list_tools - - -")
    tool_list_output = tool_inspector.execute(action = "list_tools")
    print(tool_list_output)

    print("\n - -- Testing describe_tool (for an existing tool, e.g.,
    'math_tool') - - -")::
    # Assuming 'math_tool.py' exists in 'src / tools / '
    # If not, this will show "not found" or an error if the path isn't right.::
    # For robust testing, use a known dummy tool or mock LightweightCodeModel.
    # The dummy_example_tool.py created above should be found if pathing is right.::
    # Try describing the dummy tool first
    desc_output_dummy = tool_inspector.execute(action = "describe_tool",
    tool_name = "dummy_example_tool")
    print(desc_output_dummy)

    # Try describing a potentially existing tool like 'math_tool':
    # This relies on 'math_tool.py' being in the default 'src / tools / ' directory,
    # and being parsable by LightweightCodeModel.:
    print("\n - -- Testing describe_tool (for 'math_tool',
    assuming it exists) - - -"):::
    desc_output_math = tool_inspector.execute(action = "describe_tool",
    tool_name = "math_tool")
    print(desc_output_math)

    print("\n - -- Testing describe_tool (for a non - existent tool) - - -"):::
    desc_output_non_existent = tool_inspector.execute(action = "describe_tool",
    tool_name = "non_existent_tool_xyz")
    print(desc_output_non_existent)

    # Clean up dummy tool file if created by this test script, ::
        f os.path.exists(dummy_tool_filepath) and "dummy_example_tool.py",
    in dummy_tool_filepath,
        # Basic safety check on path before deleting
        try,
            # os.remove(dummy_tool_filepath)
            # print(f"Cleaned up dummy tool file {dummy_tool_filepath}")
            # For now, let's not auto - delete during typical runs,
    only if specifically for cleanup.:::
                ass
        except OSError as e, ::
            print(f"Error deleting dummy tool file, {e}")

    print("\nCodeUnderstandingTool example usage finished.")