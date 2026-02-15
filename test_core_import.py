import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.resolve()
backend_src = project_root / "apps" / "backend" / "src"

sys.path.insert(0, str(backend_src))
print(f"Added to sys.path: {backend_src}")

try:
    from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
    print("✅ Successfully imported DigitalLifeIntegrator")
    
    from core.hardware.hal import HardwareManager
    print("✅ Successfully imported HardwareManager")
    
    hw = HardwareManager()
    print("✅ Successfully initialized HardwareManager")
    print(f"   Architecture: {hw.capabilities.architecture}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
