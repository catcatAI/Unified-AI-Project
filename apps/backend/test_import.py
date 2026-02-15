import time

start_time = time.time()
print("Starting import...")

from src.services.main_api_server import app

elapsed = time.time() - start_time
print(f"\nImport completed in {elapsed:.2f} seconds")

if elapsed > 10:
    print("WARNING: Import time exceeds 10 seconds!")
elif elapsed > 2:
    print("WARNING: Import time exceeds 2-second target")
else:
    print("Import time is acceptable")
