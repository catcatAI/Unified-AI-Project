import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)
print(f"Project root: {project_root}")
print(f"Sys path: {sys.path}")

try:
    from apps.backend.src.core_services import initialize_services, get_services, shutdown_services
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()