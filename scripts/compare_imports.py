import toml
import yaml

def get_installed_packages():
    """
    Reads the list of imported packages from the file.
    """
    with open("imported_packages.txt", "r") as f:
        packages = [line.strip() for line in f.readlines() if line.strip()]
    return set(packages)

def get_defined_dependencies():
    """
    Reads the defined dependencies from dependency_config.yaml.
    """
    with open("dependency_config.yaml", "r") as f:
        dep_config = yaml.safe_load(f)

    defined_deps = {}
    for category in dep_config.get("dependencies", {}).values():
        for dep in category:
            package_name = dep["name"]
            import_name = dep.get("import_name", package_name.lower().replace("-", "_"))
            defined_deps[import_name] = package_name

    return defined_deps

if __name__ == "__main__":
    imported_packages = get_installed_packages()
    defined_dependencies = get_defined_dependencies()

    missing_deps = imported_packages - set(defined_dependencies.keys())
    unused_deps = set(defined_dependencies.keys()) - imported_packages

    # Filter out standard library modules and local modules
    standard_lib = {"os", "sys", "re", "json", "asyncio", "threading", "subprocess", "collections", "datetime", "time", "uuid", "logging", "argparse", "ast", "contextlib", "enum", "functools", "gc", "glob", "hashlib", "importlib", "io", "pathlib", "queue", "random", "shutil", "signal", "socket", "ssl", "string", "tempfile", "traceback", "types", "unittest", "warnings", "wave", "zlib"}
    local_modules = {"src", "tests", "core_ai", "services", "tools", "interfaces", "hsp", "mcp", "shared", "agents", "game", "configs", "scripts", "angela", "base", "dialogue_manager", "execution_monitor", "inventory", "model", "npcs", "player", "service_discovery_module", "startup_with_fallbacks", "trust_manager_module", "ui"}

    missing_deps = missing_deps - standard_lib - local_modules
    unused_deps = unused_deps - standard_lib - local_modules

    print("Missing dependencies (imported but not defined):")
    for dep in sorted(list(missing_deps)):
        print(dep)

    print("\nUnused dependencies (defined but not imported):")
    for dep in sorted(list(unused_deps)):
        print(dep)
