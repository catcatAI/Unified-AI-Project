from apps.backend.main import app
for route in app.routes:
    print(f"Path: {route.path}, Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
