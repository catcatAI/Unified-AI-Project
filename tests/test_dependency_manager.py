try:
    import apps.backend.src.core.managers.dependency_manager
    print("dependency_manager imported successfully")
except Exception as e:
    print(f"Error importing dependency_manager: {e}")