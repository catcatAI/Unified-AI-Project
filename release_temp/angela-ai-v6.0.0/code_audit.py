import os
import ast
import sys
import importlib.util

def check_syntax(file_path):
    """Checks for syntax errors in a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return None
    except SyntaxError as e:
        return f"SyntaxError in {file_path}: {e}"
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def check_imports(file_path, project_root):
    """Checks for potential import errors (basic check)."""
    # This is a simplified check. A full check requires running the code or using a complex static analyzer.
    # We will just try to parse imports and see if they look valid relative to project root.
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        errors = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Basic check: just ensure we can't obviously fail on standard libs
                    pass 
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("apps."):
                    # Check if the file exists
                    module_path = node.module.replace(".", os.sep)
                    full_path = os.path.join(project_root, module_path)
                    if not os.path.exists(full_path) and not os.path.exists(full_path + ".py"):
                         # Try directory
                         if not os.path.isdir(full_path):
                            errors.append(f"Potential broken import in {file_path}: from {node.module} ...")
        return errors
    except Exception as e:
        return [f"Error analyzing imports in {file_path}: {e}"]

def main():
    project_root = os.getcwd()
    print(f"Scanning project root: {project_root}")
    
    syntax_errors = []
    import_warnings = []
    
    for root, dirs, files in os.walk(project_root):
        if "node_modules" in root or ".venv" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # Print checking message to correlate warnings
                # print(f"Checking {file_path}...") 
                
                # Check Syntax
                error = check_syntax(file_path)
                if error:
                    syntax_errors.append(error)
                
                # Check Imports
                warnings = check_imports(file_path, project_root)
                import_warnings.extend(warnings)

    print("\n--- Syntax Check Results ---")
    if syntax_errors:
        for err in syntax_errors:
            print(err)
    else:
        print("No syntax errors found.")

    print("\n--- Import Check Results ---")
    if import_warnings:
        for warn in import_warnings:
            print(warn)
    else:
        print("No obvious import issues found.")

if __name__ == "__main__":
    main()
