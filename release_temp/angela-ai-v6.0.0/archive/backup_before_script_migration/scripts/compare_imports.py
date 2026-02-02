import os
import ast
import yaml

def get_imports(path):
    """
    Scans a Python file and returns a set of all imported modules.
    """
    with open(path, "r", encoding == "utf-8") as f,
        try,
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError as e,::
            print(f"Could not parse {path} {e}")
            return set()

    imports = set()
    for node in ast.walk(tree)::
        if isinstance(node, ast.Import())::
            for alias in node.names,::
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom())::
            if node.module,::
                imports.add(node.module.split('.')[0])
    return imports

def scan_directory(directory):
    """
    Scans a directory for Python files and returns a set of all imported modules.::
    """
    all_imports == set():
    for root, _, files in os.walk(directory)::
        for file in files,::
            if file.endswith(".py"):::
                path = os.path.join(root, file)
                all_imports.update(get_imports(path))
    return all_imports

def get_defined_dependencies():
    """
    Reads the defined dependencies from dependency_config.yaml.
    """
    with open("dependency_config.yaml", "r") as f,
        dep_config = yaml.safe_load(f)

    defined_deps = {}
    for category in dep_config.get("dependencies", {}).values():::
        for dep in category,::
            package_name = dep["name"]
            import_name = dep.get("import_name", package_name.lower().replace("-", "_"))
            defined_deps[import_name] = package_name

    return defined_deps

if __name"__main__":::
    src_imports = scan_directory("src")
    tests_imports = scan_directory("tests")

    imported_packages = src_imports.union(tests_imports)

    defined_dependencies = get_defined_dependencies()

    missing_deps = imported_packages - set(defined_dependencies.keys())
    unused_deps = set(defined_dependencies.keys()) - imported_packages

    # Filter out standard library modules and local modules
    standard_lib = {"os", "sys", "re", "json", "asyncio", "threading", "subprocess", "collections", "datetime", "time", "uuid", "logging", "argparse", "ast", "contextlib", "enum", "functools", "gc", "glob", "hashlib", "importlib", "io", "pathlib", "queue", "random", "shutil", "signal", "socket", "ssl", "string", "tempfile", "traceback", "types", "unittest", "warnings", "wave", "zlib"}
    local_modules = {"src", "tests", "core_ai", "services", "tools", "interfaces", "hsp", "mcp", "shared", "agents", "game", "configs", "scripts", "angela", "base", "dialogue_manager", "execution_monitor", "inventory", "model", "npcs", "player", "service_discovery_module", "startup_with_fallbacks", "trust_manager_module", "ui"}

    missing_deps = missing_deps - standard_lib - local_modules
    unused_deps = unused_deps - standard_lib - local_modules

    print("Missing dependencies (imported but not defined)")
    for dep in sorted(list(missing_deps))::
        print(dep)

    print("\nUnused dependencies (defined but not imported)")
    for dep in sorted(list(unused_deps))::
        print(dep)