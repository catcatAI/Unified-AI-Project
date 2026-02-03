import os
import glob
import shutil

DATA_DIR = r"d:\Projects\Unified-AI-Project\apps\backend\data"
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed_data")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")

def wipe_memory():
    print("--- Wiping Memory ---")
    
    # 1. Delete Processed Data (HAM Memory JSONs)
    if os.path.exists(PROCESSED_DATA_DIR):
        json_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*.json"))
        for f in json_files:
            try:
                os.remove(f)
                print(f"Deleted: {f}")
            except Exception as e:
                print(f"Error deleting {f}: {e}")
    else:
        print("No processed_data directory found.")

    # 2. Delete Vector Store (ChromaDB)
    if os.path.exists(VECTOR_STORE_DIR):
        try:
            shutil.rmtree(VECTOR_STORE_DIR)
            print(f"Deleted Vector Store: {VECTOR_STORE_DIR}")
        except Exception as e:
            print(f"Error deleting vector store: {e}")
    else:
        print("No vector_store directory found.")

    print("--- Memory Wipe Complete ---")

if __name__ == "__main__":
    wipe_memory()
