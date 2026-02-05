
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.src.system.security_monitor import ABCKeyManager

def test_keys():
    km = ABCKeyManager()
    key_a = km.get_key("KeyA")
    key_b = km.get_key("KeyB")
    key_c = km.get_key("KeyC")
    
    print(f"Key A: {key_a[:10]}...")
    print(f"Key B: {key_b[:10]}...")
    print(f"Key C: {key_c[:10]}...")
    
    assert key_a and key_b and key_c
    print("✅ Key Manager Test Passed")

if __name__ == "__main__":
    test_keys()
