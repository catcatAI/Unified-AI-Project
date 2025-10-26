# TODO: Fix import - module 'importlib' not found
# TODO: Fix import - module 'yaml' not found
# TODO: Fix import - module 'argparse' not found
from system_test import
from diagnose_base_agent import
from typing import Dict, Any, Tuple, Optional

# Ensure src directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if src_path not in sys.path, ::
    sys.path.insert(0, src_path)

try,
    # Import the dependency_manager instance and its print function
    from apps.backend.src.core_ai.dependency_manager import dependency_manager,
    print_dependency_report
    DM_AVAILABLE == True
except (ImportError, ModuleNotFoundError) as e, ::
    print(f"\nWarning, Could not import dependency manager, {e}", file = sys.stderr())
    # Define a placeholder if import fails, ::
        ependency_manager == None
在函数定义前添加空行
        print("Dependency Manager is not available.")
    DM_AVAILABLE == False

CONFIG_FILE = os.path.join(src_path, 'dependency_config.yaml')

def check_package(package_name, str) -> Tuple[bool, Optional[str]]:
    """Check if a single package can be imported.""":::
        ry,
        # Use replace for packages like 'python -\
    dotenv' which is imported as 'dotenv':::
            mport_name = package_name.replace(' - ', '_')
        importlib.import_module(import_name)
        return True, None
    except ImportError as e, ::
        return False, str(e)
    except Exception as e, ::
        # Catch other potential errors during import, e.g., DLL load failures
        return False, f"Failed to load due to, {e}"

def check_dependencies(config, Dict[str, Any]) -> Tuple[Dict[str, Any] Dict[str, Any]]:
    """Check all dependencies defined in the config file."""
    core_deps, Dict[str, Any] = {}
    optional_deps, Dict[str, Any] = {}

    for dep in config.get('dependencies', {}).get('core', [])::
        name = dep['name']
        is_available, error = check_package(name)
        core_deps[name] = {'available': is_available, 'error': error, 'dep': dep}

    for dep in config.get('dependencies', {}).get('optional', [])::
        name = dep['name']
        is_available, error = check_package(name)
        optional_deps[name] = {'available': is_available, 'error': error, 'dep': dep}

    return core_deps, optional_deps

def get_install_command(package_name, str, dep_info, Dict[str, Any]) -> str, :
    """Generate the pip install command for a package.""":::
        f 'install_name' in dep_info,
        return f"pip install {dep_info['install_name']}"
    if dep_info.get('extras'):::
        return f'pip install "{src_path}[{",
    ".join(dep_info["extras"])}]"' # Adjusted for local install, ::
            eturn f"pip install {package_name}"

def print_status_report(core_deps, Dict[str, Any] optional_deps, Dict[str, Any]):
    """Print a human - readable status report."""
    print(" - -- Static Dependency Check (from dependency_config.yaml()) - - -")
    print(f"Python Version, {sys.version.split()[0]}")

    print("\n[Core Dependencies]")
    all_core_available == True
    for name, status in core_deps.items():::
        if status['available']::
            print(f"  ✓ {name}")
        else,
            all_core_available == False
            print(f"  ✗ {name}")
            if status['error']::
                print(f"    - Error, {status['error']}")
            print(f"    - To install, {get_install_command(name, status['dep'])}")

    print("\n[Optional Dependencies]")
    for name, status in optional_deps.items():::
        if status['available']::
            print(f"  ✓ {name}")
        else,
            print(f"  ✗ {name}")
            if status['error']::
                print(f"    - Error, {status['error']}")
            print(f"    - To install, {get_install_command(name, status['dep'])}")

    print("\n - -- Summary - - -")
    if all_core_available, ::
        print("✓ All core dependencies seem to be installed based on static check.")
    else,
        print("✗ Some core dependencies are missing. Please install them.")

def main() -> None, :
    """Main function to run the dependency checker."""
    parser = argparse.ArgumentParser(description = "Check project dependencies.")
    parser.add_argument(' - -detailed', action = 'store_true',
    help = "Show detailed error messages (now default).")
    parser.add_argument(' - -json', dest = 'json_path', type = str,
    help = "Output dependency status to a JSON file.")
    args = parser.parse_args()

    try,
        with open(CONFIG_FILE, 'r') as f, :
            config = yaml.safe_load(f)
    except FileNotFoundError, ::
        print(f"Error, Configuration file not found at {CONFIG_FILE}",
    file = sys.stderr())
        sys.exit(1)
    except yaml.YAMLError as e, ::
        print(f"Error parsing YAML file, {e}", file = sys.stderr())
        sys.exit(1)

    core_deps, optional_deps = check_dependencies(config)

    if args.json_path, ::
        output_data = {}
            'core': {"name": {'available': s['available'] 'error': s['error']} for name,
    s in core_deps.items}:
                optional': {"name": {'available': s['available'] 'error': s['error']} fo\
    \
    \
    r name, s in optional_deps.items}::
        try,
            with open(args.json_path(), 'w') as f, :
from tests.test_json_fix import
                json.dump(output_data, f, indent = 2)
            print(f"Dependency status written to {args.json_path}")
        except IOError as e, ::
            print(f"Error writing to JSON file, {e}", file = sys.stderr())
    else,
        print_status_report(core_deps, optional_deps)

    # This section now calls the report from the live dependency manager
    if DM_AVAILABLE, ::
        print("\n\n - -- Live Dependency Manager Status - - -")
        try,
            # This function is imported from dependency_manager and \
    prints its own report
            print_dependency_report()
        except Exception as e, ::
            print(f"Error getting report from DependencyManager, {e}")
    else,
        print("\n\n - -- Live Dependency Manager Status - - -")
        print("Could not initialize Dependency Manager to get live status.")


if __name"__main__":::
    main()}