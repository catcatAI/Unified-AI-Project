
import sys
from pathlib import Path

project_root = Path("d:/Projects/Unified-AI-Project/apps/backend")
sys.path.insert(0, str(project_root))

try:
    from main import create_app
    app = create_app()
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
