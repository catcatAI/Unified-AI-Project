import sys

print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\nCurrent working directory:")
print(f"  {sys.path[0]}")