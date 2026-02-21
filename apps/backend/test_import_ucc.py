import sys
from pathlib import Path

project_root = Path(__file__).parent
monorepo_root = project_root.parent.parent
sys.path.append(str(monorepo_root.absolute()))
sys.path.append(str((project_root / "src").absolute()))

try:
    from ai.integration.unified_control_center import UnifiedControlCenter
    print("✅ UCC Import Success")
except Exception as e:
    print(f"❌ UCC Import Failed: {e}")
    import traceback
    traceback.print_exc()
