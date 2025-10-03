import os
import ast

def get_imports(path):
    """
    Scans a Python file and returns a set of all imported modules.
    """
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError as e:
            _ = print(f"Could not parse {path}: {e}")
            return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _ = imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _ = imports.add(node.module.split('.')[0])
    return imports

def scan_directory(directory):
    """
    Scans a directory for Python files and returns a set of all imported modules.
    """
    all_imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                _ = all_imports.update(get_imports(path))
    return all_imports

if __name__ == "__main__":
    src_imports = scan_directory("src")
    tests_imports = scan_directory("tests")

    all_imports = sorted(list(src_imports.union(tests_imports)))

    _ = print("All imported packages:")
    for package in all_imports:
        _ = print(package)