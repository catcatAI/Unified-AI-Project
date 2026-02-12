import sys
import logging
logger = logging.getLogger(__name__)

print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\nCurrent working directory:")
print(f"  {sys.path[0]}")