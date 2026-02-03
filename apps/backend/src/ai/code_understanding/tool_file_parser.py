import ast
import os
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def extract_method_parameters(method_node: ast.FunctionDef) -> List[Dict[str, Any]]:
    """
    Helper to extract parameter details from an ast.FunctionDef node.
    """
    params_details = []
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
        if i >= pos_defaults_start_idx and i < num_pos_args:  # Positional/regular arg with default:
            default_val_node = args.defaults[i - pos_defaults_start_idx]
            if default_val_node:  # Can be None if there's a default of None literally:
                param_info["default"] = ast.unparse(default_val_node) if hasattr(ast, 'unparse') else "DefaultValue"
        elif arg_node in args.kwonlyargs:
            # For kwonlyargs, kw_defaults is a list of default values, matching kwonlyargs by position.
            # Some values in kw_defaults can be None (for args without defaults).
            try:
                kwonly_idx = args.kwonlyargs.index(arg_node)
                if kwonly_idx < len(args.kw_defaults) and args.kw_defaults[kwonly_idx] is not None:
                    default_val_node = args.kw_defaults[kwonly_idx]
                    # type ignore
                    param_info["default"] = ast.unparse(default_val_node) if hasattr(ast, 'unparse') else "DefaultValue"
            except ValueError:
                pass  # Should not happen if arg_node is from args.kwonlyargs
        params_details.append(param_info)

    if args.vararg:
        vararg_info = {"name": f" * {args.vararg.arg}", "annotation": None, "default": None}
        if args.vararg.annotation:
            vararg_info["annotation"] = ast.unparse(args.vararg.annotation) if hasattr(ast, 'unparse') else "TypeHint"
        params_details.append(vararg_info)

    if args.kwarg:
        kwarg_info = {"name": f" * *{args.kwarg.arg}", "annotation": None, "default": None}
        if args.kwarg.annotation:
            kwarg_info["annotation"] = ast.unparse(args.kwarg.annotation) if hasattr(ast, 'unparse') else "TypeHint"
        params_details.append(kwarg_info)

    return params_details

def parse_python_file(filepath: str) -> Optional[Tuple[ast.AST, List[str]]]:
    """
    Parses a Python file and extracts its AST and dependencies.
    """
    if not os.path.isfile(filepath):
        logger.error(f"File not found at '{filepath}' for parsing.")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as source_file:
            source_code = source_file.read()
        tree = ast.parse(source_code, filename=filepath)
    except Exception as e:
        logger.error(f"Error parsing Python file '{filepath}': {e}", exc_info=True)
        return None

    dependencies = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                dependencies.append(node.module)

    return tree, dependencies
