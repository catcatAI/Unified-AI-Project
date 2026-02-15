import sys
import time
import importlib.util
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "backend"))

print("Profiling backend import performance...")
print("=" * 70)

start_time = time.time()
try:
    from src.services.main_api_server import app
    total_time = time.time() - start_time
    print(f"\n✓ Total import time: {total_time:.2f}s")
    
    if total_time > 10:
        print(f"⚠ WARNING: Import time exceeds 10 seconds!")
    elif total_time > 2:
        print(f"⚠ WARNING: Import time exceeds 2 seconds (target)")
    else:
        print(f"✓ Import time is acceptable")
        
except Exception as e:
    total_time = time.time() - start_time
    print(f"\n✗ Import failed after {total_time:.2f}s")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("\nAnalyzing slow imports...")
print("(Running detailed profiling with -X importtime)\n")
